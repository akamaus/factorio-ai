#!/usr/bin/env python3
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

SZ = 8


cells_dir = [[Const('cells_dir_%s_%s' % (j, i), Dir) for i in range(SZ)] for j in range(SZ)]
cells_sup = [[Bool('cells_sup_%s_%s' % (j, i)) for i in range(SZ)] for j in range(SZ)]
cells_cons = [[Bool('cells_cons_%s_%s' % (j, i)) for i in range(SZ)] for j in range(SZ)]
cells_dst = [[Int('cells_dst_%s_%s' % (j, i)) for i in range(SZ)] for j in range(SZ)]


def all_coords():
    for i in range(SZ):
        for j in range(SZ):
            yield i, j


def print_belt(m):
    for i in range(SZ):
        for j in range(SZ):
            c = cells_dir[i][j]
            res = m.eval(c)
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


def print_dst(m):
    for i in range(SZ):
        for j in range(SZ):
            c = cells_dst[i][j]
            res = m.eval(c)
            print(res,end=' ')
        print()


def pymoves(i, j):
    """ Returns move variants as [(cell, dir)] """
    res = []
    if i > 0:
        res.append((i-1, j, Dir.u))
    if i < SZ-1:
        res.append((i+1, j, Dir.d))
    if j > 0:
        res.append((i, j-1, Dir.l))
    if j < SZ-1:
        res.append((i, j+1, Dir.r))
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


belt_cost = Function('belt_cost', Dir, IntSort())
s.add(belt_cost(Dir.nodir) == 0)
s.add(belt_cost(Dir.u) == 1)
s.add(belt_cost(Dir.d) == 1)
s.add(belt_cost(Dir.l) == 1)
s.add(belt_cost(Dir.r) == 1)

belt_count = Int('belt_count')

sum = 0
for i,j in all_coords():
    sum = sum + belt_cost(cells_dir[i][j])

s.add(belt_count == sum)


# forward chain
for i, j in all_coords():
    vars = []
    dst = cells_dst[i][j]
    d = cells_dir[i][j]

    vars.append(cells_cons[i][j])
    vars.append(dst == 0)
    if i > 0:
        vars.append(And(d == Dir.u, cells_dst[i-1][j] == dst - 1))
    if i < SZ-1:
        vars.append(And(d == Dir.d, cells_dst[i+1][j] == dst - 1))
    if j > 0:
        vars.append(And(d == Dir.l, cells_dst[i][j-1] == dst - 1))
    if j < SZ-1:
        vars.append(And(d == Dir.r, cells_dst[i][j+1] == dst - 1))
    s.add(Or(*vars))


# backward chain
for i, j in all_coords():
    vars = []
    dst = cells_dst[i][j]

    s.add(cells_cons[i][j] == (dst == 1))
    s.add(Implies(cells_sup[i][j], And(dst > 1))) # , cells_dir[i][j] != Dir.nodir)))

    vars.append(cells_sup[i][j])
    vars.append(dst == 0 ) # Not(cells_cons[i][j]))
    if i > 0:
        vars.append(And(cells_dir[i-1][j] == Dir.d, cells_dst[i-1][j] == dst + 1))
    if i < SZ-1:
        vars.append(And(cells_dir[i+1][j] == Dir.u, cells_dst[i+1][j] == dst + 1))
    if j > 0:
        vars.append(And(cells_dir[i][j-1] == Dir.r, cells_dst[i][j-1] == dst + 1))
    if j < SZ-1:
        vars.append(And(cells_dir[i][j+1] == Dir.l, cells_dst[i][j+1] == dst + 1))
    s.add(Or(*vars))



srcs = [(0,0), (SZ-1,0), (0,SZ-1)]
dst = (SZ-1, SZ-1)

# request satisfaction
for i, j in all_coords():
    sup = cells_sup[i][j]
    cons = cells_cons[i][j]

    if (i, j) in srcs:
        s.add(sup)
    else:
        s.add(Not(sup))

    if (i, j) == dst:
        s.add(cons)
    else:
        s.add(Not(cons))


s.push()

print('Modelling time:', time.time() - t0)
t0 = time.time()

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

print('Full time', time.time() - t0)
