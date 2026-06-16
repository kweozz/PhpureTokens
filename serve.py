#!/usr/bin/env python3
"""Tiny static server, no os.getcwd() default — works under restricted sandboxes."""
import os, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

class Handler(SimpleHTTPRequestHandler):
    pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 4173
print(f"Serving {ROOT} on http://localhost:{port}")
HTTPServer(("127.0.0.1", port), Handler).serve_forever()
