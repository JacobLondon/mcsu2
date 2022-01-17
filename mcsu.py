import math
import time
from typing import List

from module import Module
from networker import NetworkerClient
from mcsu_data import *

def list_get(mylist: list, index: int):
    if len(mylist) <= index:
        return None
    return mylist[index]

def list_get_int(mylist: list, index: int):
    which = list_get(mylist, index)
    if which is None: return None
    try:
        number = int(which)
        return number
    except:
        return None

def distance(x0, y0, x1, y1):
    return math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

class McsuNetworkerClient(NetworkerClient):
    def register(self, data: DataPlayer):
        self.send('register', data)
        message: DataRegister = self.receive()
        if not message is None:
            data.uid = message.uid

    def status(self, data: DataGame):
        self.send('status', {})
        message: DataGame = self.receive()
        if not message is None:
            data.turn = message.turn
            data.players = message.players

    def attack(self, data: DataAttack):
        self.send('attack', data)

    def move(self, data: DataMove):
        self.send('move', data)
    
    def finish_turn(self):
        self.send('finish', {})

    def quit_out(self):
        self.send('quit', {})

class McsuModule(Module):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    # TODO: Re-register upon reconnect?
    def init(self):
        self.player: DataPlayer = DataPlayer(-1, [])
        self.game_data: DataGame = DataGame(0, [])
        self.client = McsuNetworkerClient(self.ip, self.port)
        self.client.register(self.player)

        self.stamp_onesec = time.time()
        self.now = time.time()

        self.need_to_exit = False

        self.selected_unit: DataUnit = None
        self.selected_defender: DataUnit = None

    def update(self):
        self.now = time.time()

        # everyone waits on me
        if self._my_turn():
            self._userinput()

        # I want on current
        else:
            pass

        if self.now - self.stamp_onesec > 1.0:
            self.client.status(self.game_data)

            # update our own representation as well
            for player in self.game_data.players:
                if player.uid == self.player.uid:
                    self.player.units = player.units

        self._draw()
        time.sleep(.25)
        return not self.need_to_exit

    def cleanup(self):
        pass

    def _my_turn(self):
        return self.player.uid == self.game_data.turn

    def _draw(self):
        print("Drawing")
        for player in self.game_data.players:
            print(player)

    def _userinput(self):
        self._input_text()

    def _input_text(self):
        command = input('> ')
        args = command.split()
        if len(args) == 0:
            return

        if list_get(args, 0) == 'quit':
            self.client.quit_out()
            self.need_to_exit = True

        elif list_get(args, 0) == 'finish':
            self.client.finish_turn()
            self.game_data.turn = -1

        elif list_get(args, 0) == 'selectplayer':
            x = list_get_int(args, 1)
            if x is None:
                print("selectplayer no x")
                return
            y = list_get_int(args, 2)
            if y is None:
                print("selectplayer no y")
                return

            self.selected_unit = None
            for unit in self.player.units:
                if unit.x == x and unit.y == y:
                    self.selected_unit = unit
                    break

        elif list_get(args, 0) == 'selectdefender':
            x = list_get_int(args, 1)
            if x is None:
                print("selectdefender no x")
                return
            y = list_get_int(args, 2)
            if y is None:
                print("selectdefender no y")
                return
        
            self.selected_defender = None
            for player in self.game_data.players:
                # TODO: Allow attacking your own guys for now...
                for unit in player.units:
                    if unit.x == x and unit.y == y:
                        self.selected_defender = unit
                        break
            if not self.selected_defender is None:
                print("selectdefender no choice")

        elif list_get(args, 0) == 'attack':
            if self.selected_unit is None or self.selected_defender is None:
                print("attack no attacker or defender")
                return

            reach_required = distance(self.selected_unit.x, self.selected_unit.y, self.selected_defender.x, self.selected_defender.y)
            if reach_required < self.selected_unit.minreach or reach_required > self.selected_unit.maxreach: return

            attack = DataAttack(self.selected_unit, self.selected_defender)
            self.client.attack(attack)

        elif list_get(args, 0) == 'move':
            if self.selected_unit is None:
                print("move no mover")
                return
            x = list_get_int(args, 1)
            if x is None:
                print("move no x")
                return
            y = list_get_int(args, 2)
            if y is None:
                print("move no y")
                return

            if self._is_occupied(x, y):
                print("move occupied")
                return
            # TODO: Is walkable as well?

            if distance(self.selected_unit.x, self.selected_unit.y, x, y) \
                    > self.selected_unit.speed:
                print("move too far")
                return

            aos = self._receives_aos(self.selected_unit, x, y)
            for ao in aos:
                attack = DataAttack(ao, self.selected_unit)
                self.client.attack(attack)

            move = DataMove(self.selected_unit, x, y)
            self.client.move(move)

    def _is_occupied(self, x: int, y: int):
        for player in self.game_data.players:
            for unit in player.units:
                if unit.x == x and unit.y == y:
                    return True
        return False

    ##
    # Given a player and a target position, return a list of attackers
    # that are given the opportunity to make an attack invoked by the
    # movement
    def _receives_aos(self, data: DataUnit, x: int, y: int) -> List[DataPlayer]:
        return []

def main(argv):
    mod = McsuModule(ip='127.0.0.1', port=20000)
    mod.run()
    return 0

if __name__ == '__main__':
    import sys
    exit(main(sys.argv))
