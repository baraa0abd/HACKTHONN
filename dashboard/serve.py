"""Serve the unified ASI dashboard locally using only Python's standard library."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

from data_loader import dashboard_data
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decision_engine import recommend
from field_validation import append_observation, metrics
import osdr_api

HERE = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE / "static"), **kwargs)

    def _json(self, code, obj):
        payload=json.dumps(obj,ensure_ascii=False,allow_nan=False,default=float).encode("utf-8");self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/osdr/metrics": return self._json(200, osdr_api.metrics())
        if parsed.path == "/api/osdr/options": return self._json(200, osdr_api.options())
        if parsed.path == "/api/recommend":
            try:
                q=parse_qs(parsed.query); radius=max(1,min(250,float(q.get("radius",[100])[0]))); days=max(1,min(7,int(q.get("days",[7])[0])))
                payload=json.dumps(recommend(max_travel_km=radius,days=days,mode=q.get("mode",["naked_eye"])[0]),ensure_ascii=False,allow_nan=False).encode("utf-8");self.send_response(200)
            except Exception as exc:
                payload=json.dumps({"error":f"تعذر جلب التوقعات الحية: {exc}"},ensure_ascii=False).encode("utf-8");self.send_response(502)
            self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload);return
        if parsed.path == "/api/validation":
            payload=json.dumps(metrics(),ensure_ascii=False).encode("utf-8");self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload);return
        if self.path.split("?", 1)[0] == "/api/dashboard":
            payload = json.dumps(dashboard_data(), ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(payload)))
            self.end_headers(); self.wfile.write(payload); return
        super().do_GET()

    def do_POST(self):
        path=urlparse(self.path).path
        if path in ("/api/osdr/predict", "/api/osdr/predict-genes"):
            limit=10_000 if path.endswith("predict") else 80_000_000  # VST files are ~5-30 MB
            try:
                size=int(self.headers.get("Content-Length","0"))
                if size<=0 or size>limit: raise ValueError(f"request body must be 1..{limit} bytes")
                body=self.rfile.read(size)
                result=osdr_api.predict(json.loads(body)) if path.endswith("predict") else osdr_api.predict_genes(body)
                return self._json(200, result)
            except FileNotFoundError as exc: return self._json(503, {"error": str(exc)})
            except Exception as exc: return self._json(400, {"error": f"{type(exc).__name__}: {exc}"})
        if path != "/api/validation":
            self.send_error(404); return
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<=0 or size>10000: raise ValueError("invalid request size")
            row=append_observation(json.loads(self.rfile.read(size)))
            payload=json.dumps({"saved":row,"metrics":metrics()},ensure_ascii=False).encode("utf-8");self.send_response(201)
        except Exception as exc:
            payload=json.dumps({"error":str(exc)},ensure_ascii=False).encode("utf-8");self.send_response(400)
        self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(payload)));self.end_headers();self.wfile.write(payload)

    def log_message(self, format, *args):
        print(format % args)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--port",type=int,default=8903)
    parser.add_argument("--host",default="127.0.0.1",help="0.0.0.0 lets phones on the same Wi-Fi connect")
    args=parser.parse_args();server=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f"Unified ASI dashboard: http://{args.host}:{args.port}  (OSDR model: /osdr.html)")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__": sys.exit(main())




