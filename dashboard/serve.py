"""Serve the unified ASI dashboard locally using only Python's standard library."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
from pathlib import Path
import sys

from data_loader import dashboard_data

HERE = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE / "static"), **kwargs)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/dashboard":
            payload = json.dumps(dashboard_data(), ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(payload)))
            self.end_headers(); self.wfile.write(payload); return
        super().do_GET()

    def log_message(self, format, *args):
        print(format % args)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--port",type=int,default=8899)
    args=parser.parse_args();server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print(f"Unified ASI dashboard: http://127.0.0.1:{args.port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__": sys.exit(main())
