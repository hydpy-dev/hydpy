# -*- coding: utf-8 -*-

# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...model specifc
from hydpy.models.llake import llake_model
from hydpy.models.llake import llake_control
from hydpy.models.llake import llake_fluxes
from hydpy.models.llake import llake_states
from hydpy.models.llake import llake_links
from hydpy.models.llake.llake_parameters import Parameters
from hydpy.models.llake.llake_sequences import Sequences
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer


class Model(modeltools.Model):
    """LARSIM-ME version of HydPy-L-Lake."""

    _RUNMETHODS = (llake_model.update_inlets_v1,
                   llake_model.update_outlets_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of LARSIM-ME-Lake, directly defined by the user."""
    _PARCLASSES = (llake_control.N,
                   llake_control.W,
                   llake_control.V,
                   llake_control.Q,
                   llake_control.MaxDW,
                   llake_control.Verzw)


class StateSequences(sequencetools.StateSequences):
    """State sequences of LARSIM-ME-Lake."""
    _SEQCLASSES = (llake_states.V,
                   llake_states.W)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of LARSIM-ME-Lake."""
    _SEQCLASSES = (llake_fluxes.QZ,
                   llake_fluxes.QA)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of LARSIM-ME-Lake."""
    _SEQCLASSES = (llake_links.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of LARSIM-ME-Lake."""
    _SEQCLASSES = (llake_links.Q,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()