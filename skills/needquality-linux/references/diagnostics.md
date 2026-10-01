# Host diagnostics

## Units and journals

Discover the named unit with `systemctl status UNIT --no-pager` and inspect
`systemctl cat UNIT`. Check its drop-ins, dependencies, service account,
restart policy, and actual executable. Read bounded evidence with
`journalctl -u UNIT --since '30 minutes ago' --no-pager`; use kernel journals
for OOM or I/O failures. Redact secrets before sharing excerpts.

| Change | Action |
|---|---|
| Application configuration | Validate with the application's checker, then `systemctl reload UNIT` if supported |
| Unit file or drop-in | Validate the unit with `systemd-analyze verify PATH`, then `systemctl daemon-reload` |
| Executable, startup environment, or setting requiring a new process | Restart the named service within the accepted disruption boundary |

`daemon-reload` rereads systemd unit definitions; it does not restart the
application or reload its configuration. A service reload asks that service to
reload its own configuration. A restart stops and starts it and may interrupt
requests. After a unit change, perform any separately required service action
and verify effective properties and application behavior. Avoid
`reload-or-restart` when an unexpected restart would exceed the allowed downtime.

Sources checked 2026-10-01: [systemctl manual](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html),
[official manual source](https://github.com/systemd/systemd/blob/main/man/systemctl.xml).

## Storage pressure

Inspect `df -h` and `df -i` to distinguish bytes from inode exhaustion. Use
bounded `du -x -h --max-depth=1 PATH` on the affected filesystem, then inspect
the large directory. Check `journalctl --disk-usage` and, if available,
`lsof +L1` for deleted files still held open. Investigate mount failures and
read-only filesystems before treating them as ordinary space shortages.

Record the owner and retention requirement before cleanup. Use existing log
rotation or retention policy; preserve database files, backups, and deployment
artifacts needed for rollback. Verify recovered space and the failed operation.
Container storage and volumes belong to `needquality-docker`.

## Resource pressure

Start with `uptime`, `free -h`, `vmstat 1 5`, and a bounded process listing;
use installed I/O tools only when that evidence points to disk contention.
Correlate the interval with unit journals, kernel OOM events, and application
latency. Load average alone does not identify CPU saturation.

Inspect `systemctl show UNIT` with selected properties such as `MemoryCurrent`,
`MemoryHigh`, `MemoryMax`, `CPUQuotaPerSecUSec`, `TasksMax`, and `LimitNOFILE`.
Check parent slice constraints, cgroup version, and the running process's
`/proc/PID/limits`; a shell's `ulimit` is not proof of service limits. For a
container, inspect its own limits rather than only the Docker daemon unit.

`MemoryHigh` applies reclaim pressure and throttling; it is not a hard ceiling.
`MemoryMax` can invoke OOM termination within the unit when usage cannot be
contained. Choose limits from observed usage and host headroom, record prior
values, and verify both effective limits and behavior under representative load.

Sources checked 2026-10-01: [resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html),
[official manual source](https://github.com/systemd/systemd/blob/main/man/systemd.resource-control.xml).
