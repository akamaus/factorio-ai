import unittest

from primitives import SOL, neighs, Abs, IntVal, \
    Point2D, Belt, \
    SegmentedBelt, Segment, non_intersecting_segs

class TestPrimitives(unittest.TestCase):
    def setUp(self) -> None:
        SOL.fresh_solver()

    def check_near(self, p1c:tuple, p2c:tuple):
        return p1c[0] == p2c[0] and abs(p1c[1] - p2c[1]) == 1 or \
               p1c[1] == p2c[1] and abs(p1c[0] - p2c[0]) == 1

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

    def test_neigh_points(self):
        p1 = Point2D()
        p2 = Point2D()
        SOL.add(neighs(p1,p2))
        m = SOL.model()
        self.assertIsNotNone(m)
        p1c = p1.eval_as_tuple()
        p2c = p2.eval_as_tuple()
        self.assertTrue(self.check_near(p1c, p2c))

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

        p1, p2 = sbelt.segment(0)
        self.assertEqual(p1.eval_as_tuple(), (10,10))
        self.assertEqual(p2.eval_as_tuple(), (15,10))

    def test_two_seg_belt(self):
        sbelt = SegmentedBelt()
        sbelt.fix_ends(source=(10, 10), sink=(15, 15))
        SOL.add(sbelt.num_segs == 2)
        m = SOL.model()
        self.assertIsNotNone(m)

        p1, p2 = sbelt.segment(0)
        print(p1.eval_as_tuple(),p2.eval_as_tuple())

        self.assertEqual(p1.eval_as_tuple(), (10,10))
        self.assertTrue(p2.eval_as_tuple() in [(15,10), (10,15)])

        p1, p2 = sbelt.segment(1)
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
        
