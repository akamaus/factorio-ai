from time import time
import unittest

from primitives import SOL, IntVal, \
    Belt, no_intersections, \
    SegmentedBelt, non_intersecting_seg_belts


class TestDemoTasks(unittest.TestCase):
    def setUp(self) -> None:
        SOL.fresh_solver()

    def test_three_belts(self):
        """ Three belts crossing each other if drawn straight. Minifying total length """
        belt1 = Belt()
        belt2 = Belt()
        belt3 = Belt()

        SOL.add(no_intersections(belt1, belt2))
        SOL.add(no_intersections(belt1, belt3))
        SOL.add(no_intersections(belt2, belt3))

        belt1.fix_ends((0, 0), (4, 4))
        belt2.fix_ends((0, 2), (4, 2))
        belt3.fix_ends((0, 4), (4, 0))

        sz = IntVal()
        SOL.add(sz.v == belt1.belt_len + belt2.belt_len + belt3.belt_len)

        t0 = time()
        dts = []
        sizes = []
        for cur_sz in SOL.shrinker_loop(sz, init=38, restore=False):
            t1 = time()
            dts.append(t1 - t0)
            t0 = time()

            sizes.append(cur_sz)

        self.assertGreater(len(sizes), 0)
        self.assertEqual(sizes[-1], 29)  # number got from experiments with visualization

    def test_three_seg_belts(self):
        """ There segmented belts crossing each other if drawn straight.
        Total length is minified by iterative tightening of constaint """

        belt1 = SegmentedBelt()
        belt2 = SegmentedBelt()
        belt3 = SegmentedBelt()

        SOL.add(non_intersecting_seg_belts(belt1, belt2))
        SOL.add(non_intersecting_seg_belts(belt1, belt3))
        SOL.add(non_intersecting_seg_belts(belt2, belt3))

        belt1.fix_ends((0,0), (20, 20))
        belt2.fix_ends((0,10), (20, 10))
        belt3.fix_ends((0,20), (20, 0))

        sz = IntVal()
        SOL.add(sz.v == belt1.num_segs + belt2.num_segs + belt3.num_segs)

        t0 = time()
        dts = []
        sizes = []

        for cur_sz in SOL.shrinker_loop(sz, init=38, restore=False):
            t1 = time()
            dts.append(t1 - t0)
            t0 = time()
            sizes.append(cur_sz)

        self.assertGreater(len(sizes), 0)
        self.assertEqual(9, sizes[-1])  # number got from experiments with visualization
