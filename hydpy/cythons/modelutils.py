
""" This module provides utilities to build and apply cython models.

"""


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
import Cython.Build
# ...third party modules
import numpy
# ...from HydPy
from hydpy import pub
from hydpy import cythons
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import magictools

if platform.system().lower() == 'windows':
    dllextension = '.pyd'
    """The dll file extension on the respective system."""
else:
    dllextension = '.so'

TYPE2STR = {bool: 'bint',
            int: 'numpy.'+str(numpy.array([1]).dtype)+'_t',
            float: 'double',
            str: 'str',
            None: 'void'}
"""Maps Python types to Cython compatible type declarations.

The Cython type belonging to Python's :class:`int` is selected to be in
agreement with numpy's default integer type on the respective platform/system.
"""
NDIM2STR = {0: '',
            1: '[:]',
            2: '[:,:]',
            3: '[:,:,:]'}

class Lines(list):
    """Handles lines to be written into a `.pyx` file."""

    def __init__(self, *args):
        list.__init__(self, args)

    def add(self, indent, line):
        """Appends the given text line with prefixed spaces in accordance with
        the given number of indentation levels.
        """
        list.append(self, indent*4*' ' + line)

    def __repr__(self):
        return '\n'.join(self) + '\n'


class Cythonizer(object):
    """Handles the writing, compiling and initialization of cython models.
    """

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.pymodule = frame.f_globals['__name__']
        for (key, value) in frame.f_locals.items():
            setattr(self, key, value)

    def complete(self):
        if self.outdated:
            if not pub.options.skipdoctests:
                pub.options.usecython = False
                self.tester.doit()
            self.doit()
            if not pub.options.skipdoctests:
                pub.options.usecython = True
                self.tester.doit()

    def doit(self):
        with magictools.PrintStyle(color=33, font=4):
            print('Translate module/package %s.'% self.pyname)
        with magictools.PrintStyle(color=33, font=2):
            self.pyxwriter.write()
        with magictools.PrintStyle(color=31, font=4):
            print('Compile module %s.' % self.cyname)
        with magictools.PrintStyle(color=31, font=2):
            self.compile_()
            self.movedll()

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
        return cythons.__path__[0]

    @property
    def cymodule(self):
        """The compiled module."""
        return importlib.import_module('hydpy.cythons.'+self.cyname)

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
        model.parameters = self.Parameters(vars(self))
        model.sequences = self.Sequences(vars(self))
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
        """True if at least one of the :attr:`~Cythonizer.pysourcefiles`
        is newer than the compiled file under :attr:`~Cythonizer.cyfilepath`,
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
        argv = copy.deepcopy(sys.argv)
        sys.argv = [sys.argv[0], 'build_ext', '--build-lib='+self.buildpath]
        exc_modules = Cython.Build.cythonize(self.cyfilepath)
        distutils.core.setup(ext_modules=exc_modules,
                             include_dirs=[numpy.get_include()])
        sys.argv = argv

    def movedll(self):
        """Try to find the resulting dll file and to move it into the
        `cythons` package.

        Things to be aware of:
          * The file extension either `pyd` (Window) or `so` (Linux).
          * The folder containing the dll file is system dependend, but is
            always a subfolder of the `cythons` package.
          * Under Linux, the filename might contain system information, e.g.
            ...cpython-36m-x86_64-linux-gnu.so.
        """
        dirinfos = os.walk(self.buildpath)
        next(dirinfos)
        system_dependend_filename = None
        for dirinfo in dirinfos:
            for filename in dirinfo[2]:
                if (filename.startswith(self.cyname) and
                        filename.endswith(dllextension)):
                    system_dependend_filename = filename
                    break
            if system_dependend_filename:
                try:
                    shutil.move(os.path.join(dirinfo[0],
                                             system_dependend_filename),
                                os.path.join(self.cydirpath,
                                             self.cyname+dllextension))
                    break
                except BaseException:
                    prefix = ('After trying to cythonize module %s, when '
                              'trying to move the final cython module %s '
                              'from directory %s to directory %s'
                              % (self.pyname, system_dependend_filename,
                                 self.buildpath, self.cydirpath))
                    suffix = ('A likely error cause is that the cython module '
                              '%s does already exist in this directory and is '
                              'currently blocked by another Python process.  '
                              'Maybe it helps to close all Python processes '
                              'and restart the cyhonization afterwards.'
                              % self.cyname+dllextension)
                    objecttools.augmentexcmessage(prefix, suffix)
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
            print('    %s' % '* model class')
            print('        %s' % '- model attributes')
            pxf.write(repr(self.modeldeclarations))
            print('        %s' % '- standard functions')
            pxf.write(repr(self.modelstandardfunctions))
            print('        %s' % '- additional functions')
            pxf.write(repr(self.modeluserfunctions))

    @property
    def cythonoptions(self):
        """Cython option lines."""
        return Lines('#!python',
                     '#cython: boundscheck=False',
                     '#cython: wraparound=False',
                     '#cython: initializedcheck=False')

    @property
    def cimports(self):
        """Import command lines."""
        return Lines('import numpy',
                     'cimport numpy',
                     'from libc.math cimport exp',
                     'from libc.stdio cimport *',
                     'from libc.stdlib cimport *',
                     'import cython',
                     'from cpython.mem cimport PyMem_Malloc',
                     'from cpython.mem cimport PyMem_Realloc',
                     'from cpython.mem cimport PyMem_Free',
                     'from hydpy.cythons cimport pointer',
                     'from hydpy.cythons import pointer')

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
        for (name1, subpars) in self.model.parameters:
            print('        - %s' % name1)
            lines.add(0, '@cython.final')
            lines.add(0, 'cdef class %s(object):'
                         % objecttools.classname(subpars))
            for (name2, par) in subpars:
                ctype = TYPE2STR[par.TYPE] + NDIM2STR[par.NDIM]
                lines.add(1, 'cdef public %s %s' % (ctype, name2))
        return lines

    @property
    def sequences(self):
        """Sequence declaration lines."""
        lines = Lines()
        for (name1, subseqs) in self.model.sequences:
            print('        - %s' % name1)
            lines.add(0, '@cython.final')
            lines.add(0, 'cdef class %s(object):'
                         % objecttools.classname(subseqs))
            for (name2, seq) in subseqs:
                ctype = 'double' + NDIM2STR[seq.NDIM]
                if isinstance(subseqs, sequencetools.LinkSequences):
                    if seq.NDIM == 0:
                        lines.add(1, 'cdef double *%s' % name2)
                    elif seq.NDIM == 1:
                        lines.add(1, 'cdef double **%s' % name2)
                else:
                    lines.add(1, 'cdef public %s %s' % (ctype, name2))
                lines.add(1, 'cdef public int _%s_ndim' % name2)
                lines.add(1, 'cdef public int _%s_length' % name2)
                for idx in range(seq.NDIM):
                    lines.add(1, 'cdef public int _%s_length_%d'
                                 % (seq.name, idx))
                if isinstance(subseqs, sequencetools.IOSubSequences):
                    lines.extend(self.iosequence(seq))
            if isinstance(subseqs, sequencetools.InputSequences):
                lines.extend(self.loaddata(subseqs))
            if isinstance(subseqs, sequencetools.IOSubSequences):
                lines.extend(self.openfiles(subseqs))
                lines.extend(self.closefiles(subseqs))
                if not isinstance(subseqs, sequencetools.InputSequence):
                    lines.extend(self.savedata(subseqs))
            if isinstance(subseqs, sequencetools.LinkSequences):
                lines.extend(self.setpointer(subseqs))
        return lines

    def iosequence(self, seq):
        """Special declaration lines for the given
        :class:`~hydpy.core.sequencetools.IOSequence` object.
        """
        lines = Lines()
        lines.add(1, 'cdef public bint _%s_diskflag' % seq.name)
        lines.add(1, 'cdef public str _%s_path' % seq.name)
        lines.add(1, 'cdef FILE *_%s_file' % seq.name)
        lines.add(1, 'cdef public bint _%s_ramflag' % seq.name)
        ctype = 'double' + NDIM2STR[seq.NDIM+1]
        lines.add(1, 'cdef public %s _%s_array' % (ctype, seq.name))
        return lines

    def openfiles(self, subseqs):
        """Open file statements."""
        print('            . openfiles')
        lines = Lines()
        lines.add(1, 'cpdef openfiles(self, int idx):')
        for (name, seq) in subseqs:
            lines.add(2, 'if self._%s_diskflag:' % name)
            lines.add(3, 'self._%s_file = fopen(str(self._%s_path), "rb+")'
                         % (2*(name,)))
            if seq.NDIM == 0:
                lines.add(3, 'fseek(self._%s_file, idx*8, SEEK_SET)'  % name)
            else:
                lines.add(3, 'fseek(self._%s_file, idx*self._%s_length*8, '
                             'SEEK_SET)' % (2*(name,)))
        return lines

    def closefiles(self, subseqs):
        """Close file statements."""
        print('            . closefiles')
        lines = Lines()
        lines.add(1, 'cpdef inline closefiles(self):')
        for (name, seq) in sorted(subseqs):
            lines.add(2, 'if self._%s_diskflag:' % name)
            lines.add(3, 'fclose(self._%s_file)' % name)
        return lines

    def loaddata(self, subseqs):
        """Load data statements."""
        print('            . loaddata')
        lines = Lines()
        lines.add(1 ,'cpdef inline loaddata(self, int idx):')
        lines.add(2 ,'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
        for (name, seq) in subseqs:
            lines.add(2 ,'if self._%s_diskflag:' % name)
            if seq.NDIM == 0:
                lines.add(3 ,'fread(&self.%s, 8, 1, self._%s_file)'
                             % (2*(name,)))
            else:
                lines.add(3 ,'fread(&self.%s[0], 8, self._%s_length, '
                             'self._%s_file)' % (3*((name,))))
            lines.add(2 ,'elif self._%s_ramflag:' % name)
            if seq.NDIM == 0:
                lines.add(3, 'self.%s = self._%s_array[idx]' % (2*(name,)))
            else:
                indexing = ''
                for idx in range(seq.NDIM):
                    lines.add(3+idx ,'for jdx%d in range(self._%s_length_%d):'
                                     % (idx, name, idx))
                    indexing += 'jdx%d,' % idx
                indexing = indexing[:-1]
                lines.add(3+seq.NDIM, 'self.%s[%s] = self._%s_array[idx,%s]'
                                      % (2*(name, indexing)))
        return lines

    def savedata(self, subseqs):
        """Save data statements."""
        print('            . savedata')
        lines = Lines()
        lines.add(1 ,'cpdef inline savedata(self, int idx):')
        lines.add(2 ,'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
        for (name, seq) in subseqs:
            lines.add(2 ,'if self._%s_diskflag:' % name)
            if seq.NDIM == 0:
                lines.add(3 ,'fwrite(&self.%s, 8, 1, self._%s_file)'
                             % (2*(name,)))
            else:
                lines.add(3 ,'fwrite(&self.%s[0], 8, self._%s_length, '
                             'self._%s_file)' % (3*(name,)))
            lines.add(2 ,'elif self._%s_ramflag:' % name)
            if seq.NDIM == 0:
                lines.add(3, 'self._%s_array[idx] = self.%s' % (2*(name,)))
            else:
                indexing = ''
                for idx in range(seq.NDIM):
                    lines.add(3+idx ,'for jdx%d in range(self._%s_length_%d):'
                                     % (idx, name, idx))
                    indexing += 'jdx%d,' % idx
                indexing = indexing[:-1]
                lines.add(3+seq.NDIM, 'self._%s_array[idx,%s] = self.%s[%s]'
                                      % (2*(name, indexing)))
        return lines

    def setpointer(self, subseqs):
        """Setpointer functions for link sequences."""
        lines = Lines()
        for (name, seq) in subseqs:
            if seq.NDIM == 0:
                lines.extend(self.setpointer0d(subseqs))
                #lines.extend(self.getpointer0d(subseqs))
            break
        for (name, seq) in subseqs:
            if seq.NDIM == 1:
                lines.extend(self.alloc(subseqs))
                lines.extend(self.dealloc(subseqs))
                lines.extend(self.setpointer1d(subseqs))
                #lines.extend(self.getpointer1d(subseqs))
            break
        return lines

    def setpointer0d(self, subseqs):
        """Setpointer function for 0-dimensional link sequences."""
        print('            . setpointer0d')
        lines = Lines()
        lines.add(1 ,'cpdef inline setpointer0d'
                     '(self, str name, pointer.PDouble value):')
        for (name, seq) in subseqs:
            lines.add(2 ,'if name == "%s":' % name)
            lines.add(3 ,'self.%s = value.p_value' % name)
        return lines

#    def getpointer0d(self, subseqs):
#        """Get the pointer of the selected 0-dimensional link sequence."""
#        print('            . getpointer0d')
#        lines = Lines()
#        lines.add(1 ,'cpdef inline getpointer0d(self, str name):')
#        lines.add(2, 'cdef pointer.PDouble value')
#        lines.add(2, 'value = pointer.PDouble(pointer.Double(0.))')
#        for (name, seq) in subseqs:
#            lines.add(2 ,'if name == "%s":' % name)
#            lines.add(3, 'value.p_value = self.%s' % name)
#        lines.add(2, 'return value')
#        return lines

    def alloc(self, subseqs):
        """Allocate memory for 1-dimensional link sequences."""
        print('            . setlength')
        lines = Lines()
        lines.add(1 ,'cpdef inline alloc(self, name, int length):')
        for (name, seq) in subseqs:
            lines.add(2 ,'if name == "%s":' % name)
            lines.add(3, 'self._%s_length_0 = length' % name)
            lines.add(3, 'self.%s = <double**> '
                         'PyMem_Malloc(length * sizeof(double*))' % name)
        return lines

    def dealloc(self, subseqs):
        """Deallocate memory for 1-dimensional link sequences."""
        print('            . dealloc')
        lines = Lines()
        lines.add(1 ,'cpdef inline dealloc(self):')
        for (name, seq) in subseqs:
            lines.add(2, 'PyMem_Free(self.%s)' %name)
        return lines

    def setpointer1d(self, subseqs):
        """Setpointer function for 1-dimensional link sequences."""
        print('            . setpointer1d')
        lines = Lines()
        lines.add(1 ,'cpdef inline setpointer1d'
                     '(self, str name, pointer.PDouble value):')
        for (name, seq) in subseqs:
            lines.add(2 ,'if name == "%s":' % name)
            lines.add(3 ,'self.%s[self.idx_sim] = value.p_value' % name)
        return lines

#    def getpointer1d(self, subseqs):
#        """Get the pointer of the selected 1-dimensional link sequence."""
#        print('            . getpointer1d')
#        lines = Lines()
#        lines.add(1 ,'cpdef inline getpointer1d(self, str name):')
#        lines.add(2, 'cdef pointer.PPDouble values')
#        lines.add(2, 'values = pointer.PPDouble()')
#        for (name, seq) in subseqs:
#            lines.add(2 ,'if name == "%s":' % name)
#            lines.add(3, 'values.length = self._%s_length_0' % name)
#            lines.add(3, 'values.pp_value = <double**> '
#                         'PyMem_Malloc(values.length * sizeof(double*))')
#            lines.add(3, 'values.pp_value = self.%s' % name)
#        lines.add(2, 'return values')
#        return lines


    @property
    def modeldeclarations(self):
        """Attribute declarations of the model class."""
        lines = Lines()
        lines.add(0 ,'@cython.final')
        lines.add(0 ,'cdef class Model(object):')
        lines.add(1, 'cdef public int idx_sim')
        for things in (self.model.parameters, self.model.sequences):
            for (name, thing) in things:
                lines.add(1, 'cdef public %s %s'
                             % (objecttools.classname(thing), name))
        if getattr(self.model.sequences, 'states', None) is not None:
            lines.add(1, 'cdef public StateSequences old_states')
            lines.add(1, 'cdef public StateSequences new_states')
        return lines

    @property
    def modelstandardfunctions(self):
        """Standard functions of the model class."""
        lines = Lines()
        lines.extend(self.doit)
        lines.extend(self.iofunctions)
        lines.extend(self.new2old)
        if 'run' not in [tpl[0] for tpl in self.listofmodeluserfunctions]:
            lines.extend(self.run)
        return lines

    @property
    def doit(self):
        """Do (most of) it function of the model class."""
        print('                . doit')
        lines = Lines()
        lines.add(1, 'cpdef inline void doit(self):')
        if getattr(self.model.sequences, 'inputs', None) is not None:
            lines.add(2, 'self.loaddata()')
        if getattr(self.model.sequences, 'inlets', None) is not None:
            lines.add(2, 'self.updateinlets()')
        lines.add(2, 'self.run()')
        if getattr(self.model.sequences, 'outlets', None) is not None:
            lines.add(2, 'self.updateoutlets()')
        if getattr(self.model.sequences, 'states', None) is not None:
            lines.add(2, 'self.new2old()')
        if getattr(self.model.sequences, 'senders', None) is not None:
            lines.add(2, 'self.updatesenders()')
        if ((getattr(self.model.sequences, 'fluxes', None) is not None) or
            (getattr(self.model.sequences, 'states', None) is not None)):
                lines.add(2, 'self.savedata()')
        return lines

    @property
    def iofunctions(self):
        """Input/output functions of the model class."""
        lines = Lines()
        for func in ('openfiles', 'closefiles', 'loaddata', 'savedata'):
            if ((func == 'loaddata') and
                (getattr(self.model.sequences, 'inputs', None) is None)):
                continue
            if ((func == 'savedata') and
                ((getattr(self.model.sequences, 'fluxes', None) is None) and
                 (getattr(self.model.sequences, 'states', None) is None))):
                continue
            print('            . %s' % func)
            lines.add(1, 'cpdef inline void %s(self):' % func)
            for (name, subseqs) in self.model.sequences:
                if func == 'loaddata':
                    applyfuncs = ('inputs',)
                elif func == 'savedata':
                     applyfuncs = ('fluxes', 'states')
                else:
                    applyfuncs = ('inputs', 'fluxes', 'states')
                if name in applyfuncs:
                    if func == 'closefiles':
                        lines.add(2, 'self.%s.%s()' % (name, func))
                    else:
                        lines.add(2, 'self.%s.%s(self.idx_sim)' % (name, func))
        return lines

    @property
    def new2old(self):
        lines = Lines()
        if getattr(self.model.sequences, 'states', None) is not None:
            print('                . new2old')
            lines.add(1 ,'cpdef inline void new2old(self):')
            lines.add(2 ,'cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5')
            for (name, seq) in sorted(self.model.sequences.states):
                if seq.NDIM == 0:
                    lines.add(2, 'self.old_states.%s = self.new_states.%s'
                                 % (2*(name,)))
                else:
                    indexing = ''
                    for idx in range(seq.NDIM):
                        lines.add(2+idx ,
                                  'for jdx%d in range(self.states._%s_length_%d):'
                                  % (idx, name, idx))
                        indexing += 'jdx%d,' % idx
                    indexing = indexing[:-1]
                    lines.add(2+seq.NDIM,'self.old_states.%s[%s] = self.new_states.%s[%s]'
                                         % (2*(name, indexing)))
        return lines

    @property
    def run(self):
        lines = Lines()
        lines.add(1 ,'cpdef inline void run(self):')
        for method in self.model._METHODS:
            lines.add(2, 'self.%s()' % method.__name__)
        return lines

    @property
    def listofmodeluserfunctions(self):
        """User functions of the model class."""
        lines = []
        for (name, member) in vars(self.model.__class__).items():
            if (inspect.isfunction(member) and
                    (name not in  ('run', 'new2old')) and
                    ('fastaccess' in inspect.getsource(member))):
                lines.append((name, member))
        run = vars(self.model.__class__).get('run')
        if run is not None:
            lines.append(('run', run))
        return lines

    @property
    def modeluserfunctions(self):
        lines = Lines()
        for (name, func) in self.listofmodeluserfunctions:
            print('            . %s' % name)
            funcconverter = FuncConverter(self.model, name, func)
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
        for things in (self.model.parameters, self.model.sequences):
            for (name, thing) in things:
                if name[:3] in self.varnames:
                    names.append(name)
        if 'old' in self.varnames:
            names.append('old_states')
        if 'new' in self.varnames:
            names.append('new_states')
        return names

    @property
    def collectorshortcuts(self):
        return [name[:3] for name in self.collectornames]

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
        lines = code.splitlines()
        lines[0] = 'def %s(self):' % self.funcname
        lines = [l.split('#')[0] for l in lines]
        lines = [l for l in lines  if not 'fastaccess' in l]
        lines = [l.rstrip() for l in lines if l.rstrip()]
        return Lines(*lines)

    @property
    def pyxlines(self):
        """Cython code lines.

        Assumptions:
          * Function shall be a method
          * Method shall be inlined
          * Method returns nothing
          * Method arguments are of type `int` (except self)
          * Local variables are of type `int`
        """
        lines = ['    '+line for line in self.cleanlines]
        lines[0] = lines[0].replace('def ', 'cpdef inline void ')
        for name in self.untypedarguments:
            lines[0] = lines[0].replace(', %s ' % name, ', int %s ' % name)
            lines[0] = lines[0].replace(', %s)' % name, ', int %s)' % name)
        if self.untypedinternalvarnames:
            lines.insert(1, '        cdef int ' +
                            ', '.join(self.untypedinternalvarnames))
        return Lines(*lines)


def exp(double):
    """Cython wrapper for numpys exp function applied on a single float."""
    return numpy.exp(double)


