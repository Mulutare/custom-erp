# Controlled update and rollback

## Update

1. Approve an immutable full Git SHA and review addon/module changes.
2. Verify the current revision, clean tree, health, capacity, and backup destination.
3. Run and verify a complete database + filestore backup.
4. Fetch the approved revision without an uncontrolled merge; inspect the diff and
   check it out only during the change window.
5. Update `RELEASE_REVISION`, render config, and build the pinned image.
6. Determine the smallest explicit comma-separated module upgrade list. Do not use
   `-u all` by default.
7. Run `update.sh`, which requires the backup and typed revision confirmation.
8. Start services, run health checks, inspect logs, and smoke-test critical roles and
   Sales/Purchase/Inventory/Finance workflows.
9. Retain the previous image/source and matching complete backup until acceptance.

## Rollback

Stop and assess whether the update changed schema or business data. If it did not,
an approved prior image may be sufficient. If it did—or this is uncertain—restore
the previous source/image **and** its matching database dump and filestore archive.
Application-code rollback alone can corrupt or misinterpret migrated data.

The tracked `rollback.sh` deliberately refuses automation. The operator must declare
the outage, identify the exact complete backup, obtain destructive-restore approval,
restore into an isolated name where possible, verify it, then switch service access.
Record revision, backup manifest, timestamps, approver, validation, and outcome.
