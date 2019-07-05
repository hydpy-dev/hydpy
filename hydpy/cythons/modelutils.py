# -*- coding: utf-8 -*-
""" This module provides utilities to build Cython models based on
Python models automatically.

.. _`issue`: https://github.com/hydpy-dev/hydpy/issues

Most model developers do not need to be aware of the features
implemented in module |modelutils|, except that they need to
initialise class |Cythonizer| within the main modules of their base
and application models (see, for example, the source code of base
model |hland| and application model |hland_v1|).

However, when implementing models with functionalities not envisaged
so far, problems might arise.  Please contact the *HydPy*
developer team then, preferably by opening an `issue`_ on GitHub.
Potentially, problems could occur when defining parameters or sequences
with larger dimensionality than anticipated.  The following
example shows the Cython code lines for the |ELSModel.get_point_states|
method of class |ELSModel|, used for deriving the |test| model.  By
now, we did only implement 0-dimensional sequences requiring this
method.  After hackishly changing the dimensionality of sequence
|test_states.S|, we still seem to get plausible results, but these
are untested in model applications:

>>> from hydpy.models.test import cythonizer
>>> pyxwriter = cythonizer.pyxwriter
>>> pyxwriter.get_point_states
            . get_point_states
    cpdef inline void get_point_states(self) nogil:
        self.sequences.states.s = \
self.sequences.states._s_points[self.numvars.idx_stage]
<BLANKLINE>

>>> pyxwriter.model.sequences.states.s.NDIM = 1
>>> pyxwriter.get_point_states
            . get_point_states
    cpdef inline void get_point_states(self) nogil:
        cdef int idx0
        for idx0 in range(self.sequences.states._s_length0):
            self.sequences.states.s[idx0] = \
self.sequences.states._s_points[self.numvars.idx_stage][idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.states.s.NDIM = 2
>>> pyxwriter.get_point_states
            . get_point_states
    cpdef inline void get_point_states(self) nogil:
        cdef int idx0, idx1
        for idx0 in range(self.sequences.states._s_length0):
            for idx1 in range(self.sequences.states._s_length1):
                self.sequences.states.s[idx0, idx1] = \
self.sequences.states._s_points[self.numvars.idx_stage][idx0, idx1]
<BLANKLINE>

>>> pyxwriter.model.sequences.states.s.NDIM = 3
>>> pyxwriter.get_point_states
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `s` is higher than expected.

The following examples show the results for some methods which are also
related to numerical integration but deal with |FluxSequence| objects.
We start with the method |ELSModel.integrate_fluxes|:

>>> pyxwriter.integrate_fluxes
            . integrate_fluxes
    cpdef inline void integrate_fluxes(self) nogil:
        cdef int jdx
        self.sequences.fluxes.q = 0.
        for jdx in range(self.numvars.idx_method):
            self.sequences.fluxes.q = \
self.sequences.fluxes.q +self.numvars.dt * s\
elf.numconsts.a_coefs[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]\
*self.sequences.fluxes._q_points[jdx]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 1
>>> pyxwriter.integrate_fluxes
            . integrate_fluxes
    cpdef inline void integrate_fluxes(self) nogil:
        cdef int jdx, idx0
        for idx0 in range(self.sequences.fluxes._q_length0):
            self.sequences.fluxes.q[idx0] = 0.
            for jdx in range(self.numvars.idx_method):
                self.sequences.fluxes.q[idx0] = \
self.sequences.fluxes.q[idx0] + self.numvars.dt * \
self.numconsts.a_coefs[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]\
*self.sequences.fluxes._q_points[jdx, idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> pyxwriter.integrate_fluxes
            . integrate_fluxes
    cpdef inline void integrate_fluxes(self) nogil:
        cdef int jdx, idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.sequences.fluxes.q[idx0, idx1] = 0.
                for jdx in range(self.numvars.idx_method):
                    self.sequences.fluxes.q[idx0, idx1] = \
self.sequences.fluxes.q[idx0, idx1] + self.numvars.dt * \
self.numconsts.a_coefs[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]\
*self.sequences.fluxes._q_points[jdx, idx0, idx1]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.integrate_fluxes
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.

Method |ELSModel.reset_sum_fluxes|:

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 0
>>> pyxwriter.reset_sum_fluxes
            . reset_sum_fluxes
    cpdef inline void reset_sum_fluxes(self) nogil:
        self.sequences.fluxes._q_sum = 0.
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 1
>>> pyxwriter.reset_sum_fluxes
            . reset_sum_fluxes
    cpdef inline void reset_sum_fluxes(self) nogil:
        cdef int idx0
        for idx0 in range(self.sequences.fluxes._q_length0):
            self.sequences.fluxes._q_sum[idx0] = 0.
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> pyxwriter.reset_sum_fluxes
            . reset_sum_fluxes
    cpdef inline void reset_sum_fluxes(self) nogil:
        cdef int idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.sequences.fluxes._q_sum[idx0, idx1] = 0.
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.reset_sum_fluxes
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.

Method |ELSModel.addup_fluxes|:

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 0
>>> pyxwriter.addup_fluxes
            . addup_fluxes
    cpdef inline void addup_fluxes(self) nogil:
        self.sequences.fluxes._q_sum = \
self.sequences.fluxes._q_sum + self.sequences.fluxes.q
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 1
>>> pyxwriter.addup_fluxes
            . addup_fluxes
    cpdef inline void addup_fluxes(self) nogil:
        cdef int idx0
        for idx0 in range(self.sequences.fluxes._q_length0):
            self.sequences.fluxes._q_sum[idx0] = \
self.sequences.fluxes._q_sum[idx0] + self.sequences.fluxes.q[idx0]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> pyxwriter.addup_fluxes
            . addup_fluxes
    cpdef inline void addup_fluxes(self) nogil:
        cdef int idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.sequences.fluxes._q_sum[idx0, idx1] = \
self.sequences.fluxes._q_sum[idx0, idx1] + self.sequences.fluxes.q[idx0, idx1]
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.addup_fluxes
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.

Method |ELSModel.calculate_error|:

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 0
>>> pyxwriter.calculate_error
            . calculate_error
    cpdef inline void calculate_error(self) nogil:
        self.numvars.error = 0.
        self.numvars.error = max(self.numvars.error, \
fabs(self.sequences.fluxes._q_results[self.numvars.idx_method]-\
self.sequences.fluxes._q_results[self.numvars.idx_method-1]))
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 1
>>> pyxwriter.calculate_error
            . calculate_error
    cpdef inline void calculate_error(self) nogil:
        self.numvars.error = 0.
        cdef int idx0
        for idx0 in range(self.sequences.fluxes._q_length0):
            self.numvars.error = max(self.numvars.error, \
abs(self.sequences.fluxes._q_results[self.numvars.idx_method, idx0]-\
self.sequences.fluxes._q_results[self.numvars.idx_method-1, idx0]))
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 2
>>> pyxwriter.calculate_error
            . calculate_error
    cpdef inline void calculate_error(self) nogil:
        self.numvars.error = 0.
        cdef int idx0, idx1
        for idx0 in range(self.sequences.fluxes._q_length0):
            for idx1 in range(self.sequences.fluxes._q_length1):
                self.numvars.error = max(self.numvars.error, \
abs(self.sequences.fluxes._q_results[self.numvars.idx_method, idx0, idx1]\
-self.sequences.fluxes._q_results[self.numvars.idx_method-1, idx0, idx1]))
<BLANKLINE>

>>> pyxwriter.model.sequences.fluxes.q.NDIM = 3
>>> pyxwriter.calculate_error
Traceback (most recent call last):
...
NotImplementedError: NDIM of sequence `q` is higher than expected.
"""
# import...
# ...from standard library
import os
import sys
import platform
import shutil
import copy
import inspect
import importlib
import distutils.core
import distutils.extension
# from Cython import Build (the actual import command has been moved to method
# `compile_` of class `Cythonizer` due to PyInstaller incompatibility)

import math
import functools
import types
from typing import *
# ...third party modules
import numpy
# ...from HydPy
import hydpy
from hydpy import config
from hydpy import cythons
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import printtools
from hydpy.core import sequencetools
from hydpy.core import testtools
if TYPE_CHECKING:
    from hydpy.core import typingtools


def get_dllextension() -> str:
    """Return the DLL file extension for the current operating system.

    The returned value depends on the response of function |platform.system|
    of module |platform|.  |get_dllextension| returns `.pyd` if
    |platform.system| returns the string "windows" and `.so` for
    all other strings:

    >>> from hydpy.cythons.modelutils import get_dllextension
    >>> import platform
    >>> from unittest import mock
    >>> with mock.patch.object(
    ...     platform, 'system', side_effect=lambda: 'Windows') as mocked:
    ...     get_dllextension()
    '.pyd'
    >>> with mock.patch.object(
    ...     platform, 'system', side_effect=lambda: 'Linux') as mocked:
    ...     get_dllextension()
    '.so'
    """
    if platform.system().lower() == 'windows':
        return '.pyd'
    return '.so'


_dllextension = get_dllextension()

_int = 'numpy.'+str(numpy.array([1]).dtype)+'_t'

TYPE2STR = {bool: 'bint',
            int: _int,
            parametertools.IntConstant: _int,
            float: 'double',
            str: 'str',
            None: 'void'}
"""Maps Python types to Cython compatible type declarations.

The Cython type belonging to Python's |int| is selected to agree
with numpy's default integer type on the current platform/system.
"""

NDIM2STR = {0: '',
            1: '[:]',
            2: '[:,:]',
            3: '[:,:,:]'}

_nogil = ' nogil' if config.FASTCYTHON else ''


class Lines(list):
    """Handles code lines for `.pyx` file."""

    def __init__(self, *args):
        list.__init__(self, args)

    def add(self, indent: int, line: 'typingtools.Mayberable1[str]') -> None:
        """Append the given text line with prefixed spaces following
        the given number of indentation levels.
        """
        if isinstance(line, str):
            list.append(self, indent*4*' ' + line)
        else:
            for subline in line:
                list.append(self, indent*4*' ' + subline)

    def __repr__(self):
        return '\n'.join(self) + '\n'


def get_methodheader(
        methodname: str, nogil: bool = False, idxarg: bool = False) -> str:
    """Returns the Cython method header for methods without arguments except
    `self`.

    Note the influence of the configuration flag `FASTCYTHON`:

    >>> from hydpy.cythons.modelutils import get_methodheader
    >>> from hydpy import config
    >>> config.FASTCYTHON = False
    >>> print(get_methodheader(methodname='test', nogil=True, idxarg=False))
    cpdef inline void test(self):
    >>> config.FASTCYTHON = True
    >>> print(get_methodheader(methodname='test', nogil=True, idxarg=True))
    cpdef inline void test(self, int idx) nogil:
    """
    if not config.FASTCYTHON:
        nogil = False
    header = f'cpdef inline void {methodname}(self'
    header += ', int idx)' if idxarg else ')'
    header += ' nogil:' if nogil else ':'
    return header


def decorate_method(wrapped: Callable) -> property:
    """The decorated method returns a |Lines| object including
    a method header.  However, the |Lines| object is empty if
    the respective model does not implement a method with the
    same name as the wrapped method.
    """
    def wrapper(self):
        lines = Lines()
        if hasattr(self.model, wrapped.__name__):
            print(f'            . {wrapped.__name__}')
            lines.add(1, get_methodheader(wrapped.__name__, nogil=True))
            for line in wrapped(self):
                lines.add(2, line)
        return lines
    functools.update_wrapper(wrapper, wrapped)
    wrapper.__doc__ = f'Lines of model method {wrapped.__name__}.'
    return property(wrapper)


class Cythonizer:
    """Handles the writing, compiling and initialisation of Cython models."""

    Model: Type['modeltools.Model']
    Parameters: Type[parametertools.Parameters]
    Sequences: Type[sequencetools.Sequences]
    tester: testtools.Tester

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.pymodule = frame.f_globals['__name__']
        for (key, value) in frame.f_locals.items():
            setattr(self, key, value)

    def finalise(self) -> None:
        """Test and cythonize the relevant model eventually.

        Method |Cythonizer.finalise| might call method |Cythonizer.cythonize|
        and method |Tester.perform_tests| depending on the actual values
        of the options |Options.autocompile|, |Options.usecython|, and
        |Options.skipdoctests| as well the value currently returned
        by property |Cythonizer.outdated|.  To explain and test the
        considerable amount of relevant combinations, we make use of Python's
        |unittest| `mock` library.

        First, we import the |Cythonizer| instance responsible for
        application model |hland_v1|, the classes |Cythonizer| and
        |Tester|, module |pub|, and the |unittest| `mock` library:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy.cythons.modelutils import Cythonizer
        >>> from hydpy.core.testtools import Tester
        >>> from hydpy import pub
        >>> from unittest import mock

        Second, we memorise the relevant settings to restore them later:

        >>> autocompile = pub.options.autocompile
        >>> skipdoctests = pub.options.skipdoctests
        >>> usecython = pub.options.usecython
        >>> outdated = Cythonizer.outdated

        Third, we define a test function mocking methods
        |Cythonizer.cythonize| and |Tester.perform_tests|, printing
        when the mocks are called and providing information on the
        current value of option |Options.usecython|:

        >>> def test():
        ...     sc = lambda: print(
        ...         f'calling method `cythonize` '
        ...         f'(usecython={bool(pub.options.usecython)})')
        ...     se = lambda: print(
        ...         f'calling method `perform_tests` '
        ...         f'(usecython={bool(pub.options.usecython)})')
        ...     with mock.patch.object(
        ...                 Cythonizer, 'cythonize', side_effect=sc) as mc,\\
        ...             mock.patch.object(
        ...                 Tester, 'perform_tests', side_effect=se) as mt:
        ...         cythonizer.finalise()

        With either option |Options.autocompile| or property
        |Cythonizer.outdated| being |False|, nothing happens:

        >>> pub.options.autocompile = False
        >>> Cythonizer.outdated = True
        >>> test()

        >>> pub.options.autocompile = True
        >>> Cythonizer.outdated = False
        >>> test()

        Option |Options.usecython| enables/disables the actual cythonization
        and option |Options.skipdoctests| enables/disables the testing
        of the Python model and, if available, of the Cython model:

        >>> Cythonizer.outdated = True
        >>> pub.options.usecython = False
        >>> pub.options.skipdoctests = True
        >>> test()

        >>> pub.options.skipdoctests = False
        >>> test()
        calling method `perform_tests` (usecython=False)

        >>> pub.options.usecython = True
        >>> pub.options.skipdoctests = True
        >>> test()
        calling method `cythonize` (usecython=True)

        >>> pub.options.skipdoctests = False
        >>> test()
        calling method `perform_tests` (usecython=False)
        calling method `cythonize` (usecython=False)
        calling method `perform_tests` (usecython=True)

        >>> pub.options.autocompile = autocompile
        >>> Cythonizer.outdated = outdated
        >>> pub.options.skipdoctests = skipdoctests
        """
        if hydpy.pub.options.autocompile and self.outdated:
            usecython = hydpy.pub.options.usecython
            try:
                if not hydpy.pub.options.skipdoctests:
                    hydpy.pub.options.usecython = False
                    self.tester.perform_tests()
                if usecython:
                    self.cythonize()
                    if not hydpy.pub.options.skipdoctests:
                        hydpy.pub.options.usecython = True
                        self.tester.perform_tests()
            finally:
                hydpy.pub.options.usecython = usecython

    def cythonize(self) -> None:
        """Translate Python source code of the relevant model first into
        Cython and then into C, compile it, and move the resulting dll
        file to the `autogen` subfolder of subpackage `cythons`."""
        with printtools.PrintStyle(color=33, font=4):
            print(f'Translate module/package {self.pyname}.')
        with printtools.PrintStyle(color=33, font=2):
            self.pyxwriter.write()
        with printtools.PrintStyle(color=31, font=4):
            print(f'Compile module {self.cyname}.')
        with printtools.PrintStyle(color=31, font=2):
            self.compile_()
            self.move_dll()

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
        return self.pymodule.split('.')[-1]

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
        return 'c_' + self.pyname

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
        return getattr(cythons.autogen, '__path__')[0]

    @property
    def cymodule(self) -> types.ModuleType:
        """The compiled module.

        Property |Cythonizer.cymodule| returns
        the relevant DLL module:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy.cythons.autogen import c_hland_v1
        >>> c_hland_v1 is cythonizer.cymodule
        True

        However, if this module is missing for some reasons (we define a
        wrong |Cythonizer.cyname| in the following), it tries to create
        the module first and returns it afterwards (which again fails
        in our example due to our modifications):

        >>> from hydpy.cythons.modelutils import Cythonizer
        >>> cyname = Cythonizer.cyname
        >>> Cythonizer.cyname = 'wrong'
        >>> from unittest import mock
        >>> with mock.patch.object(Cythonizer, 'cythonize') as mock:
        ...     cythonizer.cymodule
        Traceback (most recent call last):
        ...
        ModuleNotFoundError: No module named 'hydpy.cythons.autogen.wrong'
        >>> mock.call_args_list
        [call()]

        >>> Cythonizer.cyname = cyname
        """
        modulepath = f'hydpy.cythons.autogen.{self.cyname}'
        try:
            return importlib.import_module(modulepath)
        except ModuleNotFoundError:
            self.cythonize()
            return importlib.import_module(modulepath)

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
        return os.path.join(self.cydirpath, f'{self.cyname}.pyx')

    @property
    def dllfilepath(self) -> str:
        """The absolute path of the compiled module.

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy import repr_
        >>> repr_(cythonizer.dllfilepath)   # doctest: +ELLIPSIS
        '.../hydpy/cythons/autogen/c_hland_v1...'
        >>> import os
        >>> os.path.exists(cythonizer.dllfilepath)
        True
        """
        return os.path.join(self.cydirpath, f'{self.cyname}{_dllextension}')

    @property
    def buildpath(self) -> str:
        """The absolute path for temporarily build files.

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy import repr_
        >>> repr_(cythonizer.buildpath)   # doctest: +ELLIPSIS
        '.../hydpy/cythons/autogen/_build'
        """
        return os.path.join(self.cydirpath, '_build')

    @property
    def pyxwriter(self) -> 'PyxWriter':
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
        dict_['model'] = model
        model.parameters = importtools.prepare_parameters(dict_)
        model.sequences = importtools.prepare_sequences(dict_)
        return PyxWriter(self, model, self.pyxfilepath)

    @property
    def pysourcefiles(self) -> List[str]:
        """All relevant source files of the actual model.

        Source files are considered to be relevant are part of the
        *HydPy* package and if they define ancestors of the classes
        of the considered model.

        For the base model |hland|, all relevant modules seem to be covered:

        >>> from hydpy.models.hland import cythonizer
        >>> import os, pprint
        >>> pprint.pprint([fn.split(os.path.sep)[-1] for fn in
        ...                sorted(cythonizer.pysourcefiles)])
        ['masktools.py',
         'modeltools.py',
         'parametertools.py',
         'sequencetools.py',
         'testtools.py',
         'variabletools.py',
         'modelutils.py',
         'hland_control.py',
         'hland_derived.py',
         'hland_fluxes.py',
         'hland_inputs.py',
         'hland_logs.py',
         'hland_masks.py',
         'hland_model.py',
         'hland_outlets.py',
         'hland_states.py']

        However, this is not the case for application model |hland_v1|,
        where the base model files are missing.  Hence, relevant
        changes in its base model might not be detected, resulting in
        an outdated application model.  This issue is relevant for
        developers only, but we should fix it someday:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> import os, pprint
        >>> pprint.pprint([fn.split(os.path.sep)[-1] for fn in
        ...                sorted(cythonizer.pysourcefiles)])
        ['masktools.py',
         'modeltools.py',
         'parametertools.py',
         'sequencetools.py',
         'testtools.py',
         'variabletools.py',
         'modelutils.py',
         'hland_v1.py']
        """
        sourcefiles = set()
        for child in vars(self).values():
            try:
                parents = inspect.getmro(child)
            except AttributeError:
                continue
            for parent in parents:
                try:
                    sourcefile = inspect.getfile(parent)
                except TypeError:
                    break
                sourcefiles.add(sourcefile)
        return [sf for sf in sourcefiles if 'hydpy' in sf]

    @property
    def outdated(self) -> bool:
        """True/False flag indicating whether a |Cythonizer| object
        should renew its Cython model or not.

        With option |Options.forcecompiling| being |True|, property
        |Cythonizer.outdated| also return |True| under all circumstances:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> from hydpy import pub
        >>> forcecompiling = pub.options.forcecompiling
        >>> pub.options.forcecompiling = True
        >>> cythonizer.outdated
        True

        With option |Options.forcecompiling| being |False|, property
        |Cythonizer.outdated| generally return |False| if *HydPy* is
        a site-package (under the assumption the user does not modify
        his site-package files and for reasons of efficiency due to
        skipping the following tests):

        >>> pub.options.forcecompiling = False
        >>> import os
        >>> split = os.path.split
        >>> os.path.split = lambda string: ['site-packages', 'hydpy']
        >>> cythonizer.outdated
        False

        When working with a "local" *HydPy* package (that is not part
        of the site-packages directory) property |Cythonizer.outdated|
        returns |True| if the required DLL file is not available at all:

        >>> os.path.split = lambda string: ['local dir', 'hydpy']
        >>> from unittest import mock
        >>> with mock.patch.object(
        ...         type(cythonizer), 'dllfilepath',
        ...         new_callable=mock.PropertyMock) as dllfilepath:
        ...     dllfilepath.return_value = 'missing'
        ...     cythonizer.outdated
        True

        If the DLL file is available, property |Cythonizer.outdated|
        returns |True| or |False| depending on the timestamp of the
        DLL file itself and the timestamp of the newest file returned
        by property |Cythonizer.pysourcefiles|:

        >>> from hydpy import TestIO
        >>> with TestIO():
        ...     with open('new.txt', 'w'):
        ...         pass
        ...     with mock.patch.object(
        ...             type(cythonizer), 'dllfilepath',
        ...             new_callable=mock.PropertyMock) as mocked:
        ...         mocked.return_value = 'new.txt'
        ...         cythonizer.outdated
        ...     with mock.patch.object(
        ...             type(cythonizer), 'pysourcefiles',
        ...             new_callable=mock.PropertyMock) as mocked:
        ...         mocked.return_value = ['new.txt']
        ...         cythonizer.outdated
        False
        True

        >>> pub.options.forcecompiling = forcecompiling
        >>> os.path.split = split
        """
        if hydpy.pub.options.forcecompiling:
            return True
        if os.path.split(
                getattr(hydpy, '__path__')[0])[-2].endswith('-packages'):
            return False
        if not os.path.exists(self.dllfilepath):
            return True
        cydate = os.stat(self.dllfilepath).st_mtime
        for pysourcefile in self.pysourcefiles:
            pydate = os.stat(pysourcefile).st_mtime
            if pydate > cydate:
                return True
        return False

    def compile_(self) -> None:
        """Translate Cython code to C code and compile it."""
        from Cython import Build
        argv = copy.deepcopy(sys.argv)
        sys.argv = [sys.argv[0], 'build_ext', '--build-lib='+self.buildpath]
        exc_modules = [distutils.extension.Extension(
            'hydpy.cythons.autogen.'+self.cyname,
            [self.pyxfilepath], extra_compile_args=['-O2'])]
        distutils.core.setup(ext_modules=Build.cythonize(exc_modules),
                             include_dirs=[numpy.get_include()])
        sys.argv = argv

    def move_dll(self) -> None:
        """Try to find the DLL file created my method |Cythonizer.compile_|
        and to move it into the `autogen` folder of the `cythons` subpackage.

        Usually, one does not need to apply the |Cythonizer.move_dll| method
        directly.  However, if you are a model developer, you might
        see one of the following error messages from time to time:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> cythonizer.move_dll()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        OSError: After trying to cythonize model `hland_v1`, the resulting \
file `c_hland_v1...` could not be found in directory \
`.../hydpy/cythons/autogen/_build` nor any of its subdirectories.  \
The distutil report should tell whether the file has been stored \
somewhere else, is named somehow else, or could not be build at all.

        >>> import os
        >>> from unittest import mock
        >>> from hydpy import TestIO
        >>> with TestIO():   # doctest: +ELLIPSIS
        ...     with mock.patch.object(
        ...             type(cythonizer), 'buildpath',
        ...             new_callable=mock.PropertyMock) as mocked_buildpath:
        ...         mocked_buildpath.return_value = '_build'
        ...         os.makedirs('_build/subdir', exist_ok=True)
        ...         filepath = f'_build/subdir/c_hland_v1{get_dllextension()}'
        ...         with open(filepath, 'w'):
        ...             pass
        ...         with mock.patch(
        ...                 'shutil.move',
        ...                 side_effect=PermissionError('Denied!')):
        ...             cythonizer.move_dll()
        Traceback (most recent call last):
        ...
        PermissionError: After trying to cythonize module `hland_v1`, \
when trying to move the final cython module `c_hland_v1...` from \
directory `_build` to directory `.../hydpy/cythons/autogen`, the \
following error occurred: Denied! A likely error cause is that the \
cython module `c_hland_v1...` does already exist in this directory \
and is currently blocked by another Python process.  Maybe it helps \
to close all Python processes and restart the cythonization afterwards.
        """
        dirinfos = os.walk(self.buildpath)
        system_dependent_filename = None
        for dirinfo in dirinfos:
            for filename in dirinfo[2]:
                if (filename.startswith(self.cyname) and
                        filename.endswith(_dllextension)):
                    system_dependent_filename = filename
                    break
            if system_dependent_filename:
                try:
                    shutil.move(os.path.join(dirinfo[0],
                                             system_dependent_filename),
                                os.path.join(self.cydirpath,
                                             self.cyname + _dllextension))
                    break
                except BaseException:
                    objecttools.augment_excmessage(
                        f'After trying to cythonize module `{self.pyname}`, '
                        f'when trying to move the final cython module '
                        f'`{system_dependent_filename}` from directory '
                        f'`{self.buildpath}` to directory '
                        f'`{objecttools.repr_(self.cydirpath)}`',
                        f'A likely error cause is that the cython module '
                        f'`{self.cyname}{_dllextension}` does already exist '
                        f'in this directory and is currently blocked by '
                        f'another Python process.  Maybe it helps to close '
                        f'all Python processes and restart the cythonization '
                        f'afterwards.')
        else:
            raise IOError(
                f'After trying to cythonize model `{self.pyname}`, the '
                f'resulting file `{self.cyname}{_dllextension}` could '
                f'not be found in directory '
                f'`{objecttools.repr_(self.buildpath)}` nor any of its '
                f'subdirectories.  The distutil report should tell '
                f'whether the file has been stored somewhere else, is '
                f'named somehow else, or could not be build at all.')


class PyxWriter:
    """Translates the source code of Python models into Cython source code.

    Method |PyxWriter| serves as a master method, which triggers the
    complete writing process.  The other properties and methods supply
    the required code lines.  Their names are selected to match the
    names of the original Python models as close as possible.
    """

    cythonizer: Cythonizer
    model: 'modeltools.Model'
    pyxpath: str

    def __init__(self, cythonizer: Cythonizer, model: 'modeltools.Model',
                 pyxpath: str) -> None:
        self.cythonizer = cythonizer
        self.model = model
        self.pyxpath = pyxpath

    def write(self) -> None:
        """Collect the source code and write it into a Cython extension
        file ("pyx")."""
        with open(self.pyxpath, 'w') as pxf:
            print('    * cython options')
            pxf.write(repr(self.cythonoptions))
            print('    * C imports')
            pxf.write(repr(self.cimports))
            print('    * constants (if defined)')
            pxf.write(repr(self.constants))
            print('    * parameter classes')
            pxf.write(repr(self.parameters))
            print('    * sequence classes')
            pxf.write(repr(self.sequences))
            print('    * numerical parameters')
            pxf.write(repr(self.numericalparameters))
            print('    * model class')
            print('        - model attributes')
            pxf.write(repr(self.modeldeclarations))
            print('        - standard functions')
            pxf.write(repr(self.modelstandardfunctions))
            print('        - numeric functions')
            pxf.write(repr(self.modelnumericfunctions))
            print('        - additional functions')
            pxf.write(repr(self.modeluserfunctions))

    @property
    def cythonoptions(self) -> List[str]:
        """Cython option lines."""
        flag = 'False' if config.FASTCYTHON else 'True'
        return Lines('#!python',
                     f'#cython: boundscheck={flag}',
                     f'#cython: wraparound={flag}',
                     f'#cython: initializedcheck={flag}')

    @property
    def cimports(self) -> List[str]:
        """Import command lines."""
        return Lines('import numpy',
                     'cimport numpy',
                     'from libc.math cimport exp, fabs, log',
                     'from libc.stdio cimport *',
                     'from libc.stdlib cimport *',
                     'import cython',
                     'from cpython.mem cimport PyMem_Malloc',
                     'from cpython.mem cimport PyMem_Realloc',
                     'from cpython.mem cimport PyMem_Free',
                     'from hydpy.cythons.autogen import pointerutils',
                     'from hydpy.cythons.autogen cimport pointerutils',
                     'from hydpy.cythons.autogen cimport configutils',
                     'from hydpy.cythons.autogen cimport smoothutils',
                     'from hydpy.cythons.autogen cimport annutils')

    @property
    def constants(self) -> List[str]:
        """Constants declaration lines."""
        lines = Lines()
        for (name, member) in vars(self.cythonizer).items():
            if (name.isupper() and not inspect.isclass(member) and
                    isinstance(member, tuple([t for t in TYPE2STR if t]))):
                ndim = numpy.array(member).ndim
                ctype = TYPE2STR[type(member)] + NDIM2STR[ndim]
                lines.add(0, f'cdef public {ctype} {name} = {member}')
        return lines

    @property
    def parameters(self) -> List[str]:
        """Parameter declaration lines."""
        lines = Lines()
        lines.add(0, '@cython.final')
        lines.add(0, 'cdef class Parameters:')
        for subpars in self.model.parameters:
            lines.add(
                1,
                f'cdef public {objecttools.classname(subpars)} {subpars.name}')
        for subpars in self.model.parameters:
            print(f'        - {subpars.name}')
            lines.add(0, '@cython.final')
            lines.add(0, f'cdef class {objecttools.classname(subpars)}:')
            for par in subpars:
                try:
                    ctype = TYPE2STR[par.TYPE] + NDIM2STR[par.NDIM]
                except KeyError:
                    ctype = par.TYPE + NDIM2STR[par.NDIM]
                lines.add(1, f'cdef public {ctype} {par.name}')
        return lines

    @property
    def sequences(self) -> List[str]:
        """Sequence declaration lines."""
        lines = Lines()
        lines.add(0, '@cython.final')
        lines.add(0, 'cdef class Sequences:')
        for subseqs in self.model.sequences:
            lines.add(
                1,
                f'cdef public {objecttools.classname(subseqs)} {subseqs.name}')
        if self.model.sequences.states:
            lines.add(1, 'cdef public StateSequences old_states')
            lines.add(1, 'cdef public StateSequences new_states')
        for subseqs in self.model.sequences:
            print(f'        - {subseqs.name}')
            lines.add(0, '@cython.final')
            lines.add(0, f'cdef class {objecttools.classname(subseqs)}:')
            for seq in subseqs:
                ctype = f'double{NDIM2STR[seq.NDIM]}'
                if isinstance(subseqs, sequencetools.LinkSequences):
                    if seq.NDIM == 0:
                        lines.add(1, f'cdef double *{seq.name}')
                    elif seq.NDIM == 1:
                        lines.add(1, f'cdef double **{seq.name}')
                        lines.add(1, f'cdef public int len_{seq.name}')
                        lines.add(
                            1,
                            f'cdef public {TYPE2STR[int]}[:] _{seq.name}_ready')
                else:
                    lines.add(1, f'cdef public {ctype} {seq.name}')
                lines.add(1, f'cdef public int _{seq.name}_ndim')
                lines.add(1, f'cdef public int _{seq.name}_length')
                for idx in range(seq.NDIM):
                    lines.add(1, f'cdef public int _{seq.name}_length_{idx}')
                if seq.NUMERIC:
                    ctype_numeric = 'double' + NDIM2STR[seq.NDIM+1]
                    lines.add(
                        1, f'cdef public {ctype_numeric} _{seq.name}_points')
                    lines.add(
                        1, f'cdef public {ctype_numeric} _{seq.name}_results')
                    if isinstance(subseqs, sequencetools.FluxSequences):
                        lines.add(
                            1,
                            f'cdef public {ctype_numeric} '
                            f'_{seq.name}_integrals')
                        lines.add(1, f'cdef public {ctype} _{seq.name}_sum')
                if isinstance(subseqs, sequencetools.IOSequences):
                    lines.extend(self.iosequence(seq))
            if isinstance(subseqs, sequencetools.IOSequences):
                lines.extend(self.open_files(subseqs))
                lines.extend(self.close_files(subseqs))
                lines.extend(self.load_data(subseqs))
                lines.extend(self.save_data(subseqs))
            if isinstance(subseqs, sequencetools.LinkSequences):
                lines.extend(self.set_pointer(subseqs))
                lines.extend(self.get_value(subseqs))
                lines.extend(self.set_value(subseqs))
        return lines

    @staticmethod
    def iosequence(seq: sequencetools.IOSequence) -> List[str]:
        """Declaration lines for the given |IOSequence| object."""
        lines = Lines()
        lines.add(1, f'cdef public bint _{seq.name}_diskflag')
        lines.add(1, f'cdef public str _{seq.name}_path')
        lines.add(1, f'cdef FILE *_{seq.name}_file')
        lines.add(1, f'cdef public bint _{seq.name}_ramflag')
        ctype = f'double{NDIM2STR[seq.NDIM+1]}'
        lines.add(1, f'cdef public {ctype} _{seq.name}_array')
        return lines

    @staticmethod
    def open_files(subseqs: sequencetools.IOSequences) -> List[str]:
        """Open file statements."""
        print('            . open_files')
        lines = Lines()
        lines.add(1, 'cpdef open_files(self, int idx):')
        for seq in subseqs:
            lines.add(2, f'if self._{seq.name}_diskflag:')
            lines.add(
                3,
                f'self._{seq.name}_file = '
                f'fopen(str(self._{seq.name}_path).encode(), "rb+")')
            if seq.NDIM == 0:
                lines.add(3, f'fseek(self._{seq.name}_file, idx*8, SEEK_SET)')
            else:
                lines.add(
                    3,
                    f'fseek(self._{seq.name}_file, '
                    f'idx*self._{seq.name}_length*8, SEEK_SET)')
        return lines

    @staticmethod
    def close_files(subseqs: sequencetools.IOSequences) -> List[str]:
        """Close file statements."""
        print('            . close_files')
        lines = Lines()
        lines.add(1, 'cpdef inline close_files(self):')
        for seq in subseqs:
            lines.add(2, f'if self._{seq.name}_diskflag:')
            lines.add(3, f'fclose(self._{seq.name}_file)')
        return lines

    @staticmethod
    def load_data(subseqs: sequencetools.IOSequences) -> List[str]:
        """Load data statements."""
        print('            . load_data')
        lines = Lines()
        lines.add(1, f'cpdef inline void load_data(self, int idx) {_nogil}:')
        lines.add(2, 'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
        for seq in subseqs:
            lines.add(2, f'if self._{seq.name}_diskflag:')
            if seq.NDIM == 0:
                lines.add(
                    3, f'fread(&self.{seq.name}, 8, 1, self._{seq.name}_file)')
            else:
                lines.add(
                    3, f'fread(&self.{seq.name}[0], 8, '
                    f'self._{seq.name}_length, self._{seq.name}_file)')
            lines.add(2, f'elif self._{seq.name}_ramflag:')
            if seq.NDIM == 0:
                lines.add(3, f'self.{seq.name} = self._{seq.name}_array[idx]')
            else:
                indexing = ''
                for idx in range(seq.NDIM):
                    lines.add(
                        3+idx,
                        f'for jdx{idx} in '
                        f'range(self._{seq.name}_length_{idx}):')
                    indexing += f'jdx{idx}, '
                indexing = indexing[:-2]
                lines.add(
                    3+seq.NDIM,
                    f'self.{seq.name}[{indexing}] = '
                    f'self._{seq.name}_array[idx, {indexing}]')
        return lines

    @staticmethod
    def save_data(subseqs: sequencetools.IOSequences) -> List[str]:
        """Save data statements."""
        print('            . save_data')
        lines = Lines()
        lines.add(1, f'cpdef inline void save_data(self, int idx) {_nogil}:')
        lines.add(2, 'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
        for seq in subseqs:
            lines.add(2, f'if self._{seq.name}_diskflag:')
            if seq.NDIM == 0:
                lines.add(
                    3, f'fwrite(&self.{seq.name}, 8, 1, self._{seq.name}_file)')
            else:
                lines.add(
                    3,
                    f'fwrite(&self.{seq.name}[0], 8, '
                    f'self._{seq.name}_length, self._{seq.name}_file)')
            lines.add(2, f'elif self._{seq.name}_ramflag:')
            if seq.NDIM == 0:
                lines.add(3, f'self._{seq.name}_array[idx] = self.{seq.name}')
            else:
                indexing = ''
                for idx in range(seq.NDIM):
                    lines.add(
                        3+idx,
                        f'for jdx{idx} in '
                        f'range(self._{seq.name}_length_{idx}):')
                    indexing += f'jdx{idx},'
                indexing = indexing[:-1]
                lines.add(
                    3+seq.NDIM,
                    f'self._{seq.name}_array[idx, {indexing}] = '
                    f'self.{seq.name}[{indexing}]')
        return lines

    def set_pointer(self, subseqs: sequencetools.LinkSequences) -> List[str]:
        """Set pointer statements for all link sequences."""
        lines = Lines()
        for seq in subseqs:
            if seq.NDIM == 0:
                lines.extend(self.set_pointer0d(subseqs))
            break
        for seq in subseqs:
            if seq.NDIM == 1:
                lines.extend(self.alloc(subseqs))
                lines.extend(self.dealloc(subseqs))
                lines.extend(self.set_pointer1d(subseqs))
            break
        return lines

    @staticmethod
    def set_pointer0d(subseqs: sequencetools.LinkSequences) -> List[str]:
        """Set pointer statements for 0-dimensional link sequences."""
        print('            . set_pointer0d')
        lines = Lines()
        lines.add(1, 'cpdef inline set_pointer0d'
                     '(self, str name, pointerutils.PDouble value):')
        for seq in subseqs:
            lines.add(2, f'if name == "{seq.name}":')
            lines.add(3, f'self.{seq.name} = value.p_value')
        return lines

    @staticmethod
    def get_value(subseqs: sequencetools.LinkSequences) -> List[str]:
        """Get value statements for link sequences."""
        print('            . get_value')
        lines = Lines()
        lines.add(1, 'cpdef get_value(self, str name):')
        lines.add(2, 'cdef int idx')
        for seq in subseqs:
            lines.add(2, f'if name == "{seq.name}":')
            if seq.NDIM == 0:
                lines.add(3, f'return self.{seq.name}[0]')
            elif seq.NDIM == 1:
                lines.add(3, f'values = numpy.empty(self.len_{seq.name})')
                lines.add(3, f'for idx in range(self.len_{seq.name}):')
                PyxWriter._check_pointer(lines, seq)
                lines.add(4, f'values[idx] = self.{seq.name}[idx][0]')
                lines.add(3, 'return values')
        return lines

    @staticmethod
    def set_value(subseqs: sequencetools.LinkSequences) -> List[str]:
        """Set value statements for link sequences."""
        print('            . set_value')
        lines = Lines()
        lines.add(1, 'cpdef set_value(self, str name, value):')
        for seq in subseqs:
            lines.add(2, f'if name == "{seq.name}":')
            if seq.NDIM == 0:
                lines.add(3, f'self.{seq.name}[0] = value')
            elif seq.NDIM == 1:
                lines.add(3, f'for idx in range(self.len_{seq.name}):')
                PyxWriter._check_pointer(lines, seq)
                lines.add(4, f'self.{seq.name}[idx][0] = value[idx]')
        return lines

    @staticmethod
    def _check_pointer(lines: Lines, seq: sequencetools.LinkSequence) \
            -> None:
        lines.add(4, f'pointerutils.check0(self._{seq.name}_length_0)')
        lines.add(4, f'if self._{seq.name}_ready[idx] == 0:')
        lines.add(5, f'pointerutils.check1(self._{seq.name}_length_0, idx)')
        lines.add(5, f'pointerutils.check2(self._{seq.name}_ready, idx)')

    @staticmethod
    def alloc(subseqs: sequencetools.LinkSequences) -> List[str]:
        """Allocate memory statements for 1-dimensional link sequences."""
        print('            . setlength')
        lines = Lines()
        lines.add(1, f'cpdef inline alloc(self, name, {TYPE2STR[int]} length):')
        for seq in subseqs:
            lines.add(2, f'if name == "{seq.name}":')
            lines.add(3, f'self._{seq.name}_length_0 = length')
            lines.add(
                3,
                f'self._{seq.name}_ready = '
                f'numpy.full(length, 0, dtype={ TYPE2STR[int].split("_")[0]})')
            lines.add(
                3,
                f'self.{seq.name} = '
                f'<double**> PyMem_Malloc(length * sizeof(double*))')
        return lines

    @staticmethod
    def dealloc(subseqs: sequencetools.LinkSequences) -> List[str]:
        """Deallocate memory statements for 1-dimensional link sequences."""
        print('            . dealloc')
        lines = Lines()
        lines.add(1, 'cpdef inline dealloc(self, name):')
        for seq in subseqs:
            lines.add(2, f'if name == "{seq.name}":')
            lines.add(3, f'PyMem_Free(self.{seq.name})')
        return lines

    @staticmethod
    def set_pointer1d(subseqs: sequencetools.LinkSequences) -> List[str]:
        """Set_pointer statements for 1-dimensional link sequences."""
        print('            . set_pointer1d')
        lines = Lines()
        lines.add(1, 'cpdef inline set_pointer1d'
                     '(self, str name, pointerutils.PDouble value, int idx):')
        for seq in subseqs:
            lines.add(2, f'if name == "{seq.name}":')
            lines.add(3, f'self.{seq.name}[idx] = value.p_value')
            lines.add(3, f'self._{seq.name}_ready[idx] = 1')
        return lines

    @property
    def numericalparameters(self) -> List[str]:
        """Numeric parameter declaration lines."""
        lines = Lines()
        if isinstance(self.model, modeltools.SolverModel):
            lines.add(0, '@cython.final')
            lines.add(0, 'cdef class NumConsts:')
            for name in ('nmb_methods', 'nmb_stages'):
                lines.add(1, f'cdef public {TYPE2STR[int]} {name}')
            for name in ('dt_increase', 'dt_decrease'):
                lines.add(1, f'cdef public {TYPE2STR[float]} {name}')
            lines.add(1, 'cdef public configutils.Config pub')
            lines.add(1, 'cdef public double[:, :, :] a_coefs')
            lines.add(0, 'cdef class NumVars:')
            for name in ('nmb_calls', 'idx_method', 'idx_stage'):
                lines.add(1, f'cdef public {TYPE2STR[int]} {name}')
            for name in ('t0', 't1', 'dt', 'dt_est',
                         'error', 'last_error', 'extrapolated_error'):
                lines.add(1, f'cdef public {TYPE2STR[float]} {name}')
            lines.add(1, f'cdef public {TYPE2STR[bool]} f0_ready')
        return lines

    @property
    def modeldeclarations(self) -> List[str]:
        """The attribute declarations of the model class."""
        lines = Lines()
        lines.add(0, '@cython.final')
        lines.add(0, 'cdef class Model:')
        lines.add(1, 'cdef public int idx_sim')
        lines.add(1, 'cdef public Parameters parameters')
        lines.add(1, 'cdef public Sequences sequences')
        if hasattr(self.model, 'numconsts'):
            lines.add(1, 'cdef public NumConsts numconsts')
        if hasattr(self.model, 'numvars'):
            lines.add(1, 'cdef public NumVars numvars')
        return lines

    @property
    def modelstandardfunctions(self) -> List[str]:
        """The standard functions of the model class."""
        lines = Lines()
        lines.extend(self.simulate)
        lines.extend(self.iofunctions)
        lines.extend(self.new2old)
        if isinstance(self.model, modeltools.AdHocModel):
            lines.extend(self.run(self.model))
        lines.extend(self.update_inlets)
        lines.extend(self.update_outlets)
        lines.extend(self.update_receivers)
        lines.extend(self.update_senders)
        return lines

    @property
    def modelnumericfunctions(self) -> List[str]:
        """Numerical integration functions of the model class."""
        lines = Lines()
        if isinstance(self.model, modeltools.SolverModel):
            lines.extend(self.solve)
            lines.extend(self.calculate_single_terms(self.model))
            lines.extend(self.calculate_full_terms(self.model))
            lines.extend(self.get_point_states)
            lines.extend(self.set_point_states)
            lines.extend(self.set_result_states)
            lines.extend(self.get_sum_fluxes)
            lines.extend(self.set_point_fluxes)
            lines.extend(self.set_result_fluxes)
            lines.extend(self.integrate_fluxes)
            lines.extend(self.reset_sum_fluxes)
            lines.extend(self.addup_fluxes)
            lines.extend(self.calculate_error)
            lines.extend(self.extrapolate_error)
        return lines

    @property
    def simulate(self) -> List[str]:
        """Simulation statements."""
        print('                . simulate')
        lines = Lines()
        lines.add(1, f'cpdef inline void simulate(self, int idx) {_nogil}:')
        lines.add(2, 'self.idx_sim = idx')
        if self.model.sequences.inputs:
            lines.add(2, 'self.load_data()')
        if self.model.INLET_METHODS:
            lines.add(2, 'self.update_inlets()')
        if isinstance(self.model, modeltools.SolverModel):
            lines.add(2, 'self.solve()')
        else:
            lines.add(2, 'self.run()')
            if self.model.sequences.states:
                lines.add(2, 'self.new2old()')
        if self.model.OUTLET_METHODS:
            lines.add(2, 'self.update_outlets()')
        return lines

    @property
    def iofunctions(self) -> List[str]:
        """Input/output functions of the model class.

        The result of property |PyxWriter.iofunctions| depends on the
        availability of different types of sequences.  So far, the
        models implemented in *HydPy* do not reflect all possible
        combinations, which is why we modify the |hland_v1| application
        model in the following examples:

        >>> from hydpy.models.hland_v1 import cythonizer
        >>> pyxwriter = cythonizer.pyxwriter
        >>> pyxwriter.iofunctions
                    . open_files
                    . close_files
                    . load_data
                    . save_data
            cpdef inline void open_files(self):
                self.sequences.inputs.open_files(self.idx_sim)
                self.sequences.fluxes.open_files(self.idx_sim)
                self.sequences.states.open_files(self.idx_sim)
            cpdef inline void close_files(self):
                self.sequences.inputs.close_files()
                self.sequences.fluxes.close_files()
                self.sequences.states.close_files()
            cpdef inline void load_data(self) nogil:
                self.sequences.inputs.load_data(self.idx_sim)
            cpdef inline void save_data(self, int idx) nogil:
                self.sequences.fluxes.save_data(self.idx_sim)
                self.sequences.states.save_data(self.idx_sim)
        <BLANKLINE>

        >>> pyxwriter.model.sequences.fluxes = None
        >>> pyxwriter.model.sequences.states = None
        >>> pyxwriter.iofunctions
                    . open_files
                    . close_files
                    . load_data
            cpdef inline void open_files(self):
                self.sequences.inputs.open_files(self.idx_sim)
            cpdef inline void close_files(self):
                self.sequences.inputs.close_files()
            cpdef inline void load_data(self) nogil:
                self.sequences.inputs.load_data(self.idx_sim)
        <BLANKLINE>

        >>> pyxwriter.model.sequences.inputs = None
        >>> pyxwriter.iofunctions
        <BLANKLINE>
        <BLANKLINE>
        """
        lines = Lines()
        if not (self.model.sequences.inputs or
                self.model.sequences.fluxes or
                self.model.sequences.states):
            return lines
        for func in ('open_files', 'close_files', 'load_data', 'save_data'):
            if (func == 'load_data') and not self.model.sequences.inputs:
                continue
            if ((func == 'save_data') and not
                    (self.model.sequences.fluxes or
                     self.model.sequences.states)):
                continue
            print(f'            . {func}')
            nogil = func in ('load_data', 'save_data')
            idx_as_arg = func == 'save_data'
            lines.add(1, get_methodheader(
                func, nogil=nogil, idxarg=idx_as_arg))
            for subseqs in self.model.sequences:
                if func == 'load_data':
                    applyfuncs: Tuple[str, ...] = ('inputs',)
                elif func == 'save_data':
                    applyfuncs = ('fluxes', 'states')
                else:
                    applyfuncs = ('inputs', 'fluxes', 'states')
                if subseqs.name in applyfuncs:
                    if func == 'close_files':
                        lines.add(2, f'self.sequences.{subseqs.name}.{func}()')
                    else:
                        lines.add(
                            2,
                            f'self.sequences.{subseqs.name}.'
                            f'{func}(self.idx_sim)')
        return lines

    @property
    def new2old(self) -> List[str]:
        """Old states to new states statements."""
        lines = Lines()
        if self.model.sequences.states:
            print('                . new2old')
            lines.add(1, get_methodheader('new2old', nogil=True))
            lines.add(2, 'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
            for seq in self.model.sequences.states:
                if seq.NDIM == 0:
                    lines.add(
                        2,
                        f'self.sequences.old_states.{seq.name} = '
                        f'self.sequences.new_states.{seq.name}')
                else:
                    indexing = ''
                    for idx in range(seq.NDIM):
                        lines.add(
                            2+idx,
                            f'for jdx{idx} in range(self.sequences.states.'
                            f'_{seq.name}_length_{idx}):')
                        indexing += f'jdx{idx},'
                    indexing = indexing[:-1]
                    lines.add(
                        2+seq.NDIM,
                        f'self.sequences.old_states.{seq.name}[{indexing}] = '
                        f'self.sequences.new_states.{seq.name}[{indexing}]')
        return lines

    def _call_methods(self, name, methods, idx_as_arg=False):
        lines = Lines()
        if hasattr(self.model, name):
            lines.add(1, get_methodheader(name,
                                          nogil=True,
                                          idxarg=idx_as_arg))
            if idx_as_arg:
                lines.add(2, 'self.idx_sim = idx')
            anything = False
            for method in methods:
                lines.add(2, f'self.{method.__name__}()')
                anything = True
            if not anything:
                lines.add(2, 'pass')
        return lines

    @property
    def update_receivers(self) -> List[str]:
        """Lines of the model method with the same name."""
        return self._call_methods('update_receivers',
                                  self.model.RECEIVER_METHODS,
                                  True)

    @property
    def update_inlets(self) -> List[str]:
        """Lines of the model method with the same name."""
        return self._call_methods('update_inlets',
                                  self.model.INLET_METHODS)

    def run(self, model: 'modeltools.AdHocModel') -> List[str]:
        """Return the lines of the model method with the same name."""
        return self._call_methods('run', model.RUN_METHODS)

    @property
    def update_outlets(self) -> List[str]:
        """Lines of the model method with the same name."""
        return self._call_methods('update_outlets',
                                  self.model.OUTLET_METHODS)

    @property
    def update_senders(self) -> List[str]:
        """Lines of the model method with the same name."""
        return self._call_methods('update_senders',
                                  self.model.SENDER_METHODS,
                                  True)

    def calculate_single_terms(self, model: 'modeltools.SolverModel') \
            -> List[str]:
        """Return the lines of the model method with the same name."""
        lines = self._call_methods('calculate_single_terms',
                                   model.PART_ODE_METHODS)
        if lines:
            lines.insert(1, ('        self.numvars.nmb_calls ='
                             'self.numvars.nmb_calls+1'))
        return lines

    def calculate_full_terms(self, model: 'modeltools.SolverModel') \
            -> List[str]:
        """Return the lines of the model method with the same name."""
        return self._call_methods('calculate_full_terms',
                                  model.FULL_ODE_METHODS)

    @property
    def listofmodeluserfunctions(self) -> List[Tuple[str, Callable]]:
        """User functions of the model class."""
        lines = []
        for (name, member) in vars(self.model).items():
            if (inspect.ismethod(member) and
                    ('fastaccess' in inspect.getsource(member))):
                lines.append((name, member))
        return lines

    @property
    def modeluserfunctions(self) -> List[str]:
        """Model-specific functions."""
        lines = Lines()
        for (name, func) in self.listofmodeluserfunctions:
            print(f'            . {name}')
            funcconverter = FuncConverter(self.model, name, func)
            lines.extend(funcconverter.pyxlines)
        return lines

    @property
    def solve(self) -> List[str]:
        """Lines of the model method with the same name."""
        lines = Lines()
        solve = getattr(self.model, 'solve', None)
        if solve:
            print('            . solve')
            funcconverter = FuncConverter(self.model, 'solve', solve)
            lines.extend(funcconverter.pyxlines)
        return lines

    @staticmethod
    def _assign_seqvalues(subseqs, subseqs_name, target, index, load):
        from1 = f'self.sequences.{subseqs_name}.%s'
        to1 = f'self.sequences.{subseqs_name}._%s_{target}'
        if index is not None:
            to1 += f'[self.numvars.{index}]'
        if load:
            from1, to1 = to1, from1
        for seq in subseqs:
            from2 = from1 % seq.name
            to2 = to1 % seq.name
            if seq.NDIM == 0:
                yield f'{to2} = {from2}'
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield (f'for idx0 in range(self.sequences.'
                       f'{subseqs.name}._{seq.name}_length0):')
                yield f'    {to2}[idx0] = {from2}[idx0]'
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield (f'for idx0 in range(self.sequences.'
                       f'{subseqs.name}._{seq.name}_length0):')
                yield (f'    for idx1 in range(self.sequences.'
                       f'{subseqs.name}._{seq.name}_length1):')
                yield f'        {to2}[idx0, idx1] = {from2}[idx0, idx1]'
            else:
                raise NotImplementedError(
                    f'NDIM of sequence `{seq.name}` is higher than expected.')

    @decorate_method
    def get_point_states(self) -> Iterator[str]:
        """Get point statements for state sequences."""
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name='states',
            target='points',
            index='idx_stage',
            load=True)

    @decorate_method
    def set_point_states(self) -> Iterator[str]:
        """Set point statements for state sequences."""
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name='states',
            target='points',
            index='idx_stage',
            load=False)

    @decorate_method
    def set_result_states(self) -> Iterator[str]:
        """Get results statements for state sequences."""
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name='states',
            target='results',
            index='idx_method',
            load=False)

    @decorate_method
    def get_sum_fluxes(self) -> Iterator[str]:
        """Get sum statements for flux sequences."""
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numericsequences,
            subseqs_name='fluxes',
            target='sum',
            index=None,
            load=True)

    @decorate_method
    def set_point_fluxes(self) -> Iterator[str]:
        """Set point statements for flux sequences."""
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numericsequences,
            subseqs_name='fluxes',
            target='points',
            index='idx_stage',
            load=False)

    @decorate_method
    def set_result_fluxes(self) -> Iterator[str]:
        """Set result statements for flux sequences."""
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numericsequences,
            subseqs_name='fluxes',
            target='results',
            index='idx_method',
            load=False)

    @decorate_method
    def integrate_fluxes(self) -> Iterator[str]:
        """Integrate statements for flux sequences."""
        max_ndim = -1
        for seq in self.model.sequences.fluxes.numericsequences:
            max_ndim = max(max_ndim, seq.NDIM)
        if max_ndim == 0:
            yield 'cdef int jdx'
        elif max_ndim == 1:
            yield 'cdef int jdx, idx0'
        elif max_ndim == 2:
            yield 'cdef int jdx, idx0, idx1'
        for seq in self.model.sequences.fluxes.numericsequences:
            to_ = f'self.sequences.fluxes.{seq.name}'
            from_ = f'self.sequences.fluxes._{seq.name}_points'
            coefs = ('self.numvars.dt * self.numconsts.a_coefs'
                     '[self.numvars.idx_method-1, self.numvars.idx_stage, jdx]')
            if seq.NDIM == 0:
                yield f'{to_} = 0.'
                yield 'for jdx in range(self.numvars.idx_method):'
                yield f'    {to_} = {to_} +{coefs}*{from_}[jdx]'
            elif seq.NDIM == 1:
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield f'    {to_}[idx0] = 0.'
                yield '    for jdx in range(self.numvars.idx_method):'
                yield (f'        {to_}[idx0] = '
                       f'{to_}[idx0] + {coefs}*{from_}[jdx, idx0]')
            elif seq.NDIM == 2:
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield (f'    for idx1 in range('
                       f'self.sequences.fluxes._{seq.name}_length1):')
                yield f'        {to_}[idx0, idx1] = 0.'
                yield '        for jdx in range(self.numvars.idx_method):'
                yield (f'            {to_}[idx0, idx1] = '
                       f'{to_}[idx0, idx1] + {coefs}*{from_}[jdx, idx0, idx1]')
            else:
                raise NotImplementedError(
                    f'NDIM of sequence `{seq.name}` is higher than expected.')

    @decorate_method
    def reset_sum_fluxes(self) -> Iterator[str]:
        """Reset sum statements for flux sequences."""
        for seq in self.model.sequences.fluxes.numericsequences:
            to_ = f'self.sequences.fluxes._{seq.name}_sum'
            if seq.NDIM == 0:
                yield f'{to_} = 0.'
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield f'    {to_}[idx0] = 0.'
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield (f'    for idx1 in '
                       f'range(self.sequences.fluxes._{seq.name}_length1):')
                yield f'        {to_}[idx0, idx1] = 0.'
            else:
                raise NotImplementedError(
                    f'NDIM of sequence `{seq.name}` is higher than expected.')

    @decorate_method
    def addup_fluxes(self) -> Iterator[str]:
        """Add up statements for flux sequences."""
        for seq in self.model.sequences.fluxes.numericsequences:
            to_ = f'self.sequences.fluxes._{seq.name}_sum'
            from_ = f'self.sequences.fluxes.{seq.name}'
            if seq.NDIM == 0:
                yield f'{to_} = {to_} + {from_}'
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield f'    {to_}[idx0] = {to_}[idx0] + {from_}[idx0]'
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield (f'    for idx1 in '
                       f'range(self.sequences.fluxes._{seq.name}_length1):')
                yield (f'        {to_}[idx0, idx1] = '
                       f'{to_}[idx0, idx1] + {from_}[idx0, idx1]')
            else:
                raise NotImplementedError(
                    f'NDIM of sequence `{seq.name}` is higher than expected.')

    @decorate_method
    def calculate_error(self) -> Iterator[str]:
        """Calculate error statements."""
        to_ = 'self.numvars.error'
        index = 'self.numvars.idx_method'
        yield f'{to_} = 0.'
        for seq in self.model.sequences.fluxes.numericsequences:
            from_ = f'self.sequences.fluxes._{seq.name}_results'
            if seq.NDIM == 0:
                yield (f'{to_} = '
                       f'max({to_}, fabs({from_}[{index}]-{from_}[{index}-1]))')
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield (f'    {to_} = max({to_}, '
                       f'abs({from_}[{index}, idx0]-{from_}[{index}-1, idx0]))')
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield (f'for idx0 in '
                       f'range(self.sequences.fluxes._{seq.name}_length0):')
                yield (f'    for idx1 in '
                       f'range(self.sequences.fluxes._{seq.name}_length1):')
                yield (f'        {to_} = max({to_}, abs({from_}[{index}, '
                       f'idx0, idx1]-{from_}[{index}-1, idx0, idx1]))')
            else:
                raise NotImplementedError(
                    f'NDIM of sequence `{seq.name}` is higher than expected.')

    @property
    def extrapolate_error(self) -> List[str]:
        """Extrapolate error statements."""
        lines = Lines()
        extrapolate_error = getattr(self.model, 'extrapolate_error', None)
        if extrapolate_error:
            print('            . extrapolate_error')
            funcconverter = FuncConverter(
                self.model, 'extrapolate_error', extrapolate_error)
            lines.extend(funcconverter.pyxlines)
        return lines


class FuncConverter:
    """Helper class for class |PyxWriter| that analyses Python functions
    and provides the required Cython code via property
    |FuncConverter.pyxlines|."""

    model: 'modeltools.Model'
    funcname: str
    func: Callable

    def __init__(
            self, model: 'modeltools.Model', funcname: str, func: Callable):
        self.model = model
        self.funcname = funcname
        vars(self)['func'] = func

    @property
    def argnames(self) -> List[str]:
        """The argument names of the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).argnames
        ['self']
        """
        return inspect.getargs(self.func.__code__)[0]

    @property
    def varnames(self) -> Tuple[str, ...]:
        """The variable names of the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).varnames
        ('self', 'con', 'inp', 'flu', 'k')
        """
        return self.func.__code__.co_varnames

    @property
    def locnames(self) -> List[str]:
        """The variable names of the handled function except for
        the argument names.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).locnames
        ['con', 'inp', 'flu', 'k']
        """
        return [vn for vn in self.varnames if vn not in self.argnames]

    @property
    def subgroupnames(self) -> List[str]:
        """The complete names of the subgroups relevant for the current
        function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).subgroupnames
        ['parameters.control', 'sequences.inputs', 'sequences.fluxes']
        """
        names = []
        for groupname in ('parameters', 'sequences'):
            for subgroup in getattr(self.model, groupname):
                if subgroup.name[:3] in self.varnames:
                    names.append(groupname + '.' + subgroup.name)
        if 'old' in self.varnames:
            names.append('sequences.old_states')
        if 'new' in self.varnames:
            names.append('sequences.new_states')
        return names

    @property
    def subgroupshortcuts(self) -> List[str]:
        """The abbreviated names of the subgroups relevant for the current
        function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).subgroupshortcuts
        ['con', 'inp', 'flu']
        """
        return [name.split('.')[-1][:3] for name in self.subgroupnames]

    @property
    def untypedvarnames(self) -> List[str]:
        """The names of the untyped variables used in the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).untypedvarnames
        ['k']
        """
        return [name for name in self.varnames
                if name not in self.subgroupshortcuts + ['self']]

    @property
    def untypedarguments(self) -> List[str]:
        """The names of the untyped arguments used by the current function.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).untypedarguments
        []
        """
        defline = self.cleanlines[0]
        return [name for name in self.untypedvarnames
                if ((f', {name},' in defline) or
                    (f', {name})' in defline))]

    @property
    def untypedinternalvarnames(self) -> List[str]:
        """The names of the untyped variables used in the current function
        except for those of the arguments.

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, None, model.calc_tc_v1).untypedinternalvarnames
        ['k']
        """
        return [name for name in self.untypedvarnames if
                name not in self.untypedarguments]

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
        """
        code = inspect.getsource(self.func)
        code = '\n'.join(code.split('"""')[::2])
        code = code.replace('modelutils.', '')
        for (name, shortcut) in zip(self.subgroupnames,
                                    self.subgroupshortcuts):
            code = code.replace(f'{shortcut}.', f'self.{name}.')
        code = self.remove_linebreaks_within_equations(code)
        lines = code.splitlines()
        self.remove_imath_operators(lines)
        lines[0] = f'def {self.funcname}(self):'
        lines = [l.split('#')[0] for l in lines]
        lines = [l for l in lines if 'fastaccess' not in l]
        lines = [l.rstrip() for l in lines if l.rstrip()]
        return Lines(*lines)

    @staticmethod
    def remove_linebreaks_within_equations(code: str) -> str:
        r"""Remove line breaks within equations.

        The following example is not an exhaustive test but shows
        how the method works in principle:

        >>> code = 'asdf = \\\n(a\n+b)'
        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> FuncConverter.remove_linebreaks_within_equations(code)
        'asdf = (a+b)'
        """
        code = code.replace('\\\n', '')
        chars = []
        counter = 0
        for char in code:
            if char in ('(', '[', '{'):
                counter += 1
            elif char in (')', ']', '}'):
                counter -= 1
            if not (counter and (char == '\n')):
                chars.append(char)
        return ''.join(chars)

    @staticmethod
    def remove_imath_operators(lines: List[str]):
        """Remove mathematical expressions that require Pythons global
        interpreter locking mechanism.

        The following example is not an exhaustive test but shows
        how the method works in principle:

        >>> lines = ['    x += 1*1']
        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> FuncConverter.remove_imath_operators(lines)
        >>> lines
        ['    x = x + (1*1)']
        """
        for idx, line in enumerate(lines):
            for operator in ('+=', '-=', '**=', '*=', '//=', '/=', '%='):
                sublines = line.split(operator)
                if len(sublines) > 1:
                    indent = line.count(' ') - line.lstrip().count(' ')
                    sublines = [sl.strip() for sl in sublines]
                    line = (f'{indent*" "}{sublines[0]} = '
                            f'{sublines[0]} {operator[:-1]} ({sublines[1]})')
                    lines[idx] = line

    @property
    def pyxlines(self) -> List[str]:
        """Cython code lines of the current function.

        Assumptions:
          * The function shall be a method.
          * The method shall be inlined.
          * The method returns nothing.
          * All method arguments are of type `int` (except self).
          * Local variables are generally of type `int` but of type `double`
            when their name starts with `d_`.

        A real example:

        >>> from hydpy.cythons.modelutils import FuncConverter
        >>> from hydpy import prepare_model, pub
        >>> with pub.options.usecython(False):
        ...     model = prepare_model('hland_v1')
        >>> FuncConverter(model, 'calc_tc_v1', model.calc_tc_v1).pyxlines
            cpdef inline void calc_tc_v1(self)  nogil:
                cdef int k
                for k in range(self.parameters.control.nmbzones):
                    self.sequences.fluxes.tc[k] = \
self.sequences.inputs.t-self.parameters.control.tcalt[k]*\
(self.parameters.control.zonez[k]-self.parameters.control.zrelt)
        <BLANKLINE>

        An example where we mock untyped arguments:

        >>> from unittest import mock
        >>> with mock.patch.object(
        ...         FuncConverter, 'untypedarguments',
        ...         new_callable=mock.PropertyMock) as untypedarguments:
        ...     untypedarguments.return_value = ['x', 'y']
        ...     with mock.patch.object(
        ...             FuncConverter, 'cleanlines',
        ...             new_callable=mock.PropertyMock) as cleanlines:
        ...         cleanlines.return_value = ['def calc_tc_v1(self, x, y):',
        ...                                    '    pass']
        ...         FuncConverter(
        ...             model, 'calc_tc_v1', model.calc_tc_v1).pyxlines
            cpdef inline void calc_tc_v1(self, int x, int y)  nogil:
                cdef int k
                pass
        <BLANKLINE>
        """
        lines = ['    '+line for line in self.cleanlines]
        lines[0] = lines[0].replace('def ', 'cpdef inline void ')
        lines[0] = lines[0].replace('):', f') {_nogil}:')
        for name in self.untypedarguments:
            lines[0] = lines[0].replace(f', {name},', f', int {name},')
            lines[0] = lines[0].replace(f', {name})', f', int {name})')
        for name in self.untypedinternalvarnames:
            if name.startswith('d_'):
                lines.insert(1, '        cdef double ' + name)
            else:
                lines.insert(1, '        cdef int ' + name)
        return Lines(*lines)


def exp(double: float) -> float:
    """Cython wrapper the |numpy.exp| function of module |numpy| applied
    on a single |float| object."""
    return numpy.exp(double)


def log(double: float) -> float:
    """Cython wrapper the |numpy.log| function of module |numpy| applied
    on a single |float| object."""
    return numpy.log(double)


def fabs(double: float) -> float:
    """Cython wrapper the |math.exp| function of module |math| applied
    on a single |float| object."""
    return math.fabs(double)
