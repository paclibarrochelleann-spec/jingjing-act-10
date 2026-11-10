#!/usr/bin/env bash
# Lab 10, Steps 4-11 in one go, for jingjing's app.
# Run on the Lightsail Ubuntu server (browser SSH):   bash setup_server.sh https://github.com/OWNER/jingjing-act-10.git
# Safe to re-run. It never overwrites an existing students.db.
set -euo pipefail

REPO_URL="${1:?Usage: bash setup_server.sh https://github.com/OWNER/jingjing-act-10.git}"
APP_NAME="$(basename "$REPO_URL" .git)"
APP_DIR="$HOME/$APP_NAME"
RUN_USER="$(whoami)"

echo "== Step 4: update Ubuntu and install software"
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx
python3 --version; git --version; nginx -v

echo "== Step 5: clone the repository"
cd "$HOME"
[ -d "$APP_DIR" ] || git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"
ls

echo "== Step 6: virtual environment and requirements"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "== Step 7: practice database"
if [ -f students.db ]; then echo "students.db already exists, leaving it alone"; else ./venv/bin/python init_db.py; fi
ls

echo "== Step 9: quick Gunicorn check"
./venv/bin/gunicorn --bind 127.0.0.1:8000 app:app --daemon --pid /tmp/gunicorn-check.pid
sleep 2
curl -s -o /dev/null -w "Gunicorn answered with HTTP %{http_code}\n" http://127.0.0.1:8000/
kill "$(cat /tmp/gunicorn-check.pid)"

echo "== Step 10: systemd service"
sudo tee /etc/systemd/system/flaskapp.service >/dev/null <<SERVICE
[Unit]
Description=Gunicorn service for Flask application
After=network.target

[Service]
User=$RUN_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload
sudo systemctl restart flaskapp
sudo systemctl enable flaskapp
sudo systemctl --no-pager status flaskapp | head -n 12

echo "== Step 11: Nginx reverse proxy"
sudo tee /etc/nginx/sites-available/flaskapp >/dev/null <<'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/flaskapp
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo
echo "Done. Open  http://YOUR-PUBLIC-IP/  in a browser (Lightsail Networking must allow TCP 80)."
