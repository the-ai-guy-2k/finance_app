#!/bin/bash
set -euo pipefail

LOG="/var/log/financial-app-bootstrap.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== SPE-01 bootstrap started: $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

APP_DIR="/opt/financial-app"
CONFIG_FILE="$APP_DIR/config.json"
ENV_FILE="$APP_DIR/env"
DOCKER_IMAGE="${docker_image}"
AWS_REGION="${aws_region}"
OPENAI_SSM_PARAMETER_NAME="${openai_ssm_parameter_name}"
BOOTSTRAP_OPENAI_API_KEY="${bootstrap_openai_api_key}"

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
    "model": "gpt-4o-mini",
    "ssm_parameter_name": "SSM_PARAMETER_NAME_PLACEHOLDER"
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
sed -i "s|SSM_PARAMETER_NAME_PLACEHOLDER|$OPENAI_SSM_PARAMETER_NAME|g" "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"

cat > "$ENV_FILE" <<EOF
OPENAI_SSM_PARAMETER_NAME=$OPENAI_SSM_PARAMETER_NAME
AWS_REGION=$AWS_REGION
AWS_DEFAULT_REGION=$AWS_REGION
EOF
chmod 600 "$ENV_FILE"
if [ -n "$BOOTSTRAP_OPENAI_API_KEY" ]; then
  echo "OPENAI_API_KEY=$BOOTSTRAP_OPENAI_API_KEY" >> "$ENV_FILE"
  echo "OpenAI key supplied via bootstrap env (IAM/SSM instance profile unavailable)."
else
  echo "OpenAI key will be loaded from SSM parameter: $OPENAI_SSM_PARAMETER_NAME (not stored in env file)."
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
  -e OPENAI_SSM_PARAMETER_NAME \\
  -e OPENAI_API_KEY \\
  -e AWS_REGION \\
  -e AWS_DEFAULT_REGION \\
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
