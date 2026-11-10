#!/usr/bin/env bash
# Lab 10, Step 17: basic troubleshooting commands. Run on the server.
sudo systemctl status flaskapp --no-pager
sudo journalctl -u flaskapp --no-pager -n 50
sudo systemctl status nginx --no-pager
sudo nginx -t
echo "--- Gunicorn directly:";  curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8000
echo "--- Through Nginx:";      curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost
ls
pwd
