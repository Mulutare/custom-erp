FROM odoo@sha256:4872f23288454b724fd2d26c176a418276c2b3552e9aa752f9396b59d864b3a0

USER root
COPY requirements-app.txt /tmp/requirements-app.txt
RUN python3 -m pip install --no-cache-dir --break-system-packages \
    --requirement /tmp/requirements-app.txt \
    && rm /tmp/requirements-app.txt

COPY --chown=odoo:odoo addons/ /mnt/extra-addons/
USER odoo
