import os.path as osp
import socket

from primitives import Point2D


class Communicator:
    BUFFER_SIZE = 2 ** 20

    def __init__(self, host='127.0.0.1', port=1268):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))

    def eval(self, lua_str: str):
        self.s.send(lua_str.encode('ascii') + b'\0')
        res = self._receive_answer()
        return res[:-1]

    def _receive_answer(self):
        ans = b''
        while True:
            r = self.s.recv(self.BUFFER_SIZE)
            ans += r
            if ans[-1] == 0:
                break
        return ans.decode('ascii')

    def close(self):
        self.s.close()


def readfile(path):
    with open(path, 'r') as f:
        return ''.join(f.readlines())


import json


class SmartCommunicator:
    def __init__(self, comm=None):
        self.comm = Communicator() if comm is None else comm

        self.load_module('get_direction')
        self.load_module('queue')
        self.load_module('find_entities')
        self.load_module('walk')

    def load_module(self, name):
        txt = readfile(osp.join(osp.dirname(__file__), 'scripts', name + '.lua'))
        res = self.comm.eval(txt)
        assert res == 'nil'

    def find_entities(self, p1, p2):
        if isinstance(p1, tuple):
            assert len(p1) == 2
            p1x, p1y = p1[0], p1[1]
        else:
            p1x, p1y = p1.x, p1.y

        if isinstance(p2, tuple):
            assert len(p2) == 2
            p2x, p2y = p2[0], p2[1]
        else:
            p2x, p2y = p2.x, p2.y

        entities_str = self.comm.eval(f"return game.table_to_json(find_entities({p1x}, {p1y}, {p2x}, {p2y}))")

        try:
            res = json.loads(entities_str)
        except json.JSONDecodeError as e:
            print(f'Got error "{e}" decoding json string "{entities_str[:50]}"')
            raise e
        return res

    def get_player_pos(self):
        res = json.loads(self.comm.eval('return game.table_to_json(game.players[1].position)'))
        return Point2D(res['x'], res['y'])

    def walk_to(self, pos):
        self.comm.eval('walk_queue:put({x=%d,y=%d})' % (pos.x, pos.y))