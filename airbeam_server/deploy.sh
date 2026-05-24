#!/bin/bash
# AirBeam Research — One-command setup script
# Run this on the server after cloning the repo:
#   chmod +x deploy.sh && ./deploy.sh

set -e

echo "🌬️  AirBeam Research — Server Setup"
echo "====================================="

# Install Python dependencies
echo "→ Installing Python dependencies..."
pip3 install -r requirements.txt --break-system-packages

# Create a systemd service so the app starts automatically on reboot
SERVICE_FILE="/etc/systemd/system/airbeam.service"
WORK_DIR="$(pwd)"
PYTHON="$(which python3)"

echo "→ Creating systemd service..."
sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=AirBeam Research Dashboard
After=network.target

[Service]
WorkingDirectory=$WORK_DIR
ExecStart=$PYTHON $WORK_DIR/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable airbeam
sudo systemctl start airbeam

echo ""
echo "✓ Done! AirBeam is running on port 5000."
echo ""
echo "Next step — set up Nginx to proxy it to your domain:"
echo "  sudo nano /etc/nginx/sites-available/airbeam"
echo ""
echo "Paste this config (replace YOUR_DOMAIN with your actual domain):"
echo "---"
cat << 'NGINX'
server {
    listen 80;
    server_name YOUR_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
NGINX
echo "---"
echo ""
echo "Then run:"
echo "  sudo ln -s /etc/nginx/sites-available/airbeam /etc/nginx/sites-enabled/"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo "For HTTPS (recommended), run:"
echo "  sudo apt install certbot python3-certbot-nginx -y"
echo "  sudo certbot --nginx -d YOUR_DOMAIN"
