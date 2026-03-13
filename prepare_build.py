# pylint: disable=import-outside-toplevel
"""Execute this file before building source or binary distributions."""

import copy
import importlib
import inspect
import os
import pickle
import sys
from typing import get_type_hints, Literal

import click
import Cython.Build
import numpy
import setuptools

INT = "numpy.int64_t"


def _clear_autogendir() -> None:
    dirpath = os.path.join("hydpy", "cythons", "autogen")
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if os.path.isfile(filepath) and (filename != "__init__.py"):
            os.remove(filepath)


def _prepare_cythonoptions(fast_cython: bool, profile_cython: bool) -> list[str]:

    # ToDo: do not share code with PyxWriter.cythondistutilsoptions

    cythonoptions = [
        "# !python",
        "# distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION",
        "# cython: language_level=3",
        "# cython: cpow=True",
    ]

    if fast_cython:
        cythonoptions.extend(
            [
                "# cython: boundscheck=False",
                "# cython: wraparound=False",
                "# cython: initializedcheck=False",
                "# cython: cdivision=True",
            ]
        )
    else:
        cythonoptions.extend(
            [
                "# cython: boundscheck=True",
                "# cython: wraparound=True",
                "# cython: initializedcheck=True",
                "# cython: cdivision=False",
            ]
        )

    if profile_cython:
        cythonoptions.extend(
            [
                "# cython: linetrace=True",
                "# distutils: define_macros=CYTHON_TRACE=1",
                "# distutils: define_macros=CYTHON_TRACE_NOGIL=1",
            ]
        )

    return cythonoptions


def _prepare_baseextensions(fast_cython: bool, profile_cython: bool) -> None:
    names = []
    for name in sorted(os.listdir(os.path.join("hydpy", "cythons"))):
        if name.split(".")[-1] == "pyx":
            names.append(name.split(".")[0])
    opt = _prepare_cythonoptions(fast_cython=fast_cython, profile_cython=profile_cython)
    for name in names:
        for suffix in ("pyx", "pxd"):
            filename = f"{name}.{suffix}"
            path_in = os.path.join("hydpy", "cythons", filename)
            path_out = os.path.join("hydpy", "cythons", "autogen", filename)
            with open(path_in, encoding="utf-8") as file_in:
                text = file_in.read()
                text = text.replace(" int ", " " + INT + " ")
                text = text.replace(" int[", " " + INT + "[")
            with open(path_out, "w", encoding="utf-8") as file_out:
                file_out.write("\n".join(opt) + "\n\n")
                file_out.write(text)


def _convert_interfaces(fast_cython: bool, profile_cython: bool) -> None:
    from hydpy import config
    from hydpy.core.modeltools import abstractmodelmethods
    from hydpy.cythons.modelutils import TYPE2STR

    _nogil = " noexcept nogil" if config.FASTCYTHON else ""

    def _write_twice(text: str) -> None:
        pxdfile.write(text)
        pyxfile.write(text)

    opt = _prepare_cythonoptions(fast_cython=fast_cython, profile_cython=profile_cython)
    pydirpath = os.path.join("hydpy", "interfaces")
    cydirpath = os.path.join("hydpy", "cythons", "autogen")
    pyfilenames = (n for n in os.listdir(pydirpath) if n.endswith(".py"))
    modulenames = (n[:-3] for n in pyfilenames if n != "__init__.py")
    pxdpath = os.path.join(cydirpath, "masterinterface.pxd")
    pyxpath = os.path.join(cydirpath, "masterinterface.pyx")
    funcname2signature: dict[str, str] = {}
    with open(pxdpath, "w", encoding="utf-8") as pxdfile, open(
        pyxpath, "w", encoding="utf-8"
    ) as pyxfile:
        _write_twice("\n".join(opt) + "\n")
        _write_twice("\ncimport numpy\n")
        _write_twice("\nfrom hydpy.cythons.autogen cimport interfaceutils\n")
        _write_twice("\n\ncdef class MasterInterface(interfaceutils.BaseInterface):\n")
        signature = f"\n    cdef void new2old(self) {_nogil}"
        pxdfile.write(f"{signature}\n")
        pyxfile.write(f"{signature}:\n")
        pyxfile.write("        pass\n")
        for modulename in modulenames:
            pymodule = importlib.import_module(f"hydpy.interfaces.{modulename}")
            name2class = {
                name: member
                for name, member in inspect.getmembers(pymodule)
                if (inspect.isclass(member) and (inspect.getmodule(member) is pymodule))
            }
            for class_ in name2class.values():
                name2func = {
                    n: m
                    for n, m in inspect.getmembers(class_)
                    if inspect.isfunction(m) and (m in abstractmodelmethods)
                }
                for funcname, func in name2func.items():
                    typehints = get_type_hints(func)
                    name2type = {n: TYPE2STR[t] for n, t in typehints.items()}
                    args = ", ".join(
                        f"{t} {n}" for n, t in name2type.items() if n != "return"
                    )
                    returntype = name2type["return"]
                    signature = (
                        f"\n    cdef {returntype} {funcname}(self, {args}) {_nogil}"
                    )
                    if funcname in funcname2signature:
                        assert signature == funcname2signature[funcname]
                    else:
                        funcname2signature[funcname] = signature
                        pxdfile.write(f"{signature}\n")
                        pyxfile.write(f"{signature}:\n")
                        if typehints["return"] is type(None):
                            pyxfile.write("        pass\n")
                        elif typehints["return"] is float:
                            pyxfile.write("        return 0.0\n")
                        elif typehints["return"] is int:
                            pyxfile.write("        return 0\n")
                        else:
                            assert False


def _compile_extensions(filetype: Literal["utils", "interface"]) -> None:
    argv = copy.deepcopy(sys.argv)
    try:
        sys.argv = [sys.argv[0], "build_ext", "--build-lib=.", "--build-temp=."]
        extension = setuptools.Extension(
            "*",
            [f"hydpy/cythons/autogen/*{filetype}.pyx"],
            include_dirs=[numpy.get_include()],
        )
        setuptools.setup(
            name="temporary", ext_modules=Cython.Build.cythonize([extension])
        )
    finally:
        sys.argv = argv


def _prepare_modelspecifics(fast_cython: bool, profile_cython: bool) -> None:
    from hydpy import config
    from hydpy import pub
    from hydpy import models
    from hydpy.core import aliastools
    from hydpy.cythons import modelutils
    from hydpy.exe import xmltools

    config.FASTCYTHON = fast_cython
    config.PROFILECYTHON = profile_cython
    with pub.options.usecython(False):
        path_: str = models.__path__[0]
        for name in [fn.split(".")[0] for fn in sorted(os.listdir(path_))]:
            if not name.startswith("_"):
                module = importlib.import_module(f"hydpy.models.{name}")
                cythonizer: modelutils.Cythonizer | None
                cythonizer = getattr(module, "cythonizer", None)
                if cythonizer:
                    cythonizer.pyxwriter.write()

        aliastools.write_sequencealiases()
        xmltools.XSDWriter().write_xsd()


def _write_mypy_plugin_data() -> None:
    """Infer and write model-specific data required by the Mypy plugin."""

    from hydpy import conf
    from hydpy import models
    from hydpy import pub
    from hydpy.core.autodoctools import autodoc_complete
    from hydpy.core.importtools import prepare_model
    from hydpy.core.variabletools import Variable
    from hydpy.auxs.interptools import BaseInterpolator

    autodoc_complete()

    model2attr2module_var: dict[str, dict[str, tuple[str, str]]] = {}
    model2subgroup2attr2module_var: dict[str, dict[str, dict[str, tuple[str, str]]]] = (
        {}
    )
    var2modelmodule_subgroupmodule_subgrouptype: dict[str, tuple[str, str, str]] = {}
    var2ndim_type: dict[str, tuple[int, type[float]]] = {}

    with pub.options.usecython(False):
        dirpath = models.__path__[0]
        for modelname in os.listdir(dirpath):
            modelpath = os.path.join(dirpath, modelname)
            if os.path.isdir(modelpath) and (modelname != "__pycache__"):
                basemodel = True
                modelmodule = f"hydpy.models.{modelname}.{modelname}_model"
            elif modelpath.endswith(".py") and (modelname != "__init__.py"):
                basemodel = False
                modelname = modelname.removesuffix(".py")
                modelmodule = f"hydpy.models.{modelname}"
            else:
                continue
            model = prepare_model(modelname)
            subdict = {}
            for method in model.get_methods():
                complete_name = method.__name__.lower()
                subdict[complete_name] = (method.__module__, method.__name__)
                short_name = complete_name.rpartition("_")[0]
                if hasattr(model, short_name):
                    subdict[short_name] = (method.__module__, method.__name__)
            model2attr2module_var[modelmodule] = subdict
            subdict_ = {}
            for prefix, vars_ in (
                ("hydpy.core.parametertools", model.parameters),
                ("hydpy.core.sequencetools", model.sequences),
            ):
                for subvars in vars_:
                    subsubdict = {}
                    for var in subvars:
                        subsubdict[var.name] = (
                            type(var).__module__,
                            type(var).__name__,
                        )
                        if basemodel:
                            fullname = f"{type(var).__module__}.{type(var).__name__}"
                            var2modelmodule_subgroupmodule_subgrouptype[fullname] = (
                                modelmodule,
                                prefix,
                                type(subvars).__name__,
                            )
                            var2ndim_type[fullname] = var.NDIM, var.TYPE
                    subdict_[f"{prefix}.{type(subvars).__name__}"] = subsubdict
            model2subgroup2attr2module_var[f"{modelmodule}.Model"] = subdict_

    vars_with_shape: set[str] = set()

    def _search_variables_with_specific_members(
        v: type[Variable | BaseInterpolator], seen: set[str]
    ) -> None:
        fullname_ = f"{v.__module__}.{v.__name__}"
        if (fullname_ in seen) or not fullname_.startswith("hydpy."):
            return
        seen.add(fullname_)
        if "shape" in vars(v):
            vars_with_shape.add(f"{fullname_}.shape")
        for w in v.__subclasses__():
            _search_variables_with_specific_members(w, seen)
        for w in v.__bases__:
            _search_variables_with_specific_members(w, seen)

    _search_variables_with_specific_members(Variable, set())
    _search_variables_with_specific_members(BaseInterpolator, set())

    filepath = os.path.join(conf.__path__[0], "mypy_plugin_data.pickle")
    with open(filepath, "wb") as file_:
        data = (
            model2attr2module_var,
            model2subgroup2attr2module_var,
            var2modelmodule_subgroupmodule_subgrouptype,
            var2ndim_type,
            vars_with_shape,
        )
        pickle.dump(data, file_, protocol=pickle.HIGHEST_PROTOCOL)


@click.command()
@click.option(
    "-f",
    "--fast-cython",
    type=bool,
    default=True,
    help="See the documentation on option `FASTCYTHON` option of module `config`.",
)
@click.option(
    "-p",
    "--profile-cython",
    type=bool,
    default=False,
    help="See the documentation on option `PROFILECYTHON` option of module `config`.",
)
@click.option(
    "-e",
    "--compile-baseextensions",
    type=bool,
    default=True,
    help="Translate the modified Cython extension files into C files and compile them.",
)
@click.option(
    "-i",
    "--compile-interfaceextensions",
    type=bool,
    default=False,
    help="Translate the generate Cython interface files into C files and compile them.",
)
def main(
    fast_cython: bool,
    profile_cython: bool,
    compile_baseextensions: bool,
    compile_interfaceextensions: bool,
) -> None:
    """Perform the following tasks:

    Copy the Cython source code of the extension modules from package `cythons` to
    subpackage `autogen` and modify the source code where necessary.  Then, optionally,
    compile the modified extensions.

    Create the Cython source code of all interface-specific extension modules defined
    in the `interfaces` subpackage.  Then, optionally, compile the created extensions.

    Create the Cython source code of all model-specific extension modules.

    Write additional XML configuration files and sequence alias files.
    """
    _clear_autogendir()
    _prepare_baseextensions(fast_cython=fast_cython, profile_cython=profile_cython)
    if compile_baseextensions:
        _compile_extensions(filetype="utils")
    _convert_interfaces(fast_cython=fast_cython, profile_cython=profile_cython)
    if compile_interfaceextensions:
        _compile_extensions(filetype="interface")
    _prepare_modelspecifics(fast_cython=fast_cython, profile_cython=profile_cython)
    _write_mypy_plugin_data()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
