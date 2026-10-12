# pylint: disable=missing-module-docstring, protected-access, used-before-assignment

if __name__ == "__main__":

    from typing import Any, assert_type

    from hydpy.core import modeltools
    from hydpy.core import parametertools
    from hydpy.models import exch_branch_io
    from hydpy.models import hland_96
    from hydpy.models.exch import exch_control
    from hydpy.models.hland import hland_control, hland_derived

    control: parametertools.ControlParameters[hland_96.Model]
    assert_type(
        control.regular,
        parametertools.RegularParameters[
            parametertools.ControlParameters[hland_96.Model]
        ],
    )
    assert_type(control.regular.beta, hland_control.Beta)
    assert_type(control.regular.names, tuple[str, ...])
    assert_type(control.regular._pars, tuple[parametertools.Parameter, ...])
    assert_type(control.regular.asdf, Any)  # type: ignore[attr-defined]
    assert_type(control.special.beta, Any)  # type: ignore[attr-defined]
    derived: parametertools.DerivedParameters[hland_96.Model]
    assert_type(derived.regular.dt, hland_derived.DT)

    control_exch: parametertools.ControlParameters[exch_branch_io.Model]
    assert_type(control_exch.regular.minstream, exch_control.MinStream)
    assert_type(control_exch.special.targets, exch_control.Targets)
    assert_type(control_exch.special.flowtransferrules, exch_control.FlowTransferRules)
    assert_type(control_exch.special.names, tuple[str, ...])
    assert_type(control_exch.regular.targets, Any)  # type: ignore[attr-defined]
    assert_type(control_exch.special.minstream, Any)  # type: ignore[attr-defined]

    subset: parametertools.ParameterSubset[
        parametertools.ControlParameters[exch_branch_io.Model], parametertools.Parameter
    ]
    assert_type(subset.minstream, exch_control.MinStream)
    assert_type(subset.targets, exch_control.Targets)
    assert_type(subset.asdf, Any)  # type: ignore[attr-defined]

    control_any: parametertools.ControlParameters[Any]
    assert_type(control_any.regular.beta, parametertools.Parameter)
    assert_type(control_any.special.beta, parametertools.SpecialParameter)
    control_model: parametertools.ControlParameters[modeltools.Model]
    assert_type(control_model.regular.beta, parametertools.Parameter)
    assert_type(control_model.special.beta, parametertools.SpecialParameter)
