from time import time

import z3

from .base_types import BasePoint2D, BaseSegment


z3.set_param('model.completion', True)


def _is_IntVal(val):
    return val.__class__.__name__ == 'IntVal'


class SolverWrapper:
    def __init__(self):
        self._sol = None
        self.fresh_solver()

    def fresh_solver(self, tactic='default'):
        if isinstance(tactic, str):
            tactic = z3.Tactic(tactic)
        self._sol = tactic.solver()

    def add(self, *args):
        self._sol.add(*args)

    def eval(self, arg):
        """ Smart evaluator, if base type is passed returns as is, if z3 sort - evaluates, if aggregate object - invokes .eval method """
        if isinstance(arg, int):
            return arg

        if isinstance(arg, (BasePoint2D, BaseSegment)):
            return arg.eval()

        res = self._sol.model().eval(arg)
        if isinstance(res, (z3.IntNumRef, z3.ArithRef)):
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
        if _is_IntVal(scalar):  # FIXME hacky, but have to break dependency loop somehow
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

    def binary_shrinking(self, scalar, lower=0, upper=None):
        if _is_IntVal(scalar):
            scalar = scalar.v

        self._sol.push()

        best_val = None

        while upper is None or upper - lower >= 1:
            if upper is not None:
                border = (lower + upper) // 2
            else:
                border = None
            print('LBU', lower, border, upper)
            t0 = time()

            self._sol.add(lower <= scalar)

            if border:
                self._sol.add(scalar <= border)
            res = self._sol.check()
            dt = time() - t0
            print(f'R={res.r}; T={dt:0.3f}')
            if res.r == 1:
                scalar_val = self.eval(scalar)
                print('V=', scalar_val)
                upper = scalar_val
                if best_val is None or best_val > scalar_val:
                    best_val = scalar_val
            elif border is None:
                print('V=unsat')
                return None  # No solution at all
            else:
                lower = border + 1

            self._sol.pop()
            self._sol.push()

        # Have to repeat check to restore model so it can be accessed by client code
        self._sol.pop()

        if res.r != 1:
            assert best_val is not None
            self._sol.add(scalar == best_val)
            chk = self._sol.check()
            assert chk.r == 1

        return best_val

