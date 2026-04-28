#!/usr/bin/env python3
"""Local dev server for the ontology editor.

Serves static files normally (GET) and exposes two POST endpoints
for writing ontology versions and vocabulary files to disk.

Endpoints:
  POST /api/save-ontology  {version, data, versions_entry}
  POST /api/save-vocab     {filename, data}
  GET  /api/vocab-files    lists schemas/vocabularies/*.json
"""

import json
import os
import re
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

ALLOWED_VOCAB_FILES = re.compile(r'^[a-z0-9_-]+\.json$')
ALLOWED_VERSION = re.compile(r'^v\d+\.\d+(\.\d+)?$')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class EditorHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/save-ontology':
            self._save_ontology()
        elif self.path == '/api/save-vocab':
            self._save_vocab()
        else:
            self._json_error(404, 'Unknown endpoint')

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/vocab-files':
            self._list_vocab_files()
        else:
            super().do_GET()

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        return json.loads(raw)

    def _json_response(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status, msg):
        self._json_response(status, {'error': msg})

    def _save_ontology(self):
        try:
            payload = self._read_body()
        except (json.JSONDecodeError, ValueError) as e:
            return self._json_error(400, f'Invalid JSON: {e}')

        version = payload.get('version', '')
        data = payload.get('data')
        versions_entry = payload.get('versions_entry')

        if not ALLOWED_VERSION.match(version):
            return self._json_error(400, f'Invalid version format: {version}')
        if not isinstance(data, dict):
            return self._json_error(400, 'data must be an object')

        ontology_dir = os.path.join(ROOT, 'ontology')
        filename = f'ontology-{version}.json'
        filepath = os.path.join(ontology_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')

        if versions_entry:
            versions_path = os.path.join(ontology_dir, 'versions.json')
            try:
                with open(versions_path) as f:
                    versions = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                versions = []

            existing = [v for v in versions if v.get('value') != version]
            existing.insert(0, versions_entry)

            with open(versions_path, 'w') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
                f.write('\n')

        self._json_response(200, {'ok': True, 'file': filename})

    def _save_vocab(self):
        try:
            payload = self._read_body()
        except (json.JSONDecodeError, ValueError) as e:
            return self._json_error(400, f'Invalid JSON: {e}')

        filename = payload.get('filename', '')
        data = payload.get('data')

        if not ALLOWED_VOCAB_FILES.match(filename):
            return self._json_error(400, f'Invalid filename: {filename}')
        if data is None:
            return self._json_error(400, 'data is required')

        vocab_dir = os.path.join(ROOT, 'schemas', 'vocabularies')
        filepath = os.path.join(vocab_dir, filename)

        if not os.path.exists(filepath):
            return self._json_error(404, f'Vocab file not found: {filename}')

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')

        self._json_response(200, {'ok': True, 'file': filename})

    def _list_vocab_files(self):
        vocab_dir = os.path.join(ROOT, 'schemas', 'vocabularies')
        files = sorted(
            f for f in os.listdir(vocab_dir)
            if f.endswith('.json')
        )
        self._json_response(200, {'files': files})


def run(port=8766):
    handler = partial(EditorHandler, directory=ROOT)
    server = HTTPServer(('127.0.0.1', port), handler)
    print(f'  Editor server  ->  http://127.0.0.1:{port}/editor.html')
    print('  Ctrl-C to stop')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
        server.server_close()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    run(port)
