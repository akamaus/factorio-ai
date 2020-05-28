import numpy as np

from primitives import Point2D, Segment


def entity_block(entities, name):
    enmap = {}
    coords = []
    amounts = []

    for e in entities:
        if e['name'] == name:
            pos = int(e['position']['x']), int(e['position']['y'])
            coords.append(pos)
            amounts.append(e['amount'])

            enmap[pos] = e['amount']

    coords = np.array(coords)
    amounts = np.array(amounts)

    center = np.sum(coords * amounts.reshape(-1, 1), axis=0) / np.sum(amounts)
    pc = Point2D(int(center[0]), int(center[1]))
    block = Segment(pc, pc)

    def fully_occupied(s: Segment):
        for p in s.enumerate_points():
            if (p.x, p.y) not in enmap:
                return False
        return True

    while True:
        enlarged = False

        if fully_occupied(block.left_neigh()):
            block.p1 = block.p1.left()
            enlarged = True

        if fully_occupied(block.right_neigh()):
            block.p2 = block.p2.right()
            enlarged = True

        if fully_occupied(block.top_neigh()):
            block.p1 = block.p1.top()
            enlarged = True

        if fully_occupied(block.bottom_neigh()):
            block.p2 = block.p2.bottom()
            enlarged = True

        if not enlarged:
            break

    return block


