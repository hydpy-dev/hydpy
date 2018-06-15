# -*- coding: utf-8 -*-
#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
"""This Cython module implements global configuration data for numerical
tool, which must be available at Cython speed during simulations."""

import cython

@cython.final
cdef class Config(object):

    def __init__(self):
        self._abs_error_max = 1e-2
        self._rel_dt_min = 1e-3

    def _get_abs_error_max(self):
        """Numerical error tolerance.

        Many numerical integration algorithms provide error estimates.  An
        integration result is only accepted, if the associated error estimate
        is lower than a given threshold value...

        The default value is:

        >>> from hydpy.cythons.configtools import Config
        >>> config = Config()
        >>> from hydpy import round_
        >>> round_(config.abs_error_max)
        0.01

        You can pass larger value, but note that too large tolerances as the
        following would possible lead to poor simulation results:

        >>> config.abs_error_max = 1e3
        >>> round_(config.abs_error_max)
        1000.0

        Tolerances lower than zero or equal zero cannot be met and are thus
        forbidden:

        >>> config.abs_error_max = 0.
        Traceback (most recent call last):
        ...
        ValueError: The numerical tolerance value `abs_error_max` must be larger than zero, but the value `0.0` was given.
        """
        return self._abs_error_max

    def _set_abs_error_max(self, value):
        value = float(value)
        if value <= 0.:
            raise ValueError(
                'The numerical tolerance value `abs_error_max` must be larger '
                'than zero, but the value `%s` was given.' % value)
        else:
            self._abs_error_max = value

    abs_error_max = property(_get_abs_error_max, _set_abs_error_max)


    def _get_rel_dt_min(self):
        """Smallest numerical step size.

        Under some circumstances, numerical integration algorithms might not
        be able to achieve sufficient accuracy with reasonable effort.  To
        prevent model simulations from becoming too long, one can restrict
        the smallest time step, with which an outer time step is allowed to
        be solved...

        The default value is:

        >>> from hydpy.cythons.configtools import Config
        >>> config = Config()
        >>> from hydpy import round_
        >>> round_(config.rel_dt_min)
        0.001

        You can pass larger value, but note that too large step sizes as the
        following would possible result in poor simulation results:

        >>> config.rel_dt_min = 1.
        >>> round_(config.rel_dt_min)
        1.0

        On the other hand, too small step sizes might result in too long
        simulation times:

        >>> config.rel_dt_min = 0.
        >>> round_(config.rel_dt_min)
        0.0

        Tolerances lower than zero or larger than one do not make sense and
        are thus forbidden:

        >>> config.rel_dt_min = 1.1
        Traceback (most recent call last):
        ...
        ValueError: The smallest integration time step `_rel_dt_min` must not be smaller than zero or larger than one, but the value `1.1` was given.
        """
        return self._rel_dt_min

    def _set_rel_dt_min(self, value):
        value = float(value)
        if (value < 0.) or (value > 1.):
            raise ValueError(
                'The smallest integration time step `_rel_dt_min` must not be '
                'smaller than zero or larger than one, but the value `%s` was '
                'given.' % value)
        else:
            self._rel_dt_min = value

    rel_dt_min = property(_get_rel_dt_min, _set_rel_dt_min)


