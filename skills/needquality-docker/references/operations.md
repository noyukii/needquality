# Compose operations

## Discover the target

Inspect `docker context show`, `docker context inspect`, relevant endpoint
overrides such as `DOCKER_HOST`, and `docker compose version`. Confirm the
effective daemon and environment before mutation. Inspect `docker compose ls`,
the deployed Compose files/overlays, project name, profiles, environment inputs,
and `docker compose ps`. Keep that exact selection on every command; a different
working directory can select a different project. Avoid printing credentials.

Validate the selected model with `docker compose config --quiet`; inspect only
non-secret fields if diagnosis needs rendered configuration. Record running
image IDs/digests, mounts, and named service state before updates.

## Update and diagnose

Pull or build the named service and use the existing deployment procedure.
Recreate it to adopt changed images or Compose configuration; `restart` alone
does neither. `up -d --no-deps SERVICE` limits dependency recreation only when
dependencies already meet the release contract. Check dependent services'
restart propagation. Avoid project-wide `down` for a service update.

Inspect bounded `logs --since 10m --tail 100 SERVICE`, exit/restart state,
healthcheck output, and `docker stats --no-stream`. Redact credentials before
sharing logs. Correlate container failures with dependency and host evidence.

## Readiness

Compose start order is not application readiness. Long-form `depends_on` with
`condition: service_healthy` needs a meaningful dependency healthcheck;
`service_completed_successfully` fits a required successful one-shot job.
Keep application retries for later dependency outages: startup conditions do
not provide continuous recovery. Where supported, use a bounded `up --wait`
and still test the real application path; running without a healthcheck is
weaker evidence. Use `needquality-server` for external-route deployment proof.

Source checked 2026-10-01: [Compose startup and readiness](https://docs.docker.com/compose/how-tos/startup-order/).

## Volumes and secrets

Inspect named volumes and bind mounts, their ownership, consumers, and backup
coverage before recreation or cleanup. Preserve persistent data; `down -v`,
volume pruning, and deleting bind-mount directories are destructive operations
that require a named, authorized data-removal scope. Use `needquality-server`
for database-aware backups and restore drills.

Compose secrets mount files under `/run/secrets/NAME` for explicitly granted
services. They do not automatically populate application environment variables.
Verify the app or image can read the mounted path; `_FILE` support is an image
convention, not universal Compose behavior. Check runtime-user readability
without printing the value. Preserve a supported injection path until the
replacement works; secret files also need host access controls.

Source checked 2026-10-01: [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/).

## Published ports

Inventory host bindings and IPv4/IPv6 exposure independently of UFW: Docker
published-port traffic can bypass UFW's usual filtering path. Prefer no host
publication for internal traffic, or a deliberate loopback/private binding
when the existing proxy needs it. Test the intended public and blocked paths
from outside the host when authorized; local listeners alone are insufficient.

Discover Docker's firewall backend before choosing rules. Preserve Docker's
network rules and use the supported backend-specific filtering mechanism;
disabling its iptables management can break networking. Record what was
tested before claiming a port is private.

Source checked 2026-10-01: [Docker packet filtering and UFW](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
