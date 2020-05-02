import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

import primitives as P
from factory import Factory


def plot_inserter(ins: P.Inserter, color='y'):
    p = ins.pos.eval()
    tgt = ins.sink().eval()
    d = ins.dir.eval()
    disp = P.dir_to_disp(d)
    plt.arrow((p.x + tgt.x) / 2 - disp[0] / 4, (p.y + tgt.y) / 2 - disp[1] / 4, disp[0] / 50, disp[1] / 50,
              width=0.1, length_includes_head=True, head_length=0.5,
              color=color)


def plot_rectangle(f: P.Rectangle, color='r'):
    p = f.pos.eval()
    r = patches.Rectangle((p.x - 0.5 + 0.2, p.y - 0.5 + 0.2), f.size_x - 0.4, f.size_y - 0.4, color=color)
    plt.gca().add_patch(r)


def plot_grid(corner1, corner2, padding=2):
    d = corner2 - corner1.eval_as_tuple()
    dx, dy = d.x, d.y
    max_d = max(dx,dy)

    px = (max_d - dx) // 2 + padding
    py = (max_d - dy) // 2 + padding

    x0, x1 = corner1.x - px, corner2.x + px
    y0, y1 = corner1.y - py, corner2.y + py

    plt.xlim(x0, x1)
    plt.ylim(y0, y1)
    plt.grid()
    plt.gca().xaxis.set_ticks(np.arange(x0 - 0.5, x1))
    plt.gca().yaxis.set_ticks(np.arange(y0 - 0.5, y1))

    plt.tick_params(
        axis='x',  # changes apply to the x-axis
        #    which='minor',      # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False)

    plt.tick_params(
        axis='y',  # changes apply to the x-axis
        #    which='minor',      # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelleft=False)


def plot_factory(f: Factory, title=None, size=None, show=False):
    assert isinstance(f, Factory)
    assert f.finalized

    if size:
        plt.figure(figsize=size)

    if title:
        plt.title(title)

    for ins in f.inserters:
        plot_inserter(ins, color='y')

    for m in f.buildings:
        plot_rectangle(m, color=m.color)

    encompassing = f.buildings[0].to_diag_seg().eval()
    for r in f.buildings:
        encompassing = P.Segment.merge(encompassing, r.to_diag_seg().eval())

    plot_grid(encompassing.p1.eval(), encompassing.p2.eval())

    if show:
        plt.show()
