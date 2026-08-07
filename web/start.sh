#!/bin/bash
# Start the Drug Success Predictor web app on port 4003
# Backend (FastAPI) on 8001, Frontend (Vite) on 4003 with proxy to backend

set -e
export PYTHONUNBUFFERED=1
DIR="$(cd "$(dirname "$0")" && pwd)"

# Resolve the instance's current external IP (ephemeral: changes on stop/start)
HOST_IP="$(curl -s -m 2 -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip' \
  2>/dev/null)"
[ -z "$HOST_IP" ] && HOST_IP="localhost"

# Kill anything on ports 4003 and 8001
pkill -9 -f "uvicorn.*8001" || true
pkill -9 -f "vite" || true
sleep 1

echo "Starting backend on :8001..."
"$DIR/venv/bin/uvicorn" main:app --host 0.0.0.0 --port 8001 \
  --app-dir "$DIR/backend" &
BACKEND_PID=$!

echo "Starting frontend on :4003..."
cd "$DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  App running at: http://$HOST_IP:4003"
echo "  Dashboard:      http://$HOST_IP:4003/dashboard"
echo "  Backend API:    http://localhost:8001/api/health"
echo ""
echo "  Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
