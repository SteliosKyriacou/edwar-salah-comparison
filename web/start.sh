#!/bin/bash
# Start the Drug Success Predictor web app on port 4003
# Backend (FastAPI) on 8001, Frontend (Vite) on 4003 with proxy to backend

set -e
export PYTHONUNBUFFERED=1
DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill anything on ports 4003 and 8001
pkill -9 -f "uvicorn.*8001" || true
pkill -9 -f "vite" || true
sleep 1

echo "Starting backend on :8001..."
conda run -n edwar-salah uvicorn main:app --host 0.0.0.0 --port 8001 \
  --app-dir "$DIR/backend" &
BACKEND_PID=$!

echo "Starting frontend on :4003..."
cd "$DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  App running at: https://willyourdrugsucceedintheclinic.stylianoskyriacou.ai"
echo "  Dashboard:      https://willyourdrugsucceedintheclinic.stylianoskyriacou.ai/dashboard"
echo "  Backend API:    http://localhost:8001/api/health"
echo ""
echo "  Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
