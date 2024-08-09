import hashlib
import json
import random
import re
import secrets
import socketserver
import string
import threading
import traceback
from http.server import BaseHTTPRequestHandler

from web3pi_proxy.config.conf import Config
from web3pi_proxy.service.admin.serviceadmin import RPCServiceAdmin
from web3pi_proxy.utils.logger import get_logger


# TODO: Whole auth is operating under bastardized concept of basic authorizations scheme with random tokens
# It's insecure for anything outside of local network and should be expanded to legitimate security measures
class AdminServerAuthentication:
    def __init__(self) -> None:
        self.salt = secrets.token_hex(8)
        self.admin_token_hash = None

    def hash(self, secret: str) -> str:
        salted_secret = secret + self.salt
        hashed = hashlib.sha256(salted_secret.encode())
        return hashed.hexdigest()

    def authenticate(self, secret) -> bool:
        if self.admin_token_hash is None:
            raise Exception("Authentication token was not generated")
        return self.hash(secret) == self.admin_token_hash

    def generate_secret(self) -> str:
        return "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(32)
        )

    def create_auth_token(self) -> str:
        if Config.ADMIN_AUTH_TOKEN:
            auth_token = Config.ADMIN_AUTH_TOKEN
        else:
            auth_token = self.generate_secret()
        self.admin_token_hash = self.hash(auth_token)
        return auth_token


# https://gist.github.com/scimad/ae0196afc0bade2ae39d604225084507
class AdminServerRequestHandler(BaseHTTPRequestHandler):
    __logger = get_logger("AdminServerRequestHandler")

    def get_valid_host_page(self, auth_token: str) -> bytes:
        assert isinstance(self.server, AdminHTTPServer)

        assert "Host" in self.headers
        host = self.headers["Host"]

        with open(Config.ADMIN_HTML_FILE, "rb") as f:
            # ip = "127.0.0.1"
            # port = self.server.server_address[1]
            #
            # if Config.PUBLIC_SERVICE:
            #     ip = my_public_ip()
            raw_page = f.read().decode("utf-8")
            host = f'return "http://{host}/";'
            host_re = r"//HOST_MARKER_S[\s\w.]+.+\s+//HOST_MARKER_E"
            auth_token_expr = f'return "{auth_token}";'
            auth_token_re = r"//TOKEN_MARKER_S[\s\w.]+.+\s+//TOKEN_MARKER_E"

            updated_page = re.sub(
                auth_token_re, auth_token_expr, re.sub(host_re, host, raw_page)
            )

            return updated_page.encode("utf-8")

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(200)
            self.send_header("Content-Type", "image/x-icon")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            # Get auth token from query params for accessing admin portal with browser
            auth_token = self.path.split("?token=")[-1]
            if self.server.auth.authenticate(auth_token):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(self.get_valid_host_page(auth_token))

                # # Test how a web browser handles partial update of a web page
                # data = bytearray(f.read())
                # i = 0
                # while i < len(data):
                #     self.wfile.write(data[i:i+250])
                #     i += 250
                #     time.sleep(0.1)
            else:
                self.send_response(401)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                response = (
                    "<!DOCTYPE html><html><head><title>Unauthorized</title></head><body><h1>You are not authorized "
                    "to access this page</h1></body></html>"
                )

                self.wfile.write(response.encode("UTF-8"))

    def log_request(self, code: int | str = ..., size: int | str = ...) -> None:
        pass

    def do_POST(self):
        # TODO: Expand JSON-RPC support
        assert isinstance(self.server, AdminHTTPServer)
        admin = self.server.admin

        content_length = int(self.headers["Content-Length"])
        json_data = json.loads(self.rfile.read(content_length).decode("utf-8"))

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        if self.server.auth.authenticate(self.get_auth_token()):
            if "method" in json_data:
                try:
                    res = admin.call_by_method(
                        json_data["method"], json_data.get("params", [])
                    )
                except Exception as error:
                    self.__logger.error(error.with_traceback)
                    print(traceback.format_exc())
                    res = {"error": "Server error"}
            else:
                res = {"error": "Missing method"}
        else:
            res = {"error": "Authentication failed"}  # TODO another http status?
        self.wfile.write(json.dumps(res if res is not None else {}).encode())

    def get_auth_token(self) -> str:
        return self.headers.get("Authorization", "").partition(" ")[-1]


class AdminHTTPServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, admin: RPCServiceAdmin, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.admin = admin
        self.auth_token = "/" + "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(32)
        )
        self.auth = AdminServerAuthentication()

    # def server_bind(self) -> None:
    #     self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     self.socket.bind(self.server_address)


class AdminHTTPServerThread(threading.Thread):

    def __init__(self, admin: RPCServiceAdmin, *args, **kwargs):
        super().__init__(daemon=True)

        self.server = AdminHTTPServer(admin, *args, **kwargs)

    def start(self) -> None:
        print(
            f"HTTP Admin server listening on: {self.server.server_address[0]}:{self.server.server_address[1]}"
        )
        # TODO: Storage for credentials
        auth_token = self.server.auth.create_auth_token()
        print("Admin auth token: " f"{auth_token}")
        print("Use it with 'Authorization' header for POST requests")
        print(f"Access admin portal with:")
        print(
            f"http://{self.server.server_address[0]}:{self.server.server_address[1]}/?token={auth_token}"
        )
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
