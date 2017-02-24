# -*- coding: utf-8 -*-
"""
Created on Tue Dec 27 23:23:53 2016

@author: tyralla
"""

# import...
# ...from standard library
from __future__ import division, print_function
import os
import sys
import copy
import struct
import textwrap
import warnings
# ...from site-packages
import numpy
# ...from HydPy
from . import pub
from . import timetools
from . import objecttools
from ..cythons import pointer

class Sequences(object):
    """Base class for handling all sequences of a specific model."""
    
    def __init__(self, kwargs):
        self.model = kwargs.get('model')
        cythonmodule = kwargs.get('cythonmodule')
        cymodel = kwargs.get('cymodel')
        for (name, cls) in kwargs.iteritems():
            if name.endswith('Sequences') and issubclass(cls, SubSequences):
                if cythonmodule:
                    cls_fastaccess = getattr(cythonmodule, name)
                    subseqs = cls(self, cls_fastaccess, cymodel)
                else:
                    subseqs = cls(self, None, None)
                setattr(self, subseqs.name, subseqs)
        
    def set_initvals(self, info, idx_date):
        self.states.set_initvals(info, idx_date)     

    def activate_disk(self, names=None):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'activate_disk'):
                subseqs.activate_disk(names)

    def deactivate_disk(self, names=None):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'deactivate_disk'):
                subseqs.deactivate_disk(names)

    def activate_ram(self, names=None):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'activate_ram'):
                subseqs.activate_ram(names)

    def deactivate_ram(self, names=None):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'deactivate_ram'):
                subseqs.deactivate_ram(names)
            
    def openfiles(self, idx=0):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'openfiles'):
                subseqs.openfiles(idx)
 
    def closefiles(self):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'closefiles'):
                subseqs.closefiles()

    def loaddata(self, idx):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'loaddata'):
                subseqs.loaddata(idx)
    
    def savedata(self, idx):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'savedata'):
                subseqs.savedata(idx)
    
    def reset(self):
        for (name, subseqs) in self:
            if hasattr(subseqs, 'reset'):
                subseqs.reset()
                
    def __iter__(self):
        for (key, value) in vars(self).iteritems():
            if isinstance(value, SubSequences):
                yield key, value
        
    @property
    def conditions(self):
        """Generator object yielding all conditions (class:`StateSequence` and
        :class:`LogSequence` objects).
        """
        for subseqs in ('states', 'logs'):
            for tuple_ in getattr(self, subseqs, ()):
                yield tuple_

    @property
    def hasconditions(self):
        """True or False, whether the :class:`Sequences` object handles at 
        conditions (at least one :class:`StateSequence` or :class:`LogSequence` 
        object)  or not."""
        for tuple_ in self.conditions:
            return True
        return False
    
    @property
    def _conditiondefaultfilename(self):
        filename = objecttools.elementname(self)
        if filename == '?':
            raise RuntimeError(
                'To load or save the conditions of a model from or to a file, '
                'its filename must be known.  This can be done, by passing '
                'filename to function `loadconditions` or `saveconditions` '
                'directly.  But in complete HydPy applications, it is usally '
                'assumed to be consistent with the name of the element '
                'handling the model.  Actually, neither a filename is given '
                'nor does the model know its master element.') 
        else:
            return filename + '.py'
            
    def loadconditions(self, filename=None, dirname=None):
        """Load initial conditions from a file and assign them to the 
        respective sequences.
        """
        if self.hasconditions:
            if filename is None:
                filename = self._conditiondefaultfilename
            namespace = locals()
            for (name, seq) in self.conditions:
                namespace[name] = seq
            namespace['model'] = self
            code = pub.conditionmanager.loadfile(filename, dirname)
            try:
                exec(code)
            except BaseException:
                exc, message, traceback_ = sys.exc_info()
                message = ('While trying to gather initial conditions of '
                           'element %s, the following error occured:  %s' 
                           % (objecttools.elementname(self), message))
                raise exc, message, traceback_
    
    def saveconditions(self, filename=None, dirname=None):
        if self.hasconditions:
            if filename is None:
                filename = self._conditiondefaultfilename
            if not filename.endswith('.py'):
                filename += '.py'
            if dirname is None:
                dirname = pub.conditionmanager.savepath
            filepath = os.path.join(dirname, filename)
            with file(filepath, 'w') as file_:
                file_.write('from hydpy.models.%s import *\n\n'
                            % self.model.__module__.split('.')[2])
                try:
                    line = ('controlcheck(projectdir="%s", controldir="%s")'
                            % (pub.controlmanager.projectdirectory, 
                               pub.controlmanager.controldirectory))
                    file_.write(line + '\n\n')
                except BaseException:
                    pass
                for (name, seq) in self.conditions:
                    file_.write(repr(seq) + '\n')
                
    def trimconditions(self):
        for (name, seq) in self.conditions:
            seq.trim()
            
    def __len__(self):
        return len(dict(self))

class SubSequences(object):
    """Base class for handling subgroups of sequences.
    
    Attributes:
      * seqs: The parent :class:`Sequences` object.
      * fastaccess: The  :class:`FastAccess` object allowing fast access to 
        the sequence values. In :ref:`Cython` mode, model specific cdef 
        classes are applied.
    
    Additional attributes are the actual :class:`Sequence` instances, 
    representing the individual time series.  These need to be defined in 
    :class:`SubSequences` subclass.  Therefore, one needs to collect the 
    appropriate :class:`Sequence` subclasses in the (hidden) class attribute 
    :attr:`~SubSequences._SEQCLASSES`, as shown in the following example:
    
    >>> from hydpy.framework.sequencetools import *
    >>> class Temperature(Sequence):
    ...    NDIM, NUMERIC = 0, False
    >>> class Precipitation(Sequence):
    ...    NDIM, NUMERIC = 0, True
    >>> class InputSequences(SubSequences):
    ...     _SEQCLASSES = (Temperature, Precipitation)
    >>> inputs = InputSequences(None) # Assign `None` for brevity.
    >>> inputs
    InputSequences object defined in module sequencetools.
    The implemented sequences with their actual values:
    temperature(0.0)
    precipitation(0.0)
        
    The order within the tuple determines the order of iteration, hence:
    
    >>> for (name, sequence) in inputs:
    ...     print(sequence)
    temperature(0.0)
    precipitation(0.0)
   
    """
    
    _SEQCLASSES = ()
  
    def __init__(self, seqs, cls_fastaccess=None, cymodel=None):
        self.seqs = seqs
        self._initfastaccess(cls_fastaccess, cymodel)
        self._initsequences()
    
    def _initfastaccess(self, cls_fastaccess, cymodel):
        if cls_fastaccess is None:
            self.fastaccess = FastAccess()
        else:
            self.fastaccess = cls_fastaccess()   
            setattr(cymodel, self.name, self.fastaccess)
    
    def _initsequences(self):
        for cls_seq in self._SEQCLASSES:
            setattr(self, objecttools.instancename(cls_seq), cls_seq()) 
            
    @classmethod
    def getname(cls):
        return objecttools.instancename(cls)[:-8]
    
    @property
    def name(self):
        return self.getname()
             
    def __setattr__(self, name, value):
        """Attributes and methods should usually not be replaced.  Existing 
        :class:`Sequence` attributes are protected in a way, that only their
        values are changed through assignements.  For new :class:`Sequence` 
        attributes, additional `fastaccess` references are defined.  If you 
        actually want to replace a sequence, you have to delete it first.
        """
        try:
            attr = getattr(self, name)
        except AttributeError:
            object.__setattr__(self, name, value)
            if isinstance(value, Sequence):
                value.connect2subseqs(self)
        else:
            try:
                attr.values = value
            except AttributeError:
                raise RuntimeError('`%s` instances do not allow the direct'
                                   'replacement of their members.  After '
                                   'initialization you should usually only '
                                   'change parameter values through '
                                   'assignements.  If you really need to '
                                   'replace a object member, delete it '
                                   'beforehand.' % objecttools.classname(self)) 
           
    def __iter__(self):
        for seqclass in self._SEQCLASSES:
            name = objecttools.instancename(seqclass)
            yield name, getattr(self, name)
    
    def __getitem__(self, key):
        return self.__dict__[key]
        
    def __repr__(self):
        lines = []
        if pub.options.reprcomments:
            lines.append('%s object defined in module %s.'
                         % (objecttools.classname(self), 
                            objecttools.modulename(self)))
            lines.append('The implemented sequences with their actual values:') 
        for (name, sequence) in self:
            try:
                lines.append('%s' % repr(sequence))
            except BaseException:
                lines.append('%s(?)' % name)
        return '\n'.join(lines)
            
    def __dir__(self):
        return objecttools.dir_(self)

class IOSubSequences(SubSequences):

    def openfiles(self, idx=0):
        self.fastaccess.openfiles(idx)

    def closefiles(self):
        self.fastaccess.closefiles()
    
    def activate_ram(self):
        for (name, seq) in self:
            seq.activate_ram()

    def deactivate_ram(self):
        for (name, seq) in self:
            seq.deactivate_ram()

    def activate_disk(self):
        for (name, seq) in self:
            seq.activate_disk()

    def deactivate_disk(self):
        for (name, seq) in self:
            seq.deactivate_disk()

    def ram2disk(self):
        for (name, seq) in self:
            seq.ram2disk()            

    def disk2ram(self):
        for (name, seq) in self:
            seq.disk2ram() 
        
        
class InputSequences(IOSubSequences):
    """Base class for handling input sequences."""

    def loaddata(self, idx):
        self.fastaccess.loaddata(idx)

        
class FluxSequences(IOSubSequences):
    """Base class for handling flux sequences."""

    @classmethod
    def getname(cls):
        return 'fluxes'

    def savedata(self, idx):
        self.fastaccess.savedata(idx)
                    
class StateSequences(IOSubSequences):
    """Base class for handling state sequences."""
    
    def _initfastaccess(self, cls_fastaccess, cymodel):
        SubSequences._initfastaccess(self, cls_fastaccess, cymodel)
        self.fastaccess_new = self.fastaccess
        if cls_fastaccess is None:
            self.fastaccess_old = FastAccess()
        else:
            setattr(cymodel, 'new_states', self.fastaccess)
            self.fastaccess_old = cls_fastaccess()  
            setattr(cymodel, 'old_states', self.fastaccess_old)
        
    def new2old(self):
        """Assign the new/final state values of the actual time step to the
        new/initial state values of the next time step.
        """
        for (name, seq) in self:
            seq.new2old()                

    def savedata(self, idx):
        self.fastaccess.savedata(idx)
    
    def reset(self):
        for (name, seq) in self:
            seq.reset()
        
class LogSequences(SubSequences):
    """Base class for handling log sequences."""

    def reset(self):
        for (name, seq) in self:
            seq.reset()

class AideSequences(SubSequences):
    """Base class for handling aide sequences."""

class LinkSequences(SubSequences):
    """Base class for handling link sequences."""
        
        
class Sequence(objecttools.ValueMath):
    """Only for inheritance."""
    
    NDIM, NUMERIC = 0, False

    def __init__(self):
        self.subseqs = None
        self.fastaccess = None
            
    def connect2subseqs(self, subseqs):
        self.subseqs = subseqs
        self.fastaccess = subseqs.fastaccess
        setattr(self.fastaccess, '_%s_ndim' % self.name, self.NDIM)
        setattr(self.fastaccess, '_%s_length' % self.name, 0) 
        for idx in range(self.NDIM):
            setattr(self.fastaccess, '_%s_length_%d' % (self.name, idx), 0)        
        self.diskflag = False
        self.ramflag = False
        try:
            setattr(self.fastaccess, '_%s_file' % self.name, '') 
        except AttributeError:
            pass
        self._initvalues()

    def __call__(self, *args):
        """The prefered way to pass values to :class:`Sequence` instances
        within initial condition files.
        """
        self.values = args
        self.trim()
        
    def _initvalues(self):
        if self.NDIM:
            setattr(self.fastaccess, self.name, None)
        else:
            setattr(self.fastaccess, self.name, 0.)
            
    def _getname(self):
        """Name of the sequence, which is the name if the instantiating 
        subclass of :class:`Sequence` in lower case letters.
        """
        return objecttools.classname(self).lower()
    name = property(_getname)      

    def _getvalue(self):
        """The actual time series value(s) handled by the respective 
        :class:`Sequence` instance.  For consistency, `value` and `values` 
        can always be used interchangeably.
        """
        value = getattr(self.fastaccess, self.name, None)
        if value is None:
            raise RuntimeError('No value/values of sequence %s of element '
                               '%s has/have been defined so far.' 
                               % (self.name, objecttools.elementname(self)))
        else:
            if self.NDIM:
                value = numpy.asarray(value)
            return value
    def _setvalue(self, value):
        if self.NDIM == 0:
            try:
                temp = value[0]
                if len(value) > 1:
                    raise ValueError('%d values are assigned to the scalar '
                                     'sequence %s of element %s, which is '
                                     'ambiguous.'
                                     % (len(value), 
                                        objecttools.elementname(self),
                                        self.name))
                value = temp
            except (TypeError, IndexError):
                pass 
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise TypeError('When trying to set the value of sequence '
                                '%s of element %s, it was not possible to '
                                'convert value `%s` to float .' 
                                % (self.name, objecttools.elementname(self),
                                   value))
        else:
            try:
                value = value.value
            except AttributeError:
                pass
            try:
                value = numpy.full(self.shape, value, dtype=float)
            except ValueError:          
                raise ValueError('For sequence %s of element %s setting new '
                                 'values failed.  The values `%s` cannot be '
                                 'converted to a numpy ndarray with shape %s '
                                 'containing entries of type float.' 
                                 % (self.name, objecttools.elementname(self), 
                                    value, self.shape))
        setattr(self.fastaccess, self.name, value)                      
    value = property(_getvalue, _setvalue)
    values = value
    
    def _getshape(self):
        """A tuple containing the lengths in all dimensions of the sequence 
        values at a specific time point.  Note that setting a new shape 
        results in a loss of the actual values of the respective sequence.  
        For 0-dimensional sequences :attr:`shape` is always an empty tuple.
        """
        if self.NDIM:
            try:
                return self.values.shape
            except AttributeError:
                raise RuntimeError('Shape information for sequence %s of '
                                   'element %s can only be retrieved after '
                                   'it has been defined.' 
                                   % (self.name, 
                                      objecttools.elementname(self)))   
        else:
            return ()
    def _setshape(self, shape):
        if self.NDIM:
            try:
                array = numpy.full(shape, 0.)
            except Exception:
                Exception_, message, traceback_ = sys.exc_info()
                message = ('While trying create a new :class:`~numpy.ndarray` '
                           'for sequence %s of element %s,the following error '
                           'occured: %s' % (self.name, 
                                            objecttools.elementname(self), 
                                            message))
                raise Exception_, message, traceback_
            if array.ndim == self.NDIM:
                setattr(self.fastaccess, self.name, array)
            else:
                raise ValueError('Sequence %s of element %s is %d-dimensional '
                                 'but the given shape indicates %d dimensions.'
                                 % (self.name, objecttools.elementname(self),
                                    self.NDIM, array.ndim))
        else:
            if shape:
                raise ValueError('The shape information of 0-dimensional '
                                 'sequences as %s of element %s can only be '
                                 '`()`, but `%s` is given.' 
                                 % (self.name, objecttools.elementname(self), 
                                    shape))
            else:
                self.value = 0.
    shape = property(_getshape, _setshape)

    def __getitem__(self, key):
        try:
            return self.values[key]
        except Exception:
            self._raiseitemexception()
               
    def __setitem__(self, key, values):
        try:
            self.values[key] = values
        except Exception:
            self._raiseitemexception() 
                             
    def _raiseitemexception(self):
        if self.values is None:
            raise RuntimeError('Sequence `%s` has no values so far.'
                               % self.name)
        else:
            Exception_, message, traceback_ = sys.exc_info()
            message = ('While trying to item access the values of sequence '
                       '`%s`, the following error occured:  %s' 
                       % (self.name, message))
            raise Exception_, message, traceback_   
            
    def __repr__(self):
        if self.NDIM == 0:
            return '%s(%s)' % (self.name, self.value)
        elif self.NDIM == 1:  
            lines = []
            cols = ', '.join(str(value) for value in self.values)
            wrappedlines = textwrap.wrap(cols, 80-len(self.name)-2)
            for (idx, line) in enumerate(wrappedlines):
                if not idx:
                    lines.append('%s(%s' % (self.name, line))
                else:
                    lines.append((len(self.name)+1)*' ' + line)
            lines[-1] += ')'
            return '\n'.join(lines)
        elif self.NDIM == 2:
            lines = []
            skip = (1+len(self.name)) * ' '
            for (idx, row) in enumerate(self.values):
                cols = ', '.join(str(value) for value in row)
                if not idx:
                    lines.append('%s(%s,' % (self.name, cols))
                else:
                    lines.append('%s%s,' % (skip, cols))
            lines[-1] = lines[-1][:-1] + ')'
            return '\n'.join(lines)
        else:
            raise NotImplementedError('`repr` does not yet support '
                                      'sequences, which handle %d-'
                                      'dimensional matrices.' % self.NDIM)

    def __dir__(self):
        return objecttools.dir_(self)
    
class IOSequence(Sequence):
    """Only for inheritance."""

    def __init__(self):
        Sequence.__init__(self)
        self._rawfilename = None
        self._filetype_ext = None
        self._filename_ext = None
        self._dirpath_ext = None
        self._dirpath_int = None
        self._filepath_ext = None
        self._filepath_int = None  

    def _getfiletype_ext(self):
        """Ending of the external data file."""
        if self._filetype_ext:
            return self._filetype_ext
        else:
            try:
                if isinstance(self, InputSequence):
                    return pub.sequencemanager.inputfiletype
                elif isinstance(self, NodeSequence):
                    return pub.sequencemanager.nodefiletype
                else:
                    return pub.sequencemanager.outputfiletype
                    
            except AttributeError:
                raise RuntimeError('For sequence %s of element %s the type '
                                   'of the external data file cannot be '
                                   'determined.  Either set it manually or '
                                   'embed the sequence object into the HydPy '
                                   'framework in the common manner to allow '
                                   'for an automatic determination.' 
                                   % (self.name, 
                                      objecttools.elementname(self)))
    def _setfiletype_ext(self, name):
        self._filetype_ext = name
    def _delfiletype_ext(self, name):
        self._filetype_ext = None
    filetype_ext = property(_getfiletype_ext, _setfiletype_ext, 
                            _delfiletype_ext)
                            
    def _getfilename_ext(self):
        """Complete filename of the external data file."""
        if self._filename_ext:
            return self._filename_ext
        else:
            return '.'.join((self.rawfilename, self.filetype_ext))
    def _setfilename_ext(self, name):
        self._filename_ext = name
    def _delfilename_ext(self):
        self._filename_ext = None
    filename_ext = property(_getfilename_ext, _setfilename_ext, 
                            _delfilename_ext)

    def _getfilename_int(self):
        """Complete filename of the internal data file."""
        return self.rawfilename + '.bin'
    filename_int = property(_getfilename_int)      

    def _getdirpath_ext(self):
        """Absolute path of the directory of the external data file."""
        if self._dirpath_ext:
            return self._dirpath_ext
        else:
            try:
                if isinstance(self, InputSequence):
                    return pub.sequencemanager.inputpath
                elif isinstance(self, NodeSequence):
                    return pub.sequencemanager.nodepath
                else:
                    return pub.sequencemanager.outputpath
            except AttributeError:
                raise RuntimeError('For sequence `%s` the directory of '
                                   'the external data file cannot be '
                                   'determined.  Either set it manually or '
                                   'embed the sequence object into the HydPy '
                                   'framework in the common manner to allow '
                                   'for an automatic determination.' 
                                   % self.name)
    def _setdirpath_ext(self, name):
        self._dirpath_ext = name
    def _deldirpath_ext(self, name):
        self._dirpath_ext = None
    dirpath_ext = property(_getdirpath_ext, _setdirpath_ext, _deldirpath_ext)
                           
    def _getdirpath_int(self):
        """Absolute path of the directory of the internal data file."""
        if self._dirpath_int:
            return self._dirpath_int
        else:
            try:
                return pub.sequencemanager.temppath
            except AttributeError:
                raise RuntimeError('For sequence `%s` the directory of '
                                   'the internal data file cannot be '
                                   'determined.  Either set it manually or '
                                   'embed the sequence object into the HydPy '
                                   'framework in the common manner to allow '
                                   'for an automatic determination.' 
                                   % self.name)
    def _setdirpath_int(self, name):
        self._dirpath_int = name
    def _deldirpath_int(self, name):
        self._dirpath_int = None
    dirpath_int = property(_getdirpath_int, _setdirpath_int, _deldirpath_int)
        
    def _getfilepath_ext(self):
        """Absolute path to the external data file."""
        if self._filepath_ext:
            return self._filepath_ext
        else:
            return os.path.join(self.dirpath_ext, self.filename_ext)
    def _setfilepath_ext(self, name):
        self._filepath_ext = name
    def _delfilepath_ext(self):
        self._filepath_ext = None
    filepath_ext = property(_getfilepath_ext, _setfilepath_ext, 
                            _delfilepath_ext)  

    def _getfilepath_int(self):
        """Absolute path to the internal data file."""
        if self._filepath_int:
            return self._filepath_int
        else:
            return os.path.join(self.dirpath_int, self.filename_int)
    def _setfilepath_int(self, name):
        self._filepath_int = name
    def _delfilepath_int(self):
        self._filepath_int = None
    filepath_int = property(_getfilepath_int, _setfilepath_int, 
                            _delfilepath_int) 
                            
    def update_fastaccess(self):
        """"""
        if self.diskflag:
            path = self.filepath_int
        else:
            path = None
        setattr(self.fastaccess, '_%s_path' % self.name, path) 
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
            setattr(self.fastaccess, '_%s_length_%d' % (self.name, idx), 
                    self.shape[idx]) 
        setattr(self.fastaccess, '_%s_length' % self.name, length) 
            
    def _getdiskflag(self):
        diskflag = getattr(self.fastaccess, '_%s_diskflag' % self.name, None)
        if diskflag is not None:
            return diskflag
        else:
            raise RuntimeError('The `diskflag` of sequence `%s` has '
                               'not been set yet.' % self.name)
    def _setdiskflag(self, value):
        setattr(self.fastaccess, '_%s_diskflag' % self.name,  bool(value))
    diskflag = property(_getdiskflag, _setdiskflag)
    
    def _getramflag(self):
        ramflag = getattr(self.fastaccess, '_%s_ramflag' % self.name, None)
        if ramflag is not None:
            return ramflag
        else:
            raise RuntimeError('The `ramflag` of sequence `%s` has '
                               'not been set yet.' % self.name)
    def _setramflag(self, value):
        setattr(self.fastaccess, '_%s_ramflag' % self.name,  bool(value))
    ramflag = property(_getramflag, _setramflag)   
    
    def _getmemoryflag(self):
        return self.ramflag or self.diskflag
    memoryflag = property(_getmemoryflag)
    
    def _getarray(self):
        array = getattr(self.fastaccess, '_%s_array' % self.name, None)
        if array is not None:
            return numpy.asarray(array)
        else:
            raise RuntimeError('The `ram array` of sequence `%s` has '
                               'not been set yet.' % self.name)             
    def _setarray(self, values):
        values = numpy.array(values, dtype=float)
        setattr(self.fastaccess, '_%s_array' % self.name,  values)   
    
    def _getseriesshape(self):
        """Shape of the whole time series (time beeing the first dimension)."""
        seriesshape = [len(pub.timegrids.init)]
        seriesshape.extend(self.shape)
        return tuple(seriesshape)   
    seriesshape = property(_getseriesshape)
    
#    def _gettimegrid_init(self):
#        if self._timegrid_init is not None:
#            return self._timegrid_init 
#        else:
#            try:
#                return pub.timegrids.init
#            except AttributeError:
#                raise RuntimeError('Initializing internal data of sequence '
#                                   '`%s` requires information about the '
#                                   'initialization period.  Define an '
#                                   'appropriate `Timegrid` instance and '
#                                   'either pass it to the sequence object '
#                                   'or store it in the `pub` module as '
#                                   'described in the documentation.' 
#                                   % self.name)
#    def _settimegrid_init(self, timegrid):
#        self._timegrid_init = timegrid 
#    timegrid_init = property(_gettimegrid_init, _settimegrid_init)
    
    def _getseries(self):
        if self.diskflag:
            return self._load_int()
        elif self.ramflag:
            return self._getarray()
        else:
            raise RuntimeError('Sequence `%s` is not requested to make any '
                               'internal data available to the user.' 
                               % self.name)                   
    def _setseries(self, values):
        series = self.series
        series[:] = values
        if self.diskflag:
            self._save_int(series)
        elif self.ramflag:
            self._setarray(series)
        else:
            raise RuntimeError('Sequence `%s` is not requested to make any '
                               'internal data available to the user.' 
                               % self.name)  
    def _delseries(self):
        if self.diskflag:
            os.remove(self.filepath_int)
        elif self.ramflag:
            setattr(self.fastaccess, '_%s_array' %self.name, None)
    series = property(_getseries, _setseries, _delseries)
        
    def load_ext(self):
        """Load the external data series in accordance with 
        :attr:`~IOSequence.timegrid_init` and store it as internal data.
        """
        if self.filetype_ext == 'npy':
            timegrid_data, values = self._load_npy()
        else:
            timegrid_data, values = self._load_asc()

        if pub.timegrids.init not in timegrid_data:
            raise RuntimeError('For sequence `%s` the initialization time '
                               'grid (%s) does not define a subset of the '
                               'time grid of the external data file %s (%s).'
                               % (self.name, pub.timegrids.init, 
                                  self.filepath_ext, timegrid_data))
        idx1 = timegrid_data[pub.timegrids.init.firstdate]
        idx2 = timegrid_data[pub.timegrids.init.lastdate]
        if self.diskflag:
            self._save_int(values[idx1:idx2])
        elif self.ramflag:
            self._setarray(values[idx1:idx2])
        else:
            raise RuntimeError('Sequence `%s` is not requested to make any '
                               'internal data available the the user.' 
                               % self.name) 
        
    def save_ext(self):
        """Write the internal data into an external data file."""
        if self.filetype_ext == 'npy':
            values = pub.timegrids.init.toarray()
            for idx in xrange(self.NDIM):
                values = numpy.expand_dims(values, idx+1)
            values = values + numpy.zeros(self.shape)
            values = numpy.concatenate((values, self.series))
            numpy.save(self.filepath_ext, values)
        else:
            with file(self.filepath_ext, 'w') as file_:
                file_.write(repr(pub.timegrids.init) + '\n')
                numpy.savetxt(file_, self.series, delimiter='\t')

    def _load_npy(self):
        """Return the data timegrid and the complete external data from a 
        binary numpy file.
        """
        try:
            data = numpy.load(self.filepath_ext)
        except BaseException:
            Exception_, message, traceback_ = sys.exc_info()
            message = ('While trying to load the external data of sequence '
                       '`%s` from file `%s`, the following error occured:  %s' 
                       % (self.name, self.filepath_ext, message))
            raise Exception_, message, traceback_
        try:
            timegrid_data = timetools.Timegrid.fromarray(data)
        except BaseException:
            Exception_, message, traceback_ = sys.exc_info()
            message = ('While trying to retrieve the data timegrid of the '
                       'external data file `%s` of sequence `%s`, the '
                       'following error occured:  %s' 
                       % (self.filepath_ext, self.name, message))
            raise Exception_, message, traceback_
        return timegrid_data, data[13:]
    
    def _load_asc(self):
        with file(self.filepath_ext) as file_:
            header = '\n'.join([file_.readline() for idx in range(3)])
        timegrid_data = eval(header, {}, {'Timegrid': timetools.Timegrid})
        values = numpy.loadtxt(self.filepath_ext, skiprows=3, 
                               ndmin=self.NDIM+1)
        return timegrid_data, values
                
    def _load_int(self):
        """Load internal data from file and return it."""
        values = numpy.fromfile(self.filepath_int)
        if self.NDIM > 0:
            values = values.reshape(self.seriesshape)
        return values

    def zero_int(self):
        """Initialize the internal data series with zero values."""
        values = numpy.zeros(self.seriesshape)
        if self.diskflag:
            self._save_int(values)
        elif self.ramflag:
            self._setarray(values)
        else:
            raise RuntimeError('Sequence `%s` is not requested to make any '
                               'internal data available to the user.' 
                               % self.name) 
                               
    def _save_int(self, values):
        values.tofile(self.filepath_int) 

    def activate_disk(self):
        """Demand reading/writing internal data from/to hard disk."""
        self.deactivate_ram()
        self.diskflag = True
        if (isinstance(self, InputSequence) or
            (isinstance(self, NodeSequence) and self.use_ext)):
            self.load_ext()
        else:
            self.zero_int()
        self.update_fastaccess()
    
    def deactivate_disk(self):
        """Prevent from reading/writing internal data from/to hard disk."""
        if self.diskflag:
            del self.series
            self.diskflag = False

    def activate_ram(self):
        """Demand reading/writing internal data from/to hard disk."""
        self.deactivate_disk()
        self.ramflag = True
        if (isinstance(self, InputSequence) or
            (isinstance(self, NodeSequence) and self.use_ext)):
            self.load_ext()
        else:
            self.zero_int()
        self.update_fastaccess()
    
    def deactivate_ram(self):
        """Prevent from reading/writing internal data from/to hard disk."""
        if self.ramflag:
            del self.series
            self.ramflag = False

    def disk2ram(self):
        """Move internal data from disk to RAM.""" 
        values = self.series
        self.deactivate_disk()
        self.ramflag = True
        self._setarray(values)
        self.update_fastaccess()

    def ram2disk(self):
        """Move internal data from RAM to disk.""" 
        values = self.series
        self.deactivate_ram()
        self.diskflag = True
        self._save_int(values)
        self.update_fastaccess()

    def _setshape(self, shape):
        Sequence._setshape(self, shape)
        self.update_fastaccess()
    shape = property(Sequence._getshape, _setshape)
            
        
class ModelIOSequence(IOSequence):  
            
    def _getrawfilename(self):
        """Filename without ending for external and internal date files."""
        if self._rawfilename:
            return self._rawfilename
        else:
            try:
                return '%s_%s_%s' % (
                       self.subseqs.seqs.model.element.name,
                       objecttools.classname(self.subseqs)[:-9].lower(), 
                       self.name)
            except AttributeError:
                raise RuntimeError('For sequence `%s` the raw filename cannot '
                                   'determined.  Either set it manually or '
                                   'embed the sequence object into the HydPy '
                                   'framework in the common manner to allow '
                                   'for an automatic determination.' 
                                   % self.name)
    def _setrawfilename(self, name):
        self._rawfilename = str(name)
    def _delrawfilename(self):
        self._rawfilename = None
    rawfilename = property(_getrawfilename, _setrawfilename, _delrawfilename)

class InputSequence(ModelIOSequence):
    """ """
    
class FluxSequence(ModelIOSequence):
    """ """

class ConditionSequence(objecttools.Trimmer):
        
    def warntrim(self):
        warnings.warn('For sequence %s of element %s at least one value '
                      'needed to be trimmed.  One possible reason could be '
                      'that the related control parameter and initial '
                      'condition files are inconsistent.' 
                      % (self.name, objecttools.elementname(self)))

    def reset(self):
        if self._oldargs:
            self(*self._oldargs)

                
class StateSequence(ModelIOSequence, ConditionSequence):
    """Handler for state time series."""
    
    def __init__(self):
        ModelIOSequence.__init__(self)
        self.fastaccess_old = None
        self.fastaccess_new = None
        self._oldargs = None
            
    def connect2subseqs(self, subseqs):
        ModelIOSequence.connect2subseqs(self, subseqs)
        self.fastaccess_old = subseqs.fastaccess_old
        self.fastaccess_new = subseqs.fastaccess_new
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, None)
        else:
            setattr(self.fastaccess_old, self.name, 0.)

    def _setshape(self, shape):
        ModelIOSequence._setshape(self, shape)
        if self.NDIM:
            setattr(self.fastaccess_old, self.name, self.new.copy())
    shape = property(ModelIOSequence._getshape, _setshape) 
    
    new = Sequence.values
    """Complete access to the state value(s), which will be used in the next
    calculation steps.  Note that :attr:`~StateSequence.new` is a synonym of 
    :attr:`~StateSequence.value`.  Use this property to modify the initial
    condition(s) of a single :class:`StateSequence` object.
    """
    
    def _getold(self):
        """Assess to the state value(s) at beginning of the time step, which
        has been processed most recently.  When using :ref:`HydPy` in the 
        normal manner.  But it can be helpful for demonstration and debugging
        purposes.
        """
        value = getattr(self.fastaccess_old, self.name, None)
        if value is None:
            raise RuntimeError('No value/values of sequence `%s` has/have '
                               'not been defined so far.' % self.name)
        else:
            if self.NDIM:
                value = numpy.asarray(value)
            return value
    def _setold(self, value):
        if self.NDIM == 0:
            try:
                temp = value[0]
                if len(value) > 1:
                    raise ValueError('%d values are assigned to the scalar '
                                     'sequence `%s`, which is ambiguous.'
                                     % (len(value)), self.name)  
                value = temp
            except (TypeError, IndexError):
                pass 
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise TypeError('When trying to set the value of sequence '
                                '`%s`, it was not possible to convert `%s` '
                                'to float .' % (self.name, value))
        else:
            try:
                value = value.value
            except AttributeError:
                pass
            try:
                value = numpy.full(self.shape, value, dtype=float)
            except ValueError:
                raise ValueError('The values `%s` cannot be converted to a '
                                 'numpy ndarray with shape %s containing '
                                 'entries of type float.' 
                                 % (value, self.shape))
        setattr(self.fastaccess_old, self.name, value)  
    old = property(_getold, _setold)

    def new2old(self):
        if self.NDIM:
            self.old[:] = self.new[:]
        else:
            self.old = self.new

    def __call__(self, *args):
        """The prefered way to pass values to :class:`Sequence` instances
        within initial condition files.
        """
        self._oldargs = copy.deepcopy(args)
        ModelIOSequence.__call__(self, *args)
        self.new2old()
        
                             
class LogSequence(Sequence, ConditionSequence):
    """ """
    
    def __init__(self):
        Sequence.__init__(self)
        self._oldargs = None
        
    def __call__(self, *args):
        self._oldargs = copy.deepcopy(args)
        Sequence.__call__(self, *args)
            
class AideSequence(Sequence):
    """ """

class LinkSequence(Sequence):
    """2"""
    
    def setpointer(self, double, idx=0):
        pdouble = pointer.PDouble(double)
        if self.NDIM == 0:
            try:
                self.fastaccess.setpointer0d(self.name, pdouble)
            except AttributeError:
                setattr(self.fastaccess, self.name, pdouble)
        elif self.NDIM == 1:
            try:
                self.fastaccess.setpointer1d(self.name, pdouble, idx)
            except AttributeError:
                ppdouble = getattr(self.fastaccess, self.name)
                ppdouble.setpointer(double, idx)
            
    def _initvalues(self):
        if self.NDIM == 0:
            try:
                setattr(self.fastaccess, self.name, None)
            except AttributeError:
                pass
        else:
            try:
                setattr(self.fastaccess, self.name, pointer.PPDouble())
            except AttributeError:
                pass

#    def _getvalue(self):
#        """Actual value(s) handled by the sequence.  For consistency, 
#        `value` and `values` can always be used interchangeably."""
#        try:
#            return getattr(self.fastaccess, self.name)
#        except AttributeError:
#            if self.NDIM == 0:
#                return self.fastaccess.getpointer0d(self.name)
#            elif self.NDIM == 1:
#                return self.fastaccess.getpointer1d(self.name)  
    def _getvalue(self):
        """ToDo"""
        raise NotImplementedError('To retrieve a pointer is very likely to '
                                  'result in bugs and is thus not supported '
                                  'at the moment.')   
    def _setvalue(self, value):
        """Could be implemented, but is not important at the moment..."""
        raise NotImplementedError('To change a pointer is very likely to '
                                  'result in bugs and is thus not supported '
                                  'at the moment.')                
    value = property(_getvalue, _setvalue)
    values = value
    
    def _getshape(self):
        if self.NDIM == 0:
            return ()
        elif self.NDIM == 1:
            try:
                return getattr(self.fastaccess, self.name).shape
            except AttributeError:
                return (getattr(self.fastaccess, '_%s_length_0' % self.name), )           
    def _setshape(self, shape):
        if self.NDIM == 1:
            try:
                getattr(self.fastaccess, self.name).shape = shape
            except AttributeError:
                self.fastaccess.dealloc()
                self.fastaccess.alloc(self.name, shape) 
    shape = property(_getshape, _setshape)
    
        
class NodeSequence(IOSequence):
        
    def _getrawfilename(self):
        """Filename without ending for external and internal date files."""
        if self._rawfilename:
            return self._rawfilename
        else:
            try:
                return '%s_%s_%s' % (
                       self.subseqs.node.name,
                       self.name,
                       self.subseqs.node.variable.lower())
            except AttributeError:
                raise RuntimeError('For sequence `%s` the raw filename cannot '
                                   'determined.  Either set it manually or '
                                   'embed the sequence object into the HydPy '
                                   'framework in the common manner to allow '
                                   'for an automatic determination.' 
                                   % self.name)
    def _setrawfilename(self, name):
        self._rawfilename = str(name)
    def _delrawfilename(self):
        self._rawfilename = None
    rawfilename = property(_getrawfilename, _setrawfilename, _delrawfilename)

    def _initvalues(self):
        setattr(self.fastaccess, self.name, pointer.Double(0.))

    def _getvalues(self):
        """Actual value(s) handled by the sequence.  For consistency, 
        `value` and `values` can always be used interchangeably."""
        try:
            return getattr(self.fastaccess, self.name)
        except AttributeError:
            if self.NDIM == 0:
                return self.fastaccess.getpointer0d(self.name)
            elif self.NDIM == 1:
                return self.fastaccess.getpointer1d(self.name)                
    def _setvalues(self, values):
        getattr(self.fastaccess, self.name)[0] = values
    values = property(_getvalues, _setvalues)
    value = values


class Sim(NodeSequence):
    NDIM, NUMERIC = 0, False
    
    def __init__(self):
        NodeSequence.__init__(self)
        self.use_ext = False
        
        
class Obs(NodeSequence):
    NDIM, NUMERIC = 0, False   

    def __init__(self):
        NodeSequence.__init__(self)
        self.use_ext = True
    
    def activate_disk(self):
        try:
            NodeSequence.activate_disk(self)
        except IOError:
            exc, message, traceback_ = sys.exc_info()
            self.diskflag = False
            warnings.warn('The option `diskflag` of the observation '
                          'sequence had to be set to `False` due to the '
                          'following problem: %s.' % message)

    def activate_ram(self):
        try:
            NodeSequence.activate_ram(self)
        except IOError:
            exc, message, traceback_ = sys.exc_info()
            self.ramflag = False
            warnings.warn('The option `ramflag` of the simulation '
                          'sequence had to be set to `False` due to the '
                          'following problem: %s.' % message)      
    
    @property
    def series_complete(self):
        return self.memoryflag and not numpy.any(numpy.isnan(self.series))
        
class NodeSequences(IOSubSequences):
    """Base class for handling node sequences."""
    
    _SEQCLASSES = (Sim, Obs)
    
    def __init__(self, seqs, cls_fastaccess=None):
        IOSubSequences.__init__(self, seqs, cls_fastaccess)
        self.node = seqs

    def loaddata(self, idx):
        self.fastaccess.loaddata(idx)

    def savedata(self, idx):
        self.fastaccess.savedata(idx)
            
         

class FastAccess(object):
    """Provides fast access to the values of the sequences of a sequence 
    subgroup and supports the handling of internal data series during 
    simulations.
    
    The following details are of relevance for :ref:`HydPy` developers only.
    
    :class:`FastAccess` is applied in Python mode only.  In Cython mode, 
    specialized and more efficient cdef classes replace it.  For 
    compatibility with these cdef classes, :class:`FastAccess` objects
    work with dynamically set instance members.  Suppose there is a 
    sequence named `seq1` which is 2-dimensional, then its associated
    attributes are:
    
      * seq1 (:class:`~numpy.ndarray`): The actual sequence values.
      * _seq1_ndim (:class:`int`): Number of dimensions.
      * _seq1_length_0 (:class:`int`): Length in the first dimension.
      * _seq1_length_1 (:class:`int`): Length in the second dimension.
      * _seq1_ramflag (:class:`bool`): Handle internal data in RAM?
      * _seq1_diskflag (:class:`bool`): Handle internal data on disk?
      * _seq1_path (:class:`str`): Path of the internal data file.
      * _seq1_file (:class:`file`): Object handling the internal data file.
     
    Note that all these dynamical attributes and the following methods are 
    initialised, changed or applied by the respective :class:`SubSequences`
    and :class:`Sequence` objects.  Handling them directly is error prone 
    and thus not recommended.
    """
    
    def openfiles(self, idx):
        """Open all files with an activated disk flag."""
        for name in self:
            if getattr(self, '_%s_diskflag' % name):
                path = getattr(self, '_%s_path' % name)
                file_ = open(path, 'rb+')
                ndim = getattr(self, '_%s_ndim' % name)
                position = 8*idx
                for idim in xrange(ndim):
                    length = getattr(self, '_%s_length_%d' % (name, idim))
                    position *= length
                file_.seek(position)
                setattr(self, '_%s_file' % name, file_)            

    def closefiles(self):
        """Close all files with an activated disk flag."""
        for name in self:
            if getattr(self, '_%s_diskflag' % name):
                file_ = getattr(self, '_%s_file' % name)
                file_.close()

    def loaddata(self, idx):
        """Load the internal data of all sequences.  Load from file if the
        corresponding disk flag is activated, otherwise load from RAM."""
        for name in self:
            ndim = getattr(self, '_%s_ndim' % name)
            diskflag = getattr(self, '_%s_diskflag' % name)
            ramflag = getattr(self, '_%s_ramflag' % name)
            if diskflag:
                file_ = getattr(self, '_%s_file' % name)
                length_tot = 1
                shape = []
                for idx in xrange(ndim):
                    length = getattr(self, '_%s_length_%s' % (name, idx))
                    length_tot *= length
                    shape.append(length)
                raw = file_.read(length_tot*8)
                values = struct.unpack(length_tot*'d', raw)
                if ndim:
                    values = numpy.array(values).reshape(shape)
                else:
                    values = values[0]
            elif ramflag:
                array = getattr(self, '_%s_array' % name)
                values = array[idx]
            if (diskflag or ramflag):
                if ndim == 0:
                    setattr(self, name, values)
                else:
                    getattr(self, name)[:] = values

    def savedata(self, idx):
        """Save the internal data of all sequences with an activated flag.
        Write to file if the corresponding disk flag is activated; store
        in working memory if the corresponding ram flag is activated."""
        for name in self:
            actual = getattr(self, name)
            diskflag = getattr(self, '_%s_diskflag' % name)
            ramflag = getattr(self, '_%s_ramflag' % name)
            if diskflag:
                file_ = getattr(self, '_%s_file' % name)
                ndim = getattr(self, '_%s_ndim' % name)
                length_tot = 1
                for idx in xrange(ndim):
                    length = getattr(self, '_%s_length_%s' % (name, idx))
                    length_tot *= length
                if ndim:
                    raw = struct.pack(length_tot*'d', *actual.flatten())
                else:
                    raw = struct.pack('d', actual)
                file_.write(raw)
            elif ramflag:
                array = getattr(self, '_%s_array' % name)
                array[idx] = actual
                
    def __iter__(self):
        """Iterate over all sequence names."""
        for key in vars(self).iterkeys():
            if not key.startswith('_'):
                yield key

