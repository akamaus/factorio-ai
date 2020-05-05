import typing as T

import z3 as Z

import primitives as P


class SubFactory:
    def __init__(self, area: T.Optional = None):
        self.area = P.Rectangle(size=None) if area is None else area
        # These are elements managed by this subfactory
        self.buildings: T.List[P.Rectangle] = []
        self.inserters: T.List[P.Inserter] = []
        self.segmented_belts: T.List[P.SegmentedBelt] = []

        self.areas: T.List[P.Rectangle] = []

        self.finalized = False

    # Constructing
    def new_machine(self, color: str, size=3):
        m = P.AssemblyMachine(size)
        m.color = color
        self.buildings.append(m)
        return m

    def new_inserter(self, color: str = 'y'):
        ins = P.Inserter()
        ins.color = color
        self.inserters.append(ins)
        return ins

    def new_segmented_belt(self, color: str = 'gray'):
        b = P.SegmentedBelt()
        b.color = color
        self.segmented_belts.append(b)
        return b

    def new_area(self, p1: T.Optional[tuple], p2: T.Optional[tuple], color: str, opacity=0.5):
        if p1 and p2:
            r = P.Rectangle(size=P.Point2D(p2[0] - p1[0] + 1, p2[1] - p1[1] + 1), x=p1[0], y=p1[1])
        elif p1 is None and p2 is None:
            r = P.Rectangle(size=None)
        else:
            raise ValueError('area must be either fully specified or fully symbolic')

        r.color = color
        r.opacity = opacity
        self.areas.append(r)
        return r

    # Connecting
    def connect_with_inserter(self, obj1, obj2) -> P.Inserter:
        assert isinstance(obj1, (P.Point2D, P.Rectangle, P.SegmentedBelt)), f"Strange type of obj1: {type(obj1)}"
        assert isinstance(obj2, (P.Point2D, P.Rectangle, P.SegmentedBelt)), f"Strange type of obj2: {type(obj2)}"

        ins = self.new_inserter()
        if isinstance(obj1, P.Point2D):
            P.SOL.add(obj1 == ins.source())
        else:
            P.SOL.add(obj1.contains(ins.source()))

        if isinstance(obj2, P.Point2D):
            P.SOL.add(obj2 == ins.sink())
        else:
            P.SOL.add(obj2.contains(ins.sink()))

        return ins

    @classmethod
    def add(self, constraint):
        """ Add arbitrary constraint """
        P.SOL.add(constraint)

    # Finalization
    def finalize(self):
        assert not self.finalized
        self._add_non_intersecting_all()

        for b in self.buildings:
            self.add(b.inside(self.area))

        self.finalized = True

    def _add_non_intersecting_all(self):
        # forbid intra-class intersections
        P.SOL.add(P.non_intersecting_rectangles(self.buildings))

        for ins1, ins2 in self._forall_commutative_pairs(self.inserters):
            P.SOL.add(Z.Not(ins1.pos == ins2.pos))

        for sb1, sb2 in self._forall_commutative_pairs(self.segmented_belts):
            P.SOL.add(P.non_intersecting_seg_belts(sb1, sb2))

        # forbid inter-class intersections
        for b, ins in self._forall_pairs(self.buildings, self.inserters):
            P.SOL.add(Z.Not(b.contains(ins.pos)))

        for b, sb in self._forall_pairs(self.buildings, self.segmented_belts):
            P.SOL.add(P.non_intersecting_seg_belt_diag_seg(sb, b.to_diag_seg()))

        for ins, sb in self._forall_pairs(self.inserters, self.segmented_belts):
            P.SOL.add(sb.not_contains(ins.pos))

    @staticmethod
    def _forall_commutative_pairs(collection: list):
        for i in range(len(collection)):
            for j in range(i + 1, len(collection)):
                yield collection[i], collection[j]

    @staticmethod
    def _forall_pairs(col1: list, col2: list):
        for e1 in col1:
            for e2 in col2:
                yield e1, e2