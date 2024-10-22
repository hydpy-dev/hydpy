"""This module implements tools for increasing the level of automation and
standardisation of the online documentation generated with Sphinx."""

# import...
# ...from standard library
from __future__ import annotations
import abc
import builtins
import collections
import copy
import datetime
import doctest
import enum
import functools
import importlib
import inspect
import itertools
import io
import math
import mimetypes
import os
import platform
import pkgutil
import subprocess
import sys
import time
import types
import typing
import unittest
import warnings

# ...from site-packages
# import matplotlib    actual import below
import numpy
import typing_extensions

# import pandas    actual import below
# import scipy    actual import below
# ...from HydPy
import hydpy
from hydpy import auxs
from hydpy import core
from hydpy import cythons
from hydpy import exe
from hydpy import interfaces
from hydpy import models
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import typingtools
from hydpy.core.typingtools import *


if TYPE_CHECKING:
    from hydpy.cythons import annutils
    from hydpy.cythons import interputils
    from hydpy.cythons import ppolyutils
    from hydpy.cythons import pointerutils
    from hydpy.cythons import quadutils
    from hydpy.cythons import rootutils
    from hydpy.cythons import smoothutils
else:
    from hydpy.cythons.autogen import annutils
    from hydpy.cythons.autogen import interputils
    from hydpy.cythons.autogen import ppolyutils
    from hydpy.cythons.autogen import pointerutils
    from hydpy.cythons.autogen import quadutils
    from hydpy.cythons.autogen import rootutils
    from hydpy.cythons.autogen import smoothutils


class Priority(enum.Enum):
    """Priority level for members defined in different sources."""

    BUILTINS = 0
    """Priority level for members defined in |builtins|."""
    CORE = 1
    """Priority level for members defined in the `core` subpackage."""
    EXE = 2
    """Priority level for members defined in the `exe` subpackage."""
    AUXS = 3
    """Priority level for members defined in the `auxs` subpackage."""
    CYTHONS = 4
    """Priority level for members defined in the `cythons` subpackage."""
    MODELS = 5
    """Priority level for members defined in the `models` subpackage."""
    HYDPY = 6
    """Priority level for *HydPy* members not falling in the other categories."""
    ELSE = 7
    """Priority level for non-*HydPy* and non |builtins| members."""

    @classmethod
    def get_priority(cls, modulename: str) -> Priority:
        """Return the priority for the given module name.

        >>> from hydpy.core.autodoctools import Priority
        >>> assert Priority.get_priority("builtins") == Priority.BUILTINS
        >>> assert Priority.get_priority("hydpy.core.test") == Priority.CORE
        >>> assert Priority.get_priority("hydpy.exe.test") == Priority.EXE
        >>> assert Priority.get_priority("hydpy.auxs.test") == Priority.AUXS
        >>> assert Priority.get_priority("hydpy.cythons.test") == Priority.CYTHONS
        >>> assert Priority.get_priority("hydpy.models.test") == Priority.MODELS
        >>> assert Priority.get_priority("hydpy.test") == Priority.HYDPY
        >>> assert Priority.get_priority("numpy.test") == Priority.ELSE
        """
        if "builtin" in modulename:
            return BUILTINS
        if modulename.startswith("hydpy.core"):
            return CORE
        if modulename.startswith("hydpy.exe"):
            return EXE
        if modulename.startswith("hydpy.auxs"):
            return AUXS
        if modulename.startswith("hydpy.cythons"):
            return CYTHONS
        if modulename.startswith("hydpy.models"):
            return MODELS
        if modulename.startswith("hydpy"):
            return HYDPY
        return ELSE


BUILTINS = Priority.BUILTINS
CORE = Priority.CORE
EXE = Priority.EXE
AUXS = Priority.AUXS
CYTHONS = Priority.CYTHONS
MODELS = Priority.MODELS
HYDPY = Priority.HYDPY
ELSE = Priority.ELSE


excluded_members = {
    "CLASSES",
    "RUN_METHODS",
    "INTERFACE_METHODS",
    "ADD_METHODS",
    "INLET_METHODS",
    "OUTLET_METHODS",
    "RECEIVER_METHODS",
    "SENDER_METHODS",
    "PART_ODE_METHODS",
    "FULL_ODE_METHODS",
    "CONTROLPARAMETERS",
    "DERIVEDPARAMETERS",
    "FIXEDPARAMETERS",
    "REQUIREDSEQUENCES",
    "UPDATEDSEQUENCES",
    "RESULTSEQUENCES",
    "SOLVERPARAMETERS",
    "SOLVERSEQUENCES",
    "SUBMETHODS",
    "SUBMODELINTERFACES",
    "SUBMODELS",
    "fastaccess",
    "fastaccess_new",
    "fastaccess_old",
    "pars",
    "seqs",
    "subvars",
    "subpars",
    "subseqs",
}
excluded_members.update(typing.__all__)
excluded_members.update(typing_extensions.__all__)

_PAR_SPEC2CAPT = collections.OrderedDict(
    (
        ("parameters", "Parameter tools"),
        ("constants", "Constants"),
        ("control", "Control parameters"),
        ("derived", "Derived parameters"),
        ("fixed", "Fixed parameters"),
        ("solver", "Solver parameters"),
    )
)

_SEQ_SPEC2CAPT = collections.OrderedDict(
    (
        ("sequences", "Sequence tools"),
        ("inputs", "Input sequences"),
        ("factors", "Factor sequences"),
        ("fluxes", "Flux sequences"),
        ("states", "State sequences"),
        ("logs", "Log sequences"),
        ("inlets", "Inlet sequences"),
        ("outlets", "Outlet sequences"),
        ("receivers", "Receiver sequences"),
        ("senders", "Sender sequences"),
        ("aides", "Aide sequences"),
    )
)

_AUX_SPEC2CAPT = collections.OrderedDict((("masks", "Masks"),))

_all_spec2capt = _PAR_SPEC2CAPT.copy()
_all_spec2capt.update(_SEQ_SPEC2CAPT)
_all_spec2capt.update(_AUX_SPEC2CAPT)


def _add_title(title: str, marker: str) -> list[str]:
    """Return a title for a basemodels docstring."""
    return ["", title, marker * len(title)]


def _add_lines(specification: str, module: types.ModuleType) -> list[str]:
    """Return autodoc commands for a basemodels docstring.

    Note that `collection classes` (e.g. `Model`, `ControlParameters`, `InputSequences`
    are placed on top of the respective section and the `contained classes` (e.g. model
    methods, `ControlParameter` instances, `InputSequence` instances at the bottom.
    This differs from the order of their definition in the respective modules, but
    results in a better documentation structure.
    """
    caption = _all_spec2capt.get(specification, "dummy")
    if caption.split()[-1] in ("parameters", "sequences", "Masks"):
        name_collectionclass = caption.title().replace(" ", "")
    else:
        name_collectionclass = None
    lines = []
    exc_mem = ", ".join(excluded_members)
    if specification == "model":
        lines += [
            "",
            f".. autoclass:: {module.__name__}.Model",
            "    :members:",
            "    :show-inheritance:",
            f"    :exclude-members: {exc_mem}",
        ]
    elif name_collectionclass is not None:
        lines += [
            "",
            f'.. autoclass:: {module.__name__.rpartition(".")[0]}'
            f".{name_collectionclass}",
            "    :members:",
            "    :noindex:",
            "    :show-inheritance:",
            f"    :exclude-members: {exc_mem}",
        ]
    lines += [
        "",
        ".. automodule:: " + module.__name__,
        "    :members:",
        "    :show-inheritance:",
    ]
    if specification == "model":
        lines += [f"    :exclude-members: Model, {exc_mem}"]
    elif name_collectionclass is None:
        lines += [f"    :exclude-members: {exc_mem}"]
    else:
        lines += [f"    :exclude-members:  {name_collectionclass}, {exc_mem}"]
    return lines


def autodoc_basemodel(module: types.ModuleType) -> None:
    """Add an exhaustive docstring to the given module of a basemodel.

    Works onlye when all modules of the basemodel are named in the standard way, e.g.
    `lland_model`, `lland_control`, `lland_inputs`.
    """
    autodoc_tuple2doc(module)
    namespace = module.__dict__
    moduledoc = namespace.get("__doc__")
    assert isinstance(moduledoc, str)
    basemodulename = namespace["__name__"].split(".")[-1]
    modules = {
        key: value
        for key, value in namespace.items()
        if (
            isinstance(value, types.ModuleType) and key.startswith(basemodulename + "_")
        )
    }
    substituter = Substituter(hydpy.substituter)
    lines = []
    specification = "model"
    modulename = f"{basemodulename}_{specification}"
    methods: tuple[type[modeltools.Method], ...] = ()
    if modulename in modules:
        module = modules[modulename]
        lines += _add_title("Method Features", "-")
        lines += _add_lines(specification, module)
        substituter.add_module(module)
        model = module.Model
        assert issubclass(model, modeltools.Model)
        methods = tuple(model.get_methods())
    _extend_methoddocstrings(module)
    _gain_and_insert_additional_information_into_docstrings(module, methods)
    for title, spec2capt in (
        ("Parameter Features", _PAR_SPEC2CAPT),
        ("Sequence Features", _SEQ_SPEC2CAPT),
        ("Auxiliary Features", _AUX_SPEC2CAPT),
    ):
        found_module = False
        new_lines = _add_title(title, "-")
        for specification, caption in spec2capt.items():
            modulename = f"{basemodulename}_{specification}"
            if modulename in modules:
                module = modules[modulename]
                found_module = True
                new_lines += _add_title(caption, ".")
                new_lines += _add_lines(specification, module)
                substituter.add_module(module)
                _gain_and_insert_additional_information_into_docstrings(module, methods)
        if found_module:
            lines += new_lines
    moduledoc += "\n".join(lines)
    namespace["__doc__"] = moduledoc
    basemodule = importlib.import_module(namespace["__name__"])
    substituter.add_module(basemodule)
    insert_docname_substitutions(
        module=modules[f"{basemodulename}_model"],
        name=basemodulename,
        substituter=substituter,
    )
    substituter.update_masters()
    namespace["substituter"] = substituter


def _insert_links_into_docstring(target: object, insertion: str) -> None:
    try:
        target.__doc__ += ""  # type: ignore[operator]
    except BaseException:
        return
    doc = getattr(target, "__doc__", None)
    if doc is not None:
        position = target.__doc__.find("\n\n")
        if position == -1:
            target.__doc__ = "\n\n".join([doc, insertion])
        else:
            position += 2
            target.__doc__ = "".join([doc[:position], insertion, doc[position:]])
    return


def _extend_methoddocstrings(module: types.ModuleType) -> None:
    model = module.Model
    assert issubclass(model, modeltools.Model)
    for method in model.get_methods():
        _insert_links_into_docstring(
            method, "\n".join(_get_methoddocstringinsertions(method))
        )


def _get_ending(container: Sized) -> str:
    return "s" if len(container) > 1 else ""


def _get_methoddocstringinsertions(method: modeltools.Method) -> list[str]:
    insertions = []
    submethods = getattr(method, "SUBMETHODS", ())
    if submethods:
        insertions.append(f"    Required submethod{_get_ending(submethods)}:")
        for submethod in submethods:
            insertions.append(
                f"      :class:`~{submethod.__module__}." f"{submethod.__name__}`"
            )
        insertions.append("")
    for pargroup in ("control", "derived", "fixed", "solver"):
        pars = getattr(method, f"{pargroup.upper()}PARAMETERS", ())
        if pars:
            insertions.append(
                f"    Requires the {pargroup} parameter{_get_ending(pars)}:"
            )
            for par in pars:
                insertions.append(f"      :class:`~{par.__module__}.{par.__name__}`")
            insertions.append("")
    for statement, tuplename in (
        ("Requires the", "REQUIREDSEQUENCES"),
        ("Updates the", "UPDATEDSEQUENCES"),
        ("Calculates the", "RESULTSEQUENCES"),
    ):
        for seqtype in (
            sequencetools.InletSequence,
            sequencetools.ReceiverSequence,
            sequencetools.InputSequence,
            sequencetools.FactorSequence,
            sequencetools.FluxSequence,
            sequencetools.StateSequence,
            sequencetools.LogSequence,
            sequencetools.AideSequence,
            sequencetools.OutletSequence,
            sequencetools.SenderSequence,
        ):
            seqs = [
                seq
                for seq in getattr(method, tuplename, ())
                if issubclass(seq, seqtype)
            ]
            if seqs:
                insertions.append(
                    f"    {statement} "
                    f"{seqtype.__name__[:-8].lower()} "
                    f"sequence{_get_ending(seqs)}:"
                )
                for seq in seqs:
                    insertions.append(
                        f"      :class:`~{seq.__module__}.{seq.__name__}`"
                    )
                insertions.append("")
    if insertions:
        insertions.append("")
    return insertions


def _gain_and_insert_additional_information_into_docstrings(
    module: types.ModuleType, allmethods: tuple[type[modeltools.Method], ...]
) -> None:
    for value in vars(module).values():
        insertions = []
        for role, description in (
            ("SUBMETHODS", "Required"),
            ("CONTROLPARAMETERS", "Required"),
            ("DERIVEDPARAMETERS", "Required"),
            ("FIXEDPARAMETERS", "Required"),
            ("SOLVERPARAMETERS", "Required"),
            ("RESULTSEQUENCES", "Calculated"),
            ("UPDATEDSEQUENCES", "Updated"),
            ("REQUIREDSEQUENCES", "Required"),
        ):
            relevantmethods = set()
            for method in allmethods:
                if value in getattr(method, role, ()):
                    relevantmethods.add(method)
            if relevantmethods:
                subinsertions = []
                for method in relevantmethods:
                    subinsertions.append(
                        f"      :class:`~{method.__module__}." f"{method.__name__}`"
                    )
                insertions.append(
                    f"    {description} by the " f"method{_get_ending(subinsertions)}:"
                )
                insertions.extend(sorted(subinsertions))
                insertions.append("\n")

        _insert_links_into_docstring(value, "\n".join(insertions))


def autodoc_applicationmodel(module: types.ModuleType) -> None:
    """Improves the docstrings of application models.

    |autodoc_applicationmodel| requires, similar to |autodoc_basemodel|, that both the
    application model and its base model are defined in the conventional way.
    """
    autodoc_tuple2doc(module)
    path_applicationmodel = module.__name__
    path_basemodel = path_applicationmodel.split("_")[0]
    module_basemodel = importlib.import_module(path_basemodel)
    substituter = Substituter(module_basemodel.substituter)
    substituter.add_module(module)
    insert_docname_substitutions(
        module=module,
        name=path_applicationmodel.split(".")[-1],
        substituter=substituter,
    )
    substituter.update_masters()
    module.substituter = substituter  # type: ignore[attr-defined]


def insert_docname_substitutions(
    module: types.ModuleType, name: str, substituter: Substituter
) -> None:
    r"""Insert model-specific substitutions based on the definitions provided by the
    available |DocName| member.

    >>> from hydpy.core.autodoctools import insert_docname_substitutions, Substituter
    >>> from hydpy.models import wland_wag
    >>> substituter = Substituter()
    >>> insert_docname_substitutions(wland_wag, "wland_wag", substituter)
    >>> for command in substituter.get_commands().split("\n"):
    ...     print(command)  # doctest: +ELLIPSIS
    .. |wland_wag.DOCNAME.complete| replace:: HydPy-W-Wag (extended version ...
    .. |wland_wag.DOCNAME.description| replace:: extended version ...
    .. |wland_wag.DOCNAME.family| replace:: HydPy-W
    .. |wland_wag.DOCNAME.long| replace:: HydPy-W-Wag
    .. |wland_wag.DOCNAME.short| replace:: W-Wag
    .. |wland_wag.Model.DOCNAME.complete| replace:: HydPy-W-Wag (extended version ...
    .. |wland_wag.Model.DOCNAME.description| replace:: extended version ...
    .. |wland_wag.Model.DOCNAME.family| replace:: HydPy-W
    .. |wland_wag.Model.DOCNAME.long| replace:: HydPy-W-Wag
    .. |wland_wag.Model.DOCNAME.short| replace:: W-Wag

    >>> from hydpy.models.wland import wland_model
    >>> substituter = Substituter()
    >>> insert_docname_substitutions(wland_model, "wland", substituter)
    >>> for command in substituter.get_commands().split("\n"):
    ...     print(command)   # doctest: +ELLIPSIS
    .. |wland.DOCNAME.complete| replace:: HydPy-W (base model)
    .. |wland.DOCNAME.description| replace:: base model
    .. |wland.DOCNAME.family| replace:: HydPy-W
    .. |wland.DOCNAME.long| replace:: HydPy-W
    .. |wland.DOCNAME.short| replace:: W
    .. |wland.Model.DOCNAME.complete| replace:: HydPy-W (base model)
    .. |wland.Model.DOCNAME.description| replace:: base model
    .. |wland.Model.DOCNAME.family| replace:: HydPy-W
    .. |wland.Model.DOCNAME.long| replace:: HydPy-W
    .. |wland.Model.DOCNAME.short| replace:: W
    """
    docname = module.Model.DOCNAME
    for member in dir(docname):
        if not (member.startswith("_") or hasattr(tuple, member)):
            substituter.add_substitution(
                short=f"|{name}.DOCNAME.{member}|",
                medium=f"|{name}.Model.DOCNAME.{member}|",
                long=getattr(docname, member),
                module=module,
            )


class Substituter:
    """Implements a HydPy specific docstring substitution mechanism."""

    master: Optional[Substituter]
    slaves: list[Substituter]
    short2long: dict[str, str]
    short2priority: dict[str, Priority]
    medium2long: dict[str, str]

    def __init__(self, master: Optional[Substituter] = None) -> None:
        self.master = master
        self.slaves = []
        if master:
            master.slaves.append(self)
            self.short2long = copy.deepcopy(master.short2long)
            self.short2priority = copy.deepcopy(master.short2priority)
            self.medium2long = copy.deepcopy(master.medium2long)
        else:
            self.short2long = {}
            self.short2priority = {}
            self.medium2long = {}

    @staticmethod
    def consider_member(
        name_member: str,
        member: Any,
        module: types.ModuleType,
        class_: Optional[type[object]] = None,
        ignore: Optional[dict[str, object]] = None,
    ) -> bool:
        """Return |True| if the given member should be added to the substitutions.  If
        not, return |False|.

        Some examples based on the site-package |numpy|:

        >>> from hydpy.core.autodoctools import Substituter
        >>> import numpy

        A constant like |numpy.nan| should be added:

        >>> Substituter.consider_member("nan", numpy.nan, numpy)
        True

        Members with a prefixed underscore should not be added:

        >>> Substituter.consider_member("_NoValue", numpy._NoValue, numpy)
        False

        Members that are actually imported modules should not be added:

        >>> Substituter.consider_member("random", numpy.random, numpy)
        False

        Members that are actually defined in other modules should not be added:

        >>> numpy.Substituter = Substituter
        >>> Substituter.consider_member("Substituter", numpy.Substituter, numpy)
        False
        >>> del numpy.Substituter

        Members that are defined in submodules of a given package (either from the
        standard library or from site-packages) should be added...

        >>> Substituter.consider_member("clip", numpy.clip, numpy)
        True

        ...but not members defined in *HydPy* submodules:

        >>> import hydpy
        >>> Substituter.consider_member("Node", hydpy.Node, hydpy)
        False

        Module |typingtools| is unique, as it is the only one for which
        |Substituter.consider_member| returns |True| all explicitly exported type
        aliases:

        >>> from hydpy.core import sequencetools, typingtools
        >>> Substituter.consider_member(
        ...     "NDArrayFloat", typingtools.NDArrayFloat, typingtools)
        True

        >>> Substituter.consider_member(
        ...     "NDArrayFloat", typingtools.NDArrayFloat, sequencetools)
        False

        For descriptor instances (with method `__get__`) being members of classes
        should be added:

        >>> from hydpy.auxs import anntools
        >>> Substituter.consider_member(
        ...     "shape_neurons", anntools.ANN.shape_neurons, anntools, anntools.ANN)
        True

        You can decide to ignore certain members:

        >>> Substituter.consider_member(
        ...     "shape_neurons", anntools.ANN.shape_neurons, anntools, anntools.ANN,
        ...     {"test": 1.0})
        True
        >>> Substituter.consider_member(
        ...     "shape_neurons", anntools.ANN.shape_neurons, anntools, anntools.ANN,
        ...     {"shape_neurons": anntools.ANN.shape_neurons})
        False
        """
        if ignore and (name_member in ignore):
            return False
        if name_member.startswith("_"):
            return False
        if inspect.ismodule(member):
            return False
        real_module = getattr(member, "__module__", None)
        if (module is not typing) and (name_member in typing.__all__):
            return False
        if (module is typingtools) and (name_member in typingtools.__all__):
            return True
        if not real_module:
            return True
        if real_module != module.__name__:
            if class_ and hasattr(member, "__get__"):
                return True
            if "hydpy" in real_module:
                return False
            if module.__name__ not in real_module:
                return False
        return True

    @staticmethod
    def get_role(member: object, cython: bool = False) -> str:
        """Return the reStructuredText role `func`, `class`, or `const` best describing
        the given member.

        Some examples based on the site-package |numpy|.  |numpy.clip| is a function:

        >>> from hydpy.core.autodoctools import Substituter
        >>> import numpy
        >>> Substituter.get_role(numpy.clip)
        'func'

        |numpy.ndarray| is a class:

        >>> Substituter.get_role(numpy.ndarray)
        'class'

        |numpy.ndarray.clip| is a method, for which also the `function` role is
        returned:

        >>> Substituter.get_role(numpy.ndarray.clip)
        'func'

        For everything else the `constant` role is returned:

        >>> Substituter.get_role(numpy.nan)
        'const'

        When analysing cython extension modules, set the option `cython` flag to |True|.
        |Double| is correctly identified as a class:

        >>> from hydpy.cythons import pointerutils
        >>> Substituter.get_role(pointerutils.Double, cython=True)
        'class'

        Only with the `cython` flag beeing |True|, for everything else the `function`
        text role is returned (doesn't make sense here, but the |numpy| module is not
        something defined in module |pointerutils| anyway):

        >>> Substituter.get_role(pointerutils.numpy, cython=True)
        'func'
        """
        if inspect.isroutine(member) or isinstance(member, numpy.ufunc):
            return "func"
        if inspect.isclass(member):
            return "class"
        if cython:
            return "func"
        return "const"

    def add_substitution(
        self, short: str, medium: str, long: str, module: types.ModuleType
    ) -> None:
        """Add the given substitutions both as a `short2long` and a `medium2long`
        mapping.

        Assume `variable1`, `variable2`, and  `variable3` are defined in the *HydPy*
        module `module1` of subpackage `exe` and the short and medium descriptions are
        `var1` and `mod1.var1` and so on:

        >>> import types
        >>> module1 = types.ModuleType("hydpy.exe.module1")
        >>> from hydpy.core.autodoctools import Substituter
        >>> substituter = Substituter()
        >>> substituter.add_substitution(
        ...     "var1", "mod1.var1", "hydpy.exe.module1.variable1", module1)
        >>> substituter.add_substitution(
        ...     "var2", "mod1.var2", "hydpy.exe.module1.variable2", module1)
        >>> substituter.add_substitution(
        ...     "var3", "mod1.var3", "hydpy.exe.module1.variable3", module1)
        >>> print(substituter.get_commands())
        .. var1 replace:: hydpy.exe.module1.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. var3 replace:: hydpy.exe.module1.variable3
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3

        If we add an object with the same, the updating of |Substituter.short2long|
        depends on its priority.  Builtins have the highest priority.  Objects defined
        in the `core`, `exe`, `auxs`, `cythons`, and `models` subpackages have the
        priorities two to six.  All other objects (incuding those of other
        site-packages) have the lowest priority.  If we add `variable1`, said to be
        defined in the `core` subpackage (higher priority than the `exe` subpackage),
        the new short substitution replaces the old one:

        >>> module2 = types.ModuleType("hydpy.core.module2")
        >>> substituter.add_substitution(
        ...     "var1", "mod2.var1", "hydpy.core.module2.variable1", module2)
        >>> print(substituter.get_commands())
        .. var1 replace:: hydpy.core.module2.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. var3 replace:: hydpy.exe.module1.variable3
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3
        .. mod2.var1 replace:: hydpy.core.module2.variable1

        If we add `variable2`, said to be defined in the `auxs` subpackage (lower
        priority than the `exe` subpackage), the old short substitution does not change:

        >>> module3 = types.ModuleType("hydpy.auxs.module3")
        >>> substituter.add_substitution(
        ...     "var2", "mod3.var2", "hydpy.auxs.module3.variable2", module3)
        >>> print(substituter.get_commands())
        .. var1 replace:: hydpy.core.module2.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. var3 replace:: hydpy.exe.module1.variable3
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3
        .. mod2.var1 replace:: hydpy.core.module2.variable1
        .. mod3.var2 replace:: hydpy.auxs.module3.variable2

        If we add `variable3`, said to be also defined in the `exe` subpackage, the
        short substitution is removed to avoid ambiguity:

        >>> module4 = types.ModuleType("hydpy.exe.module4")
        >>> substituter.add_substitution(
        ...     "var3", "mod4.var3", "hydpy.exe.module4.variable3", module4)
        >>> print(substituter.get_commands())
        .. var1 replace:: hydpy.core.module2.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3
        .. mod2.var1 replace:: hydpy.core.module2.variable1
        .. mod3.var2 replace:: hydpy.auxs.module3.variable2
        .. mod4.var3 replace:: hydpy.exe.module4.variable3

        Adding `variable3` of `module1` accidentally again does not result in any
        undesired side-effects:

        >>> substituter.add_substitution(
        ...     "var3", "mod1.var3", "hydpy.exe.module1.variable3", module1)
        >>> print(substituter.get_commands())
        .. var1 replace:: hydpy.core.module2.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3
        .. mod2.var1 replace:: hydpy.core.module2.variable1
        .. mod3.var2 replace:: hydpy.auxs.module3.variable2
        .. mod4.var3 replace:: hydpy.exe.module4.variable3

        In order to reduce the risk of name conflicts, only the `medium2long` mapping
        is supported for modules not part of the *HydPy* package:

        >>> module5 = types.ModuleType("external")
        >>> substituter.add_substitution(
        ...     "var4", "mod5.var4", "external.variable4", module5)
        >>> print(substituter.get_commands())
        .. var1 replace:: hydpy.core.module2.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3
        .. mod2.var1 replace:: hydpy.core.module2.variable1
        .. mod3.var2 replace:: hydpy.auxs.module3.variable2
        .. mod4.var3 replace:: hydpy.exe.module4.variable3
        .. mod5.var4 replace:: external.variable4

        The only exception to this rule is |builtins|, for which only the
        |Substituter.short2long| mapping is supported (note also, that the module name
        `builtins` is removed from string `long`):

        >>> import builtins
        >>> substituter.add_substitution(
        ...     "str", "blt.str", ":func:`~builtins.str`", builtins)
        >>> print(substituter.get_commands())
        .. str replace:: :func:`str`
        .. var1 replace:: hydpy.core.module2.variable1
        .. var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var1 replace:: hydpy.exe.module1.variable1
        .. mod1.var2 replace:: hydpy.exe.module1.variable2
        .. mod1.var3 replace:: hydpy.exe.module1.variable3
        .. mod2.var1 replace:: hydpy.core.module2.variable1
        .. mod3.var2 replace:: hydpy.auxs.module3.variable2
        .. mod4.var3 replace:: hydpy.exe.module4.variable3
        .. mod5.var4 replace:: external.variable4
        """
        name = module.__name__
        priority = Priority.get_priority(name)
        if priority == BUILTINS:
            self.short2long[short] = long.split("~")[0] + long.split(".")[-1]
            self.short2priority[short] = priority
        else:
            self.medium2long[medium] = long
            if priority != ELSE:
                if priority.value < self.short2priority.get(short, ELSE).value:
                    self.short2long[short] = long
                    self.short2priority[short] = priority
                elif priority == self.short2priority[short]:
                    self.short2long.pop(short, None)

    def add_module(self, module: types.ModuleType, cython: bool = False) -> None:
        """Add the given module, its members, and their submembers.

        The first examples are based on the site-package |numpy|: which is passed to
        method |Substituter.add_module|:

        >>> from hydpy.core.autodoctools import Substituter
        >>> substituter = Substituter()
        >>> import numpy
        >>> substituter.add_module(numpy)

        First, the module itself is added:

        >>> substituter.find("|numpy|")
        |numpy| :mod:`~numpy`

        Second, constants like |numpy.nan| are added:

        >>> substituter.find("|numpy.nan|")
        |numpy.nan| :const:`~numpy.nan`

        Third, functions like |numpy.clip| are added:

        >>> substituter.find("|numpy.clip|")
        |numpy.clip| :func:`~numpy.clip`

        Fourth, clases line |numpy.ndarray| are added:

        >>> substituter.find("|numpy.ndarray|")
        |numpy.ndarray| :class:`~numpy.ndarray`

        Method |Substituter.add_module| also searches for available annotations:

        >>> from hydpy.core import timetools
        >>> substituter.add_module(timetools)
        >>> substituter.find("Timegrids.init")
        |Timegrids.initindices| :const:`~hydpy.core.timetools.Timegrids.initindices`
        |Timegrids.init| :attr:`~hydpy.core.timetools.Timegrids.init`
        |timetools.Timegrids.initindices| \
:const:`~hydpy.core.timetools.Timegrids.initindices`
        |timetools.Timegrids.init| :attr:`~hydpy.core.timetools.Timegrids.init`

        >>> from hydpy.auxs import calibtools
        >>> substituter.add_module(calibtools)
        >>> substituter.find("RuleIUH.update_parameters")
        |RuleIUH.update_parameters| \
:attr:`~hydpy.auxs.calibtools.RuleIUH.update_parameters`
        |calibtools.RuleIUH.update_parameters| \
:attr:`~hydpy.auxs.calibtools.RuleIUH.update_parameters`

        Module |typingtools| is unique, as it is the only one for which
        |Substituter.add_module| considers all explicitly exported type aliases:

        >>> from hydpy.core import typingtools
        >>> substituter.add_module(typingtools)
        >>> substituter.find("|NDArrayFloat|")  # doctest: +ELLIPSIS
        |NDArrayFloat| :...:`~hydpy.core.typingtools.NDArrayFloat`

        When adding Cython modules, the `cython` flag should be set |True|:

        >>> from hydpy.cythons import pointerutils
        >>> substituter.add_module(pointerutils, cython=True)
        >>> substituter.find("set_pointer")
        |PPDouble.set_pointer| \
:func:`~hydpy.cythons.autogen.pointerutils.PPDouble.set_pointer`
        |pointerutils.PPDouble.set_pointer| \
:func:`~hydpy.cythons.autogen.pointerutils.PPDouble.set_pointer`
        """
        name_module = module.__name__.split(".")[-1]
        short = f"|{name_module}|"
        long = f":mod:`~{module.__name__}`"
        self.short2long[short] = long
        for name_member, member in vars(module).items():
            if self.consider_member(name_member, member, module):
                role = self.get_role(member, cython)
                short = f"|{name_member}|"
                medium = f"|{name_module}.{name_member}|"
                long = f":{role}:`~{module.__name__}.{name_member}`"
                self.add_substitution(short, medium, long, module)
                if inspect.isclass(member):
                    annotations = getattr(member, "__annotations__", {})
                    for name_submember, submember in vars(member).items():
                        if self.consider_member(
                            name_member=name_submember,
                            member=submember,
                            module=module,
                            class_=member,
                            ignore=annotations,
                        ):
                            role = self.get_role(submember, cython)
                            short = f"|{name_member}.{name_submember}|"
                            medium = (
                                f"|{name_module}.{name_member}." f"{name_submember}|"
                            )
                            long = (
                                f":{role}:`~{module.__name__}."
                                f"{name_member}.{name_submember}`"
                            )
                            self.add_substitution(short, medium, long, module)
                    for name_submember, submember in annotations.items():
                        short = f"|{name_member}.{name_submember}|"
                        medium = f"|{name_module}.{name_member}." f"{name_submember}|"
                        long = (
                            f":attr:`~{module.__name__}."
                            f"{name_member}.{name_submember}`"
                        )
                        self.add_substitution(short, medium, long, module)

    def add_modules(self, package: types.ModuleType) -> None:
        """Add the modules of the given package without their members."""
        for name in sorted(os.listdir(package.__path__[0])):
            if name.startswith("_"):
                continue
            name = name.split(".")[0]
            short = f"|{name}|"
            long = f":mod:`~{package.__package__}.{name}`"
            self.short2long[short] = long

    def update_masters(self) -> None:
        """Update all `master` |Substituter| objects.

        If a |Substituter| object is passed to the constructor of another |Substituter|
        object, they become `master` and `slave`:

        >>> from hydpy.core.autodoctools import Substituter
        >>> sub1 = Substituter()
        >>> from hydpy.core import devicetools
        >>> sub1.add_module(devicetools)
        >>> sub2 = Substituter(sub1)
        >>> sub3 = Substituter(sub2)
        >>> sub3.master.master is sub1
        True
        >>> sub2 in sub1.slaves
        True

        During initialisation, all mappings handled by the master object are passed to
        its new slave:

        >>> sub3.find("Node|")
        |Node| :class:`~hydpy.core.devicetools.Node`
        |devicetools.Node| :class:`~hydpy.core.devicetools.Node`

        Updating a slave, does not affect its master directly:

        >>> from hydpy.core import hydpytools
        >>> sub3.add_module(hydpytools)
        >>> sub3.find("HydPy|")
        |HydPy| :class:`~hydpy.core.hydpytools.HydPy`
        |hydpytools.HydPy| :class:`~hydpy.core.hydpytools.HydPy`
        >>> sub2.find("HydPy|")

        Through calling |Substituter.update_masters|, the `medium2long` mappings are
        passed from the slave to its master:

        >>> sub3.update_masters()
        >>> sub2.find("HydPy|")
        |hydpytools.HydPy| :class:`~hydpy.core.hydpytools.HydPy`

        Then each master object updates its own master object also:

        >>> sub1.find("HydPy|")
        |hydpytools.HydPy| :class:`~hydpy.core.hydpytools.HydPy`

        In reverse, subsequent updates of master objects to not affect their slaves
        directly:

        >>> from hydpy.core import masktools
        >>> sub1.add_module(masktools)
        >>> sub1.find("Masks|")
        |Masks| :class:`~hydpy.core.masktools.Masks`
        |NodeMasks| :class:`~hydpy.core.masktools.NodeMasks`
        |masktools.Masks| :class:`~hydpy.core.masktools.Masks`
        |masktools.NodeMasks| :class:`~hydpy.core.masktools.NodeMasks`
        >>> sub2.find("Masks|")

        Through calling |Substituter.update_slaves|, the `medium2long` mappings are
        passed the master to all of its slaves:

        >>> sub1.update_slaves()
        >>> sub2.find("Masks|")
        |masktools.Masks| :class:`~hydpy.core.masktools.Masks`
        |masktools.NodeMasks| :class:`~hydpy.core.masktools.NodeMasks`
        >>> sub3.find("Masks|")
        |masktools.Masks| :class:`~hydpy.core.masktools.Masks`
        |masktools.NodeMasks| :class:`~hydpy.core.masktools.NodeMasks`
        """
        if self.master is not None:
            self.master.medium2long.update(self.medium2long)
            self.master.update_masters()

    def update_slaves(self) -> None:
        """Update all `slave` |Substituter| objects.

        See method |Substituter.update_masters| for further information.
        """
        for slave in self.slaves:
            slave.medium2long.update(self.medium2long)
            slave.update_slaves()

    def get_commands(self, source: Optional[str] = None) -> str:
        """Return a string containing multiple `reStructuredText` replacements with the
        substitutions currently defined.

        Some examples based on the subpackage |optiontools|:

        >>> from hydpy.core.autodoctools import Substituter
        >>> substituter = Substituter()
        >>> from hydpy.core import optiontools
        >>> substituter.add_module(optiontools)

        When calling |Substituter.get_commands| with the `source` argument, the
        complete `short2long` and `medium2long` mappings are translated into
        replacement commands (only a few of them are shown):

        >>> print(substituter.get_commands())   # doctest: +ELLIPSIS
        .. |OptionContextBase._new_value| replace:: \
:attr:`~hydpy.core.optiontools.OptionContextBase._new_value`
        .. |OptionContextBase._old_value| replace:: \
:attr:`~hydpy.core.optiontools.OptionContextBase._old_value`
        ...
        .. |optiontools.TypeOption| replace:: \
:const:`~hydpy.core.optiontools.TypeOption`
        .. |optiontools.l1| replace:: :const:`~hydpy.core.optiontools.l1`

        Through passing a string (usually the source code of a file to be documented),
        only the replacement commands relevant for this string are translated:

        >>> from hydpy.core import objecttools
        >>> import inspect
        >>> source = inspect.getsource(objecttools)
        >>> print(substituter.get_commands(source))
        .. |Options.ellipsis| replace:: \
:const:`~hydpy.core.optiontools.Options.ellipsis`
        .. |Options.reprdigits| replace:: \
:const:`~hydpy.core.optiontools.Options.reprdigits`
        """
        commands = []
        for key, value in self:
            if (source is None) or (key in source):
                commands.append(f".. {key} replace:: {value}")
        return "\n".join(commands)

    def find(self, text: str) -> None:
        """Print all substitutions that include the given text string."""
        for key, value in self:
            if (text in key) or (text in value):
                print(key, value)

    def __iter__(self) -> Iterator[tuple[str, str]]:
        yield from sorted(self.short2long.items())
        yield from sorted(self.medium2long.items())


def prepare_mainsubstituter() -> Substituter:
    """Prepare and return a |Substituter| object for the main `__init__` file of
    *HydPy*."""
    # pylint: disable=import-outside-toplevel
    import matplotlib
    from matplotlib import figure
    from matplotlib import pyplot
    import pandas
    import scipy

    substituter = Substituter()
    for module in (
        abc,
        builtins,
        numpy,
        datetime,
        unittest,
        doctest,
        inspect,
        io,
        os,
        sys,
        time,
        collections,
        itertools,
        subprocess,
        scipy,
        typing,
        platform,
        math,
        mimetypes,
        pandas,
        matplotlib,
        figure,
        pyplot,
        warnings,
    ):
        substituter.add_module(module)
    for subpackage in (auxs, core, cythons, interfaces, exe):
        for _, name, _ in pkgutil.iter_modules(subpackage.__path__):
            full_name = subpackage.__name__ + "." + name
            substituter.add_module(importlib.import_module(full_name))
    substituter.add_modules(models)
    for cymodule in (
        annutils,
        interputils,
        ppolyutils,
        pointerutils,
        quadutils,
        rootutils,
        smoothutils,
    ):
        substituter.add_module(cymodule, cython=True)
    substituter.short2long["|pub|"] = ":mod:`~hydpy.pub`"
    substituter.short2priority["|pub|"] = BUILTINS
    substituter.short2long["|config|"] = ":mod:`~hydpy.config`"
    substituter.short2priority["|config|"] = BUILTINS
    return substituter


def _number_of_line(member_tuple: tuple[str, object]) -> int:
    """Try to return the number of the first line of the definition of a member of a
    module."""

    def _query_index_first_line(member_: object) -> int:
        result = member_.__code__.co_firstlineno  # type: ignore[attr-defined]
        assert isinstance(result, int)
        return result

    member = member_tuple[1]
    try:
        return _query_index_first_line(member)
    except AttributeError:
        pass
    try:
        return inspect.findsource(member)[1]  # type: ignore[arg-type]
    except BaseException:
        pass
    if (submembers := getattr(member, "__dict__", None)) is not None:
        for value in submembers.values():
            try:
                return _query_index_first_line(value)
            except AttributeError:
                pass
    return 0


def autodoc_module(module: types.ModuleType) -> None:
    """Add a short summary of all implemented members to a module's docstring."""
    doc = getattr(module, "__doc__")
    members = []
    for name, member in inspect.getmembers(module):
        if (not name.startswith("_")) and (inspect.getmodule(member) is module):
            members.append((name, member))
    members = sorted(members, key=_number_of_line)
    if members:
        lines = [
            f"\n\nModule :mod:`~{module.__name__}` implements the following members:\n"
        ]
        for name, member in members:
            if inspect.isfunction(member):
                type_ = "func"
            elif inspect.isclass(member):
                type_ = "class"
            else:
                type_ = "obj"
            lines.append(
                f"      * :{type_}:`~{name}` {objecttools.description(member)}"
            )
        doc = doc + "\n\n" + "\n".join(lines) + "\n\n" + 80 * "_"
        module.__doc__ = doc


_name2descr = {
    "CLASSES": "The following classes are selected",
    "RECEIVER_METHODS": (
        'The following "receiver update methods" are called in the given sequence '
        "before performing a simulation step"
    ),
    "INLET_METHODS": (
        'The following "inlet update methods" are called in the given sequence at the '
        "beginning of each simulation step"
    ),
    "RUN_METHODS": (
        'The following "run methods" are called in the given sequence during each '
        "simulation step"
    ),
    "PART_ODE_METHODS": (
        "The following methods define the relevant components of a system of ODE "
        "equations (e.g. direct runoff)"
    ),
    "FULL_ODE_METHODS": (
        "The following methods define the complete equations of an ODE system (e.g. "
        "change in storage of `fast water` due to effective precipitation and direct "
        "runoff)"
    ),
    "OUTLET_METHODS": (
        'The following "outlet update methods" are called in the given sequence at '
        "the end of each simulation step"
    ),
    "SENDER_METHODS": (
        'The following "sender update methods" are called in the given sequence after '
        "performing a simulation step"
    ),
    "INTERFACE_METHODS": (
        "The following interface methods are available to main models using the "
        "defined model as a submodel"
    ),
    "ADD_METHODS": (
        'The following "additional methods" might be called by one or more of the '
        "other methods or are meant to be directly called by the user"
    ),
    "SUBMODELINTERFACES": (
        "Users can hook submodels into the defined main model if they satisfy one of "
        "the following interfaces"
    ),
    "SUBMODELS": (
        'The following "submodels" might be called by one or more of the implemented '
        "methods or are meant to be directly called by the user"
    ),
}

_loggedtuples: set[str] = set()


def autodoc_tuple2doc(module: types.ModuleType) -> None:
    """Include tuples as `CLASSES` of `ControlParameters` and `RUN_METHODS` of `Models`
    into the respective docstring."""
    modulename = module.__name__
    for membername, member in inspect.getmembers(module):
        for tuplename, descr in _name2descr.items():
            tuple_ = getattr(member, tuplename, None)
            if tuple_:
                logstring = f"{modulename}.{membername}.{tuplename}"
                if logstring not in _loggedtuples:
                    _loggedtuples.add(logstring)
                    lst = [f"\n\n\n    {descr}:"]
                    if tuplename == "CLASSES":
                        type_ = "func"
                    else:
                        type_ = "class"
                    for cls in tuple_:
                        lst.append(
                            f"      * "
                            f":{type_}:`~{cls.__module__}.{cls.__name__}`"
                            f" {objecttools.description(cls)}"
                        )
                    doc = getattr(member, "__doc__")
                    member.__doc__ = doc + "\n".join(l for l in lst)


def _make_cssstyle(
    *,
    marginleft: Optional[str] = None,
    marginbottom: Optional[str] = None,
    margintop: Optional[str] = None,
    colour: Optional[str] = None,
    fontfamily: Optional[str] = None,
    fontstyle: Optional[str] = None,
    fontsize: Optional[str] = None,
) -> str:

    styles = []
    if marginleft is not None:
        styles.append(f"margin-left:{marginleft}")
    if marginbottom is not None:
        styles.append(f"margin-bottom:{marginbottom}")
    if margintop is not None:
        styles.append(f"margin-top:{margintop}")
    if colour is not None:
        styles.append(f"color:{colour}")
    if fontfamily is not None:
        styles.append(f"font-family:{fontfamily}")
    if fontstyle is not None:
        styles.append(f"font-style:{fontstyle}")
    if fontsize is not None:
        styles.append(f"font-size:{fontsize}")
    style = "; ".join(styles)
    return f'style="{style}"'


class Directory(TypedDict):
    """Helper for representing directory structures."""

    subdirectories: dict[str, Directory]
    """Mapping between the subdirectory names and the subdirectories of a directory."""

    files: list[str]
    """The names of all files of a directory."""


class ProjectStructure:
    """Analyser and visualiser of the file structure of HydPy projects."""

    _dirpath: str
    """Directory path to the HydPy project."""
    _projectname: str
    """Directory name of the HydPy project."""
    _branch: str
    """The relevant git branch (required to build stable references to the correct 
    project files on GitHub)."""

    def __init__(self, *, projectpath: str, branch: str) -> None:
        self._dirpath = projectpath
        self._projectname = os.path.split(projectpath)[-1]
        self._branch = branch

    @functools.cached_property
    def url_prefix(self) -> str:
        """The base GitHub URL that is common to all project files of the relevant
        branch.

        >>> import os
        >>> from hydpy import data
        >>> projectpath = os.path.join(data.__path__[0], "HydPy-H-Lahn")
        >>> from hydpy.core.autodoctools import ProjectStructure
        >>> ProjectStructure(projectpath=projectpath, branch="master").url_prefix
        'https://github.com/hydpy-dev/hydpy/blob/master/hydpy/data'
        >>> ProjectStructure(projectpath=projectpath, branch="release/v6.0").url_prefix
        'https://github.com/hydpy-dev/hydpy/blob/release/v6.0/hydpy/data'
        """

        return f"https://github.com/hydpy-dev/hydpy/blob/{self._branch}/hydpy/data"

    def _get_filereference(self, url_dirpath: str, filename: str) -> str:
        url_suffix = "/".join([url_dirpath, filename])
        return (
            f"<a "
            f'class="reference external" '
            f'href="{self.url_prefix}/{url_suffix}">{filename}'
            f"</a>"
        )

    @functools.cached_property
    def directories(self) -> Directory:
        """A representation of the project's file structure based on nested |Directory|
        dictionaries.

        >>> import os
        >>> from hydpy import data
        >>> dirpath = os.path.join(data.__path__[0], "HydPy-H-Lahn")
        >>> from hydpy.core.autodoctools import ProjectStructure
        >>> pj = ProjectStructure(projectpath=dirpath, branch="master")
        >>> from pprint import pprint
        >>> pprint(pj.directories["files"])
        ['multiple_runs.xml',
         'multiple_runs_alpha.xml',
         'single_run.xml',
         'single_run.xmlt']
        >>> list(pj.directories["subdirectories"])
        ['conditions', 'control', 'network', 'series']
        >>> control = pj.directories["subdirectories"]["control"]
        >>> pprint(control["subdirectories"]["default"]["files"])
        ['land.py',
         'land_dill_assl.py',
         'land_lahn_kalk.py',
         'land_lahn_leun.py',
         'land_lahn_marb.py',
         'stream_dill_assl_lahn_leun.py',
         'stream_lahn_leun_lahn_kalk.py',
         'stream_lahn_marb_lahn_leun.py']
        >>> pprint(control["subdirectories"]["default"]["subdirectories"])
        {}
        """

        def _make_directory(dirpath: str) -> Directory:
            subdir: Directory = {"subdirectories": {}, "files": []}
            for name in sorted(os.listdir(dirpath)):
                if name.startswith("_"):
                    continue
                path = os.path.join(dirpath, name)
                if os.path.isfile(path):
                    subdir["files"].append(name)
                else:
                    subdirpath = os.path.join(dirpath, name)
                    subdir["subdirectories"][name] = _make_directory(subdirpath)
            return subdir

        return _make_directory(self._dirpath)

    @functools.cached_property
    def html(self) -> str:
        """A representation of the project's file structure based on nested HTML
        `describe` elements, including inline CSS instructions.

        >>> import os
        >>> from hydpy import data
        >>> projectpath = os.path.join(data.__path__[0], "HydPy-H-Lahn")
        >>> from hydpy.core.autodoctools import ProjectStructure
        >>> pj = ProjectStructure(projectpath=projectpath, branch="master")
        >>> print(pj.html)  # doctest: +ELLIPSIS
        <details style="margin-left:1em; color:#20435c; font-family:'Trebuchet MS'">
          <summary><b>HydPy-H-Lahn</b></summary>
          ...
          <details style="margin-left:1em">
            <summary><b>control</b></summary>
            <details style="margin-left:1em">
              <summary><b>default</b></summary>
              <h style="margin-left:1em"><a class="reference external" \
href="https://github.com/hydpy-dev/hydpy/blob/master/hydpy/data/HydPy-H-Lahn/control\
/default/land.py">land.py</a></h><br/>
              ...
              <h style="margin-left:1em"><a class="reference external" \
href="https://github.com/hydpy-dev/hydpy/blob/master/hydpy/data/HydPy-H-Lahn/control\
/default/stream_lahn_marb_lahn_leun.py">stream_lahn_marb_lahn_leun.py</a></h><br/>
            </details>
          </details>
          ...
        </details>
        """

        def _make_html(
            dirname: str, dir_: Directory, url: str, indent: int
        ) -> list[str]:
            if indent == 0:
                style = _make_cssstyle(
                    marginleft="1em", colour="#20435c", fontfamily="'Trebuchet MS'"
                )
            else:
                style = _make_cssstyle(marginleft="1em")
            prefix = indent * "  "
            lines = []
            lines.append(f"{prefix}<details {style}>")
            lines.append(f"{prefix}  <summary><b>{dirname}</b></summary>")
            for subdirname, subdir in dir_["subdirectories"].items():
                html_ = _make_html(
                    dirname=subdirname,
                    dir_=subdir,
                    url="/".join([url, subdirname]),
                    indent=indent + 1,
                )
                lines.extend(html_)
            for filename in dir_["files"]:
                ref = self._get_filereference(url_dirpath=url, filename=filename)
                lines.append(f"{prefix}  <h {style}>{ref}</h><br/>")
            lines.append(f"{prefix}</details>")
            return lines

        html = _make_html(
            dirname=self._projectname,
            dir_=self.directories,
            url=self._projectname,
            indent=0,
        )
        return "\n".join(html)


def make_modellink(model: type[modeltools.Model]) -> str:
    """Create an internal HTML reference pointing to an application model.

    >>> from hydpy.core.autodoctools import make_modellink
    >>> from hydpy.models import hland_96
    >>> make_modellink(hland_96.Model)
    '<a class="reference internal" \
href="hland_96.html#module-hydpy.models.hland_96" \
title="HydPy-H-HBV96 (adoption of SMHI-IHMS-HBV96)">\
<code class="xref py py-mod docutils literal notranslate">\
<span class="pre">hland_96</span></code></a>'
    """
    name = model.__HYDPY_NAME__
    return (
        '<a class="reference internal" '
        f'href="{name}.html#module-hydpy.models.{name}" '
        f'title="{model.DOCNAME.complete}">'
        '<code class="xref py py-mod docutils literal notranslate">'
        f'<span class="pre">{name}</span></code></a>'
    )


def make_interfacelink(interface: type[modeltools.SubmodelInterface]) -> str:
    """Create an internal HTML reference pointing to a submodel interface.

    >>> from hydpy.core.autodoctools import make_interfacelink
    >>> from hydpy.interfaces.aetinterfaces import AETModel_V1
    >>> make_interfacelink(AETModel_V1)
    '<a class="reference internal" \
href="aetinterfaces.html#hydpy.interfaces.aetinterfaces.AETModel_V1" \
title="hydpy.interfaces.aetinterfaces.AETModel_V1">\
<code class="xref py py-class docutils literal notranslate">\
<span class="pre">AETModel_V1</span></code></a>'
    """
    classname = interface.__name__
    modulepath = interface.__module__
    modulename = modulepath.split(".")[-1]
    classpath = f"{modulepath}.{classname}"
    return (
        f'<a class="reference internal" '
        f'href="{modulename}.html#{classpath}" '
        f'title="{classpath}"><code '
        f'class="xref py py-class docutils literal notranslate"><span '
        f'class="pre">{classname}</span></code></a>'
    )


Port: TypeAlias = Union[modeltools.SubmodelProperty, modeltools.SubmodelsProperty]

Subgraphs: TypeAlias = dict[
    type[modeltools.Model], dict[Port, list[type[modeltools.Model]]]
]

Graph: TypeAlias = dict[
    type[modeltools.Model], dict[Port, tuple["Graph", list[type[modeltools.Model]]]]
]


class SubmodelGraph:
    """Analyser and visualiser of the advisable connections between main models and
    submodels."""

    _modelname: Optional[str]

    def __init__(self, *, modelname: Optional[str] = None) -> None:
        self._modelname = modelname

    @functools.cached_property
    def interfaces(self) -> tuple[type[modeltools.SubmodelInterface], ...]:
        """All available submodel interfaces.

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> for interface in SubmodelGraph().interfaces:
        ...     print(interface.__HYDPY_NAME__)  # doctest: +ELLIPSIS
        AETModel_V1
        ChannelModel_V1
        ...
        TempModel_V1
        TempModel_V2
        WaterLevelModel_V1
        """
        dirpath = interfaces.__path__[0]
        filenames = (n for n in os.listdir(dirpath) if n.endswith(".py"))
        modulenames = (n[:-3] for n in filenames if n != "__init__.py")
        classes = []
        for modulename in modulenames:
            module = importlib.import_module(f"hydpy.interfaces.{modulename}")
            for _, member in inspect.getmembers(module):
                if (
                    inspect.isclass(member)
                    and (inspect.getmodule(member) is module)
                    and issubclass(member, modeltools.SubmodelInterface)
                ):
                    classes.append(member)
        return tuple(sorted(classes, key=lambda c: c.__name__))

    @functools.cached_property
    def models(self) -> tuple[type[modeltools.Model], ...]:
        """All available application models.

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> for model in SubmodelGraph().models:
        ...     print(model.__HYDPY_NAME__)  # doctest: +ELLIPSIS
        arma_rimorido
        conv_idw
        ...
        wland_wag
        wq_trapeze
        wq_trapeze_strickler
        wq_walrus
        """
        dirpath = models.__path__[0]
        filenames = (n for n in os.listdir(dirpath) if n.endswith(".py"))
        modulenames = (n[:-3] for n in filenames if n != "__init__.py")
        classes = []
        for modulename in modulenames:
            module = importlib.import_module(f"hydpy.models.{modulename}")
            for _, member in inspect.getmembers(module):
                if (
                    inspect.isclass(member)
                    and issubclass(member, modeltools.Model)
                    and (inspect.getmodule(member) is module)
                    and member.__name__ == "Model"
                ):
                    classes.append(member)
        return tuple(sorted(classes, key=lambda c: c.__HYDPY_NAME__))

    @functools.cached_property
    def rootmodels(self) -> tuple[type[modeltools.Model], ...]:
        """The models that build the roots of the submodel graph.

        By default, all documentation-relevant main models:

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> for model in SubmodelGraph().rootmodels:
        ...     print(model.__HYDPY_NAME__)  # doctest: +ELLIPSIS
        arma_rimorido
        conv_idw
        ...
        sw1d_channel
        wland_gd
        wland_wag

        Or only the selected model:

        >>> for model in SubmodelGraph(modelname="wland_gd").rootmodels:
        ...     print(model.__HYDPY_NAME__)
        wland_gd
        """
        rootmodels = []
        for model in self.models:
            if (model.__HYDPY_ROOTMODEL__ is True) and (
                ((name := self._modelname) is None) or (name == model.__HYDPY_NAME__)
            ):
                rootmodels.append(model)
        assert rootmodels
        return tuple(rootmodels)

    @functools.cached_property
    def subgraphs(self) -> Subgraphs:
        """Mappings from all models over their ports to their potential submodels.

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> subgraphs = SubmodelGraph().subgraphs
        >>> from hydpy.models import exch_branch_hbv96, hland_96
        >>> subgraphs[exch_branch_hbv96.Model]
        {}
        >>> for port, models in subgraphs[hland_96.Model].items():
        ...     print(port.name, *(model.__HYDPY_NAME__ for model in models))
        aetmodel evap_aet_hbv96 evap_aet_minhas evap_aet_morsim
        rconcmodel rconc_nash rconc_uh
        """
        main2port2subs: Subgraphs = {}
        for main in self.models:
            main2port2subs[main] = {}
            for _, port in inspect.getmembers(main):
                if isinstance(
                    port, (modeltools.SubmodelProperty, modeltools.SubmodelsProperty)
                ):
                    main2port2subs[main][port] = [
                        m for m in self.models if issubclass(m, port.interfaces)
                    ]
        return main2port2subs

    @functools.cached_property
    def graph(self) -> Graph:
        """The complete (recursive) graph for all or the selected root models.

        Example for a main model without any submodels:

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> graph = SubmodelGraph(modelname="exch_branch_hbv96").graph
        >>> for model, subgraph in graph.items():
        ...     print(model.__HYDPY_NAME__, subgraph)
        exch_branch_hbv96 {}

        Complex example that covers two important cases: (1) main models used as
        sub-submodels; (2) PET models are not suggested as submodel candidates for
        other PET models due to special-casing:

        >>> graph = SubmodelGraph(modelname="hland_96").graph
        >>> for model, subgraph in graph.items():
        ...     print(model.__HYDPY_NAME__, *(port.name for port in subgraph))
        hland_96 aetmodel rconcmodel

        >>> selected = tuple(graph.values())[0]
        >>> for port, (subgraphs, mainsubmodels) in selected.items():
        ...     print(port.name)
        ...     print("main-submodels:", *(m.__HYDPY_NAME__ for m in mainsubmodels))
        ...     print("sub-submodels:", *(m.__HYDPY_NAME__ for m in subgraphs))
        aetmodel
        main-submodels:
        sub-submodels: evap_aet_hbv96 evap_aet_minhas evap_aet_morsim
        rconcmodel
        main-submodels:
        sub-submodels: rconc_nash rconc_uh

        >>> selected = tuple(selected.values())[0][0]
        >>> for model, subgraph in selected.items():
        ...     print(model.__HYDPY_NAME__, *(port.name for port in subgraph))
        evap_aet_hbv96 intercmodel petmodel snowcovermodel soilwatermodel tempmodel
        evap_aet_minhas intercmodel petmodel soilwatermodel
        evap_aet_morsim intercmodel radiationmodel snowalbedomodel snowcovermodel \
snowycanopymodel soilwatermodel tempmodel

        >>> selected = tuple(tuple(selected.values())[0].items())[:2]
        >>> for port, (subgraphs, mainsubmodels) in selected:
        ...     print(port.name)
        ...     print("main-submodels:", *(m.__HYDPY_NAME__ for m in mainsubmodels))
        ...     print("sub-submodels:", *(m.__HYDPY_NAME__ for m in subgraphs))
        intercmodel
        main-submodels: hland_96
        sub-submodels: dummy_interceptedwater
        petmodel
        main-submodels:
        sub-submodels: evap_pet_ambav1 evap_pet_hbv96 evap_pet_m evap_pet_mlc \
evap_ret_fao56 evap_ret_io evap_ret_tw2002

        >>> selected = selected[1][1][0]
        >>> for model, subgraph in selected.items():
        ...     print(model.__HYDPY_NAME__, *(port.name for port in subgraph))
        evap_pet_ambav1 precipmodel radiationmodel snowcovermodel tempmodel
        evap_pet_hbv96 precipmodel tempmodel
        evap_pet_m retmodel
        evap_pet_mlc retmodel
        evap_ret_fao56 radiationmodel tempmodel
        evap_ret_io
        evap_ret_tw2002 radiationmodel tempmodel

        >>> selected = tuple(selected.values())[2]
        >>> for port, (subgraphs, mainsubmodels) in selected.items():
        ...     print(port.name)
        ...     print("main-submodels:", *(m.__HYDPY_NAME__ for m in mainsubmodels))
        ...     print("sub-submodels:", *(m.__HYDPY_NAME__ for m in subgraphs))
        retmodel
        main-submodels:
        sub-submodels: evap_ret_fao56 evap_ret_io evap_ret_tw2002

        Example showing that "side-model" ports are ignored:

        >>> graph = SubmodelGraph(modelname="sw1d_channel").graph
        >>> for model, subgraph in graph.items():
        ...     print(model.__HYDPY_NAME__, *(port.name for port in subgraph))
        sw1d_channel routingmodels storagemodels

        >>> selected = tuple(graph.values())[0]
        >>> for port, (subgraphs, mainsubmodels) in selected.items():
        ...     print(port.name)
        ...     print("main-submodels:", *(m.__HYDPY_NAME__ for m in mainsubmodels))
        ...     print("sub-submodels:", *(m.__HYDPY_NAME__ for m in subgraphs))
        routingmodels
        main-submodels:
        sub-submodels: sw1d_gate_out sw1d_lias sw1d_lias_sluice sw1d_pump sw1d_q_in \
sw1d_q_out sw1d_weir_out
        storagemodels
        main-submodels:
        sub-submodels: sw1d_storage

        >>> selected = tuple(selected.values())[0][0]
        >>> for model, subgraph in selected.items():
        ...     print(model.__HYDPY_NAME__, *(port.name for port in subgraph))
        sw1d_gate_out
        sw1d_lias crosssection
        sw1d_lias_sluice crosssection
        sw1d_pump crosssection
        sw1d_q_in crosssection
        sw1d_q_out crosssection
        sw1d_weir_out
        """

        def _exclude(
            mainmodel: type[modeltools.Model], submodel: type[modeltools.Model]
        ) -> bool:
            name_main = mainmodel.__HYDPY_NAME__
            name_sub = submodel.__HYDPY_NAME__
            main_comps = name_main.split("_")
            sub_comps = name_sub.split("_")
            if "evap" == main_comps[0] == sub_comps[0]:
                if (main_comps[1] == "pet") and (sub_comps[1] != "ret"):
                    return True
            return False

        def _get_subgraph(
            model: type[modeltools.Model], visited: set[type[modeltools.Model]]
        ) -> Graph:

            visited.add(model)

            graph: Graph = {model: {}}

            for port, submodels in self.subgraphs[model].items():

                if isinstance(port, modeltools.SubmodelProperty):
                    if port.sidemodel:
                        continue
                elif port.sidemodels:
                    continue

                mainsubmodels = []
                subgraph: Graph = {}
                for submodel in submodels:
                    if _exclude(model, submodel):
                        continue
                    if (
                        (submodel in visited)
                        and issubclass(model, modeltools.SubmodelInterface)
                        and model().add_mainmodel_as_subsubmodel(submodel())
                    ):
                        mainsubmodels.append(submodel)
                        continue
                    if submodel.__HYDPY_ROOTMODEL__:
                        continue
                    subgraph |= _get_subgraph(submodel, visited.copy())
                graph[model][port] = (subgraph, mainsubmodels)

            return graph

        complete: Graph = {}
        for root in self.rootmodels:
            complete[root] = _get_subgraph(model=root, visited=set())[root]
        return complete

    @staticmethod
    def make_portinfo(port: Port, mainsubmodels: list[type[modeltools.Model]]) -> str:
        """Create an informative sentence about the given port (if available, in the
        context of the given main models usable as sub-submodels).

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> from hydpy.models.hland_96 import Model as h
        >>> SubmodelGraph.make_portinfo(h.rconcmodel, [])  # doctest: +ELLIPSIS
        'Allows one submodel that follows the <a ...RConcModel_V1...</a> interface.'
        >>> SubmodelGraph.make_portinfo(h.aetmodel, [])  # doctest: +ELLIPSIS
        'Requires one submodel that follows the <a ...AETModel_V1...</a> interface \
(no default available).'
        >>> from hydpy.models.evap_aet_hbv96 import Model as e
        >>> SubmodelGraph.make_portinfo(e.tempmodel, [h])  # doctest: +ELLIPSIS
        'Requires one submodel that follows the <a ...TempModel_V1...</a> or \
<a ...TempModel_V2...</a> interface (default is <a ...HydPy-H-HBV96...</a>).'
        >>> from hydpy.models.sw1d_channel import Model as s
        >>> SubmodelGraph.make_portinfo(s.storagemodels, [])  # doctest: +ELLIPSIS
        'Allows multiple submodels that follow the <a ...StorageModel_V1...</a> \
interface.'
        """
        if isinstance(port, modeltools.SubmodelProperty):
            nmb_models = "one submodel that follows"
            if port.optional:
                necessity = "Allows"
                default = ""
            else:
                necessity = "Requires"
                if mainsubmodels:
                    assert len(mainsubmodels) == 1
                    default = f" (default is {make_modellink(mainsubmodels[0])})"
                else:
                    default = " (no default available)"
        else:
            nmb_models = "multiple submodels that follow"
            necessity = "Allows"
            default = ""
        links = objecttools.enumeration(
            [make_interfacelink(i) for i in port.interfaces], conjunction="or"
        )
        return f"{necessity} {nmb_models} the {links} interface{default}."

    @functools.cached_property
    def html(self) -> str:
        """A representation of the complete or selected part of the submodel graph
        based on nested HTML `describe` elements, including inline CSS instructions.

        >>> from hydpy.core.autodoctools import SubmodelGraph
        >>> print(SubmodelGraph().html)  # doctest: +ELLIPSIS
        <details style="margin-left:1.0em; color:#20435c; font-family:'Trebuchet MS'">
          <summary><b>Complete Submodel Graph</b></summary>
          <h style="margin-left:1.9em"><a ...HydPy-ARMA-RIMO/RIDO...</a></h></br>
          ...
        </details>

        >>> print(SubmodelGraph(modelname="hland_96").html)  # doctest: +ELLIPSIS
        <details style="margin-left:1.0em; color:#20435c; font-family:'Trebuchet MS'">
          <summary><b>Submodel Graph of HydPy-H-HBV96 (adoption of ...)</b></summary>
          <details style="margin-left:1.0em">
            <summary><a ...HydPy-H-HBV96...</a></summary>
            <details style="margin-left:1.0em">
              <summary>aetmodel</summary>
              <p style="margin-left:1.2em; margin-bottom:0.0em; margin-top:0.2em; \
font-style:italic; font-size:80%">Requires one submodel ...</p>
              <details style="margin-left:1.0em">
                <summary><a ...HydPy-Evap-AET-HBV96...</a></summary>
                <details style="margin-left:1.0em">
                  <summary>intercmodel</summary>
                  <p style="margin-left:1.2em; margin-bottom:0.0em; margin-top:0.2em; \
font-style:italic; font-size:80%">Requires one submodel ...</p>
                  <h style="margin-left:1.9em"><a ...HydPy-H-HBV96...</a><br/></h>
                  <h style="margin-left:1.9em"><a ...HydPy-Dummy-InterceptedWater ...\
</a></h></br>
        ...
          </details>
        </details>
        """
        style_main = _make_cssstyle(
            marginleft="1.0em", colour="#20435c", fontfamily="'Trebuchet MS'"
        )
        style_10em = _make_cssstyle(marginleft="1.0em")
        style_19em = _make_cssstyle(marginleft="1.9em")
        style_descr = _make_cssstyle(
            marginleft="1.2em",
            margintop="0.2em",
            marginbottom="0.0em",
            fontstyle="italic",
            fontsize="80%",
        )

        def _make_html(graph: Graph, indent: int) -> list[str]:
            prefix = indent * " "
            lines = []
            for model, port2subgraph_mainsubs in graph.items():
                modellink = make_modellink(model)
                if not port2subgraph_mainsubs:
                    lines.append(f"{prefix}<h {style_19em}>{modellink}</h></br>")
                    continue
                lines.append(f"{prefix}<details {style_10em}>")
                lines.append(f"{prefix}  <summary>{modellink}</summary>")
                for port, (subgraph, mainsubmodels) in port2subgraph_mainsubs.items():
                    lines.append(f"{prefix}  <details {style_10em}>")
                    lines.append(f"{prefix}    <summary>{port.name}</summary>")
                    info = self.make_portinfo(port, mainsubmodels)
                    lines.append(f"{prefix}    <p {style_descr}>{info}</p>")
                    for mainsubmodel in mainsubmodels:
                        link = make_modellink(mainsubmodel)
                        lines.append(f"{prefix}    <h {style_19em}>{link}<br/></h>")
                    lines.extend(_make_html(subgraph, indent + 4))
                    lines.append(f"{prefix}  </details>")
                lines.append(f"{prefix}</details>")
            return lines

        lines_ = [f"<details {style_main}>"]
        if self._modelname is None:
            lines_.append("  <summary><b>Complete Submodel Graph</b></summary>")
        else:
            docname = tuple(self.graph)[0].DOCNAME.complete
            lines_.append(f"  <summary><b>Submodel Graph of {docname}</b></summary>")
        lines_.extend(_make_html(self.graph, 2))
        lines_.append("</details>")
        return "\n".join(lines_)


# ToDo: remove when stopping supporting Python 3.12
#       (see https://github.com/python/cpython/issues/107995)
__test__ = {
    f"ProjectStructure.{name}": member
    for name, member in inspect.getmembers(ProjectStructure)
    if isinstance(member, functools.cached_property)
} | {
    f"SubmodelGraph.{name}": member
    for name, member in inspect.getmembers(SubmodelGraph)
    if isinstance(member, functools.cached_property)
}
