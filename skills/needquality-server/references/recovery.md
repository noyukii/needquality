# Backups and recovery

## Backup contract

Name the data, recovery point and recovery time objectives, retention, storage
destination, access controls, and restore target. Include required configuration,
uploads, database globals, and key recovery. Inventory Compose volumes and bind
mounts with `needquality-docker`; volume existence is not backup evidence.

Use the database's supported backup method for a running database. A tar/copy
of active PostgreSQL data files is not a consistent backup. File-level copies
require shutdown or a consistent snapshot covering the complete cluster,
including WAL and all relevant filesystems. Merely blocking client connections
is insufficient. Use the installed database/version's documented physical
backup procedure when logical dumps do not meet the recovery objective.

Source checked 2026-10-01: [PostgreSQL filesystem backups](https://www.postgresql.org/docs/current/backup-file.html).

For PostgreSQL, `pg_dump` gives a consistent single-database snapshot but omits
cluster-wide roles and tablespaces. Capture needed globals separately with
`pg_dumpall --globals-only` or preserve their provisioning source. Check client
and server version compatibility, privileges, extensions, artifact completeness,
and command exit status. Protect backup files and role credentials; capture
pipeline failures as well as the last command's status.

## Restore drill

Restore into an isolated target with distinct storage and credentials; prevent
production traffic, jobs, emails, and webhooks from reaching it. Match required
versions, roles, extensions, and configuration. Use `psql -X` with
`ON_ERROR_STOP=on` for plain SQL or the installed `pg_restore` failure controls
for archive formats. Check every restore error; a partial restore is not ready.

Source checked 2026-10-01: [PostgreSQL SQL dumps and restore](https://www.postgresql.org/docs/current/backup-dump.html).

Verify required schema and representative records, then exercise application
reads and writes against the isolated target. Record artifact identity,
restored recovery point, elapsed time, failures, and application checks. A file,
checksum, or successful backup command alone does not prove recoverability.
Report a failed or unexercised restore as NOT VERIFIED or INCONCLUSIVE; preserve
evidence, fix the cause, and repeat the drill before claiming recovery readiness.

## Rollback

Record previous image/release and configuration, migration state, persistent
data compatibility, and the decision point before deploying. Reverting an image
does not revert schema or data. If the prior release cannot run against the
current schema, use the agreed forward fix or separately tested data recovery;
do not improvise a down migration or restore over the live database.

State writes that would be lost, accepted downtime, and the user's authorization
before destructive recovery. Preserve the failed release's logs and relevant
data. Apply rollback to the named service and recheck dependency readiness,
external application behavior, and job processing before declaring recovery.
