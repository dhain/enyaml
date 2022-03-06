__all__ = [
    'SENTINEL',
    'Context',
    'render_all',
]

from contextlib import contextmanager
from collections import ChainMap


SENTINEL = object()


class Context(ChainMap):
    @contextmanager
    def push(self, dct=None, pos=0):
        if dct is None:
            dct = {}
        self.maps.insert(pos, dct)
        try:
            yield self
        finally:
            del self.maps[pos]


def render_all(tmpls, ctx=None):
    if ctx is None:
        ctx = Context()
    for tmpl in tmpls:
        result = tmpl.render(ctx)
        if result is SENTINEL:
            continue
        yield result
