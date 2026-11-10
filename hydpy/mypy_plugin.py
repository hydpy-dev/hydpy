# pylint: disable=too-many-boolean-expressions
"""This module provides a Mypy plugin that infers more precise types and warns about
potential problems in situations where HydPy relies on runtime behaviour that is not
(and possibly cannot be) expressed via static type hints."""

from calendar import monthrange
from collections.abc import Sequence
from configparser import ConfigParser
from os.path import join, split
from hashlib import sha256
from pickle import loads
import re
from functools import partial
from typing import Callable, cast, Final, Literal, NamedTuple
from warnings import warn

from mypy.checker import TypeChecker
from mypy.checkmember import analyze_member_access
from mypy.errorcodes import (
    ARG_TYPE,
    ASSIGNMENT,
    ATTR_DEFINED,
    CALL_ARG,
    DEPRECATED,
    INDEX,
    OPERATOR,
)
from mypy.message_registry import ErrorMessage
from mypy.messages import format_type
from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_OPT,
    ARG_POS,
    ARG_STAR,
    ARG_STAR2,
    Argument,
    CallExpr,
    ClassDef,
    Decorator,
    Expression,
    FuncDef,
    ListComprehension,
    ListExpr,
    MemberExpr,
    MypyFile,
    NameExpr,
    OverloadedFuncDef,
    TempNode,
    TupleExpr,
    TypeAlias,
    TypeInfo,
    Var,
)
from mypy.options import Options
from mypy.plugin import (
    AttributeContext,
    CheckerPluginInterface,
    ClassDefContext,
    FunctionContext,
    Plugin,
    MethodContext,
    MethodSigContext,
    ReportConfigContext,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins.common import add_method_to_class
from mypy.semanal_shared import has_placeholder
from mypy.subtypes import is_same_type, is_subtype
from mypy.typeops import bind_self, make_simplified_union
from mypy.types import (
    AnyType,
    CallableType,
    ExtraAttrs,
    FunctionLike,
    get_proper_type,
    LiteralType,
    Instance,
    NoneType,
    Overloaded,
    TupleType,
    Type,
    TypeAliasType,
    TypeOfAny,
    TypeVarType,
    UnboundType,
    UninhabitedType,
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

FASTACCESS = set(
    [
        "hydpy.core.variabletools.SubVariables.fastaccess",
        "hydpy.core.sequencetools.StateSequences.fastaccess_old",
        "hydpy.core.sequencetools.StateSequences.fastaccess_new",
    ]
)

SUBGROUPS = set(
    [
        "hydpy.core.parametertools.ControlParameters",
        "hydpy.core.parametertools.DerivedParameters",
        "hydpy.core.parametertools.FixedParameters",
        "hydpy.core.parametertools.SolverParameters",
        "hydpy.core.sequencetools.InputSequences",
        "hydpy.core.sequencetools.FactorSequences",
        "hydpy.core.sequencetools.FluxSequences",
        "hydpy.core.sequencetools.StateSequences",
        "hydpy.core.sequencetools.LogSequences",
        "hydpy.core.sequencetools.AideSequences",
        "hydpy.core.sequencetools.InletSequences",
        "hydpy.core.sequencetools.OutletSequences",
        "hydpy.core.sequencetools.ObserverSequences",
        "hydpy.core.sequencetools.ReceiverSequences",
        "hydpy.core.sequencetools.SenderSequences",
    ]
)

LINKSEQUENCES = set(
    [
        "hydpy.core.sequencetools.InletSequences",
        "hydpy.core.sequencetools.OutletSequences",
        "hydpy.core.sequencetools.ObserverSequences",
        "hydpy.core.sequencetools.ReceiverSequences",
        "hydpy.core.sequencetools.SenderSequences",
    ]
)

VALUES = set(
    [
        "hydpy.core.variabletools.Variable.value",
        "hydpy.core.variabletools.Variable.values",
        "hydpy.core.parametertools.CallbackParameter.value",
        "hydpy.core.sequencetools.NodeSequence.value",
        "hydpy.core.sequencetools.StateSequence.new",
        "hydpy.core.sequencetools.StateSequence.old",
    ]
)
SERIES = set(
    [
        "hydpy.core.sequencetools.IOSequence.series",
        "hydpy.core.sequencetools.IOSequence.simseries",
        "hydpy.core.sequencetools.IOSequence.evalseries",
    ]
)

# '__add__': ('__add__', False), '__radd__': ('__add__', True), '__sub__': ...
BINARY_OPERATORS: Final = {
    f"__{prefix}{name}__": (f"__{name}__", prefix == "r")
    for name in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow", "divmod")
    for prefix in ("", "r")
}

# '__iadd__': '__add__', '__isub__': '__sub__', ...
INPLACE_OPERATORS: Final = {
    f"__i{name}__": f"__{name}__"
    for name in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow")
}

UNARY_OPERATORS: Final = (
    "__pos__",
    "__neg__",
    "__abs__",
    "__invert__",
    "__floor__",
    "__ceil__",
    "__trunc__",
    "__round__",
)

# '_operator.pos': '__pos__', 'operator.__pos__': '__pos__', ...
UNARY_FUNCTIONS: Final = {
    "builtins.abs": "__abs__",
    "builtins.round": "__round__",
    "math.floor": "__floor__",
    "math.ceil": "__ceil__",
    "math.trunc": "__trunc__",
    **{
        fullname: f"__{method}__"
        for name, method in (
            ("pos", "pos"),
            ("neg", "neg"),
            ("abs", "abs"),
            ("invert", "invert"),
            ("inv", "invert"),
        )
        for fullname in (f"_operator.{name}", f"operator.__{name}__")
    },
}

# '_operator.add': '__add__', 'operator.__add__': '__add__', ...
# (`divmod` is missing because Mypy uses `Variable.__divmod__` instead)
BINARY_FUNCTIONS: Final = {
    "builtins.pow": "__pow__",
    **{
        fullname: f"__{name}__"
        for name in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow")
        for fullname in (f"_operator.{name}", f"operator.__{name}__")
    },
}

# '_operator.iadd': '__add__', 'operator.__iadd__': '__add__', ...
INPLACE_FUNCTIONS: Final = {
    fullname: f"__{name}__"
    for name in ("add", "sub", "mul", "truediv", "floordiv", "mod", "pow")
    for fullname in (f"_operator.i{name}", f"operator.__i{name}__")
}

SCALAR_TYPES: Final = {
    "builtins.float": float,
    "builtins.int": int,
    "builtins.bool": bool,
}

# 'math.acos': 'float', 'math.acosh': 'float', ...
SCALAR_FUNCTIONS: Final = {
    "builtins.complex": "complex",
    "builtins.float": "float",
    "builtins.int": "int",
    **{
        f"math.{name}": "float"
        for name in (
            "acos",
            "acosh",
            "asin",
            "asinh",
            "atan",
            "atan2",
            "atanh",
            "cbrt",
            "copysign",
            "cos",
            "cosh",
            "degrees",
            "erf",
            "erfc",
            "exp",
            "exp2",
            "expm1",
            "fabs",
            "fma",
            "fmod",
            "frexp",
            "gamma",
            "hypot",
            "isclose",
            "isfinite",
            "isinf",
            "isnan",
            "ldexp",
            "lgamma",
            "log",
            "log10",
            "log1p",
            "log2",
            "modf",
            "nextafter",
            "pow",
            "radians",
            "remainder",
            "sin",
            "sinh",
            "sqrt",
            "tan",
            "tanh",
            "ulp",
        )
    },
}

SIZED_FUNCTIONS: Final = ("builtins.len", "builtins.reversed")

# functions iterating over their first argument:
FIRST_ITERABLE_FUNCTIONS: Final = (
    "builtins.list",
    "builtins.tuple",
    "builtins.set",
    "builtins.frozenset",
    "builtins.sorted",
    "builtins.enumerate",
    "builtins.sum",
    "builtins.any",
    "builtins.all",
)

# functions iterating over their first argument only if it is the only positional one:
SINGLE_ITERABLE_FUNCTIONS: Final = ("builtins.min", "builtins.max", "builtins.iter")

# functions comparing the items of their (first) argument if not given a key function:
COMPARING_FUNCTIONS: Final = ("builtins.min", "builtins.max", "builtins.sorted")

# functions iterating over all their arguments (or all but a leading function):
ALL_ITERABLE_FUNCTIONS: Final = ("builtins.zip", "builtins.map", "builtins.filter")

REFINED_MEMBERS: Final = frozenset(
    VALUES
    | SERIES
    | {
        f"hydpy.core.variabletools.Variable.{method}"
        for method in (
            *BINARY_OPERATORS,
            *INPLACE_OPERATORS,
            *UNARY_OPERATORS,
            "__getitem__",
            "__setitem__",
            "__iter__",
            "__contains__",
        )
    }
)
"""The full names of all members annotated with `GeneralHook` because the plugin refines
their types."""

CONDITION_GROUPS: Final = {
    "states": "hydpy.core.sequencetools.StateSequences",
    "logs": "hydpy.core.sequencetools.LogSequences",
}

DIRPATH = split(__file__)[0]

# 'hydpy.models.arma_rimorido': {
#     'pick_q_v1': ('hydpy.models.arma.arma_model', 'Pick_Q_V1'),
#     'pick_q': ('hydpy.models.arma.arma_model', 'Pick_Q_V1'), ...}, ...
MODEL_MAP: dict[str, dict[str, tuple[str, str]]]

# 'hydpy.models.arma_rimorido.Model': {
#     'hydpy.core.parametertools.ControlParameters': {
#         'responses': ('hydpy.models.arma.arma_control', 'Responses'), ...}, ...}, ...
VAR_MAP_1: dict[str, dict[str, dict[str, tuple[str, str]]]]

# 'hydpy.models.arma.arma_control.Responses': (
#     'hydpy.models.arma.arma_model', 'hydpy.core.parametertools', 'ControlParameters'
# ), ...
VAR_MAP_2: dict[str, tuple[str, str, str]]

# 'hydpy.models.arma.arma_derived.Nmb': (0, int),
# 'hydpy.models.arma.arma_derived.MaxQ': (1, float), ...
VAR_INFO: dict[str, tuple[int, type[float]]]

# 'hydpy.core.variabletools.Variable.shape',
# 'hydpy.core.parametertools.SeasonalParameter.shape', ...
VAR_SHAPE: set[str]

# 'hydpy.models.hland.hland_control.RecStep',
# 'hydpy.models.rconc.rconc_control.NmbSteps', ...
VAR_TIMEINT: set[str]

# 'hydpy.models.evap.evap_control.Water': None, ...,
# 'hydpy.models.hland.hland_control.ZoneArea': ('field', 'forest', ...), ...
ZIP_CONSTANTS: dict[str, tuple[str, ...] | None]

# 'hydpy.models.hland_96.Model.add_aetmodel_v1': ('field', 'forest', ...), ...
ADDER_KEYWORDS: dict[str, tuple[str, ...]]

# 'hydpy.models.evap.evap_control.Albedo': None, ...,
# 'hydpy.models.evap.evap_control.MonthFactor': ('jan', 'feb', ...), ...
KEYWORD_NAMES: dict[str, tuple[str, ...] | None]

# 'hydpy.models.arma.arma_control.Responses': 'object', ...,
# 'hydpy.models.dam.dam_control.WaterVolume2WaterLevel':
#     'interputils.SimpleInterpolator', ...
SPECIAL_CTYPES: dict[str, str]

with open(join(DIRPATH, "conf", "mypy_plugin_data.pickle"), "rb") as file_:
    _DATA: Final = file_.read()
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
    SPECIAL_CTYPES,
) = loads(_DATA)

DATA_HASH: Final = sha256(_DATA).hexdigest()
"""Hash of the plugin data (for invalidating Mypy's cache after updates)."""

TOY_FORMAT: Final = re.compile(r"toy(_[0-9]{1,2}){1,5}")
"""Standard format of time of year names."""

THRESHOLD_FORMAT: Final = re.compile(r"th_(0|[1-9][0-9]*)_(0|[0-9]*[1-9])")
"""Standard format of threshold names."""

SUBMODELS_FORMAT: Final = re.compile(r"(.+)_(0|[1-9][0-9]*)")
"""Standard format of the names of submodels handled by `SubmodelsProperty`
instances."""

BASEMODEL_MODULE_FORMAT: Final = re.compile(r"hydpy\.models\.([a-z0-9]+)\.\1_model")
"""Standard format of the names of base model modules."""

BASEMODEL_PACKAGE_FORMAT: Final = re.compile(
    r"hydpy\.models\.([a-z0-9]+)\.\1_[a-z0-9_]+"
)
"""Standard format of the names of all modules of base model packages."""


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
    VariableX.trim(ScalarInputFloat | None, ScalarInputFloat | None) -> bool
    VariableY.trim(VectorInputCompleteInt | None, VectorInputCompleteInt | None) -> bool
    ...
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


LITERALS: Final = (ListExpr, TupleExpr, ListComprehension)


def _match_literal(
    api: TypeChecker, expr: Expression, candidates: Type
) -> tuple[Type | None, Type]:
    """Return the first of the given candidate types that fits the given container
    literal (like `[x, y]`), if any, and the literal's type inferred in the context of
    this candidate (or without context, if no candidate fits).

    Mypy infers container literals based on the type context.  However, contexts like
    `Any` (unknown) or unions of multiple sequence types (ambiguous) do not help, and
    mypy falls back to types like `list[Any]` (too wide, so invalid items pass) or
    `list[object]` (joined, so valid items like `[numpy.int64(1), 2]` fail).  Hence,
    we try each candidate separately.
    """
    proper = get_proper_type(candidates)
    items = proper.items if isinstance(proper, UnionType) else [candidates]
    for item in items:
        with api.msg.filter_errors() as watcher:
            with api.local_type_map:
                inferred = api.expr_checker.accept(expr, type_context=item)
        if not watcher.has_new_errors() and is_subtype(inferred, item):
            return item, inferred
    with api.msg.filter_errors(), api.local_type_map:
        return None, api.expr_checker.accept(expr)


def _split_star_args(
    context: MethodSigContext, signature: CallableType, candidates: Type
) -> CallableType:
    """Replace the arbitrary positional arguments of the given signature with one
    positional argument per given value, typed with the candidate a container literal
    fits (see `_match_literal`) or with all candidates otherwise."""
    default = context.default_signature
    if (
        not isinstance(api := context.api, TypeChecker)
        or (ARG_STAR not in default.arg_kinds)
        or not _is_alias(
            default.arg_types[default.arg_kinds.index(ARG_STAR)], "CallHook"
        )
        or (ARG_STAR not in signature.arg_kinds)
        or not isinstance(call := context.context, CallExpr)
        or (ARG_STAR in call.arg_kinds)
    ):
        return signature
    values = context.args[default.arg_kinds.index(ARG_STAR)]
    if not any(isinstance(v, LITERALS) for v in values):
        return signature
    types_: list[Type] = []
    for value in values:
        match = None
        if isinstance(value, LITERALS):
            match = _match_literal(api, value, candidates)[0]
        types_.append(candidates if match is None else match)
    idx = signature.arg_kinds.index(ARG_STAR)
    return signature.copy_modified(
        arg_types=signature.arg_types[:idx] + types_ + signature.arg_types[idx + 1 :],
        arg_kinds=signature.arg_kinds[:idx]
        + len(values) * [ARG_POS]
        + signature.arg_kinds[idx + 1 :],
        arg_names=signature.arg_names[:idx]
        + len(values) * [None]
        + signature.arg_names[idx + 1 :],
    )


def call_hook(context: MethodSigContext) -> FunctionLike:
    """
    `VariableX.__call__(*values: CallHook, ...) -> None`
    -->
    `VariableX.__call__(*values: ScalarInputFloat, ...) -> None`
    `VariableY.__call__(*values: ScalarInputInt | VectorInputInt, ...) -> None`
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
    default = _insert_entry_or_row_keywords(context, var_inst, types_[0], default)
    return _split_star_args(context, default, values_type)


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


def _refers_to_generalhook(type_: Type | None) -> bool:
    """Tell whether the given type is or contains the type alias `GeneralHook`."""
    if type_ is None:
        return False
    if _is_alias(type_, "GeneralHook"):
        return True
    if isinstance(type_, TypeAliasType):
        return any(_refers_to_generalhook(arg) for arg in type_.args)
    proper = get_proper_type(type_)
    if isinstance(proper, Overloaded):
        return any(_refers_to_generalhook(item) for item in proper.items)
    if isinstance(proper, CallableType):
        return _refers_to_generalhook(proper.ret_type) or any(
            _refers_to_generalhook(arg) for arg in proper.arg_types
        )
    if isinstance(proper, Instance):
        return any(_refers_to_generalhook(arg) for arg in proper.args)
    if isinstance(proper, (TupleType, UnionType)):
        return any(_refers_to_generalhook(item) for item in proper.items)
    return False


def _has_generalhook_member(info: TypeInfo, name: str) -> bool:
    """Tell whether the given member of the given class is annotated with `GeneralHook`
    where it is defined, which is the class itself or one of its base classes.

    If a subclass overrides such a member with a more specific annotation, the result
    is `False`, so that the plugin respects this annotation instead of refining the
    member's type.
    """
    if (definer := info.get_containing_type_info(name)) is None:
        return False
    node = definer.names[name].node
    if isinstance(node, Decorator):
        node = node.func
    return isinstance(node, (FuncDef, OverloadedFuncDef)) and _refers_to_generalhook(
        node.type
    )


def _may_refine(type_: Type, name: str) -> bool:
    """Tell whether the plugin may refine an operation that involves the given member of
    the given (operand) type.

    Only variables can prevent refinement by overriding a member annotated with
    `GeneralHook` more specifically (see `_has_generalhook_member`).  Hence, the result
    is always `True` for non-variable types.
    """
    if isinstance(inst := get_proper_type(type_), Instance) and inst.type.has_base(
        "hydpy.core.variabletools.Variable"
    ):
        return _has_generalhook_member(inst.type, name)
    return True


def _reflect(method: str, reflected: bool) -> str:
    """Return the name of the reflected version of the given binary operator method
    (e.g. `__radd__` for `__add__`) if required."""
    return f"__r{method[2:]}" if reflected else method


def method_hook(context: AttributeContext) -> Type:
    """
    `ModelX.__getattr__("calc_x_v1" or "calc_x") -> modeltools.Method`
    -->
    `ModelX.__getattr__("calc_x_v1" or "calc_x") -> modelx.modelx_model.Calc_X_V1`

    Within base model packages, the general model classes of `modeltools` referenced by
    `model`, `self`, or `.model` fall back to the base model.  Then, the plugin also
    resolves old-style submodels (like `pegasush`) and other members of the base model
    class, including those inherited from mixins like `SegmentModel` (e.g. submodel type
    IDs or index properties like `idx_segment`).  Submodels handled by
    `SubmodelProperty` or `SubmodelsProperty` objects remain `Any` (model methods access
    them via `cast`).  The plugin reports all other members as unknown.
    """
    if not (
        isinstance(api := context.api, TypeChecker)
        and isinstance(model_inst := context.type, Instance)
        and isinstance(member_expr := context.context, MemberExpr)
        and isinstance(default := get_proper_type(context.default_attr_type), AnyType)
        and (default.type_of_any == TypeOfAny.explicit)
    ):
        return context.default_attr_type
    basemodule = (
        _get_basemodel_module(api, model_inst)
        if _is_own_model_expression(member_expr.expr)
        else None
    )
    model_module = (
        model_inst.type.fullname.rpartition(".")[0]
        if basemodule is None
        else basemodule
    )
    if not (model_map := MODEL_MAP.get(model_module)):
        return context.default_attr_type
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
                return bind_self(bind_self(call_type, is_classmethod=True), model_inst)
            return bind_self(call_type, model_inst)
    if basemodule is not None:
        if (
            submodel := _get_old_style_submodel_instance(api, basemodule, attr_name)
        ) is not None:
            return submodel
        if (
            member_type := _get_basemodel_member_type(api, basemodule, member_expr)
        ) is not None:
            return member_type
    model_name = (
        model_inst.type.fullname if basemodule is None else f"{basemodule}.Model"
    )
    context.api.msg.report(
        msg=f"Model `{model_name}` has no member `{attr_name}`.",
        context=member_expr,
        severity="error",
        code=ATTR_DEFINED,
        origin_context=None,
    )
    return context.default_attr_type


def _get_basemodel_member_type(
    api: TypeChecker, module_name: str, member_expr: MemberExpr
) -> Type | None:
    """Return the type of the member of the base model defined in the given module that
    the given member expression refers to, if available.

    For submodels handled by `SubmodelProperty` or `SubmodelsProperty` objects, the type
    is still `Any` (we might change this later).
    """
    if ((info := _get_typeinfo(api, f"{module_name}.Model")) is None) or (
        (symbol := info.get(name := member_expr.name)) is None
    ):
        return None
    if isinstance(symbol_type := get_proper_type(symbol.type), Instance) and (
        symbol_type.type.has_base("hydpy.core.modeltools.SubmodelProperty")
        or symbol_type.type.has_base("hydpy.core.modeltools.SubmodelsProperty")
    ):
        return AnyType(TypeOfAny.special_form)
    base_inst = Instance(info, args=[])
    with api.msg.filter_errors():
        return analyze_member_access(
            name,
            base_inst,
            member_expr,
            is_lvalue=False,
            is_super=False,
            is_operator=False,
            original_type=base_inst,
            chk=api,
            suppress_errors=True,
        )


def _get_old_style_submodel_instance(
    api: TypeChecker, module_name: str, attr_name: str
) -> Instance | None:
    """Return the type of the "old-style" submodel defined in the given module that
    models handle via the given attribute name, if available."""
    if (module := api.modules.get(module_name)) is not None:
        for name, symbol in module.names.items():
            if (
                (name.lower() == attr_name)
                and isinstance(info := symbol.node, TypeInfo)
                and info.has_base("hydpy.core.modeltools.Submodel")
            ):
                return Instance(info, args=[])
    return None


def variables_hook1(context: AttributeContext) -> Type:
    """
    `ModelX.Parameters[T, ...]`
    -->
    `ModelX.Parameters[ModelX, ...]`
    """
    if (model_inst := _get_model_instance(context.type)) and isinstance(
        vars_inst := get_proper_type(context.default_attr_type), Instance
    ):
        if (
            isinstance(member_expr := context.context, MemberExpr)
            and _is_own_model_expression(member_expr.expr)
            and (base_inst := _get_basemodel_instance(context.api, model_inst))
        ):
            model_inst = base_inst
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
    if (subvars_type := _get_generic_subvars_type(context)) is not None:
        return subvars_type
    return context.default_attr_type


def _get_generic_subvars_type(context: AttributeContext) -> Type | None:
    """
    `Variable.subvars` --> `SubVariables[Any, Any, ...]`
    -->
    `Variable.subvars` --> `SubVariables[BaseModelX, Parameters[BaseModelX] |
    Sequences[BaseModelX], ...]`

    Only applies within the modules of base model packages, where generic variables
    belong to the base model.
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and isinstance(default := get_proper_type(context.default_attr_type), Instance)
        and (default.type.fullname == "hydpy.core.variabletools.SubVariables")
        and (len(default.args) == 4)
        and isinstance(get_proper_type(default.args[0]), AnyType)
        and (match := BASEMODEL_PACKAGE_FORMAT.fullmatch(api.tree.fullname))
    ):
        base = match.group(1)
        model_info = _get_typeinfo(api, f"hydpy.models.{base}.{base}_model.Model")
        pars_info = _get_typeinfo(api, "hydpy.core.parametertools.Parameters")
        seqs_info = _get_typeinfo(api, "hydpy.core.sequencetools.Sequences")
        if (model_info is None) or (pars_info is None) or (seqs_info is None):
            return None
        model_inst = Instance(model_info, args=[])
        group_type = UnionType(
            [
                Instance(pars_info, args=[model_inst]),
                Instance(seqs_info, args=[model_inst]),
            ]
        )
        return default.copy_modified(args=[model_inst, group_type, *default.args[2:]])
    return None


def fastaccess_hook(context: AttributeContext) -> Type:
    """
    `ControlParameters[ModelX].fastaccess -> FastAccessParameter`
    -->
    `ControlParameters[ModelX].fastaccess -> FastAccessParameter` with the types of the
    values of all control parameters of `ModelX` as extra attributes
    """
    default = context.default_attr_type
    if (
        isinstance(api := context.api, TypeChecker)
        and isinstance(default_inst := get_proper_type(default), Instance)
        and isinstance(subvars_inst := context.type, Instance)
        and ((subvars_name := subvars_inst.type.fullname) in SUBGROUPS)
        and (len(subvars_inst.args) > 0)
        and (model_inst := _get_model_instance(subvars_inst.args[0]))
        and (name_map := _get_model_map(model_inst))
    ):
        subvars_map = name_map[1].get(subvars_name, {})
        link = subvars_name in LINKSEQUENCES
        int_inst = api.named_type("builtins.int")
        attrs: dict[str, Type] = {}
        for attr_name, (module_name, var_name) in subvars_map.items():
            ndim_type = VAR_INFO.get(f"{module_name}.{var_name}")
            if ndim_type is None:
                attrs[attr_name] = _get_special_fastaccess_type(
                    api, f"{module_name}.{var_name}"
                )
                continue
            ndim, type_ = ndim_type
            if (attr_type := _get_fastaccess_type(api, ndim, type_)) is None:
                return default
            attrs[attr_name] = attr_type
            if link and (ndim == 1):
                attrs[f"len_{attr_name}"] = int_inst
            if (var_info := _get_typeinfo(api, f"{module_name}.{var_name}")) is None:
                continue
            if var_info.has_base("hydpy.core.parametertools.KeywordParameter1D"):
                attrs[f"_{attr_name}_entrymin"] = int_inst
            elif var_info.has_base("hydpy.core.parametertools.KeywordParameter2D"):
                attrs[f"_{attr_name}_rowmin"] = int_inst
                attrs[f"_{attr_name}_columnmin"] = int_inst
            if var_info.has_base("hydpy.core.parametertools.CallbackParameter"):
                model_info = _get_typeinfo(api, "hydpy.core.modeltools.Model")
                attrs[f"{attr_name}_callback"] = CallableType(
                    arg_types=[
                        (
                            AnyType(TypeOfAny.special_form)
                            if model_info is None
                            else Instance(model_info, args=[])
                        )
                    ],
                    arg_kinds=[ARG_POS],
                    arg_names=[None],
                    ret_type=NoneType(),
                    fallback=api.named_type("builtins.function"),
                )
        new_inst = default_inst.copy_modified()
        new_inst.extra_attrs = ExtraAttrs(attrs=attrs)
        return new_inst
    if (
        isinstance(api := context.api, TypeChecker)
        and not api.tree.fullname.startswith("hydpy.")
        and isinstance(subvars_inst := context.type, Instance)
        and (len(subvars_inst.args) > 0)
        and (_get_model_instance(subvars_inst.args[0]) is not None)
    ):
        return AnyType(TypeOfAny.special_form)
    return default


def _get_fastaccess_type(
    api: TypeChecker, ndim: int, type_: type[float]
) -> Type | None:
    """Return the type of the values of a variable with the given dimensionality and
    value type, as seen by the methods of a model via `fastaccess` objects."""
    scalar = api.named_type(f"builtins.{type_.__name__}")
    if ndim == 0:
        return scalar
    name = {1: "FastAccessVector", 2: "FastAccessMatrix"}.get(ndim)
    if (name is None) or (
        (info := _get_typeinfo(api, f"hydpy.core.typingtools.{name}")) is None
    ):
        return None
    return Instance(info, args=[scalar])


def _get_special_fastaccess_type(api: TypeChecker, fullname: str) -> Type:
    """Return the type of the object a special parameter hands over to the methods of a
    model via its `fastaccess` object.

    The type follows from the parameter's `CTYPE`: `object` means the parameter hands
    over nothing but `None`, and names like `interputils.SimpleInterpolator` refer to
    the corresponding extension classes of subpackage `hydpy.cythons`.
    """
    if (ctype := SPECIAL_CTYPES.get(fullname)) is None:
        return AnyType(TypeOfAny.special_form)
    if ctype == "object":
        return NoneType()
    if (info := _get_typeinfo(api, f"hydpy.cythons.{ctype}")) is None:
        return AnyType(TypeOfAny.special_form)
    return Instance(info, args=[])


def fastaccess_member_hook(context: AttributeContext) -> Type:
    """
    `FastAccess.__getattr__("var") -> Any`
    -->
    `FastAccess.__getattr__("var") -> float` (or another type stored as an extra
    attribute by `fastaccess_hook`)

    Report an error if a `fastaccess` object with known extra attributes does not
    handle the requested variable.
    """
    if (
        isinstance(fastaccess_inst := context.type, Instance)
        and ((extra_attrs := fastaccess_inst.extra_attrs) is not None)
        and isinstance(member_expr := context.context, MemberExpr)
    ):
        if (attr_type := extra_attrs.attrs.get(member_expr.name)) is not None:
            return attr_type
        context.api.msg.report(
            msg=(
                f"The `fastaccess` object does not handle a variable named "
                f"`{member_expr.name}`."
            ),
            context=member_expr,
            severity="error",
            code=ATTR_DEFINED,
            origin_context=None,
        )
        return AnyType(type_of_any=TypeOfAny.from_error)
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


def _get_typeinfo(api: TypeChecker, fullname: str) -> TypeInfo | None:
    """Return the type information on the class with the given full name, if
    available."""
    module_name, _, class_name = fullname.rpartition(".")
    if (
        ((module := api.modules.get(module_name)) is not None)
        and ((symbol := module.names.get(class_name)) is not None)
        and isinstance(info := symbol.node, TypeInfo)
    ):
        return info
    return None


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
        and (name_map := _get_model_map(model_inst))
        and isinstance(member_expr := context.context, MemberExpr)
        and (owner_inst.type.get(member_expr.name) is None)
    ):
        model_name, model_map = name_map
        attr_name = member_expr.name
        group_name = subvars_inst.type.fullname
        if group_name in model_map:
            subvars_maps = [model_map[group_name]]
        else:
            subvars_maps = [
                subvars_map
                for name, subvars_map in model_map.items()
                if (info := _get_typeinfo(api, name)) and info.has_base(group_name)
            ]
        var_refs = [m[attr_name] for m in subvars_maps if attr_name in m]
        if len(var_refs) > 1:
            return None
        if var_refs:
            module_name, var_name = var_refs[0]
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
            group_name.rpartition(".")[-1]
            .removeprefix("Sub")
            .replace("Variables", " variable")
            .replace("Parameters", " parameter")
            .replace("Sequences", " sequence")
            .lower()
            .strip()
        )
        if kind is not None:
            var_type = f"{kind} {var_type}"
        context.api.msg.report(
            msg=f"Model `{model_name}` has no {var_type} `{attr_name}`.",
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
    context: AttributeContext | MethodContext | MethodSigContext,
) -> tuple[int, type] | None:
    if isinstance(var_inst := context.type, Instance):
        return _get_inherited_ndim_and_type(var_inst.type)
    return None


def _get_vectorlike(
    context: AttributeContext | FunctionContext | MethodContext | MethodSigContext,
    ndim: int,
    type_: type[float],
    input_: bool,
) -> Type | None:
    if not isinstance(api := context.api, TypeChecker):
        return None
    match ndim:
        case 0:
            if input_:
                suffix = type_.__name__.capitalize()
                return _get_alias_target(api, f"ScalarInput{suffix}")
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
    return _get_alias_target(api, f"{prefix}{middle}{suffix}")


def _get_vectorlikes(
    context: AttributeContext | FunctionContext | MethodContext, input_: bool
) -> list[Type] | None:
    """Return the vector-like types of all supported dimensionalities and value types,
    which are the candidates for the values of variables with unknown dimensionality or
    value type."""
    vectorlikes = []
    for ndim in range(4):
        for type_ in (float, int, bool):
            vectorlike = _get_vectorlike(
                context=context, ndim=ndim, type_=type_, input_=input_
            )
            if vectorlike is None:
                return None
            vectorlikes.append(vectorlike)
    return vectorlikes


def _get_any_vectorlike(
    context: AttributeContext | FunctionContext | MethodContext, input_: bool
) -> Type | None:
    """Return the union of the vector-like types of all supported dimensionalities and
    value types."""
    if (vectorlikes := _get_vectorlikes(context=context, input_=input_)) is None:
        return None
    return make_simplified_union(vectorlikes)


def _get_alias_target(api: TypeChecker, name: str) -> Type | None:
    """Return the target of the type alias with the given name defined in module
    `typingtools`, if available."""
    if (
        ((module := api.modules.get("hydpy.core.typingtools")) is not None)
        and ((sym := module.names.get(name)) is not None)
        and isinstance(node := sym.node, TypeAlias)
    ):
        return node.target
    return None


def _get_plain_any(type_: Type) -> Type:
    """Replace `Any` stemming from the type alias `GeneralHook` with an explicit `Any`.

    Without this adjustment, Mypy would infer `float64` instead of `Any` for
    `numpy.sum(numpy.isnan(x))` with `x: GeneralHook` because it ignores `Any` stemming
    from aliases when checking for overload matches.
    """
    if _is_alias(type_, "GeneralHook"):
        return AnyType(TypeOfAny.explicit)
    return type_


def _get_values_or_series(context: AttributeContext, series: bool) -> Type:
    default = _get_plain_any(context.default_attr_type)
    ndim_type = _get_ndim_and_type(context)
    if ndim_type is None:
        # We cannot restrict assignments to all numerical values without making Mypy
        # narrow, e.g., `x.values` to `float` after `x.values = 0.0`.
        return default
    vectorlike = _get_vectorlike(
        context=context,
        ndim=ndim_type[0] + series,
        type_=ndim_type[1],
        input_=context.is_lvalue,
    )
    if vectorlike is None:
        return default
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


def _get_value_type(
    context: FunctionContext | MethodContext, type_: Type
) -> Type | None:
    """Return the type of the value of the given variable type or, if the given type is
    not a variable type, the given type itself.

    Return |None| if the given type is a variable type for which no further information
    is available.
    """
    if not isinstance(inst := get_proper_type(type_), Instance):
        return type_
    if (ndim_type := _get_inherited_ndim_and_type(inst.type)) is not None:
        return _get_vectorlike(
            context=context, ndim=ndim_type[0], type_=ndim_type[1], input_=False
        )
    if inst.type.has_base("hydpy.core.variabletools.Variable"):
        return None
    return type_


def _get_scalar_type(
    context: FunctionContext | MethodContext, ndim: int, type_: type[float]
) -> Type | None:
    """Return the type of the single values of a variable with the given dimensionality
    and value type: a Python scalar type (e.g. `float`) for 0-dimensional variables and
    a numpy scalar type (e.g. `numpy.float64`) for multidimensional variables."""
    vectorlike = _get_vectorlike(context=context, ndim=ndim, type_=type_, input_=False)
    if ndim == 0:
        return vectorlike
    if (
        isinstance(array := get_proper_type(vectorlike), Instance)
        and (len(array.args) == 2)
        and isinstance(dtype := get_proper_type(array.args[1]), Instance)
        and (len(dtype.args) == 1)
    ):
        return dtype.args[0]
    return None


def _get_dimensionality(
    context: FunctionContext | MethodContext, type_: Type
) -> tuple[int, type[float]] | None:
    """Return the dimensionality and the (Python) value type of the given variable,
    scalar, or vector-like type, if determinable."""
    proper = get_proper_type(type_)
    if isinstance(proper, Instance):
        if (ndim_type := _get_inherited_ndim_and_type(proper.type)) is not None:
            return ndim_type
        if (scalar := SCALAR_TYPES.get(proper.type.fullname)) is not None:
            return 0, scalar
    for scalar in (float, int, bool):
        for ndim in (1, 2, 3):
            vectorlike = _get_vectorlike(
                context=context, ndim=ndim, type_=scalar, input_=False
            )
            if (vectorlike is not None) and is_same_type(proper, vectorlike):
                return ndim, scalar
        element = _get_scalar_type(context=context, ndim=1, type_=scalar)
        if (element is not None) and is_same_type(proper, element):
            return 0, scalar
    return None


def _set_dimensionality(
    context: FunctionContext | MethodContext, type_: Type, ndim: int
) -> Type | None:
    """Replace the (unspecific) shape of the given array type, or of all array types
    contained in the given tuple type, with the shape of the given dimensionality."""
    proper = get_proper_type(type_)
    if isinstance(proper, TupleType):
        items = [_set_dimensionality(context, item, ndim) for item in proper.items]
        if any(item is None for item in items):
            return None
        return proper.copy_modified(items=[i for i in items if i is not None])
    if (
        isinstance(proper, Instance)
        and (proper.type.fullname == "numpy.ndarray")
        and (len(proper.args) == 2)
        and isinstance(
            template := get_proper_type(
                _get_vectorlike(context=context, ndim=ndim, type_=float, input_=False)
            ),
            Instance,
        )
    ):
        return proper.copy_modified(args=[template.args[0], proper.args[1]])
    return None


def _check_binary_operation(
    context: FunctionContext | MethodContext, method: str, left: Type, right: Type
) -> Type:
    """Check the given binary operation based on the types of the given values and
    return its result type.

    Mypy checks the operation based on the available stubs.  However, the overloaded
    operator methods of numpy's `ndarray` often lose the dimensionality (and sometimes
    the precise data type) of the result.  Hence, if the dimensionalities and value
    types of both operands are known, we replace numpy's result type by applying the
    operation to the value types and "lifting" the result to the broadcast
    dimensionality.  If this is impossible (for example, for `float ** float`, which
    might be complex for Python scalars, or for `divmod`), we only replace the shape of
    numpy's result type(s).
    """
    assert isinstance(api := context.api, TypeChecker)
    result = api.expr_checker.check_op(
        method=method,
        base_type=left,
        arg=TempNode(right, context=context.context),
        context=context.context,
        allow_reverse=True,
    )[0]
    if (
        ((left_info := _get_dimensionality(context, left)) is None)
        or ((right_info := _get_dimensionality(context, right)) is None)
        or ((ndim := max(left_info[0], right_info[0])) == 0)
        or ((reshaped := _set_dimensionality(context, result, ndim)) is None)
    ):
        return result
    if ((left_info[1], right_info[1]) == (bool, bool)) or isinstance(
        get_proper_type(result), TupleType
    ):
        return reshaped
    with api.msg.filter_errors():
        scalar = api.expr_checker.check_op(
            method=method,
            base_type=api.named_type(f"builtins.{left_info[1].__name__}"),
            arg=TempNode(
                api.named_type(f"builtins.{right_info[1].__name__}"),
                context=context.context,
            ),
            context=context.context,
            allow_reverse=True,
        )[0]
    if isinstance(scalar := get_proper_type(scalar), Instance) and (
        (type_ := SCALAR_TYPES.get(scalar.type.fullname)) is not None
    ):
        lifted = _get_vectorlike(context=context, ndim=ndim, type_=type_, input_=False)
        if lifted is not None:
            return lifted
    return reshaped


def _check_unknown_operation(
    context: FunctionContext | MethodContext,
    method: str,
    left: Type | None,
    right: Type | None,
) -> None:
    """Check the given binary operation involving at least one variable with unknown
    dimensionality or value type (indicated by |None|).

    The operation is erroneous only if it fails for all possible value types.  We then
    report the error for scalar `float` values.
    """
    if (
        not isinstance(api := context.api, TypeChecker)
        or ((left is None) and (right is None))
        or ((candidates := _get_vectorlikes(context, input_=False)) is None)
    ):
        return
    for candidate in candidates:
        with api.msg.filter_errors() as watcher:
            api.expr_checker.check_op(
                method=method,
                base_type=candidate if left is None else left,
                arg=TempNode(
                    candidate if right is None else right, context=context.context
                ),
                context=context.context,
                allow_reverse=True,
            )
        if not watcher.has_new_errors():
            return
    api.expr_checker.check_op(
        method=method,
        base_type=candidates[0] if left is None else left,
        arg=TempNode(
            candidates[0] if right is None else right, context=context.context
        ),
        context=context.context,
        allow_reverse=True,
    )


def binary_operator_hook(context: MethodContext, method: str, reflected: bool) -> Type:
    """
    `VariableX.__add__(object) -> Any`
    -->
    `VariableX.__add__(float) -> float`
    `VariableX.__add__(VectorFloat) -> VectorFloat`
    `VariableX.__add__(VariableY) -> VectorFloat`
    ...
    """
    default = _get_plain_any(context.default_return_type)
    if (
        not isinstance(context.api, TypeChecker)
        or (len(context.arg_types) != 1)
        or (len(context.arg_types[0]) != 1)
        or not _may_refine(context.arg_types[0][0], _reflect(method, not reflected))
    ):
        return default
    self_value = _get_value_type(context, context.type)
    other_value = _get_value_type(context, context.arg_types[0][0])
    left, right = (other_value, self_value) if reflected else (self_value, other_value)
    if (left is None) or (right is None):
        _check_unknown_operation(context=context, method=method, left=left, right=right)
        return default
    return _check_binary_operation(
        context=context, method=method, left=left, right=right
    )


def binary_function_hook(context: FunctionContext, method: str) -> Type:
    """
    `pow(VariableX, object) -> Any`
    -->
    `pow(VariableX, float) -> float`
    `operator.add(float, VariableY) -> VectorFloat`
    `operator.mul(VariableX, VariableY) -> VectorFloat`
    ...
    """
    default = context.default_return_type
    arg_types = context.arg_types
    if (
        (len(arg_types) < 2)
        or (len(arg_types[0]) != 1)
        or (len(arg_types[1]) != 1)
        or any(len(types) > 0 for types in arg_types[2:])
    ):
        return default
    left, right = arg_types[0][0], arg_types[1][0]
    if not (_may_refine(left, method) and _may_refine(right, _reflect(method, True))):
        return default
    left_value = _get_value_type(context, left)
    right_value = _get_value_type(context, right)
    if (left_value is left) and (right_value is right):
        return default  # no variable involved
    if (left_value is None) or (right_value is None):
        _check_unknown_operation(
            context=context, method=method, left=left_value, right=right_value
        )
        return _get_plain_any(default)
    if not isinstance(context.api, TypeChecker):
        return _get_plain_any(default)
    return _check_binary_operation(
        context=context, method=method, left=left_value, right=right_value
    )


def inplace_operator_hook(context: MethodContext, method: str) -> Type:
    """
    `VariableX.__iadd__(object) -> VariableX`
    -->
    `VariableX.__iadd__(float) -> VariableX`
    `VariableX.__iadd__(str) -> error`
    `VariableY.__iadd__(float) -> error`  (if the result does not fit, e.g. `int`)
    ...
    """
    result = binary_operator_hook(context=context, method=method, reflected=False)
    _check_inplace_result(context=context, var_type=context.type, result=result)
    return context.default_return_type


def inplace_function_hook(context: FunctionContext, method: str) -> Type:
    """
    `operator.iadd(VariableX, object) -> Any`
    -->
    `operator.iadd(VariableX, float) -> VariableX`
    `operator.iadd(VariableX, str) -> error`
    `operator.iadd(VariableY, float) -> error`  (if the result does not fit)
    `operator.iadd(float, VariableX) -> float`  (falls back to `float + VariableX`)
    ...
    """
    if (
        (len(context.arg_types) > 0)
        and (len(context.arg_types[0]) == 1)
        and not _may_refine(context.arg_types[0][0], f"__i{method[2:]}")
    ):
        return context.default_return_type
    result = binary_function_hook(context=context, method=method)
    if (
        (len(context.arg_types) > 0)
        and (len(context.arg_types[0]) == 1)
        and isinstance(var_inst := get_proper_type(context.arg_types[0][0]), Instance)
        and var_inst.type.has_base("hydpy.core.variabletools.Variable")
    ):
        _check_inplace_result(context=context, var_type=var_inst, result=result)
        return var_inst
    return result


def _check_inplace_result(
    context: FunctionContext | MethodContext, var_type: Type, result: Type
) -> None:
    """Report an error if the given variable type cannot accept the given result type
    of an in-place operation."""
    if (
        isinstance(api := context.api, TypeChecker)
        and not isinstance(get_proper_type(result), AnyType)
        and isinstance(var_inst := get_proper_type(var_type), Instance)
        and ((ndim_type := _get_inherited_ndim_and_type(var_inst.type)) is not None)
        and (
            (
                target := _get_vectorlike(
                    context=context, ndim=ndim_type[0], type_=ndim_type[1], input_=True
                )
            )
            is not None
        )
    ):
        api.check_subtype(
            subtype=result,
            supertype=target,
            context=context.context,
            msg=ErrorMessage(
                "Incompatible result of in-place operation", code=ASSIGNMENT
            ),
            subtype_label="result",
            supertype_label="variable accepts",
        )


def _apply_unary_operator(
    context: FunctionContext | MethodContext,
    var_type: Type,
    method: str,
    args: Sequence[Type] = (),
) -> Type:
    default = _get_plain_any(context.default_return_type)
    if (
        not isinstance(api := context.api, TypeChecker)
        or not isinstance(var_inst := get_proper_type(var_type), Instance)
        or ((ndim_type := _get_inherited_ndim_and_type(var_inst.type)) is None)
        or ((self_value := _get_value_type(context, var_inst)) is None)
    ):
        return default
    if method in ("__floor__", "__ceil__", "__trunc__"):
        result = _get_vectorlike(
            context=context, ndim=ndim_type[0], type_=int, input_=False
        )
        return default if result is None else result
    if method == "__invert__":
        return _check_binary_operation(
            context=context,
            method="__truediv__",
            left=api.named_type("builtins.float"),
            right=self_value,
        )
    if (method == "__round__") and (ndim_type[0] > 0):
        # `Variable.__round__` preserves the type of multidimensional values
        return self_value
    # 0-dimensional variables behave like their values (with `__round__`, this
    # includes the distinction between passing `ndigits` or not):
    check = partial(
        api.expr_checker.check_method_call_by_name,
        method=method,
        base_type=self_value,
        args=[TempNode(arg, context=context.context) for arg in args],
        arg_kinds=[ARG_POS] * len(args),
        context=context.context,
    )
    if not args:
        return check()[0]
    # Mypy already checks `ndigits` against the signatures of `Variable.__round__`
    # and `builtins.round`, so we suppress duplicate errors:
    with api.msg.filter_errors() as watcher:
        result = check()[0]
    return default if watcher.has_new_errors() else result


def unary_operator_hook(context: MethodContext, method: str) -> Type:
    """
    `VariableX.__neg__() -> Any`
    -->
    `VariableX.__neg__() -> float`
    `VariableY.__neg__() -> VectorFloat`
    ...
    """
    args = context.arg_types[0] if context.arg_types else []
    return _apply_unary_operator(
        context=context, var_type=context.type, method=method, args=args
    )


def unary_function_hook(context: FunctionContext, method: str) -> Type:
    """
    `abs(VariableX) -> Any`
    -->
    `abs(VariableX) -> float`
    `abs(VariableY) -> VectorFloat`
    ...
    """
    if (
        (len(arg_types := context.arg_types) == 0)
        or (len(arg_types[0]) != 1)
        or not _may_refine(arg_types[0][0], method)
    ):
        return _get_plain_any(context.default_return_type)
    args = arg_types[1] if len(arg_types) > 1 else []
    return _apply_unary_operator(
        context=context, var_type=arg_types[0][0], method=method, args=args
    )


def getitem_hook(context: MethodContext) -> Type:
    """
    `VariableX.__getitem__(object) -> Any`
    -->
    `VariableX.__getitem__(int) -> float`
    `VariableY.__getitem__(slice) -> VectorFloat`
    ...
    """
    default = _get_plain_any(context.default_return_type)
    if (
        not isinstance(api := context.api, TypeChecker)
        or (len(context.arg_types) != 1)
        or (len(context.arg_types[0]) != 1)
        or ((ndim_type := _get_ndim_and_type(context)) is None)
        or ((self_value := _get_value_type(context, context.type)) is None)
    ):
        return default
    ndim, type_ = ndim_type
    if ndim == 0:
        return self_value
    key = context.arg_types[0][0]
    result = api.expr_checker.check_method_call_by_name(
        method="__getitem__",
        base_type=self_value,
        args=[TempNode(key, context=context.context)],
        arg_kinds=[ARG_POS],
        context=context.context,
    )[0]
    proper = get_proper_type(key)
    items = proper.items if isinstance(proper, TupleType) else [proper]
    names = [
        item.type.fullname if isinstance(item, Instance) else None
        for item in (get_proper_type(i) for i in items)
    ]
    if (len(names) <= ndim) and all(
        name in ("builtins.int", "builtins.slice") for name in names
    ):
        newdim = ndim - names.count("builtins.int")
        refined = _get_scalar_type(context=context, ndim=ndim, type_=type_)
        if newdim > 0:
            refined = _get_vectorlike(
                context=context, ndim=newdim, type_=type_, input_=False
            )
        if refined is not None:
            return refined
    return result


def setitem_hook(context: MethodContext) -> Type:
    """
    `VariableX.__setitem__(object, object) -> None`
    -->
    `VariableX.__setitem__(int, float) -> None`
    `VariableX.__setitem__(str, float) -> error`
    `VariableY.__setitem__(int, float) -> error`  (if the value does not fit)
    ...
    """
    if (
        not isinstance(api := context.api, TypeChecker)
        or (len(context.arg_types) != 2)
        or (len(context.arg_types[0]) != 1)
        or (len(context.arg_types[1]) != 1)
    ):
        return context.default_return_type
    key, value = context.arg_types[0][0], context.arg_types[1][0]
    value_expr = context.args[1][0]

    def _get_value(candidates: Type) -> Type:
        # `__setitem__` annotates `value` with `Any`, so mypy infers container
        # literals like `[x, y]` as `list[Any]`, which would let invalid items pass
        if isinstance(value_expr, LITERALS):
            return _match_literal(api, value_expr, candidates)[1]
        return value

    if ((ndim_type := _get_ndim_and_type(context)) is None) or (
        (self_value := _get_value_type(context, context.type)) is None
    ):
        # unknown dimensionality or value type: accept all numerical values
        if (
            (anylike := _get_any_vectorlike(context, input_=True)) is not None
        ) and not is_subtype(value := _get_value(anylike), anylike):
            api.fail(
                f"Incompatible value for item assignment (value "
                f"{format_type(value, api.options)}, variable accepts only numbers "
                f"and arrays or nested sequences of numbers)",
                context.context,
                code=ASSIGNMENT,
            )
        return context.default_return_type
    ndim, type_ = ndim_type
    if ndim == 0:
        api.check_subtype(
            subtype=key,
            supertype=UnionType(
                [api.named_type("builtins.int"), api.named_type("builtins.slice")]
            ),
            context=context.context,
            msg=ErrorMessage(
                "Invalid key for a 0-dimensional variable (only `0` and `:` are "
                "allowed)",
                code=INDEX,
            ),
        )
    else:
        api.expr_checker.check_method_call_by_name(
            method="__getitem__",
            base_type=self_value,
            args=[TempNode(key, context=context.context)],
            arg_kinds=[ARG_POS],
            context=context.context,
        )
    targets = [
        _get_vectorlike(context=context, ndim=n, type_=type_, input_=True)
        for n in range(ndim + 1)
    ]
    if all(target is not None for target in targets):
        supertype = UnionType.make_union([t for t in targets if t is not None])
        api.check_subtype(
            subtype=_get_value(supertype),
            supertype=supertype,
            context=context.context,
            msg=ErrorMessage("Incompatible value for item assignment", code=ASSIGNMENT),
            subtype_label="value",
            supertype_label="variable accepts",
        )
    return context.default_return_type


def _get_variable_args(context: FunctionContext) -> list[tuple[int, str]]:
    """Return the dimensionalities and names of all arguments of the given function
    call that are variables with known dimensionality."""
    infos = []
    for arg_types in context.arg_types:
        for arg_type in arg_types:
            if isinstance(var_inst := get_proper_type(arg_type), Instance) and (
                (ndim_type := _get_inherited_ndim_and_type(var_inst.type)) is not None
            ):
                infos.append((ndim_type[0], var_inst.type.name))
    return infos


def scalar_function_hook(context: FunctionContext, scalar: str) -> Type:
    """
    `float(VariableX) -> float`
    `float(VariableY) -> error`  (if `VariableY` is multidimensional)
    `math.exp(VariableX) -> float`
    `math.atan2(VariableX, VariableY) -> error`  (if `VariableY` is multidimensional)
    ...
    """
    for ndim, name in _get_variable_args(context):
        if ndim:
            context.api.fail(
                f'Variable "{name}" is {ndim}-dimensional and thus cannot be '
                f"converted to a scalar {scalar} value",
                context.context,
                code=ARG_TYPE,
            )
    return context.default_return_type


def _get_item_type(
    context: FunctionContext | MethodContext, ndim: int, type_: type[float]
) -> Type | None:
    """Return the type of the items yielded when iterating over a variable with the
    given (non-zero) dimensionality and value type."""
    if ndim == 1:
        return _get_scalar_type(context=context, ndim=ndim, type_=type_)
    return _get_vectorlike(context=context, ndim=ndim - 1, type_=type_, input_=False)


def _get_inherited_ndim_and_type(info: TypeInfo) -> tuple[int, type] | None:
    """Return the dimensionality and value type of the given variable class or, if
    unknown, of its nearest base class with known dimensionality and value type.

    Subclasses of concrete variable classes inherit the methods added by
    `variable_class_hook` and thus also need the related checks.
    """
    for base in info.mro:
        if (ndim_type := VAR_INFO.get(base.fullname)) is not None:
            return ndim_type
    return None


def iter_hook(context: MethodContext) -> Type:
    """
    `VariableX.__iter__() -> Iterator[Any]`
    -->
    `VariableX.__iter__() -> error`  (if `VariableX` is 0-dimensional)

    `iter_signature_hook` adds precise `__iter__` methods to all multidimensional
    variable classes, so that this hook only needs to handle 0-dimensional ones.
    """
    if (
        isinstance(var_inst := context.type, Instance)
        and ((ndim_type := _get_inherited_ndim_and_type(var_inst.type)) is not None)
        and (ndim_type[0] == 0)
    ):
        context.api.fail(
            f'Variable "{var_inst.type.name}" is 0-dimensional and thus not iterable',
            context.context,
            code=ATTR_DEFINED,
        )
    return context.default_return_type


def contains_hook(context: MethodContext) -> Type:
    """
    `VariableX.__contains__(object) -> bool`
    `VariableY.__contains__(object) -> error`  (if `VariableY` is 0-dimensional)

    For the `in` operator, Mypy suppresses this error and then falls back on checking
    iteration, so that `iter_hook` reports the 0-dimensional variable instead.
    """
    if (
        isinstance(var_inst := context.type, Instance)
        and ((ndim_type := _get_ndim_and_type(context)) is not None)
        and (ndim_type[0] == 0)
    ):
        context.api.fail(
            f'Variable "{var_inst.type.name}" is 0-dimensional and thus does not '
            f"support the `in` operator",
            context.context,
            code=OPERATOR,
        )
    return context.default_return_type


def _has_arrayhook_member(info: TypeInfo) -> bool:
    """Tell whether method `__array__` of the given class is annotated with `ArrayHook`
    where it is defined, which is the class itself or one of its base classes (or if
    the plugin added it to a base class already).

    Like `_has_generalhook_member`, `_has_arrayhook_member` returns `False` if a class
    overrides `__array__` with a more specific annotation, so that the plugin respects
    it.

    Mypy analyses method signatures only after applying base class hooks (see
    `array_hook`).  Hence, `_has_arrayhook_member` usually has to identify `ArrayHook`
    by the name used in the (still unanalysed) annotation.
    """
    if (definer := info.get_containing_type_info("__array__")) is None:
        return False
    sym = definer.names["__array__"]
    if sym.plugin_generated:
        return True
    node = sym.node
    if isinstance(node, Decorator):
        node = node.func
    if not isinstance(node, FuncDef) or not isinstance(node.type, CallableType):
        return False
    ret_type = node.type.ret_type
    if isinstance(ret_type, UnboundType):
        return ret_type.name.rpartition(".")[2] == "ArrayHook"
    return _is_alias(ret_type, "ArrayHook")


def _get_semanal_alias_target(
    api: SemanticAnalyzerPluginInterface, name: str
) -> Type | None:
    """Return the target of the type alias with the given name defined in module
    |typingtools| during semantic analysis.

    If the alias is not ready yet, `_get_semanal_alias_target` defers the analysis of
    the current target (as long as possible) and returns |None|.
    """
    alias = api.lookup_fully_qualified_or_none(f"hydpy.core.typingtools.{name}")
    if (
        (alias is not None)
        and isinstance(alias_node := alias.node, TypeAlias)
        and not has_placeholder(alias_node.target)
    ):
        return alias_node.target
    if not api.final_iteration:
        api.defer()
    return None


def _add_precise_method(
    api: SemanticAnalyzerPluginInterface,
    cls: ClassDef,
    name: str,
    args: list[Argument],
    return_type: Type,
) -> None:
    """Add a method with the given signature to the given class unless it already has
    an identical plugin-generated one."""
    sym = cls.info.names.get(name)
    if (
        (sym is not None)
        and sym.plugin_generated
        and isinstance(node := sym.node, FuncDef)
        and isinstance(node.type, CallableType)
        and is_same_type(node.type.ret_type, return_type)
    ):
        return
    method = add_method_to_class(
        api=api, cls=cls, name=name, args=args, return_type=return_type
    )
    if isinstance(method, FuncDef):
        method.is_trivial_body = True


def array_hook(context: ClassDefContext) -> None:
    """
    `VariableX.__array__() -> ArrayHook`
    -->
    `VariableX.__array__() -> ndarray[tuple[()], dtype[float64]]`  (0-dim., float)
    `VariableY.__array__() -> VectorInt`  (1-dimensional, int)
    ...

    In contrast to the other hooks, this one adds a method with a precise signature to
    each variable class with known dimensionality and value type during semantic
    analysis.  Otherwise, Mypy would rely on the general signature defined by
    `Variable` when checking if a variable fulfils numpy's array protocol (e.g. when
    passing it to `numpy.sum`).  Subclasses of these variable classes inherit the
    precise signature.
    """
    api, cls = context.api, context.cls
    if ((ndim_type := VAR_INFO.get(cls.info.fullname)) is None) or (
        not _has_arrayhook_member(cls.info)
    ):
        return
    ndim, type_ = ndim_type
    if (
        prefix := {0: "Vector", 1: "Vector", 2: "Matrix", 3: "Tensor"}.get(ndim)
    ) is None:
        return
    name = f"{prefix}{type_.__name__.capitalize()}"
    if (return_type := _get_semanal_alias_target(api, name)) is None:
        return
    dtype_inst = api.named_type_or_none("numpy.dtype", [AnyType(TypeOfAny.explicit)])
    if dtype_inst is None:
        if not api.final_iteration:
            api.defer()
        return
    if ndim == 0:
        if not isinstance(vector := get_proper_type(return_type), Instance):
            return
        empty_tuple = TupleType(
            [], fallback=api.named_type("builtins.tuple", [UninhabitedType()])
        )
        return_type = vector.copy_modified(args=[empty_tuple, vector.args[1]])
    dtype_type = UnionType([dtype_inst, NoneType()])
    copy_type = UnionType([api.named_type("builtins.bool"), NoneType()])
    _add_precise_method(
        api=api,
        cls=cls,
        name="__array__",
        args=[
            Argument(Var("dtype", dtype_type), dtype_type, None, ARG_OPT),
            Argument(Var("copy", copy_type), copy_type, None, ARG_OPT),
        ],
        return_type=return_type,
    )


def _has_iterhook_member(info: TypeInfo) -> bool:
    """Tell whether method `__iter__` of the given class is the general one annotated
    with `Iterator[GeneralHook]` or one added by `iter_signature_hook` where it is
    defined (the class itself or one of its base classes).

    Like `_has_arrayhook_member`, `_has_iterhook_member` returns `False` if a class
    overrides `__iter__` with a more specific annotation and must identify `GeneralHook`
    by name as long as Mypy has not analysed the annotation.
    """
    if (definer := info.get_containing_type_info("__iter__")) is None:
        return False
    sym = definer.names["__iter__"]
    if sym.plugin_generated:
        return True
    node = sym.node
    if isinstance(node, Decorator):
        node = node.func
    if not isinstance(node, FuncDef) or not isinstance(node.type, CallableType):
        return False
    ret_type = node.type.ret_type
    if isinstance(ret_type, UnboundType):
        return any(
            isinstance(arg, UnboundType)
            and (arg.name.rpartition(".")[2] == "GeneralHook")
            for arg in ret_type.args
        )
    return _refers_to_generalhook(node.type)


def iter_signature_hook(context: ClassDefContext) -> None:
    """
    `VariableX.__iter__() -> Iterator[GeneralHook]`
    -->
    `VariableX.__iter__() -> Iterator[GeneralHook]`  (if `VariableX` is 0-dimensional)
    `VariableY.__iter__() -> Iterator[numpy.float64]`  (if `VariableY` is 1-dimensional)
    `VariableZ.__iter__() -> Iterator[VectorFloat]`  (if `VariableZ` is 2-dimensional)
    ...

    Like `array_hook`, this hook adds a method with a precise signature to each
    multidimensional variable class with known value type during semantic analysis.
    Otherwise, Mypy would rely on the general signature defined by `Variable` when
    checking if a variable is an `Iterable[...]` of the expected type (e.g. in
    `x: list[str] = list(variable)`), which the other hooks cannot prevent.  For
    0-dimensional variables, `iter_hook` and `iterable_function_hook` report errors.
    """
    api, cls = context.api, context.cls
    if ((ndim_type := VAR_INFO.get(cls.info.fullname)) is None) or (
        not _has_iterhook_member(cls.info)
    ):
        return
    ndim, type_ = ndim_type
    if (prefix := {1: "Vector", 2: "Vector", 3: "Matrix"}.get(ndim)) is None:
        return
    name = f"{prefix}{type_.__name__.capitalize()}"
    if (item := _get_semanal_alias_target(api, name)) is None:
        return
    if ndim == 1:
        if not (
            isinstance(vector := get_proper_type(item), Instance)
            and isinstance(dtype := get_proper_type(vector.args[1]), Instance)
        ):
            return
        item = dtype.args[0]
    if (iterator := api.named_type_or_none("typing.Iterator", [item])) is None:
        if not api.final_iteration:
            api.defer()
        return
    _add_precise_method(
        api=api, cls=cls, name="__iter__", args=[], return_type=iterator
    )


def variable_class_hook(context: ClassDefContext) -> None:
    """Add methods with precise signatures to variable classes."""
    array_hook(context)
    iter_signature_hook(context)


def iterable_function_hook(
    context: FunctionContext, fullname: str, first_only: bool
) -> Type:
    """
    `list(VariableX) -> list[Any]`
    -->
    `list(VariableX) -> error`  (if `VariableX` is 0-dimensional)
    `min(VariableZ) -> error`  (if `VariableZ` is 2-dimensional and no key is given)
    `sum(VariableY) -> numpy.float64`  (if `VariableY` is 1-dimensional)
    `sum(VariableZ) -> VectorFloat`  (if `VariableZ` is 2-dimensional)
    `sum(VariableB) -> numpy.int64`  (if `VariableB` is 1-dimensional and boolean)
    ...

    For multidimensional variables, Mypy derives the result types of functions like
    `list` and `min` from the precise `__iter__` methods added by
    `iter_signature_hook`.  Only `sum` without a given start value needs refinement, as
    Mypy's stubs would add `Literal[0]` (the default start value) to the result type.
    """
    default = context.default_return_type
    nmb_positional = sum(
        kind == ARG_POS for kinds in context.arg_kinds for kind in kinds
    )
    if (fullname in SINGLE_ITERABLE_FUNCTIONS) and (nmb_positional != 1):
        return default
    infos: list[tuple[str, int, type[float]]] = []
    for arg_types in context.arg_types[:1] if first_only else context.arg_types:
        for arg_type in arg_types:
            if (
                isinstance(var_inst := get_proper_type(arg_type), Instance)
                and (
                    (ndim_type := _get_inherited_ndim_and_type(var_inst.type))
                    is not None
                )
                and _has_iterhook_member(var_inst.type)
            ):
                infos.append((var_inst.type.name, *ndim_type))
    keywords = {
        name: get_proper_type(type_)
        for names, types in zip(context.arg_names, context.arg_types)
        for name, type_ in zip(names, types)
        if name is not None
    }
    # `key=None` means comparing the items themselves:
    compares = (fullname in COMPARING_FUNCTIONS) and isinstance(
        keywords.get("key", NoneType()), NoneType
    )
    for name, ndim, _ in infos:
        if not ndim:
            context.api.fail(
                f'Variable "{name}" is 0-dimensional and thus not iterable',
                context.context,
                code=ARG_TYPE,
            )
        elif compares and (ndim > 1):
            context.api.fail(
                f'Variable "{name}" is {ndim}-dimensional and thus its items (arrays) '
                f"are not comparable",
                context.context,
                code=ARG_TYPE,
            )
    if (
        (fullname != "builtins.sum")
        or (len(infos) != 1)
        or (nmb_positional != 1)
        or ("start" in keywords)
        or ((ndim := infos[0][1]) == 0)
    ):
        return default
    # Without a given start value, `sum` starts with `0`, so summing booleans results
    # in integers:
    type_ = int if issubclass(infos[0][2], bool) else infos[0][2]
    item = _get_item_type(context=context, ndim=ndim, type_=type_)
    return default if item is None else item


def sized_function_hook(context: FunctionContext, fullname: str) -> Type:
    """
    `len(VariableX) -> int`
    `len(VariableY) -> error`  (if `VariableY` is 0-dimensional)
    """
    funcname = fullname.rpartition(".")[2]
    for ndim, name in _get_variable_args(context):
        if not ndim:
            context.api.fail(
                f'Variable "{name}" is 0-dimensional and thus does not support '
                f"`{funcname}`",
                context.context,
                code=ARG_TYPE,
            )
    return context.default_return_type


def _get_literal_key(context: MethodContext) -> str | None:
    """Return the value of the literal string given as the first argument of the given
    method call, if available."""
    if (len(context.arg_types) > 0) and (len(context.arg_types[0]) == 1):
        key_type = get_proper_type(context.arg_types[0][0])
        if isinstance(key_type, Instance) and (key_type.last_known_value is not None):
            key_type = key_type.last_known_value
        if isinstance(key_type, LiteralType) and isinstance(key_type.value, str):
            return key_type.value
    return None


def _get_model_instance(type_: Type) -> Instance | None:
    """Return the (upper bound of the) model type the given type refers to."""
    type_ = get_proper_type(type_)
    if isinstance(type_, TypeVarType):
        type_ = get_proper_type(type_.upper_bound)
    if isinstance(type_, Instance) and type_.type.has_base(
        "hydpy.core.modeltools.Model"
    ):
        return type_
    return None


def _get_model_map(
    model_inst: Instance,
) -> tuple[str, dict[str, dict[str, tuple[str, str]]]] | None:
    """Return the name and the variable map of the given model.

    For model classes without their own entry but defined in a base model module (for
    example, mixin classes), fall back to the corresponding base model.

    Note that the variable maps of base models also include the variables of all
    corresponding application models, so that the fallbacks cover, for example, solver
    parameters only used by some application models.
    """
    name = model_inst.type.fullname
    if (model_map := VAR_MAP_1.get(name)) is not None:
        return name, model_map
    if BASEMODEL_MODULE_FORMAT.fullmatch(module := model_inst.type.module_name):
        name = f"{module}.Model"
        if (model_map := VAR_MAP_1.get(name)) is not None:
            return name, model_map
    return None


def _is_own_model_expression(expr: Expression) -> bool:
    """Tell whether the given expression (presumably) refers to the model the current
    code belongs to: the names `model` (e.g. the first argument of the `__call__`
    methods of `Method` subclasses) and `self` or attributes named `model` (e.g.
    `self.subpars.pars.model`).

    The base model fallback (see `_get_basemodel_module`) only applies to such
    expressions, so that other model objects, for example, a main model passed to a
    submodel, remain unrefined.
    """
    if isinstance(expr, NameExpr):
        return expr.name in ("model", "self")
    return isinstance(expr, MemberExpr) and (expr.name == "model")


def _get_basemodel_module(
    api: CheckerPluginInterface, model_inst: Instance
) -> str | None:
    """If the given model type is one of the general model classes defined in module
    `modeltools` and referenced within a module of a base model package, return the name
    of the base model's module."""
    if (
        (model_inst.type.module_name == "hydpy.core.modeltools")
        and isinstance(api, TypeChecker)
        and (match := BASEMODEL_PACKAGE_FORMAT.fullmatch(api.tree.fullname))
    ):
        base = match.group(1)
        return f"hydpy.models.{base}.{base}_model"
    return None


def _get_basemodel_instance(
    api: CheckerPluginInterface, model_inst: Instance
) -> Instance | None:
    """Return the base model type `_get_basemodel_module` selects for the given model
    type, if available."""
    if (
        isinstance(api, TypeChecker)
        and ((module := _get_basemodel_module(api, model_inst)) is not None)
        and ((info := _get_typeinfo(api, f"{module}.Model")) is not None)
    ):
        return Instance(info, args=[])
    return None


def _get_submodel_instance(model_inst: Instance, attr_name: str) -> Instance | None:
    """Return the type of the submodel (interface) the given model handles via the
    attribute with the given name."""
    if match := SUBMODELS_FORMAT.fullmatch(attr_name):
        attr_name = match.group(1)
        descriptor = "hydpy.core.modeltools.SubmodelsProperty"
    else:
        descriptor = "hydpy.core.modeltools.SubmodelProperty"
    if (
        ((attr_sym := model_inst.type.get(attr_name)) is not None)
        and ((attr_type := attr_sym.type) is not None)
        and isinstance(attr_inst := get_proper_type(attr_type), Instance)
        and (attr_inst.type.fullname == descriptor)
        and (len(attr_inst.args) == 1)
    ):
        return _get_model_instance(attr_inst.args[0])
    return None


def _get_type_arg(context: MethodContext, position: int) -> Type | None:
    """Return the type argument at the given position of the generic instance whose
    method is called, if available."""
    if isinstance(inst := context.type, Instance) and (len(inst.args) > position):
        return inst.args[position]
    return None


def conditionsmodel_hook(context: MethodContext) -> Type:
    """
    `ConditionsModel[ModelX]["model.submodely"] -> ConditionsSubmodel[Model]`
    -->
    `ConditionsModel[ModelX]["model.submodely"] -> ConditionsSubmodel[SubmodelY]`
    """
    default = context.default_return_type
    if (
        ((key := _get_literal_key(context)) is None)
        or ((model_type := _get_type_arg(context, 0)) is None)
        or ((model_inst := _get_model_instance(model_type)) is None)
        or not isinstance(default_inst := get_proper_type(default), Instance)
    ):
        return default
    names = key.split(".")
    if names[0] != "model":
        context.api.msg.report(
            msg=(
                f"Condition key `{key}` does not start with `model`, the name of the "
                f"main model."
            ),
            context=context.context,
            severity="error",
            code=ARG_TYPE,
            origin_context=None,
        )
        return default
    for name in names[1:]:
        if (submodel_inst := _get_submodel_instance(model_inst, name)) is None:
            return default
        model_inst = submodel_inst
    return default_inst.copy_modified(args=[model_inst])


def conditionssubmodel_hook(context: MethodContext) -> Type:
    """
    `ConditionsSubmodel[ModelX]["states"] -> ConditionsGroup[ModelX, str]`
    -->
    `ConditionsSubmodel[ModelX]["states"] -> ConditionsGroup[ModelX, Literal["states"]]`
    """
    default = context.default_return_type
    if (
        not isinstance(api := context.api, TypeChecker)
        or ((key := _get_literal_key(context)) is None)
        or ((model_type := _get_type_arg(context, 0)) is None)
        or not isinstance(default_inst := get_proper_type(default), Instance)
    ):
        return default
    if key not in CONDITION_GROUPS:
        context.api.msg.report(
            msg=(
                f"Condition group `{key}` does not exist (only `states` and `logs` are "
                f"supported)."
            ),
            context=context.context,
            severity="error",
            code=ARG_TYPE,
            origin_context=None,
        )
        return default
    group_type = LiteralType(value=key, fallback=api.named_type("builtins.str"))
    return default_inst.copy_modified(args=[model_type, group_type])


def _get_condition_type(context: MethodContext) -> Type | None:
    """Return the value type of the condition sequence selected by the literal key of
    the given `ConditionsGroup.__getitem__` or `ConditionsGroup.__setitem__` call.

    Return `None` if the type is not determinable.  Report an error and return an
    `AnyType` if the model does not handle the selected sequence.
    """
    if (
        ((key := _get_literal_key(context)) is None)
        or ((model_type := _get_type_arg(context, 0)) is None)
        or ((model_inst := _get_model_instance(model_type)) is None)
        or ((name_map := _get_model_map(model_inst)) is None)
        or ((group_type := _get_type_arg(context, 1)) is None)
        or not isinstance(group_literal := get_proper_type(group_type), LiteralType)
        or ((group := CONDITION_GROUPS.get(str(group_literal.value))) is None)
    ):
        return None
    model_name, model_map = name_map
    if (key in (seqs := model_map.get(group, {}))) and (
        (ndim_type := VAR_INFO.get(".".join(seqs[key]))) is not None
    ):
        return _get_vectorlike(
            context=context, ndim=ndim_type[0], type_=ndim_type[1], input_=False
        )
    context.api.msg.report(
        msg=(
            f"Model `{model_name}` has no "
            f"{str(group_literal.value).rstrip('s')} sequence `{key}`."
        ),
        context=context.context,
        severity="error",
        code=ARG_TYPE,
        origin_context=None,
    )
    return AnyType(type_of_any=TypeOfAny.from_error)


def conditionsgroup_getitem_hook(context: MethodContext) -> Type:
    """
    `ConditionsGroup[ModelX, Literal["states"]]["y"] -> float | NDArrayFloat`
    -->
    `ConditionsGroup[ModelX, Literal["states"]]["y"] -> float`
    """
    value_type = _get_condition_type(context)
    return context.default_return_type if value_type is None else value_type


def conditionsgroup_setitem_hook(context: MethodContext) -> Type:
    """
    `ConditionsGroup[ModelX, Literal["states"]]["y"] <- float | NDArrayFloat`
    -->
    `ConditionsGroup[ModelX, Literal["states"]]["y"] <- float`
    """
    default = context.default_return_type
    if (
        not isinstance(api := context.api, TypeChecker)
        or (len(context.arg_types) != 2)
        or (len(context.arg_types[1]) != 1)
        or ((target := _get_condition_type(context)) is None)
        or isinstance(get_proper_type(target), AnyType)
        or ((general := _get_alias_target(api, "ConditionValue")) is None)
    ):
        return default
    value = context.arg_types[1][0]
    # Mypy itself already reports cases where `not is_subtype(value, general)`:
    if is_subtype(value, general):
        api.check_subtype(
            subtype=value,
            supertype=target,
            context=context.context,
            msg=ErrorMessage("Incompatible value for condition assignment", ASSIGNMENT),
            subtype_label="value",
            supertype_label="condition sequence requires",
        )
    return default


def _get_variable_method_hook(name: str) -> Callable[[MethodContext], Type] | None:
    """Return the hook refining the variable method with the given name, if any."""
    if (binary := BINARY_OPERATORS.get(name)) is not None:
        return partial(binary_operator_hook, method=binary[0], reflected=binary[1])
    if (inplace := INPLACE_OPERATORS.get(name)) is not None:
        return partial(inplace_operator_hook, method=inplace)
    if name in UNARY_OPERATORS:
        return partial(unary_operator_hook, method=name)
    return {
        "__getitem__": getitem_hook,
        "__setitem__": setitem_hook,
        "__iter__": iter_hook,
        "__contains__": contains_hook,
    }.get(name)


METHOD_HOOKS: Final[dict[str, Callable[[MethodContext], Type]]] = {
    "hydpy.core.importtools.SubmodelAdder.__call__": submodeladder_call_hook,
    "hydpy.core.importtools.SubmodelAdder.__enter__": submodeladder_enter_hook,
    "hydpy.core.typingtools.ConditionsModel.__getitem__": conditionsmodel_hook,
    "hydpy.core.typingtools.ConditionsSubmodel.__getitem__": conditionssubmodel_hook,
    "hydpy.core.typingtools.ConditionsGroup.__getitem__": conditionsgroup_getitem_hook,
    "hydpy.core.typingtools.ConditionsGroup.__setitem__": conditionsgroup_setitem_hook,
}


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

    def report_config_data(  # pylint: disable=unused-argument
        self, ctx: ReportConfigContext
    ) -> str:
        """Report the hash of the plugin data so that Mypy invalidates its cache after
        regenerating the data."""
        return DATA_HASH

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        """Add all model main modules and variable modules the dependencies."""
        if any(file.fullname.startswith(s) for s in self.relevant_sources):
            return [(10, "hydpy.core.typingtools", -1)] + [
                (10, m, -1) for m in MODEL_MAP
            ]
        return []

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if (hook := METHOD_HOOKS.get(fullname)) is not None:
            return hook
        prefix, _, name = fullname.rpartition(".")
        if (
            ((hook := _get_variable_method_hook(name)) is not None)
            and ((info := self._get_variable_info(prefix)) is not None)
            and _has_generalhook_member(info, name)
        ):
            return hook
        return None

    def _get_variable_info(self, fullname: str) -> TypeInfo | None:
        """Return the type information of the (base or concrete) subclass of `Variable`
        identified by the given full name, if available."""
        if (
            ((symbol := self.lookup_fully_qualified(fullname)) is not None)
            and isinstance(info := symbol.node, TypeInfo)
            and info.has_base("hydpy.core.variabletools.Variable")
        ):
            return info
        return None

    def get_function_hook(
        self, fullname: str
    ) -> Callable[[FunctionContext], Type] | None:
        """Hooks for refining return types."""
        if fullname == "hydpy.core.importtools.prepare_model":
            return prepare_model_hook
        if (method := UNARY_FUNCTIONS.get(fullname)) is not None:
            return partial(unary_function_hook, method=method)
        if (method := BINARY_FUNCTIONS.get(fullname)) is not None:
            return partial(binary_function_hook, method=method)
        if (method := INPLACE_FUNCTIONS.get(fullname)) is not None:
            return partial(inplace_function_hook, method=method)
        if (scalar := SCALAR_FUNCTIONS.get(fullname)) is not None:
            return partial(scalar_function_hook, scalar=scalar)
        if fullname in SIZED_FUNCTIONS:
            return partial(sized_function_hook, fullname=fullname)
        if fullname in FIRST_ITERABLE_FUNCTIONS:
            return partial(iterable_function_hook, fullname=fullname, first_only=True)
        if fullname in SINGLE_ITERABLE_FUNCTIONS:
            return partial(iterable_function_hook, fullname=fullname, first_only=True)
        if fullname in ALL_ITERABLE_FUNCTIONS:
            return partial(iterable_function_hook, fullname=fullname, first_only=False)
        return None

    def get_base_class_hook(
        self, fullname: str
    ) -> Callable[[ClassDefContext], None] | None:
        if fullname.startswith("hydpy."):
            return variable_class_hook
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
        # pylint: disable=too-many-return-statements
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
        if fullname in FASTACCESS:
            return fastaccess_hook
        classname = fullname.rpartition(".")[0]
        if classname == "hydpy.core.variabletools.SubVariables":
            return variable_hook
        if classname == "hydpy.core.parametertools.ParameterSubset":
            return parametersubset_hook
        if classname == "hydpy.core.modeltools.Model":
            return method_hook
        if classname == "hydpy.core.variabletools.FastAccess":
            return fastaccess_member_hook
        return None


def plugin(version: str) -> type[MypyPlugin]:  # pylint: disable=unused-argument
    """Make the plugin directly available."""
    return MypyPlugin
