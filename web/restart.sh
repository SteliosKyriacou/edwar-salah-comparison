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
echo "  App running at: http://71.136.137.86:5174"
echo "  Dashboard:      http://71.136.137.86:5174/dashboard"
echo "  Logs:           /tmp/web-app.log"
