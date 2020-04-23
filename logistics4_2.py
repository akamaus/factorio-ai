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

Dir = Datatype('Dir')
Dir.declare('u')
Dir.declare('d')
Dir.declare('l')
Dir.declare('r')
Dir.declare('nodir')
Dir = Dir.create()


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


Cell = DeclareSort('Cell')
cells = [[Const('cell_%s_%s' % (j,i), Cell) for i in range(SZ)] for j in range(SZ)]

def all_cells():
    for i in range(SZ):
        for j in range(SZ):
            yield cells[i][j]


s.add(Distinct(*[c for c in all_cells()]))


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


def print_path(m,c2):
    for i in range(SZ):
        for j in range(SZ):
            c = cells[i][j]
            res = m.eval(path_cost(c,c2))
            print(res, end=' ')
        print()


def print_dist_to_sink(m):
    for i in range(SZ):
        for j in range(SZ):
            c = cells[i][j]
            res = m.eval(dist_to_sink(c))
            print(res, end=' ')
        print()


def neighs(i, j):
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


belt_field = Function('belt_field', Cell, Dir)
dist_to_sink = Function('dist_to_sink', Cell, IntSort())
source = Function('source', Cell, BoolSort())
sink = Function('sink', Cell, BoolSort())


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


def Abs(x):
    return If(x >= 0, x, -x)


for c in all_cells():
    s.add(sink(c) == (dist_to_sink(c) == 0))
    s.add(Implies(source(c), dist_to_sink(c) > 0))


# forward_tracing
for i, j, c1 in all_coord_cells():
    variants = []
    for c2, d in neighs(i, j):
        v = And(belt_field(c1) == d, dist_to_sink(c2) == dist_to_sink(c1)-1)
        variants.append(v)
    s.add(Implies(dist_to_sink(c1) > 0, Or(*variants)))


# Backward tracing
for i, j, c1 in all_coord_cells():
    variants = []
    for c2, d in neighs(i, j):
        v = And(dist_to_sink(c2) == dist_to_sink(c1) + 1, belt_field(c2) == inv_dir(d))
        variants.append(v)
    s.add(Implies(dist_to_sink(c1) >= 0, Or(source(c1), *variants)))


c1 = cells[0][0]
c2 = cells[SZ-1][0]
c3 = cells[0][SZ-1]
c4 = cells[SZ-1][SZ-1]

s.add(dist_to_sink(c1) > 0)
s.add(dist_to_sink(c2) > 0)
s.add(dist_to_sink(c3) > 0)
s.add(dist_to_sink(c4) == 0)

def declare_all(pred, tgt_list):
    for c in all_cells():
        is_tgt = False
        for t in tgt_list:
            if eq(c, t):
                is_tgt = True
                break
        s.add(pred(c) == is_tgt)


declare_all(source, [c1,c2,c3])
declare_all(sink, [c4])


s.push()
print('Modelling time:', time() - t0)


def solve():
    while True:
        t1 = time()
        check_res = s.check()
        t2 = time()

        print('Check time:', t2 - t1)

        if str(check_res) == 'sat':
            m = s.model()
        #    print('connected', m[connected])
        #    print('belt_field', m[belt_field])
            print_belt(m)
            #print("Path")
            print_dist_to_sink(m)
        else:
            print('unsat!')
            break

        s.pop()
        used_belts = m.eval(belt_count)
        print('belts:', used_belts)
        s.push()
        s.add(belt_count < used_belts)
        print('Tweaking time:', time() - t2)


if __name__ == '__main__':
    t1 = time()
    solve()
    t2 = time()
    print('Solve time:', t2-t1)
