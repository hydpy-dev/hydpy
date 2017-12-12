# -*- coding: utf-8 -*-
"""This module is thought for easing doctests only."""

# import...
# ...from standard library
from __future__ import division, print_function
import copy
# ...from HydPy
from hydpy.core import autodoctools


class Dummies(object):
    """Handles "global" doctest data temporarily.

    A typical use pattern is to generated the instance of a class in the main
    docstring of the class and to test the different class methods based on
    this instance in seperate docstrings afterwards.

    After each test of a complete module, this module is empty again (except
    for variable names starting with two underscores).
    """

    def clear(self):
        for name in list(vars(self)):
            delattr(self, name)

    def __setattr__(self, name, value):
        super(Dummies, self).__setattr__('_'+name, value)

    def __getattr__(self, name):
        try:
            obj = super(Dummies, self).__getattribute__('_'+name)
            return copy.deepcopy(obj)
        except AttributeError:
            raise AttributeError('Dummies object does not handle an object '
                                 'named `%s` at the moment.' % name)


autodoctools.autodoc_module()
