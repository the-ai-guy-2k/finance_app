#!/bin/bash
set -euo pipefail

LOG="/var/log/financial-app-bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== SPE-01 bootstrap started: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

APP_DIR="/opt/financial-app"
CONFIG_FILE="$APP_DIR/config.json"
ENV_FILE="$APP_DIR/env"
DOCKER_IMAGE="${docker_image}"

dnf update -y
dnf install -y docker

systemctl enable docker
systemctl start docker

mkdir -p "$APP_DIR/data" "$APP_DIR/uploads" "$APP_DIR/logs"
chmod 700 "$APP_DIR"

cat > "$CONFIG_FILE" <<'EOF'
{
  "flask": {
    "secret_key": "spe01-demo-secret-change-if-reused"
  },
  "openai": {
    "model": "gpt-4o-mini"
  },
  "upload": {
    "folder": "uploads",
    "max_size_mb": 10,
    "allowed_receipt_formats": ["png", "jpg", "jpeg", "webp"],
    "allowed_csv_format": "csv"
  },
  "data": {
    "folder": "data"
  }
}
EOF

chmod 600 "$CONFIG_FILE"

if [ -n "${openai_api_key_b64}" ]; then
  decoded_key="$(echo "${openai_api_key_b64}" | base64 -d)"
  printf 'OPENAI_API_KEY=%s\n' "$decoded_key" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  unset decoded_key
  echo "OpenAI API key written to $ENV_FILE from Terraform variable."
else
  cat > "$ENV_FILE" <<'EOF'
# Set your OpenAI API key here, then restart the service:
#   sudo systemctl restart financial-app
OPENAI_API_KEY=
EOF
  chmod 600 "$ENV_FILE"
  echo "WARNING: OPENAI_API_KEY not provided at apply time."
  echo "Operator must edit $ENV_FILE and restart financial-app.service."
fi

echo "Pulling Docker image: $DOCKER_IMAGE"
docker pull "$DOCKER_IMAGE"

cat > /etc/systemd/system/financial-app.service <<EOF
[Unit]
Description=Financial Nebula Node (SPE-01)
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=10
EnvironmentFile=$ENV_FILE
ExecStartPre=-/usr/bin/docker stop financial-app
ExecStartPre=-/usr/bin/docker rm financial-app
ExecStart=/usr/bin/docker run --name financial-app \\
  --rm \\
  -p 80:5000 \\
  -e OPENAI_API_KEY \\
  -v $CONFIG_FILE:/app/config.json:ro \\
  -v $APP_DIR/data:/app/data \\
  -v $APP_DIR/uploads:/app/uploads \\
  -v $APP_DIR/logs:/app/logs \\
  $DOCKER_IMAGE
ExecStop=/usr/bin/docker stop financial-app

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable financial-app.service
systemctl restart financial-app.service

echo "=== SPE-01 bootstrap complete: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "App should be reachable on port 80 after the container starts."
