# -*- coding: utf-8 -*-


def description(self):
    """Returns the first "paragraph" of the docstring of the given object.

    Note that ugly things like multiple whitespaces and newline characters
    are removed:

    >>> from hydpy.core import texttools, objecttools
    >>> texttools.description(objecttools.augment_excmessage)
    'Augment an exception message with additional information while keeping \
the original traceback.'

    In case the given object does not define a docstring, the following
    is returned:
    >>> texttools.description(type('Test', (), {}))
    'no description available'
    """
    if self.__doc__ in (None, ''):
        return 'no description available'
    return ' '.join(self.__doc__.split('\n\n')[0].split())
