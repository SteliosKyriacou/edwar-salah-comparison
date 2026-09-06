#!/bin/bash
# Stop ONLY this checkout's web app (backend 8101 / frontend 4103).
# Deliberately does not use `pkill -f vite` or `pkill -f uvicorn`: another
# instance of this app runs from /home/stelios/repos/edwar-salah-comparison.

DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/ports.env"
PGID_FILE="$DIR/logs/app.pgid"

echo "Stopping backend ($BACKEND_PORT) and frontend ($FRONTEND_PORT)..."

# 1) Kill the process group recorded by restart.sh (backend + vite + wrappers).
if [ -f "$PGID_FILE" ]; then
  PGID="$(cat "$PGID_FILE")"
  if [ -n "$PGID" ]; then kill -9 -"$PGID" 2>/dev/null || true; fi
  rm -f "$PGID_FILE"
fi

# 2) Fallback: kill whatever still holds our two ports, and nothing else.
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  pids="$(ss -ltnpH "sport = :$port" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | sort -u)"
  if [ -n "$pids" ]; then
    echo "  freeing :$port (pids: $(echo $pids | tr '\n' ' '))"
    kill -9 $pids 2>/dev/null || true
  fi
done

echo "Stopped."
