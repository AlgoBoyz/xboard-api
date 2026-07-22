#!/bin/bash
# deploy-mcp.sh — Deploy Xboard Admin MCP Server to a production panel.
#
# Usage:
#   bash deploy-mcp.sh [--api-key <key>] [--base-url <url>] [--secure-path <path>]
#
# Defaults:
#   BASE_URL=http://127.0.0.1
#   SECURE_PATH=bfee17b1
#   API_KEY=auto-generated

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1}"
SECURE_PATH="${SECURE_PATH:-bfee17b1}"
API_KEY="${API_KEY:-$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")}"
INSTALL_DIR="/opt/xboard-mcp"
ENV_FILE="/etc/xboard-mcp.env"
SERVICE_FILE="/etc/systemd/system/xboard-mcp.service"

echo "=== Xboard MCP Server Deployment ==="
echo "  Install dir: $INSTALL_DIR"
echo "  Base URL:    $BASE_URL"
echo "  Secure path: $SECURE_PATH"

# 1. Create directory
sudo mkdir -p "$INSTALL_DIR"
sudo chown "$USER:$USER" "$INSTALL_DIR"

# 2. Copy source
if [ -d ./xboard_api ]; then
    cp -r ./xboard_api "$INSTALL_DIR/"
    cp xboard_mcp_server.py "$INSTALL_DIR/"
else
    echo "ERROR: Run from xboard-api/ directory (must contain xboard_api/ and xboard_mcp_server.py)"
    exit 1
fi

# 3. Install Python deps
pip3 install mcp python-dotenv requests --break-system-packages 2>/dev/null || \
    pip3 install mcp python-dotenv requests

# 4. Create env file
sudo tee "$ENV_FILE" > /dev/null << EOF
XBOARD_BASE_URL=$BASE_URL
XBOARD_SECURE_PATH=$SECURE_PATH
XBOARD_API_KEY=$API_KEY
XBOARD_MCP_HOST=127.0.0.1
XBOARD_MCP_PORT=9020
XBOARD_AUDIT_LOG=/var/log/xboard-mcp-audit.log
EOF
sudo chmod 600 "$ENV_FILE"

# 5. Create systemd service
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Xboard Admin API MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$ENV_FILE
ExecStart=/usr/bin/python3 $INSTALL_DIR/xboard_mcp_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now xboard-mcp
sudo systemctl status xboard-mcp --no-pager | head -6

# 7. Generate SSH key for MCP (if not exists)
SSH_KEY="$HOME/.ssh/xboard-mcp-prod"
if [ ! -f "$SSH_KEY" ]; then
    ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -q
    echo "  SSH key generated: $SSH_KEY"
    echo "  Public key (add to panel authorized_keys):"
    cat "${SSH_KEY}.pub"
fi

echo ""
echo "=== Deployment Complete ==="
echo "  API Key: $API_KEY"
echo "  Audit log: /var/log/xboard-mcp-audit.log"
echo ""
echo "  Test: curl -H 'X-API-Key: $API_KEY' http://127.0.0.1:9020/sse"
echo ""
echo "  opencode config snippet:"
echo '  "xboard-prod": {'
echo '    "command": ["ssh", "-o", "StrictHostKeyChecking=no", "-i", "'$SSH_KEY'", "user@panel-host", "python3", "'$INSTALL_DIR'/xboard_mcp_server.py"],'
echo '    "type": "local",'
echo '    "enabled": true'
echo '  }'
