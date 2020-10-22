# -*- coding: utf-8 -*-
"""This module is thought for easing doctests only."""

# import...
# ...from standard library
import copy


class Dummies:
    """Handles "global" doctest data.

    A typical use pattern is to generated the instance of a class in the
    main docstring of the class and to test the different class methods
    based on this instance in separate docstrings afterwards.

    Class |Dummies| tries to ensure that the original objects are
    not altered due to performing different tests.  This protection
    mechanism is successfull for the simple following test class:

    >>> class Test:
    ...
    ...     def __init__(self):
    ...         self.name = 'some_name'
    ...         self.values = [1, 2, 3]

    As shown by the following results, neither the name nor the values of
    `dummies.test` can be altered by changing the respective
    attributes of the local object `test`:

    >>> from hydpy import dummies
    >>> dummies.test = Test()
    >>> test = dummies.test
    >>> test.name = 'different_name'
    >>> dummies.test.name
    'some_name'
    >>> test.values[1] = 4
    >>> dummies.test.values
    [1, 2, 3]

    The show pretection mechanism is implemented via making "deep copies"
    of objects handled by |Dummies| objects.  So lets see what happens
    when we subclass the test class and disable deep copying:

    >>> class Test(Test):
    ...
    ...     def __deepcopy__(self, dict_):
    ...         raise NotImplementedError()

    Repeating the the above examples still shows that attribute `name` is
    still protected but attribute `values` is not, meaning `test` is only
    a flat copy of `dummies.test`:

    >>> from hydpy import dummies
    >>> dummies.test = Test()
    >>> test = dummies.test
    >>> test.name = 'different_name'
    >>> dummies.test.name
    'some_name'
    >>> test.values[1] = 4
    >>> dummies.test.values
    [1, 4, 3]

    When we also disable flat copying, neither the name nor the values
    of `dummies.test` are protected:

    >>> class Test(Test):
    ...
    ...     def __copy__(self):
    ...         raise NotImplementedError()

    >>> from hydpy import dummies
    >>> dummies.test = Test()
    >>> test = dummies.test
    >>> test.name = 'different_name'
    >>> dummies.test.name
    'different_name'
    >>> test.values[1] = 4
    >>> dummies.test.values
    [1, 4, 3]

    After each test of a complete module, the dummy object is empty again
    (except for variable names starting with two underscores).
    """

    def clear(self):
        """Remove all currently handled attributes.

        >>> from hydpy import dummies
        >>> dummies.x = 1
        >>> dummies.y = None
        >>> dummies.x
        1
        >>> hasattr(dummies, 'y')
        True
        >>> dummies.clear()
        >>> hasattr(dummies, 'x') or hasattr(dummies, 'y')
        False
        """
        for name in list(vars(self)):
            delattr(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, "_" + name, value)

    def __getattr__(self, name):
        try:
            obj = object.__getattribute__(self, "_" + name)
        except AttributeError:
            raise AttributeError(
                f"Dummies object does not handle an object "
                f"named `{name}` at the moment."
            ) from None
        try:
            return copy.deepcopy(obj)
        except BaseException:
            pass
        try:
            return copy.copy(obj)
        except BaseException:
            pass
        return obj
