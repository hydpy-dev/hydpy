# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.models import hland_96
    from hydpy.models.dam import (
        dam_model,
        dam_solver,
        dam_logs,
        dam_inlets,
        dam_outlets,
        dam_receivers,
        dam_observers,
        dam_senders,
    )
    from hydpy.models.hland import (
        hland_control,
        hland_derived,
        hland_fixed,
        hland_inputs,
        hland_factors,
        hland_fluxes,
        hland_states,
    )

    control: parametertools.ControlParameters[hland_96.Model]
    assert_type(control.beta, hland_control.Beta)
    assert_type(control.name, str)
    assert_type(control.k3, Any)  # type: ignore[attr-defined]
    assert_type(control.asdf, Any)  # type: ignore[attr-defined]
    derived: parametertools.DerivedParameters[hland_96.Model]
    assert_type(derived.dt, hland_derived.DT)
    assert_type(derived.name, str)
    assert_type(derived.asdf, Any)  # type: ignore[attr-defined]
    fixed: parametertools.FixedParameters[hland_96.Model]
    assert_type(fixed.pi, hland_fixed.Pi)
    assert_type(fixed.name, str)
    assert_type(fixed.asdf, Any)  # type: ignore[attr-defined]
    solver: parametertools.SolverParameters[dam_model.Model]
    assert_type(solver.abserrormax, dam_solver.AbsErrorMax)
    assert_type(solver.name, str)
    assert_type(solver.asdf, Any)  # type: ignore[attr-defined]

    inputs: sequencetools.InputSequences[hland_96.Model]
    assert_type(inputs.p, hland_inputs.P)
    assert_type(inputs.name, str)
    assert_type(inputs.asdf, Any)  # type: ignore[attr-defined]
    factors: sequencetools.FactorSequences[hland_96.Model]
    assert_type(factors.tc, hland_factors.TC)
    assert_type(factors.name, str)
    assert_type(factors.asdf, Any)  # type: ignore[attr-defined]
    fluxes: sequencetools.FluxSequences[hland_96.Model]
    assert_type(fluxes.pc, hland_fluxes.PC)
    assert_type(fluxes.name, str)
    assert_type(fluxes.asdf, Any)  # type: ignore[attr-defined]
    states: sequencetools.StateSequences[hland_96.Model]
    assert_type(states.sm, hland_states.SM)
    assert_type(states.name, str)
    assert_type(states.asdf, Any)  # type: ignore[attr-defined]
    logs: sequencetools.LogSequences[dam_model.Model]
    assert_type(logs.loggedoutflow, dam_logs.LoggedOutflow)
    assert_type(logs.name, str)
    assert_type(logs.asdf, Any)  # type: ignore[attr-defined]
    inlets: sequencetools.InletSequences[dam_model.Model]
    assert_type(inlets.q, dam_inlets.Q)
    assert_type(inlets.name, str)
    assert_type(inlets.asdf, Any)  # type: ignore[attr-defined]
    outlets: sequencetools.OutletSequences[dam_model.Model]
    assert_type(outlets.q, dam_outlets.Q)
    assert_type(outlets.name, str)
    assert_type(outlets.asdf, Any)  # type: ignore[attr-defined]
    receivers: sequencetools.ReceiverSequences[dam_model.Model]
    assert_type(receivers.d, dam_receivers.D)
    assert_type(receivers.name, str)
    assert_type(receivers.asdf, Any)  # type: ignore[attr-defined]
    observers: sequencetools.ObserverSequences[dam_model.Model]
    assert_type(observers.a, dam_observers.A)
    assert_type(observers.name, str)
    assert_type(observers.asdf, Any)  # type: ignore[attr-defined]
    senders: sequencetools.SenderSequences[dam_model.Model]
    assert_type(senders.r, dam_senders.R)
    assert_type(senders.name, str)
    assert_type(senders.asdf, Any)  # type: ignore[attr-defined]
