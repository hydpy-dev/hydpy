# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import parametertools


class K(parametertools.Parameter):
    """Storage coefficient [1/T].

    For educational purposes, the actual value of parameter |K| does
    not depend on the difference between the actual simulation time step and
    the actual parameter time step.
    """

    NDIM, TYPE, TIME, SPAN = 0, float, None, (0.0, None)


class N(parametertools.Parameter):
    """Number of storages [-]."""

    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        seqs = self.subpars.pars.model.sequences
        seqs.states.sv.shape = self
        seqs.fluxes.qv.shape = self
