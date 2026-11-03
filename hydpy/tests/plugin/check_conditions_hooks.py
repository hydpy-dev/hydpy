# pylint: disable=missing-module-docstring, used-before-assignment

if __name__ == "__main__":

    from typing import Literal, assert_type

    from hydpy.core import modeltools
    from hydpy.core import typingtools
    from hydpy.interfaces import rconcinterfaces
    from hydpy.models import arma_rimorido
    from hydpy.models.dam import dam_model
    from hydpy.models import gland_gr5
    from hydpy.models import hland_96
    from hydpy.models import rconc_nash

    vector: typingtools.VectorFloat

    # main models
    gr5: gland_gr5.Model
    conditions = gr5.conditions
    assert_type(conditions, typingtools.ConditionsModel[gland_gr5.Model])
    submodel = conditions["model"]
    assert_type(submodel, typingtools.ConditionsSubmodel[gland_gr5.Model])
    states = submodel["states"]
    assert_type(states, typingtools.ConditionsGroup[gland_gr5.Model, Literal["states"]])
    assert_type(states["i"], float)
    assert_type(conditions["model"]["states"]["s"], float)
    conditions["model"]["states"]["s"] = 1.0
    conditions["model"]["states"]["s"] = [1.0]  # type: ignore[assignment]
    conditions["model"]["states"]["s"] = vector  # type: ignore[assignment]
    _ = conditions["model"]["states"]["wrong"]  # type: ignore[arg-type]
    conditions["model"]["states"]["wrong"] = 1.0  # type: ignore[arg-type]
    _ = conditions["model"]["wrong"]  # type: ignore[arg-type]
    _ = conditions["wrong"]  # type: ignore[arg-type]

    # submodels
    assert_type(
        conditions["model.rconcmodel"],
        typingtools.ConditionsSubmodel[rconcinterfaces.RConcModel_V1],
    )
    assert_type(
        conditions["model.rconcmodel"]["states"]["sc"], typingtools.ConditionValue
    )
    assert_type(
        conditions["model.unknown"], typingtools.ConditionsSubmodel[modeltools.Model]
    )

    # vector and log sequences
    nash: rconc_nash.Model
    assert_type(nash.sequences.conditions["states"]["sc"], typingtools.VectorFloat)
    h96: hland_96.Model
    assert_type(h96.conditions["model"]["states"]["sm"], typingtools.VectorFloat)
    h96.conditions["model"]["states"]["sm"] = vector
    h96.conditions["model"]["states"]["sm"] = 1.0  # type: ignore[assignment]
    h96.conditions["model"]["states"]["sm"] = [1.0]  # type: ignore[assignment]
    h96.conditions["model"]["states"]["uz"] = 1
    h96.conditions["model"]["states"]["uz"] = vector  # type: ignore[assignment]
    rimorido: arma_rimorido.Model
    assert_type(rimorido.conditions["model"]["logs"]["login"], typingtools.MatrixFloat)

    # model classes defined in base model modules (like mixins) without own entries:
    mixin: typingtools.ConditionsModel[dam_model.MixinSimpleWaterBalance]
    assert_type(mixin["model"]["states"]["watervolume"], float)
    _ = mixin["model"]["states"]["wrong"]  # type: ignore[arg-type]

    # non-literal keys
    key: str
    assert_type(conditions[key], typingtools.ConditionsSubmodel[modeltools.Model])
    assert_type(states[key], typingtools.ConditionValue)
    states[key] = 1.0
    states[key] = vector
