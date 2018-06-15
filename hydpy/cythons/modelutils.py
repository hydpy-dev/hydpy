# -*- coding: utf-8 -*-
""" This module provides utilities to build and apply cython models."""
# import...
# ...from standard library
from __future__ import division, print_function
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
# ...third party modules
import numpy
# ...from HydPy
from hydpy import pub
from hydpy import cythons
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import printtools
from hydpy.core import sequencetools


if platform.system().lower() == 'windows':
    dllextension = '.pyd'
    """The dll file extension on the respective system."""
else:
    dllextension = '.so'

_int = 'numpy.'+str(numpy.array([1]).dtype)+'_t'

TYPE2STR = {bool: 'bint',
            int: _int,
            parametertools.IntConstant: _int,
            float: 'double',
            str: 'str',
            None: 'void'}
"""Maps Python types to Cython compatible type declarations.

The Cython type belonging to Python's |int| is selected to be in
agreement with numpy's default integer type on the respective platform/system.
"""

NDIM2STR = {0: '',
            1: '[:]',
            2: '[:,:]',
            3: '[:,:,:]'}

_nogil = ' nogil' if pub.options.fastcython else ''


class Lines(list):
    """Handles lines to be written into a `.pyx` file."""

    def __init__(self, *args):
        list.__init__(self, args)

    def add(self, indent, line):
        """Appends the given text line with prefixed spaces in accordance with
        the given number of indentation levels.
        """
        if isinstance(line, abctools.StringABC):
            list.append(self, indent*4*' ' + line)
        else:
            for subline in line:
                list.append(self, indent*4*' ' + subline)

    def __repr__(self):
        return '\n'.join(self) + '\n'


def method_header(method_name, nogil=False, idx_as_arg=False):
    """Returns the Cython method header for methods without arguments except
    `self`."""
    if not pub.options.fastcython:
        nogil = False
    header = 'cpdef inline void %s(self' % method_name
    header += ', int idx)' if idx_as_arg else ')'
    header += ' nogil:' if nogil else ':'
    return header


def decorate_method(wrapped):
    """The decorated method will return a |Lines| object including
    a method header.  However, the |Lines| object will be empty if
    the respective model does not implement a method with the same
    name as the wrapped method.
    """
    def wrapper(self):
        lines = Lines()
        if hasattr(self.model, wrapped.__name__):
            print('            . %s' % wrapped.__name__)
            lines.add(1, method_header(wrapped.__name__, nogil=True))
            for line in wrapped(self):
                lines.add(2, line)
        return lines
    functools.update_wrapper(wrapper, wrapped)
    wrapper.__doc__ = 'Lines of model method %s.' % wrapped.__name__
    return property(wrapper)


class Cythonizer(object):
    """Handles the writing, compiling and initialization of cython models.
    """

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.pymodule = frame.f_globals['__name__']
        for (key, value) in frame.f_locals.items():
            setattr(self, key, value)

    def complete(self):
        if (not pub._is_hydpy_bundled) and self.outdated:
            usecython = pub.options.usecython
            try:
                if not pub.options.skipdoctests:
                    pub.options.usecython = False
                    self.tester.doit()
                if usecython:
                    self.doit()
                    if not pub.options.skipdoctests:
                        pub.options.usecython = True
                        self.tester.doit()
            finally:
                pub.options.usecython = usecython

    def doit(self):
        with printtools.PrintStyle(color=33, font=4):
            print('Translate module/package %s.' % self.pyname)
        with printtools.PrintStyle(color=33, font=2):
            self.pyxwriter.write()
        with printtools.PrintStyle(color=31, font=4):
            print('Compile module %s.' % self.cyname)
        with printtools.PrintStyle(color=31, font=2):
            self.compile_()
            self.move_dll()

    @property
    def pyname(self):
        """Name of the compiled module."""
        if self.pymodule.endswith('__init__'):
            return self.pymodule.split('.')[-2]
        else:
            return self.pymodule.split('.')[-1]

    @property
    def cyname(self):
        """Name of the compiled module."""
        return 'c_' + self.pyname

    @property
    def cydirpath(self):
        """Absolute path of the directory containing the compiled modules."""
        return cythons.autogen.__path__[0]

    @property
    def cymodule(self):
        """The compiled module."""
        return importlib.import_module('hydpy.cythons.autogen.'+self.cyname)

    @property
    def cyfilepath(self):
        """Absolute path of the compiled module."""
        return os.path.join(self.cydirpath, self.cyname+'.pyx')

    @property
    def buildpath(self):
        """Absolute path for temporarily build files."""
        return os.path.join(self.cydirpath, '_build')

    @property
    def pyxwriter(self):
        """Update the pyx file."""
        model = self.Model()
        if hasattr(self, 'Parameters'):
            model.parameters = self.Parameters(vars(self))
        else:
            model.parameters = parametertools.Parameters(vars(self))
        if hasattr(self, 'Sequences'):
            model.sequences = self.Sequences(model=model, **vars(self))
        else:
            model.sequences = sequencetools.Sequences(model=model,
                                                      **vars(self))
        return PyxWriter(self, model, self.cyfilepath)

    @property
    def pysourcefiles(self):
        """All source files of the actual models Python classes and their
        respective base classes."""
        sourcefiles = set()
        for (name, child) in vars(self).items():
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
        return Lines(*sourcefiles)

    @property
    def outdated(self):
        """True if at least one of the |Cythonizer.pysourcefiles| is
        newer than the compiled file under |Cythonizer.cyfilepath|,
        otherwise False.
        """
        if not os.path.exists(self.cyfilepath):
            return True
        cydate = os.stat(self.cyfilepath).st_mtime
        for pysourcefile in self.pysourcefiles:
            pydate = os.stat(pysourcefile).st_mtime
            if pydate > cydate:
                return True
        return False

    def compile_(self):
        """Translate cython code to C code and compile it."""
        from Cython import Build
        argv = copy.deepcopy(sys.argv)
        sys.argv = [sys.argv[0], 'build_ext', '--build-lib='+self.buildpath]
        exc_modules = [
                distutils.extension.Extension(
                        'hydpy.cythons.autogen.'+self.cyname,
                        [self.cyfilepath], extra_compile_args=['-O2'])]
        distutils.core.setup(ext_modules=Build.cythonize(exc_modules),
                             include_dirs=[numpy.get_include()])
        sys.argv = argv

    def move_dll(self):
        """Try to find the resulting dll file and to move it into the
        `cythons` package.

        Things to be aware of:
          * The file extension either `pyd` (Window) or `so` (Linux).
          * The folder containing the dll file is system dependent, but is
            always a subfolder of the `cythons` package.
          * Under Linux, the filename might contain system information, e.g.
            ...cpython-36m-x86_64-linux-gnu.so.
        """
        dirinfos = os.walk(self.buildpath)
        next(dirinfos)
        system_dependent_filename = None
        for dirinfo in dirinfos:
            for filename in dirinfo[2]:
                if (filename.startswith(self.cyname) and
                        filename.endswith(dllextension)):
                    system_dependent_filename = filename
                    break
            if system_dependent_filename:
                try:
                    shutil.move(os.path.join(dirinfo[0],
                                             system_dependent_filename),
                                os.path.join(self.cydirpath,
                                             self.cyname+dllextension))
                    break
                except BaseException:
                    prefix = ('After trying to cythonize module %s, when '
                              'trying to move the final cython module %s '
                              'from directory %s to directory %s'
                              % (self.pyname, system_dependent_filename,
                                 self.buildpath, self.cydirpath))
                    suffix = ('A likely error cause is that the cython module '
                              '%s does already exist in this directory and is '
                              'currently blocked by another Python process.  '
                              'Maybe it helps to close all Python processes '
                              'and restart the cyhonization afterwards.'
                              % self.cyname+dllextension)
                    objecttools.augment_excmessage(prefix, suffix)
        else:
            raise IOError('After trying to cythonize module %s, the resulting '
                          'file %s could neither be found in directory %s nor '
                          'its subdirectories.  The distul report should tell '
                          'whether the file has been stored somewhere else,'
                          'is named somehow else, or could not be build at '
                          'all.' % self.buildpath)

    def __dir__(self):
        return objecttools.dir_(self)


class PyxWriter(object):
    """Writes a new pyx file into framework.models.cython when initialized.
    """

    def __init__(self, cythonizer, model, pyxpath):
        self.cythonizer = cythonizer
        self.model = model
        self.pyxpath = pyxpath

    def write(self):
        with open(self.pyxpath, 'w') as pxf:
            print('    %s' % '* cython options')
            pxf.write(repr(self.cythonoptions))
            print('    %s' % '* C imports')
            pxf.write(repr(self.cimports))
            print('    %s' % '* constants (if defined)')
            pxf.write(repr(self.constants))
            print('    %s' % '* parameter classes')
            pxf.write(repr(self.parameters))
            print('    %s' % '* sequence classes')
            pxf.write(repr(self.sequences))
            print('    %s' % '* numerical parameters')
            pxf.write(repr(self.numericalparameters))
            print('    %s' % '* model class')
            print('        %s' % '- model attributes')
            pxf.write(repr(self.modeldeclarations))
            print('        %s' % '- standard functions')
            pxf.write(repr(self.modelstandardfunctions))
            print('        %s' % '- numeric functions')
            pxf.write(repr(self.modelnumericfunctions))
            print('        %s' % '- additional functions')
            pxf.write(repr(self.modeluserfunctions))

    @property
    def cythonoptions(self):
        """Cython option lines."""
        flag = 'False' if pub.options.fastcython else 'True'
        return Lines('#!python',
                     '#cython: boundscheck=%s' % flag,
                     '#cython: wraparound=%s' % flag,
                     '#cython: initializedcheck=%s' % flag)

    @property
    def cimports(self):
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
                     'from hydpy.cythons.autogen cimport pointerutils',
                     'from hydpy.cythons.autogen cimport configutils',
                     'from hydpy.cythons.autogen cimport smoothutils',
                     'from hydpy.cythons.autogen cimport annutils')

    @property
    def constants(self):
        """Constants declaration lines."""
        lines = Lines()
        for (name, member) in vars(self.cythonizer).items():
            if (name.isupper() and
                    (not inspect.isclass(member)) and
                    (type(member) in TYPE2STR)):
                ndim = numpy.array(member).ndim
                ctype = TYPE2STR[type(member)] + NDIM2STR[ndim]
                lines.add(0, 'cdef public %s %s = %s'
                             % (ctype, name, member))
        return lines

    @property
    def parameters(self):
        """Parameter declaration lines."""
        lines = Lines()
        lines.add(0, '@cython.final')
        lines.add(0, 'cdef class Parameters(object):')
        for subpars in self.model.parameters:
            lines.add(1, 'cdef public %s %s'
                         % (objecttools.classname(subpars), subpars.name))
        for subpars in self.model.parameters:
            print('        - %s' % subpars.name)
            lines.add(0, '@cython.final')
            lines.add(0, 'cdef class %s(object):'
                         % objecttools.classname(subpars))
            for par in subpars:
                try:
                    ctype = TYPE2STR[par.TYPE] + NDIM2STR[par.NDIM]
                except KeyError:
                    ctype = par.TYPE + NDIM2STR[par.NDIM]
                lines.add(1, 'cdef public %s %s' % (ctype, par.name))
        return lines

    @property
    def sequences(self):
        """Sequence declaration lines."""
        lines = Lines()
        lines.add(0, '@cython.final')
        lines.add(0, 'cdef class Sequences(object):')
        for subseqs in self.model.sequences:
            lines.add(1, 'cdef public %s %s'
                         % (objecttools.classname(subseqs), subseqs.name))
        if getattr(self.model.sequences, 'states', None) is not None:
            lines.add(1, 'cdef public StateSequences old_states')
            lines.add(1, 'cdef public StateSequences new_states')
        for subseqs in self.model.sequences:
            print('        - %s' % subseqs.name)
            lines.add(0, '@cython.final')
            lines.add(0, 'cdef class %s(object):'
                         % objecttools.classname(subseqs))
            for seq in subseqs:
                ctype = 'double' + NDIM2STR[seq.NDIM]
                if isinstance(subseqs, sequencetools.LinkSequences):
                    if seq.NDIM == 0:
                        lines.add(1, 'cdef double *%s' % seq.name)
                    elif seq.NDIM == 1:
                        lines.add(1, 'cdef double **%s' % seq.name)
                        lines.add(1, 'cdef public int len_%s' % seq.name)
                else:
                    lines.add(1, 'cdef public %s %s' % (ctype, seq.name))
                lines.add(1, 'cdef public int _%s_ndim' % seq.name)
                lines.add(1, 'cdef public int _%s_length' % seq.name)
                for idx in range(seq.NDIM):
                    lines.add(1, 'cdef public int _%s_length_%d'
                                 % (seq.name, idx))
                if seq.NUMERIC:
                    ctype_numeric = 'double' + NDIM2STR[seq.NDIM+1]
                    lines.add(1, 'cdef public %s _%s_points'
                                 % (ctype_numeric, seq.name))
                    lines.add(1, 'cdef public %s _%s_results'
                                 % (ctype_numeric, seq.name))
                    if isinstance(subseqs, sequencetools.FluxSequences):
                        lines.add(1, 'cdef public %s _%s_integrals'
                                     % (ctype_numeric, seq.name))
                        lines.add(1, 'cdef public %s _%s_sum'
                                     % (ctype, seq.name))
                if isinstance(subseqs, sequencetools.IOSequences):
                    lines.extend(self.iosequence(seq))
            if isinstance(subseqs, sequencetools.InputSequences):
                lines.extend(self.load_data(subseqs))
            if isinstance(subseqs, sequencetools.IOSequences):
                lines.extend(self.open_files(subseqs))
                lines.extend(self.close_files(subseqs))
                if not isinstance(subseqs, sequencetools.InputSequence):
                    lines.extend(self.save_data(subseqs))
            if isinstance(subseqs, sequencetools.LinkSequences):
                lines.extend(self.set_pointer(subseqs))
        return lines

    def iosequence(self, seq):
        """Special declaration lines for the given |IOSequence| object.
        """
        lines = Lines()
        lines.add(1, 'cdef public bint _%s_diskflag' % seq.name)
        lines.add(1, 'cdef public str _%s_path' % seq.name)
        lines.add(1, 'cdef FILE *_%s_file' % seq.name)
        lines.add(1, 'cdef public bint _%s_ramflag' % seq.name)
        ctype = 'double' + NDIM2STR[seq.NDIM+1]
        lines.add(1, 'cdef public %s _%s_array' % (ctype, seq.name))
        return lines

    def open_files(self, subseqs):
        """Open file statements."""
        print('            . open_files')
        lines = Lines()
        lines.add(1, 'cpdef open_files(self, int idx):')
        for seq in subseqs:
            lines.add(2, 'if self._%s_diskflag:' % seq.name)
            lines.add(3, 'self._%s_file = fopen(str(self._%s_path).encode(), '
                         '"rb+")' % (2*(seq.name,)))
            if seq.NDIM == 0:
                lines.add(3,
                          'fseek(self._%s_file, idx*8, SEEK_SET)' % seq.name)
            else:
                lines.add(3, 'fseek(self._%s_file, idx*self._%s_length*8, '
                             'SEEK_SET)' % (2*(seq.name,)))
        return lines

    def close_files(self, subseqs):
        """Close file statements."""
        print('            . close_files')
        lines = Lines()
        lines.add(1, 'cpdef inline close_files(self):')
        for seq in subseqs:
            lines.add(2, 'if self._%s_diskflag:' % seq.name)
            lines.add(3, 'fclose(self._%s_file)' % seq.name)
        return lines

    def load_data(self, subseqs):
        """Load data statements."""
        print('            . load_data')
        lines = Lines()
        lines.add(1, 'cpdef inline void load_data(self, int idx) %s:' % _nogil)
        lines.add(2, 'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
        for seq in subseqs:
            lines.add(2, 'if self._%s_diskflag:' % seq.name)
            if seq.NDIM == 0:
                lines.add(3, 'fread(&self.%s, 8, 1, self._%s_file)'
                             % (2*(seq.name,)))
            else:
                lines.add(3, 'fread(&self.%s[0], 8, self._%s_length, '
                             'self._%s_file)' % (3*((seq.name,))))
            lines.add(2, 'elif self._%s_ramflag:' % seq.name)
            if seq.NDIM == 0:
                lines.add(3, 'self.%s = self._%s_array[idx]' % (2*(seq.name,)))
            else:
                indexing = ''
                for idx in range(seq.NDIM):
                    lines.add(3+idx, 'for jdx%d in range(self._%s_length_%d):'
                                     % (idx, seq.name, idx))
                    indexing += 'jdx%d,' % idx
                indexing = indexing[:-1]
                lines.add(3+seq.NDIM, 'self.%s[%s] = self._%s_array[idx,%s]'
                                      % (2*(seq.name, indexing)))
        return lines

    def save_data(self, subseqs):
        """Save data statements."""
        print('            . save_data')
        lines = Lines()
        lines.add(1, 'cpdef inline void save_data(self, int idx) %s:' % _nogil)
        lines.add(2, 'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
        for seq in subseqs:
            lines.add(2, 'if self._%s_diskflag:' % seq.name)
            if seq.NDIM == 0:
                lines.add(3, 'fwrite(&self.%s, 8, 1, self._%s_file)'
                             % (2*(seq.name,)))
            else:
                lines.add(3, 'fwrite(&self.%s[0], 8, self._%s_length, '
                             'self._%s_file)' % (3*(seq.name,)))
            lines.add(2, 'elif self._%s_ramflag:' % seq.name)
            if seq.NDIM == 0:
                lines.add(3, 'self._%s_array[idx] = self.%s' % (2*(seq.name,)))
            else:
                indexing = ''
                for idx in range(seq.NDIM):
                    lines.add(3+idx, 'for jdx%d in range(self._%s_length_%d):'
                                     % (idx, seq.name, idx))
                    indexing += 'jdx%d,' % idx
                indexing = indexing[:-1]
                lines.add(3+seq.NDIM, 'self._%s_array[idx,%s] = self.%s[%s]'
                                      % (2*(seq.name, indexing)))
        return lines

    def set_pointer(self, subseqs):
        """Set_pointer functions for link sequences."""
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

    def set_pointer0d(self, subseqs):
        """Set_pointer function for 0-dimensional link sequences."""
        print('            . set_pointer0d')
        lines = Lines()
        lines.add(1, 'cpdef inline set_pointer0d'
                     '(self, str name, pointerutils.PDouble value):')
        for seq in subseqs:
            lines.add(2, 'if name == "%s":' % seq.name)
            lines.add(3, 'self.%s = value.p_value' % seq.name)
        return lines

    def alloc(self, subseqs):
        """Allocate memory for 1-dimensional link sequences."""
        print('            . setlength')
        lines = Lines()
        lines.add(1, 'cpdef inline alloc(self, name, int length):')
        for seq in subseqs:
            lines.add(2, 'if name == "%s":' % seq.name)
            lines.add(3, 'self._%s_length_0 = length' % seq.name)
            lines.add(3, 'self.%s = <double**> '
                         'PyMem_Malloc(length * sizeof(double*))' % seq.name)
        return lines

    def dealloc(self, subseqs):
        """Deallocate memory for 1-dimensional link sequences."""
        print('            . dealloc')
        lines = Lines()
        lines.add(1, 'cpdef inline dealloc(self):')
        for seq in subseqs:
            lines.add(2, 'PyMem_Free(self.%s)' % seq.name)
        return lines

    def set_pointer1d(self, subseqs):
        """Set_pointer function for 1-dimensional link sequences."""
        print('            . set_pointer1d')
        lines = Lines()
        lines.add(1, 'cpdef inline set_pointer1d'
                     '(self, str name, pointerutils.PDouble value, int idx):')
        for seq in subseqs:
            lines.add(2, 'if name == "%s":' % seq.name)
            lines.add(3, 'self.%s[idx] = value.p_value' % seq.name)
        return lines

    @property
    def numericalparameters(self):
        """Numeric parameter declaration lines."""
        lines = Lines()
        if self.model.NUMERICAL:
            lines.add(0, '@cython.final')
            lines.add(0, 'cdef class NumConsts(object):')
            for name in ('nmb_methods', 'nmb_stages'):
                lines.add(1, 'cdef public %s %s' % (TYPE2STR[int], name))
            for name in ('dt_increase', 'dt_decrease'):
                lines.add(1, 'cdef public %s %s' % (TYPE2STR[float], name))
            lines.add(1, 'cdef public configutils.Config pub')
            lines.add(1, 'cdef public double[:, :, :] a_coefs')
            lines.add(0, 'cdef class NumVars(object):')
            for name in ('nmb_calls', 'idx_method', 'idx_stage'):
                lines.add(1, 'cdef public %s %s' % (TYPE2STR[int], name))
            for name in ('t0', 't1', 'dt', 'dt_est',
                         'error', 'last_error', 'extrapolated_error'):
                lines.add(1, 'cdef public %s %s' % (TYPE2STR[float], name))
            lines.add(1, 'cdef public %s f0_ready' % TYPE2STR[bool])
        return lines

    @property
    def modeldeclarations(self):
        """Attribute declarations of the model class."""
        lines = Lines()
        lines.add(0, '@cython.final')
        lines.add(0, 'cdef class Model(object):')
        lines.add(1, 'cdef public int idx_sim')
        lines.add(1, 'cdef public Parameters parameters')
        lines.add(1, 'cdef public Sequences sequences')
        if hasattr(self.model, 'numconsts'):
            lines.add(1, 'cdef public NumConsts numconsts')
        if hasattr(self.model, 'numvars'):
            lines.add(1, 'cdef public NumVars numvars')
        return lines

    @property
    def modelstandardfunctions(self):
        """Standard functions of the model class."""
        lines = Lines()
        lines.extend(self.doit)
        lines.extend(self.iofunctions)
        lines.extend(self.new2old)
        lines.extend(self.run)
        lines.extend(self.update_inlets)
        lines.extend(self.update_outlets)
        lines.extend(self.update_receivers)
        lines.extend(self.update_senders)
        return lines

    @property
    def modelnumericfunctions(self):
        """Numerical functions of the model class."""
        lines = Lines()
        lines.extend(self.solve)
        lines.extend(self.calculate_single_terms)
        lines.extend(self.calculate_full_terms)
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
    def doit(self):
        """Do (most of) it function of the model class."""
        print('                . doit')
        lines = Lines()
        lines.add(1, 'cpdef inline void doit(self, int idx) %s:' % _nogil)
        lines.add(2, 'self.idx_sim = idx')
        if getattr(self.model.sequences, 'inputs', None) is not None:
            lines.add(2, 'self.load_data()')
        if self.model._INLET_METHODS:
            lines.add(2, 'self.update_inlets()')
        if hasattr(self.model, 'solve'):
            lines.add(2, 'self.solve()')
        else:
            lines.add(2, 'self.run()')
            if getattr(self.model.sequences, 'states', None) is not None:
                lines.add(2, 'self.new2old()')
        if self.model._OUTLET_METHODS:
            lines.add(2, 'self.update_outlets()')
        return lines

    @property
    def iofunctions(self):
        """Input/output functions of the model class."""
        lines = Lines()
        for func in ('open_files', 'close_files', 'load_data', 'save_data'):
            if ((func == 'load_data') and
                    (getattr(self.model.sequences, 'inputs', None) is None)):
                continue
            if ((func == 'save_data') and
                ((getattr(self.model.sequences, 'fluxes', None) is None) and
                 (getattr(self.model.sequences, 'states', None) is None))):
                continue
            print('            . %s' % func)
            nogil = func in ('load_data', 'save_data')
            idx_as_arg = func == 'save_data'
            lines.add(1, method_header(
                func, nogil=nogil, idx_as_arg=idx_as_arg))
            for subseqs in self.model.sequences:
                if func == 'load_data':
                    applyfuncs = ('inputs',)
                elif func == 'save_data':
                    applyfuncs = ('fluxes', 'states')
                else:
                    applyfuncs = ('inputs', 'fluxes', 'states')
                if subseqs.name in applyfuncs:
                    if func == 'close_files':
                        lines.add(2, 'self.sequences.%s.%s()'
                                     % (subseqs.name, func))
                    else:
                        lines.add(2, 'self.sequences.%s.%s(self.idx_sim)'
                                     % (subseqs.name, func))
        return lines

    @property
    def new2old(self):
        lines = Lines()
        if getattr(self.model.sequences, 'states', None) is not None:
            print('                . new2old')
            lines.add(1, method_header('new2old', nogil=True))
            lines.add(2, 'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
            for seq in self.model.sequences.states:
                if seq.NDIM == 0:
                    lines.add(2, 'self.sequences.old_states.%s = '
                                 'self.sequences.new_states.%s'
                                 % (2*(seq.name,)))
                else:
                    indexing = ''
                    for idx in range(seq.NDIM):
                        lines.add(2+idx,
                                  'for jdx%d in range('
                                  'self.sequences.states._%s_length_%d):'
                                  % (idx, seq.name, idx))
                        indexing += 'jdx%d,' % idx
                    indexing = indexing[:-1]
                    lines.add(
                        2+seq.NDIM,
                        'self.sequences.old_states.%s[%s] = '
                        'self.sequences.new_states.%s[%s]'
                        % (2*(seq.name, indexing)))
        return lines

    def _call_methods(self, name, methods, idx_as_arg=False):
        lines = Lines()
        if hasattr(self.model, name):
            lines.add(1, method_header(name,
                                       nogil=True,
                                       idx_as_arg=idx_as_arg))
            if idx_as_arg:
                lines.add(2, 'self.idx_sim = idx')
            anything = False
            for method in methods:
                lines.add(2, 'self.%s()' % method.__name__)
                anything = True
            if not anything:
                lines.add(2, 'pass')
        return lines

    @property
    def update_receivers(self):
        """Lines of model method with the same name."""
        return self._call_methods('update_receivers',
                                  self.model._RECEIVER_METHODS,
                                  True)

    @property
    def update_inlets(self):
        """Lines of model method with the same name."""
        return self._call_methods('update_inlets',
                                  self.model._INLET_METHODS)

    @property
    def run(self):
        """Lines of model method with the same name."""
        return self._call_methods('run',
                                  self.model._RUN_METHODS)

    @property
    def update_outlets(self):
        """Lines of model method with the same name."""
        return self._call_methods('update_outlets',
                                  self.model._OUTLET_METHODS)

    @property
    def update_senders(self):
        """Lines of model method with the same name."""
        return self._call_methods('update_senders',
                                  self.model._SENDER_METHODS,
                                  True)

    @property
    def calculate_single_terms(self):
        """Lines of model method with the same name."""
        lines = self._call_methods('calculate_single_terms',
                                   self.model._PART_ODE_METHODS)
        if lines:
            lines.insert(1, ('        self.numvars.nmb_calls ='
                             'self.numvars.nmb_calls+1'))
        return lines

    @property
    def calculate_full_terms(self):
        """Lines of model method with the same name."""
        return self._call_methods('calculate_full_terms',
                                  self.model._FULL_ODE_METHODS)

    @property
    def listofmodeluserfunctions(self):
        """User functions of the model class."""
        lines = []
        for (name, member) in vars(self.model.__class__).items():
            if (inspect.isfunction(member) and
                    (name not in ('run', 'new2old')) and
                    ('fastaccess' in inspect.getsource(member))):
                lines.append((name, member))
        run = vars(self.model.__class__).get('run')
        if run is not None:
            lines.append(('run', run))
        for (name, member) in vars(self.model).items():
            if (inspect.ismethod(member) and
                    ('fastaccess' in inspect.getsource(member))):
                lines.append((name, member))
        return lines

    @property
    def modeluserfunctions(self):
        lines = Lines()
        for (name, func) in self.listofmodeluserfunctions:
            print('            . %s' % name)
            funcconverter = FuncConverter(self.model, name, func)
            lines.extend(funcconverter.pyxlines)
        return lines

    @property
    def solve(self):
        lines = Lines()
        if hasattr(self.model, 'solve'):
            print('            . solve')
            funcconverter = FuncConverter(self.model, 'solve',
                                          self.model.solve)
            lines.extend(funcconverter.pyxlines)
        return lines

    @staticmethod
    def _assign_seqvalues(subseqs, subseqs_name, target, index, load):
        from1 = 'self.sequences.%s.' % subseqs_name + '%s'
        to1 = 'self.sequences.%s.' % subseqs_name + '_%s_' + target
        if index is not None:
            to1 += '[self.numvars.%s]' % index
        if load:
            from1, to1 = to1, from1
        for seq in subseqs:
            from2 = from1 % seq.name
            to2 = to1 % seq.name
            if seq.NDIM == 0:
                yield '%s = %s' % (to2, from2)
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield ('for idx0 in range(self.sequences.%s._%s_length0):'
                       % (subseqs.name, seq.name))
                yield ('    %s[idx0] = %s[idx0]'
                       % (to2, from2))
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield ('for idx0 in range(self.sequences.%s._%s_length0):'
                       % (subseqs.name, seq.name))
                yield ('    for idx1 in range(self.sequences._%s_length1):'
                       % (subseqs.name, seq.name))
                yield ('        %s[idx0, idx1] = %s[idx0, idx1]'
                       % (to2, from2))
            else:
                raise NotImplementedError(
                    'NDIM of sequence `%s` is higher than expected' % seq.name)

    @decorate_method
    def get_point_states(self):
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name='states',
            target='points',
            index='idx_stage',
            load=True)

    @decorate_method
    def set_point_states(self):
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name='states',
            target='points',
            index='idx_stage',
            load=False)

    @decorate_method
    def set_result_states(self):
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.states,
            subseqs_name='states',
            target='results',
            index='idx_method',
            load=False)

    @decorate_method
    def get_sum_fluxes(self):
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numerics,
            subseqs_name='fluxes',
            target='sum',
            index=None,
            load=True)

    @decorate_method
    def set_point_fluxes(self):
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numerics,
            subseqs_name='fluxes',
            target='points',
            index='idx_stage',
            load=False)

    @decorate_method
    def set_result_fluxes(self):
        yield self._assign_seqvalues(
            subseqs=self.model.sequences.fluxes.numerics,
            subseqs_name='fluxes',
            target='results',
            index='idx_method',
            load=False)

    @decorate_method
    def integrate_fluxes(self):
        max_ndim = -1
        for seq in self.model.sequences.fluxes.numerics:
            max_ndim = max(max_ndim, seq.NDIM)
        if max_ndim == 0:
            yield 'cdef int jdx'
        elif max_ndim == 1:
            yield 'cdef int jdx, idx0'
        elif max_ndim == 2:
            yield 'cdef int jdx, idx0, idx1'
        for seq in self.model.sequences.fluxes.numerics:
            to_ = 'self.sequences.fluxes.%s' % seq.name
            from_ = 'self.sequences.fluxes._%s_points' % seq.name
            coefs = ('self.numvars.dt * self.numconsts.a_coefs'
                     '[self.numvars.idx_method-1,self.numvars.idx_stage,jdx]')
            if seq.NDIM == 0:
                yield '%s = 0.' % to_
                yield 'for jdx in range(self.numvars.idx_method):'
                yield '    %s = %s +%s*%s[jdx]' % (to_, to_, coefs, from_)
            elif seq.NDIM == 1:
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield '    %s[idx0] = 0.' % to_
                yield '    for jdx in range(self.numvars.idx_method):'
                yield ('        %s[idx0] = %s[idx0] + %s*%s[jdx, idx0]'
                       % (to_, to_, coefs, from_))
            elif seq.NDIM == 2:
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield ('    for idx1 in range('
                       'self.sequences.fluxes._%s_length1):' % seq.name)
                yield '        %s[idx0, idx1] = 0.' % to_
                yield '        for jdx in range(self.numvars.idx_method):'
                yield ('            %s[idx0, idx1] = '
                       '%s[idx0, idx1] + %s*%s[jdx, idx0, idx1]'
                       % (to_, to_, coefs, from_))
            else:
                raise NotImplementedError(
                    'NDIM of sequence `%s` is higher than expected' % seq.name)

    @decorate_method
    def reset_sum_fluxes(self):
        for seq in self.model.sequences.fluxes.numerics:
            to_ = 'self.sequences.fluxes._%s_sum' % seq.name
            if seq.NDIM == 0:
                yield '%s = 0.' % to_
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield '    %s[idx0] = 0.' % to_
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield ('    for idx1 in range('
                       'self.sequences.fluxes._%s_length1):' % seq.name)
                yield '        %s[idx0, idx1] = 0.' % to_
            else:
                raise NotImplementedError(
                    'NDIM of sequence `%s` is higher than expected' % seq.name)

    @decorate_method
    def addup_fluxes(self):
        for seq in self.model.sequences.fluxes.numerics:
            to_ = 'self.sequences.fluxes._%s_sum' % seq.name
            from_ = 'self.sequences.fluxes.%s' % seq.name
            if seq.NDIM == 0:
                yield '%s = %s + %s' % (to_, to_, from_)
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield ('    %s[idx0] = %s[idx0] + %s[idx0]'
                       % (to_, to_, from_))
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield ('    for idx1 in range('
                       'self.sequences.fluxes._%s_length1):' % seq.name)
                yield ('        %s[idx0, idx1] = '
                       '%s[idx0, idx1] + %s[idx0, idx1]'
                       % (to_, to_, from_))
            else:
                raise NotImplementedError(
                    'NDIM of sequence `%s` is higher than expected' % seq.name)

    @decorate_method
    def calculate_error(self):
        to_ = 'self.numvars.error'
        index = 'self.numvars.idx_method'
        yield '%s = 0.' % to_
        for seq in self.model.sequences.fluxes.numerics:
            from_ = 'self.sequences.fluxes._%s_results' % seq.name
            if seq.NDIM == 0:
                yield ('%s = max(%s, fabs(%s[%s]-%s[%s-1]))'
                       % (to_, to_, from_, index, from_, index))
            elif seq.NDIM == 1:
                yield 'cdef int idx0'
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield ('    %s = max(%s, abs(%s[%s, idx0]-%s[%s-1, idx0]))'
                       % (to_, to_, from_, index, from_, index))
            elif seq.NDIM == 2:
                yield 'cdef int idx0, idx1'
                yield ('for idx0 in range(self.sequences.fluxes._%s_length0):'
                       % seq.name)
                yield ('    for idx1 in range('
                       'self.sequences.fluxes._%s_length1):' % seq.name)
                yield ('        %s = '
                       'max(%s, abs(%s[%s, idx0, idx1]-%s[%s-1, idx0, idx1]))'
                       % (to_, to_, from_, index, from_, index))
            else:
                raise NotImplementedError(
                    'NDIM of sequence `%s` is higher than expected' % seq.name)

    @property
    def extrapolate_error(self):
        lines = Lines()
        if hasattr(self.model, 'extrapolate_error'):
            print('            . extrapolate_error')
            funcconverter = FuncConverter(self.model, 'extrapolate_error',
                                          self.model.extrapolate_error)
            lines.extend(funcconverter.pyxlines)
        return lines


class FuncConverter(object):

    def __init__(self, model, funcname, func):
        self.model = model
        self.funcname = funcname
        self.func = func

    @property
    def argnames(self):
        return inspect.getargs(self.func.__code__)[0]

    @property
    def varnames(self):
        return self.func.__code__.co_varnames

    @property
    def locnames(self):
        return [vn for vn in self.varnames if vn not in self.argnames]

    @property
    def sourcelines(self):
        return Lines(*inspect.getsourcelines(self.func)[0])

    @property
    def collectornames(self):
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
    def collectorshortcuts(self):
        return [name.split('.')[-1][:3] for name in self.collectornames]

    @property
    def untypedvarnames(self):
        return [name for name in self.varnames
                if name not in (self.collectorshortcuts + ['self'])]

    @property
    def untypedarguments(self):
        defline = self.cleanlines[0]
        return [name for name in self.untypedvarnames
                if ((', %s,' % name in defline) or
                    (', %s)' % name in defline))]

    @property
    def untypedinternalvarnames(self):
        return [name for name in self.untypedvarnames if
                name not in self.untypedarguments]

    @property
    def cleanlines(self):
        """Cleaned code lines.

        Implemented cleanups:
          * eventually remove method version
          * remove docstrings
          * remove comments
          * remove empty lines
          * remove line brackes within brackets
          * replace `modelutils` with nothing
          * remove complete lines containing `fastaccess`
          * replace shortcuts with complete references
        """
        code = inspect.getsource(self.func)
        code = '\n'.join(code.split('"""')[::2])
        code = code.replace('modelutils.', '')
        for (name, shortcut) in zip(self.collectornames,
                                    self.collectorshortcuts):
            code = code.replace('%s.' % shortcut, 'self.%s.' % name)
        code = self.remove_linebreaks_within_equations(code)
        lines = code.splitlines()
        self.remove_imath_operators(lines)
        lines[0] = 'def %s(self):' % self.funcname
        lines = [l.split('#')[0] for l in lines]
        lines = [l for l in lines if 'fastaccess' not in l]
        lines = [l.rstrip() for l in lines if l.rstrip()]
        return Lines(*lines)

    @staticmethod
    def remove_linebreaks_within_equations(code):
        r"""Remove line breaks within equations.

        This is not a exhaustive test, but shows how the method works:

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
    def remove_imath_operators(lines):
        """Remove mathematical expressions that require Pythons global
        interpreter locking mechanism.

        This is not a exhaustive test, but shows how the method works:

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
                    line = ('%s%s = %s %s (%s)'
                            % (indent*' ', sublines[0], sublines[0],
                               operator[:-1], sublines[1]))
                    lines[idx] = line

    @property
    def pyxlines(self):
        """Cython code lines.

        Assumptions:
          * Function shall be a method
          * Method shall be inlined
          * Method returns nothing
          * Method arguments are of type `int` (except self)
          * Local variables are generally of type `int` but of type `double`
            when their name starts with `d_`
        """
        lines = ['    '+line for line in self.cleanlines]
        lines[0] = lines[0].replace('def ', 'cpdef inline void ')
        lines[0] = lines[0].replace('):', ') %s:' % _nogil)
        for name in self.untypedarguments:
            lines[0] = lines[0].replace(', %s ' % name, ', int %s ' % name)
            lines[0] = lines[0].replace(', %s)' % name, ', int %s)' % name)
        for name in self.untypedinternalvarnames:
            if name.startswith('d_'):
                lines.insert(1, '        cdef double ' + name)
            else:
                lines.insert(1, '        cdef int ' + name)
        return Lines(*lines)


def exp(double):
    """Cython wrapper for numpys exp function applied on a single float."""
    return numpy.exp(double)


def log(double):
    """Cython wrapper for numpys log function applied on a single float."""
    return numpy.log(double)


def fabs(double):
    """Cython wrapper for maths fabs function applied on a single float."""
    return math.fabs(double)


autodoctools.autodoc_module()
