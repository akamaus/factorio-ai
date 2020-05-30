import typing as T


def tail(gen: T.Iterator) -> T.Iterator:
    first = True
    for el in gen:
        if not first:
            yield el
        first = False
