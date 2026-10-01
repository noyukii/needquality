# Deployment and maintenance

## Preflight

Confirm the target host, environment, release directory, Compose project and
file overlays, named service, reverse proxy, and external route. Inspect the
existing CI and deployment scripts before choosing commands. Check disk and
inode headroom, dependency health, persistent data, and access recovery.

Record the running release/image digest, previous usable release, configuration
version, schema version, and expected downtime. Define success and rollback
checks before mutation. If a migration is involved, establish old/new code
compatibility and its lock/downtime requirements with `needquality-sql`;
read [recovery.md](recovery.md) before proceeding.

## Trace configuration to the process

Follow each required key through CI variable scope and protection, job inputs,
deployment/provisioning scripts, transfer to the host, environment or secret
files, Compose interpolation, service injection, and application consumption.
Distinguish the Compose `.env` interpolation source from `env_file`,
`environment`, and mounted secrets. A value present in CI does not establish
that it reached the running application.

Verify presence and the expected configuration behavior without printing secret
values. Keep secrets out of shell tracing, rendered Compose output, process
environment dumps, and logs; `docker compose config --quiet` validates without
printing the resolved model. After configuration changes, recreate the named
container when needed; a restart alone does not adopt new Compose environment.
Use `needquality-docker` for mounted-secret compatibility.

## Apply and prove

Use the existing release process. For a service-only Compose update, retain the
exact context, project, overlays, and environment selection on every command;
pull or build the named image and recreate that service. `up -d --no-deps SERVICE`
is appropriate only when its dependencies already satisfy the release. Inspect
dependency restart propagation before claiming only one service will change.

Check readiness and bounded logs, then test the application's intended route
through the existing proxy with the real hostname, TLS validation, status,
and expected response. A container marked running, an open TCP port, or a local
health endpoint does not prove the external application path. Keep readiness,
proxy reachability, and application behavior as separate evidence.

Source checked 2026-10-01: [Compose production deployments](https://docs.docker.com/compose/how-tos/production/).

## Proxy and maintenance

Inspect the installed proxy and active configuration. Preserve its certificate,
upstream, forwarding, timeout, and access conventions. Validate the proposed
configuration before applying it. For existing NGINX, use `nginx -t` with the
actual config path and privileges, then its supported reload; inspect logs and
the external route afterward. A successful command alone does not prove new
workers accepted the intended traffic.

For maintenance, name the disruption window, affected routes, jobs, and writes;
drain or pause them through existing controls when necessary. Coordinate
scheduled jobs and migrations to avoid concurrent writes. Verify restored
traffic and job processing before declaring the window complete.

Sources checked 2026-10-01: [NGINX reload behavior](https://nginx.org/en/docs/beginners_guide.html),
[NGINX configuration test](https://nginx.org/en/docs/switches.html).
