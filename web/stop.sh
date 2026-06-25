#!/bin/bash
# Stop the Drug Success Predictor web app

echo "Stopping backend (8001) and frontend (5174)..."
lsof -ti:5174 -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true
echo "Stopped."
