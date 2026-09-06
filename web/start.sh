#!/bin/bash
# Start the websearch-enabled AlphaForge web app.
# Backend (FastAPI) on $BACKEND_PORT, frontend (Vite) on $FRONTEND_PORT with /api + /dashboard proxied.

set -e
export PYTHONUNBUFFERED=1
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/ports.env"

bash "$DIR/stop.sh"
sleep 1

echo "Starting backend on :$BACKEND_PORT..."
"$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" \
  --app-dir "$DIR/backend" &
BACKEND_PID=$!

echo "Starting frontend on :$FRONTEND_PORT..."
cd "$DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  App running at: http://$PUBLIC_HOST:$FRONTEND_PORT"
echo "  Dashboard:      http://$PUBLIC_HOST:$FRONTEND_PORT/dashboard"
echo "  Backend API:    http://localhost:$BACKEND_PORT/api/health"
echo ""
echo "  Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
