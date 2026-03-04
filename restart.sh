#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Killing existing processes..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true
sleep 2

source ~/anaconda3/etc/profile.d/conda.sh
conda activate edwar-salah

echo "Starting FastAPI backend on 0.0.0.0:8000..."
cd "$PROJECT_DIR/web/backend"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
echo "FastAPI PID: $!"

echo "Starting Vite frontend on 0.0.0.0:5173..."
cd "$PROJECT_DIR/web/frontend"
nohup npx vite --host 0.0.0.0 > /tmp/vite.log 2>&1 &
echo "Vite PID: $!"

sleep 3
echo ""
echo "=== FastAPI ==="
tail -5 /tmp/fastapi.log
echo ""
echo "=== Vite ==="
tail -5 /tmp/vite.log
echo ""
echo "Done."
