"""Credential redaction and persistence boundary for evaluation evidence."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

SECRET_KEY_RE = re.compile(
    r"(?:authorization|cookie|credential|password|passwd|secret|token|api[_-]?key|private[_-]?key)",
    re.I,
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b(?:sk|pk)[-_][A-Za-z0-9_-]{12,}\b", re.I),
    re.compile(r"\b(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b(?:glpat-|npm_|xox[baprs]-)[A-Za-z0-9_-]{10,}\b", re.I),
    re.compile(r"\bwhsec_[A-Za-z0-9_-]{16,}\b", re.I),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}=*", re.I),
    re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@[^\s]+", re.I),
)


def environment_secrets(environment: dict[str, str] | None = None) -> list[str]:
    source = os.environ if environment is None else environment
    return sorted(
        {
            value
            for key, value in source.items()
            if SECRET_KEY_RE.search(key) and isinstance(value, str) and len(value) >= 8
        },
        key=len,
        reverse=True,
    )


def redact_text(value: str, environment: dict[str, str] | None = None) -> str:
    redacted = value
    for secret in environment_secrets(environment):
        redacted = redacted.replace(secret, "<redacted>")
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("<redacted>", redacted)
    return redacted


def redact(value: Any, environment: dict[str, str] | None = None) -> Any:
    secrets = environment_secrets(environment)

    def visit(item: Any) -> Any:
        if isinstance(item, dict):
            return {
                str(key): "<redacted>" if SECRET_KEY_RE.search(str(key)) else visit(child)
                for key, child in item.items()
            }
        if isinstance(item, (list, tuple)):
            return [visit(child) for child in item]
        if isinstance(item, str):
            text = item
            for secret in secrets:
                text = text.replace(secret, "<redacted>")
            for pattern in SECRET_PATTERNS:
                text = pattern.sub("<redacted>", text)
            return text
        return item

    return visit(value)


def save_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact_text(value), encoding="utf-8")


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(value), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(redact(event), ensure_ascii=False) + "\n")
