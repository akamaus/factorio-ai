import z3

import primitives as P
from subfactory import SubFactory


class ProductionLine(SubFactory):
    """ AssemblyMachines or Drills built along straight line together with belts and inserters """
    
    def __init__(self, num_machines: int, machine_size: int, num_inputs: int, auto_output=False, color='gray'):
        """ num_machines - number of machines in a row 
            machine_size - size of a single machine(in cells)
            num_inputs - number of input lines (common for all machines as they presumably share a single program)
        """
        assert isinstance(num_machines, int)
        assert isinstance(machine_size, int)
        assert isinstance(num_inputs, int)
        self.num_machines = num_machines
        self.machine_size = machine_size
        self.num_inputs = num_inputs

        # conservative estimations (2 for inserters)
        area = P.Rectangle(size=P.Point2D(x=num_machines * machine_size, y=machine_size + num_inputs + 1 + 2))
        area.color = color
        area.opacity = 0.2
        super().__init__(area=area)

        self.model_machine = self.new_machine(size=machine_size, color='gray')

        self.input_belts = [self.new_segmented_belt() for _ in range(num_inputs)]
        self.input_inserters = [self.connect_with_inserter(self.input_belts[i], self.model_machine) for i in range(num_inputs)]
        self.output_belt = self.new_segmented_belt()

        # tying machine to left side
        self.add(self.model_machine.pos.x == self.area.pos.x)
        # constraining  belts positions
        area_ds = self.area.to_diag_seg()
        for b in self.input_belts + [self.output_belt]:
            P.SOL.add(b.num_segs == 1)
            P.SOL.add(b.segment(0).horizontal())
            P.SOL.add(z3.Or(z3.And(b.source().x == area_ds.p1.x, b.sink().x == area_ds.p2.x),
                            z3.And(b.source().x == area_ds.p2.x, b.sink().x == area_ds.p1.x)))

        if auto_output:
            ds_machine = self.model_machine.to_diag_seg()
            self.add(z3.Or(self.output_belt.segment(0).p1.y == ds_machine.p1.y - 1,
                           self.output_belt.segment(0).p1.y == ds_machine.p2.y + 1))
        else:
            self.connect_with_inserter(self.model_machine, self.output_belt)

    def input(self, k: int) -> P.Point2D:
        assert k < self.num_inputs
        return self.input_belts[k].source()

    def output(self) -> P.Point2D:
        return self.output_belt.sink()
