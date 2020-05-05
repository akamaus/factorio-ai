import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

import primitives as P
from factory import Factory
from subfactory import SubFactory


def plot_inserter(ins: P.Inserter, color='y'):
    p = ins.pos.eval()
    tgt = ins.sink().eval()
    d = ins.dir.eval()
    disp = P.dir_to_disp(d)
    plt.arrow((p.x + tgt.x) / 2 - disp[0] / 4, (p.y + tgt.y) / 2 - disp[1] / 4, disp[0] / 50, disp[1] / 50,
              width=0.1, length_includes_head=True, head_length=0.5,
              color=color)


def plot_rectangle(f: P.Rectangle, gap=0.2, color='r', opacity=None):
    p = f.pos.eval()
    sx,sy = f.size.eval_as_tuple()
    r = patches.Rectangle((p.x - 0.5 + gap, p.y - 0.5 + gap), sx - 2*gap, sy - 2*gap, color=color, alpha=opacity)
    plt.gca().add_patch(r)


def plot_segmented_belt(belt: P.SegmentedBelt, color='gray'):
    GAP=0.1
    corners = belt.eval_corners()
    for c1, c2 in zip(corners, corners[1:]):
        x1 = min(c1[0], c2[0])
        x2 = max(c1[0], c2[0])
        y1 = min(c1[1], c2[1])
        y2 = max(c1[1], c2[1])

        r = patches.Rectangle((x1 - 0.5 + GAP, y1 - 0.5 + GAP), x2 - x1 + 1 - 2*GAP, y2 - y1 + 1 - 2*GAP, color=color)
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


def plot_subfactory(f: SubFactory):
    assert isinstance(f, SubFactory)
    assert f.finalized

    for ins in f.inserters:
        plot_inserter(ins, color='y')

    for m in f.buildings:
        if isinstance(m, P.AssemblyMachine):
            plot_rectangle(m, color=m.color)

    for sb in f.segmented_belts:
        plot_segmented_belt(sb, color=sb.color)

    for a in f.areas:
        plot_rectangle(a, color=a.color, opacity=a.opacity, gap=0)

    plot_rectangle(f.area, color=getattr(f.area, 'color', 'gray'), opacity=0.2, gap=0)


def plot_factory(f: Factory, title=None, size=None, show=False):

    if size:
        plt.figure(figsize=size)

    if title:
        plt.title(title)

    for pl in f.production_lines:
        plot_subfactory(pl)

    plot_subfactory(f)

    # Calculating occupied area, setting limites and drawing grid
    encompassing = f.buildings[0].to_diag_seg().eval()

    def all_areas():
        for b in f.buildings:
            yield b.to_diag_seg().eval()

        for sb in f.segmented_belts:
            yield sb.eval_area()

        for a in f.areas:
            yield a.to_diag_seg().eval()

    for area in all_areas():
        encompassing = P.Segment.merge(encompassing, area)

    plot_grid(encompassing.p1.eval(), encompassing.p2.eval())

    if show:
        plt.show()
