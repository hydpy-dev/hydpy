"""This module provides tools for the efficient handling of input and output
sequence aliases."""

# import...
# ...from standard library
import importlib
import inspect
import os
import pkgutil
import types

# ...from site-packages
import black

# ...from HydPy
import hydpy
from hydpy import config
from hydpy import models
from hydpy.core import sequencetools
from hydpy.core.typingtools import *


class LazyInOutSequenceImport:
    """Import the input or output sequence the alias is referring to only when required.

    .. _`special method lookup`: https://docs.python.org/reference/datamodel.html#special-lookup  # pylint: disable=line-too-long

    Importing all input and output sequences costs a significant amount of
    initialisation time, and one typically uses at most a few of them within a
    specific project.  Hence, we implemented class |LazyInOutSequenceImport| for
    postponing the imports of the sequences available by modules `inputs` and
    `outputs`.  We hope we could catch all exceptional cases so that a user will
    never realise to work with a |LazyInOutSequenceImport| object instead with an
    input or output class object (except when directly asking for it with function
    |type|).

    Directly after importing, the alias is of type |LazyInOutSequenceImport|:

    >>> from hydpy.core.aliastools import LazyInOutSequenceImport
    >>> def get_example_alias():
    ...     return LazyInOutSequenceImport(
    ...         modulename="hydpy.models.hland.hland_inputs",
    ...         classname="T",
    ...         alias="hland_inputs_T",
    ...         namespace=locals(),
    ...     )
    >>> hland_inputs_T = get_example_alias()
    >>> type(hland_inputs_T)
    <class 'hydpy.core.aliastools.LazyInOutSequenceImport'>

    After accessing an attribute, its type changed to |abc.ABCMeta|, which is the
    meta-class of all input and output sequences:

    >>> hland_inputs_T.__name__
    'T'
    >>> type(hland_inputs_T)
    <class 'type'>

    Due to Python's `special method lookup`_, we must explicitly define the relevant
    ones.  The following examples list all considered methods:

    >>> hland_inputs_T = get_example_alias()
    >>> from hydpy.models.hland.hland_inputs import T, P
    >>> hash(hland_inputs_T) == hash(T)
    True

    >>> hland_inputs_T = get_example_alias()
    >>> hland_inputs_T == T
    True
    >>> hland_inputs_T = get_example_alias()
    >>> T == hland_inputs_T
    True

    >>> hland_inputs_T = get_example_alias()
    >>> hland_inputs_T != P
    True
    >>> hland_inputs_T = get_example_alias()
    >>> P != hland_inputs_T
    True

    >>> hland_inputs_T = get_example_alias()
    >>> str(hland_inputs_T)
    "<class 'hydpy.models.hland.hland_inputs.T'>"

    >>> hland_inputs_T = get_example_alias()
    >>> repr(hland_inputs_T)
    "<class 'hydpy.models.hland.hland_inputs.T'>"

    >>> hland_inputs_T = get_example_alias()
    >>> dir(hland_inputs_T)   # doctest: +ELLIPSIS
    ['INIT', 'NDIM', ...]
    """

    def __init__(
        self, modulename: str, classname: str, alias: str, namespace: dict[str, Any]
    ) -> None:
        self._modulename = modulename
        self._classname = classname
        self._alias = alias
        self._namespace = namespace

    def _get_sequencetype(self) -> sequencetools.InOutSequenceTypes:
        dict_ = object.__getattribute__(self, "__dict__")
        module = importlib.import_module(dict_["_modulename"])
        return getattr(module, dict_["_classname"])

    def __getattribute__(self, name: str) -> Any:
        class_ = LazyInOutSequenceImport._get_sequencetype(self)
        dict_ = object.__getattribute__(self, "__dict__")
        alias = dict_["_alias"]
        dict_["_namespace"][alias] = class_
        hydpy.sequence2alias[class_] = alias
        frame = inspect.currentframe()
        while frame is not None:
            if alias in frame.f_locals:
                frame.f_locals[alias] = class_
            frame = frame.f_back
        if name == "_get_sequencetype":
            return types.MethodType(LazyInOutSequenceImport._get_sequencetype, self)
        return getattr(class_, name)

    def __hash__(self) -> int:
        return hash(self._get_sequencetype())

    def __eq__(self, other: object) -> bool:
        return self._get_sequencetype() == other

    def __ne__(self, other: object) -> bool:
        return self._get_sequencetype() != other

    def __str__(self) -> str:
        return str(self._get_sequencetype())

    def __repr__(self) -> str:
        return repr(self._get_sequencetype())

    def __dir__(self) -> list[str]:
        return dir(self._get_sequencetype())


def write_sequencealiases() -> None:
    """Write the sequence alias module `aliases.py`.

    After extending a model or adding a new one, you can update the module by calling
    |write_sequencealiases|:

    >>> from hydpy.core.aliastools import write_sequencealiases
    >>> write_sequencealiases()
    """
    groupname2sequencetype2ndims = (
        ("inputs", sequencetools.InputSequence, (0,)),
        ("inlets", sequencetools.InletSequence, (0, 1)),
        ("receivers", sequencetools.ReceiverSequence, (0, 1)),
        ("observers", sequencetools.ObserverSequence, (0, 1)),
        ("factors", sequencetools.FactorSequence, (0,)),
        ("fluxes", sequencetools.FluxSequence, (0,)),
        ("states", sequencetools.StateSequence, (0,)),
        ("outlets", sequencetools.OutletSequence, (0, 1)),
        ("senders", sequencetools.SenderSequence, (0, 1)),
    )
    modelpath: str = models.__path__[0]
    sequence2alias: dict[sequencetools.InOutSequenceTypes, str] = {}
    for moduleinfo in pkgutil.iter_modules([modelpath]):
        if not moduleinfo.ispkg:
            continue
        for groupname, sequencetype, ndim in groupname2sequencetype2ndims:
            modelname = moduleinfo.name
            modulepath = f"hydpy.models.{modelname}.{modelname}_{groupname}"
            try:
                module = importlib.import_module(modulepath)
            except ModuleNotFoundError:
                continue
            for member in vars(module).values():
                if (
                    (getattr(member, "__module__", None) == modulepath)
                    and issubclass(member, sequencetype)
                    and member.NDIM in ndim
                ):
                    alias = f"{modelname}_{groupname}_{member.__name__}"
                    sequence2alias[member] = alias

    lines = [
        '"""This module provides the aliases of the sequences of all available models '
        "one might \nwant to connect to node sequences.",
        "",
        "This file was automatically created by function |write_sequencealiases|.",
        '"""',
        "# import...",
        "# ...from standard library",
        "from typing import TYPE_CHECKING",
        "# ...from HydPy",
        "from hydpy.core.aliastools import LazyInOutSequenceImport",
    ]
    lines.append("if TYPE_CHECKING:")
    for sequence, alias in sequence2alias.items():
        lines.append(
            f"    from {sequence.__module__} " f"import {sequence.__name__} as {alias}"
        )
    lines.append("else:")
    for sequence, alias in sequence2alias.items():
        lines.append(
            f"    {alias} = LazyInOutSequenceImport("
            f'        modulename="{sequence.__module__}",'
            f'        classname="{sequence.__name__}",'
            f'        alias="{alias}",'
            f"        namespace=locals(),"
            f"    )"
        )
    exports = (f'"{alias}"' for alias in sequence2alias.values())
    lines.append(f'\n__all__ = [{", ".join(exports)}]')
    text = "\n".join(lines)
    text = black.format_str(text, mode=black.FileMode())
    filepath = os.path.join(hydpy.__path__[0], "aliases.py")
    with open(filepath, "w", encoding=config.ENCODING) as file_:
        file_.write(text)
