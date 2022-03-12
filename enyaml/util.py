# Copyright (c) 2022, Sadie Hain. All rights reserved.
# Released under the BSD 3-Clause License
# https://enyaml.org/LICENSE

__all__ = [
    'Context',
]

from contextlib import contextmanager
from collections import ChainMap


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
