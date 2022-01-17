import copy
import threading
import socketserver
import json
from typing import List
from mcsu_data import *

_BUFFER_SIZE = 1024
_CLIENTS_MAX = 8

class State:
    def __init__(self):
        self.userdata = DataGame(0, [])
        self.uid_free = []
        self.uid = 0
        self.lock = threading.Semaphore()

    def get_userdata(self):
        self.lock.acquire()
        mycopy: DataGame = copy.deepcopy(self.userdata)
        self.lock.release()
        return mycopy

    def set_userdata(self, player: DataPlayer):
        self.lock.acquire()

        found = False
        for i, curplayer in enumerate(self.userdata.players):
            if curplayer.uid == player.uid:
                self.userdata.players[i] = player
                found = True
                break
        if not found:
            self.userdata.players.append(player)

        self.lock.release()

    def next_turn(self):
        self.lock.acquire()
        self.uid = (self.uid + 1) % len(self.userdata.players)
        self.lock.release()

    def del_uid(self, uid: int):
        self.lock.acquire()
        for player in self.userdata.players:
            if uid == player.uid:
                self.uid_free.append(uid)

                # we can't remain in this turn anymore
                if self.userdata.turn == player.uid:
                    self.next_turn()

                del self.userdata.players[uid]
                break
        self.lock.release()

    def new_uid(self) -> int:
        self.lock.acquire()
        if len(self.uid_free) > 0:
            uid = self.uid_free.pop(0)
            self.lock.release()
            return uid

        uid = self.uid
        self.uid += 1
        self.lock.release()
        return uid

class McsuServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.state: State = State()
        self.turn: int = 0

    def run(self):
        class Handler(socketserver.ThreadingTCPServer):
            thisref = self
            def handle(self):
                this = Handler.thisref
                uid = -1

                # DC if too many clients
                if len(self.state) >= _CLIENTS_MAX:
                    print("Too many clients!")
                    return

                self.request.setblocking(True)
                while True:
                    data = self.receive()
                    if data is None:
                        if uid != -1: self.state.del_uid(uid)
                        print("No data")
                        break

                    command = data.get('_command')
                    if command is None:
                        if uid != -1: self.state.del_uid(uid)
                        print("No command")
                        break

                    elif command == 'register':
                        uid = self.state.new_uid()
                        units = data.get('units')
                        if not units is None:
                            data = DataPlayer(uid, units)
                            self.state.set_userdata(data)
                        data = DataRegister(uid)
                        self.send(data)

                    elif command == 'status':
                        if uid == -1:
                            print("No status uid")
                            break
                        data: DataGame = self.state.get_userdata()
                        self.send(data)

                    elif command == 'finish':
                        if uid == -1:
                            print("No finish uid")
                            break
                        self.state.next_turn()

                    elif command == 'quit':
                        if uid != -1:
                            print("No quit uid")
                            self.state.del_uid(uid)
                        self.state.del_uid(uid)
                        break
                
                    elif command == 'move':
                        if uid == -1:
                            print("No move uid")
                            break

                        # get commanded position
                        selected_unit = data.get('mover')
                        x = data.get('x')
                        y = data.get('y')
                        if selected_unit is None or x is None or y is None:
                            print("No selected unit/x/y")
                            break

                        state: DataGame = self.state.get_userdata()
                        need_to_break = False
                        for player in state.players:
                            if not uid == player.uid: continue

                            # find data unit from selected unit
                            for unit in player.units:
                                if unit.x == selected_unit.x and unit.y == selected_unit.y:
                                    # move it!
                                    unit.x = x
                                    unit.y = y
                            if need_to_break: break

                    elif command == 'attack':
                        pass

            def send(self, obj):
                myobj = obj if type(obj) is dict else obj.__dict__
                try:
                    message = json.dumps(myobj)
                except:
                    print('Failed to dumps')
                    return

                try:
                    self.request.sendall(message)
                except:
                    print('Failed to sendall')
                    return

            def receive(self):
                try:
                    self.message = self.request.recv(_BUFFER_SIZE)
                except:
                    print("Failed to receive")
                    return None

                # disconnected
                if len(self.message) == 0: return None

                try:
                    data: dict = json.loads(self.message)
                except:
                    print("Failed to loads")
                    return None
                return data

        with socketserver.ThreadingTCPServer((self.host, self.port), Handler) as server:
            server.serve_forever()

def main(args):
    server = McsuServer('0.0.0.0', 20000)
    server.run()
    return 0

if __name__ == '__main__':
    import sys
    exit(main(sys.argv))
