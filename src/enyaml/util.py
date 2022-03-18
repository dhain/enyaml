# Copyright (c) 2022, Sadie Hain. All rights reserved.
# Released under the BSD 3-Clause License
# https://enyaml.org/LICENSE

__all__ = [
    'Context',
]

from contextlib import contextmanager
from collections import ChainMap


class Context(ChainMap):
    """
    Context objects behave like a :term:`mapping`, with the added benefit of
    multiple "levels" of scope. Modifications to the Context at a given scope
    will be discarded when the scope is exited. For example:

    .. testsetup::

       from enyaml import Context

    >>> c = Context()
    >>> c['foo'] = 1
    >>> with c.push():
    ...     c['foo'] = 2
    ...     c['bar'] = 3
    ...     dict(c)
    {'foo': 2, 'bar': 3}
    >>> dict(c)
    {'foo': 1}
    """

    @contextmanager
    def push(self, dct=None, pos=0):
        """Push a :term:`mapping` onto the Context as a new scope.

        :param mapping, optional dct: A :term:`mapping` object to push onto the
           Context. If not specified or :const:`None`, a new :class:`dict` will
           be created.
        :param int, optional pos: The position in the stack to insert the
           mapping. The inner-most scope is :const:`0`, which is the default.
        :returns: A context manager which will remove the scope from the
           Context upon exit.

        Examples:

        >>> c = Context({'foo': 1})
        >>> with c.push():
        ...     c['foo'] = 2
        ...     dict(c)
        {'foo': 2}
        >>> dict(c)
        {'foo': 1}

        >>> with c.push({'bar': 1}):
        ...     dict(c)
        {'foo': 1, 'bar': 1}
        >>> dict(c)
        {'foo': 1}

        >>> with c.push():
        ...     with c.push({'baz': 1}, 1):
        ...         c['bar'] = c['baz']
        ...     dict(c)
        {'foo': 1, 'bar': 1}
        """

        if dct is None:
            dct = {}
        self.maps.insert(pos, dct)
        try:
            yield self
        finally:
            del self.maps[pos]
