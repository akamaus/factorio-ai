import unittest
import z3

from factory_theory.primitives import SOL, neighs, Abs, IntVal, \
    Point2D, Belt, \
    SegmentedBelt, Segment, non_intersecting_segs, non_intersecting_seg_belt_diag_seg, \
    Rectangle, \
    Dir, dir_to_disp, Inserter


class TestBase(unittest.TestCase):
    def setUp(self) -> None:
        SOL.fresh_solver()

    def check_near(self, p1c:tuple, p2c:tuple):
        return p1c[0] == p2c[0] and abs(p1c[1] - p2c[1]) == 1 or \
               p1c[1] == p2c[1] and abs(p1c[0] - p2c[0]) == 1


class TestPrimitives(TestBase):
    def test_neigh_segments(self):
        seg = Segment(Point2D(0,0), Point2D(1,1))

        ls = seg.left_neigh()
        self.assertEqual(Point2D(-1, 0), ls.p1)
        self.assertEqual(Point2D(-1, 1), ls.p2)

        rs = seg.right_neigh()
        self.assertEqual(Point2D(2, 0), rs.p1)
        self.assertEqual(Point2D(2, 1), rs.p2)

        bs = seg.bottom_neigh()
        self.assertEqual(Point2D(0, 2), bs.p1)
        self.assertEqual(Point2D(1, 2), bs.p2)

    def test_neigh_points(self):
        p1 = Point2D()
        p2 = Point2D()
        SOL.add(neighs(p1,p2))
        m = SOL.model()
        self.assertIsNotNone(m)
        p1c = p1.eval_as_tuple()
        p2c = p2.eval_as_tuple()
        self.assertTrue(self.check_near(p1c, p2c))

    def test_intersecting_rectangles(self):
        r1 = Rectangle(size=3, x=0, y=0)
        r2 = Rectangle(size=2, x=2, y=2)
        SOL.add(r1.intersecting(r2))
        m = SOL.model()
        self.assertIsNotNone(m)

    def test_non_intersecting_rectangles(self):
        r1 = Rectangle(x=0,y=0, size=2)
        r2 = Rectangle(x=2,y=0, size=3)
        SOL.add(r1.non_intersecting(r2))
        m = SOL.model()
        self.assertIsNotNone(m)

    def test_dir_to_disp(self):
        disp = dir_to_disp(Dir.u)
        self.assertEqual(0, disp[0])
        self.assertEqual(1, disp[1])

    def test_dir_to_disp_static(self):
        disp = dir_to_disp(Dir.u)
        self.assertEqual(0, disp[0])
        self.assertEqual(1, disp[1])

    def test_dir_to_disp_dynamic(self):
        dr = z3.Const('dir', Dir)
        SOL.add(dr == Dir.u)
        disp = dir_to_disp(dr)
        m = SOL.model()
        self.assertEqual(0, SOL.eval(disp[0]))
        self.assertEqual(1, SOL.eval(disp[1]))


class TestSol(TestBase):
    def test_shrinker(self):
        p1 = Point2D()
        dst = IntVal()
        SOL.add(dst.v == Abs(p1.x - 2) + Abs(p1.y - 3))
        dists = []
        for d in SOL.shrinker_loop(dst):
            dists.append(d)

        p1c = p1.eval_as_tuple()
        self.assertEqual(dists[-1], 0)
        self.assertEqual(p1c, (2,3))


class TestBelts(TestBase):
    def test_belt(self):
        belt = Belt()
        belt.fix_ends(source=(1,1), sink=(5,5))
        self.assertIsNotNone(SOL.model())

        pts = belt.eval_points()
        for i in range(len(pts)-1):
            self.assertTrue(self.check_near(pts[i], pts[i+1]))
        self.assertEqual(belt.source().eval_as_tuple(), (1, 1))
        self.assertEqual(belt.sink().eval_as_tuple(), (5, 5))

    def test_belt_shrink(self):
        belt = Belt()
        belt.fix_ends(source=(1,1), sink=(5,5))
        lens = []
        for l in SOL.shrinker_loop(belt.belt_len):
            lens.append(l)

        self.assertEqual(lens[-1], 9)

    def test_one_seg_belt(self):
        sbelt = SegmentedBelt()
        sbelt.fix_ends(source=(10, 10), sink=(15, 10))
        SOL.add(sbelt.num_segs == 1)
        m = SOL.model()
        self.assertIsNotNone(m)

        s = sbelt.segment(0)
        self.assertEqual(s.p1.eval_as_tuple(), (10,10))
        self.assertEqual(s.p2.eval_as_tuple(), (15,10))

    def test_two_seg_belt(self):
        sbelt = SegmentedBelt()
        sbelt.fix_ends(source=(10, 10), sink=(15, 15))
        SOL.add(sbelt.num_segs == 2)
        m = SOL.model()
        self.assertIsNotNone(m)

        s = sbelt.segment(0)
        p1 = s.p1
        p2 = s.p2

        self.assertEqual(p1.eval_as_tuple(), (10,10))
        self.assertTrue(p2.eval_as_tuple() in [(15,10), (10,15)])

        s = sbelt.segment(1)
        p2 = s.p2
        self.assertEqual(p2.eval_as_tuple(), (15,15))

    def test_seg_belt_shrink(self):
        sbelt = SegmentedBelt()
        sbelt.fix_ends(source=(10,10), sink=(15,15))
        seg_nums = []
        for l in SOL.shrinker_loop(sbelt.num_segs, init=10):
            seg_nums.append(l)
        self.assertEqual(seg_nums[-1], 2)

    def test_intersecting_segments1(self):
        s1 = Segment(Point2D(0,0), Point2D(10,0))
        s2 = Segment(Point2D(5, 5), Point2D(5, -5))
        SOL.add(non_intersecting_segs(s1, s2))
        m = SOL.model()
        self.assertIsNone(m)
    
    def test_intersecting_segments2(self):
        s1 = Segment(Point2D(0,0), Point2D(10,0))
        s2 = Segment(Point2D(5, 5), Point2D(5, -5))
        SOL.add(non_intersecting_segs(s2, s1))
        m = SOL.model()
        self.assertIsNone(m)

    def test_non_intersecting_segments1(self):
        s1 = Segment(Point2D(0, 0), Point2D(10, 0))
        s2 = Segment(Point2D(12, 5), Point2D(12, -5))
        SOL.add(non_intersecting_segs(s1, s2))
        m = SOL.model()
        self.assertIsNotNone(m)

    def test_intersecting_segbelt_and_dseg(self):
        sb = SegmentedBelt()
        SOL.add(sb.corner(0) == Point2D(0, 0))
        SOL.add(sb.corner(1) == Point2D(10, 0))
        SOL.add(sb.sink() == Point2D(20, 0))
        SOL.add(sb.num_segs >= 2)
        ds = Segment(Point2D(), Point2D(), is_diag=True)
        SOL.add(ds.p1 == Point2D(12, 0))
        SOL.add(ds.p2 == Point2D(15, 3))
        SOL.add(non_intersecting_seg_belt_diag_seg(sb, ds))
        d = None
        for d in SOL.shrinker_loop(sb.num_segs):
            pass
        self.assertEqual(4, d)

    def test_seg_contains_cases(self):
        SOL.fresh_solver()
        sb = Segment(p1=Point2D(0,0), p2=Point2D(10,0))
        SOL.add(sb.contains(Point2D(5,0)))
        self.assertIsNotNone(SOL.model())

        SOL.fresh_solver()
        sb = Segment(p1=Point2D(10, 0), p2=Point2D(0, 0))
        SOL.add(sb.contains(Point2D(5, 0)))
        self.assertIsNotNone(SOL.model())

        SOL.fresh_solver()
        sb = Segment(p1=Point2D(0, 0), p2=Point2D(0, 10))
        SOL.add(sb.contains(Point2D(0, 5)))
        self.assertIsNotNone(SOL.model())

        SOL.fresh_solver()
        sb = Segment(p1=Point2D(0, 10), p2=Point2D(0, 0))
        SOL.add(sb.contains(Point2D(0, 5)))
        self.assertIsNotNone(SOL.model())

    def test_seg_contains(self):
        sb = SegmentedBelt()
        SOL.add(sb.num_segs >= 2)
        SOL.add(sb.segment(0).contains(Point2D(5, 2)))
        SOL.add(sb.segment(1).contains(Point2D(10, 5)))
        SOL.add(sb.segment(0).horizontal())
        SOL.model()
        c1 = SOL.eval(sb.corner(1))
        self.assertEqual(c1, Point2D(10,2))

    def test_seg_belt_contains(self):
        sb = SegmentedBelt()
        SOL.add(sb.contains(Point2D(0, 0)))
        SOL.add(sb.contains(Point2D(10, 10)))
        d = None
        for d in SOL.shrinker_loop(sb.num_segs):
            pass
        self.assertEqual(2, d)

    def test_seg_belt_enumerate(self):
        sb = SegmentedBelt()
        SOL.add(sb.source() == (0,0))
        SOL.add(sb.sink() == (5,5))
        SOL.add(sb.num_segs < 5)
        ln = sb.len(5)

        for d in SOL.shrinker_loop(ln):
            pass

        self.assertEqual(11, d)

        p0 = None
        for p in sb.enumerate_points():
            if p0:
                dx = p.x - p0.x
                dy = p.y - p0.y
                self.assertTrue(dx == 0 and dy == 1 or dx == 1 and dy == 0)
            p0 = p


class TestInserters(TestBase):
    def test_inserter_chain(self):
        in1 = Inserter()
        in2 = Inserter()
        SOL.add(in1.source() == (0,0))
        SOL.add(in2.source() == in1.sink())
        SOL.add(in2.sink() == (4,0))

        self.assertIsNotNone(SOL.model())
        self.assertEqual((2,0), in1.sink().eval_as_tuple())
        self.assertEqual((1, 0), in1.pos.eval_as_tuple())
        self.assertTrue(in1.dir.eval().eq(Dir.r))
        self.assertTrue(in2.dir.eval().eq(Dir.r))

    def test_unit_inserter_connection(self):
        in1 = Inserter(unit_len_only=True)
        in2 = Inserter(unit_len_only=True)
        disp = IntVal()

        SOL.add(in1.source() == (0,0))
        SOL.add(in1.sink() == in2.source())
        x2 = in2.sink().x
        SOL.add(disp.v == -z3.If(x2 > 0, x2, -x2))

        for res in SOL.shrinker_loop(disp.v):
            pass
        self.assertEqual(-4, res)

    def test_long_inserter_connection(self):
        in1 = Inserter(unit_len_only=False)
        in2 = Inserter(unit_len_only=False)
        disp = IntVal()

        SOL.add(in1.source() == (0, 0))
        SOL.add(in1.sink() == in2.source())
        x2 = in2.sink().x
        SOL.add(disp.v == -z3.If(x2 > 0, x2, -x2))

        for res in SOL.shrinker_loop(disp.v):
            pass
        print('arm', in1.arm_len.eval())
        self.assertEqual(-8, res)
