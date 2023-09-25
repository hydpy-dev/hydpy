# pylint: disable=import-outside-toplevel
"""Execute this file before building source or binary distributions."""

import copy
import importlib
import inspect
import os
import sys
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

import click
import Cython.Build
import numpy
import setuptools

# Determine the correct type string for integer values in Cython compatible with numpy
# on the respective machine:
INT = f"numpy.{numpy.array([1]).dtype}_t"


def _clear_autogendir() -> None:
    dirpath = os.path.join("hydpy", "cythons", "autogen")
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if os.path.isfile(filepath) and (filename != "__init__.py"):
            os.remove(filepath)


def _prepare_cythonoptions(fast_cython: bool, profile_cython: bool) -> List[str]:

    # ToDo: do not share code with PyxWriter.cythondistutilsoptions

    cythonoptions = [
        "# -*- coding: utf-8 -*-",
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
    from hydpy.core.modeltools import abstractmodelmethods
    from hydpy.cythons.modelutils import TYPE2STR

    def _write_twice(text: str) -> None:
        pxdfile.write(text)
        pyxfile.write(text)

    opt = _prepare_cythonoptions(fast_cython=fast_cython, profile_cython=profile_cython)
    pydirpath = os.path.join("hydpy", "interfaces")
    cydirpath = os.path.join("hydpy", "cythons", "autogen")
    pyfilenames = (n for n in os.listdir(pydirpath) if n.endswith(".py"))
    modulenames = (n[:-3] for n in pyfilenames if n != "__init__.py")
    pxdpath = os.path.join(cydirpath, f"masterinterface.pxd")
    pyxpath = os.path.join(cydirpath, f"masterinterface.pyx")
    funcname2signature: Dict[str, str] = {}
    with open(pxdpath, "w", encoding="utf-8") as pxdfile, open(
        pyxpath, "w", encoding="utf-8"
    ) as pyxfile:
        _write_twice("\n".join(opt) + "\n")
        _write_twice("\ncimport numpy\n")
        _write_twice("\nfrom hydpy.cythons.autogen cimport interfaceutils\n")
        _write_twice("\n\ncdef class MasterInterface(interfaceutils.BaseInterface):\n")
        signature = f"\n    cdef void new2old(self) nogil"
        pxdfile.write(f"{signature}\n")
        pyxfile.write(f"{signature}:\n")
        pyxfile.write(f"        pass\n")
        for modulename in modulenames:
            pymodule = importlib.import_module(f"hydpy.interfaces.{modulename}")
            name2class = {
                name: member
                for name, member in inspect.getmembers(pymodule)
                if (inspect.isclass(member) and (inspect.getmodule(member) is pymodule))
            }
            for classname, class_ in name2class.items():
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
                        f"\n    cdef {returntype} {funcname}(self, {args}) nogil"
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


def _compile_extensions(filetype: Literal["utils", "interfaces"]) -> None:
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
    from hydpy.auxs import xmltools
    from hydpy.cythons import modelutils

    config.FASTCYTHON = fast_cython
    config.PROFILECYTHON = profile_cython
    with pub.options.usecython(False):
        path_: str = models.__path__[0]
        for name in [fn.split(".")[0] for fn in sorted(os.listdir(path_))]:
            if not name.startswith("_"):
                module = importlib.import_module(f"hydpy.models.{name}")
                cythonizer: Optional[modelutils.Cythonizer]
                cythonizer = getattr(module, "cythonizer", None)
                if cythonizer:
                    cythonizer.pyxwriter.write()

        aliastools.write_sequencealiases()
        xmltools.XSDWriter().write_xsd()


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


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
