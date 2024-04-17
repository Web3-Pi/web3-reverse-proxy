from core.sockets.basesocket import BaseSocket
from core.sockets.clientsocket import ClientSocket
from service.tempimpl.request.request_reader import read_request
from service.tempimpl.request.response_reader import recv_response


class RequestHandler:

    POST_REQUEST_LINE = 'POST /{} HTTP/1.1\r\n'
    HOST_LAST_HEADER = "Host: {}\r\n\r\n"
    NUM_REQ = 0

    def __init__(self, endpoint: str, port: int, name: str) -> None:
        self.port = port
        self.endpoint = endpoint
        self.name = name

        self.endpoint_sock = BaseSocket.create_socket(endpoint, port, False)
        self.ip = self.endpoint_sock.get_peer_name()[0]
        self.endpoint_sock.get_peer_name()

        self.host_header = self.HOST_LAST_HEADER.format(endpoint).encode("utf-8")

    def recv_resp(self, data: bytes) -> bytearray:
        self.endpoint_sock.send_all(data)
        return recv_response(self.endpoint_sock)

    def get_response(self, data: bytes) -> bytearray:
        try:
            return self.recv_resp(data)
        except IOError:
            self.endpoint_sock.close()
            self.endpoint_sock = self.endpoint_sock.create_socket(self.endpoint, self.port, False)
        except Exception:
            raise

        return self.recv_resp(data)

    def get_cur_no_handled(self) -> int:
        return self.NUM_REQ

    def handle_request(self, cs: ClientSocket) -> None:
        while True:
            req = read_request(cs)

            if req is None:
                return

            res = self.get_response(b'POST / HTTP/1.1\r\n' + req.headers + self.host_header + req.content)
            assert res is not None
            try:
                # assert cs.is_ready_write()
                cs.send_all(res)
                RequestHandler.NUM_REQ += 1
            except IOError:
                print("IO ERROR")
                return
            except Exception:
                raise
