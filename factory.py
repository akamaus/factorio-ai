import typing as T

import z3 as Z

import primitives as P

class Factory:
    """ Factory object for creating and managing all stuff on the map """
    def __init__(self):
        self.buildings: T.List[P.Rectangle] = []
        self.inserters: T.List[P.Inserter] = []
        self.segmented_belts: T.List[P.SegmentedBelt] = []

        P.SOL.fresh_solver()

    def new_machine(self, color:str):
        m = P.AssemblyMachine()
        m.color = color
        self.buildings.append(m)
        return m

    def new_inserter(self, color: str = 'y'):
        ins = P.Inserter()
        ins.color = color
        self.inserters.append(ins)
        return ins

    def connect_with_inserter(self, obj1, obj2) -> P.Inserter:
        if isinstance(obj1, P.Rectangle) and isinstance(obj2, P.Rectangle):
            ins = self.new_inserter()
            P.SOL.add(P.connection(obj1, ins, obj2))
            return ins
        else:
            raise('Unknown type pairs', type(obj1), type(obj2))

    def add_non_intersecting_all(self):
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

    def _forall_commutative_pairs(self, collection: list):
        for i in range(len(collection)):
            for j in range(i + 1, len(collection)):
                yield collection[i], collection[j]

    def _forall_pairs(self, col1: list, col2: list):
        for e1 in col1:
            for e2 in col2:
                yield e1,e2

    def finalize_and_model(self):
        self.add_non_intersecting_all()
        return P.SOL.model()
