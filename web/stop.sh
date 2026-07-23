#!/bin/bash
# Stop the Drug Success Predictor web app

echo "Stopping backend (8001) and frontend (4003)..."
pkill -9 -f "uvicorn.*8001" || true
pkill -9 -f "vite" || true
echo "Stopped."
