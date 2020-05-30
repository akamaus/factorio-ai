from time import time
import typing as T

from factory_theory import primitives as P
from factory_theory.subfactory import SubFactory
from factory_theory.production_line import ProductionLine


class Factory(SubFactory):
    """ Factory object for creating and managing all stuff on the map """
    def __init__(self):
        super().__init__()
        self.production_lines = []

        self.elapsed_time: T.Optional[float] = None
        P.SOL.fresh_solver()

    def new_production_line(self, num_machines: int, machine_size: int,
                            num_inputs: int, auto_output=False, color='gray'):
        pl = ProductionLine(num_machines=num_machines, machine_size=machine_size,
                            num_inputs=num_inputs, auto_output=auto_output, color=color)

        self.production_lines.append(pl)
        self.buildings.append(pl.area)

        return pl

    def finalize(self):
        for pl in self.production_lines:
            pl.finalize()

        super().finalize()

    def finalize_and_model(self, minimize_metric=None):
        """ Adds final constraints and solves for model """
        self.finalize()

        t0 = time()
        metric = None
        if minimize_metric is not None:
            metric = P.SOL.binary_shrinking(minimize_metric, 0, None)
        m = P.SOL.model()
        self.elapsed_time = time() - t0

        if m:
            self.postprocess()
            for pl in self.production_lines:
                pl.postprocess()
            return m, metric

