# -*- coding: utf-8 -*-

# import...
# ...standard
from __future__ import division, print_function
import sys
import inspect
import time
import copy
import textwrap
import warnings
# ...third party
import numpy
# ...HydPy specific
from . import pub
from . import objecttools
from . import filetools
from . import timetools


# The import of `_strptime` is not thread save.  The following call of 
# `strptime` is supposed to prevent possible problems arising from this bug. 
time.strptime('1999', '%Y')

class Parameters(object):
    """Base class for handling all parameters of a specific model."""
    
    def __init__(self, kwargs):
        self.model = kwargs.get('model')
        cythonmodule = kwargs.get('cythonmodule')
        cymodel = kwargs.get('cymodel')
        for (name, cls) in kwargs.iteritems():
            if name.endswith('Parameters') and issubclass(cls, SubParameters):
                if cythonmodule:
                    cls_fastaccess = getattr(cythonmodule, name)
                    subpars = cls(self, cls_fastaccess, cymodel)
                else:
                    subpars = cls(self, None, None)
                setattr(self, subpars.name, subpars)
                
    def update(self):
        """Needs to be defined for each individual :class:`Parameters` 
        subclass that contains `derived` paramemeters, whose values are 
        calculated on the basis of given control parameter values.
        """
    
    def verify(self):
        """"""
        for (name, parameter) in self.control:
            parameter.verify()
        for (name, parameter) in self.derived:
            parameter.verify() 
            
    def __iter__(self):
        for (key, value) in vars(self).iteritems():
            if isinstance(value, SubParameters):
                yield key, value

    def __len__(self):
        return len(dict(self))
        
    def __dir__(self):
        return objecttools.dir_(self)
            
            
class SubParameters(object):
    """Base class for handling subgroups of model parameters."""

    _PARCLASSES = ()
    
    def __init__(self, pars, cls_fastaccess=None, cymodel=None):
        self.pars = pars
        if cls_fastaccess is None:
            self.fastaccess = type('FastAccess', (), {})
        else:
            self.fastaccess = cls_fastaccess()
            setattr(cymodel, self.name, self.fastaccess)
        for Par in self._PARCLASSES:
            setattr(self, objecttools.instancename(Par), Par()) 
  
    @classmethod
    def getname(cls):
        return objecttools.instancename(cls)[:-10]

    @property
    def name(self):
        return self.getname()
        
    def __setattr__(self, name, value):
        """Attributes and methods should usually not be replaced.  Existing 
        :class:`Parameter` attributes are protected in a way, that only their
        values are changed through assignements.  For new :class:`Parameter` 
        attributes, additional `fastaccess` references are defined.  If you 
        actually want to replace a parameter, you have to delete it first.
        """
        try:
            attr = getattr(self, name)
        except AttributeError:
            object.__setattr__(self, name, value)
            if isinstance(value, Parameter):
                value.subpars = self
                value.fastaccess = self.fastaccess
                try:
                    # Necessary when working in Python mode...
                    setattr(self.fastaccess, value.name, None)
                except TypeError:
                    # ...but unnecessary and impossible in Cython mode.
                    pass
        else:
            try:
                attr._setvalue(value)
            except AttributeError:
                raise RuntimeError('`%s` instances do not allow the direct'
                                   'replacement of their members.  After '
                                   'initialization you should usually only '
                                   'change parameter values through '
                                   'assignements.  If you really need to '
                                   'replace a object member, delete it '
                                   'beforehand.' % objecttools.classname(self))  
                
    def __iter__(self):
        for Par in self._PARCLASSES:
            name = objecttools.instancename(Par)
            yield name, getattr(self, name)
    
    def __dir__(self):
        return objecttools.dir_(self)
        
        
class Parameter(objecttools.ValueMath, objecttools.Trimmer):
    """Base class for :class:`SingleParameter` and :class:`MultiParameter`."""
    
    _parameterstep = None
    _simulationstep = None
    
    def __init__(self):
        self.subpars = None
        self.fastaccess = type('JustForDemonstrationPurposes', (), 
                               {self.name: None})()
    
    def _getname(self):
        """Name of the parameter, which is the name if the instantiating 
        subclass of :class:`Parameter` in lower case letters.
        """
        return objecttools.classname(self).lower()
    name = property(_getname)                                
                                    
    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`Parameter` instances
        within parameter control files.
        """
        if args and kwargs:
            raise ValueError('For parameter %s of element %s both positional '
                             'and keyword arguments are given, which is '
                             'ambiguous.' 
                             % (self.name, objecttools.elementname(self)))
        elif not args and not kwargs:
            raise ValueError('For parameter %s of element %s neither a '
                             'positional nor a keyword argument is given.' 
                             % (self.name, objecttools.elementname(self)))            
        elif 'pyfile' in kwargs:
            values = self._getvalues_from_auxiliaryfile(kwargs['pyfile'])
            self.values = self.applytimefactor(values)
            del(kwargs['pyfile'])
        elif args:
            self.values = self.applytimefactor(numpy.array(args))
        else:
            raise NotImplementedError('The value(s) of parameter %s of '
                                      'element %s could not be set based on '
                                      'the given keyword arguments.' 
                                      % (self.name, 
                                         objecttools.elementname(self)))
        self.trim()

    def _getvalues_from_auxiliaryfile(self, pyfile):
        """Tries to return the parameter values from the auxiliary control file 
        with the given name.  
        
        Things are a little complicated here.  To understand this method, you 
        should first take a look at function :func:`parameterstep`.
        """
        frame = inspect.currentframe().f_back.f_back
        while frame:
            namespace = frame.f_locals
            try:
                subnamespace = {'model': namespace['model'],
                                'focus': self}
                break
            except KeyError:
                frame = frame.f_back
        else:
            raise RuntimeError('Something has gone wrong when trying to '
                               'read parameter `%s` from file `%s`.'
                               % (self.name, pyfile)) 
        filetools.ControlFileManager.read2dict(pyfile, subnamespace)
        try:
            subself = subnamespace[self.name]
        except KeyError:
            raise RuntimeError('Something has gone wrong when trying to '
                               'read parameter `%s` from file `%s`.'
                               % (self.name, pyfile))
        return subself.values
                                   
    def _getparameterstep(self):
        """The parameter time step size new parameter values might be related 
        to.
        """
        if self._parameterstep is None:
            raise RuntimeError('The general parameter time step has not been '
                               'defined so far.')
        else:
            return self._parameterstep
    def _setparameterstep(self, value):
        try:
            self._parameterstep = timetools.Period(value)
        except Exception:
            Exception_, message, traceback_ = sys.exc_info()
            message = ('While trying to set the general parameter time step,'
                       'the following error occured:  %s' % message)
            raise Exception_, message, traceback_
    parameterstep = property(_getparameterstep, _setparameterstep)      
    
    def _getsimulationstep(self):
        """The simulation time step size new parameter values might be related 
        to.
        """
        try:
            return pub.timegrids.stepsize
        except AttributeError:
            return self._simulationstep
    simulationstep = property(_getsimulationstep)
    
    def _gettimefactor(self):
        """Factor to adapt a new parameter value related to 
        :attr:`parameterstep` to a different simulation time step.
        """
        try:
            parfactor = pub.timegrids.parfactor
        except AttributeError:
            if self._simulationstep is None:
                raise RuntimeError('The calculation of the effective value '
                                   'of parameter `%s` requires a definition '
                                   'of the actual simulation time step.  '
                                   'The simulation time step is project '
                                   'specific.  When initializing the HydPy '
                                   'framework, it is automatically specified '
                                   'under `pub.timegrids.stepsize.  For '
                                   'testing purposes, one can alternatively '
                                   'apply the function `simulationstep`.  '
                                   'Please see the documentation for more '
                                   'details.' % self.name)
            else:
                date1 = timetools.Date('2000.01.01')
                date2 = date1 + self._simulationstep
                parfactor = timetools.Timegrids(timetools.Timegrid(
                                 date1, date2, self._simulationstep)).parfactor               
        return parfactor(self.parameterstep)
    timefactor = property(_gettimefactor)
                
    def warntrim(self):
        warnings.warn('For parameter %s of element %s at least one value '
                      'needed to be trimmed.  Two possible reasons could be '
                      'that the a parameter bound violated or that the values '
                      'of two (or more) different parameters are inconsistent.'
                      % (self.name, objecttools.elementname(self)))
                      
    def applytimefactor(self, values):
        """Change the given parameter value/values in accordance with the 
        actual parameter simulation time step if necessary, and return it/them.
        """
        # Note: At least `values /= self.timefactor` is less flexible than
        # `values = values / self.timefactor` regarding the type of `values`.
        if self.TIME is True:
            values = values * self.timefactor
        elif self.TIME is False:
            values = values / self.timefactor
        return values

    def reverttimefactor(self, values):
        """Change the given parameter value/values inversely in accordance 
        with the actual parameter simulation time step if necessary, and 
        return it/them.
        """
        # Note: At least `values /= self.timefactor` is less flexible than
        # `values = values / self.timefactor` regarding the type of `values`.
        if self.TIME is True:
            values = values / self.timefactor
        elif self.TIME is False:
            values = values * self.timefactor
        return values
    
    def commentrepr(self):
        """Returns a list with comments, e.g. for making string representations 
        more informative.  When :attr:`pub.options.reprcomments` is set to 
        `False`, an empty list is returned.
        """
        lines = []
        if pub.options.reprcomments:
            lines.append('# %s' % self.__doc__.split('\n')[0])
            if self.TIME is not None:
                lines.append('# The actual value representation depends on '
                             'the actual parameter step size, which is `%s`.' 
                             % self.parameterstep)
        return lines
                                       
    def __str__(self):
        return str(self.values)
   
    def __dir__(self):
        return objecttools.dir_(self)
        

class SingleParameter(Parameter):
    """Base class for model parameters handling a single value."""
    NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)

    def _getshape(self):
        """An empty tuple.  (Only intended for increasing consistent usability 
        of :class:`SingleParameter` and :class:`MultiParameter` instances.)
        """
        return ()                          
    def _setshape(self, shape):
        raise RuntimeError('The shape information of `SingleParameters` '
                           'as `%s` cannot be changed.' % self.name)
    shape = property(_getshape, _setshape)

    def _getvalue(self):
        """The actual parameter value handled by the respective 
        :class:`SingleParameter` instance.
        """
        values = getattr(self.fastaccess, self.name, None)
        if values is not None:
            return values
        else:
            raise RuntimeError('No value of parameter `%s` has been defined '
                               'so far.' % self.name)
    def _setvalue(self, value):
        try:
            temp = value[0]
            if len(value) > 1:
                raise ValueError('%d values are assigned to the scalar '
                                 'parameter `%s`, which is ambiguous.'
                                 % (len(value)), self.name)  
            value = temp
        except (TypeError, IndexError):
            pass 
        try:
            value = self.TYPE(value)
        except (ValueError, TypeError):
            raise TypeError('When trying to set the value of parameter `%s`, '
                             'it was not possible to convert `%s` to type '
                             '`%s`.' % (self.name, value, 
                                        objecttools.classname(self.TYPE)))
        #self.checkbounds(value)
        setattr(self.fastaccess, self.name, value)
    value = property(_getvalue, _setvalue)
    values = value 
                                 
#    def checkbounds(self, value):
#        """Raises a :class:`~exceptions.ValueError` if the given number lies 
#        outside the :attr:`SPAN` of the actual subclass of :class:`Parameter`.
#        """
#        if (self.SPAN[0] is not None) and (value < self.SPAN[0]):
#            raise ValueError('The value of parameter `%s` must not be '
#                             'less than %s, but the given value is %s.' 
#                             % (self.name, self.SPAN[0], value))
#        if (self.SPAN[1] is not None) and (value > self.SPAN[1]):
#            raise ValueError('The value of parameter `%s` must not be '
#                             'greater than %s, but the given value is %s.'
#                             % (self.name, self.SPAN[1], value))
 
    def verify(self):
        """Raises a :class:`~exceptions.RuntimeError` if the value of the 
        instance of the respective subclass of :class:`SingleParameter` is 
        `None` or `nan`.
        """
        if self.values is None:
            raise RuntimeError('The value of parameter `%s` has not been '
                               'set yet.' % self.name)     
    
    def __len__(self):
        """Returns 1.  (This method is only intended for increasing consistent 
        usability of :class:`SingleParameter` and :class:`MultiParameter` 
        instances.)
        """
        return 1

    def __getitem__(self, key):
        if key in (0, slice(None, None, None)):
            return self.value
        else:
            raise IndexError('The only allowed index for scalar parameters '
                             'like `%s` is `0` (or `:`), but `%s` is given.' 
                             % (self.name, key))            
               
    def __setitem__(self, key, value):
        if key in (0, slice(None, None, None)):
            self.value = value
        else:
            raise IndexError('The only allowed index for scalar parameters '
                             'like `%s` is `0` (or `:`), but `%s` is given.' 
                             % (self.name, key))     
#
#    def __repr__(self):
#        lines = self.commentrepr()
#        lines.append('%s(%s)' % (self.name, self.reverttimefactor(self.value)))
#        return '\n'.join(lines)
                             
                              
class MultiParameter(Parameter):
    """Base class for model parameters handling multiple values."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def _getshape(self):
        """A tuple containing the lengths in all dimensions of the parameter 
        values.  Note that setting a new shape results in a loss of all values 
        of the respective parameter.
        """
        try:
            return getattr(self.fastaccess, self.name).shape
        except AttributeError:
            raise RuntimeError('Shape information for parameter `%s` '
                               'can only be retrieved after it has been '
                               'defined.' % self.name)        
    def _setshape(self, shape):
        try:
            array = numpy.full(shape, numpy.nan, dtype=self.TYPE)
        except Exception:
            Exception_, message, traceback_ = sys.exc_info()
            message = ('While trying create a new :class:`~numpy.ndarray` '
                       'for parameter `%s`,the following error occured: %s.' 
                       % (self.name, message))
            raise Exception_, message, traceback_
        if array.ndim == self.NDIM:
            setattr(self.fastaccess, self.name, array)
        else:
            raise ValueError('Parameter `%s` is %d-dimensional but the '
                             'given shape indicates %d dimensions.'
                             % (self.name, self.NDIM, array.ndim))
    shape = property(_getshape, _setshape)
    
    def _getvalue(self):
        """The actual parameter value(s) handled by the respective 
        :class:`Parameter` instance.  For consistency, `value` and `values` 
        can always be used interchangeably.
        """
        value = getattr(self.fastaccess, self.name, None)
        if value is None:
            raise RuntimeError('No value/values of parameter `%s` has/have '
                               'been defined so far.' % self.name)
        else:
            return numpy.asarray(value)
    def _setvalue(self, value):
        try:
            value = value.value
        except AttributeError:
            pass
        try:
            value = numpy.full(self.shape, value, dtype=self.TYPE)
        except ValueError:
            raise ValueError('The values `%s` cannot be converted to a numpy '
                             'ndarray with shape %s containing entries of '
                             'type %s.' % (value, self.shape, 
                                           objecttools.classname(self.TYPE)))
        #self.checkbounds(value)
        setattr(self.fastaccess, self.name, value)
    value = property(_getvalue, _setvalue)
    values = value
    
#    def checkbounds(self, values):
#        """Raises a :class:`~exceptions.ValueError` if at least one of given 
#        numbers lies outside the :attr:`SPAN` of the actual subclass of 
#        :class:`Parameter`.
#        """
#        minvalue, maxvalue = numpy.nanmin(values), numpy.nanmax(values)
#        if ((self.SPAN[0] is not None) and  (minvalue < self.SPAN[0])):
#            raise ValueError('Parameter `%s` must not contain values less'
#                             'than %s, but the smallest given value is %s.' 
#                             % (self.name, self.SPAN[0], minvalue))
#        if ((self.SPAN[1] is not None) and (maxvalue > self.SPAN[1])):
#            raise ValueError('Parameter `%s` must not contain values greater '
#                             'than %s, but the largest given value is %s.' 
#                               % (self.name, self.SPAN[1], maxvalue))
    
    def getverifymask(self):
        """Returns a numpy array with all entries being `True` of the same
        shape as the values handled by the respective parameter.  All entries
        beeing `True` indicates that the method :func:`~MultiParameter.verify`
        checks all entries of the numpy array storing the parameter values.  
        Overwrite :func:`~MultiParameter.verify` for :class:`MultiParameter' 
        subclasses, where certain entries do not to be checked.
        """
        return numpy.full(self.shape, True, dtype=bool) 
        
    def verify(self):
        """Raises a :class:`~exceptions.RuntimeError` if at least one of the 
        required values of the instance of the respective subclass of 
        :class:`MultiParameter` is `None` or `nan`. The method 
        :func:`~MultiParameter.getverifymask` defines, which values are 
        considered to be necessary.
        """
        if self.values is None:
             raise RuntimeError('The values of parameter `%s` have not '
                                'been set yet.' % self.name)
        nmbnan = sum(numpy.isnan(self.values[self.getverifymask()]))
        if nmbnan:  
             raise RuntimeError('For parameter `%s`, %d required values have '
                                'not been set yet.' % (self.name, nmbnan)) 
    
    def copy(self):
        """Return a deep copy of the parameter values."""
        return copy.deepcopy(self.values)
        
    def __len__(self):
        """Returns the number of values handled by the :class:`MultiParameter`
        instance.  It is required, that the `shape` has been set beforehand, 
        which specifies the length in each dimension.
        """
        return numpy.cumprod(self.shape)[-1]

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
            raise RuntimeError('Parameter `%s` has no values so far.'
                               % self.name)
        else:
            Exception_, message, traceback_ = sys.exc_info()
            message = ('While trying to item access the values of parameter '
                       '`%s`, the following error occured:  %s' 
                       % (self.name, message))
            raise Exception_, message, traceback_   
    
    def compressrepr(self):
        """Returns a compressed parameter value string, which is (in 
        accordance with :attr:`~MultiParameter.NDIM`) contained in a 
        nested list.  If the compression fails, a 
        :class:`~exceptions.NotImplementedError` is raised.         
        """
        unique = numpy.unique(self.values)
        if sum(numpy.isnan(unique)) == len(unique.flatten()):
            unique = numpy.array([numpy.nan])
        else:
            unique = self.reverttimefactor(unique)
        if len(unique) == 1:
            result = str(unique[0])
            for idx in range(self.NDIM):
                result = [result]
            return result
        else:
            raise NotImplementedError('For parameter `%s` there is no '
                                      'compression method implemented, '
                                      'working for its actual values.' 
                                      % self.name)
                   
#    def __repr__(self):
#        lines = self.commentrepr()
#        try:
#            values = self.compressrepr()
#        except NotImplementedError:
#            values = self.reverttimefactor(self.values)
#        except BaseException:
#            Exception_, message, traceback_ = sys.exc_info()
#            message = ('While trying to find a compressed string '
#                       'representation for parameter `%s`, the following '
#                       'error occured:  %s' % (self.name, message))
#            raise Exception_, message, traceback_            
#        if self.NDIM == 1:       
#            cols = ', '.join(str(value) for value in values)
#            wrappedlines = textwrap.wrap(cols, 80-len(self.name)-2)
#            for (idx, line) in enumerate(wrappedlines):
#                if not idx:
#                    lines.append('%s(%s' % (self.name, line))
#                else:
#                    lines.append((len(self.name)+1)*' ' + line)
#            lines[-1] += ')'
#            return '\n'.join(lines)
#        elif self.NDIM == 2:
#            skip = (1+len(self.name)) * ' '
#            for (idx, row) in enumerate(values):
#                cols = ', '.join(str(value) for value in row)
#                if not idx:
#                    lines.append('%s(%s,' % (self.name, cols))
#                else:
#                    lines.append('%s%s,' % (skip, cols))
#            lines[-1] = lines[-1][:-1] + ')'
#            return '\n'.join(lines)
#        else:
#            raise NotImplementedError('`repr` does not yet support '
#                                      'parameters, which handle %d-'
#                                      'dimensional matrices.' % self.NDIM)
                                      
