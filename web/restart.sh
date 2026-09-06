#!/bin/bash
# Restart the websearch-enabled AlphaForge web app in the background.

DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/ports.env"

echo "Stopping..."
bash "$DIR/stop.sh"
sleep 2

echo "Starting..."
mkdir -p "$DIR/logs"
# Own session/process group so stop.sh can kill exactly this app and nothing else.
setsid nohup bash "$DIR/start.sh" > "$DIR/logs/web-app.log" 2>&1 &
APP_PID=$!
sleep 1
ps -o pgid= -p "$APP_PID" 2>/dev/null | tr -d ' ' > "$DIR/logs/app.pgid"

sleep 5
echo ""
echo "  App running at: http://$PUBLIC_HOST:$FRONTEND_PORT"
echo "  Dashboard:      http://$PUBLIC_HOST:$FRONTEND_PORT/dashboard"
echo "  Logs:           $DIR/logs/web-app.log"
