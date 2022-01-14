# pylint: disable=import-outside-toplevel
"""Execute this file before building source or binary distributions."""

import copy
import importlib
import os
import sys
from typing import *

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


def _prepare_baseextensions(fast_cython: bool, profile_cython: bool) -> None:
    names = []
    for name in sorted(os.listdir(os.path.join("hydpy", "cythons"))):
        if name.split(".")[-1] == "pyx":
            names.append(name.split(".")[0])
    for name in names:
        for suffix in ("pyx", "pxd"):
            filename = f"{name}.{suffix}"
            path_in = os.path.join("hydpy", "cythons", filename)
            path_out = os.path.join("hydpy", "cythons", "autogen", filename)
            cythonoptions = [
                "# -*- coding: utf-8 -*-",
                "# !python",
                "# cython: language_level=3",
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
            with open(path_in, encoding="utf-8") as file_in:
                text = file_in.read()
                text = text.replace(" int ", " " + INT + " ")
                text = text.replace(" int[", " " + INT + "[")
            with open(path_out, "w", encoding="utf-8") as file_out:
                file_out.write("\n".join(cythonoptions) + "\n\n")
                file_out.write(text)


def _compile_baseextensions() -> None:
    argv = copy.deepcopy(sys.argv)
    try:
        sys.argv = [sys.argv[0], "build_ext", "--build-lib=.", "--build-temp=."]
        extension = setuptools.Extension(
            "*",
            ["hydpy/cythons/autogen/*utils.pyx"],
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
    with pub.options.usecython(False), pub.options.forcecompiling(False):
        path_: str = models.__path__[0]  # type: ignore[attr-defined, name-defined]
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
def main(fast_cython: bool, profile_cython: bool) -> None:
    """Perform the following tasks:

    Copy the Cython source code of the extension modules from package `cythons` to
    subpackage `autogen` and modify the source code where necessary.

    Create the Cython source code of all model-specific extension modules.

    Write additional XML configuration files and sequence alias files.
    """
    _clear_autogendir()
    _prepare_baseextensions(fast_cython=fast_cython, profile_cython=profile_cython)
    _compile_baseextensions()
    _prepare_modelspecifics(fast_cython=fast_cython, profile_cython=profile_cython)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
