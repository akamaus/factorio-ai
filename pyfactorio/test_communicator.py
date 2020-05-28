from time import sleep
import pytest
import unittest

from .communicator import SmartCommunicator


class TestDemoTasks(unittest.TestCase):
    def setUp(self) -> None:
        self.sc = SmartCommunicator()

    def test_player_pos(self):
        pos = self.sc.get_player_pos()
        self.assertTrue(-1000 < pos.x < 1000)
        assert -1000 < pos.y < 1000

    def test_move(self):
        pos = self.sc.get_player_pos()
        tpos = pos + (2, 2)

        self.sc.walk_to(tpos)
        sleep(0.5)

        pos2 = self.sc.get_player_pos()
        assert (tpos.x - pos2.x)**2 + (tpos.y - pos2.y)**2 < 2

        self.sc.walk_to(pos)
        sleep(0.5)

        pos3 = self.sc.get_player_pos()
        assert (pos.x - pos3.x)**2 + (pos.y - pos3.y)**2 < 2
