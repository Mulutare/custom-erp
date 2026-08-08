# cPanel/WHM reverse proxy

This runbook assumes Apache is the cPanel-managed public frontend. Confirm the
actual topology first: some servers use Nginx Manager or another proxy ahead of
Apache. Do not edit generated Apache files directly because WHM rebuilds them.

## Operator steps

1. Create the subdomain/account mapping for `erp.<domain>` in cPanel/WHM.
2. Point DNS to the server only when private validation is complete.
3. Confirm Apache modules `proxy`, `proxy_http`, `proxy_wstunnel`, and `headers`.
4. For the standard Apache userdata mechanism, create the domain-specific include
   directory (substituting the real cPanel user and FQDN), copy the reviewed proxy
   fragment, and preserve root ownership:

   ```sh
   install -d -m 0755 \
     /etc/apache2/conf.d/userdata/ssl/2_4/<CPANEL_USER>/<ERP_FQDN>
   install -m 0644 deployment/proxy/apache-odoo.conf.example \
     /etc/apache2/conf.d/userdata/ssl/2_4/<CPANEL_USER>/<ERP_FQDN>/passiontech.conf
   ```

   If the server's WHM version uses a different include hierarchy, stop and use its
   documented path rather than creating an unrecognized one.
5. Validate and rebuild using cPanel-supported tools, then restart only after the
   generated configuration passes:

   ```sh
   /scripts/rebuildhttpdconf
   /usr/local/apache/bin/apachectl -t
   /scripts/restartsrv_httpd
   ```
6. Run AutoSSL after DNS resolves; verify the certificate chain and renewal.
7. Force HTTP-to-HTTPS redirects without redirecting ACME/AutoSSL validation paths
   incorrectly.
8. Verify `Host`, `X-Forwarded-For`, `X-Forwarded-Proto=https`, websocket upgrade,
   600-second proxy timeout, and the chosen 128 MB upload limit.
9. From an external host, verify only 80/443 are reachable—not 5432/8069/8072.

The included Nginx example is optional and must be adapted to the installed WHM
topology; it is not a requirement. TLS terminates at the WHM frontend. No
certificate or private key belongs in this repository.
