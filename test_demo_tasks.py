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

    def test_factory_minification(self):
        from factory import Factory

        MAX_SEGS = 1
        N = 2
        f = Factory()
        prods1 = [f.new_machine('b') for _ in range(N)]
        prods2 = [f.new_machine('g') for _ in range(N)]
        prods3 = [f.new_machine('r') for _ in range(N)]
        sbelt12 = f.new_segmented_belt()
        sbelt23 = f.new_segmented_belt()

        metric = IntVal()

        f.add(metric.v == f.area.size.x + f.area.size.y)

        prod1_area = f.new_area(None, None, color='blue', opacity=0.2)
        prod2_area = f.new_area(None, None, color='green', opacity=0.2)
        prod3_area = f.new_area(None, None, color='red', opacity=0.2)

        for a1, a2 in f._forall_commutative_pairs([prod1_area, prod2_area, prod3_area]):
            f.add(a1.non_intersecting(a2))

        f.add(sbelt12.num_segs <= MAX_SEGS)
        f.add(sbelt23.num_segs <= MAX_SEGS)

        for p1 in prods1:
            f.connect_with_inserter(p1, sbelt12)
            f.add(p1.inside(prod1_area))

        for p2 in prods2:
            f.connect_with_inserter(sbelt12, p2)
            f.connect_with_inserter(p2, sbelt23)
            f.add(p2.inside(prod2_area))

        for p3 in prods3:
            f.connect_with_inserter(sbelt23, p3)
            f.add(p3.inside(prod3_area))

        m, metric = f.finalize_and_model(metric)
        self.assertIsNotNone(m)
        self.assertEqual(18, metric)

    def test_production_line_stacking(self):
        from factory import Factory

        S1 = 15
        S2 = 10
        S3 = S2
        f = Factory()
        p1 = f.new_production_line(num_machines=S1, machine_size=2, num_inputs=0, auto_output=True, color='b')
        p2 = f.new_production_line(num_machines=S2, machine_size=3, num_inputs=1, color='g')
        p3 = f.new_production_line(num_machines=S3, machine_size=3, num_inputs=1, color='r')

        f.connect_with_inserter(p1.output(), p2.input(0))
        f.connect_with_inserter(p2.output(), p3.input(0))

        metric = f.area.size.x + f.area.size.y
        model, best_metric = f.finalize_and_model(minimize_metric=metric)
        self.assertEqual(49, best_metric)