#!/bin/sh
set -e

# ==============================================================================
# Container Entrypoint: Volume Permissions & Privilege Drop
# Ensures persistent volumes mounted at /app/data are writable by non-root appuser
# ==============================================================================

# Ensure storage directories exist inside the mounted volume
mkdir -p "${DATA_DIR:-/app/data}/raw_documents" \
         "${DATA_DIR:-/app/data}/vector_store" \
         "${DATA_DIR:-/app/data}/eval_datasets"

# Ensure the unprivileged appuser (UID 1000) owns the data directory
chown -R appuser:appuser "${DATA_DIR:-/app/data}"

# Drop root privileges and execute application command as appuser
if command -v gosu >/dev/null 2>&1; then
    exec gosu appuser "$@"
else
    exec su -s /bin/sh appuser -c "$*"
fi
