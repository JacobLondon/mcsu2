import socket
import json

_BUFFER_SIZE = 1024

class NetworkerClient:
    def __init__(self, ip='127.0.0.1', port=20000):
        self.address = (ip, port)
        self._connect()

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.connect(self.address)
            return True
        except:
            self.sock = None
        return False

    def _disconnect(self):
        if not self.connected():
            return
        self.sock.close()
        self.sock = None

    def connected(self):
        return not self.sock is None

    def send(self, command: str, obj):
        if not self.connected() and not self._connect():
            return

        myobj = obj if type(obj) is dict else obj.__dict__
        data = {'_command': command, **myobj}
        try:
            message = json.dumps(data)
        except:
            return

        try:
            print('sending', message)
            self.sock.sendall(message)
        except:
            self.sock = None

    def receive(self) -> dict:
        if not self.connected() and not self._connect():
            return None

        try:
            message = self.sock.recv(_BUFFER_SIZE)
            print('receive', message)
            data = json.loads(message)
        except:
            data = None
        return data
