import typing as T
import z3
from z3 import Const, IntSort, And, Or, Function, Consts, ForAll, Implies, Not


class SolverWrapper:
    def __init__(self):
        self._sol = None
        self.fresh_solver()

    def fresh_solver(self):
        self._sol = z3.Solver()

    def add(self, *args):
        self._sol.add(*args)

    def eval(self, *args):
        return self._sol.model().eval(*args)

    def model(self):
        chk = self._sol.check()
        if chk.r == 1:
            return self._sol.model()

    def shrinker_loop(self, scalar, init=None, restore=True):
        if isinstance(scalar, IntVal):
            scalar = scalar.v

        self._sol.push()
        if init:
            self._sol.add(scalar <= init)
        best_val = None
        while self._sol.check().r == 1:
            scalar_val = self.eval(scalar).as_long()
            best_val = scalar_val
            yield scalar_val
            self._sol.pop()
            self._sol.push()
            self._sol.add(scalar < scalar_val)

        # Have to repeat check to restore model so it can be accessed by client code
        self._sol.pop()

        if restore and best_val is not None:
            self._sol.add(scalar == best_val)
            chk = self._sol.check()
            assert chk.r == 1


SOL: SolverWrapper = SolverWrapper()


class IntVal:
    _IDX = 0
    def __init__(self):
        self.v = Const(f'intval{self._IDX}', IntSort())
        self.__class__._IDX += 1

    def eval(self):
        return SOL.eval(self.v).as_long()


class Point2D:
    _IDX = 0
    def __init__(self, x=None, y=None):
        self.x = Const(f"p{self._IDX}_x", IntSort()) if x is None else x
        self.y = Const(f"p{self._IDX}_y", IntSort()) if y is None else y
        self.__class__._IDX += 1

    def __repr__(self):
        return f'Point2D({self.x},{self.y})'

    def __eq__(self, other):
        if isinstance(other, Point2D):
            x,y = other.x, other.y
        elif isinstance(other, tuple):
            assert len(other) == 2
            x,y = other
        return And(self.x == x, self.y == y)

    def eval_as_tuple(self):
        x = SOL.eval(self.x).as_long()
        y = SOL.eval(self.y).as_long()
        return x,y


def near_z(x, y):
    return Or(x == y+1, x == y-1)


def neighs(p1: Point2D, p2:Point2D):
    assert isinstance(p1, Point2D)
    assert isinstance(p2, Point2D)
    return Or(And(p1.x == p2.x, near_z(p1.y, p2.y)),
              And(p1.y == p2.y, near_z(p1.x, p2.x)))


def Abs(x):
    return z3.If(x >= 0, x, -x)


class Belt:
    _IDX = 0
    def __init__(self):
        self.belt_x = Function(f'belt{self._IDX}_x', IntSort(), IntSort())
        self.belt_y = Function(f'belt{self._IDX}_y', IntSort(), IntSort())
        self.belt_len = Const(f'belt{self._IDX}_len', IntSort())
        SOL.add(self.belt_len > 0)

        i,j = Consts("i j", IntSort())
        # neighbor condition
        SOL.add(ForAll([i], Implies(And(i < self.belt_len - 1, i >= 0),
                                    neighs(self[i], self[i+1]))))

        # no intersections
        SOL.add(ForAll([i, j], Implies(And(i >= 0, i < j, j < self.belt_len),
                                       Not(self[i] == self[j]))))
        self.__class__._IDX += 1

    def __getitem__(self, i):
        return Point2D(self.belt_x(i), self.belt_y(i))

    def source(self):
        return self[0]

    def sink(self):
        return self[self.belt_len-1]

    def lazy_points(self)->T.List[Point2D]:
        m = SOL.model()
        blen = m.eval(self.belt_len).as_long()
        points = []
        for k in range(0, blen):
            points.append(self[k])
        return points

    def eval_points(self)->T.List[T.Tuple[int,int]]:
        m = SOL.model()
        blen = m.eval(self.belt_len).as_long()
        points = []
        for k in range(0, blen):
            points.append(self[k].eval_as_tuple())
        return points

    # convenience
    def fix_ends(self, source, sink):
        SOL.add(self.source() == source)
        SOL.add(self.sink() == sink)


def no_intersections(belt1: Belt, belt2: Belt):
    assert isinstance(belt1, Belt)
    assert isinstance(belt2, Belt)

    i,j = Consts("i j", IntSort())
    SOL.add(ForAll([i,j], Implies(And(0 <= i, i < belt1.belt_len, 0 <=j, j < belt2.belt_len),
                                  Not(belt1[i] == belt2[j]))))