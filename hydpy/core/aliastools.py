# -*- coding: utf-8 -*-
"""This module provides tools for the efficient handling of input and output
sequence aliases.

.. note::

    We are not sure if class |LazyInOutSequenceImport| always works as expected
    under Python 3.6.  Hence, function |write_sequencealiases| does not use it
    when generating the alias modules `inputs` and `outputs` if one executes it
    with Python 3.6.  Applying |LazyInOutSequenceImport| under Python 3.6 is at
    your own risk.
"""
# import...
# ...from standard library
import importlib
import inspect
import os
import pkgutil
import sys
import types
from typing import *

# ...from site-packages
import black

# ...from HydPy
import hydpy
from hydpy import models
from hydpy.core import sequencetools

_python36 = sys.version_info[:2] < (3, 7)


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
    ...         alias="hland_T",
    ...         namespace=locals(),
    ...     )
    >>> hland_T = get_example_alias()
    >>> def normalise_typestring(typestr):
    ...     # for handling differences between Python 3.6 and newer versions
    ...     if "class" in typestr:
    ...         typestr = typestr.split("'")[1]
    ...     if typestr == "typing.GenericMeta":
    ...         return "type"
    ...     return typestr
    >>> normalise_typestring(str(type(hland_T)))
    'hydpy.core.aliastools.LazyInOutSequenceImport'

    After accessing an attribute, its type changed to |type|, which is the meta-class
    of all input and output sequences:

    >>> hland_T.__name__
    'T'
    >>> normalise_typestring(str(type(hland_T)))
    'type'

    Due to Python's `special method lookup`_, we must explicitly define the relevant
    ones.  The following examples list all considered methods:

    >>> hland_T = get_example_alias()
    >>> from hydpy.models.hland.hland_inputs import T, P
    >>> hash(hland_T) == hash(T)
    True

    >>> hland_T = get_example_alias()
    >>> hland_T == T
    True
    >>> hland_T = get_example_alias()
    >>> T == hland_T   # doctest: +SKIP
    True  # correct for Python 3.7 and newer but incorrect for Python 3.6

    >>> hland_T = get_example_alias()
    >>> hland_T != P
    True
    >>> hland_T = get_example_alias()
    >>> P != hland_T
    True

    >>> hland_T = get_example_alias()
    >>> normalise_typestring(str(hland_T))
    'hydpy.models.hland.hland_inputs.T'

    >>> hland_T = get_example_alias()
    >>> normalise_typestring(repr(hland_T))
    'hydpy.models.hland.hland_inputs.T'

    >>> hland_T = get_example_alias()
    >>> dir(hland_T)   # doctest: +ELLIPSIS
    ['INIT', 'NDIM', ...]
    """

    def __init__(
        self,
        modulename: str,
        classname: str,
        alias: str,
        namespace: Dict[str, Any],
    ) -> None:
        self._modulename = modulename
        self._classname = classname
        self._alias = alias
        self._namespace = namespace

    def _get_sequencetype(self) -> sequencetools.TypesInOutSequence:
        dict_ = object.__getattribute__(self, "__dict__")
        module = importlib.import_module(dict_["_modulename"])
        return getattr(module, dict_["_classname"])  # type: ignore[no-any-return]

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

    def __dir__(self) -> List[str]:
        return dir(self._get_sequencetype())


def write_sequencealiases() -> None:
    """Write the alias modules `inputs` and `outputs`.

    After extending a model or adding a new one, you can update both modules by
    calling |write_sequencealiases|:

    >>> from hydpy.core.aliastools import write_sequencealiases
    >>> write_sequencealiases()
    """
    modelpath: str = models.__path__[0]  # type: ignore[attr-defined, modelname-defined]
    for groupnames, sequencetypes, filename in (
        (
            ("inputs",),
            (sequencetools.InputSequence,),
            "inputs.py",
        ),
        (
            ("fluxes", "states"),
            (sequencetools.FluxSequence, sequencetools.StateSequence),
            "outputs.py",
        ),
    ):
        sequence2alias: Dict[sequencetools.TypesInOutSequence, str] = {}
        for moduleinfo in pkgutil.walk_packages([modelpath]):
            if not moduleinfo.ispkg:
                continue
            for groupname in groupnames:
                modelname = moduleinfo.name
                modulepath = f"hydpy.models.{modelname}.{modelname}_{groupname}"
                try:
                    module = importlib.import_module(modulepath)
                except ModuleNotFoundError:
                    continue
                for member in vars(module).values():
                    if (
                        (getattr(member, "__module__", None) == modulepath)
                        and issubclass(member, sequencetypes)
                        and member.NDIM == 0
                    ):
                        alias = f"{modelname}_{member.__name__}"
                        sequence2alias[member] = alias
        hydpypath = hydpy.__path__[0]  # type: ignore[attr-defined, modelname-defined]

        lines = [
            f'"""This module provides the aliases of the {filename[:-4]} '
            "variables of all available models.\n",
            "This file was automatically created by function |write_sequencealiases|.",
            '"""\n',
            "# import...",
        ]
        if not _python36:  # pragma: no cover
            lines.append("# ...from standard library")
            lines.append("from typing import TYPE_CHECKING\n")
        lines.append("# ...from HydPy")
        if _python36:  # pragma: no cover
            lines.append("import hydpy")
            blanks = ""
        else:  # pragma: no cover
            blanks = "    "
            lines.append("from hydpy.core.aliastools import LazyInOutSequenceImport\n")
            lines.append("if TYPE_CHECKING:")
        for sequence, alias in sequence2alias.items():
            lines.append(
                f"{blanks}from {sequence.__module__} "
                f"import {sequence.__name__} as {alias}"
            )
        if _python36:  # pragma: no cover
            lines.append("")
            for sequence, alias in sequence2alias.items():
                lines.append(f'hydpy.sequence2alias[{alias}] = "{alias}"')
        else:  # pragma: no cover
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
        text = "\n".join(lines)
        text = black.format_str(text, mode=black.FileMode())
        with open(os.path.join(hydpypath, filename), "w") as file_:
            file_.write(text)
