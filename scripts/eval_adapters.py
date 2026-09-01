"""Provider adapters and streamed event normalization for NeedQuality evals."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval_evidence import redact

MAX_STDERR = 100_000


def now() -> str:
    return datetime.now(UTC).isoformat()


def probe(command: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="needquality-runner-probe-") as temp:
        home = Path(temp)
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "CODEX_HOME": str(home / ".codex"),
                "XDG_CONFIG_HOME": str(home / ".config"),
            }
        )
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=environment,
        )


def canonical_tool(name: str) -> str:
    lowered = re.sub(r"[^a-z0-9_.-]+", "", name.lower())
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    if compact in {
        "web",
        "websearch",
        "websearchcall",
        "websearchtoolcall",
        "webfetch",
        "webfetchcall",
        "webfetchtoolcall",
    }:
        return "web"
    if compact in {
        "bash",
        "shell",
        "terminal",
        "commandexecution",
        "shellcommand",
        "shelltoolcall",
        "terminaltoolcall",
    }:
        return "shell"
    return lowered.removesuffix("toolcall").removesuffix("tooluse").removesuffix("call")


def valid_tool_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = canonical_tool(value)
    return normalized or None


def event(
    event_type: str,
    raw_ref: str,
    timestamp: str,
    *,
    tool: str | None = None,
    arguments: Any = None,
    status: str | None = None,
    call_id: str | None = None,
) -> dict:
    return {
        "type": event_type,
        "tool": canonical_tool(tool) if tool else None,
        "arguments": redact(arguments),
        "status": status,
        "timestamp": timestamp,
        "call_id": call_id,
        "raw_ref": raw_ref,
    }


class ProviderAdapter:
    name = ""
    executable = ""
    supports_tool_free_judge = False

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def unavailable_reason(self) -> str:
        return "executable not found" if not self.available() else ""

    def version(self) -> str:
        cached = getattr(self, "_version_cache", None)
        if cached is not None:
            return cached
        if not self.available():
            self._version_cache = "unavailable"
            return self._version_cache
        try:
            done = probe([self.executable, "--version"])
        except (OSError, subprocess.TimeoutExpired) as error:
            self._version_cache = f"unknown: {error}"
            return self._version_cache
        self._version_cache = (done.stdout or done.stderr).strip().splitlines()[0] or "unknown"
        return self._version_cache

    def build_command(self, prompt: str, cwd: Path, model: str | None, mode: str) -> list[str]:
        raise NotImplementedError

    def normalize_record(
        self, payload: dict, raw_ref: str, timestamp: str
    ) -> tuple[list[dict], list[str], list[str]]:
        raise NotImplementedError

    def execute(
        self,
        prompt: str,
        cwd: Path,
        home: Path,
        model: str | None,
        timeout: int,
        mode: str = "task",
    ) -> dict:
        if mode == "judge" and not self.supports_tool_free_judge:
            raise ValueError(f"{self.name} cannot enforce a tool-free semantic judge")
        command = self.build_command(prompt, cwd, model, mode)
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "CODEX_HOME": str(home / ".codex"),
                "XDG_CONFIG_HOME": str(home / ".config"),
            }
        )
        started_at = now()
        started = time.monotonic()
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as error:
            return self.failed_result(command, started, started_at, error)

        messages: queue.Queue[tuple[str, str | None, str]] = queue.Queue()

        def read_stream(label: str, stream: Any) -> None:
            try:
                for line in iter(stream.readline, ""):
                    messages.put((label, line, now()))
            finally:
                messages.put((label, None, now()))
                stream.close()

        threads = [
            threading.Thread(target=read_stream, args=("stdout", process.stdout), daemon=True),
            threading.Thread(target=read_stream, args=("stderr", process.stderr), daemon=True),
        ]
        for thread in threads:
            thread.start()

        raw_events: list[dict] = []
        events: list[dict] = []
        final_parts: list[str] = []
        errors: list[str] = []
        stderr: list[str] = []
        stderr_size = 0
        malformed = False
        timed_out = False
        closed: set[str] = set()
        calls: dict[str, str] = {}
        deadline = started + timeout
        index = 0

        def consume(label: str, line: str | None, received: str) -> None:
            nonlocal index, stderr_size, malformed
            if line is None:
                closed.add(label)
                return
            if label == "stderr":
                if stderr_size < MAX_STDERR:
                    stderr.append(line[: MAX_STDERR - stderr_size])
                    stderr_size += len(stderr[-1])
                return
            if not line.strip():
                return
            index += 1
            raw_ref = f"stdout:{index}"
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                payload = {"type": "raw", "text": line.rstrip("\r\n")}
                malformed = True
            raw_events.append(
                {"index": index, "raw_ref": raw_ref, "timestamp": received, "payload": payload}
            )
            if payload.get("type") == "raw":
                events.append(event("raw", raw_ref, received))
                return
            normalized, texts, record_errors = self.normalize_record(
                payload, raw_ref, received
            )
            for row in normalized:
                call_id = row.get("call_id")
                if row.get("tool") and call_id:
                    calls[call_id] = row["tool"]
                elif row.get("type") == "tool_result" and call_id in calls:
                    row["tool"] = calls[call_id]
                events.append(row)
            final_parts.extend(texts)
            errors.extend(f"{raw_ref}: {message}" for message in record_errors)

        while len(closed) < 2:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                self.stop(process)
                break
            try:
                label, line, received = messages.get(timeout=min(0.1, remaining))
            except queue.Empty:
                if process.poll() is not None and all(not thread.is_alive() for thread in threads):
                    break
                continue
            consume(label, line, received)

        if process.poll() is None:
            try:
                process.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
                self.stop(process)
        for thread in threads:
            thread.join(timeout=1)
        while not messages.empty():
            consume(*messages.get_nowait())

        final = final_parts[-1].strip() if final_parts else ""
        if not final and raw_events and all(row["payload"].get("type") == "raw" for row in raw_events):
            final = "\n".join(row["payload"]["text"] for row in raw_events).strip()
        stderr_text = "".join(stderr)
        if timed_out:
            stderr_text = f"{stderr_text}\nrunner timed out after {timeout}s".strip()
        return {
            "returncode": process.returncode,
            "seconds": round(time.monotonic() - started, 3),
            "raw_events": raw_events,
            "events": events,
            "final": final,
            "malformed": malformed,
            "normalization_errors": errors,
            "stderr": stderr_text,
            "command": [*command[:-1], "<prompt>"],
            "started_at": started_at,
            "ended_at": now(),
            "timed_out": timed_out,
        }

    @staticmethod
    def stop(process: subprocess.Popen) -> None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    @staticmethod
    def failed_result(command: list[str], started: float, started_at: str, error: OSError) -> dict:
        return {
            "returncode": None,
            "seconds": round(time.monotonic() - started, 3),
            "raw_events": [],
            "events": [],
            "final": "",
            "malformed": False,
            "normalization_errors": [],
            "stderr": str(error),
            "command": [*command[:-1], "<prompt>"],
            "started_at": started_at,
            "ended_at": now(),
            "timed_out": False,
        }


class CursorAdapter(ProviderAdapter):
    name = "cursor"
    executable = "cursor-agent"
    tools = {
        "shellToolCall": "shell",
        "terminalToolCall": "shell",
        "webSearchToolCall": "web",
        "webFetchToolCall": "web",
        "readToolCall": "read",
        "writeToolCall": "write",
        "editToolCall": "edit",
        "deleteToolCall": "delete",
        "grepToolCall": "grep",
        "globToolCall": "glob",
        "listDirToolCall": "list-dir",
        "mcpToolCall": "mcp",
        "computerUseToolCall": "computer-use",
    }

    def build_command(self, prompt: str, cwd: Path, model: str | None, mode: str) -> list[str]:
        command = [
            self.executable,
            "--print",
            "--output-format",
            "stream-json",
            "--trust",
            "--workspace",
            str(cwd),
            "--sandbox",
            "enabled",
        ]
        command += ["--mode", "ask"] if mode == "smoke" else ["--force"]
        if model:
            command += ["--model", model]
        return [*command, prompt]

    def normalize_record(self, payload: dict, raw_ref: str, timestamp: str) -> tuple[list[dict], list[str], list[str]]:
        events: list[dict] = []
        errors: list[str] = []
        kind = str(payload.get("type", "unknown"))
        container = payload.get("tool_call")
        if kind == "tool_call" and isinstance(container, dict):
            if "name" in container or "tool" in container:
                name = valid_tool_name(container.get("name") or container.get("tool"))
                if not name:
                    errors.append("Cursor tool record has no valid name")
                else:
                    events.append(
                        event(
                            "tool_call",
                            raw_ref,
                            timestamp,
                            tool=name,
                            arguments=container.get("input") or container.get("arguments"),
                            status=container.get("status") or payload.get("status") or payload.get("subtype"),
                            call_id=str(container.get("id") or payload.get("call_id") or "") or None,
                        )
                    )
            else:
                for name, details in container.items():
                    if name not in self.tools or not isinstance(details, dict):
                        errors.append(f"unrecognized Cursor tool record: {name}")
                        continue
                    tool = self.tools[name]
                    if name == "mcpToolCall":
                        arguments = details.get("args") or details.get("input") or details.get("arguments")
                        argument_map = arguments if isinstance(arguments, dict) else {}
                        mcp_name = valid_tool_name(
                            details.get("tool")
                            or details.get("name")
                            or argument_map.get("tool")
                            or argument_map.get("toolName")
                            or argument_map.get("name")
                        )
                        server = valid_tool_name(
                            details.get("server")
                            or argument_map.get("server")
                            or argument_map.get("serverName")
                        )
                        if not mcp_name:
                            errors.append("Cursor MCP tool record has no valid tool name")
                            continue
                        tool = f"{server}.{mcp_name}" if server else mcp_name
                    events.append(
                        event(
                            "tool_call",
                            raw_ref,
                            timestamp,
                            tool=tool,
                            arguments=details.get("args") or details.get("input") or details.get("arguments"),
                            status=details.get("status") or payload.get("status") or payload.get("subtype"),
                            call_id=str(details.get("id") or payload.get("call_id") or "") or None,
                        )
                    )
        elif kind in {"command_execution", "shell_command"}:
            events.append(event(kind, raw_ref, timestamp, tool="shell", arguments=payload.get("command") or payload.get("input"), status=payload.get("status"), call_id=str(payload.get("id") or "") or None))
        elif kind in {"web_search", "web_search_call"}:
            events.append(event(kind, raw_ref, timestamp, tool="web", arguments=payload.get("query") or payload.get("arguments"), status=payload.get("status"), call_id=str(payload.get("id") or "") or None))
        elif "tool" in kind.lower():
            errors.append(f"unrecognized Cursor tool event type: {kind}")
        if not events:
            events.append(event(kind, raw_ref, timestamp, status=payload.get("status")))
        texts: list[str] = []
        if kind == "result":
            if payload.get("is_error"):
                errors.append("Cursor terminal result reports an error")
            elif isinstance(payload.get("result"), str):
                texts.append(payload["result"])
            else:
                errors.append("Cursor terminal result has no text")
        return events, texts, errors


class CodexAdapter(ProviderAdapter):
    name = "codex"
    executable = "codex"

    def build_command(self, prompt: str, cwd: Path, model: str | None, mode: str) -> list[str]:
        command = [
            self.executable,
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only" if mode == "smoke" else "workspace-write",
            "-C",
            str(cwd),
        ]
        if mode == "task":
            command.append("--approve-for-me")
        if model:
            command += ["--model", model]
        return [*command, prompt]

    def normalize_record(self, payload: dict, raw_ref: str, timestamp: str) -> tuple[list[dict], list[str], list[str]]:
        events: list[dict] = []
        errors: list[str] = []
        outer_kind = str(payload.get("type", "unknown"))
        if isinstance(payload.get("items"), list):
            items = [item for item in payload["items"] if isinstance(item, dict)]
            if len(items) != len(payload["items"]):
                errors.append("Codex items record contains a non-object entry")
        else:
            items = [payload.get("item") if isinstance(payload.get("item"), dict) else payload]
        texts: list[str] = []
        for item in items:
            kind = str(item.get("type", outer_kind))
            status = item.get("status") or payload.get("status")
            if not status and outer_kind.endswith(".completed"):
                status = "completed"
            call_id = str(item.get("id") or item.get("call_id") or "") or None
            if kind in {"command_execution", "shell_command"}:
                events.append(event(kind, raw_ref, timestamp, tool="shell", arguments=item.get("command") or item.get("input"), status=status, call_id=call_id))
            elif kind in {"web_search", "web_search_call"}:
                events.append(event(kind, raw_ref, timestamp, tool="web", arguments=item.get("query") or item.get("arguments"), status=status, call_id=call_id))
            elif kind in {"mcp_tool_call", "mcp_call", "function_call", "tool_call"}:
                name = valid_tool_name(item.get("name") or item.get("tool"))
                if not name:
                    errors.append(f"Codex {kind} record has no valid name")
                else:
                    server = valid_tool_name(item.get("server"))
                    tool = f"{server}.{name}" if server else name
                    events.append(event(kind, raw_ref, timestamp, tool=tool, arguments=item.get("arguments") or item.get("input"), status=status, call_id=call_id))
            elif "tool" in kind.lower() or "command" in kind.lower():
                errors.append(f"unrecognized Codex tool event type: {kind}")
            if kind in {"agent_message", "output_text"} and isinstance(item.get("text"), str):
                texts.append(item["text"])
        if isinstance(payload.get("result"), str):
            texts.append(payload["result"])
        if not events:
            events.append(event(outer_kind, raw_ref, timestamp, status=payload.get("status")))
        return events, texts, errors


class ClaudeAdapter(ProviderAdapter):
    name = "claude"
    executable = "claude"
    supports_tool_free_judge = True
    required_flags = {
        "--safe-mode",
        "--mcp-config",
        "--no-chrome",
        "--setting-sources",
        "--settings",
        "--strict-mcp-config",
        "--tools",
    }

    def available(self) -> bool:
        if not shutil.which(self.executable):
            return False
        cached = getattr(self, "_help_cache", None)
        if cached is None:
            try:
                done = probe([self.executable, "--help"])
                cached = done.stdout or done.stderr
            except (OSError, subprocess.TimeoutExpired):
                cached = ""
            self._help_cache = cached
        return all(flag in cached for flag in self.required_flags)

    def unavailable_reason(self) -> str:
        if not shutil.which(self.executable):
            return "executable not found"
        return "strict sandbox and tool-free judge flags are unavailable"

    def build_command(self, prompt: str, cwd: Path, model: str | None, mode: str) -> list[str]:
        sandbox = json.dumps(
            {
                "sandbox": {
                    "enabled": True,
                    "failIfUnavailable": True,
                    "allowUnsandboxedCommands": False,
                    "excludedCommands": [],
                    "filesystem": {
                        "denyRead": [str(Path.home())],
                        "allowRead": [str(cwd)],
                        "denyWrite": ["/"],
                        "allowWrite": [str(cwd)],
                    },
                }
            },
            separators=(",", ":"),
        )
        command = [
            self.executable,
            "--print",
            "--output-format",
            "stream-json",
            "--no-session-persistence",
            "--setting-sources",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            "{}",
            "--no-chrome",
            "--settings",
            sandbox,
            "--permission-mode",
            "plan" if mode in {"smoke", "judge"} else "bypassPermissions",
        ]
        if mode == "task":
            command.append("--allow-dangerously-skip-permissions")
        if mode == "judge":
            command += ["--safe-mode", "--tools", ""]
        if model:
            command += ["--model", model]
        return [*command, prompt]

    def normalize_record(self, payload: dict, raw_ref: str, timestamp: str) -> tuple[list[dict], list[str], list[str]]:
        events: list[dict] = []
        errors: list[str] = []
        tool_like = False
        outer_kind = str(payload.get("type", "unknown"))
        nodes: list[dict] = []
        if outer_kind in {"tool_use", "tool_result"}:
            nodes.append(payload)
        message = payload.get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), list):
            nodes.extend(block for block in message["content"] if isinstance(block, dict))
        for node in nodes:
            kind = str(node.get("type", ""))
            if kind == "tool_use":
                tool_like = True
                name = valid_tool_name(node.get("name") or node.get("tool"))
                if not name:
                    errors.append("Claude tool_use record has no valid name")
                    continue
                events.append(event("tool_call", raw_ref, timestamp, tool=name, arguments=node.get("input") or node.get("arguments"), status=str(node.get("status") or "started"), call_id=str(node.get("id") or "") or None))
            elif kind == "tool_result":
                tool_like = True
                events.append(event("tool_result", raw_ref, timestamp, status="error" if node.get("is_error") else "completed", call_id=str(node.get("tool_use_id") or node.get("id") or "") or None))
        if not events:
            events.append(event(outer_kind, raw_ref, timestamp, status=payload.get("status")))
        if "tool" in outer_kind.lower() and not tool_like:
            errors.append(f"unrecognized Claude tool event type: {outer_kind}")
        texts: list[str] = []
        if outer_kind == "result" and isinstance(payload.get("result"), str):
            texts.append(payload["result"])
        elif outer_kind == "assistant" and isinstance(payload.get("message"), dict):
            for block in payload["message"].get("content", []):
                if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                    texts.append(block["text"])
        return events, texts, errors


def adapter_for(name: str) -> ProviderAdapter:
    adapters = {adapter.name: adapter for adapter in (CursorAdapter(), CodexAdapter(), ClaudeAdapter())}
    try:
        return adapters[name]
    except KeyError as error:
        raise ValueError(f"unsupported runner: {name}") from error
