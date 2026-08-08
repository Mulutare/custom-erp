# Production backup and restore

A complete ERP backup is one PostgreSQL custom dump plus the matching Odoo
filestore from the same database state. A dump alone is incomplete.

## Backup

`deployment/scripts/backup.sh` creates a mode-0700 timestamped directory with:

- `database.dump`
- `filestore.tar.gz`
- `manifest.txt` containing revision/database/time metadata
- `COMPLETE`, written only after both artifacts are non-empty

The script briefly pauses Odoo to prevent writes while `pg_dump` and the filestore
archive are captured, and its failure trap unpauses the service. Schedule it during
a quiet window and monitor completion; PostgreSQL remains available internally.

Run daily and before every update. A practical starting policy is 14–30 daily,
8–12 weekly, and 12 monthly copies, adjusted for legal/business requirements and
storage. `BACKUP_RETENTION_DAYS` only prints eligible candidates; the script does
not delete them automatically. Replicate complete sets to protected off-server
storage, encrypt in transit/at rest, restrict permissions, alert on failure, and
test restoration quarterly or after material platform changes.

## Restore

1. Declare an outage or restrict proxy access; confirm the backup `COMPLETE` marker.
2. Confirm database dump and filestore archive belong to the same backup directory.
3. Retain a safety backup of the current target before any replacement.
4. Prefer restoring into a new database name. The restore script refuses to
   overwrite an existing database and requires typed confirmation:

   ```sh
   deployment/scripts/restore.sh deployment/env/.env.production \
     /srv/passiontech/backups/<COMPLETE_BACKUP> <NEW_DATABASE_NAME>
   ```

5. The script stages the archived source filestore, renames it to the new database,
   refuses an existing destination, and applies Odoo ownership. Confirm permissions
   prevent unrelated host users reading it.
6. Start Odoo, run health checks, review ERROR/CRITICAL/Traceback logs, verify login,
   company identity, attachment download, and reports.
7. Upgrade only explicitly required modules after source/schema review. Never run an
   automatic blanket upgrade merely because a restore occurred.

Restoring over production is destructive and requires separate explicit operator
approval. Database and filestore must always move or roll back together.
