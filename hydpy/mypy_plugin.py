# pylint: disable=too-many-boolean-expressions
"""This module provides a Mypy plugin that infers more precise types and warns about
potential problems in situations where HydPy relies on runtime behaviour that is not
(and possibly cannot be) expressed via static type hints."""

from configparser import ConfigParser
from os.path import join, split
from pickle import load
from typing import Callable, Final
from warnings import warn

from mypy.checker import TypeChecker
from mypy.errorcodes import ARG_TYPE, ATTR_DEFINED
from mypy.nodes import Decorator, MemberExpr, MypyFile, TypeInfo
from mypy.options import Options
from mypy.plugin import AttributeContext, FunctionContext, Plugin
from mypy.typeops import bind_self
from mypy.types import (
    AnyType,
    CallableType,
    get_proper_type,
    LiteralType,
    Instance,
    Type,
    TypeOfAny,
)

VARS1 = set(
    ["hydpy.core.modeltools.Model.parameters", "hydpy.core.modeltools.Model.sequences"]
)
VARS2 = set(
    [
        "hydpy.core.variabletools.SubVariables.vars",
        "hydpy.core.parametertools.SubParameters.pars",
        "hydpy.core.sequencetools.SubSequences.seqs",
    ]
)
SUBVARS = set(
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

DIRPATH = split(__file__)[0]

MODEL_MAP: dict[str, dict[str, tuple[str, str]]]
VAR_MAP: dict[str, dict[str, dict[str, tuple[str, str]]]]
with open(join(DIRPATH, "conf", "mypy_plugin_data.pickle"), "rb") as file_:
    MODEL_MAP, VAR_MAP = load(file_)


def prepare_model_hook(context: FunctionContext) -> Type:
    """
    `prepare_model("modelx") -> Model`
    -->
    `prepare_model("modelx") -> ModelX`
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and (len(arg_types := context.arg_types) == 1)
        and (len(arg_types[0]) == 1)
        and isinstance(arg_type := get_proper_type(arg_types[0][0]), Instance)
        and isinstance(literal := arg_type.last_known_value, LiteralType)
    ):
        if (module_name := f"hydpy.models.{literal.value}") in MODEL_MAP:
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
        )
    return context.default_return_type


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
            method_info = module_type.names[method_name].node
            assert isinstance(method_info, TypeInfo)
            assert isinstance(dec_node := method_info.names["__call__"].node, Decorator)
            assert isinstance(
                call_type := get_proper_type(dec_node.var.type), CallableType
            )
            return bind_self(call_type, model_inst)
        context.api.msg.report(
            msg=f"Model `{model_inst.type.fullname}` has no method `{attr_name}`.",
            context=member_expr,
            severity="error",
            code=ATTR_DEFINED,
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
        return vars_inst.copy_modified(args=(model_inst,) + vars_inst.args[1:])
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


def subvariables_hook(context: AttributeContext) -> Type:
    """
    `Parameters[ModelX, ...].ControlParameters[T, ...]`
    -->
    `Parameters[ModelX, ...].ControlParameters[ModelX, ...]`
    """
    if isinstance(vars_inst := context.type, Instance) and isinstance(
        subvars_inst := get_proper_type(context.default_attr_type), Instance
    ):
        return subvars_inst.copy_modified(
            args=(vars_inst.args[0],) + subvars_inst.args[1:]
        )
    return context.default_attr_type


def variable_hook(context: AttributeContext) -> Type:
    """
    `ControlParameters[ModelX, ...].__getattr__("par") -> parametertools.Parameter`
    -->
    `ControlParameters[ModelX, ...].__getattr__("par") -> modelx.modelx_control.Par`
    """
    if (
        isinstance(api := context.api, TypeChecker)
        and isinstance(subvars_inst := context.type, Instance)
        and (len(args := subvars_inst.args) > 0)
        and isinstance(model_inst := get_proper_type(args[0]), Instance)
        and (model_map := VAR_MAP.get(model_inst.type.fullname))
        and (subvars_map := model_map.get(subvars_inst.type.fullname))
        and isinstance(member_expr := context.context, MemberExpr)
    ):
        if (attr_name := member_expr.name) in subvars_map:
            module_name, var_name = subvars_map[attr_name]
            if (module_type := api.modules.get(module_name)) is None:
                return context.default_attr_type
            var_info = module_type.names[var_name].node
            assert isinstance(var_info, TypeInfo)
            return Instance(typ=var_info, args=[])
        var_type = (
            subvars_inst.type.fullname.rpartition(".")[-1]
            .replace("Parameters", " parameter")
            .replace("Sequences", " sequence")
            .lower()
        )
        context.api.msg.report(
            msg=f"Model `{model_inst.type.fullname}` has no {var_type} `{attr_name}`.",
            context=member_expr,
            severity="error",
            code=ATTR_DEFINED,
        )
    return context.default_attr_type


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
            return [(10, m, -1) for m in MODEL_MAP]
        return []

    def get_function_hook(
        self, fullname: str
    ) -> Callable[[FunctionContext], Type] | None:
        """Hooks for refining return types."""
        if fullname == "hydpy.core.importtools.prepare_model":
            return prepare_model_hook
        return None

    def get_attribute_hook(
        self, fullname: str
    ) -> Callable[[AttributeContext], Type] | None:
        """Hooks for refining attribute types."""
        if fullname in VARS1:
            return variables_hook1
        if fullname in VARS2:
            return variables_hook2
        if fullname in SUBVARS:
            return subvariables_hook
        if fullname.rpartition(".")[0] == "hydpy.core.variabletools.SubVariables":
            return variable_hook
        if fullname.rpartition(".")[0] == "hydpy.core.modeltools.Model":
            return method_hook
        return None


def plugin(version: str) -> type[MypyPlugin]:  # pylint: disable=unused-argument
    """Make the plugin directly available."""
    return MypyPlugin
