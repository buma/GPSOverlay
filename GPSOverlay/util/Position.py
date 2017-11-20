import itertools
import collections

from builtins import property as _property, tuple as _tuple
from operator import itemgetter as _itemgetter

class Position(tuple):
    'Position(top, right, bottom, left)'

    __slots__ = ()

    _fields = ('top', 'right', 'bottom', 'left')

    def __new__(_cls, top, right, bottom, left):
        'Create new instance of Position(top, right, bottom, left)'
        return _tuple.__new__(_cls, (top, right, bottom, left))

    @classmethod
    def make(cls, in_iterable, new=tuple.__new__, len=len):
        """Make a new Position object from a sequence or iterable

        Parameters
        ---------
        in_iterable
            List of parameters to set position. Rules are same as in CSS
            (padding, margin, border etc.):
            - 1 value sets all 4 fields.
            - 2 values: (first sets top and bottom, 2nd sets left and right)
            - 3 values: (first sets top, second left/right and third bottom
            - 4 values: (sets in order: top, right, bottom, left)
        """
        if len(in_iterable) == 1:
            iterable = itertools.repeat(in_iterable[0],4)
        elif len(in_iterable) == 2:
            iterable = [in_iterable[0], in_iterable[1], in_iterable[0],
                    in_iterable[1]]
        elif len(in_iterable) == 3:
            iterable = in_iterable + [in_iterable[1]]
        else:
            iterable = in_iterable
        result = new(cls, iterable)
        if len(result) != 4:
            raise TypeError('Expected 4 arguments, got %d' % len(result))
        return result

    def _replace(_self, **kwds):
        'Return a new Position object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('top', 'right', 'bottom', 'left'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % list(kwds))
        return result

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + '(top=%r, right=%r, bottom=%r, left=%r)' % self

    def _asdict(self):
        'Return a new OrderedDict which maps field names to their values.'
        return collections.OrderedDict(zip(self._fields, self))

    def __getnewargs__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return tuple(self)

    top = _property(_itemgetter(0), doc='top margin/padding')

    right = _property(_itemgetter(1), doc='right margin/padding')

    bottom = _property(_itemgetter(2), doc='bottom margin/padding')

    left = _property(_itemgetter(3), doc='left margin/padding')
