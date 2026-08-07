#!/bin/bash
# Restart the Drug Success Predictor web app

DIR="$(cd "$(dirname "$0")" && pwd)"

# Resolve the instance's current external IP (ephemeral: changes on stop/start)
HOST_IP="$(curl -s -m 2 -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip' \
  2>/dev/null)"
[ -z "$HOST_IP" ] && HOST_IP="localhost"

echo "Stopping..."
bash "$DIR/stop.sh"
sleep 2

echo "Starting..."
nohup bash "$DIR/start.sh" > /tmp/web-app.log 2>&1 &

sleep 4
echo ""
echo "  App running at: http://$HOST_IP:4003"
echo "  Dashboard:      http://$HOST_IP:4003/dashboard"
echo "  Logs:           /tmp/web-app.log"
