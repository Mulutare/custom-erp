#!/usr/bin/env sh
set -eu
cat <<'EOF'
Rollback is intentionally not automatic.
Application-only rollback is unsafe after schema or data changes.
Select the approved previous Git revision/image AND its matching complete
database plus filestore backup. Follow docs/UPDATE_ROLLBACK.md and use
restore.sh only after explicit outage and destructive-restore approval.
EOF
exit 1
