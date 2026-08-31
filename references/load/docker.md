# Docker / Compose

Read this when touching `Dockerfile`, `compose.yaml`, or
`docker-compose.yml`. Core rules in `SKILL.md` and `trust.md` still
apply. Match the repo's runtime and package manager.

## Build

Use the existing base image, lockfile, and build command. Do not add
Kubernetes, a new service, or a multi-stage build for a one-function
change. Keep the build context narrow with `.dockerignore`; never copy
`.env`, credentials, SSH keys, or host build output into an image.

The final command must run the app's real entrypoint. Do not replace a
failed build step with `|| true`, an empty command, or a fake health
check. If the repo pins image digests, match that convention; do not
invent pinning or upgrade the base image as drive-by work.

## Runtime

Compose service names, ports, volumes, environment keys, and health
checks match the existing tree. `depends_on` ordering is not readiness;
use the repo's health condition or retry policy at the real boundary.
Health checks must test a meaningful dependency and return failure when
that dependency is down. Run `docker compose config` before claiming
the file is valid, then build or start the named service when possible.

Do not run migrations, seed credentials, `prisma db push`, or reset a
shared database from image boot. Run as the existing non-root user when
the repo supports it. Keep secrets in the runtime secret mechanism,
not ARG/ENV that becomes image metadata.
