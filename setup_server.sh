#!/bin/bash
# EduAI Pro - VPS Setup Script for Eskiz.uz
# Run this script from /var/www/eduai after cloning the repo:
#   cd /var/www/eduai && git pull && bash setup_server.sh
set -e

echo "======================================"
echo "  EduAI Pro - VPS Setup Starting..."
echo "======================================"

# --- 1. Update system and install dependencies ---
echo "[1/8] Installing system packages..."
apt-get update -y
apt-get install -y python3-pip python3-venv python3.10-venv postgresql postgresql-contrib nginx git curl certbot python3-certbot-nginx

# --- 2. Setup PostgreSQL ---
echo "[2/8] Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE eduai_db;" 2>/dev/null || echo "DB already exists"
sudo -u postgres psql -c "CREATE USER eduai_user WITH PASSWORD 'EduAiSecure2026!';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE eduai_db TO eduai_user;"
sudo -u postgres psql -c "ALTER DATABASE eduai_db OWNER TO eduai_user;"
echo "PostgreSQL ready."

# --- 3. Create .env file interactively ---
echo ""
echo "[3/8] Setting up .env file..."
echo "Enter your API keys below. Press Enter to skip optional keys."
echo ""
read -p "GROQ_API_KEY (required - for AI features): " GROQ_KEY
read -p "TELEGRAM_BOT_TOKEN (for parent notifications): " TG_TOKEN
read -p "GOOGLE_CLIENT_ID (optional - for Google login): " G_ID
read -p "GOOGLE_CLIENT_SECRET (optional - for Google login): " G_SECRET

cat > /var/www/eduai/.env << ENVEOF
SECRET_KEY=EduAiProSuperSecretKey2026XYZ
DATABASE_URL=postgresql://eduai_user:EduAiSecure2026!@localhost/eduai_db
GROQ_API_KEY=${GROQ_KEY}
TELEGRAM_BOT_TOKEN=${TG_TOKEN}
GOOGLE_CLIENT_ID=${G_ID}
GOOGLE_CLIENT_SECRET=${G_SECRET}
FLASK_ENV=production
ENVEOF
echo ".env file created."

# --- 4. Setup Python virtual environment ---
echo "[4/8] Setting up Python venv..."
cd /var/www/eduai
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Python packages installed."

# --- 5. Initialize database tables ---
echo "[5/8] Creating database tables..."
python3 << PYEOF
import os, sys
sys.path.insert(0, '/var/www/eduai')
os.chdir('/var/www/eduai')
from dotenv import load_dotenv
load_dotenv()
from app import app, db
with app.app_context():
    db.create_all()
    print('All database tables created!')
PYEOF

# --- 6. Create Gunicorn systemd service ---
echo "[6/8] Creating systemd service..."
cat > /etc/systemd/system/eduai.service << SVCEOF
[Unit]
Description=EduAI Pro Flask Application
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/var/www/eduai
Environment=PATH=/var/www/eduai/venv/bin
EnvironmentFile=/var/www/eduai/.env
ExecStart=/var/www/eduai/venv/bin/gunicorn --workers 3 --bind unix:/var/www/eduai/eduai.sock --timeout 120 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable eduai
systemctl start eduai
echo "Systemd service started."

# --- 7. Configure Nginx ---
echo "[7/8] Configuring Nginx..."
cat > /etc/nginx/sites-available/eduai << NGEOF
server {
    listen 80;
    server_name eduai-pro.uz www.eduai-pro.uz;

    client_max_body_size 50M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/eduai/eduai.sock;
        proxy_read_timeout 120;
        proxy_connect_timeout 120;
    }

    location /static {
        alias /var/www/eduai/static;
        expires 30d;
    }
}
NGEOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/eduai /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
echo "Nginx configured."

# --- 8. Done - Show next steps ---
echo "[8/8] Finishing up..."
echo ""
echo "======================================"
echo "  EduAI Pro Setup Complete!"
echo "======================================"
echo ""
SERVERIP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo "Server IP: $SERVERIP"
echo ""
echo "NEXT STEPS for Domain & SSL:"
echo "1. Go to your domain registrar for eduai-pro.uz"
echo "2. Add DNS A record:   @   -> $SERVERIP"
echo "3. Add DNS A record:   www -> $SERVERIP"
echo "4. Wait 5-30 minutes for DNS to propagate"
echo "5. Then run this command for free SSL:"
echo "   certbot --nginx -d eduai-pro.uz -d www.eduai-pro.uz --agree-tos -m arifovjavohir9@gmail.com --non-interactive"
echo ""
echo "App status:"
systemctl status eduai --no-pager | head -15
