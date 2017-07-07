
# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...model specifc
from hydpy.models.hstream import hstream_model
from hydpy.models.hstream import hstream_control
from hydpy.models.hstream import hstream_derived
from hydpy.models.hstream import hstream_states
from hydpy.models.hstream import hstream_inlets
from hydpy.models.hstream import hstream_outlets
from hydpy.models.hstream.hstream_parameters import Parameters
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer


class Model(modeltools.Model):
    """The HBV96 version of HydPy-H-Stream (hstream_v1)."""
    _RUNMETHODS = (hstream_model.calc_qjoints_v1,
                   hstream_model.update_inlets_v1,
                   hstream_model.update_outlets_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of hstream_v1, directly defined by the user."""
    _PARCLASSES = (hstream_control.Lag,
                   hstream_control.Damp)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hstream_v1, indirectly defined by the user."""
    _PARCLASSES = (hstream_derived.NmbSegments,
                   hstream_derived.C1,
                   hstream_derived.C2,
                   hstream_derived.C3)


class StateSequences(sequencetools.StateSequences):
    """State sequences of hstream_v1."""
    _SEQCLASSES = (hstream_states.QJoints,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of stream_v1."""
    _SEQCLASSES = (hstream_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of hstream_v1."""
    _SEQCLASSES = (hstream_outlets.Q,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
