# PassionTech ERP native Linux deployment (Odoo 19 Community)

> **PREPARATION ONLY - DO NOT DEPLOY WITHOUT AN APPROVED CHANGE WINDOW.**
>
> **GO-LIVE REMAINS BLOCKED PENDING PROFESSIONAL ACCOUNTING VALIDATION.**
> Private infrastructure may be staged, but public operational use requires the
> approvals and release gates in `PRODUCTION_RELEASE_GATE.md`.

This runbook provides a non-Docker alternative to `PRODUCTION_DEPLOYMENT.md`.
It runs Odoo 19 Community from pinned source under systemd, with PostgreSQL on
the same Linux host. It does not replace or modify the Docker package.

## Supported reference layout

The commands target a clean Ubuntu 24.04 LTS or Debian 12 server with root/sudo
access. Odoo 19 requires PostgreSQL 13 or newer. Confirm all package names and
the OS support lifecycle before the deployment window.

```text
Internet
  -> TCP 443 (80 only for redirect/certificate validation)
  -> cPanel/WHM-managed Apache TLS frontend
  -> 127.0.0.1:8069 Odoo HTTP
     127.0.0.1:8072 Odoo websocket/gevent
  -> local PostgreSQL (loopback/Unix socket only; never public)

/srv/passiontech/app       approved PassionTech repository revision
/opt/odoo/19.0             approved Odoo Community source revision
/opt/odoo/venv             isolated Python environment
/var/lib/odoo              Odoo data and filestore
/etc/odoo/odoo.conf        production configuration and secrets
/var/log/odoo              Odoo logs
/srv/passiontech/backups   protected DB + filestore backups
```

## Values that must be approved first

Record these in the change ticket. Do not use a moving branch or `latest` build.

```sh
PASSIONTECH_SHA=<APPROVED_FULL_COMMIT_SHA>
ODOO_UPSTREAM_SHA=<TESTED_FULL_ODOO_19_COMMUNITY_COMMIT_SHA>
DB_NAME=passiontech_prod
DB_USER=passiontech_odoo
ERP_FQDN=erp.example.com
```

`PASSIONTECH_SHA` must pass `PRODUCTION_RELEASE_GATE.md`. The upstream Odoo SHA
must be tested with that application revision and retained for rollback. Keep
database, Odoo source, custom addons, and filestore versions together.

## 1. Provision and harden the host

1. Patch the OS and WHM/cPanel using vendor-supported methods.
2. Confirm CPU, RAM, disk, backup storage, and the actual Apache/Nginx topology.
3. Configure SSH keys, least-privilege sudo, time synchronization, monitoring,
   and a host firewall.
4. Permit public 443 and only the minimum use of port 80. Never expose 5432,
   8069, or 8072.
5. Create a non-login service account and required directories:

   ```sh
   sudo adduser --system --group --home /var/lib/odoo odoo
   sudo install -d -o root -g root -m 0755 /srv/passiontech /opt/odoo
   sudo install -d -o odoo -g odoo -m 0750 /var/lib/odoo /var/log/odoo
   sudo install -d -o root -g odoo -m 0750 /etc/odoo
   sudo install -d -o root -g root -m 0700 /srv/passiontech/backups
   ```

## 2. Install OS prerequisites

Install Git, Python tooling, PostgreSQL, build tools, LDAP/XML/image libraries,
fonts, Node tooling required by Odoo assets, and log rotation:

```sh
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip python3-dev \
  build-essential pkg-config libpq-dev libldap2-dev libsasl2-dev libssl-dev \
  libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev libffi-dev liblcms2-dev \
  libblas-dev libatlas-base-dev postgresql postgresql-client nodejs npm \
  fontconfig fonts-dejavu-core logrotate curl ca-certificates
sudo npm install -g rtlcss
```

Install the patched `wkhtmltopdf` 0.12.6 build appropriate for the exact OS and
CPU architecture, verify its package checksum/signature, then confirm:

```sh
wkhtmltopdf --version
```

Odoo documents 0.12.6 as necessary for PDF headers and footers. Do not download
an unverified binary or substitute a random build.

## 3. Install pinned Odoo and PassionTech source

Clone into temporary sibling directories, verify the expected SHAs, and only
then place them at their final paths. Do not install Enterprise code.

```sh
sudo git clone --branch 19.0 --single-branch \
  https://github.com/odoo/odoo.git /opt/odoo/19.0
sudo git -C /opt/odoo/19.0 checkout --detach "$ODOO_UPSTREAM_SHA"
test "$(git -C /opt/odoo/19.0 rev-parse HEAD)" = "$ODOO_UPSTREAM_SHA"

sudo git clone <APPROVED_REPOSITORY_URL> /srv/passiontech/app
sudo git -C /srv/passiontech/app checkout --detach "$PASSIONTECH_SHA"
test "$(git -C /srv/passiontech/app rev-parse HEAD)" = "$PASSIONTECH_SHA"
sudo test -z "$(git -C /srv/passiontech/app status --porcelain)"
```

Create an isolated Python environment and install Odoo's pinned requirements
plus this repository's addon requirements:

```sh
sudo python3 -m venv /opt/odoo/venv
sudo /opt/odoo/venv/bin/python -m pip install --upgrade pip wheel setuptools
sudo /opt/odoo/venv/bin/python -m pip install \
  -r /opt/odoo/19.0/requirements.txt \
  -r /srv/passiontech/app/requirements-app.txt
sudo chown -R root:root /opt/odoo/19.0 /opt/odoo/venv /srv/passiontech/app
sudo chmod -R a-w /opt/odoo/19.0 /opt/odoo/venv /srv/passiontech/app
```

If dependency compilation fails, stop and resolve the missing OS package in a
staging environment. Do not weaken version pins or use `--break-system-packages`.

## 4. Configure PostgreSQL

Keep PostgreSQL bound locally and use SCRAM authentication. Generate a unique
database password offline; never place it in shell history, source control, or
this document. As the PostgreSQL administrator, create the least-privilege role
and database through an approved secure session:

```sql
CREATE ROLE passiontech_odoo LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT PASSWORD '<UNIQUE_DATABASE_PASSWORD>';
CREATE DATABASE passiontech_prod OWNER passiontech_odoo
  ENCODING 'UTF8' TEMPLATE template0;
REVOKE ALL ON DATABASE passiontech_prod FROM PUBLIC;
```

Confirm `listen_addresses` is limited to loopback (or use only the Unix socket),
password encryption is SCRAM, and `pg_hba.conf` permits only the required local
connection. Validate and reload PostgreSQL using the OS service tools. Do not
grant the Odoo role superuser, role creation, or unrestricted database creation.

## 5. Configure Odoo

Generate `/etc/odoo/odoo.conf` offline with mode `0640`, owner `root:odoo`:

```ini
[options]
admin_passwd = <STRONG_UNIQUE_MASTER_PASSWORD>
db_host = 127.0.0.1
db_port = 5432
db_user = passiontech_odoo
db_password = <UNIQUE_DATABASE_PASSWORD>
db_name = passiontech_prod
dbfilter = ^passiontech_prod$
list_db = False
proxy_mode = True
http_interface = 127.0.0.1
http_port = 8069
gevent_port = 8072
addons_path = /opt/odoo/19.0/odoo/addons,/opt/odoo/19.0/addons,/var/lib/odoo/addons/19.0,/srv/passiontech/app/addons
data_dir = /var/lib/odoo
workers = <SIZED_INTEGER>
max_cron_threads = <SIZED_INTEGER>
limit_memory_soft = <SIZED_BYTES>
limit_memory_hard = <SIZED_BYTES>
limit_time_cpu = 120
limit_time_real = 240
log_level = info
log_handler = :INFO,werkzeug:WARNING
logfile = /var/log/odoo/odoo.log
without_demo = True
```

Size worker and memory values from measured server capacity and expected
concurrency. Confirm the service account can read the configuration but other
users cannot:

```sh
sudo chown root:odoo /etc/odoo/odoo.conf
sudo chmod 0640 /etc/odoo/odoo.conf
sudo -u odoo test -r /etc/odoo/odoo.conf
```

## 6. Create the systemd service

Create `/etc/systemd/system/odoo19.service`:

```ini
[Unit]
Description=PassionTech ERP - Odoo 19 Community
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
WorkingDirectory=/opt/odoo/19.0
ExecStart=/opt/odoo/venv/bin/python /opt/odoo/19.0/odoo-bin -c /etc/odoo/odoo.conf
Restart=on-failure
RestartSec=5s
TimeoutStopSec=90s
KillSignal=SIGINT
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/odoo /var/log/odoo
UMask=0027

[Install]
WantedBy=multi-user.target
```

Validate before enabling it:

```sh
sudo systemd-analyze verify /etc/systemd/system/odoo19.service
sudo systemctl daemon-reload
```

Do not start Odoo until the database path below is selected.

## 7. Initialize or restore exactly one database path

### A. Fresh production bootstrap (recommended)

Run the reviewed module set once, without demo data:

```sh
sudo -u odoo /opt/odoo/venv/bin/python /opt/odoo/19.0/odoo-bin \
  -c /etc/odoo/odoo.conf --without-demo=all --stop-after-init \
  -i passiontech_branding,passiontech_core,passiontech_security,passiontech_financial_reports,l10n_et,purchase_stock,stock_account,stock_landed_costs,product_expiry,stock_picking_batch,stock_dropshipping,sale_margin,sale_loyalty,sale_product_matrix,purchase_product_matrix,purchase_requisition,account_debit_note,account_check_printing,crm,delivery,account_asset_management,account_financial_report,account_reconcile_oca,account_statement_base,account_statement_import_base,account_statement_import_file,account_statement_import_file_reconcile_oca,account_statement_import_sheet_file,account_statement_import_sheet_file_xlsx
```

Manually configure the approved legal identity, Ethiopia/ETB chart, warehouse,
journals, banks, sequences, taxes, fiscal positions, named roles, email, and
accountant-approved mappings. Never automate by numeric database IDs.

### B. Migrate tested `office-db`

Transfer a final matching PostgreSQL custom dump and filestore through protected
storage. Stop Odoo, restore into an empty database owned by `passiontech_odoo`,
place the matching filestore at:

```text
/var/lib/odoo/filestore/passiontech_prod
```

Set ownership to `odoo:odoo`, permissions to `0750` for directories and `0640`
for files, and upgrade only explicitly reviewed modules. This path carries all
development/demo records and accounting mappings; review them before go-live.

Never combine paths A and B. Never restore a database dump without its matching
filestore.

## 8. Start and validate privately

```sh
sudo systemctl enable --now odoo19
sudo systemctl status odoo19 --no-pager
curl --fail --silent --show-error http://127.0.0.1:8069/web/login >/dev/null
sudo ss -lntp | grep -E ':(5432|8069|8072)\b'
sudo journalctl -u odoo19 --since '1 hour ago' --no-pager
```

Confirm 5432, 8069, and 8072 listen only locally. Review Odoo logs for `ERROR`,
`CRITICAL`, and tracebacks. Configure logrotate for `/var/log/odoo/*.log` with
restricted permissions and a post-rotate service reload/restart tested in staging.

## 9. Configure the reverse proxy

Follow `CPANEL_WHM_DEPLOYMENT.md` and use the tracked
`deployment/proxy/apache-odoo.conf.example`. Do not edit WHM-generated Apache
files directly. Validate the generated configuration before restart.

Keep DNS unchanged during private validation. In the separately approved go-live
window, verify AutoSSL, HTTPS redirect behavior, forwarded headers, websocket
routing to 8072, proxy timeout, upload limit, and external port exposure.

## 10. Email, backups, and acceptance

1. Configure SMTP in Odoo with a dedicated least-privilege account; keep its
   credentials in Odoo's protected database configuration, not Git.
2. Verify SPF, DKIM, DMARC, TLS, delivery, bounce handling, and password reset.
3. Back up PostgreSQL with `pg_dump --format=custom` and archive the matching
   `/var/lib/odoo/filestore/passiontech_prod` while writes are stopped or blocked.
4. Store a manifest with application SHA, Odoo SHA, database name, timestamp,
   checksums, and tool versions. Mark a set complete only when both artifacts pass.
5. Encrypt and replicate complete sets off-host. Test restoration into an isolated
   database and filestore quarterly and after material platform changes.
6. Smoke-test login, attachments, company isolation, scheduled actions, email,
   reports, and the approved Sales/Purchase/Inventory/Finance role workflows.
7. Obtain the written accountant/tax approval and business-owner sign-off required
   by `PRODUCTION_RELEASE_GATE.md`. Only then authorize operational go-live.

## Native update and rollback

1. Approve immutable PassionTech and Odoo full SHAs.
2. Capture and verify a complete database + filestore backup.
3. Build a new source/venv release in sibling paths; never `git pull` over the
   running release.
4. Stop the service, switch only reviewed paths/configuration, and run the smallest
   explicit module upgrade list. Do not use `-u all` by default.
5. Start, health-check, inspect logs, and complete business smoke tests.
6. If schema or business data changed, rollback requires the prior source/venv
   **and** its matching database and filestore. Code-only rollback is unsafe.

Document every revision, backup manifest, timestamp, approver, validation result,
and outcome. A destructive production restore always requires separate approval.

## Official Odoo references

- Odoo 19 source installation: https://www.odoo.com/documentation/19.0/administration/on_premise/source.html
- Odoo 19 on-premise deployment: https://www.odoo.com/documentation/19.0/administration/on_premise/deploy.html
- Odoo 19 Python requirements: https://github.com/odoo/odoo/blob/19.0/requirements.txt

