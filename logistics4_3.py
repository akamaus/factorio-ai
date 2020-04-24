#!/usr/bin/env python3
""" Here we use only unary functions and trace locally in both directions.
    If

"""
import os
from time import time

from z3 import *

SZ = int(os.environ.get('SZ', '6'))

s = Solver()
#s.set(unsat_core=True)

t0 = time()


class Point2D:
    _IDX = 0
    def __init__(self, label=None):
        if label == None:
            label = f"p{self._IDX}"
            self.__class__._IDX += 1

        cs = Consts(f"{label}_x {label}_y", IntSort())
        self.x = cs[0]
        self.y = cs[1]

    def __repr__(self):
        return f'Point2D({self.x},{self.y})'

    def __eq__(self, other):
        if isinstance(other, Point2D):
            x,y = other.x, other.y
        elif isinstance(other, tuple):
            assert len(other) == 2
            x,y = other
        return And(self.x == x, self.y == y)
            

def near_z(x, y):
    return Or(x == y+1, x == y-1)


def neighs(p1: Point2D, p2:Point2D):
    assert isinstance(p1, Point2D)
    assert isinstance(p2, Point2D)
    return Or(And(p1.x == p2.x, near_z(p1.y, p2.y)),
              And(p1.y == p2.y, near_z(p1.x, p2.x)))


belt_x = Function('belt_x', IntSort(), IntSort())
belt_y = Function('belt_y', IntSort(), IntSort())
belt_len = Const('belt_len', IntSort())

def belt(i):
    return (belt_x(i), belt_y(i))

i,j = Consts("i j", IntSort())

#s.add(belt_len > 0)
#s.add(ForAll([i], Implies(And(i < belt_len-1, i >=0),
#                          neighs(belt(i), belt(i+1)))))


def Abs(x):
    return If(x >= 0, x, -x)


#s.add(belt_x(0) == 0)
#s.add(belt_y(0) == 0)

#s.add(belt_x(belt_len) == SZ)
#s.add(belt_y(belt_len) == SZ)

print('Modelling time:', time() - t0)

s.push()


def solve():
    while True:
        t1 = time()
        check_res = s.check()
        t2 = time()

        print('Check time:', t2 - t1)

        if str(check_res) == 'sat':
            m = s.model()
            print_belt(m)

        else:
            print('unsat!')
            break

        s.pop()
        used_belts = m.eval(belt_len)
        print('belts:', used_belts)
        s.push()
        s.add(belt_len < used_belts)
        print('Tweaking time:', time() - t2)


if __name__ == '__main__':
    t1 = time()
    solve()
    t2 = time()
    print('Solve time:', t2-t1)
