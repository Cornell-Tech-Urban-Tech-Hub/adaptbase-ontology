#!/bin/bash
# Start ontology viewer locally

PORT=8765
URL="http://127.0.0.1:${PORT}/viewer/"

(sleep 1 && open "${URL}") &

echo "  Ontology viewer  →  ${URL}"
echo "  Ctrl-C to stop"
python3 -m http.server ${PORT}
