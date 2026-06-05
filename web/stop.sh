#!/bin/bash
# Stop the Drug Success Predictor web app

echo "Stopping backend (8000) and frontend (5173)..."
lsof -ti:5173 -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
echo "Stopped."
