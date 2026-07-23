#!/bin/bash
# Restart the Drug Success Predictor web app

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Stopping..."
bash "$DIR/stop.sh"
sleep 2

echo "Starting..."
nohup bash "$DIR/start.sh" > /tmp/web-app.log 2>&1 &

sleep 4
echo ""
echo "  App running at: http://136.119.133.178:4003"
echo "  Dashboard:      http://136.119.133.178:4003/dashboard"
echo "  Logs:           /tmp/web-app.log"
