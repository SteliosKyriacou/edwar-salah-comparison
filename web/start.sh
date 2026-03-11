#!/bin/bash
# Start the Drug Success Predictor web app on port 5173
# Backend (FastAPI) on 8000, Frontend (Vite) on 5173 with proxy to backend

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill anything on ports 5173 and 8000
lsof -ti:5173 -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

echo "Starting backend on :8000..."
conda run -n edward_salah uvicorn main:app --host 0.0.0.0 --port 8000 \
  --app-dir "$DIR/backend" &
BACKEND_PID=$!

echo "Starting frontend on :5173..."
cd "$DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "  App running at: http://localhost:5173"
echo "  Backend API at: http://localhost:8000/api/health"
echo ""
echo "  Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
