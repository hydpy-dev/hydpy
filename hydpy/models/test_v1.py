# -*- coding: utf-8 -*-
"""This simple test model is thought for testing numerical integration
strategies.  It can be seen from two perspectives.  On the one hand
it implements the Dahlquist test equation (on the real axis only), which is
related to stiff initial value problems.  On the other hand it describes a
simple storage with a linear loss term and without any input.  The loss rate
:class:`test_fluxes.Q` and the initial storage content :class:`test_states.S`
can be set as required.
"""
# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core.modelimports import *
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from test
from hydpy.models.test import test_model
from hydpy.models.test import test_control
from hydpy.models.test import test_fluxes
from hydpy.models.test import test_states


class Model(modeltools.ModelELS):
    """Test model, Version 1."""
    _PART_ODE_METHODS = (test_model.calc_q_v1,)
    _FULL_ODE_METHODS = (test_model.calc_s_v1,)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of Test model, Version 1."""
    _PARCLASSES = (test_control.K,)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of Test model, Version 1."""
    _SEQCLASSES = (test_fluxes.Q,)


class StateSequences(sequencetools.StateSequences):
    """State sequences of Test model, Version 1."""
    _SEQCLASSES = (test_states.S,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()