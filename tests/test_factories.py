import unittest

from factory_theory.factory import Factory


class TestFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.f = Factory()

    def test_trivial(self):
        f = self.f
        metric = f.area.size.x + f.area.size.y
        m1 = f.new_machine('r')

        m, metric = f.finalize_and_model(minimize_metric=metric)
        self.assertEqual(6, metric)

    def test_two_machines_and_belt(self):
        f = self.f
        metric = f.area.size.x + f.area.size.y
        m1 = f.new_machine('g')
        m2 = f.new_machine('r')
        b = f.new_segmented_belt()
        f.add(b.num_segs == 1)

        f.connect_with_inserter(m1, b)
        f.connect_with_inserter(b, m2)

        m, metric = f.finalize_and_model(minimize_metric=metric)
        self.assertEqual(9, metric)

    def test_machine_and_belt_all_sides(self):

        locs = [(-10, 0), (10, 0),
                (-10, 6), (10, 6)]

        for loc in locs:
            f = Factory()
            m = f.new_machine(color='r')
            f.add(m.pos == (0, 2))
            b = f.new_segmented_belt()
            f.add(b.num_segs == 1)
            f.add(b.segment(0).horizontal())
            f.add(b.source() == loc)
            f.connect_with_inserter(b, m)
            m = f.finalize_and_model()
            self.assertIsNotNone(m, f'should be connectable {loc}')

    def test_processing_line_input_output_locations(self):
        S = 4

        locs = [(0,0), (0,6), (11, 6), (11, 0)]

        for l1, l2 in Factory._forall_pairs(locs, locs):
            f = Factory()
            pl = f.new_production_line(num_machines=S, machine_size=3, num_inputs=1, color='g')
            f.add(pl.area.pos == (0, 0))

            f.add(pl.input(0) == l1)
            f.add(pl.output() == l2)

            m = f.finalize_and_model()
            if l1[1] != l2[1]:
                self.assertIsNotNone(m, f'should be solution for l1={l1}, l2={l2}')
            else:
                self.assertIsNone(m, f'should be unsolvable for l1={l1}, l2={l2}')
