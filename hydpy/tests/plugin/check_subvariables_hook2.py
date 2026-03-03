# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type

    from hydpy.core import parametertools
    from hydpy.core import sequencetools
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
        hland_model,
        hland_control,
        hland_derived,
        hland_fixed,
        hland_inputs,
        hland_factors,
        hland_fluxes,
        hland_states,
    )

    beta: hland_control.Beta
    assert_type(beta.subvars, parametertools.ControlParameters[hland_model.Model])
    assert_type(beta.subpars, parametertools.ControlParameters[hland_model.Model])
    assert_type(beta.forest, float)
    dt: hland_derived.DT
    assert_type(dt.subvars, parametertools.DerivedParameters[hland_model.Model])
    assert_type(dt.subpars, parametertools.DerivedParameters[hland_model.Model])
    assert_type(dt.subseqs, Any)  # type: ignore[attr-defined]
    pi: hland_fixed.Pi
    assert_type(pi.subvars, parametertools.FixedParameters[hland_model.Model])
    assert_type(pi.subpars, parametertools.FixedParameters[hland_model.Model])
    assert_type(pi.subseqs, Any)  # type: ignore[attr-defined]
    abserrormax: dam_solver.AbsErrorMax
    assert_type(abserrormax.subvars, parametertools.SolverParameters[dam_model.Model])
    assert_type(abserrormax.subpars, parametertools.SolverParameters[dam_model.Model])
    assert_type(abserrormax.subseqs, Any)  # type: ignore[attr-defined]

    p: hland_inputs.P
    assert_type(p.subvars, sequencetools.InputSequences[hland_model.Model])
    assert_type(p.subseqs, sequencetools.InputSequences[hland_model.Model])
    assert_type(p.subpars, Any)  # type: ignore[attr-defined]
    tc: hland_factors.TC
    assert_type(tc.subvars, sequencetools.FactorSequences[hland_model.Model])
    assert_type(tc.subseqs, sequencetools.FactorSequences[hland_model.Model])
    assert_type(tc.subpars, Any)  # type: ignore[attr-defined]
    pc: hland_fluxes.PC
    assert_type(pc.subvars, sequencetools.FluxSequences[hland_model.Model])
    assert_type(pc.subseqs, sequencetools.FluxSequences[hland_model.Model])
    assert_type(pc.subpars, Any)  # type: ignore[attr-defined]
    sm: hland_states.SM
    assert_type(sm.subvars, sequencetools.StateSequences[hland_model.Model])
    assert_type(sm.subseqs, sequencetools.StateSequences[hland_model.Model])
    assert_type(sm.subpars, Any)  # type: ignore[attr-defined]
    loggedoutflow: dam_logs.LoggedOutflow
    assert_type(loggedoutflow.subvars, sequencetools.LogSequences[dam_model.Model])
    assert_type(loggedoutflow.subseqs, sequencetools.LogSequences[dam_model.Model])
    assert_type(loggedoutflow.subpars, Any)  # type: ignore[attr-defined]
    q: dam_inlets.Q
    assert_type(q.subvars, sequencetools.InletSequences[dam_model.Model])
    assert_type(q.subseqs, sequencetools.InletSequences[dam_model.Model])
    assert_type(q.subpars, Any)  # type: ignore[attr-defined]
    q_: dam_outlets.Q
    assert_type(q_.subvars, sequencetools.OutletSequences[dam_model.Model])
    assert_type(q_.subseqs, sequencetools.OutletSequences[dam_model.Model])
    assert_type(q_.subpars, Any)  # type: ignore[attr-defined]
    d: dam_receivers.D
    assert_type(d.subvars, sequencetools.ReceiverSequences[dam_model.Model])
    assert_type(d.subseqs, sequencetools.ReceiverSequences[dam_model.Model])
    assert_type(d.subpars, Any)  # type: ignore[attr-defined]
    a: dam_observers.A
    assert_type(a.subvars, sequencetools.ObserverSequences[dam_model.Model])
    assert_type(a.subseqs, sequencetools.ObserverSequences[dam_model.Model])
    assert_type(a.subpars, Any)  # type: ignore[attr-defined]
    r: dam_senders.R
    assert_type(r.subvars, sequencetools.SenderSequences[dam_model.Model])
    assert_type(r.subseqs, sequencetools.SenderSequences[dam_model.Model])
    assert_type(r.subpars, Any)  # type: ignore[attr-defined]
