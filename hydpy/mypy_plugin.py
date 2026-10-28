# pylint: disable=too-many-boolean-expressions
"""This module provides a Mypy plugin that infers more precise types and warns about
potential problems in situations where HydPy relies on runtime behaviour that is not
(and possibly cannot be) expressed via static type hints."""

from calendar import monthrange
from configparser import ConfigParser
from os.path import join, split
from pickle import load
import re
from typing import Callable, cast, Final, Literal, NamedTuple
from warnings import warn

from mypy.checker import TypeChecker
from mypy.errorcodes import ARG_TYPE, ATTR_DEFINED, CALL_ARG, DEPRECATED
from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_STAR2,
    CallExpr,
    Decorator,
    MemberExpr,
    MypyFile,
    TypeAlias,
    TypeInfo,
)
from mypy.options import Options
from mypy.plugin import (
    AttributeContext,
    FunctionContext,
    Plugin,
    MethodContext,
    MethodSigContext,
)
from mypy.typeops import bind_self
from mypy.types import (
    AnyType,
    CallableType,
    ExtraAttrs,
    FunctionLike,
    get_proper_type,
    LiteralType,
    Instance,
    NoneType,
    TupleType,
    Type,
    TypeAliasType,
    TypeOfAny,
    UnionType,
)

VARS1 = set(
    ["hydpy.core.modeltools.Model.parameters", "hydpy.core.modeltools.Model.sequences"]
)
VARS2 = set(
    [
        "hydpy.core.variabletools.SubVariables.vars",
        "hydpy.core.parametertools.SubVariables.pars",
        "hydpy.core.sequencetools.IOSequences.seqs",
        "hydpy.core.sequencetools.ModelSequences.seqs",
    ]
)
SUBVARS1 = set(
    [
        "hydpy.core.parametertools.Parameters.control",
        "hydpy.core.parametertools.Parameters.derived",
        "hydpy.core.parametertools.Parameters.fixed",
        "hydpy.core.parametertools.Parameters.solver",
        "hydpy.core.sequencetools.Sequences.inlets",
        "hydpy.core.sequencetools.Sequences.observers",
        "hydpy.core.sequencetools.Sequences.receivers",
        "hydpy.core.sequencetools.Sequences.inputs",
        "hydpy.core.sequencetools.Sequences.factors",
        "hydpy.core.sequencetools.Sequences.fluxes",
        "hydpy.core.sequencetools.Sequences.states",
        "hydpy.core.sequencetools.Sequences.logs",
        "hydpy.core.sequencetools.Sequences.aides",
        "hydpy.core.sequencetools.Sequences.outlets",
        "hydpy.core.sequencetools.Sequences.senders",
    ]
)
SUBVARS2 = set(
    [
        "hydpy.core.variabletools.Variable.subvars",
        "hydpy.core.parametertools.Parameter.subvars",
        "hydpy.core.parametertools.Parameter.subpars",
        "hydpy.core.parametertools.SpecialParameter.subvars",
        "hydpy.core.parametertools.SpecialParameter.subpars",
        "hydpy.core.sequencetools.InputSequence.subvars",
        "hydpy.core.sequencetools.InputSequence.subseqs",
        "hydpy.core.sequencetools.FactorSequence.subvars",
        "hydpy.core.sequencetools.FactorSequence.subseqs",
        "hydpy.core.sequencetools.FluxSequence.subvars",
        "hydpy.core.sequencetools.FluxSequence.subseqs",
        "hydpy.core.sequencetools.StateSequence.subvars",
        "hydpy.core.sequencetools.StateSequence.subseqs",
        "hydpy.core.sequencetools.LogSequence.subvars",
        "hydpy.core.sequencetools.LogSequence.subseqs",
        "hydpy.core.sequencetools.AideSequence.subvars",
        "hydpy.core.sequencetools.AideSequence.subseqs",
        "hydpy.core.sequencetools.InletSequence.subvars",
        "hydpy.core.sequencetools.InletSequence.subseqs",
        "hydpy.core.sequencetools.OutletSequence.subvars",
        "hydpy.core.sequencetools.OutletSequence.subseqs",
        "hydpy.core.sequencetools.ObserverSequence.subvars",
        "hydpy.core.sequencetools.ObserverSequence.subseqs",
        "hydpy.core.sequencetools.ReceiverSequence.subvars",
        "hydpy.core.sequencetools.ReceiverSequence.subseqs",
        "hydpy.core.sequencetools.SenderSequence.subvars",
        "hydpy.core.sequencetools.SenderSequence.subseqs",
    ]
)
VALUES = set(
    [
        "hydpy.core.variabletools.Variable.value",
        "hydpy.core.variabletools.Variable.values",
        "hydpy.core.parametertools.Parameter.value",
        "hydpy.core.parametertools.Parameter.values",
        "hydpy.core.sequencetools.Sequence_.value",
        "hydpy.core.sequencetools.Sequence_.values",
    ]
)
SERIES = set(
    [
        "hydpy.core.sequencetools.IOSequence.series",
        "hydpy.core.sequencetools.IOSequence.simseries",
        "hydpy.core.sequencetools.IOSequence.evalseries",
    ]
)

DIRPATH = split(__file__)[0]

MODEL_MAP: dict[str, dict[str, tuple[str, str]]]
VAR_MAP_1: dict[str, dict[str, dict[str, tuple[str, str]]]]
VAR_MAP_2: dict[str, tuple[str, str, str]]
VAR_INFO: dict[str, tuple[int, type[float]]]
VAR_SHAPE: set[str]
VAR_TIMEINT: set[str]
ZIP_CONSTANTS: dict[str, tuple[str, ...] | None]
ADDER_KEYWORDS: dict[str, tuple[str, ...]]
KEYWORD_NAMES: dict[str, tuple[str, ...] | None]
with open(join(DIRPATH, "conf", "mypy_plugin_data.pickle"), "rb") as file_:
    (
        MODEL_MAP,
        VAR_MAP_1,
        VAR_MAP_2,
        VAR_INFO,
        VAR_SHAPE,
        VAR_TIMEINT,
        ZIP_CONSTANTS,
        ADDER_KEYWORDS,
        KEYWORD_NAMES,
    ) = load(file_)

TOY_FORMAT: Final = re.compile(r"toy(_[0-9]{1,2}){1,5}")
"""Standard format of time of year names."""

THRESHOLD_FORMAT: Final = re.compile(r"th_(0|[1-9][0-9]*)_(0|[0-9]*[1-9])")
"""Standard format of threshold names."""


def _standardize_toy(name: str) -> str | None:
    """Return the standard time of year name for the given keyword name, or `None` if
    the runtime does not support it."""
    values = name.split("_")[1:]
    if not 1 <= len(values) <= 5:
        return None
    try:
        integers = [int(value) for value in values]
    except ValueError:
        return None
    return "_".join(["toy"] + [f"{integer:02}" for integer in integers])


def _standardize_threshold(name: str) -> str | None:
    """Return the standard threshold name for the given keyword name, or `None` if the
    runtime does not support it."""
    parts = name.split("_")
    try:
        if (len(parts) > 1) and parts[-2].isdigit():
            integer = str(int(parts[-2]))
            decimal = parts[-1]
            if not (decimal.isascii() and decimal.isdigit()):
                return None
            decimal = decimal.rstrip("0") or "0"
        else:
            integer = str(int(parts[-1]))
            decimal = "0"
    except ValueError:
        return None
    return f"th_{integer}_{decimal}"


class KeywordFormat(NamedTuple):
    """Format of the keyword names accepted by the `__call__` method of specific
    classes."""

    pattern: re.Pattern[str]
    standardize: Callable[[str], str | None]
    description: str


KEYWORD_FORMATS: Final = {
    "hydpy.models.arma.arma_control.Responses": KeywordFormat(
        THRESHOLD_FORMAT, _standardize_threshold, "threshold name"
    ),
    "hydpy.core.parametertools.SeasonalParameter": KeywordFormat(
        TOY_FORMAT, _standardize_toy, "time of year name"
    ),
    "hydpy.auxs.interptools.SeasonalInterpolator": KeywordFormat(
        TOY_FORMAT, _standardize_toy, "time of year name"
    ),
}


LANDTYPES: Final = "__hydpy_landtypes__"
"""Name of the "extra attribute" that informs about the land type constants main
models pass to their submodels.

Its value is a string literal like "evap:field,forest,glacier,ilake,sealed".  Entries
for different submodel families are separated by semicolons.  (At runtime, a main model
passes its constants to the zip parameters and the keyword parameters with row names
depending on the main model of a specific base model family, and these stay valid for
all nested submodels of the same family as long as the main model's `with` block is
active.  Hence, the plugin collects the constants per family.)
"""


def _get_family(fullname: str) -> str:
    """
    `hydpy.models.evap_aet_hbv96.Model` --> `evap`
    `hydpy.models.evap.evap_control.Water` --> `evap`
    """
    return fullname.split(".")[2].split("_")[0]


def _decode_landtypes(type_: Instance) -> dict[str, str]:
    """Return the given type's land type information as a dictionary that maps submodel
    families to comma-separated land type names (empty if not available)."""
    if (
        ((extra := type_.extra_attrs) is not None)
        and ((literal := extra.attrs.get(LANDTYPES)) is not None)
        and isinstance(literal := get_proper_type(literal), LiteralType)
        and isinstance(value := literal.value, str)
    ):
        return dict(item.split(":") for item in value.split(";"))
    return {}


def _encode_landtypes(
    api: TypeChecker, family2landtypes: dict[str, str]
) -> ExtraAttrs | None:
    """Return a new `ExtraAttrs` object that contains the given land type information as
    a string literal (or `None` if there is no information)."""
    if not family2landtypes:
        return None
    value = ";".join(f"{k}:{v}" for k, v in sorted(family2landtypes.items()))
    literal = LiteralType(value=value, fallback=api.named_type("builtins.str"))
    return ExtraAttrs(attrs={LANDTYPES: literal}, immutable={LANDTYPES})


def _forward_landtypes(type_: Instance) -> ExtraAttrs | None:
    """Return a new `ExtraAttrs` object that contains the given type's land type
    information (if available)."""
    if ((extra := type_.extra_attrs) is not None) and (
        (literal := extra.attrs.get(LANDTYPES)) is not None
    ):
        return ExtraAttrs(attrs={LANDTYPES: literal}, immutable={LANDTYPES})
    return None


def prepare_model_hook(context: FunctionContext) -> Type:
    """
    `prepare_model("modelx") -> Model`
    -->
    `prepare_model("modelx") -> ModelX`
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and (len(arg_types := context.arg_types) in (1, 2))
        and (len(arg_types[0]) == 1)
        and isinstance(arg_type := get_proper_type(arg_types[0][0]), Instance)
        and isinstance(literal := arg_type.last_known_value, LiteralType)
    ):
        arg = literal.value
        if ((module_name := f"hydpy.models.{arg}") in MODEL_MAP) or (
            (module_name := f"hydpy.models.{arg}.{arg}_model") in MODEL_MAP
        ):
            if (module_type := api.modules.get(module_name)) is None:
                return context.default_return_type
            if (model_type := module_type.names.get("Model")) is None:
                return context.default_return_type
            assert isinstance(node := model_type.node, TypeInfo)
            return Instance(typ=node, args=[])
        context.api.msg.report(
            msg=f"No model named `{module_name}` available.",
            context=context.context,
            severity="error",
            code=ARG_TYPE,
            origin_context=None,
        )
    return context.default_return_type


def submodeladder_call_hook(context: MethodContext) -> Type:
    """
    `ModelX.add_submodely_v1("modely") -> modeltools.SubmodelInterface`
    -->
    `ModelX.add_submodely_v1("modely") -> modely.Model`
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and (len(arg_types := context.arg_types) >= 2)
        and (len(arg_types[0]) == 1)
        and isinstance(arg_type := get_proper_type(arg_types[0][0]), Instance)
        and isinstance(literal := arg_type.last_known_value, LiteralType)
        and isinstance(
            adder_inst := get_proper_type(context.default_return_type), Instance
        )
    ):
        arg = literal.value
        if ((module_name := f"hydpy.models.{arg}") in MODEL_MAP) or (
            (module_name := f"hydpy.models.{arg}.{arg}_model") in MODEL_MAP
        ):
            if (
                ((module_type := api.modules.get(module_name)) is None)
                or ((model_sym := module_type.names.get("Model")) is None)
                or not isinstance(model_info := model_sym.node, TypeInfo)
                or (len(adder_args := adder_inst.args) != 3)
                or not isinstance(
                    interface_inst := get_proper_type(adder_args[2]), Instance
                )
            ):
                return context.default_return_type
            interface_name = interface_inst.type.fullname
            if model_info.has_base(interface_name):
                submodel_inst = Instance(
                    model_info,
                    args=[],
                    extra_attrs=_get_submodel_landtypes(api, context, model_info),
                )
                return adder_inst.copy_modified(args=adder_args[:2] + (submodel_inst,))
            context.api.msg.report(
                msg=(
                    f"Model `{module_name}` does not comply with the submodel "
                    f"interface `{interface_name}`."
                ),
                context=context.context,
                severity="error",
                code=ARG_TYPE,
                origin_context=None,
            )
        context.api.msg.report(
            msg=f"No model named `{module_name}` available.",
            context=context.context,
            severity="error",
            code=ARG_TYPE,
            origin_context=None,
        )
    return context.default_return_type


def _get_submodel_landtypes(
    api: TypeChecker, context: MethodContext, submodel_info: TypeInfo
) -> ExtraAttrs | None:
    """Return the land type information relevant for the submodel (see `LANDTYPES`)."""
    if (
        isinstance(call_expr := context.context, CallExpr)
        and isinstance(callee := call_expr.callee, MemberExpr)
        and ((main_type := api.lookup_type_or_none(callee.expr)) is not None)
        and isinstance(main_inst := get_proper_type(main_type), Instance)
    ):
        family2landtypes = _decode_landtypes(main_inst)
        key = f"{main_inst.type.fullname}.{callee.name}"
        if (keywords := ADDER_KEYWORDS.get(key)) is not None:
            family = _get_family(submodel_info.fullname)
            family2landtypes[family] = ",".join(keywords)
        return _encode_landtypes(api, family2landtypes)
    return None


def submodeladder_enter_hook(context: MethodContext) -> Type:
    """
    `ModelX.add_submodely_v1("modely") -> modeltools.SubmodelInterface`
    -->
    `ModelX.add_submodely_v1("modely") -> modely.Model`
    """
    if isinstance(adder_inst := context.type, Instance):
        return adder_inst.args[2]
    return context.default_return_type


def trim_hook(context: MethodSigContext) -> FunctionLike:
    """
    VariableX.trim(TrimHook, TrimHook) -> bool
    -->
    VariableX.trim(float | None, float | None) -> bool
    """
    default = context.default_signature
    if (default.arg_names != ["lower", "upper"]) or not all(
        _is_alias(at, "TrimHook") for at in default.arg_types
    ):
        return default
    ndim_type = _get_ndim_and_type(context)
    if ndim_type is None:
        return default
    vectorlike = _get_vectorlike(
        context=context, ndim=ndim_type[0], type_=ndim_type[1], input_=True
    )
    if vectorlike is None:
        return default
    vl_opt = UnionType(items=[vectorlike, NoneType()])
    return default.copy_modified(arg_types=(vl_opt, vl_opt))


def call_hook(context: MethodSigContext) -> FunctionLike:
    """
    `VariableX.__call__(*values: CallHook, ...) -> None`
    -->
    `VariableX.__call__(*values: float, ...) -> None`
    `VariableY.__call__(*values: int | VectorInputInt, ...) -> None`
    ...

    `ZipParameterX.__call__(*, default: float = ..., **constants: float) -> None`
    -->
    `ZipParameterX.__call__(*, default: float = ..., field: float = ..., ...) -> None`

    `KeywordParameter1DX.__call__(**entries: float) -> None`
    -->
    `KeywordParameter1DX.__call__(*, jan: float = ..., feb: float = ..., ...) -> None`
    """
    default = _restrict_keywords(context, context.default_signature)
    ndim_type = _get_ndim_and_type(context)
    if (ndim_type is None) or not isinstance(var_inst := context.type, Instance):
        return default
    ndim, type_ = ndim_type
    types_: tuple[type[float], ...] = (type_,)
    if var_inst.type.fullname in VAR_TIMEINT:
        types_ = (float, int)
    items = []
    for subtype in types_:
        for subndim in range(1 if ndim else 0, ndim + 1):
            vectorlike = _get_vectorlike(
                context=context, ndim=subndim, type_=subtype, input_=True
            )
            if vectorlike is None:
                return default
            items.append(vectorlike)
    values_type = UnionType.make_union(items)
    default = default.copy_modified(
        arg_types=[
            values_type if _is_alias(at, "CallHook") else at for at in default.arg_types
        ]
    )
    default = _insert_zip_keywords(context, var_inst, types_[0], default)
    return _insert_entry_or_row_keywords(context, var_inst, types_[0], default)


def _restrict_keywords(
    context: MethodSigContext, signature: CallableType
) -> CallableType:
    """Replace the arbitrary keyword arguments with the call's keyword names the runtime
    supports (see `KEYWORD_FORMATS`) and report invalid, duplicate, and deprecated
    names."""
    if (
        (not isinstance(var_inst := context.type, Instance))
        or (not signature.arg_kinds)
        or (signature.arg_kinds[-1] != ARG_STAR2)
        or (not isinstance(call := context.context, CallExpr))
        or (ARG_STAR2 in call.arg_kinds)
    ):
        return signature
    for fullname, format_ in KEYWORD_FORMATS.items():
        if var_inst.type.has_base(fullname):
            break
    else:
        return signature
    name2standard = {
        n: s
        for n in call.arg_names
        if (n is not None) and ((s := format_.standardize(n)) is not None)
    }
    names = list(name2standard)
    invalid: set[str] = set()
    if format_.pattern is TOY_FORMAT:
        invalid = _check_toys(context, call, names)
    else:
        _check_thresholds(context, call, name2standard)
    for name, standard in name2standard.items():
        if (name not in invalid) and not format_.pattern.fullmatch(name):
            _report_deprecation(
                context,
                call,
                f'The {format_.description} "{name}" is deprecated and will no longer '
                f'be supported in HydPy 8.0.  Please write "{standard}" instead.',
            )
    return signature.copy_modified(
        arg_types=signature.arg_types[:-1] + len(names) * [signature.arg_types[-1]],
        arg_kinds=signature.arg_kinds[:-1] + len(names) * [ARG_NAMED_OPT],
        arg_names=signature.arg_names[:-1] + names,
    )


def _check_toys(
    context: MethodSigContext, call: CallExpr, names: list[str]
) -> set[str]:
    """Report invalid times of year and different names for the same time of year
    and return the invalid names."""
    invalid = set()
    toy2name: dict[tuple[int, ...], str] = {}
    for name in names:
        toy = tuple(int(v) for v in name.split("_")[1:])
        toy += (1, 1, 0, 0, 0)[len(toy) :]
        month, day, hour, minute, second = toy
        if not (
            (1 <= month <= 12)
            and (1 <= day <= monthrange(2000, month)[1])
            and (hour <= 23)
            and (minute <= 59)
            and (second <= 59)
        ):
            invalid.add(name)
            context.api.fail(
                f'Keyword "{name}" does not define a valid time of year',
                call,
                code=CALL_ARG,
            )
        elif (other := toy2name.setdefault(toy, name)) != name:
            context.api.fail(
                f'Keywords "{other}" and "{name}" define the same time of year',
                call,
                code=CALL_ARG,
            )
    return invalid


def _check_thresholds(
    context: MethodSigContext, call: CallExpr, name2standard: dict[str, str]
) -> None:
    """Report different names for the same threshold value."""
    standard2name: dict[str, str] = {}
    for name, standard in name2standard.items():
        if (other := standard2name.setdefault(standard, name)) != name:
            context.api.fail(
                f'Keywords "{other}" and "{name}" define the same threshold value',
                call,
                code=CALL_ARG,
            )


def _report_deprecation(context: MethodSigContext, call: CallExpr, msg: str) -> None:
    if context.api.options.report_deprecated_as_note:
        context.api.msg.note(msg, call, code=DEPRECATED)
    else:
        context.api.fail(msg, call, code=DEPRECATED)


def _insert_zip_keywords(
    context: MethodSigContext,
    var_inst: Instance,
    type_: type[float],
    signature: CallableType,
) -> CallableType:
    """Replace the arbitrary keyword arguments `constants` of zip parameters with the
    lowercase names of the relevant constants (the main model's ones for submodels,
    see `LANDTYPES`) and give them and `default` the parameter's scalar type."""
    if (
        (var_inst.type.fullname not in ZIP_CONSTANTS)
        or (not signature.arg_kinds)
        or (signature.arg_kinds[-1] != ARG_STAR2)
        or (signature.arg_names[-1] != "constants")
        or ((scalar := _get_vectorlike(context, 0, type_, input_=True)) is None)
    ):
        return signature
    if (constants := ZIP_CONSTANTS[var_inst.type.fullname]) is None:
        family2landtypes = _decode_landtypes(var_inst)
        if (
            landtypes := family2landtypes.get(_get_family(var_inst.type.fullname))
        ) is None:
            return signature
        constants = tuple(landtypes.split(","))
    names = list(signature.arg_names[:-1])
    kinds = list(signature.arg_kinds[:-1])
    types = [
        scalar if n == "default" else t for n, t in zip(names, signature.arg_types)
    ]
    for name in constants:
        names.append(name)
        kinds.append(ARG_NAMED_OPT)
        types.append(scalar)
    return signature.copy_modified(arg_types=types, arg_kinds=kinds, arg_names=names)


def _insert_entry_or_row_keywords(
    context: MethodSigContext,
    var_inst: Instance,
    type_: type[float],
    signature: CallableType,
) -> CallableType:
    """Replace the arbitrary keyword arguments `entries` of |KeywordParameter1D| and
    `rows` of |KeywordParameter2D| subclasses with the entry or row names (the main
    model's land types for names depending on it, see `LANDTYPES`), give them the type
    the parameter's `TYPE` requires, and report missing and unknown names."""
    if (
        (var_inst.type.fullname not in KEYWORD_NAMES)
        or (not signature.arg_kinds)
        or (signature.arg_kinds[-1] != ARG_STAR2)
        or ((kind := signature.arg_names[-1]) not in ("entries", "rows"))
    ):
        return signature
    ndim = 1 if kind == "rows" else 0
    if (value_type := _get_vectorlike(context, ndim, type_, input_=True)) is None:
        return signature
    if (names := KEYWORD_NAMES[var_inst.type.fullname]) is None:
        family2landtypes = _decode_landtypes(var_inst)
        if (
            landtypes := family2landtypes.get(_get_family(var_inst.type.fullname))
        ) is None:
            return signature
        names = tuple(landtypes.split(","))
    unknown: list[str] = []
    if (
        isinstance(call := context.context, CallExpr)
        and call.arg_names
        and all(k == ARG_NAMED for k in call.arg_kinds)
        and ("auxfile" not in call.arg_names)
    ):
        given = set(call.arg_names)
        missing = [n for n in names if n not in given]
        unknown = [n for n in call.arg_names if (n is not None) and (n not in names)]
        attr = "entrynames" if kind == "entries" else "rownames"
        for adjective, problems, explanation in (
            ("Missing", missing, f'each name in "{attr}" is required'),
            ("Unexpected", unknown, f'not in "{attr}"'),
        ):
            if problems:
                plural = "s" if len(problems) > 1 else ""
                quoted = ", ".join(f'"{n}"' for n in problems)
                context.api.fail(
                    f"{adjective} keyword argument{plural} {quoted} ({explanation})",
                    call,
                    code=CALL_ARG,
                )
    allnames = list(names) + unknown
    return signature.copy_modified(
        arg_types=signature.arg_types[:-1] + len(allnames) * [value_type],
        arg_kinds=signature.arg_kinds[:-1] + len(allnames) * [ARG_NAMED_OPT],
        arg_names=signature.arg_names[:-1] + allnames,
    )


def _is_alias(type_: Type, name: str) -> bool:
    return (
        isinstance(type_, TypeAliasType)
        and ((alias := type_.alias) is not None)
        and (alias.fullname == f"hydpy.core.typingtools.{name}")
    )


def method_hook(context: AttributeContext) -> Type:
    """
    `ModelX.__getattr__("calc_x_v1" or "calc_x") -> modeltools.Method`
    -->
    `ModelX.__getattr__("calc_x_v1" or "calc_x") -> modelx.modelx_model.Calc_X_V1`
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and isinstance(model_inst := context.type, Instance)
        and (model_map := MODEL_MAP.get(model_inst.type.fullname.rpartition(".")[0]))
        and isinstance(member_expr := context.context, MemberExpr)
        and isinstance(default := get_proper_type(context.default_attr_type), AnyType)
        and (default.type_of_any == TypeOfAny.explicit)
    ):
        if (attr_name := member_expr.name) in model_map:
            module_name, method_name = model_map[attr_name]
            if (module_type := api.modules.get(module_name)) is None:
                return context.default_attr_type
            if (
                isinstance(method_info := module_type.names[method_name].node, TypeInfo)
                and ((call_sym := method_info.get("__call__")) is not None)
                and isinstance(call_node := call_sym.node, Decorator)
                and isinstance(
                    call_type := get_proper_type(call_node.var.type), CallableType
                )
            ):
                if method_info.has_base("hydpy.core.modeltools.AutoMethod"):
                    return bind_self(
                        bind_self(call_type, is_classmethod=True), model_inst
                    )
                return bind_self(call_type, model_inst)
        context.api.msg.report(
            msg=f"Model `{model_inst.type.fullname}` has no method `{attr_name}`.",
            context=member_expr,
            severity="error",
            code=ATTR_DEFINED,
            origin_context=None,
        )
    return context.default_attr_type


def variables_hook1(context: AttributeContext) -> Type:
    """
    `ModelX.Parameters[T, ...]`
    -->
    `ModelX.Parameters[ModelX, ...]`
    """
    if isinstance(model_inst := context.type, Instance) and isinstance(
        vars_inst := get_proper_type(context.default_attr_type), Instance
    ):
        new_inst = vars_inst.copy_modified(args=(model_inst,) + vars_inst.args[1:])
        new_inst.extra_attrs = _forward_landtypes(model_inst)
        return new_inst
    return context.default_attr_type


def variables_hook2(context: AttributeContext) -> Type:
    """
    `ControlParameters[ModelX, ...].Parameters[T, ...]`
    -->
    `ControlParameters[ModelX, ...].Parameters[ModelX, ...]`
    """
    if isinstance(subvars_inst := context.type, Instance) and isinstance(
        vars_inst := get_proper_type(context.default_attr_type), Instance
    ):
        return vars_inst.copy_modified(
            args=(subvars_inst.args[0],) + vars_inst.args[1:]
        )
    return context.default_attr_type


def subvariables_hook1(context: AttributeContext) -> Type:
    """
    `Parameters[ModelX, ...].ControlParameters[T, ...]`
    -->
    `Parameters[ModelX, ...].ControlParameters[ModelX, ...]`
    """
    if isinstance(vars_inst := context.type, Instance) and isinstance(
        subvars_inst := get_proper_type(context.default_attr_type), Instance
    ):
        new_inst = subvars_inst.copy_modified(
            args=(vars_inst.args[0],) + subvars_inst.args[1:]
        )
        new_inst.extra_attrs = _forward_landtypes(vars_inst)
        return new_inst
    return context.default_attr_type


def subvariables_hook2(context: AttributeContext) -> Type:
    """
    ParX.subvars --> `SubParameters[TM_co, ...]`
    -->
    ParX.subvars --> `ControlParameters[BaseModelX, ...]`
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and isinstance(var_inst := context.type, Instance)
        and (var_data := VAR_MAP_2.get(var_inst.type.fullname))
    ):
        model_module_name, subgroup_module_name, subgroup_name = var_data
        if (
            (model_module_type := api.modules.get(model_module_name))
            and (model_sym := model_module_type.names.get("Model"))
            and isinstance(model_info := model_sym.node, TypeInfo)
            and (subgroup_module_type := api.modules.get(subgroup_module_name))
            and (subgroup_sym := subgroup_module_type.names.get(subgroup_name))
            and isinstance(subgroup_info := subgroup_sym.node, TypeInfo)
        ):
            return Instance(subgroup_info, args=[Instance(model_info, args=[])])
    return context.default_attr_type


def variable_hook(context: AttributeContext) -> Type:
    """
    `ControlParameters[ModelX, ...].__getattr__("par") -> parametertools.Parameter`
    -->
    `ControlParameters[ModelX, ...].__getattr__("par") -> modelx.modelx_control.Par`
    """
    var_type = _get_variable_type(context=context, subvars_type=context.type, kind=None)
    if var_type is None:
        return _get_regular_parameter_type(context.default_attr_type)
    return var_type


def parametersubset_hook(context: AttributeContext) -> Type:
    """
    `RegularParameters[ControlParameters[ModelX, ...]].__getattr__("par")
    -> parametertools.Parameter`
    -->
    `RegularParameters[ControlParameters[ModelX, ...]].__getattr__("par")
    -> modelx.modelx_control.Par`

    `SpecialParameters[ControlParameters[ModelX, ...]].__getattr__("par")
    -> parametertools.SpecialParameter`
    -->
    `SpecialParameters[ControlParameters[ModelX, ...]].__getattr__("par")
    -> modelx.modelx_control.Par`
    """
    if isinstance(subset_inst := context.type, Instance) and (
        len(args := subset_inst.args) > 0
    ):
        kind: Literal["regular", "special"] | None = None
        if subset_inst.type.has_base("hydpy.core.parametertools.RegularParameters"):
            kind = "regular"
        elif subset_inst.type.has_base("hydpy.core.parametertools.SpecialParameters"):
            kind = "special"
        var_type = _get_variable_type(context=context, subvars_type=args[0], kind=kind)
        if var_type is not None:
            return var_type
    return context.default_attr_type


def _get_variable_type(
    context: AttributeContext,
    subvars_type: Type,
    kind: Literal["regular", "special"] | None,
) -> Type | None:
    """Return the type of the variable addressed via the given subgroup type (and of the
    given kind) or None if the model or the attribute name is unknown or if the
    attribute is a real member of the accessed object."""
    if (
        isinstance(api := context.api, TypeChecker)
        and isinstance(owner_inst := context.type, Instance)
        and isinstance(subvars_inst := get_proper_type(subvars_type), Instance)
        and (len(args := subvars_inst.args) > 0)
        and isinstance(model_inst := get_proper_type(args[0]), Instance)
        and (model_map := VAR_MAP_1.get(model_inst.type.fullname))
        and isinstance(member_expr := context.context, MemberExpr)
        and (owner_inst.type.get(member_expr.name) is None)
    ):
        attr_name = member_expr.name
        if (subvars_map := model_map.get(subvars_inst.type.fullname)) and (
            attr_name in subvars_map
        ):
            module_name, var_name = subvars_map[attr_name]
            if (module_type := api.modules.get(module_name)) is None:
                return context.default_attr_type
            var_info = module_type.names[var_name].node
            assert isinstance(var_info, TypeInfo)
            special = var_info.has_base("hydpy.core.parametertools.SpecialParameter")
            if (kind is None) or ((kind == "special") == special):
                extra_attrs = None
                fullname = var_info.fullname
                if (ZIP_CONSTANTS.get(fullname, ()) is None) or (
                    KEYWORD_NAMES.get(fullname, ()) is None
                ):
                    extra_attrs = _forward_landtypes(model_inst)
                return Instance(typ=var_info, args=[], extra_attrs=extra_attrs)
        var_type = (
            subvars_inst.type.fullname.rpartition(".")[-1]
            .replace("Parameters", " parameter")
            .replace("Sequences", " sequence")
            .lower()
        )
        if kind is not None:
            var_type = f"{kind} {var_type}"
        context.api.msg.report(
            msg=f"Model `{model_inst.type.fullname}` has no {var_type} `{attr_name}`.",
            context=member_expr,
            severity="error",
            code=ATTR_DEFINED,
            origin_context=None,
        )
        return AnyType(type_of_any=TypeOfAny.from_error)
    return None


def _get_regular_parameter_type(type_: Type) -> Type:
    """
    `SubParameters[Any, ...].__getattr__("par") -> Parameter | SpecialParameter`
    -->
    `SubParameters[Any, ...].__getattr__("par") -> Parameter`

    For convenience, we treat parameters accessed via attribute names as regular
    parameters if the actual model type is unknown.
    """
    if isinstance(union := get_proper_type(type_), UnionType):
        for item in union.items:
            if (
                isinstance(item := get_proper_type(item), Instance)
                and item.type.fullname == "hydpy.core.parametertools.Parameter"
            ):
                return item
    return type_


def _get_ndim_and_type(
    context: AttributeContext | MethodSigContext,
) -> tuple[int, type] | None:
    if isinstance(var_inst := context.type, Instance) and (
        (fullname := var_inst.type.fullname) in VAR_INFO
    ):
        return VAR_INFO[fullname]
    return None


def _get_vectorlike(
    context: AttributeContext | MethodSigContext,
    ndim: int,
    type_: type[float],
    input_: bool,
) -> Type | None:
    if not isinstance(api := context.api, TypeChecker):
        return None
    match ndim:
        case 0:
            if (
                ((module := api.modules.get("builtins")) is not None)
                and ((scalar_sym := module.names.get(type_.__name__)) is not None)
                and isinstance(scalar_info := scalar_sym.node, TypeInfo)
            ):
                return Instance(scalar_info, args=[])
            return None
        case 1:
            prefix = "Vector"
        case 2:
            prefix = "Matrix"
        case 3:
            prefix = "Tensor"
        case _:
            return None
    middle = "InputComplete" if input_ else ""
    suffix = type_.__name__.capitalize()
    vl_name = f"{prefix}{middle}{suffix}"
    if (
        ((module := api.modules.get("hydpy.core.typingtools")) is not None)
        and ((vl_sym := module.names.get(vl_name)) is not None)
        and isinstance(vl_node := vl_sym.node, TypeAlias)
    ):
        return vl_node.target
    return None


def _get_values_or_series(context: AttributeContext, series: bool) -> Type:
    ndim_type = _get_ndim_and_type(context)
    if ndim_type is None:
        return context.default_attr_type
    vectorlike = _get_vectorlike(
        context=context,
        ndim=ndim_type[0] + series,
        type_=ndim_type[1],
        input_=context.is_lvalue,
    )
    if vectorlike is None:
        return context.default_attr_type
    return vectorlike


def values_hook(context: AttributeContext) -> Type:
    """
    `ParameterX.value(s) -> Any`
    -->
    `ParameterX.value(s) -> float`
    `ParameterX.value(s) -> ndarray[int]`
    ...

    `ParameterX.value(s) <- Any
    -->
    `ParameterX.value(s) <- float
    `ParameterX.value(s) <- int | [int] | ndarray[int]
    ...
    """
    return _get_values_or_series(context=context, series=False)


def series_hook(context: AttributeContext) -> Type:
    """
    `SequenceX.series -> Any`
    -->
    `SequenceX.series -> ndarray[int]`
    ...

    `SequenceX.series <- Any
    -->
    `SequenceX.series <- float
    `SequenceX.series <- int | [int] | ndarray[int]
    ...
    """
    return _get_values_or_series(context=context, series=True)


def shape_hook(context: AttributeContext) -> Type:
    """
    `VariableX.shape -> tuple[int, ...]`
    `VariableY.shape -> tuple[int, ...]`
    -->
    `VariableX.shape -> tuple[int]`
    `VariableY.shape -> tuple[int, int]`

    `VariableX.shape <- int | tuple[int, ...]
    `VariableY.shape <- int | tuple[int, ...]
    -->
    `VariableX.shape <- int, tuple[int]
    `VariableY.shape <- tuple[int, int]
    """
    default = context.default_attr_type
    ndim_type = _get_ndim_and_type(context)
    if (ndim_type is None) or not isinstance(api := context.api, TypeChecker):
        return default
    int_inst = api.named_type("builtins.int")
    tuple_type = TupleType(
        cast(list[Type], ndim_type[0] * [int_inst]),
        fallback=api.named_type("builtins.tuple"),
    )
    if (ndim_type[0] == 1) and context.is_lvalue:
        return UnionType([int_inst, tuple_type])
    return tuple_type


class MypyPlugin(Plugin):
    """Mypy plugin for HydPy."""

    relevant_sources: Final[tuple[str, ...]]
    section: Final[str] = "hydpy.mypy_plugin"
    option: Final[str] = "relevant_sources"

    def __init__(self, options: Options) -> None:
        self.relevant_sources = self._parse_configfile(options.config_file)

    @classmethod
    def _parse_configfile(cls, name: str | None) -> tuple[str, ...]:
        if (name is None) or (name.lower() != "mypy.ini"):
            warn(
                "The Mypy plugin for HydPy currently only works when configured within "
                "a mypy.ini file."
            )
            return ()
        cf = ConfigParser()
        cf.read(name)
        if not cf.has_section(cls.section):
            warn(f"The config file `{name}` misses the required {cls.section} section.")
            return ()
        if not cf.has_option(cls.section, cls.option):
            warn(f"The config file `{name}` misses the required {cls.option} option.")
            return ()
        return tuple(v.strip() for v in cf.get(cls.section, cls.option).split(","))

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        """Add all model main modules and variable modules the dependencies."""
        if any(file.fullname.startswith(s) for s in self.relevant_sources):
            return [(10, "hydpy.core.typingtools", -1)] + [
                (10, m, -1) for m in MODEL_MAP
            ]
        return []

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if fullname == "hydpy.core.importtools.SubmodelAdder.__call__":
            return submodeladder_call_hook
        if fullname == "hydpy.core.importtools.SubmodelAdder.__enter__":
            return submodeladder_enter_hook
        return None

    def get_function_hook(
        self, fullname: str
    ) -> Callable[[FunctionContext], Type] | None:
        """Hooks for refining return types."""
        if fullname == "hydpy.core.importtools.prepare_model":
            return prepare_model_hook
        return None

    def get_method_signature_hook(
        self, fullname: str
    ) -> Callable[[MethodSigContext], FunctionLike] | None:
        if fullname.endswith(".trim"):
            return trim_hook
        if fullname.endswith(".__call__"):
            return call_hook
        return None

    def get_attribute_hook(
        self, fullname: str
    ) -> Callable[[AttributeContext], Type] | None:
        """Hooks for refining attribute types."""
        if fullname in VALUES:
            return values_hook
        if fullname in VAR_SHAPE:
            return shape_hook
        if fullname in SERIES:
            return series_hook
        if fullname in VARS1:
            return variables_hook1
        if fullname in VARS2:
            return variables_hook2
        if fullname in SUBVARS1:
            return subvariables_hook1
        if fullname in SUBVARS2:
            return subvariables_hook2
        return {
            "hydpy.core.variabletools.SubVariables": variable_hook,
            "hydpy.core.parametertools.ParameterSubset": parametersubset_hook,
            "hydpy.core.modeltools.Model": method_hook,
        }.get(fullname.rpartition(".")[0])


def plugin(version: str) -> type[MypyPlugin]:  # pylint: disable=unused-argument
    """Make the plugin directly available."""
    return MypyPlugin
