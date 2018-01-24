# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Version 2 of HydPy-Dam.

Application model :mod:`~hydpy.models.dam_v002` is a simplification of
:mod:`~hydpy.models.dam_v001`.  While most functionlities are identical,
:mod:`~hydpy.models.dam_v002` does not calculate
:class:` ~hydpy.models.dam.RequiredRemoteRelease` on its own, but picks
this information from the simulation results of another model.

The following explanations focus on this difference.  For further
information on the usage of :mod:`~hydpy.models.dam_v002` please read
the documentation on model :mod:`~hydpy.models.dam_v001`.

Integration examples:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '21.01.2000',
    ...                                    '1d'))

    >>> from hydpy import Node
    >>> input_ = Node('input')
    >>> output = Node('output')
    >>> remote = Node('remote')

    >>> from hydpy import Element
    >>> dam = Element('dam', inlets=input_, outlets=output, receivers=remote)

    >>> from hydpy.models.dam_v002 import *
    >>> parameterstep('1d')
    >>> dam.connect(model)

    >>> from hydpy.core.testtools import IntegrationTest
    >>> test = IntegrationTest(
    ...     dam,
    ...     inits=((states.watervolume, 0.0),))
    >>> test.dateformat = '%d.%m.'

    >>> natural.sequences.sim.series = [
    ...         1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 1.0,
    ...         1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]


"""

# import...
# ...from standard library
from __future__ import division, print_function
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.core.modelimports import *
# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_solver
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_receivers


class Model(modeltools.ModelELS):
    """Version 2 of HydPy-Dam."""

    _INLET_METHODS = (dam_model.pic_inflow_v1,
                      dam_model.calc_requiredrelease_v1,
                      dam_model.calc_targetedrelease_v1)
    _RECEIVER_METHODS = (dam_model.pic_requiredremoterelease_v1,)
    _PART_ODE_METHODS = (dam_model.pic_inflow_v1,
                         dam_model.calc_waterlevel_v1,
                         dam_model.calc_actualrelease_v1,
                         dam_model.calc_flooddischarge_v1,
                         dam_model.calc_outflow_v1)
    _FULL_ODE_METHODS = (dam_model.update_watervolume_v1,)
    _OUTLET_METHODS = (dam_model.pass_outflow_v1,
                       dam_model.update_loggedoutflow_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-Dam, Version 2."""
    _PARCLASSES = (dam_control.CatchmentArea,
                   dam_control.NmbLogEntries,
                   dam_control.NearDischargeMinimumThreshold,
                   dam_control.NearDischargeMinimumTolerance,
                   dam_control.WaterLevelMinimumThreshold,
                   dam_control.WaterLevelMinimumTolerance,
                   dam_control.WaterVolume2WaterLevel,
                   dam_control.WaterLevel2FloodDischarge)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-Dam, Version 2."""
    _PARCLASSES = (dam_derived.TOY,
                   dam_derived.Seconds,
                   dam_derived.NearDischargeMinimumSmoothPar1,
                   dam_derived.NearDischargeMinimumSmoothPar2,
                   dam_derived.WaterLevelMinimumSmoothPar)


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of HydPy-Dam, Version 2."""
    _PARCLASSES = (dam_solver.AbsErrorMax,
                   dam_solver.RelDTMin)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-Dam, Version 2."""
    _SEQCLASSES = (dam_fluxes.Inflow,
                   dam_fluxes.RequiredRemoteRelease,
                   dam_fluxes.RequiredRelease,
                   dam_fluxes.TargetedRelease,
                   dam_fluxes.ActualRelease,
                   dam_fluxes.FloodDischarge,
                   dam_fluxes.Outflow)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-Dam, Version 2."""
    _SEQCLASSES = (dam_states.WaterVolume,)


class AideSequences(sequencetools.AideSequences):
    """State sequences of HydPy-Dam, Version 2."""
    _SEQCLASSES = (dam_aides.WaterLevel,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-Dam, Version 2."""
    _SEQCLASSES = (dam_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-Dam, Version 2."""
    _SEQCLASSES = (dam_outlets.Q,)


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 2."""
    _SEQCLASSES = (dam_receivers.Q,)


# pylint: disable=invalid-name
tester = Tester()
