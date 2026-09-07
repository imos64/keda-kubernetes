"""Small CPU-work and Prometheus-metric demo; no external dependencies."""
import hashlib, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
count = 0
lock = threading.Lock()
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global count
        path = self.path.split('?',1)[0]
        if path == '/healthz': body = b'ok\n'
        elif path == '/metrics':
            with lock: value = count
            body = ('# HELP demo_requests_total Work requests served.\n# TYPE demo_requests_total counter\ndemo_requests_total %d\n' % value).encode()
        elif path in ('/', '/work'):
            hashlib.pbkdf2_hmac('sha256',b'demo',b'autoscaling',100000)
            with lock: count += 1
            body = b'work complete\n'
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type','text/plain; version=0.0.4')
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
if __name__ == '__main__':
    server=ThreadingHTTPServer((os.environ.get('BIND','0.0.0.0'),int(os.environ.get('PORT','8080'))),Handler)
    print(server.server_address[1],flush=True);server.serve_forever()
