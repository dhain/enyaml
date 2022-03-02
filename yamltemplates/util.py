__all__ = [
    'SENTINEL',
    'AttrChainMap',
    'render_all',
]

from collections import ChainMap


SENTINEL = object()


class AttrChainMap(ChainMap):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return super().__getattr__(name)


def render_all(tmpls, ctx=None):
    if ctx is None:
        ctx = AttrChainMap()
    for tmpl in tmpls:
        result = tmpl.render(ctx)
        if result is SENTINEL:
            continue
        yield result
