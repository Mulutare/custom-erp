# Production precheck

> **GO-LIVE BLOCKED PENDING PROFESSIONAL ACCOUNTING VALIDATION.** Infrastructure
> preparation does not approve Ethiopian accounting or statutory compliance.

## Inputs required from the server owner

- Server IP, FQDN (normally `erp.<domain>`), DNS control, and intended hostname.
- CPU cores, RAM, disk size/type/free space, expected concurrent users, and cron load.
- OS, cPanel/WHM version, EasyApache profile, Apache/Nginx topology, and AutoSSL status.
- Root SSH availability, firewall manager, Docker support, and backup destination.
- SMTP host, port, encryption, sender, service username, and DNS ownership for SPF,
  DKIM, and DMARC.

## Read-only checks

1. Install supported Docker Engine, Compose v2, Git, and Python 3.
2. Clone the repository at the approved full commit SHA.
3. Copy `deployment/env/.env.production.example` to the ignored
   `deployment/env/.env.production`; replace every placeholder and set mode 0600.
4. Create `/srv/passiontech/backups`, owned by the deployment operator and mode
   0700. Place backups on storage monitored independently from the application disk.
   Set `MIN_FREE_DISK_GB` to the approved operating floor; preflight fails below it.
5. Run:

   ```sh
   deployment/scripts/preflight.sh deployment/env/.env.production
   ```

The script checks Docker/Compose, source revision, required files, rendered config,
backup write access, CPU, RAM, disk, and relevant listening ports. It does not
change DNS, firewall, WHM, or start services.

## Worker sizing

Finalize values only after server sizing. Start conservatively: reserve RAM for
PostgreSQL, the OS, cPanel, and the web server; estimate roughly one worker per
active request plus cron capacity. Odoo's common CPU ceiling of approximately
`(2 × CPU cores) + 1` is an upper bound, not a target. Confirm that
`workers × ODOO_LIMIT_MEMORY_SOFT` fits the RAM remaining after those reserves.
Use at least one cron thread if scheduled work is enabled. Load-test and monitor
before increasing values.

## Security checklist

- `list_db=False`, strong unique master password, and unique DB credentials.
- PostgreSQL has no published port; Odoo 8069/8072 bind only to loopback.
- HTTPS only; port 80 is limited to redirect/AutoSSL challenges.
- Secrets, certificates, dumps, archives, runtime config, and backups are outside Git.
- Restricted root/SSH access, least-privilege file ownership, firewall enabled.
- WHM, OS, Docker, PostgreSQL image, and Odoo image updates follow change control.
- Backups are encrypted at the storage/transport layer where required and restores
  are tested regularly.

## Cleanup item

The deleted test database `office_db_restore_gate` no longer exists. Its 771-file
filestore was confirmed at `/var/lib/odoo/filestore/office_db_restore_gate`.
Before cleanup, re-check the database absence and ensure the path is not a link:

```sh
docker compose exec -T db psql -U odoo -d postgres -Atc \
  "SELECT datname FROM pg_database WHERE datname='office_db_restore_gate'"
docker compose exec -T odoo sh -c \
  'test -d /var/lib/odoo/filestore/office_db_restore_gate && test ! -L /var/lib/odoo/filestore/office_db_restore_gate'
```

If the first command prints nothing and the second succeeds, an authorized server
operator may remove exactly that path using the volume's owning UID:

```sh
docker compose exec --user root -T odoo rm -rf -- \
  /var/lib/odoo/filestore/office_db_restore_gate
```

Never broaden that command and never target `office-db` or the release backup.
