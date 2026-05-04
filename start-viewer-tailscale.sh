#!/bin/bash
# Start ontology viewer bound to Tailscale IP (accessible to other devices on tailnet)

HOST=100.115.183.48
PORT=8765
URL="http://${HOST}:${PORT}/viewer/"

(sleep 1 && open "${URL}") &

echo "  Ontology viewer  →  ${URL}"
echo "  Ctrl-C to stop"
python3 -m http.server ${PORT} --bind ${HOST}
