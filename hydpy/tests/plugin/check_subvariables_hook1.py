# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import assert_type

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.models import hland_96

    p: parametertools.Parameters[hland_96.Model]
    assert_type(p.control, parametertools.ControlParameters[hland_96.Model])
    assert_type(p.derived, parametertools.DerivedParameters[hland_96.Model])
    assert_type(p.fixed, parametertools.FixedParameters[hland_96.Model])
    assert_type(p.solver, parametertools.SolverParameters[hland_96.Model])

    s: sequencetools.Sequences[hland_96.Model]
    assert_type(s.inputs, sequencetools.InputSequences[hland_96.Model])
    assert_type(s.factors, sequencetools.FactorSequences[hland_96.Model])
    assert_type(s.fluxes, sequencetools.FluxSequences[hland_96.Model])
    assert_type(s.states, sequencetools.StateSequences[hland_96.Model])
    assert_type(s.logs, sequencetools.LogSequences[hland_96.Model])
    assert_type(s.inlets, sequencetools.InletSequences[hland_96.Model])
    assert_type(s.outlets, sequencetools.OutletSequences[hland_96.Model])
    assert_type(s.receivers, sequencetools.ReceiverSequences[hland_96.Model])
    assert_type(s.observers, sequencetools.ObserverSequences[hland_96.Model])
    assert_type(s.senders, sequencetools.SenderSequences[hland_96.Model])
