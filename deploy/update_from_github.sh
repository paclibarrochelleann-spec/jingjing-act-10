#!/usr/bin/env bash
# Lab 10, Step 16: pull the latest code from GitHub and restart the service.
# Run on the server from anywhere:   bash ~/jingjing-act-10/deploy/update_from_github.sh
set -euo pipefail
cd "$(dirname "$0")/.."
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart flaskapp
sudo systemctl --no-pager status flaskapp | head -n 12
