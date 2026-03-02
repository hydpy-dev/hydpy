# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.models import hland_96

    p = parametertools.Parameters[hland_96.Model]
    control: parametertools.ControlParameters[hland_96.Model]
    assert_type(control.vars, p)
    assert_type(control.pars, p)
    assert_type(control.seqs, Any)  # type: ignore[attr-defined]
    assert_type(control.asdf, Any)  # type: ignore[attr-defined]
    derived: parametertools.DerivedParameters[hland_96.Model]
    assert_type(derived.vars, p)
    assert_type(derived.pars, p)
    assert_type(derived.seqs, Any)  # type: ignore[attr-defined]
    assert_type(derived.asdf, Any)  # type: ignore[attr-defined]
    fixed: parametertools.FixedParameters[hland_96.Model]
    assert_type(fixed.vars, p)
    assert_type(fixed.pars, p)
    assert_type(fixed.seqs, Any)  # type: ignore[attr-defined]
    assert_type(fixed.asdf, Any)  # type: ignore[attr-defined]
    solver: parametertools.SolverParameters[hland_96.Model]
    assert_type(solver.vars, p)
    assert_type(solver.pars, p)
    assert_type(solver.seqs, Any)  # type: ignore[attr-defined]
    assert_type(solver.asdf, Any)  # type: ignore[attr-defined]

    s = sequencetools.Sequences[hland_96.Model]
    inputs: sequencetools.InputSequences[hland_96.Model]
    assert_type(inputs.vars, s)
    assert_type(inputs.seqs, s)
    assert_type(inputs.pars, Any)  # type: ignore[attr-defined]
    assert_type(inputs.asdf, Any)  # type: ignore[attr-defined]
    factors: sequencetools.FactorSequences[hland_96.Model]
    assert_type(factors.vars, s)
    assert_type(factors.seqs, s)
    assert_type(factors.pars, Any)  # type: ignore[attr-defined]
    assert_type(factors.asdf, Any)  # type: ignore[attr-defined]
    fluxes: sequencetools.FluxSequences[hland_96.Model]
    assert_type(fluxes.vars, s)
    assert_type(fluxes.seqs, s)
    assert_type(fluxes.pars, Any)  # type: ignore[attr-defined]
    assert_type(fluxes.asdf, Any)  # type: ignore[attr-defined]
    states: sequencetools.StateSequences[hland_96.Model]
    assert_type(states.vars, s)
    assert_type(states.seqs, s)
    assert_type(states.pars, Any)  # type: ignore[attr-defined]
    assert_type(states.asdf, Any)  # type: ignore[attr-defined]
    logs: sequencetools.LogSequences[hland_96.Model]
    assert_type(logs.vars, s)
    assert_type(logs.seqs, s)
    assert_type(logs.pars, Any)  # type: ignore[attr-defined]
    inlets: sequencetools.InletSequences[hland_96.Model]
    assert_type(inlets.vars, s)
    assert_type(inlets.seqs, s)
    assert_type(inlets.pars, Any)  # type: ignore[attr-defined]
    assert_type(inlets.asdf, Any)  # type: ignore[attr-defined]
    outlets: sequencetools.OutletSequences[hland_96.Model]
    assert_type(outlets.vars, s)
    assert_type(outlets.seqs, s)
    assert_type(outlets.pars, Any)  # type: ignore[attr-defined]
    assert_type(outlets.asdf, Any)  # type: ignore[attr-defined]
    receivers: sequencetools.ReceiverSequences[hland_96.Model]
    assert_type(receivers.vars, s)
    assert_type(receivers.seqs, s)
    assert_type(receivers.pars, Any)  # type: ignore[attr-defined]
    assert_type(receivers.asdf, Any)  # type: ignore[attr-defined]
    observers: sequencetools.ObserverSequences[hland_96.Model]
    assert_type(observers.vars, s)
    assert_type(observers.seqs, s)
    assert_type(observers.pars, Any)  # type: ignore[attr-defined]
    assert_type(observers.asdf, Any)  # type: ignore[attr-defined]
    senders: sequencetools.SenderSequences[hland_96.Model]
    assert_type(senders.vars, s)
    assert_type(senders.seqs, s)
    assert_type(senders.pars, Any)  # type: ignore[attr-defined]
    assert_type(senders.asdf, Any)  # type: ignore[attr-defined]
