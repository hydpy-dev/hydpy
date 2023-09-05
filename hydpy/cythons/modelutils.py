# -*- coding: utf-8 -*-
""" This module provides utilities to build Cython models based on Python models
automatically.

.. _`issue`: https://github.com/hydpy-dev/hydpy/issues

Most model developers do not need to be aware of the features implemented in module
|modelutils|, except that they need to initialise class |Cythonizer| within the main
modules of their base and application models (see, for example, the source code of base
model |hland| and application model |hland_v1|).

However, when implementing models with functionalities not envisaged so far, problems
might arise.  Please contact the *HydPy* developer team then, preferably by opening an
`issue`_ on GitHub.  Potentially, problems could occur when defining parameters or
sequences with larger dimensionality than anticipated.  The following example shows the
Cython code lines for the |ELSModel.get_point_states| method of class |ELSModel|, used
for deriving the |test| model.  By now, we did only implement 0-dimensional and
1-dimensional sequences requiring this method.  After hackishly changing the
dimensionality of sequences |test_states.S|, we still seem to get plausible results,
but these are untested in model applications:

>>> from hydpy.models.test import cythonizer
>>> pyxwriter = cythonizer.pyxwriter
>>> from hydpy.cythons.modelutils import PyxPxdLines
>>> lines = PyxPxdLines()
>>> pyxwriter.get_point_states(lines)
            . get_point_states
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void get_point_states(self) nogil:
        cdef ...int... idx0
        self.sequences.states.s = \
self.sequences.states._s_points[self.numvars.idx_stage]
        for idx0 in range(self.sequences.states._sv_length):
            self.sequences.states.sv[idx0] = \
self.sequences.states._sv_points[self.numvars.idx_stage][idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.states.s.NDIM = 2
>>> lines.pyx.clear()
>>> pyxwriter.get_point_states(lines)
            . get_point_states
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void get_point_states(self) nogil:
        cdef ...int... idx0, idx1
        for idx0 in range(self.sequences.states._s_length0):
            for idx1 in range(self.sequences.states._s_length1):
                self.sequences.states.s[idx0, idx1] = \
self.sequences.states._s_points[self.numvars.idx_stage][idx0, idx1]
        for idx0 in range(self.sequences.states._sv_length):
            self.sequences.states.sv[idx0] = \
self.sequences.states._sv_points[self.numvars.idx_stage][idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.states.s.NDIM = 3
>>> pyxwriter.get_point_states(lines)
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `s` is higher than expected.

The following examples show the results for some methods which are also related to
numerical integration but deal with |FluxSequence| objects.  We start with the method
|ELSModel.integrate_fluxes|:

>>> lines.pyx.clear()
>>> pyxwriter.integrate_fluxes(lines)
            . integrate_fluxes
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void integrate_fluxes(self) nogil:
        cdef ...int... jdx, idx0
        self.sequences.fluxes.q = 0.
        for jdx in range(self.numvars.idx_method):
            self.sequences.fluxes.q = \
self.sequences.fluxes.q +self.numvars.dt * \
self.numconsts.a_coefs[self.numvars.idx_method-1, \
self.numvars.idx_stage, jdx]*self.sequences.fluxes._q_points[jdx]
        for idx0 in range(self.sequences.fluxes._qv_length):
            self.sequences.fluxes.qv[idx0] = 0.
            for jdx in range(self.numvars.idx_method):
                self.sequences.fluxes.qv[idx0] = \
self.sequences.fluxes.qv[idx0] + self.numvars.dt * \
self.numconsts.a_coefs[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]*\
self.sequences.fluxes._qv_points[jdx, idx0]
<BLANKLINE>


>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> lines.pyx.clear()
>>> pyxwriter.integrate_fluxes(lines)
            . integrate_fluxes
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void integrate_fluxes(self) nogil:
        cdef ...int... jdx, idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.sequences.fluxes.q[idx0, idx1] = 0.
                for jdx in range(self.numvars.idx_method):
                    self.sequences.fluxes.q[idx0, idx1] = \
self.sequences.fluxes.q[idx0, idx1] + self.numvars.dt * \
self.numconsts.a_coefs[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]*\
self.sequences.fluxes._q_points[jdx, idx0, idx1]
        for idx0 in range(self.sequences.fluxes._qv_length):
            self.sequences.fluxes.qv[idx0] = 0.
            for jdx in range(self.numvars.idx_method):
                self.sequences.fluxes.qv[idx0] = \
self.sequences.fluxes.qv[idx0] + self.numvars.dt * \
self.numconsts.a_coefs[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]\
*self.sequences.fluxes._qv_points[jdx, idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.integrate_fluxes(lines)
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.

Method |ELSModel.reset_sum_fluxes|:

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 0
>>> lines.pyx.clear()
>>> pyxwriter.reset_sum_fluxes(lines)
            . reset_sum_fluxes
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void reset_sum_fluxes(self) nogil:
        cdef ...int... idx0
        self.sequences.fluxes._q_sum = 0.
        for idx0 in range(self.sequences.fluxes._qv_length):
            self.sequences.fluxes._qv_sum[idx0] = 0.
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> lines.pyx.clear()
>>> pyxwriter.reset_sum_fluxes(lines)
            . reset_sum_fluxes
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void reset_sum_fluxes(self) nogil:
        cdef ...int... idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.sequences.fluxes._q_sum[idx0, idx1] = 0.
        for idx0 in range(self.sequences.fluxes._qv_length):
            self.sequences.fluxes._qv_sum[idx0] = 0.
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.reset_sum_fluxes(lines)
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.

Method |ELSModel.addup_fluxes|:

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 0
>>> lines.pyx.clear()
>>> pyxwriter.addup_fluxes(lines)
            . addup_fluxes
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void addup_fluxes(self) nogil:
        cdef ...int... idx0
        self.sequences.fluxes._q_sum = \
self.sequences.fluxes._q_sum + self.sequences.fluxes.q
        for idx0 in range(self.sequences.fluxes._qv_length):
            self.sequences.fluxes._qv_sum[idx0] = \
self.sequences.fluxes._qv_sum[idx0] + self.sequences.fluxes.qv[idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> lines.pyx.clear()
>>> pyxwriter.addup_fluxes(lines)
            . addup_fluxes
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void addup_fluxes(self) nogil:
        cdef ...int... idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.sequences.fluxes._q_sum[idx0, idx1] = \
self.sequences.fluxes._q_sum[idx0, idx1] + self.sequences.fluxes.q[idx0, idx1]
        for idx0 in range(self.sequences.fluxes._qv_length):
            self.sequences.fluxes._qv_sum[idx0] = \
self.sequences.fluxes._qv_sum[idx0] + self.sequences.fluxes.qv[idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.addup_fluxes(lines)
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.

Method |ELSModel.calculate_error|:

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 0
>>> lines.pyx.clear()
>>> pyxwriter.calculate_error(lines)
            . calculate_error
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void calculate_error(self) nogil:
        cdef ...int... idx0
        cdef double abserror
        self.numvars.abserror = 0.
        if self.numvars.use_relerror:
            self.numvars.relerror = 0.
        else:
            self.numvars.relerror = inf
        abserror = fabs(\
self.sequences.fluxes._q_results[self.numvars.idx_method]-\
self.sequences.fluxes._q_results[self.numvars.idx_method-1])
        self.numvars.abserror = max(self.numvars.abserror, abserror)
        if self.numvars.use_relerror:
            if self.sequences.fluxes._q_results[self.numvars.idx_method] == 0.:
                self.numvars.relerror = inf
            else:
                self.numvars.relerror = max(self.numvars.relerror, \
fabs(abserror/self.sequences.fluxes._q_results[self.numvars.idx_method]))
        for idx0 in range(self.sequences.fluxes._qv_length):
            abserror = fabs(\
self.sequences.fluxes._qv_results[self.numvars.idx_method, idx0]-\
self.sequences.fluxes._qv_results[self.numvars.idx_method-1, idx0])
            self.numvars.abserror = max(self.numvars.abserror, abserror)
            if self.numvars.use_relerror:
                if self.sequences.fluxes._qv_results\
[self.numvars.idx_method, idx0] == 0.:
                    self.numvars.relerror = inf
                else:
                    self.numvars.relerror = max(self.numvars.relerror, \
fabs(abserror/self.sequences.fluxes._qv_results[self.numvars.idx_method, idx0]))
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> lines.pyx.clear()
>>> pyxwriter.calculate_error(lines)
            . calculate_error
>>> lines.pyx  # doctest: +ELLIPSIS
    cpdef inline void calculate_error(self) nogil:
        cdef ...int... idx0, idx1
        cdef double abserror
        self.numvars.abserror = 0.
        if self.numvars.use_relerror:
            self.numvars.relerror = 0.
        else:
            self.numvars.relerror = inf
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                abserror = fabs(\
self.sequences.fluxes._q_results[self.numvars.idx_method, idx0, idx1]-\
self.sequences.fluxes._q_results[self.numvars.idx_method-1, idx0, idx1])
                self.numvars.abserror = max(self.numvars.abserror, abserror)
                if self.numvars.use_relerror:
                    if self.sequences.fluxes._q_results\
[self.numvars.idx_method, idx0, idx1] == 0.:
                        self.numvars.relerror = inf
                    else:
                        self.numvars.relerror = max(self.numvars.relerror, fabs(\
abserror/self.sequences.fluxes._q_results[self.numvars.idx_method, idx0, idx1]))
        for idx0 in range(self.sequences.fluxes._qv_length):
            abserror = fabs(\
self.sequences.fluxes._qv_results[self.numvars.idx_method, idx0]-\
self.sequences.fluxes._qv_results[self.numvars.idx_method-1, idx0])
            self.numvars.abserror = max(self.numvars.abserror, abserror)
            if self.numvars.use_relerror:
                if self.sequences.fluxes._qv_results\
[self.numvars.idx_method, idx0] == 0.:
                    self.numvars.relerror = inf
                else:
                    self.numvars.relerror = max(\
self.numvars.relerror, \
fabs(abserror/self.sequences.fluxes._qv_results[self.numvars.idx_method, idx0]))
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.calculate_error(lines)
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.
"""
# import...
# ...from standard library
from __future__ import annotations
import copy

# pylint: enable=no-name-in-module
# pylint: enable=import-error
import functools
import importlib
import inspect
import math
import os
import platform
import shutil
import sys
import types

# ...third party modules
import numpy
from numpy import inf  # pylint: disable=unused-import
from numpy import nan  # pylint: disable=unused-import
import setuptools

# ...from HydPy
import hydpy
from hydpy import config
from hydpy import cythons
from hydpy.core import exceptiontools
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import testtools
from hydpy.core.typingtools import *


if TYPE_CHECKING:
    import Cython.Build as build
else:
    build = exceptiontools.OptionalImport("build", ["Cython.Build"], locals())


def get_dllextension() -> str:
    """Return the DLL file extension for the current operating system.

    The returned value depends on the response of function |platform.system| of module
    |platform|.  |get_dllextension| returns `.pyd` if |platform.system| returns the
    string "windows" and `.so` for all other strings:

    >>> from hydpy.cythons.modelutils import get_dllextension
    >>> import platform
    >>> from unittest import mock
    >>> with mock.patch.object(
    ...     platform, "system", side_effect=lambda: "Windows") as mocked:
    ...     get_dllextension()
    '.pyd'
    >>> with mock.patch.object(
    ...     platform, "system", side_effect=lambda: "Linux") as mocked:
    ...     get_dllextension()
    '.so'
    """
    if platform.system().lower() == "windows":
        return ".pyd"
    return ".so"


_dllextension = get_dllextension()

_int = "numpy." + str(numpy.array([1]).dtype) + "_t"

TYPE2STR: Dict[Union[Type[Any], str, None], str] = {  # pylint: disable=duplicate-key
    bool: "numpy.npy_bool",
    "bool": "numpy.npy_bool",
    int: _int,
    "int": _int,
    parametertools.IntConstant: _int,
    "parametertools.IntConstant": _int,
    "IntConstant": _int,
    float: "double",
    "float": "double",
    str: "str",
    "str": "str",
    None: "void",
    "None": "void",
    type(None): "void",
    Vector: "double[:]",  # to be removed as soon as possible
    "Vector": "double[:]",
    "Vector": "double[:]",
    VectorFloat: "double[:]",  # This works because the `__getitem__`
    # of `_ProtocolMeta` is decorated by `_tp_cache`.  I don't know if this caching
    # is documented behaviour, so this might cause (little) trouble in the future.
    "VectorFloat": "double[:]",
    "VectorFloat": "double[:]",
}
"""Maps Python types to Cython compatible type declarations.

The Cython type belonging to Python's |int| is selected to agree with numpy's default 
integer type on the current platform/system.
"""

_checkable_types: List[Type[Any]] = []
for maybe_a_type in TYPE2STR:
    try:
        isinstance(1, maybe_a_type)  # type: ignore[arg-type]
    except TypeError:
        continue
    assert isinstance(maybe_a_type, type)
    _checkable_types.append(maybe_a_type)
CHECKABLE_TYPES: Tuple[Type[Any], ...] = tuple(_checkable_types)
""""Real types" of |TYPE2STR| allowed as second arguments of function |isinstance|."""
del _checkable_types

NDIM2STR = {0: "", 1: "[:]", 2: "[:,:]", 3: "[:,:,:]"}

_nogil = " nogil" if config.FASTCYTHON else ""


class Lines(List[str]):
    """Handles the code lines for a `.pyx` or a `pxd` file."""

    def __init__(self, *args: str) -> None:
        super().__init__(args)

    def add(self, indent: int, line: Mayberable1[str]) -> None:
        """Append the given text line with prefixed spaces following the given number
        of indentation levels."""
        if isinstance(line, str):
            self.append(indent * 4 * " " + line)
        else:
            for subline in line:
                self.append(indent * 4 * " " + subline)

    def __repr__(self) -> str:
        return "\n".join(self) + "\n"


class PyxPxdLines:
    """Handles the code lines for a `.pyx` and a `pxd` file."""

    pyx: Lines
    pxd: Lines

    def __init__(self) -> None:
        self.pyx = Lines()
        self.pxd = Lines()

    def add(self, indent: int, line: str) -> None:
        """Pass the given data to method |Lines.add| of the `pyx` and `pxd` |Lines|
        instances."""
        self.pyx.add(indent, line)
        if line.endswith(":") and (" class " not in line):
            line = line[:-1]
        self.pxd.add(indent, line)


def get_methodheader(
    methodname: str, nogil: bool = False, idxarg: bool = False, inline: bool = True
) -> str:
    """Returns the Cython method header for methods without arguments except`self`.

    Note the influence of the configuration flag `FASTCYTHON`:

    >>> from hydpy.cythons.modelutils import get_methodheader
    >>> from hydpy import config
    >>> config.FASTCYTHON = False
    >>> print(get_methodheader("test", nogil=True, idxarg=False, inline=True))
    cpdef inline void test(self):
    >>> config.FASTCYTHON = True
    >>> methodheader = get_methodheader("test", nogil=True, idxarg=True, inline=False)
    >>> print(methodheader)  # doctest: +ELLIPSIS
    cpdef void test(self, ...int... idx) nogil:
    """
    if not config.FASTCYTHON:
        nogil = False
    nogil_ = " nogil" if nogil else ""
    idxarg_ = f", {_int} idx" if idxarg else ""
    inline_ = " inline" if inline else ""
    return f"cpdef{inline_} void {methodname}(self{idxarg_}){nogil_}:"


def decorate_method(
    wrapped: Callable[[PyxWriter], Iterator[str]]
) -> Callable[[PyxWriter, PyxPxdLines], None]:
    """The decorated method returns a |Lines| object including a method header.
    However, the |Lines| object is empty if the respective model does not implement a
    method with the same name as the wrapped method.
    """

    def wrapper(self: PyxWriter, lines: PyxPxdLines) -> None:
        if hasattr(self.model, wrapped.__name__):
            print(f"            . {wrapped.__name__}")
            pyx, both = lines.pyx.add, lines.add
            both(1, get_methodheader(wrapped.__name__, nogil=True))
            for line in wrapped(self):
                pyx(2, line)

    functools.update_wrapper(wrapper, wrapped)
    return wrapper


def compile_(cyname: str, pyxfilepath: str, buildpath: str) -> None:
    """Translate Cython code to C code and compile it."""
    argv = copy.deepcopy(sys.argv)
    try:
        sys.argv = [
            sys.argv[0],
            "build_ext",
            f"--build-lib={buildpath}",
            f"--build-temp={buildpath}",
        ]
        print(sys.argv)
        exc_modules = [
            setuptools.Extension(
                name=f"hydpy.cythons.autogen.{cyname}",
                sources=[pyxfilepath],
                extra_compile_args=["-O2"],
            )
        ]
        setuptools.setup(
            ext_modules=build.cythonize(exc_modules), include_dirs=[numpy.get_include()]
        )
    finally:
        sys.argv = argv


def move_dll(pyname: str, cyname: str, cydirpath: str, buildpath: str) -> None:
    """Try to find the DLL file created by function |compile_| and try to move it to
    the `autogen` folder of the `cythons` subpackage.

    Usually, one does not need to apply |move_dll| directly.  However, if you are a
    model developer, you might see one of the following error messages from time to
    time:

    >>> from hydpy.cythons.modelutils import move_dll
    >>> from hydpy.models.hland_v1 import cythonizer as c
    >>> move_dll(pyname=c.pyname, cyname=c.cyname,
    ...          cydirpath=c.cydirpath, buildpath=c.buildpath)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    OSError: After trying to cythonize `hland_v1`, the resulting file `c_hland_v1...` \
could not be found in directory `.../hydpy/cythons/autogen/_build` nor any of its \
subdirectories.  The distutil report should tell whether the file has been stored \
somewhere else, is named somehow else, or could not be build at all.

    >>> import os
    >>> from unittest import mock
    >>> from hydpy import TestIO
    >>> with TestIO():   # doctest: +ELLIPSIS
    ...     with mock.patch.object(
    ...             type(c), "buildpath", new_callable=mock.PropertyMock
    ...     ) as mocked_buildpath:
    ...         mocked_buildpath.return_value = "_build"
    ...         os.makedirs("_build/subdir", exist_ok=True)
    ...         filepath = f"_build/subdir/c_hland_v1{get_dllextension()}"
    ...         with open(filepath, "w"):
    ...             pass
    ...         with mock.patch(
    ...                 "shutil.move",
    ...                 side_effect=PermissionError("Denied!")):
    ...             move_dll(pyname=c.pyname, cyname=c.cyname,
    ...                      cydirpath=c.cydirpath, buildpath=c.buildpath)
    Traceback (most recent call last):
    ...
    PermissionError: After trying to cythonize `hland_v1`, when trying to move the \
final cython module `c_hland_v1...` from directory `_build` to directory \
`.../hydpy/cythons/autogen`, the following error occurred: Denied! A likely error \
cause is that the cython module `c_hland_v1...` does already exist in this directory \
and is currently blocked by another Python process.  Maybe it helps to close all \
Python processes and restart the cythonization afterwards.
    """
    dirinfos = os.walk(buildpath)
    system_dependent_filename = None
    for dirinfo in dirinfos:
        for filename in dirinfo[2]:
            if filename.startswith(cyname) and filename.endswith(_dllextension):
                system_dependent_filename = filename
                break
        if system_dependent_filename:
            try:
                shutil.move(
                    os.path.join(dirinfo[0], system_dependent_filename),
                    os.path.join(cydirpath, cyname + _dllextension),
                )
                break
            except BaseException:
                objecttools.augment_excmessage(
                    f"After trying to cythonize `{pyname}`, when trying to move the "
                    f"final cython module `{system_dependent_filename}` from "
                    f"directory `{buildpath}` to directory "
                    f"`{objecttools.repr_(cydirpath)}`",
                    f"A likely error cause is that the cython module "
                    f"`{cyname}{_dllextension}` does already exist in this directory "
                    f"and is currently blocked by another Python process.  Maybe it "
                    f"helps to close all Python processes and restart the "
                    f"cythonization afterwards.",
                )
    else:
        raise IOError(
            f"After trying to cythonize `{pyname}`, the resulting file "
            f"`{cyname}{_dllextension}` could not be found in directory "
            f"`{objecttools.repr_(buildpath)}` nor any of its subdirectories.  The "
            f"distutil report should tell whether the file has been stored somewhere "
            f"else, is named somehow else, or could not be build at all."
        )


class Cythonizer:
    """Handles the writing, compiling and initialisation of Cython models."""

    Model: Type[modeltools.Model]
    Parameters: Type[parametertools.Parameters]
    Sequences: Type[sequencetools.Sequences]
    tester: testtools.Tester
    pymodule: str
    _cymodule: Optional[types.ModuleType]

    def __init__(self) -> None:
        self._cymodule = None
        frame = inspect.currentframe()
        assert frame is not None
        frame = frame.f_back
        assert frame is not None
        self.pymodule = frame.f_globals["__name__"]
        for key, value in frame.f_locals.items():
            setattr(self, key, value)

    def cythonize(self) -> None:
        """Translate Python source code of the relevant model first into Cython and
        then into C, compile it, and move the resulting dll file to the `autogen`
        subfolder of subpackage `cythons`."""
        print(f"Translate module/package {self.pyname}.")
        self.pyxwriter.write()
        print(f"Compile module {self.cyname}.")
        compile_(
            cyname=self.cyname, pyxfilepath=self.pyxfilepath, buildpath=self.buildpath
        )
        move_dll(
            pyname=self.pyname,
            cyname=self.cyname,
            cydirpath=self.cydirpath,
            buildpath=self.buildpath,
        )

    @property
    def pyname(self) -> str:
        """Name of the original Python module or package.

        >>> from hydpy.models.hland import cythonizer
        >>> cythonizer.pyname
        'hland'
        >>> from hydpy.models.hland_v1 import cythonizer
        >>> cythonizer.pyname
        'hland_v1'
        """
        return self.pymodule.split(".")[-1]

    @property
    def cyname(self) -> str:
        """Name of the compiled module.

        >>> from hydpy.models.hland import cythonizer
        >>> cythonizer.cyname
        'c_hland'
        >>> from hydpy.models.hland_v1 import cythonizer
        >>> cythonizer.cyname
        'c_hland_v1'
        """
        return "c_" + self.pyname

    @property
    def cydirpath(self) -> str:
        """The absolute path of the directory containing the compiled modules.

        >>> from hydpy.models.hland import cythonizer
        >>> from hydpy import repr_
        >>> repr_(cythonizer.cydirpath)   # doctest: +ELLIPSIS
        '.../hydpy/cythons/autogen'
        >>> import os
        >>> os.path.exists(cythonizer.cydirpath)
        True
        """
        return cythons.autogen.__path__[0]

    @property
    def cymodule(self) -> types.ModuleType:
        """The compiled module.

        Property |Cythonizer.cymodule| returns the relevant DLL module:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy.cythons.autogen import c_hland_v1
        >>> c_hland_v1 is cythonizer.cymodule
        True

        However, if this module is missing for some reasons, it tries to create the
        module first and returns it afterwards.  For demonstration purposes, we define
        a wrong |Cythonizer.cyname|:

        >>> from hydpy.cythons.modelutils import Cythonizer
        >>> cyname = Cythonizer.cyname
        >>> Cythonizer.cyname = "wrong"
        >>> cythonizer._cymodule = None
        >>> from unittest import mock
        >>> with mock.patch.object(Cythonizer, "cythonize") as mock:
        ...     cythonizer.cymodule
        Traceback (most recent call last):
        ...
        ModuleNotFoundError: No module named 'hydpy.cythons.autogen.wrong'
        >>> mock.call_args_list
        [call()]

        >>> Cythonizer.cyname = cyname
        """
        cymodule = self._cymodule
        if cymodule:
            return cymodule
        modulepath = f"hydpy.cythons.autogen.{self.cyname}"
        try:
            self._cymodule = importlib.import_module(modulepath)
        except ModuleNotFoundError:
            self.cythonize()
            self._cymodule = importlib.import_module(modulepath)
        return self._cymodule

    @property
    def pyxfilepath(self) -> str:
        """The absolute path of the compiled module.

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy import repr_
        >>> repr_(cythonizer.pyxfilepath)   # doctest: +ELLIPSIS
        '.../hydpy/cythons/autogen/c_hland_v1.pyx'
        >>> import os
        >>> os.path.exists(cythonizer.pyxfilepath)
        True
        """
        return os.path.join(self.cydirpath, f"{self.cyname}.pyx")

    @property
    def dllfilepath(self) -> str:
        """The absolute path of the compiled module.

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy import repr_
        >>> repr_(cythonizer.dllfilepath)   # doctest: +ELLIPSIS
        '.../hydpy/cythons/autogen/c_hland_v1...'
        >>> import os
        >>> os.path.exists(os.path.split(cythonizer.dllfilepath)[0])
        True
        """
        return os.path.join(self.cydirpath, f"{self.cyname}{_dllextension}")

    @property
    def buildpath(self) -> str:
        """The absolute path for temporarily build files.

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy import repr_
        >>> repr_(cythonizer.buildpath)   # doctest: +ELLIPSIS
        '.../hydpy/cythons/autogen/_build'
        """
        return os.path.join(self.cydirpath, "_build")

    @property
    def pyxwriter(self) -> PyxWriter:
        """A new |PyxWriter| instance.

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> pyxwriter = cythonizer.pyxwriter
        >>> from hydpy import classname
        >>> classname(pyxwriter)
        'PyxWriter'
        >>> cythonizer.pyxwriter is pyxwriter
        False
        """
        model = self.Model()
        dict_ = vars(self)
        dict_["model"] = model
        model.parameters = importtools.prepare_parameters(dict_)
        model.sequences = importtools.prepare_sequences(dict_)
        return PyxWriter(self, model, self.pyxfilepath)


class PyxWriter:
    """Translates the source code of Python models into Cython source code.

    Method |PyxWriter| serves as a master method, which triggers the complete writing
    process.  The other properties and methods supply the required code lines.  Their
    names are selected to match the names of the original Python models as close as
    possible.
    """

    cythonizer: Cythonizer
    model: modeltools.Model
    pyxpath: str
    pxdpath: str

    def __init__(
        self, cythonizer: Cythonizer, model: modeltools.Model, pyxpath: str
    ) -> None:
        self.cythonizer = cythonizer
        self.model = model
        self.pyxpath = pyxpath
        self.pxdpath = pyxpath.replace(".pyx", ".pxd")

    def write(self) -> None:
        """Collect the source code and write it into a Cython extension file ("pyx")
        and its definition file ("pxd")."""

        lines = PyxPxdLines()

        print("    * cython options")
        self.cythondistutilsoptions(lines)
        print("    * C imports")
        self.cimports(lines)
        print("        - callback features")
        self.callbackfeatures(lines)
        print("    * constants (if defined)")
        self.constants(lines)
        print("    * parameter classes")
        self.parameters(lines)
        print("    * sequence classes")
        self.sequences(lines)
        print("    * numerical parameters")
        self.numericalparameters(lines)
        print("    * submodel classes")
        self.submodels(lines)
        print("    * model class")
        print("        - model attributes")
        self.modeldeclarations(lines)
        print("        - standard functions")
        self.modelstandardfunctions(lines)
        print("        - numeric functions")
        self.modelnumericfunctions(lines)
        print("        - additional functions")
        self.modeluserfunctions(lines)

        with open(self.pyxpath, "w", encoding=config.ENCODING) as pyxfile:
            pyxfile.write(repr(lines.pyx))
        with open(self.pxdpath, "w", encoding=config.ENCODING) as pxdfile:
            pxdfile.write(repr(lines.pxd))

    def cythondistutilsoptions(self, lines: PyxPxdLines) -> None:
        """Cython and Distutils option lines.

        Use the configuration options "FASTCYTHON" and "PROFILECYTHON" to configure the
        cythonization processes as follows:

        >>> from hydpy.cythons.modelutils import PyxWriter
        >>> pyxwriter = PyxWriter(None, None, "file.pyx")
        >>> from hydpy.cythons.modelutils import PyxPxdLines
        >>> lines = PyxPxdLines()
        >>> pyxwriter.cythondistutilsoptions(lines)
        >>> lines.pyx  # doctest: +ELLIPSIS
        #!python
        # distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION
        # cython: language_level=3
        # cython: cpow=True
        # cython: boundscheck=False
        # cython: wraparound=False
        # cython: initializedcheck=False
        # cython: cdivision=True
        <BLANKLINE>

        >>> from hydpy import config
        >>> config.FASTCYTHON = False
        >>> config.PROFILECYTHON = True
        >>> lines.pyx.clear()
        >>> pyxwriter.cythondistutilsoptions(lines)
        >>> lines.pyx  # doctest: +ELLIPSIS
        #!python
        # distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION
        # cython: language_level=3
        # cython: cpow=True
        # cython: boundscheck=True
        # cython: wraparound=True
        # cython: initializedcheck=True
        # cython: cdivision=False
        # cython: linetrace=True
        # distutils: define_macros=CYTHON_TRACE=1
        # distutils: define_macros=CYTHON_TRACE_NOGIL=1
        <BLANKLINE>

        >>> config.FASTCYTHON = True
        >>> config.PROFILECYTHON = False
        """

        # ToDo: do not share code with prepare.__prepare_cythonoptions

        both = lines.add

        both(0, "#!python")
        both(0, "# distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION")
        both(0, "# cython: language_level=3")
        both(0, "# cython: cpow=True")

        if config.FASTCYTHON:
            both(0, "# cython: boundscheck=False")
            both(0, "# cython: wraparound=False")
            both(0, "# cython: initializedcheck=False")
            both(0, "# cython: cdivision=True")
        else:
            both(0, "# cython: boundscheck=True")
            both(0, "# cython: wraparound=True")
            both(0, "# cython: initializedcheck=True")
            both(0, "# cython: cdivision=False")

        if config.PROFILECYTHON:
            both(0, "# cython: linetrace=True")
            both(0, "# distutils: define_macros=CYTHON_TRACE=1")
            both(0, "# distutils: define_macros=CYTHON_TRACE_NOGIL=1")

    def cimports(self, lines: PyxPxdLines) -> None:
        """Import command lines."""
        add = lines.add
        add(0, "from typing import Optional")
        add(0, "import numpy")
        add(0, "cimport numpy")
        add(
            0,
            "from libc.math cimport exp, fabs, log, sin, cos, tan, asin, acos, atan, "
            "isnan, isinf",
        )
        add(0, "from libc.math cimport NAN as nan")
        add(0, "from libc.math cimport INFINITY as inf")
        add(0, "import cython")
        add(0, "from cpython.mem cimport PyMem_Malloc")
        add(0, "from cpython.mem cimport PyMem_Realloc")
        add(0, "from cpython.mem cimport PyMem_Free")
        add(0, "from hydpy.cythons.autogen cimport configutils")
        add(0, "from hydpy.cythons.autogen cimport interfaceutils")
        add(0, "from hydpy.cythons.autogen cimport interputils")
        add(0, "from hydpy.cythons.autogen import pointerutils")
        add(0, "from hydpy.cythons.autogen cimport pointerutils")
        add(0, "from hydpy.cythons.autogen cimport quadutils")
        add(0, "from hydpy.cythons.autogen cimport rootutils")
        add(0, "from hydpy.cythons.autogen cimport smoothutils")
        add(0, "from hydpy.cythons.autogen cimport masterinterface")

    def constants(self, lines: PyxPxdLines) -> None:
        """Constants declaration lines."""
        both = lines.add
        for name, member in vars(self.cythonizer).items():
            if (
                name.isupper()
                and not inspect.isclass(member)
                and isinstance(member, CHECKABLE_TYPES)
            ):
                ndim = numpy.array(member).ndim
                ctype = TYPE2STR[type(member)] + NDIM2STR[ndim]
                both(0, f"cdef public {ctype} {name} = {member}")

    def parameters(self, lines: PyxPxdLines) -> None:
        """Parameter declaration lines."""
        if self.model.parameters:
            pyx, pxd, both = lines.pyx.add, lines.pxd.add, lines.add
            both(0, "@cython.final")
            both(0, "cdef class Parameters:")
            pyx(1, "pass")
            if not self.model.parameters:
                pxd(1, "pass")
            for subpars in self.model.parameters:
                pxd(1, f"cdef public {type(subpars).__name__} {subpars.name}")
            for subpars in self.model.parameters:
                print(f"        - {subpars.name}")
                both(0, "@cython.final")
                both(0, f"cdef class {type(subpars).__name__}:")
                pyx(1, "pass")
                for par in subpars:
                    try:
                        ctype = TYPE2STR[par.TYPE] + NDIM2STR[par.NDIM]
                    except KeyError:
                        ctype = par.TYPE + NDIM2STR[par.NDIM]
                    pxd(1, f"cdef public {ctype} {par.name}")
                    if isinstance(par, parametertools.KeywordParameter1D):
                        pxd(1, f"cdef public {TYPE2STR[int]} _{par.name}_entrymin")
                    elif isinstance(par, parametertools.KeywordParameter2D):
                        prefix = f"cdef public {TYPE2STR[int]} _{par.name}"
                        for suffix in ("rowmin", "columnmin"):
                            pxd(1, f"{prefix}_{suffix}")

    def sequences(self, lines: PyxPxdLines) -> None:
        """Sequence declaration lines."""
        sqt = sequencetools
        pyx, pxd, both = lines.pyx.add, lines.pxd.add, lines.add
        both(0, "@cython.final")
        both(0, "cdef class Sequences:")
        pyx(1, "pass")
        for subseqs in self.model.sequences:
            pxd(1, f"cdef public {type(subseqs).__name__} {subseqs.name}")
        if self.model.sequences.states:
            pxd(1, "cdef public StateSequences old_states")
            pxd(1, "cdef public StateSequences new_states")
        for subseqs in self.model.sequences:
            print(f"        - {subseqs.name}")
            both(0, "@cython.final")
            both(0, f"cdef class {type(subseqs).__name__}:")
            if isinstance(subseqs, (sqt.LogSequences, sqt.AideSequences)):
                pyx(1, "pass")
            for seq in subseqs:
                ctype = f"double{NDIM2STR[seq.NDIM]}"
                if isinstance(subseqs, sqt.LinkSequences):
                    if seq.NDIM == 0:
                        pxd(1, f"cdef double *{seq.name}")
                    elif seq.NDIM == 1:
                        pxd(1, f"cdef double **{seq.name}")
                        pxd(1, f"cdef public {_int} len_{seq.name}")
                        pxd(1, f"cdef public {TYPE2STR[int]}[:] _{seq.name}_ready")
                else:
                    pxd(1, f"cdef public {ctype} {seq.name}")
                pxd(1, f"cdef public {_int} _{seq.name}_ndim")
                pxd(1, f"cdef public {_int} _{seq.name}_length")
                for idx in range(seq.NDIM):
                    pxd(1, f"cdef public {_int} _{seq.name}_length_{idx}")
                if seq.NUMERIC:
                    ctype_numeric = "double" + NDIM2STR[seq.NDIM + 1]
                    pxd(1, f"cdef public {ctype_numeric} _{seq.name}_points")
                    pxd(1, f"cdef public {ctype_numeric} _{seq.name}_results")
                    if isinstance(subseqs, sqt.FluxSequences):
                        pxd(1, f"cdef public {ctype_numeric} " f"_{seq.name}_integrals")
                        pxd(1, f"cdef public {ctype} _{seq.name}_sum")
                if isinstance(seq, sqt.IOSequence):
                    self.iosequence(lines, seq)
            if isinstance(subseqs, sqt.IOSequences):
                self.load_data(lines, subseqs)
                self.save_data(lines, subseqs)
            if isinstance(subseqs, sqt.LinkSequences):
                self.set_pointer(lines, subseqs)
                self.get_value(lines, subseqs)
                self.set_value(lines, subseqs)
            if isinstance(subseqs, (sqt.InputSequences, sqt.OutputSequences)):
                self.set_pointer(lines, subseqs)
            if isinstance(subseqs, sqt.OutputSequences):
                self.update_outputs(lines, subseqs)

    @staticmethod
    def iosequence(lines: PyxPxdLines, seq: sequencetools.IOSequence) -> None:
        """Declaration lines for the given |IOSequence| object."""
        ctype = f"double{NDIM2STR[seq.NDIM+1]}"
        add = lines.pxd.add
        add(1, f"cdef public bint _{seq.name}_ramflag")
        add(1, f"cdef public {ctype} _{seq.name}_array")
        add(1, f"cdef public bint _{seq.name}_diskflag_reading")
        add(1, f"cdef public bint _{seq.name}_diskflag_writing")
        add(1, f"cdef public double[:] _{seq.name}_ncarray")
        if isinstance(seq, sequencetools.InputSequence) and (seq.NDIM == 0):
            add(1, f"cdef public bint _{seq.name}_inputflag")
            add(1, f"cdef double *_{seq.name}_inputpointer")
        elif isinstance(seq, sequencetools.OutputSequence) and (seq.NDIM == 0):
            add(1, f"cdef public bint _{seq.name}_outputflag")
            add(1, f"cdef double *_{seq.name}_outputpointer")

    @staticmethod
    def _get_index(ndim: int) -> str:
        return ", ".join(f"jdx{idx}" for idx in range(ndim))

    @staticmethod
    def _add_cdef_jdxs(
        lines: PyxPxdLines, subseqs: sequencetools.IOSequences[Any, Any, Any]
    ) -> None:
        maxndim = max(seq.NDIM for seq in subseqs)
        if maxndim:
            jdxs = ", ".join(f"jdx{ndim}" for ndim in range(maxndim))
            lines.pyx.add(2, f"cdef {_int} {jdxs}")

    @classmethod
    def load_data(
        cls, lines: PyxPxdLines, subseqs: sequencetools.IOSequences[Any, Any, Any]
    ) -> None:
        """Load data statements."""
        print("            . load_data")
        pyx, both = lines.pyx.add, lines.add
        both(1, f"cpdef inline void load_data(self, {_int} idx) {_nogil}:")
        cls._add_cdef_jdxs(lines, subseqs)
        pyx(2, f"cdef {_int} k")
        for seq in subseqs:
            if isinstance(seq, sequencetools.InputSequence) and (seq.NDIM == 0):
                pyx(2, f"if self._{seq.name}_inputflag:")
                pyx(3, f"self.{seq.name} = self._{seq.name}_inputpointer[0]")
                if_or_elif = "elif"
            else:
                if_or_elif = "if"
            pyx(2, f"{if_or_elif} self._{seq.name}_diskflag_reading:")
            if seq.NDIM == 0:
                pyx(3, f"self.{seq.name} = self._{seq.name}_ncarray[0]")
            else:
                pyx(3, "k = 0")
                for idx in range(seq.NDIM):
                    pyx(
                        3 + idx,
                        f"for jdx{idx} in range(self._{seq.name}_length_{idx}):",
                    )
                pyx(
                    3 + seq.NDIM,
                    f"self.{seq.name}[{cls._get_index(seq.NDIM)}] "
                    f"= self._{seq.name}_ncarray[k]",
                )
                pyx(3 + seq.NDIM, "k += 1")
            pyx(2, f"elif self._{seq.name}_ramflag:")
            if seq.NDIM == 0:
                pyx(3, f"self.{seq.name} = self._{seq.name}_array[idx]")
            else:
                for idx in range(seq.NDIM):
                    pyx(
                        3 + idx,
                        f"for jdx{idx} in " f"range(self._{seq.name}_length_{idx}):",
                    )
                index = cls._get_index(seq.NDIM)
                pyx(
                    3 + seq.NDIM,
                    f"self.{seq.name}[{index}] = self._{seq.name}_array[idx, {index}]",
                )

    @classmethod
    def save_data(
        cls, lines: PyxPxdLines, subseqs: sequencetools.IOSequences[Any, Any, Any]
    ) -> None:
        """Save data statements."""
        print("            . save_data")
        pyx, both = lines.pyx.add, lines.add
        both(1, f"cpdef inline void save_data(self, {_int} idx) {_nogil}:")
        cls._add_cdef_jdxs(lines, subseqs)
        pyx(2, f"cdef {_int} k")
        for seq in subseqs:
            pyx(2, f"if self._{seq.name}_diskflag_writing:")
            if seq.NDIM == 0:
                pyx(3, f"self._{seq.name}_ncarray[0] = self.{seq.name}")
            else:
                pyx(3, "k = 0")
                for idx in range(seq.NDIM):
                    pyx(
                        3 + idx,
                        f"for jdx{idx} in " f"range(self._{seq.name}_length_{idx}):",
                    )
                index = cls._get_index(seq.NDIM)
                pyx(
                    3 + seq.NDIM,
                    f"self._{seq.name}_ncarray[k] = self.{seq.name}[{index}]",
                )
                pyx(3 + seq.NDIM, "k += 1")
            pyx(2, f"if self._{seq.name}_ramflag:")
            if seq.NDIM == 0:
                pyx(3, f"self._{seq.name}_array[idx] = self.{seq.name}")
            else:
                for idx in range(seq.NDIM):
                    pyx(
                        3 + idx,
                        f"for jdx{idx} in " f"range(self._{seq.name}_length_{idx}):",
                    )
                index = cls._get_index(seq.NDIM)
                pyx(
                    3 + seq.NDIM,
                    f"self._{seq.name}_array[idx, {index}] = self.{seq.name}[{index}]",
                )

    def set_pointer(
        self,
        lines: PyxPxdLines,
        subseqs: Union[
            sequencetools.InputSequences,
            sequencetools.OutputSequences[Any],
            sequencetools.LinkSequences[Any],
        ],
    ) -> None:
        """Set pointer statements for all input, output, and link sequences."""
        if isinstance(subseqs, sequencetools.InputSequences):
            self.set_pointerinput(lines, subseqs)
        elif isinstance(subseqs, sequencetools.OutputSequences):
            self.set_pointeroutput(lines, subseqs)
        else:
            if any(seq.NDIM == 0 for seq in subseqs):
                self.set_pointer0d(lines, subseqs)
            if any(seq.NDIM == 1 for seq in subseqs):
                self.alloc(lines, subseqs)
                self.dealloc(lines, subseqs)
                self.set_pointer1d(lines, subseqs)

    @staticmethod
    def set_pointer0d(
        lines: PyxPxdLines, subseqs: sequencetools.LinkSequences[Any]
    ) -> None:
        """Set pointer statements for 0-dimensional link sequences."""
        print("            . set_pointer0d")
        pyx, both = lines.pyx.add, lines.add
        both(
            1,
            "cpdef inline set_pointer0d(self, str name, pointerutils.Double value):",
        )
        pyx(2, "cdef pointerutils.PDouble pointer = pointerutils.PDouble(value)")
        for seq in (seq for seq in subseqs if seq.NDIM == 0):
            pyx(2, f'if name == "{seq.name}":')
            pyx(3, f"self.{seq.name} = pointer.p_value")

    @staticmethod
    def get_value(
        lines: PyxPxdLines, subseqs: sequencetools.LinkSequences[Any]
    ) -> None:
        """Get value statements for link sequences."""
        print("            . get_value")
        pyx, both = lines.pyx.add, lines.add
        both(1, "cpdef get_value(self, str name):")
        pyx(2, f"cdef {_int} idx")
        for seq in subseqs:
            pyx(2, f'if name == "{seq.name}":')
            if seq.NDIM == 0:
                pyx(3, f"return self.{seq.name}[0]")
            elif seq.NDIM == 1:
                pyx(3, f"values = numpy.empty(self.len_{seq.name})")
                pyx(3, f"for idx in range(self.len_{seq.name}):")
                PyxWriter._check_pointer(lines, seq)
                pyx(4, f"values[idx] = self.{seq.name}[idx][0]")
                pyx(3, "return values")

    @staticmethod
    def set_value(
        lines: PyxPxdLines, subseqs: sequencetools.LinkSequences[Any]
    ) -> None:
        """Set value statements for link sequences."""
        print("            . set_value")
        pyx, both = lines.pyx.add, lines.add
        both(1, "cpdef set_value(self, str name, value):")
        for seq in subseqs:
            pyx(2, f'if name == "{seq.name}":')
            if seq.NDIM == 0:
                pyx(3, f"self.{seq.name}[0] = value")
            elif seq.NDIM == 1:
                pyx(3, f"for idx in range(self.len_{seq.name}):")
                PyxWriter._check_pointer(lines, seq)
                pyx(4, f"self.{seq.name}[idx][0] = value[idx]")

    @staticmethod
    def _check_pointer(lines: PyxPxdLines, seq: sequencetools.LinkSequence) -> None:
        pyx = lines.pyx.add
        pyx(4, f"pointerutils.check0(self._{seq.name}_length_0)")
        pyx(4, f"if self._{seq.name}_ready[idx] == 0:")
        pyx(5, f"pointerutils.check1(self._{seq.name}_length_0, idx)")
        pyx(5, f"pointerutils.check2(self._{seq.name}_ready, idx)")

    @staticmethod
    def alloc(lines: PyxPxdLines, subseqs: sequencetools.LinkSequences[Any]) -> None:
        """Allocate memory statements for 1-dimensional link sequences."""
        print("            . setlength")
        pyx, both = lines.pyx.add, lines.add
        both(1, f"cpdef inline alloc(self, name, {TYPE2STR[int]} length):")
        for seq in (seq for seq in subseqs if seq.NDIM == 1):
            pyx(2, f'if name == "{seq.name}":')
            pyx(3, f"self._{seq.name}_length_0 = length")
            pyx(
                3,
                f"self._{seq.name}_ready = "
                f"numpy.full(length, 0, dtype={ TYPE2STR[int].split('_')[0]})",
            )
            pyx(
                3,
                f"self.{seq.name} = "
                f"<double**> PyMem_Malloc(length * sizeof(double*))",
            )

    @staticmethod
    def dealloc(lines: PyxPxdLines, subseqs: sequencetools.LinkSequences[Any]) -> None:
        """Deallocate memory statements for 1-dimensional link sequences."""
        print("            . dealloc")
        pyx, both = lines.pyx.add, lines.add
        both(1, "cpdef inline dealloc(self, name):")
        for seq in (seq for seq in subseqs if seq.NDIM == 1):
            pyx(2, f'if name == "{seq.name}":')
            pyx(3, f"PyMem_Free(self.{seq.name})")

    @staticmethod
    def set_pointer1d(
        lines: PyxPxdLines, subseqs: sequencetools.LinkSequences[Any]
    ) -> None:
        """Set_pointer statements for 1-dimensional link sequences."""
        print("            . set_pointer1d")
        pyx, both = lines.pyx.add, lines.add
        both(
            1,
            "cpdef inline set_pointer1d"
            f"(self, str name, pointerutils.Double value, {_int} idx):",
        )
        pyx(2, "cdef pointerutils.PDouble pointer = pointerutils.PDouble(value)")
        for seq in (seq for seq in subseqs if seq.NDIM == 1):
            pyx(2, f'if name == "{seq.name}":')
            pyx(3, f"self.{seq.name}[idx] = pointer.p_value")
            pyx(3, f"self._{seq.name}_ready[idx] = 1")

    @classmethod
    def set_pointerinput(
        cls, lines: PyxPxdLines, subseqs: sequencetools.InputSequences
    ) -> None:
        """Set pointer statements for input sequences."""
        print("            . set_pointerinput")
        pyx, both = lines.pyx.add, lines.add
        both(
            1,
            "cpdef inline set_pointerinput"
            "(self, str name, pointerutils.PDouble value):",
        )
        subseqs_ = cls._filter_inputsequences(subseqs)
        if subseqs_:
            for seq in subseqs_:
                pyx(2, f'if name == "{seq.name}":')
                pyx(3, f"self._{seq.name}_inputpointer = value.p_value")
        else:
            pyx(2, "pass")

    @classmethod
    def set_pointeroutput(
        cls, lines: PyxPxdLines, subseqs: sequencetools.OutputSequences[Any]
    ) -> None:
        """Set pointer statements for output sequences."""
        print("            . set_pointeroutput")
        pyx, both = lines.pyx.add, lines.add
        both(
            1,
            "cpdef inline set_pointeroutput"
            "(self, str name, pointerutils.PDouble value):",
        )
        subseqs_ = cls._filter_outputsequences(subseqs)
        if subseqs_:
            for seq in subseqs_:
                pyx(2, f'if name == "{seq.name}":')
                pyx(3, f"self._{seq.name}_outputpointer = value.p_value")
        else:
            pyx(2, "pass")

    @staticmethod
    def _filter_inputsequences(
        subseqs: sequencetools.InputSequences,
    ) -> List[sequencetools.InputSequence]:
        return [subseq for subseq in subseqs if not subseq.NDIM]

    @staticmethod
    def _filter_outputsequences(
        subseqs: sequencetools.OutputSequences[Any],
    ) -> List[sequencetools.OutputSequence]:
        return [subseq for subseq in subseqs if not subseq.NDIM]

    def numericalparameters(self, lines: PyxPxdLines) -> None:
        """Numeric parameter declaration lines."""
        if isinstance(self.model, modeltools.SolverModel):
            pyx, pxd, both = lines.pyx.add, lines.pxd.add, lines.add
            both(0, "@cython.final")
            both(0, "cdef class NumConsts:")
            pyx(1, "pass")
            for name in ("nmb_methods", "nmb_stages"):
                pxd(1, f"cdef public {TYPE2STR[int]} {name}")
            for name in ("dt_increase", "dt_decrease"):
                pxd(1, f"cdef public {TYPE2STR[float]} {name}")
            pxd(1, "cdef public configutils.Config pub")
            pxd(1, "cdef public double[:, :, :] a_coefs")

            both(0, "@cython.final")
            both(0, "cdef class NumVars:")
            pyx(1, "pass")
            pxd(1, "cdef public bint use_relerror")
            for name in ("nmb_calls", "idx_method", "idx_stage"):
                pxd(1, f"cdef public {TYPE2STR[int]} {name}")
            for name in (
                "t0",
                "t1",
                "dt",
                "dt_est",
                "abserror",
                "relerror",
                "last_abserror",
                "last_relerror",
                "extrapolated_abserror",
                "extrapolated_relerror",
            ):
                pxd(1, f"cdef public {TYPE2STR[float]} {name}")
            pxd(1, f"cdef public {TYPE2STR[bool]} f0_ready")

    def submodels(self, lines: PyxPxdLines) -> None:
        """Submodel declaration lines."""
        for submodel in self.model.SUBMODELS:
            pyx, pxd, both = lines.pyx.add, lines.pxd.add, lines.add
            both(0, "@cython.final")
            cls = submodel.CYTHONBASECLASS
            both(
                0,
                f"cdef class {submodel.__name__}("
                f"{cls.__module__.split('.')[-1]}.{cls.__name__}):",
            )
            pxd(1, "cdef public Model model")
            pyx(1, "def __init__(self, Model model):")
            pyx(2, "self.model = model")
            for idx, method in enumerate(submodel.METHODS):
                both(1, f"cpdef double apply_method{idx}(self, double x) nogil:")
                pyx(2, f"return self.model.{method.__name__.lower()}(x)")

    def modeldeclarations(self, lines: PyxPxdLines) -> None:
        """The attribute declarations of the model class."""
        # pylint: disable=too-many-branches
        submodeltypes_old = getattr(self.model, "SUBMODELS", ())
        submodelnames_new = [
            n.split(".")[-1]
            for n in self.model.find_submodels(
                include_subsubmodels=False,
                include_sidemodels=True,
                include_optional=True,
                aggregate_vectors=True,
            )
        ]
        pyx, pxd, both = lines.pyx.add, lines.pxd.add, lines.add
        both(0, "@cython.final")
        follows_interface = any(
            base
            for base in inspect.getmro(type(self.model))
            if issubclass(base, modeltools.SubmodelInterface)
            and base.__module__.startswith("hydpy.interfaces.")
        )
        if follows_interface:
            both(0, "cdef class Model(masterinterface.MasterInterface):")
        else:
            both(0, "cdef class Model:")
        for cls in inspect.getmro(type(self.model)):
            for name, member in vars(cls).items():
                if isinstance(member, modeltools.IndexProperty):
                    if (name != "idx_sim") or not follows_interface:
                        pxd(1, f"cdef public {_int} {name}")
        if isinstance(self.model, modeltools.SubstepModel):
            pxd(1, f"cdef public {TYPE2STR[float]} timeleft")
        if self.model.parameters:
            pxd(1, "cdef public Parameters parameters")
        pxd(1, "cdef public Sequences sequences")
        for name in submodelnames_new:
            if name.endswith("_*"):
                name = name[:-2]
                pxd(1, f"cdef public interfaceutils.SubmodelsProperty {name}")
            else:
                pxd(1, f"cdef public masterinterface.MasterInterface {name}")
                pxd(1, f"cdef public {TYPE2STR[bool]} {name}_is_mainmodel")
                pxd(1, f"cdef public {TYPE2STR[int]} {name}_typeid")
        for submodel in submodeltypes_old:
            pxd(1, f"cdef public {submodel.__name__} {submodel.name}")
        if hasattr(self.model, "numconsts"):
            pxd(1, "cdef public NumConsts numconsts")
        if hasattr(self.model, "numvars"):
            pxd(1, "cdef public NumVars numvars")
        if submodeltypes_old or submodelnames_new:
            pyx(1, "def __init__(self):")
            pyx(2, "super().__init__()")
            for name in submodelnames_new:
                if name.endswith("_*"):
                    name = name[:-2]
                    pyx(2, f"self.{name} = interfaceutils.SubmodelsProperty()")
                else:
                    pyx(2, f"self.{name} = None")
                    pyx(2, f"self.{name}_is_mainmodel = False")
            for submodel in submodeltypes_old:
                pyx(2, f"self.{submodel.name} = {submodel.__name__}(self)")
        baseinterface = "Optional[masterinterface.MasterInterface]"
        for name in submodelnames_new:
            if not name.endswith("_*"):
                pyx(1, f"def get_{name}(self) -> {baseinterface}:")
                pyx(2, f"return self.{name}")
                pyx(1, f"def set_{name}(self, {name}: {baseinterface}) -> None:")
                pyx(2, f"self.{name} = {name}")

    def modelstandardfunctions(self, lines: PyxPxdLines) -> None:
        """The standard functions of the model class."""
        self.simulate(lines)
        self.iofunctions(lines)
        self.new2old(lines)
        if isinstance(self.model, modeltools.RunModel):
            self.run(lines, self.model)
        self.update_inlets(lines)
        self.update_outlets(lines)
        self.update_receivers(lines)
        self.update_senders(lines)
        self.update_outputs_model(lines)

    def modelnumericfunctions(self, lines: PyxPxdLines) -> None:
        """Numerical integration functions of the model class."""
        if isinstance(self.model, modeltools.SolverModel):
            self.solve(lines)
            self.calculate_single_terms(lines, self.model)
            self.calculate_full_terms(lines, self.model)
            self.get_point_states(lines)
            self.set_point_states(lines)
            self.set_result_states(lines)
            self.get_sum_fluxes(lines)
            self.set_point_fluxes(lines)
            self.set_result_fluxes(lines)
            self.integrate_fluxes(lines)
            self.reset_sum_fluxes(lines)
            self.addup_fluxes(lines)
            self.calculate_error(lines)
            self.extrapolate_error(lines)

    def simulate(self, lines: PyxPxdLines) -> None:
        """Simulation statements."""
        print("                . simulate")
        pyx, both = lines.pyx.add, lines.add
        both(1, f"cpdef inline void simulate(self, {_int} idx) {_nogil}:")
        pyx(2, "self.idx_sim = idx")
        seqs = self.model.sequences
        if seqs.inputs or self.model.SUBMODELINTERFACES:
            pyx(2, "self.load_data(idx)")
        if self.model.INLET_METHODS:
            pyx(2, "self.update_inlets()")
        if isinstance(self.model, modeltools.SolverModel):
            pyx(2, "self.solve()")
        else:
            pyx(2, "self.run()")
            if seqs.states:
                pyx(2, "self.new2old()")
        if self.model.OUTLET_METHODS:
            pyx(2, "self.update_outlets()")
        if seqs.factors or seqs.fluxes or seqs.states:
            pyx(2, "self.update_outputs()")

    def _call_submodel_method(self, lines: PyxPxdLines, methodcall: str) -> None:
        name2submodel = self.model.find_submodels(
            include_subsubmodels=False,
            include_optional=True,
            aggregate_vectors=True,
        )
        pyx = lines.pyx.add
        if any(name.endswith("_*") for name in name2submodel):
            pyx(2, f"cdef {_int} i_submodel")
        for fullname in name2submodel:
            name = fullname.rpartition(".")[2]
            if name.endswith("_*"):
                name = name[:-2]
                pyx(2, f"for i_submodel in range(self.{name}.number):")
                pyx(3, f"if self.{name}.typeids[i_submodel] > 0:")
                pyx(
                    4,
                    f"(<masterinterface.MasterInterface>"
                    f"self.{name}.submodels[i_submodel]).{methodcall}",
                )
            else:
                pyx(
                    2, f"if (self.{name} is not None) and not self.{name}_is_mainmodel:"
                )
                pyx(3, f"self.{name}.{methodcall}")

    def iofunctions(self, lines: PyxPxdLines) -> None:
        """Input/output functions of the model class.

        The result of property |PyxWriter.iofunctions| depends on the availability of
        different types of sequences.  So far, the models implemented in *HydPy* do not
        reflect all possible combinations, which is why we modify the |hland_v1|
        application model in the following examples:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> pyxwriter = cythonizer.pyxwriter
        >>> from hydpy.cythons.modelutils import PyxPxdLines
        >>> lines = PyxPxdLines()
        >>> pyxwriter.iofunctions(lines)
                    . load_data
                    . save_data
        >>> lines.pyx  # doctest: +ELLIPSIS
            cpdef void load_data(self, ...int... idx) nogil:
                self.idx_sim = idx
                self.sequences.inputs.load_data(idx)
                if (self.aetmodel is not None) and not self.aetmodel_is_mainmodel:
                    self.aetmodel.load_data(idx)
            cpdef void save_data(self, ...int... idx) nogil:
                self.idx_sim = idx
                self.sequences.inputs.save_data(idx)
                self.sequences.factors.save_data(idx)
                self.sequences.fluxes.save_data(idx)
                self.sequences.states.save_data(idx)
                if (self.aetmodel is not None) and not self.aetmodel_is_mainmodel:
                    self.aetmodel.save_data(idx)
        <BLANKLINE>

        >>> pyxwriter.model.sequences.factors = None
        >>> pyxwriter.model.sequences.fluxes = None
        >>> pyxwriter.model.sequences.states = None
        >>> lines.pyx.clear()
        >>> pyxwriter.iofunctions(lines)
                    . load_data
                    . save_data
        >>> lines.pyx  # doctest: +ELLIPSIS
            cpdef void load_data(self, ...int... idx) nogil:
                self.idx_sim = idx
                self.sequences.inputs.load_data(idx)
                if (self.aetmodel is not None) and not self.aetmodel_is_mainmodel:
                    self.aetmodel.load_data(idx)
            cpdef void save_data(self, ...int... idx) nogil:
                self.idx_sim = idx
                self.sequences.inputs.save_data(idx)
                if (self.aetmodel is not None) and not self.aetmodel_is_mainmodel:
                    self.aetmodel.save_data(idx)
        <BLANKLINE>

        >>> pyxwriter.model.sequences.inputs = None
        >>> lines.pyx.clear()
        >>> pyxwriter.iofunctions(lines)
        >>> lines.pyx  # doctest: +ELLIPSIS
        <BLANKLINE>
        <BLANKLINE>
        """
        seqs = self.model.sequences
        if not (seqs.inputs or seqs.factors or seqs.fluxes or seqs.states):
            return
        pyx, both = lines.pyx.add, lines.add
        for func in ("load_data", "save_data"):
            if (func == "load_data") and not (
                seqs.inputs or self.model.SUBMODELINTERFACES
            ):
                continue
            print(f"            . {func}")
            nogil = func in ("load_data", "save_data")
            both(1, get_methodheader(func, nogil=nogil, idxarg=True, inline=False))
            pyx(2, "self.idx_sim = idx")
            for subseqs in seqs:
                if func == "load_data":
                    applyfuncs: Tuple[str, ...] = ("inputs",)
                else:
                    applyfuncs = ("inputs", "factors", "fluxes", "states")
                if subseqs.name in applyfuncs:
                    pyx(2, f"self.sequences.{subseqs.name}." f"{func}(idx)")
            self._call_submodel_method(lines, f"{func}(idx)")

    def new2old(self, lines: PyxPxdLines) -> None:
        """Old states to new states statements."""
        name2submodel = self.model.find_submodels(
            include_subsubmodels=False, include_optional=True, aggregate_vectors=True
        )
        pyx, both = lines.pyx.add, lines.add
        if self.model.sequences.states or name2submodel:
            print("                . new2old")
            both(1, get_methodheader("new2old", nogil=True, inline=False))
        if self.model.sequences.states:
            self._add_cdef_jdxs(lines, self.model.sequences.states)
            for seq in self.model.sequences.states:
                if seq.NDIM == 0:
                    pyx(
                        2,
                        f"self.sequences.old_states.{seq.name} = "
                        f"self.sequences.new_states.{seq.name}",
                    )
                else:
                    indexing = ""
                    for idx in range(seq.NDIM):
                        pyx(
                            2 + idx,
                            f"for jdx{idx} in range(self.sequences.states."
                            f"_{seq.name}_length_{idx}):",
                        )
                        indexing += f"jdx{idx},"
                    indexing = indexing[:-1]
                    pyx(
                        2 + seq.NDIM,
                        f"self.sequences.old_states.{seq.name}[{indexing}] = "
                        f"self.sequences.new_states.{seq.name}[{indexing}]",
                    )
        self._call_submodel_method(lines, "new2old()")

    def _call_methods(
        self,
        lines: PyxPxdLines,
        name: str,
        methods: Tuple[Type[modeltools.Method], ...],
        idx_as_arg: bool = False,
    ) -> None:
        if hasattr(self.model, name):
            pyx, both = lines.pyx.add, lines.add
            both(1, get_methodheader(name, nogil=True, idxarg=idx_as_arg))
            if idx_as_arg:
                pyx(2, "self.idx_sim = idx")
            anything = False
            for method in methods:
                pyx(2, f"self.{method.__name__.lower()}()")
                anything = True
            if not anything:
                pyx(2, "pass")

    def _call_runmethods_segmentwise(
        self, lines: PyxPxdLines, methods: Tuple[Type[modeltools.Method], ...]
    ) -> None:
        if hasattr(self.model, "run"):
            pyx, both = lines.pyx.add, lines.add
            both(1, get_methodheader("run", nogil=True, idxarg=False))
            pyx(2, f"cdef {TYPE2STR[int]} idx_segment, idx_run")
            pyx(2, "for idx_segment in range(self.parameters.control.nmbsegments):")
            pyx(3, "self.idx_segment = idx_segment")
            pyx(3, "for idx_run in range(self.parameters.solver.nmbruns):")
            pyx(4, "self.idx_run = idx_run")
            for method in methods:
                pyx(4, f"self.{method.__name__.lower()}()")

    def update_receivers(self, lines: PyxPxdLines) -> None:
        """Lines of the model method with the same name."""
        self._call_methods(lines, "update_receivers", self.model.RECEIVER_METHODS, True)

    def update_inlets(self, lines: PyxPxdLines) -> None:
        """Lines of the model method with the same name."""
        self._call_methods(lines, "update_inlets", self.model.INLET_METHODS)

    def run(self, lines: PyxPxdLines, model: modeltools.RunModel) -> None:
        """Return the lines of the model method with the same name."""
        if isinstance(model, modeltools.SegmentModel):
            self._call_runmethods_segmentwise(lines, model.RUN_METHODS)
        else:
            nmb = len(lines.pyx)
            self._call_methods(lines, "run", model.RUN_METHODS)
            if isinstance(model, modeltools.SubstepModel):
                pyx = Lines()
                pyx.extend(lines.pyx[: nmb + 1])
                add = pyx.add
                add(2, "self.timeleft = self.parameters.derived.seconds")
                add(2, "while True:")
                for line in lines.pyx[nmb + 1 :]:
                    add(1, line)
                add(3, "if self.timeleft <= 0.0:")
                add(4, "break")
                add(3, "self.new2old()")
                lines.pyx = pyx

    def update_outlets(self, lines: PyxPxdLines) -> None:
        """Lines of the model method with the same name."""
        self._call_methods(lines, "update_outlets", self.model.OUTLET_METHODS)

    def update_senders(self, lines: PyxPxdLines) -> None:
        """Lines of the model method with the same name."""
        self._call_methods(lines, "update_senders", self.model.SENDER_METHODS, True)

    def update_outputs_model(self, lines: PyxPxdLines) -> None:
        """Lines of the model method with the same name (except the `_model` suffix)."""
        pyx, both = lines.pyx.add, lines.add
        both(1, get_methodheader("update_outputs", nogil=True, idxarg=False))
        factors = self._filter_outputsequences(self.model.sequences.factors)
        fluxes = self._filter_outputsequences(self.model.sequences.fluxes)
        states = self._filter_outputsequences(self.model.sequences.states)
        if factors:
            pyx(2, "self.sequences.factors.update_outputs()")
        if fluxes:
            pyx(2, "self.sequences.fluxes.update_outputs()")
        if states:
            pyx(2, "self.sequences.states.update_outputs()")
        if not (factors or fluxes or states):
            pyx(2, "pass")

    def update_outputs(
        self, lines: PyxPxdLines, subseqs: sequencetools.OutputSequences[Any]
    ) -> None:
        """Lines of the subsequences method with the same name."""
        pyx, both = lines.pyx.add, lines.add
        both(1, get_methodheader("update_outputs", nogil=True, idxarg=False))
        subseqs_ = self._filter_outputsequences(subseqs)
        if subseqs_:
            for seq in subseqs_:
                name = seq.name
                pyx(2, f"if self._{name}_outputflag:")
                pyx(3, f"self._{name}_outputpointer[0] = self.{name}")
        else:
            pyx(2, "pass")

    def calculate_single_terms(
        self, lines: PyxPxdLines, model: modeltools.SolverModel
    ) -> None:
        """Return the lines of the model method with the same name."""
        nmb = len(lines.pyx)
        self._call_methods(lines, "calculate_single_terms", model.PART_ODE_METHODS)
        if len(lines.pyx) > nmb:
            lines.pyx.insert(
                nmb + 1, ("        self.numvars.nmb_calls = self.numvars.nmb_calls + 1")
            )

    def calculate_full_terms(
        self, lines: PyxPxdLines, model: modeltools.SolverModel
    ) -> None:
        """Return the lines of the model method with the same name."""
        self._call_methods(lines, "calculate_full_terms", model.FULL_ODE_METHODS)

    @property
    def name2function_method(self) -> Dict[str, Callable[..., Any]]:
        """Functions defined by |Method| subclasses."""
        name2function = {}
        for name, member in vars(self.model).items():
            if getattr(getattr(member, "__func__", None), "__HYDPY_METHOD__", False):
                name2function[name] = member
        return name2function

    @property
    def name2submethodnames_automethod(
        self,
    ) -> Dict[str, Tuple[Type[modeltools.Method], ...]]:
        """Submethods selected by |AutoMethod| subclasses."""
        name2submethods = {}
        for name, member in vars(self.model).items():
            if (
                isinstance(member, types.MethodType)
                and isinstance(call := member.__func__, types.MethodType)
                and inspect.isclass(method := call.__self__)
                and issubclass(automethod := method, modeltools.AutoMethod)
            ):
                name2submethods[name] = automethod.SUBMETHODS
        return name2submethods

    @property
    def interfacemethods(self) -> Set[str]:
        """The full and abbreviated names of the selected model's interface methods."""
        if hasattr(self.model, "INTERFACE_METHODS"):
            interfaces = set(m.__name__.lower() for m in self.model.INTERFACE_METHODS)
            interfaces.update(set(i.rpartition("_")[0] for i in interfaces))
            return interfaces
        return set()

    def modeluserfunctions(self, lines: PyxPxdLines) -> None:
        """Model-specific functions."""
        for name, func in self.name2function_method.items():
            print(f"            . {name}")
            inline = name not in self.interfacemethods
            funcconverter = FuncConverter(
                model=self.model, funcname=name, func=func, inline=inline
            )
            pyxlines = funcconverter.pyxlines
            lines.pyx.extend(pyxlines)
            lines.pxd.append(pyxlines[0][:-1])
        for name, submethods in self.name2submethodnames_automethod.items():
            print(f"            . {name}")
            self.automethod(lines, name=name, submethods=submethods)

    def callbackfeatures(self, lines: PyxPxdLines) -> None:
        """Features to let users define callback functions."""

        pyx, pxd = lines.pyx.add, lines.pxd.add

        pxd(0, "ctypedef void (*CallbackType) (Model) nogil")
        pyx(0, "")
        pxd(0, "cdef class CallbackWrapper:")
        pxd(1, "cdef CallbackType callback")
        pyx(0, "")
        pyx(0, "cdef void do_nothing(Model model) nogil:")
        pyx(1, "pass")
        pyx(0, "")
        pyx(0, "cpdef get_wrapper():")
        pyx(1, "cdef CallbackWrapper wrapper = CallbackWrapper()")
        pyx(1, "wrapper.callback = do_nothing")
        pyx(1, "return wrapper")
        pyx(0, "")

    def automethod(
        self,
        lines: PyxPxdLines,
        name: str,
        submethods: Tuple[Type[modeltools.Method], ...],
    ) -> None:
        """Lines of a method defined by a |AutoMethod| subclass."""
        pyx, both = lines.pyx.add, lines.add
        inline = name not in self.interfacemethods
        both(1, get_methodheader(methodname=name, nogil=True, inline=inline))
        for submethod in submethods:
            pyx(2, f"self.{submethod.__name__.lower()}()")

    def solve(self, lines: PyxPxdLines) -> None:
        """Lines of the model method with the same name."""
        if solve := getattr(self.model, "solve", None):
            print("            . solve")
            funcconverter = FuncConverter(self.model, "solve", solve)
            pyxlines = funcconverter.pyxlines
            lines.pyx.extend(pyxlines)
            lines.pxd.append(pyxlines[0][:-1])

    @classmethod
    def _assign_seqvalues(
        cls,
        subseqs: Iterable[sequencetools.IOSequence],
        subseqs_name: str,
        target: str,
        index: Optional[str],
        load: bool,
    ) -> Iterator[str]:
        subseqs = list(subseqs)
        from1 = f"self.sequences.{subseqs_name}.%s"
        to1 = f"self.sequences.{subseqs_name}._%s_{target}"
        if index is not None:
            to1 += f"[self.numvars.{index}]"
        if load:
            from1, to1 = to1, from1
        yield from cls._declare_idxs(subseqs)
        for seq in subseqs:
            from2 = from1 % seq.name
            to2 = to1 % seq.name
            if seq.NDIM == 0:
                yield f"{to2} = {from2}"
            elif seq.NDIM == 1:
                yield (
                    f"for idx0 in range(self.sequences."
                    f"{subseqs_name}._{seq.name}_length):"
                )
                yield f"    {to2}[idx0] = {from2}[idx0]"
            elif seq.NDIM == 2:
                yield (
                    f"for idx0 in range(self.sequences."
                    f"{subseqs_name}._{seq.name}_length0):"
                )
                yield (
                    f"    for idx1 in range(self.sequences."
                    f"{subseqs_name}._{seq.name}_length1):"
                )
                yield f"        {to2}[idx0, idx1] = {from2}[idx0, idx1]"
            else:
                raise NotImplementedError(
                    f"NDIM of sequence `{seq.name}` is higher than expected."
                )

    @staticmethod
    def _declare_idxs(subseqs: Iterable[sequencetools.IOSequence]) -> Iterator[str]:
        maxdim = 0
        for seq in subseqs:
            maxdim = max(maxdim, seq.NDIM)
        if maxdim == 1:
            yield f"cdef {_int} idx0"
        elif maxdim == 2:
            yield f"cdef {_int} idx0, idx1"

    @decorate_method
    def get_point_states(self) -> Iterator[str]:
        """Get point statements for state sequences."""
        return self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name="states",
            target="points",
            index="idx_stage",
            load=True,
        )

    @decorate_method
    def set_point_states(self) -> Iterator[str]:
        """Set point statements for state sequences."""
        return self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name="states",
            target="points",
            index="idx_stage",
            load=False,
        )

    @decorate_method
    def set_result_states(self) -> Iterator[str]:
        """Get results statements for state sequences."""
        return self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name="states",
            target="results",
            index="idx_method",
            load=False,
        )

    @decorate_method
    def get_sum_fluxes(self) -> Iterator[str]:
        """Get sum statements for flux sequences."""
        return self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numericsequences,
            subseqs_name="fluxes",
            target="sum",
            index=None,
            load=True,
        )

    @decorate_method
    def set_point_fluxes(self) -> Iterator[str]:
        """Set point statements for flux sequences."""
        return self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numericsequences,
            subseqs_name="fluxes",
            target="points",
            index="idx_stage",
            load=False,
        )

    @decorate_method
    def set_result_fluxes(self) -> Iterator[str]:
        """Set result statements for flux sequences."""
        return self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numericsequences,
            subseqs_name="fluxes",
            target="results",
            index="idx_method",
            load=False,
        )

    @decorate_method
    def integrate_fluxes(self) -> Iterator[str]:
        """Integrate statements for flux sequences."""
        max_ndim = -1
        for seq in self.model.sequences.fluxes.numericsequences:
            max_ndim = max(max_ndim, seq.NDIM)
        if max_ndim == 0:
            yield f"cdef {_int} jdx"
        elif max_ndim == 1:
            yield f"cdef {_int} jdx, idx0"
        elif max_ndim == 2:
            yield f"cdef {_int} jdx, idx0, idx1"
        for seq in self.model.sequences.fluxes.numericsequences:
            to_ = f"self.sequences.fluxes.{seq.name}"
            from_ = f"self.sequences.fluxes._{seq.name}_points"
            coefs = (
                "self.numvars.dt * self.numconsts.a_coefs"
                "[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]"
            )
            if seq.NDIM == 0:
                yield f"{to_} = 0."
                yield "for jdx in range(self.numvars.idx_method):"
                yield f"    {to_} = {to_} +{coefs}*{from_}[jdx]"
            elif seq.NDIM == 1:
                yield (
                    f"for idx0 in " f"range(self.sequences.fluxes._{seq.name}_length):"
                )
                yield f"    {to_}[idx0] = 0."
                yield "    for jdx in range(self.numvars.idx_method):"
                yield (
                    f"        {to_}[idx0] = "
                    f"{to_}[idx0] + {coefs}*{from_}[jdx, idx0]"
                )
            elif seq.NDIM == 2:
                yield (
                    f"for idx0 in " f"range(self.sequences.fluxes._{seq.name}_length0):"
                )
                yield (
                    f"    for idx1 in range("
                    f"self.sequences.fluxes._{seq.name}_length1):"
                )
                yield f"        {to_}[idx0, idx1] = 0."
                yield "        for jdx in range(self.numvars.idx_method):"
                yield (
                    f"            {to_}[idx0, idx1] = "
                    f"{to_}[idx0, idx1] + {coefs}*{from_}[jdx, idx0, idx1]"
                )
            else:
                raise NotImplementedError(
                    f"NDIM of sequence `{seq.name}` is higher than expected."
                )

    @decorate_method
    def reset_sum_fluxes(self) -> Iterator[str]:
        """Reset sum statements for flux sequences."""
        subseqs = list(self.model.sequences.fluxes.numericsequences)
        yield from PyxWriter._declare_idxs(subseqs)
        for seq in subseqs:
            to_ = f"self.sequences.fluxes._{seq.name}_sum"
            if seq.NDIM == 0:
                yield f"{to_} = 0."
            elif seq.NDIM == 1:
                yield (
                    f"for idx0 in " f"range(self.sequences.fluxes._{seq.name}_length):"
                )
                yield f"    {to_}[idx0] = 0."
            elif seq.NDIM == 2:
                yield (
                    f"for idx0 in " f"range(self.sequences.fluxes._{seq.name}_length0):"
                )
                yield (
                    f"    for idx1 in "
                    f"range(self.sequences.fluxes._{seq.name}_length1):"
                )
                yield f"        {to_}[idx0, idx1] = 0."
            else:
                raise NotImplementedError(
                    f"NDIM of sequence `{seq.name}` is higher than expected."
                )

    @decorate_method
    def addup_fluxes(self) -> Iterator[str]:
        """Add up statements for flux sequences."""
        subseqs = list(self.model.sequences.fluxes.numericsequences)
        yield from PyxWriter._declare_idxs(subseqs)
        for seq in subseqs:
            to_ = f"self.sequences.fluxes._{seq.name}_sum"
            from_ = f"self.sequences.fluxes.{seq.name}"
            if seq.NDIM == 0:
                yield f"{to_} = {to_} + {from_}"
            elif seq.NDIM == 1:
                yield (
                    f"for idx0 in " f"range(self.sequences.fluxes._{seq.name}_length):"
                )
                yield f"    {to_}[idx0] = {to_}[idx0] + {from_}[idx0]"
            elif seq.NDIM == 2:
                yield (
                    f"for idx0 in " f"range(self.sequences.fluxes._{seq.name}_length0):"
                )
                yield (
                    f"    for idx1 in "
                    f"range(self.sequences.fluxes._{seq.name}_length1):"
                )
                yield (
                    f"        {to_}[idx0, idx1] = "
                    f"{to_}[idx0, idx1] + {from_}[idx0, idx1]"
                )
            else:
                raise NotImplementedError(
                    f"NDIM of sequence `{seq.name}` is higher than expected."
                )

    @decorate_method
    def calculate_error(self) -> Iterator[str]:
        """Calculate error statements."""
        subseqs = list(self.model.sequences.fluxes.numericsequences)
        assert isinstance(self.model, modeltools.ELSModel)
        if self.model.SOLVERSEQUENCES:
            subseqs = [
                seq for seq in subseqs if isinstance(seq, self.model.SOLVERSEQUENCES)
            ]
        yield from self._declare_idxs(subseqs)
        userel = "self.numvars.use_relerror:"
        abserror = "self.numvars.abserror"
        relerror = "self.numvars.relerror"
        index = "self.numvars.idx_method"
        yield "cdef double abserror"
        yield f"{abserror} = 0."
        yield f"if {userel}"
        yield f"    {relerror} = 0."
        yield "else:"
        yield f"    {relerror} = inf"
        for seq in subseqs:
            results = f"self.sequences.fluxes._{seq.name}_results"
            if seq.NDIM == 0:
                yield f"abserror = fabs(" f"{results}[{index}]-{results}[{index}-1])"
                yield f"{abserror} = max({abserror}, abserror)"
                yield f"if {userel}"
                yield f"    if {results}[{index}] == 0.:"
                yield f"        {relerror} = inf"
                yield "    else:"
                yield (
                    f"        {relerror} = max("
                    f"{relerror}, fabs(abserror/{results}[{index}]))"
                )
            elif seq.NDIM == 1:
                yield (
                    f"for idx0 in range(" f"self.sequences.fluxes._{seq.name}_length):"
                )
                yield (
                    f"    abserror = fabs("
                    f"{results}[{index}, idx0]-{results}[{index}-1, idx0])"
                )
                yield f"    {abserror} = max({abserror}, abserror)"
                yield f"    if {userel}"
                yield f"        if {results}[{index}, idx0] == 0.:"
                yield f"            {relerror} = inf"
                yield "        else:"
                yield (
                    f"            {relerror} = max("
                    f"{relerror}, fabs(abserror/{results}[{index}, idx0]))"
                )
            elif seq.NDIM == 2:
                yield (
                    f"for idx0 in range(" f"self.sequences.fluxes._{seq.name}_length0):"
                )
                yield (
                    f"    for idx1 in range("
                    f"self.sequences.fluxes._{seq.name}_length1):"
                )

                yield (
                    f"        abserror = fabs({results}[{index}, "
                    f"idx0, idx1]-{results}[{index}-1, idx0, idx1])"
                )
                yield f"        {abserror} = max({abserror}, abserror)"
                yield f"        if {userel}"
                yield f"            if {results}[{index}, idx0, idx1] == 0.:"
                yield f"                {relerror} = inf"
                yield "            else:"
                yield (
                    f"                {relerror} = max("
                    f"{relerror}, "
                    f"fabs(abserror/{results}[{index}, idx0, idx1]))"
                )
            else:
                raise NotImplementedError(
                    f"NDIM of sequence `{seq.name}` is higher than expected."
                )

    def extrapolate_error(self, lines: PyxPxdLines) -> None:
        """Extrapolate error statements."""
        extrapolate_error = getattr(self.model, "extrapolate_error", None)
        if extrapolate_error:
            print("            . extrapolate_error")
            funcconverter = FuncConverter(
                self.model, "extrapolate_error", extrapolate_error
            )
            pyxlines = funcconverter.pyxlines
            lines.pyx.extend(pyxlines)
            lines.pxd.append(pyxlines[0][:-1])

    def write_stubfile(self) -> None:
        """Write a stub file for the actual base or application model.

        At the moment, *HydPy* creates model objects quite dynamically.  In many
        regards, this comes with lots of conveniences.  However, there two critical
        drawbacks compared to more static approaches: some amount of additional
        initialisation time and, more important, much opaqueness for code inspection
        tools.  In this context, we experiment with "stub files" at the moment.  These
        could either contain typing information only or define statically predefined
        model classes.  The following example uses method |PyxWriter.write_stubfile| to
        write a (far from perfect) prototype stub file for base model |hland|:

        >>> from hydpy.models.hland import *
        >>> cythonizer.pyxwriter.write_stubfile()

        This is the path to the written file:

        >>> import os
        >>> import hydpy
        >>> filepath = os.path.join(hydpy.__path__[0], "hland.py")
        >>> os.path.exists(filepath)
        True

        However, it's just an experimental prototype, so we better remove it:

        >>> os.remove(filepath)
        >>> os.path.exists(filepath)
        False
        """
        hydpypath: str = hydpy.__path__[0]
        filepath = os.path.join(hydpypath, f"{self.model.name}.py")
        base = ".".join(self.model.__module__.split(".")[:3])
        with open(filepath, "w", encoding=config.ENCODING) as stubfile:
            stubfile.write(
                f"# -*- coding: utf-8 -*-\n\n"
                f"import hydpy\n"
                f"from {base} import *\n"
                f"from hydpy.core.parametertools import (\n"
                f"  FastAccess,)\n"
                f"from hydpy.core.parametertools import (\n"
                f"  Parameters, FastAccessParameter)\n"
                f"from hydpy.core.sequencetools import (\n"
                f"    Sequences,)\n\n"
            )
            for subpars in self.model.parameters:
                classname = f"FastAccess{subpars.name.capitalize()}Parameters"
                stubfile.write(f"\n\nclass {classname}(FastAccessParameter):\n")
                for partype in subpars.CLASSES:
                    stubfile.write(
                        f"    {partype.__name__.lower()}: "
                        f"{partype.__module__}.{partype.__name__}\n"
                    )
            for subpars in self.model.parameters:
                classname = f"{subpars.name.capitalize()}Parameters"
                stubfile.write(f"\n\nclass {classname}({classname}):\n")
                stubfile.write(f"    fastaccess: FastAccess{classname}\n")
                for partype in subpars.CLASSES:
                    stubfile.write(
                        f"    {partype.__name__.lower()}: "
                        f"{partype.__module__}.{partype.__name__}\n"
                    )
            stubfile.write("\n\nclass Parameters(Parameters):\n")
            for subpars in self.model.parameters:
                classname = f"{subpars.name.capitalize()}Parameters"
                stubfile.write(f"    {subpars.name}: {classname}\n")

            for subseqs in self.model.sequences:
                classname = f"FastAccess{type(subseqs).__name__}"
                stubfile.write(f"\n\nclass {classname}(FastAccess):\n")
                for seqtype in subseqs.CLASSES:
                    stubfile.write(
                        f"    {seqtype.__name__.lower()}: "
                        f"{seqtype.__module__}.{seqtype.__name__}\n"
                    )
            for subseqs in self.model.sequences:
                classname = type(subseqs).__name__
                stubfile.write(f"\n\nclass {classname}({classname}):\n")
                stubfile.write(f"    fastaccess: FastAccess{classname}\n")
                if classname == "StateSequences":
                    stubfile.write(f"    fastaccess_old: FastAccess{classname}\n")
                    stubfile.write(f"    fastaccess_new: FastAccess{classname}\n")
                for seqtype in subseqs.CLASSES:
                    stubfile.write(
                        f"    {seqtype.__name__.lower()}: "
                        f"{seqtype.__module__}.{seqtype.__name__}\n"
                    )
            stubfile.write("\n\nclass Sequences(Sequences):\n")
            for group in self.model.sequences:
                classname = type(group).__name__
                stubfile.write(f"    {group.name}: {classname}\n")

            stubfile.write(
                "\n\nclass Model(Model):\n"
                "    parameters: Parameters\n"
                "    sequences: Sequences\n"
            )
            for method in self.model.get_methods():
                stubfile.write(
                    f"    {method.__name__.lower()}: hydpy.core.modeltools.Method\n"
                )

            stubfile.write("\n\nmodel: Model\n")
            stubfile.write("parameters: Parameters\n")
            stubfile.write("sequences: Sequences\n")
            for subpars in self.model.parameters:
                classname = f"{subpars.name.capitalize()}Parameters"
                stubfile.write(f"{subpars.name}: {classname}\n")
            for subseqs in self.model.sequences:
                classname = type(subseqs).__name__
                stubfile.write(f"{subseqs.name}: {classname}\n")
            if self.model.parameters.control:
                for partype in self.model.parameters.control.CLASSES:
                    stubfile.write(
                        f"{partype.__name__.lower()}: "
                        f"{partype.__module__}.{partype.__name__}\n"
                    )


class FuncConverter:
    """Helper class for class |PyxWriter| that analyses Python functions and provides
    the required Cython code via property |FuncConverter.pyxlines|."""

    model: modeltools.Model
    funcname: str
    func: Callable[..., Any]
    inline: bool

    def __init__(
        self,
        model: modeltools.Model,
        funcname: str,
        func: Callable[..., Any],
        inline: bool = True,
    ) -> None:
        self.model = model
        self.funcname = funcname
        self.func = func
        self.inline = inline

    @property
    def argnames(self) -> List[str]:
        """The argument names of the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).argnames
        ['model']
        """
        return inspect.getargs(self.func.__code__)[0]

    @property
    def varnames(self) -> Tuple[str, ...]:
        """The variable names of the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).varnames
        ('self', 'con', 'der', 'inp', 'fac', 'k')
        """
        return tuple(
            vn if vn != "model" else "self" for vn in self.func.__code__.co_varnames
        )

    @property
    def locnames(self) -> List[str]:
        """The variable names of the handled function except for the argument names.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).locnames
        ['self', 'con', 'der', 'inp', 'fac', 'k']
        """
        return [vn for vn in self.varnames if vn not in self.argnames]

    @property
    def subgroupnames(self) -> List[str]:
        """The complete names of the subgroups relevant for the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).subgroupnames
        ['parameters.control', 'parameters.derived', 'sequences.inputs', \
'sequences.factors']
        """
        names = []
        for groupname in ("parameters", "sequences"):
            for subgroup in getattr(self.model, groupname):
                if subgroup.name[:3] in self.varnames:
                    names.append(groupname + "." + subgroup.name)
        if "old" in self.varnames:
            names.append("sequences.old_states")
        if "new" in self.varnames:
            names.append("sequences.new_states")
        return names

    @property
    def subgroupshortcuts(self) -> List[str]:
        """The abbreviated names of the subgroups relevant for the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).subgroupshortcuts
        ['con', 'der', 'inp', 'fac']
        """
        return [name.split(".")[-1][:3] for name in self.subgroupnames]

    @property
    def untypedvarnames(self) -> List[str]:
        """The names of the untyped variables used in the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).untypedvarnames
        ['k']
        """
        return [
            name
            for name in self.varnames
            if name not in self.subgroupshortcuts + ["self"]
        ]

    @property
    def untypedarguments(self) -> List[str]:
        """The names of the untyped arguments used by the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).untypedarguments
        []
        """
        defline = self.cleanlines[0]
        return [
            name
            for name in self.untypedvarnames
            if ((f", {name}," in defline) or (f", {name})" in defline))
        ]

    @property
    def untypedinternalvarnames(self) -> List[str]:
        """The names of the untyped variables used in the current function except for
        those of the arguments.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")
        >>> FuncConverter(model, None, model.calc_tc_v1).untypedinternalvarnames
        ['k']
        """
        return [
            name for name in self.untypedvarnames if name not in self.untypedarguments
        ]

    @property
    def cleanlines(self) -> List[str]:
        """The leaned code lines of the current function.

        The implemented cleanups:
          * eventually, remove method version
          * remove all docstrings
          * remove all comments
          * remove all empty lines
          * remove line bracks within brackets
          * remove the phrase `modelutils`
          * remove all lines containing the phrase `fastaccess`
          * replace all shortcuts with complete reference names
          * replace " model." with " self."
          * remove ".values" and "value"
          * remove the ": float" annotation
        """
        code = inspect.getsource(self.func)
        code = "\n".join(code.split('"""')[::2])
        code = code.replace("modelutils.", "")
        code = code.replace(" model.", " self.")
        code = code.replace("[model.", "[self.")
        code = code.replace("(model.", "(self.")
        code = code.replace(".values", "")
        code = code.replace(".value", "")
        code = code.replace(": float", "")
        for name, shortcut in zip(self.subgroupnames, self.subgroupshortcuts):
            code = code.replace(f"{shortcut}.", f"self.{name}.")
        code = self.remove_linebreaks_within_equations(code)
        lines = code.splitlines()
        self.remove_imath_operators(lines)
        del lines[0]  # remove @staticmethod
        lines = [line[4:] for line in lines]  # unindent
        argnames = self.argnames
        argnames[0] = "self"
        lines[0] = f"def {self.funcname}({', '.join(argnames)}):"
        lines = [line.split("#")[0] for line in lines]
        lines = [line for line in lines if "fastaccess" not in line]
        lines = [line.rstrip() for line in lines if line.rstrip()]
        return Lines(*lines)

    @staticmethod
    def remove_linebreaks_within_equations(code: str) -> str:
        r"""Remove line breaks within equations.

        The following example is not an exhaustive test but shows how the method works
        in principle:

        >>> code = "asdf = \\\n(a\n+b)"
        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> FuncConverter.remove_linebreaks_within_equations(code)
        'asdf = (a+b)'
        """
        code = code.replace("\\\n", "")
        chars = []
        counter = 0
        for char in code:
            if char in ("(", "[", "{"):
                counter += 1
            elif char in (")", "]", "}"):
                counter -= 1
            if not (counter and (char == "\n")):
                chars.append(char)
        return "".join(chars)

    @staticmethod
    def remove_imath_operators(lines: List[str]) -> None:
        """Remove mathematical expressions that require Pythons global interpreter
        locking mechanism.

        The following example is not an exhaustive test but shows how the method works
        in principle:

        >>> lines = ["    x += 1*1"]
        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> FuncConverter.remove_imath_operators(lines)
        >>> lines
        ['    x = x + (1*1)']
        """
        for idx, line in enumerate(lines):
            for operator_ in ("+=", "-=", "**=", "*=", "//=", "/=", "%="):
                sublines = line.split(operator_)
                if len(sublines) > 1:
                    indent = line.count(" ") - line.lstrip().count(" ")
                    sublines = [sl.strip() for sl in sublines]
                    line = (
                        f"{indent*' '}{sublines[0]} = "
                        f"{sublines[0]} {operator_[:-1]} ({sublines[1]})"
                    )
                    lines[idx] = line

    @property
    def pyxlines(self) -> Lines:
        """Cython code lines of the current function.

        Assumptions:
          * The function shall be a method.
          * Annotations specify all argument and return types.
          * Non-default argument and return types are translate to
            "modulename.classname" strings.
          * Local variables are generally of type `int` but of type `double` when their
            name starts with `d_`.
          * Identical type names in Python and Cython when casting.

        We import some classes and prepare a pure-Python instance of application model
        |hland_v1|:

        >>> from types import MethodType
        >>> from hydpy.core.modeltools import Method, Model
        >>> from hydpy.core.typingtools import Vector
        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model("hland_v1")

        First, we show an example of a standard method without additional arguments and
        returning nothing but requiring two local variables:

        >>> class Calc_Test_V1(Method):
        ...     @staticmethod
        ...     def __call__(model: Model) -> None:
        ...         con = model.parameters.control.fastaccess
        ...         flu = model.sequences.fluxes.fastaccess
        ...         inp = model.sequences.inputs.fastaccess
        ...         for k in range(con.nmbzones):
        ...             d_pc = con.kg[k]*inp.p[k]
        ...             flu.pc[k] = d_pc
        >>> model.calc_test_v1 = MethodType(Calc_Test_V1.__call__, model)
        >>> lines = FuncConverter(model, "calc_test_v1", model.calc_test_v1).pyxlines
        >>> lines  # doctest: +ELLIPSIS
            cpdef inline void calc_test_v1(self) nogil:
                cdef double d_pc
                cdef ...int... k
                for k in range(self.parameters.control.nmbzones):
                    d_pc = self.parameters.control.kg[k]*self.sequences.inputs.p[k]
                    self.sequences.fluxes.pc[k] = d_pc
        <BLANKLINE>

        The second example shows that `float` and `Vector` annotations translate into
        `double` and `double[:]` types, respectively:

        >>> class Calc_Test_V2(Method):
        ...     @staticmethod
        ...     def __call__(model: Model, value: float, values: Vector) -> float:
        ...         con = model.parameters.control.fastaccess
        ...         return con.kg[0]*value*values[1]
        >>> model.calc_test_v2 = MethodType(Calc_Test_V2.__call__, model)
        >>> FuncConverter(model, "calc_test_v2", model.calc_test_v2).pyxlines
            cpdef inline double calc_test_v2(self, double value, double[:] values) \
nogil:
                return self.parameters.control.kg[0]*value*values[1]
        <BLANKLINE>

        Third, Python's standard cast function translates into Cython's cast syntax:

        >>> from hydpy.interfaces import channelinterfaces
        >>> class Calc_Test_V3(Method):
        ...     @staticmethod
        ...     def __call__(model: Model) -> channelinterfaces.StorageModel_V1:
        ...         return cast(channelinterfaces.StorageModel_V1, model.soilmodel)
        >>> model.calc_test_v3 = MethodType(Calc_Test_V3.__call__, model)
        >>> FuncConverter(model, "calc_test_v3", model.calc_test_v3).pyxlines
            cpdef inline masterinterface.MasterInterface calc_test_v3(self) nogil:
                return (<masterinterface.MasterInterface>self.soilmodel)
        <BLANKLINE>

        >>> class Calc_Test_V4(Method):
        ...     @staticmethod
        ...     def __call__(model: Model) -> None:
        ...         cast(
        ...             Union[
        ...                 channelinterfaces.RoutingModel_V1,
        ...                 channelinterfaces.RoutingModel_V2,
        ...             ],
        ...             model.routingmodels[0],
        ...         ).get_partialdischargedownstream()
        >>> model.calc_test_v4 = MethodType(Calc_Test_V4.__call__, model)
        >>> FuncConverter(model, "calc_test_v4", model.calc_test_v4).pyxlines
            cpdef inline void calc_test_v4(self) nogil:
                (<masterinterface.MasterInterface>self.routingmodels[0]).\
get_partialdischargedownstream()
        <BLANKLINE>
        """

        def _get_cytype(name_: str) -> str:
            pytype = annotations_[name_]
            if pytype in TYPE2STR:
                return TYPE2STR[pytype]
            if pytype.__module__.startswith("hydpy.interfaces."):
                return "masterinterface.MasterInterface"
            return f"{pytype.__module__.split('.')[-1]}.{pytype.__name__}"

        annotations_ = get_type_hints(self.func)
        lines = ["    " + line for line in self.cleanlines]
        lines[0] = lines[0].lower()
        inline = " inline" if self.inline else ""
        lines[0] = lines[0].replace("def ", f"cpdef{inline} {_get_cytype('return')} ")
        lines[0] = lines[0].replace("):", f"){_nogil}:")
        for name in self.untypedarguments:
            cytype = _get_cytype(name)
            lines[0] = lines[0].replace(f", {name},", f", {cytype} {name},")
            lines[0] = lines[0].replace(f", {name})", f", {cytype} {name})")
        code = inspect.getsource(self.func)
        for name in self.untypedinternalvarnames:
            if (f" {name}: float" in code) or name.startswith("d_"):
                cytype = "double"
            else:
                cytype = "int"
            lines.insert(1, f"        cdef {cytype} {name}")
        for idx, line in enumerate(lines):
            if "cast(" in line:
                part1, _, part23 = line.partition("cast(")
                part2, _, part3 = part23.partition(")")
                part2 = part2.strip().strip(",").rpartition(",")[2].strip()
                lines[idx] = f"{part1}(<masterinterface.MasterInterface>{part2}){part3}"
        return Lines(*lines)


def exp(double: float) -> float:
    """Cython wrapper for the |numpy.exp| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import exp
    >>> from unittest import mock
    >>> with mock.patch("numpy.exp") as func:
    ...     _ = exp(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.exp(double)


def log(double: float) -> float:
    """Cython wrapper for the |numpy.log| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import log
    >>> from unittest import mock
    >>> with mock.patch("numpy.log") as func:
    ...     _ = log(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.log(double)


def fabs(double: float) -> float:
    """Cython wrapper for the |math.exp| function of module |math| applied on a single
    |float| object.

    >>> from hydpy.cythons.modelutils import fabs
    >>> from unittest import mock
    >>> with mock.patch("math.fabs") as func:
    ...     _ = fabs(123.4)
    >>> func.call_args
    call(123.4)
    """
    return math.fabs(double)


def sin(double: float) -> float:
    """Cython wrapper for the |numpy.sin| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import sin
    >>> from unittest import mock
    >>> with mock.patch("numpy.sin") as func:
    ...     _ = sin(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.sin(double)


def cos(double: float) -> float:
    """Cython wrapper for the |numpy.cos| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import cos
    >>> from unittest import mock
    >>> with mock.patch("numpy.cos") as func:
    ...     _ = cos(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.cos(double)


def tan(double: float) -> float:
    """Cython wrapper for the |numpy.tan| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import tan
    >>> from unittest import mock
    >>> with mock.patch("numpy.tan") as func:
    ...     _ = tan(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.tan(double)


def asin(double: float) -> float:
    """Cython wrapper for the |numpy.arcsin| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import asin
    >>> from unittest import mock
    >>> with mock.patch("numpy.arcsin") as func:
    ...     _ = asin(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.arcsin(double)


def acos(double: float) -> float:
    """Cython wrapper for the |numpy.arccos| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import acos
    >>> from unittest import mock
    >>> with mock.patch("numpy.arccos") as func:
    ...     _ = acos(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.arccos(double)


def atan(double: float) -> float:
    """Cython wrapper for the |numpy.arctan| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import atan
    >>> from unittest import mock
    >>> with mock.patch("numpy.arctan") as func:
    ...     _ = atan(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.arctan(double)


def isnan(double: float) -> float:
    """Cython wrapper for the |numpy.isnan| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import isnan
    >>> from unittest import mock
    >>> with mock.patch("numpy.isnan") as func:
    ...     _ = isnan(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.isnan(double)


def isinf(double: float) -> float:
    """Cython wrapper for the |numpy.isinf| function of module |numpy| applied on a
    single |float| object.

    >>> from hydpy.cythons.modelutils import isnan
    >>> from unittest import mock
    >>> with mock.patch("numpy.isinf") as func:
    ...     _ = isinf(123.4)
    >>> func.call_args
    call(123.4)
    """
    return numpy.isinf(double)
