#!/bin/bash
# Start ontology editor locally (with write support)

PORT=8766
URL="http://127.0.0.1:${PORT}/editor.html"

(sleep 1 && open "${URL}") &

echo "  Ontology editor  ->  ${URL}"
echo "  Ctrl-C to stop"
python3 scripts/editor-server.py ${PORT}
