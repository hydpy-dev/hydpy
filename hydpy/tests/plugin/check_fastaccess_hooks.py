# pylint: disable=missing-module-docstring, used-before-assignment, protected-access
# pylint: disable=pointless-statement

if __name__ == "__main__":

    from typing import Any, assert_type, Callable

    from hydpy.core import modeltools
    from hydpy.core import parametertools
    from hydpy.core import sequencetools
    from hydpy.core.typingtools import FastAccessMatrix, FastAccessVector
    from hydpy.cythons import interputils
    from hydpy.models import arma_rimorido, conv_idw, dam_llake, hland_96
    from hydpy.models.evap import evap_model
    from hydpy.models.exch import exch_model
    from hydpy.models.sw1d import sw1d_model

    h: hland_96.Model

    # 0-dimensional and 1-dimensional variables of different types:
    con = h.parameters.control.fastaccess
    assert_type(con, parametertools.FastAccessParameter)
    assert_type(con.nmbzones, int)
    assert_type(con.tcorr, FastAccessVector[float])
    assert_type(con.tcorr[0], float)
    assert_type(con.zonetype, FastAccessVector[int])
    assert_type(con.zonetype[0], int)
    assert_type(len(con.tcorr), int)
    assert_type(con.asdf, Any)  # type: ignore[attr-defined]

    # assignments:
    flu = h.sequences.fluxes.fastaccess
    flu.qt = 1.0
    flu.qt = "1.0"  # type: ignore[assignment]
    flu.qt = 1  # integers are fine for floats
    flu.tf[0] = 1.0
    flu.tf[0] = "1.0"  # type: ignore[assignment]
    flu.asdf = 1.0  # type: ignore[attr-defined]

    # old and new state values:
    states = h.sequences.states
    assert_type(states.fastaccess_old.sm, FastAccessVector[float])
    assert_type(states.fastaccess_new.sm, FastAccessVector[float])
    assert_type(states.fastaccess.sm, FastAccessVector[float])

    # 1-dimensional link sequences and their lengths:
    d: dam_llake.Model
    inl = d.sequences.inlets.fastaccess
    assert_type(inl, sequencetools.FastAccessLinkSequence)
    assert_type(inl.q[0], float)
    assert_type(inl.len_q, int)
    out = d.sequences.outlets.fastaccess
    assert_type(out.q, float)
    assert_type(out.len_q, Any)  # type: ignore[attr-defined]

    # subgroups without any variables:
    hinl = h.sequences.inlets.fastaccess
    assert_type(hinl, sequencetools.FastAccessLinkSequence)
    assert_type(hinl.q, Any)  # type: ignore[attr-defined]
    assert_type(hinl.len_q, Any)  # type: ignore[attr-defined]
    hinl.q = 1.0  # type: ignore[attr-defined]
    assert_type(h.parameters.solver.fastaccess.asdf, Any)  # type: ignore[attr-defined]

    # special parameters that hand over Cython extension objects:
    dcon = d.parameters.control.fastaccess
    simple = dcon.watervolume2waterlevel
    assert_type(simple, interputils.SimpleInterpolator)
    simple.inputs[0] = 1.0
    simple.calculate_values()
    simple.calculate_derivatives(0)
    assert_type(simple.outputs[0], float)
    assert_type(simple.output_derivatives[0], float)
    seasonal = dcon.waterlevel2flooddischarge
    assert_type(seasonal, interputils.SeasonalInterpolator)
    seasonal.calculate_values(0)
    seasonal.calculate_values()  # type: ignore[call-arg]
    assert_type(seasonal.ratios[0, 0], float)
    assert_type(seasonal.algorithm_types[0], int)
    seasonal.inputs[0] = 1.0
    assert_type(seasonal.outputs[0], float)
    simple.algorithm  # type: ignore[attr-defined]  # not public at the Cython level
    dcon.watervolume2waterlevel = None  # type: ignore[assignment]

    # special parameters that do not hand over anything:
    a: arma_rimorido.Model
    acon = a.parameters.control.fastaccess
    assert_type(acon.responses, None)
    acon.responses.inputs  # type: ignore[attr-defined]
    c: conv_idw.Model
    assert_type(c.parameters.control.fastaccess.inputcoordinates, None)

    # special parameters accessed via base models:
    x: exch_model.Model
    xcon = x.parameters.control.fastaccess
    assert_type(xcon.x2y, interputils.SimpleInterpolator)
    assert_type(xcon.rules, interputils.SeasonalInterpolator)
    assert_type(xcon.targets, None)

    # 2-dimensional variables and the hidden offsets of keyword parameters:
    e: evap_model.Model
    econ = e.parameters.control.fastaccess
    assert_type(econ.albedo, FastAccessMatrix[float])
    assert_type(econ.albedo[0, 1], float)
    assert_type(econ.albedo[0], FastAccessVector[float])
    assert_type(econ._albedo_rowmin, int)
    assert_type(econ._albedo_columnmin, int)
    assert_type(econ._monthfactor_entrymin, int)
    assert_type(econ._monthfactor_rowmin, Any)  # type: ignore[attr-defined]

    # callback parameters:
    s: sw1d_model.Model
    scon = s.parameters.control.fastaccess
    assert_type(scon.gateheight, float)
    assert_type(scon.gateheight_callback, Callable[[modeltools.Model], None])

    # unknown models (within HydPy, reading undeclared attributes is allowed but
    # writing is not; outside HydPy, the `fastaccess` objects are `Any`):
    m: modeltools.Model
    assert_type(m.parameters.control.fastaccess.asdf, Any)
    m.parameters.control.fastaccess.asdf = 1.0  # type: ignore[attr-defined]
