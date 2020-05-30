import typing as T


class BasePoint2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'Point2D({self.x},{self.y})'

    def __eq__(self, other):
        print('BaseEq')
        if isinstance(other, BasePoint2D):
            x,y = other.x, other.y
        elif isinstance(other, tuple):
            assert len(other) == 2
            x,y = other
        else:
            raise ValueError('strange type for', other)

        resx = self.x == x
        resy = self.y == y

        return resx and resy

    def __add__(self, disp: tuple):
        assert isinstance(disp, tuple)
        return self.__class__(self.x + disp[0], self.y + disp[1])

    def __sub__(self, disp: tuple):
        assert isinstance(disp, tuple)
        return self.__class__(self.x - disp[0], self.y - disp[1])

    def right(self):
        return self.__class__(self.x + 1, self.y)

    def left(self):
        return self.__class__(self.x - 1, self.y)

    def top(self):
        return self.__class__(self.x, self.y - 1)

    def bottom(self):
        return self.__class__(self.x, self.y + 1)

    def as_tuple(self):
        return self.x, self.y

    def round(self):
        assert isinstance(self.x, (int, float))
        assert isinstance(self.y, (int, float))
        return BasePoint2D(round(self.x), round(self.y))


class BaseSegment:
    def __init__(self, p1: BasePoint2D, p2: BasePoint2D, is_diag: bool = False):
        assert isinstance(p1, BasePoint2D)
        assert isinstance(p2, BasePoint2D)
        self.p1 = p1
        self.p2 = p2
        self.is_diag = is_diag

    def __repr__(self):
        return(f'BaseSegment({repr(self.p1)}, {repr(self.p2)})')

    def horizontal(self):
        assert not self.is_diag
        return self.p1.y == self.p2.y

    def vertical(self):
        assert not self.is_diag
        return self.p1.x == self.p2.x

    def len(self):
        return abs(self.p1.x - self.p2.x) + abs(self.p1.y - self.p2.y) + 1

    # Building some related objects
    def enumerate_points(self) -> T.Iterator[BasePoint2D]:
        """ If segment is fully realized then it's points can be enumerated """
        p1, p2 = self.p1, self.p2
        for x in range(p1.x, p2.x + 1):
            for y in range(p1.y, p2.y + 1):
                yield BasePoint2D(x, y)

    def left_neigh(self):
        p = self.p1.left()
        return self.__class__(p, p.__class__(p.x, self.p2.y))

    def right_neigh(self):
        p = self.p2.right()
        return self.__class__(p.__class__(p.x, self.p1.y), p)

    def top_neigh(self):
        p = self.p1.top()
        return self.__class__(p, p.__class__(self.p2.x, p.y))

    def bottom_neigh(self):
        p = self.p2.bottom()
        return self.__class__(p.__class__(self.p1.x, p.y), p)

