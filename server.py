import http.server
import urllib.request
import urllib.parse
import socket
import ssl
import os

socket.setdefaulttimeout(12)

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Block private key from being served
        if self.path.rstrip('/') in ('/key.pem',):
            self.send_response(403)
            self.end_headers()
            return
        if self.path.startswith('/proxy?'):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get('url', [None])[0]
            if not url:
                self.send_response(400)
                self.end_headers()
                return
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache'
                })
                opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
                opener.addheaders = []
                with opener.open(req, timeout=12) as resp:
                    data = resp.read(1024 * 512)  # max 512 KB
                self.send_response(200)
                self.send_header('Content-Type', 'application/xml; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = 8765
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with http.server.HTTPServer(('0.0.0.0', port), ProxyHandler) as httpd:
        use_https = os.path.exists('cert.pem') and os.path.exists('key.pem')
        if use_https:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain('cert.pem', 'key.pem')
            httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = '127.0.0.1'

        scheme = 'https' if use_https else 'http'
        print(f'News server → {scheme}://{local_ip}:{port}/News.html')
        if not use_https:
            print('  Tip: run generate_cert.py to enable HTTPS for full PWA support on iOS')
        httpd.serve_forever()
