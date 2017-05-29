# -*- coding: utf-8 -*-

# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools


def update_inlets_v1(self):
    """Update the inlet link sequence."""
    flu = self.sequences.fluxes.fastaccess
    inl = self.sequences.outlets.fastaccess
    flu.qz = inl.q[0]


def update_outlets_v1(self):
    """Update the outlet link sequence."""
    flu = self.sequences.fluxes.fastaccess
    out = self.sequences.outlets.fastaccess
    out.q[0] += flu.qa


class Model(modeltools.Model):
    """Base model for HydPy-L-Lake."""

    _RUNMETHODS = (update_inlets_v1,
                   update_outlets_v1)
