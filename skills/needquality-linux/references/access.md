# Host access

## Discover

Read `/etc/os-release`, `uname -r`, `uname -m`, `hostname`, and `id`. Confirm
the host, environment, privilege level, and available recovery console. Check
the installed init system and tool versions; a Linux container may lack systemd.
Use installed manuals for version-specific options.

For Ubuntu/Debian packages, inspect `apt-cache policy PACKAGE` and simulate
the named change with `apt-get -s install PACKAGE`. Review removals, dependency
changes, service restarts, and reboot requirements before applying it. Keep
existing repositories and package pins; a package task is not a release upgrade.

Inspect users with `getent passwd USER` and `id USER`; inspect path ownership
and traversal with `stat` and `namei -l PATH`. Match the service account and
required permissions. Change the smallest named path or group membership;
avoid world-writable permissions and recursive ownership changes across system
or database directories. Verify the operation as the intended user.

## Preserve SSH access

1. Keep the current session open. Record working access and a recovery path;
   save the affected configuration with its ownership and mode.
2. Discover the active SSH service and any socket unit. Inspect includes and
   drop-ins; Ubuntu commonly reads `sshd_config.d` before the main file, and
   most directives use the first value. Check effective settings with
   `sudo sshd -T`, including `-C` connection criteria for relevant `Match` rules.
   Inspect `PasswordAuthentication`, `KbdInteractiveAuthentication`, and
   `AuthenticationMethods`; check the distro's PAM setup for password prompts
   while preserving any required MFA policy.
3. Prove the intended key, user, and sudo access in a separate connection before
   disabling a working authentication method. Select the intended key explicitly
   and confirm it was accepted; prevent password or other-key fallback from
   masking failure while retaining required MFA. For a port change, inspect and
   allow the new path through host and provider firewalls before changing
   listeners; retain the working port until the new connection succeeds.
4. Run `sudo sshd -t` on the proposed configuration before applying it. Resolve
   errors before any reload or restart. If socket activation owns the listener,
   follow the installed socket configuration procedure rather than assuming
   an `sshd_config` port edit alone changes it.
5. Apply the supported service action to the discovered unit, staging a new
   listener alongside the working one for a port transition. Open a fresh
   connection with SSH multiplexing disabled and verify authentication and
   required privilege. Keep the original session until this succeeds; restore
   the saved configuration through it or the recovery console if it fails.

Sources checked 2026-10-01: [Ubuntu OpenSSH server](https://ubuntu.com/server/docs/how-to/security/openssh-server/),
[OpenSSH authentication methods](https://man.openbsd.org/sshd_config).

## Firewall

Inspect listeners (`ss -lntup`), the active firewall backend and rules, and any
provider firewall. With existing UFW, inspect `sudo ufw status verbose` and
preview the named rule using `sudo ufw --dry-run ...`. Preserve the current SSH
port and authorized source before enabling or tightening rules; test fresh
access afterward. Include IPv4 and IPv6 and keep a way to revert the change.

If Docker publishes ports, use `needquality-docker` to inspect and test that
exposure separately. A UFW status listing alone does not prove those ports are
blocked. Preserve the installed firewall rather than replacing its backend.
