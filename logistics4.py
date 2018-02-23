from z3 import *

s = Solver()
s.set(unsat_core=True)

Dir = Datatype('Dir')
Dir.declare('u')
Dir.declare('d')
Dir.declare('l')
Dir.declare('r')
Dir = Dir.create()

SZ = 2
Cell = DeclareSort('Cell')
cells = [[Const('cell_%s_%s' % (j,i), Cell) for i in range(SZ)] for j in range(SZ)]


def declare_maybe(typ):
    assert is_sort(typ)
    maybe = Datatype('Maybe' + typ.name())
    maybe.declare('just', ('getJust', typ))
    maybe.declare('nothing')
    return maybe.create()


MaybeCell = declare_maybe(Cell)
MaybeDir = declare_maybe(Dir)

move = Function('move', Dir, Cell, MaybeCell)

for i in range(SZ):
    for j in range(SZ):
        c = cells[i][j]

        res = MaybeCell.just(cells[i][j-1]) if j > 0 else MaybeCell.nothing
        s.add(move(Dir.l, c) == res)

        res = MaybeCell.just(cells[i][j+1]) if j < SZ-1 else MaybeCell.nothing
        s.add(move(Dir.r, c) == res)

        res = MaybeCell.just(cells[i-1][j]) if i > 0 else MaybeCell.nothing
        s.add(move(Dir.u, c) == res)

        res = MaybeCell.just(cells[i+1][j]) if i < SZ-1 else MaybeCell.nothing
        s.add(move(Dir.d, c) == res)


belt_field = Function('belt_field', Cell, MaybeDir)
connected = Function('connected', Cell, Cell, BoolSort())

c1, c2, c3 = Consts(['c1', 'c2', 'c3'], Cell)
d = Const('d', Dir)
s.add(ForAll([c1], connected(c1, c1)))  # Reflexivity

s.add(ForAll([c1, c2], Implies(And(belt_field(c1) == MaybeDir.nothing,
                                   c1 != c2),
                               Not(connected(c1, c2)))))
# s.add(ForAll([c1, c2, c3], Implies(And(connected(c1, c2),  # Transitivity
#                                        connected(c2, c3)),
#                                    connected(c1, c3))))
# s.assert_and_track(ForAll([c1, c2, d], Implies(And(belt_field(c1) == MaybeDir.just(d),  # belt => connected
#                                       move(d, c1) == MaybeCell.just(c2)),
#                                   connected(c1, c2))), 'forw')

c2mu = move(Dir.u, c2); c2u = MaybeCell.getJust(c2mu)
c2md = move(Dir.d, c2); c2d = MaybeCell.getJust(c2md)
c2ml = move(Dir.l, c2); c2l = MaybeCell.getJust(c2ml)
c2mr = move(Dir.r, c2); c2r = MaybeCell.getJust(c2mr)

# s.assert_and_track(ForAll([c1,c2], Implies(And(c1 != c2, (connected(c1, c2))),
#                                                                 And(MaybeCell.is_just(c2ml),
#                                                                    belt_field(c2l) == MaybeDir.just(Dir.r),
#                                                                    connected(c1, c2l)))), 'back')
             #(Or(And(MaybeCell.is_just(c2mu),
#                                                                   belt_field(c2u) == MaybeDir.just(Dir.d),
#                                                                   connected(c1, c2u)),
#                                                               And(MaybeCell.is_just(c2md),
#                                                                   belt_field(c2d) == MaybeDir.just(Dir.u),
#                                                                   connected(c1, c2d)),
#                                                               And(MaybeCell.is_just(c2ml),
#                                                                   belt_field(c2l) == MaybeDir.just(Dir.r),
#                                                                   connected(c1, c2l)),
#                                                               And(MaybeCell.is_just(c2mr),
#                                                                   belt_field(c2r) == MaybeDir.just(Dir.l),
#                                                                   connected(c1, c2r))))))

s.assert_and_track(ForAll([c1,c2], Implies(c1 != c2, Or(And(connected(c1,c2), Not(connected(c2,c1))),
                                                       And(connected(c2,c1), Not(connected(c1,c2)))))), 'tst')

s.add(belt_field(cells[0][0]) == MaybeDir.just(Dir.r))
s.add(connected(cells[0][0], cells[0][1]))
s.add(Not (connected(cells[0][1], cells[0][0])))
if str(s.check()) == 'sat':
    m = s.model()
    print('connected', m[connected])
    print('belt_field', m[belt_field])
else:
    print('unsat!', s.check(), s.unsat_core())
