#!/bin/bash
# Start ontology viewer with local HTTP server

PORT=8765
URL="http://127.0.0.1:${PORT}/viewer.html"

echo "=========================================="
echo "  Resilience Ontology Viewer"
echo "=========================================="
echo ""
echo "Starting server on port ${PORT}..."
echo "Viewer URL: ${URL}"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Open browser after a short delay
(sleep 2 && open "${URL}") &

# Start Python HTTP server in current directory
python3 -m http.server ${PORT} --bind 127.0.0.1
