import json
import random
import re
import socket
import socketserver
import string
import threading

from http.server import BaseHTTPRequestHandler

from web3_reverse_proxy.config.conf import ADMIN_HTML_FILE

from web3_reverse_proxy.service.admin.serviceadmin import RPCServiceAdmin


# https://gist.github.com/scimad/ae0196afc0bade2ae39d604225084507
class AdminServerRequestHandler(BaseHTTPRequestHandler):

    def get_valid_host_page(self) -> bytes:
        assert isinstance(self.server, AdminHTTPServer)

        assert 'Host' in self.headers
        host = self.headers['Host']

        with open(ADMIN_HTML_FILE, 'rb') as f:
            # ip = "127.0.0.1"
            # port = self.server.server_address[1]
            #
            # if PUBLIC_SERVICE:
            #     ip = my_public_ip()
            raw_page = f.read().decode("utf-8")
            host = f'return "http://{host}/{self.server.auth_token}";'
            host_re = r'//HOST_MARKER_S[\s\w.]+.+\s+//HOST_MARKER_E'

            updated_page = re.sub(host_re, host, raw_page)

            return updated_page.encode("utf-8")

    def do_GET(self):
        if self.path == '/6a5d70f03252a227a6b8292ac80b33d4b1740833a65e31175':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(self.get_valid_host_page())

            # # Test how a web browser handles partial update of a web page
            # data = bytearray(f.read())
            # i = 0
            # while i < len(data):
            #     self.wfile.write(data[i:i+250])
            #     i += 250
            #     time.sleep(0.1)
        elif self.path == '/favicon.ico':
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.send_header('Content-Length', '0')
            self.end_headers()
        else:
            self.send_response(401)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            response = '<!DOCTYPE html><html><head><title>Unauthorized</title></head><body><h1>You are not authorized '\
                       'to access this page</h1></body></html>'

            self.wfile.write(response.encode("UTF-8"))

    def log_request(self, code: int | str = ..., size: int | str = ...) -> None:
        pass

    def do_POST(self):
        assert isinstance(self.server, AdminHTTPServer)
        admin = self.server.admin

        content_length = int(self.headers['Content-Length'])
        json_data = json.loads(self.rfile.read(content_length).decode("utf-8"))

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.path == self.server.auth_token:
            if 'method' in json_data and 'params' in json_data:
                res = admin.call_by_method(json_data['method'], json_data['params'])
                self.wfile.write(json.dumps(res if res is not None else {}).encode())
        else:
            self.wfile.write(json.dumps({}).encode())


class AdminHTTPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, admin: RPCServiceAdmin, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.admin = admin
        self.auth_token = '/' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

    # def server_bind(self) -> None:
    #     self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     self.socket.bind(self.server_address)


class AdminHTTPServerThread(threading.Thread):

    def __init__(self, admin: RPCServiceAdmin, *args, **kwargs):
        super().__init__(daemon=True)

        self.server = AdminHTTPServer(admin, *args, **kwargs)

    def start(self) -> None:
        print(f"HTTP Admin server listening on: {self.server.server_address[0]}:{self.server.server_address[1]}")
        print(f"HTTP Admin server url: "
              f"http://<IP addr>:{self.server.server_address[1]}/6a5d70f03252a227a6b8292ac80b33d4b1740833a65e31175")
        super().start()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        print(f"HTTP Admin server shutdown initiated")
        try:
            self.server.shutdown()
            self.join()
        except KeyboardInterrupt:
            pass
        except Exception:
            raise
        print(f"HTTP Admin server shutdown complete")
