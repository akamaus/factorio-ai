import typing as T
import z3
from z3 import Const, IntSort, And, Or, Function, Consts, ForAll, Implies, Not


# General
class SolverWrapper:
    def __init__(self):
        self._sol = None
        self.fresh_solver()

    def fresh_solver(self):
        self._sol = z3.Solver()

    def add(self, *args):
        self._sol.add(*args)

    def eval(self, arg):
        """ Smart evaluator, if base type is passed returns as is, if z3 sort - evaluates, if aggregate object - invokes .eval method """
        if isinstance(arg, int):
            return arg

        if isinstance(arg, (Point2D, Segment)):
            return arg.eval()

        res = self._sol.model().eval(arg)
        if isinstance(res, z3.IntNumRef):
            res = res.as_long()
        elif isinstance(res, z3.DatatypeRef):
            pass
        else:
            raise ValueError('unknown result', type(res), res)
        return res

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
            scalar_val = self.eval(scalar)
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
    def __init__(self, label='', value=None):
        if value is None:
            self.v = Const(f'intval_{label}{self._IDX}', IntSort())
            self.__class__._IDX += 1
        else:
            self.v = value

    def eval(self):
        return SOL.eval(self.v)


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
        else:
            raise ValueError('strange type for', other)

        resx = self.x == x
        resy = self.y == y

        if resx is True and resy is True:
            return True
        elif resx is False or resy is False:
            return False
        elif resx is True:
            return resy
        elif resy is True:
            return resx
        else:
            return And(resx, resy)

    def __add__(self, disp: tuple):
        assert isinstance(disp, tuple)
        return Point2D(self.x + disp[0], self.y + disp[1])

    def __sub__(self, disp: tuple):
        assert isinstance(disp, tuple)
        return Point2D(self.x - disp[0], self.y - disp[1])

    def eval(self):
        x = SOL.eval(self.x)
        y = SOL.eval(self.y)
        return Point2D(x,y)

    def eval_as_tuple(self):
        x = SOL.eval(self.x)
        y = SOL.eval(self.y)
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


def Max(x,y):
    return z3.If(x > y, x, y)


def Min(x, y):
    return z3.If(x < y, x, y)


# Belts
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
        blen = m.eval(self.belt_len)
        points = []
        for k in range(0, blen):
            points.append(self[k])
        return points

    def eval_points(self)->T.List[T.Tuple[int,int]]:
        m = SOL.model()
        assert(m)
        blen = SOL.eval(self.belt_len)
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
    return ForAll([i,j], Implies(And(0 <= i, i < belt1.belt_len, 0 <=j, j < belt2.belt_len),
                                 Not(belt1[i] == belt2[j])))


class Segment:
    def __init__(self, p1:Point2D, p2:Point2D, is_diag:bool=False):
        assert isinstance(p1, Point2D)
        assert isinstance(p2, Point2D)
        self.p1 = p1
        self.p2 = p2
        self.is_diag = is_diag

    def __repr__(self):
        return(f'Segment({repr(self.p1)}, {repr(self.p2)})')

    def horizontal(self):
        assert not self.is_diag
        return self.p1.y == self.p2.y

    def vertical(self):
        assert not self.is_diag
        return self.p1.x == self.p2.x

    def contains(self, p: Point2D):
        assert isinstance(p, Point2D)
        assert not self.is_diag
        return Or(And(self.horizontal(), self.p1.y == p.y,  self.p1.x <= p.x, p.x <= self.p2.x),
                  And(self.vertical(), self.p1.x == p.x, self.p1.y <= p.y, p.y <= self.p2.y))

    def eval(self):
        p1 = self.p1.eval()
        p2 = self.p2.eval()
        return Segment(p1,p2, self.is_diag)

    @classmethod
    def merge(self, seg1, seg2):
        assert isinstance(seg1, Segment)
        assert isinstance(seg2, Segment)
        return Segment(Point2D(min(seg1.p1.x, seg2.p1.x), min(seg1.p1.y, seg2.p1.y)),
                       Point2D(max(seg1.p2.x, seg2.p2.x), max(seg1.p2.y, seg2.p2.y)), is_diag=True)

class SegmentedBelt:
    _IDX = 0
    def __init__(self):
        self.corners_x = Function(f'seg_belt{self._IDX}_x', IntSort(), IntSort())
        self.corners_y = Function(f'seg_belt{self._IDX}_y', IntSort(), IntSort())
        self.num_segs = Const(f'seg_belt{self._IDX}_num_segs', IntSort())
        SOL.add(self.num_segs > 0)

        i,j = Consts("i j", IntSort())
        SOL.add(ForAll([i], Implies(And(0 <= i, i < self.num_segs),
                                    Or(self.segment(i).horizontal(), self.segment(i).vertical()))))

        self.__class__._IDX += 1

    def corner(self, i) -> Point2D:
        return Point2D(self.corners_x(i), self.corners_y(i))

    def segment(self, i) -> Segment:
        return Segment(self.corner(i) , self.corner(i+1))

    def source(self):
        return Point2D(self.corners_x(0), self.corners_y(0))

    def sink(self):
        return Point2D(self.corners_x(self.num_segs), self.corners_y(self.num_segs))

    def not_contains(self, p: Point2D):
        i = Const("i", IntSort())
        return (ForAll([i], Implies(And(0 <= i, i < self.num_segs), Not(self.segment(i).contains(p)))))

    def contains(self, p: Point2D):
        return Not(self.not_contains(p))

    def fix_ends(self, source, sink):
        SOL.add(self.source() == source)
        SOL.add(self.sink() == sink)

    def eval_corners(self)->T.List[T.Tuple[int, int]]:
        points = []
        nc = SOL.eval(self.num_segs) + 1
        for i in range(nc):
            p = Point2D(self.corners_x(i), self.corners_y(i))
            t = p.eval_as_tuple()
            points.append(t)
        return points

    def eval_area(self) -> Segment:
        """ Returns Diagonal segment bounding belt's area """
        corners = self.eval_corners()
        x1 = min(map(lambda c: c[0], corners))
        x2 = max(map(lambda c: c[0], corners))
        y1 = min(map(lambda c: c[1], corners))
        y2 = max(map(lambda c: c[1], corners))
        return Segment(Point2D(x1,y1), Point2D(x2,y2), is_diag=True)


def non_intersecting_segs(s1: Segment, s2: Segment):
    assert isinstance(s1, Segment)
    assert isinstance(s2, Segment)
    return Or(Max(s1.p1.x, s1.p2.x) < Min(s2.p1.x, s2.p2.x),
              Max(s1.p1.y, s1.p2.y) < Min(s2.p1.y, s2.p2.y),
              Max(s2.p1.x, s2.p2.x) < Min(s1.p1.x, s1.p2.x),
              Max(s2.p1.y, s2.p2.y) < Min(s1.p1.y, s1.p2.y))


def non_intersecting_seg_belts(belt1: SegmentedBelt , belt2: SegmentedBelt):
    assert isinstance(belt1, SegmentedBelt)
    assert isinstance(belt2, SegmentedBelt)

    i,j = Consts("i j", IntSort())
    return ForAll([i,j], Implies(And(0 <= i, i < belt1.num_segs, 0 <=j, j < belt2.num_segs),
                                 non_intersecting_segs(belt1.segment(i), belt2.segment(j))))


def non_intersecting_seg_belt_diag_seg(belt: SegmentedBelt, dseg: Segment):
    """ all segments of a belt must not intersect a given ordered diagonal segment """
    assert isinstance(belt, SegmentedBelt)
    assert isinstance(dseg, Segment)
    assert dseg.is_diag

    i = Const("i", IntSort())
    return ForAll([i], Implies(And(0 <= i, i < belt.num_segs),
                                   Or(Max(belt.segment(i).p1.x, belt.segment(i).p2.x) < dseg.p1.x,
                                      Min(belt.segment(i).p1.x, belt.segment(i).p2.x) > dseg.p2.x,
                                      Max(belt.segment(i).p1.y, belt.segment(i).p2.y) < dseg.p1.y,
                                      Min(belt.segment(i).p1.y, belt.segment(i).p2.y) > dseg.p2.y)))


# Buildings
class Rectangle:
    """ Generic class for all rectangular things, supports both floating and fixed locations """
    def __init__(self, size_x, size_y,  x=None, y=None):
        self.pos = Point2D(x,y)

        self.size_x = size_x
        self.size_y = size_y

    def to_diag_seg(self)->Segment:
        return Segment(self.pos, self.pos + (self.size_x-1, self.size_y-1), is_diag=True)

    def non_intersecting(self, other: 'Rectangle'):
        assert isinstance(other, Rectangle)
        s1 = self.to_diag_seg()
        s2 = other.to_diag_seg()

        return Or(s1.p2.x < s2.p1.x, s1.p2.y < s2.p1.y,
                  s2.p2.x < s1.p1.x, s2.p2.y < s1.p1.y)

    def intersecting(self, other: 'Rectangle'):
        return Not(self.non_intersecting(other))

    def contains(self, p: Point2D):
        assert isinstance(p, Point2D)
        s = self.to_diag_seg()
        return And(s.p1.x <= p.x, p.x <= s.p2.x,
                   s.p1.y <= p.y, p.y <= s.p2.y)


def non_intersecting_rectangles(*rects: T.List[Rectangle]):
    if len(rects) == 1 and isinstance(rects[0], list):
        rects = rects[0]
    assert len(rects) >= 2
    cases = []
    for i in range(len(rects)):
        assert isinstance(rects[i], Rectangle)
        for j in range(i+1, len(rects)):
            cases.append(rects[i].non_intersecting(rects[j]))
    return And(cases)



class AssemblyMachine(Rectangle):
    def __init__(self, x=None, y=None):
        super().__init__(3,3, x, y)


Dir = z3.Datatype('Dir')
Dir.declare('u')
Dir.declare('d')
Dir.declare('l')
Dir.declare('r')
Dir = Dir.create()


class DirVal:
    _IDX = 0
    def __init__(self, label=''):
        self.v = Const(f'dirval_{label}{self._IDX}', Dir)
        self.__class__._IDX += 1

    def eval(self):
        return SOL.eval(self.v)


def dir_to_disp(x: T.Union[DirVal, z3.DatatypeRef], length:T.Union[int, z3.Int] = 1) -> tuple:
    if isinstance(x, DirVal):
        x = x.v

    assert isinstance(x, z3.DatatypeRef)
    if x.eq(Dir.u):
        res = (0,length)
    elif x.eq(Dir.d):
        res = (0, -length)
    elif x.eq(Dir.r):
        res = (length, 0)
    elif x.eq(Dir.l):
        res = (-length, 0)
    else:
        If = z3.If
        res_x = If(Dir.is_r(x), length, If(Dir.is_l(x), -length, 0))
        res_y = If(Dir.is_u(x), length, If(Dir.is_d(x), -length, 0))
        res = (res_x, res_y)
    return res


class Inserter:
    def __init__(self, unit_len_only=True):
        self.pos = Point2D()
        self.dir = DirVal()
        self.arm_len = IntVal(value=1 if unit_len_only else None)
        if not unit_len_only:
            SOL.add(And(1 <= self.arm_len.v, self.arm_len.v <= 2))

    def source(self) -> Point2D:
        disp = dir_to_disp(self.dir, length=self.arm_len.v)
        return self.pos - disp

    def sink(self) -> Point2D:
        disp = dir_to_disp(self.dir, length=self.arm_len.v)
        return self.pos + disp


def connection(r1: Rectangle, ins: Inserter, r2: Rectangle):
    assert isinstance(r1, Rectangle)
    assert isinstance(r2, Rectangle)
    assert isinstance(ins, Inserter)
    return And(Not(r1.contains(ins.pos)), Not(r2.contains(ins.pos)),
               r1.contains(ins.source()), r2.contains(ins.sink()))
