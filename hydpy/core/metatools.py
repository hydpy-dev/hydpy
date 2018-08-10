# -*- coding: utf-8 -*-


def description(self):
    """Returns the first "paragraph" of the docstring of the given object.

    Note that ugly things like multiple whitespaces and newline characters
    are removed:

    >>> from hydpy.core import metatools, objecttools
    >>> metatools.description(objecttools.augment_excmessage)
    'Augment an exception message with additional information while keeping \
the original traceback.'

    In case the given object does not define a docstring, the following
    is returned:
    >>> metatools.description(type('Test', (), {}))
    'no description available'
    """
    if self.__doc__ in (None, ''):
        return 'no description available'
    return ' '.join(self.__doc__.split('\n\n')[0].split())


class MetaSubgroupType(type):
    """Type for generating subclasses of |SubParameters|, |SubSequences|,
    and |Masks|.

    See class |SubParameters| for the effects of applying |MetaSubgroupType|.
    """
    def __new__(mcs, name, parents, dict_):
        classes = dict_.get('CLASSES')
        if classes is None:
            raise NotImplementedError(
                'For class `%s`, the required tuple `CLASSES` '
                'is not defined.'
                % name)
        if classes:
            lst = ['\n\n\n    The following classes are selected:']
            for cls in classes:
                lst.append('      * :class:`~%s` %s'
                           % ('.'.join((cls.__module__,
                                        cls.__name__)),
                              description(cls)))
            doc = dict_.get('__doc__', None)
            if doc is None:
                doc = ''
            dict_['__doc__'] = doc + '\n'.join(l for l in lst)
        return type.__new__(mcs, name, parents, dict_)


MetaSubgroupClass = MetaSubgroupType(
    'MetaSubgroupClass', (), {'CLASSES': ()})
