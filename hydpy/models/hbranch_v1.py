
# imports...
# ...standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...model specifc
from hydpy.models.hbranch import hbranch_model
from hydpy.models.hbranch import hbranch_control
from hydpy.models.hbranch import hbranch_derived
from hydpy.models.hbranch import hbranch_fluxes
from hydpy.models.hbranch import hbranch_inlets
from hydpy.models.hbranch import hbranch_outlets
# Load the required `magic` functions into the local namespace.
from hydpy.core.magictools import parameterstep
from hydpy.core.magictools import simulationstep
from hydpy.core.magictools import controlcheck
from hydpy.core.magictools import Tester
from hydpy.cythons.modelutils import Cythonizer


class Model(hbranch_model.Model):
    """The HBV96 version of HydPy-H-Stream (hbranch_v1)."""
    _RUNMETHODS = (hbranch_model.calc_outputs_v1,
                   hbranch_model.update_inlets_v1,
                   hbranch_model.update_outlets_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of hbranch_v1, directly defined by the user."""
    _PARCLASSES = (hbranch_control.XPoints,
                   hbranch_control.YPoints)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of hbranch_v1, indirectly defined by the user."""
    _PARCLASSES = (hbranch_derived.NmbBranches,
                   hbranch_derived.NmbPoints)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of hbranch_v1."""
    _SEQCLASSES = (hbranch_fluxes.Input,
                   hbranch_fluxes.Outputs)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of hbranch_v1."""
    _SEQCLASSES = (hbranch_inlets.Total,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of hbranch_v1."""
    _SEQCLASSES = (hbranch_outlets.Branched,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
