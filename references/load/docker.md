# Docker / Compose

Read this when touching `Dockerfile`, `compose.yaml`, or
`docker-compose.yml`. Core rules in `SKILL.md` and `trust.md` still
apply. Match the repo's runtime and package manager.

## Build

Use the existing base image, lockfile, and build command. Do not add
Kubernetes, a new service, or a multi-stage build for a one-function
change. If the repo pins image digests, match that convention; do not
invent pinning or upgrade the base image as drive-by work.

Layer order is the cache: copy the dependency manifest, install, then
copy source — not `COPY . .` first, which reinstalls on every source
edit.

```dockerfile
# slop — every code change busts the install layer
COPY . .
RUN npm ci

# needquality
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
```

Keep the build context narrow with `.dockerignore`; never copy `.env`,
credentials, SSH keys, `.git`, or host build output into an image. An
`ARG`/`ENV` secret persists in image history — use the build secret
mechanism the repo's builder supports, or inject at runtime. Clean
package-manager caches in the same `RUN` layer that created them —
a later `rm` does not shrink the image.

The final command must run the app's real entrypoint, in exec form
(`CMD ["node", "server.js"]`) so signals reach the process — shell
form wraps it in `sh -c` and breaks graceful shutdown. Do not replace
a failed build step with `|| true`, an empty command, or a fake health
check.

## Runtime

Compose service names, ports, volumes, environment keys, and health
checks match the existing tree. `depends_on` ordering is not readiness;
use the repo's health condition or retry policy at the real boundary.
Health checks must test a meaningful dependency and return failure when
that dependency is down. Run `docker compose config` before claiming
the file is valid, then build or start the named service when possible.

Do not run migrations, seed credentials, `prisma db push`, or reset a
shared database from image boot. Run as the existing non-root user when
the repo supports it (`USER`), and add one only when the app does not
need root — matching the tree beats inventing hardening. Keep secrets
in the runtime secret mechanism, not ARG/ENV that becomes image
metadata, and not committed `env_file` entries. Named volumes for data
that must survive the container; a bind mount of source is a dev
convenience, not a production layout. Do not publish a port the
service does not need on the host — container-to-container traffic
uses the compose network.
