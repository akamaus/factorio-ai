#!/usr/bin/env python2
from __future__ import print_function

from z3 import *
import time

s = Solver()
#s.set(unsat_core=True)

t0 = time.time()

Dir = Datatype('Dir')
Dir.declare('u')
Dir.declare('d')
Dir.declare('l')
Dir.declare('r')
Dir.declare('nodir')
Dir = Dir.create()

SZ = 7

Cell = DeclareSort('Cell')
cells = [[Const('cell_%s_%s' % (j,i), Cell) for i in range(SZ)] for j in range(SZ)]


def all_cells():
    for i in range(SZ):
        for j in range(SZ):
            yield cells[i][j]


def all_coord_cells():
    for i in range(SZ):
        for j in range(SZ):
            yield i,j, cells[i][j]


def print_belt(m):
    for i in range(SZ):
        for j in range(SZ):
            c = cells[i][j]
            res = m.eval(belt_field(c))
            if eq(Dir.nodir, res):
                ch='.'
            elif eq(Dir.r, res):
                ch='>'
            elif eq(Dir.l, res):
                ch = '<'
            elif eq(Dir.u, res):
                ch = '^'
            elif eq(Dir.d, res):
                ch = 'v'
            else:
                raise ValueError('strange dir', res)
            print(ch,end='')
        print()


def pymoves(i,j):
    """ Returns move variants as [(cell, dir)] """
    res = []
    if i > 0:
        res.append((cells[i-1][j], Dir.u))
    if i < SZ-1:
        res.append((cells[i+1][j], Dir.d))
    if j > 0:
        res.append((cells[i][j-1], Dir.l))
    if j < SZ-1:
        res.append((cells[i][j+1], Dir.r))
    return res


def inv_dir(d):
    """ Inverts direction """
    if eq(d, Dir.u):
        return Dir.d
    elif eq(d, Dir.d):
        return Dir.u
    elif eq(d, Dir.l):
        return Dir.r
    elif eq(d, Dir.r):
        return Dir.l
    else:
        assert ValueError('Strange dir', d)


belt_field = Function('belt_field', Cell, Dir)
connected = Function('connected', Cell, Cell, BoolSort())

belt_cost = Function('belt_cost', Dir, IntSort())
s.add(belt_cost(Dir.nodir) == 0)
s.add(belt_cost(Dir.u) == 1)
s.add(belt_cost(Dir.d) == 1)
s.add(belt_cost(Dir.l) == 1)
s.add(belt_cost(Dir.r) == 1)

belt_count = Int('belt_count')

sum = 0
for c in all_cells():
    sum = sum + belt_cost(belt_field(c))

s.add(belt_count == sum)

# Reflexivity
for c in all_cells():
    s.add(connected(c, c))

# Antisimmetry
for c1 in all_cells():
    for c2 in all_cells():
        if not eq(c1,c2):
            s.add(Implies(connected(c1, c2), Not(connected(c2, c1))))


# belt connects neighbors
for i,j, c1 in all_coord_cells():
    for c2, d in pymoves(i, j):
        s.add(Implies(belt_field(c1) == d, connected(c1, c2)))


# connection by means of a belt
for i, j, c1 in all_coord_cells():
    for c3 in all_cells():
        if not eq(c1,c3):
            s.add(Implies(connected(c1,c3),
                          Or([And(belt_field(c1) == d,
                                  connected(c2, c3))
                                                for c2, d in pymoves(i, j)])))

for c1 in all_cells():
    for i, j, c2 in all_coord_cells():
        for c3, d in pymoves(i, j):
            s.add(Implies(And(belt_field(c2) == d, connected(c1,c2)),
                      (connected(c1,c3))))

#
# # backward induction
# for c1 in all_cells():
#     for i,j, c2 in all_coord_cells():
#         if not eq(c1,c2):
#             mvs = pymoves(i,j)
#             vars = [ And(connected(c1,c3),
#                          belt_field(c3) == MaybeDir.just(inv_dir(d))) for c3,d in mvs ]
#             s.add(Implies(connected(c1,c2), Or(*vars)))

#s.assert_and_track(ForAll([c1,c2], Implies(c1 != c2, Or(And(connected(c1,c2), Not(connected(c2,c1))),
#                                                       And(connected(c2,c1), Not(connected(c1,c2)))))), 'tst')

#s.add(belt_field(cells[0][0]) == MaybeDir.just(Dir.r))

c1 = cells[0][0]
c2 = cells[SZ-1][0]
c3 = cells[0][SZ-1]
c4 = cells[SZ-1][SZ-1]

s.add(connected(c1,c4))
s.add(connected(c2,c4))
s.add(connected(c3,c4))

#s.assert_and_track(belt_field(c2) == MaybeDir.nothing, 'no_back')

s.push()

print('Modelling time:', time.time() - t0)
while True:
    t1 = time.time()
    check_res = s.check()
    t2 = time.time()

    print('Check time:', t2 - t1)

    if str(check_res) == 'sat':
        m = s.model()
    #    print('connected', m[connected])
    #    print('belt_field', m[belt_field])
        print_belt(m)
    else:
        print('unsat!', s.check(), s.unsat_core())
        break

    s.pop()
    used_belts = m.eval(belt_count)
    print('belts:', used_belts)
    t3 = time.time()
    s.push()
    s.add(belt_count < used_belts)
    print('Tweaking time:', time.time() - t3)
