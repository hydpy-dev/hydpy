# -*- coding: utf-8 -*-
"""This module implements tools for handling the parameters of
hydrological models.
"""
# import...
# ...standard
from __future__ import division, print_function
import os
import inspect
import time
import copy
import warnings
# ...third party
import numpy
# ...HydPy specific
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import filetools
from hydpy.core import timetools
from hydpy.core import autodoctools


# The import of `_strptime` is not thread save.  The following call of
# `strptime` is supposed to prevent possible problems arising from this bug.
time.strptime('1999', '%Y')


class Parameters(object):
    """Base class for handling all parameters of a specific model."""

    def __init__(self, kwargs):
        self.model = kwargs.get('model')
        self.control = None
        self.derived = None
        cythonmodule = kwargs.get('cythonmodule')
        cymodel = kwargs.get('cymodel')
        for (name, cls) in kwargs.items():
            if name.endswith('Parameters') and issubclass(cls, SubParameters):
                if cythonmodule:
                    cls_fastaccess = getattr(cythonmodule, name)
                    subpars = cls(self, cls_fastaccess, cymodel)
                else:
                    subpars = cls(self, None, None)
                setattr(self, subpars.name, subpars)

    def update(self):
        """Calls the update methods of all derived parameters."""
        if self.derived:
            for par in self.derived._PARCLASSES:
                name = objecttools.instancename(par)
                try:
                    self.derived.__dict__[name].update()
                except BaseException:
                    objecttools.augmentexcmessage(
                        'While trying to update the derived parameter `%s` of '
                        'element `%s`' % (name, objecttools.devicename(self)))

    def savecontrols(self, parameterstep=None, simulationstep=None,
                     filename=None, dirname=None):
        if self.control:
            if filename is None:
                filename = self._controldefaultfilename
            if not filename.endswith('.py'):
                filename += '.py'
            if dirname is None:
                dirname = pub.controlmanager.controlpath
            filepath = os.path.join(dirname, filename)
            with open(filepath, 'w') as file_:
                file_.write('from hydpy.models.%s import *\n\n'
                            % self.model.__module__.split('.')[2])
                if not parameterstep:
                    parameterstep = pub.timegrids.stepsize
                file_.write('parameterstep("%s")\n' % parameterstep)
                if not simulationstep:
                    simulationstep = pub.timegrids.stepsize
                file_.write('simulationstep("%s")\n\n' % simulationstep)
                for (name, par) in self.control:
                    _parameterstep = par._parameterstep
                    try:
                        par.parameterstep = parameterstep
                        file_.write(repr(par) + '\n')
                    finally:
                        par._parameterstep = _parameterstep

    @property
    def _controldefaultfilename(self):
        filename = objecttools.devicename(self)
        if filename == '?':
            raise RuntimeError(
                'To save the control parameters of a model to a file, its '
                'filename must be known.  This can be done, by passing '
                'filename to function `savecontrols` directly.  '
                'But in complete HydPy applications, it is usally '
                'assumed to be consistent with the name of the element '
                'handling the model.  Actually, neither a filename is given '
                'nor does the model know its master element.')
        else:
            return filename + '.py'

    def verify(self):
        """"""
        for (name, parameter) in self.control:
            parameter.verify()
        for (name, parameter) in self.derived:
            parameter.verify()

    def __iter__(self):
        for (key, value) in vars(self).items():
            if isinstance(value, SubParameters):
                yield key, value

    def __len__(self):
        return len(dict(self))

    def __dir__(self):
        return objecttools.dir_(self)


class MetaSubParametersType(type):
    def __new__(cls, name, parents, dict_):
        parclasses = dict_.get('_PARCLASSES')
        if parclasses is None:
            raise NotImplementedError(
                'For class `%s`, the required tuple `_PARCLASSES` is not '
                'defined.  Please see the documentation of class '
                '`SubParameters` of module `parametertools` for further '
                'information.' % name)
        if parclasses:
            lst = ['\n\n\n    The following parameter classes are selected:']
            for parclass in parclasses:
                    lst.append('      * :class:`~%s` `%s`'
                               % ('.'.join((parclass.__module__,
                                            parclass.__name__)),
                                  autodoctools.description(parclass)))
            doc = dict_.get('__doc__', None)
            if doc is None:
                doc = ''
            dict_['__doc__'] = doc + '\n'.join(l for l in lst)
        return type.__new__(cls, name, parents, dict_)


MetaSubParametersClass = MetaSubParametersType('MetaSubParametersClass',
                                               (), {'_PARCLASSES': ()})


class SubParameters(MetaSubParametersClass):
    """Base class for handling subgroups of model parameters.

    When trying to implement a new model, one has to define its parameter
    classes.  Currently, the HydPy framework  distinguishes between control
    parameters and derived parameters.  These parameter classes should be
    collected by subclasses of class :class:`SubParameters` called
    `ControlParameters` or `DerivedParameters` respectivly.  This should be
    done via the `_PARCLASSES` tuple in the following manner:

    >>> from hydpy.core.parametertools import SingleParameter, SubParameters
    >>> class Par2(SingleParameter):
    ...     pass
    >>> class Par1(SingleParameter):
    ...     pass
    >>> class ControlParameters(SubParameters):
    ...     _PARCLASSES = (Par2, Par1)

    The order within the tuple determines the order of iteration, e.g.:

    >>> control = ControlParameters(None) # Assign `None` for brevity.
    >>> control
    par2(nan)
    par1(nan)

    If one forgets to define a `_PARCLASSES` tuple so (and maybe tries to add
    the parameters in the constructor of the subclass of
    :class:`SubParameters`, the following error is raised:

    >>> class ControlParameters(SubParameters):
    ...     pass
    Traceback (most recent call last):
    ...
    NotImplementedError: For class `ControlParameters`, the required tuple `_PARCLASSES` is not defined.  Please see the documentation of class `SubParameters` of module `parametertools` for further information.
    """
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
                value.connect(self)
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

    def __repr__(self):
        lines = []
        if pub.options.reprcomments:
            lines.append('#%s object defined in module %s.'
                         % (objecttools.classname(self),
                            objecttools.modulename(self)))
            lines.append('#The implemented parameters with their actual '
                         'values are:')
        for (name, parameter) in self:
            try:
                lines.append('%s' % repr(parameter))
            except BaseException:
                lines.append('%s(?)' % name)
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class Parameter(objecttools.ValueMath):
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
                             % (self.name, objecttools.devicename(self)))
        elif not args and not kwargs:
            raise ValueError('For parameter %s of element %s neither a '
                             'positional nor a keyword argument is given.'
                             % (self.name, objecttools.devicename(self)))
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
                                         objecttools.devicename(self)))
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
        filetools.ControlManager.read2dict(pyfile, subnamespace)
        try:
            subself = subnamespace[self.name]
        except KeyError:
            raise RuntimeError('Something has gone wrong when trying to '
                               'read parameter `%s` from file `%s`.'
                               % (self.name, pyfile))
        return subself.values

    @property
    def initvalue(self):
        initvalue = (getattr(self, 'INIT', None) if
                     pub.options.usedefaultvalues else None)
        if initvalue is None:
            type_ = getattr(self, 'TYPE', float)
            if type_ is float:
                initvalue = numpy.nan
            elif type_ is int:
                initvalue = objecttools._INT_NAN
            elif type_ is bool:
                initvalue = False
            else:
                NotImplementedError(
                    'For parameter `%s` no `INIT` class attribute is '
                    'defined, but no standard value for its TYPE `%s`'
                    'is available' % (self.name, objecttools.classname(type_)))
        return initvalue

    def _getparameterstep(self):
        """The parameter time step size new parameter values might be related
        to.
        """
        if Parameter._parameterstep is None:
            raise RuntimeError('The general parameter time step has not been '
                               'defined so far.')
        else:
            return self._parameterstep

    def _setparameterstep(self, value):
        try:
            Parameter._parameterstep = timetools.Period(value)
        except Exception:
            objecttools.augmentexcmessage('While trying to set the general '
                                          'parameter time step')

    parameterstep = property(_getparameterstep, _setparameterstep)

    def _getsimulationstep(self):
        """The simulation time step size new parameter values might be related
        to.
        """
        try:
            return pub.timegrids.stepsize
        except AttributeError:
            return Parameter._simulationstep

    def _setsimulationstep(self, value):
        try:
            Parameter._simulationstep = timetools.Period(value)
        except Exception:
            objecttools.augmentexcmessage('While trying to set the general '
                                          'simulation time step')

    simulationstep = property(_getsimulationstep, _setsimulationstep)

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

    trim = objecttools.trim

    def warntrim(self):
        warnings.warn('For parameter %s of element %s at least one value '
                      'needed to be trimmed.  Two possible reasons could be '
                      'that the a parameter bound violated or that the values '
                      'of two (or more) different parameters are inconsistent.'
                      % (self.name, objecttools.devicename(self)))

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
        lines = super(Parameter, self).commentrepr()
        if (pub.options.reprcomments and
                (getattr(self, 'TIME', None) is not None)):
            lines.append('# The actual value representation depends on '
                         'the actual parameter step size,')
            lines.append('# which is `%s`.' % self.parameterstep)
        return lines

    def __str__(self):
        return str(self.values)

    def __dir__(self):
        return objecttools.dir_(self)


class SingleParameter(Parameter):
    """Base class for model parameters handling a single value."""
    NDIM, TYPE, TIME, SPAN, INIT = 0, float, None, (None, None), None

    def connect(self, subpars):
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess
        setattr(self.fastaccess, self.name, self.initvalue)

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
        return getattr(self.fastaccess, self.name, numpy.nan)

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
        setattr(self.fastaccess, self.name, value)

    value = property(_getvalue, _setvalue)
    values = value

    def verify(self):
        """Raises a :class:`~exceptions.RuntimeError` if the value of the
        instance of the respective subclass of :class:`SingleParameter` is
        `nan`.
        """
        if numpy.isnan(self.value):
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

    def __repr__(self):
        lines = self.commentrepr()
        lines.append('%s(%s)'
                     % (self.name,
                        objecttools.repr_(self.reverttimefactor(self.value))))
        return '\n'.join(lines)


class MultiParameter(Parameter):
    """Base class for model parameters handling multiple values."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (None, None)

    def connect(self, subpars):
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess
        setattr(self.fastaccess, self.name, None)

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
            array = numpy.full(shape, self.initvalue, dtype=self.TYPE)
        except Exception:
            objecttools.augmentexcmessage('While trying create a new numpy '
                                          'ndarray` for parameter `%s`'
                                          % self.name)
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
            return value
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
        setattr(self.fastaccess, self.name, value)

    value = property(_getvalue, _setvalue)
    values = value

    def _getverifymask(self):
        """A numpy array with all entries being `True` of the same
        shape as the values handled by the respective parameter.  All entries
        beeing `True` indicates that the method :func:`~MultiParameter.verify`
        checks all entries of the numpy array storing the parameter values.
        Overwrite :func:`~MultiParameter.verify` for :class:`MultiParameter`
        subclasses, where certain entries do not to be checked.
        """
        return numpy.full(self.shape, True, dtype=bool)

    verifymask = property(_getverifymask)

    def verify(self):
        """Raises a :class:`~exceptions.RuntimeError` if at least one of the
        required values of the instance of the respective subclass of
        :class:`MultiParameter` is `None` or `nan`. The property
        :func:`~MultiParameter.verifymask` defines, which values are
        considered to be necessary.
        """
        if self.values is None:
            raise RuntimeError('The values of parameter `%s` have not '
                               'been set yet.' % self.name)
        nmbnan = sum(numpy.isnan(self.values[self.verifymask]))
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
            objecttools.augmentexcmessage('While trying to item access the '
                                          'values of parameter `%s`'
                                          % self.name)

    def compressrepr(self):
        """Returns a compressed parameter value string, which is (in
        accordance with :attr:`~MultiParameter.NDIM`) contained in a
        nested list.  If the compression fails, a
        :class:`~exceptions.NotImplementedError` is raised.
        """
        if self.value is None:
            unique = numpy.array([numpy.nan])
        elif self.length == 0:
            return ['']
        else:
            unique = numpy.unique(self.values)
        if sum(numpy.isnan(unique)) == len(unique.flatten()):
            unique = numpy.array([numpy.nan])
        else:
            unique = self.reverttimefactor(unique)
        if len(unique) == 1:
            result = objecttools.repr_(unique[0])
            for idx in range(self.NDIM):
                result = [result]
            return result
        else:
            raise NotImplementedError('For parameter `%s` there is no '
                                      'compression method implemented, '
                                      'working for its actual values.'
                                      % self.name)

    def __repr__(self):
        try:
            values = self.compressrepr()
        except NotImplementedError:
            islong = self.length > 255
            values = self.reverttimefactor(self.values)
        except BaseException:
            objecttools.augmentexcmessage('While trying to find a compressed '
                                          'string representation for '
                                          'parameter `%s`' % self.name)
        else:
            islong = False
        return super(Parameter, self)._repr(values, islong)


class ZipParameter(MultiParameter):
    """Base class for model parameters handling multiple values that offers
    additional keyword zipping fuctionality.

    When inheriting an actual parameter class from :class:`ZipParameter` one
    needs to define suitable class constants
    :const:`~ZipParameter.REQUIRED_VALUES` (a :class:`tuple`) and
    :const:`~ZipParameter.MODEL_CONSTANTS` (a :class:`dict`).  Additionally,
    a property named `refparameter` must be defined.

    The implementation and functioning of subclasses of :class:`ZipParameter`
    is best illustrated by an example: see the documentation of the class
    :class:`~hydpy.models.hland.hland_parameters.MultiParameter` of the
    HydPy-H-Land model.
    """
    REQUIRED_VALUES = ()
    MODEL_CONSTANTS = {}

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`Parameter` instances
        within parameter control files.
        """
        try:
            Parameter.__call__(self, *args, **kwargs)
        except NotImplementedError as exc:
            if kwargs:
                refvalues = self.refparameter.values
                if min(refvalues) < 1:
                    raise RuntimeError('Parameter %s does not seem to '
                                       'be prepared properly for element %s.  '
                                       'Hence, setting values for parameter '
                                       '%s via keyword arguments is not '
                                       'possible.'
                                       % (self.refparameter.name,
                                          objecttools.devicename(self),
                                          self.name))
                self.values = kwargs.pop('default', numpy.nan)
                for (key, value) in kwargs.items():
                    sel = self.MODEL_CONSTANTS.get(key.upper())
                    if sel is None:
                        raise exc
                    else:
                        self.values[refvalues == sel] = value
                self.values = self.applytimefactor(self.values)
                self.trim()
            else:
                raise exc

    def _getshape(self):
        """Return a tuple containing the lengths in all dimensions of the
        parameter values.
        """
        try:
            return MultiParameter._getshape(self)
        except RuntimeError:
            raise RuntimeError('Shape information for parameter `%s` can '
                               'only be retrieved after it has been defined. '
                               ' You can do this manually, but usually it is '
                               'done automatically by defining the value of '
                               'parameter `%s` first in each parameter '
                               'control file.'
                               % (self.name, self.shapeparameter.name))

    shape = property(_getshape, MultiParameter._setshape)

    def _getverifymask(self):
        """A numpy array of the same shape as the value array handled
        by the respective parameter.  `True` entries indicate that certain
        parameter values are required, which depends on the tuple
        :const:`REQUIRED_VALUES` of the respective subclass.
        """
        mask = numpy.full(self.shape, False, dtype=bool)
        refvalues = self.refparameter.values
        for reqvalue in self.REQUIRED_VALUES:
            mask[refvalues == reqvalue] = True
        return mask

    verifymask = property(_getverifymask)

    def compressrepr(self):
        """Returns a compressed parameter value string, which is (in
        accordance with :attr:`NDIM`) contained in a nested list.  If the
        compression fails, a :class:`~exceptions.NotImplementedError` is
        raised.
        """
        try:
            return MultiParameter.compressrepr(self)
        except NotImplementedError as exc:
            results = []
            refvalues = self.refparameter.values
            if min(refvalues) < 1:
                raise NotImplementedError('Parameter %s is not defined '
                                          'poperly, which circumvents finding '
                                          'a suitable compressed.')
            for (key, value) in self.MODEL_CONSTANTS.items():
                if value in self.REQUIRED_VALUES:
                    unique = numpy.unique(self.values[refvalues == value])
                    unique = self.reverttimefactor(unique)
                    if len(unique) == 1:
                        results.append('%s=%s'
                                       % (key.lower(),
                                          objecttools.repr_(unique[0])))
                    elif len(unique) > 1:
                        raise exc
            result = ', '.join(sorted(results))
            for idx in range(self.NDIM):
                result = [result]
            return result


class SeasonalParameter(MultiParameter):
    """Class for the flexible handling of parameters with anual cycles.

    Let us prepare a 1-dimensional :class:`SeasonalParameter` instance:
    >>> from hydpy.core.parametertools import SeasonalParameter
    >>> seasonalparameter = SeasonalParameter()
    >>> seasonalparameter.NDIM = 1

    For the following examples, we assume a simulation step size of one day:

    >>> from hydpy.core.timetools import Period
    >>> seasonalparameter.simulationstep = Period('1d')

    To define its shape, the first entry of the assigned :class:`tuple`
    object is ignored:
    >>> seasonalparameter.shape = (None,)

    Instead it is derived from the `simulationstep` defined above:

    >>> seasonalparameter.shape
    (366,)

    The annual pattern of seasonal parameters is defined through pairs of
    :class:`~hydpy.core.timetools.TOY` objects and different values (e.g.
    of type :class:`float`).  One can define them all at once in the
    following manner:

    >>> seasonalparameter(_1=2., _7_1=4., _3_1_0_0_0=5.)

    Note that, as :class:`str` objects, all keywords in the call above would
    be proper :class:`~hydpy.core.timetools.TOY` initialization arguments.
    If they are not properly written, the following exception is raised:

    >>> SeasonalParameter()(_a=1.)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define parameter `seasonalparameter` of element `?`, the following error occured: While trying to retrieve the month for TOY (time of year) object based on the string `_a`, the following error occured: For TOY (time of year) objects, all properties must be of type `int`, but the value `a` of type `str` given for property `month` cannot be converted to `int`.

    As the following string representation shows, are the pairs of each
    :class:`SeasonalParameter` instance automatically sorted:

    >>> seasonalparameter
    seasonalparameter(toy_1_1_0_0_0=2.0,
                      toy_3_1_0_0_0=5.0,
                      toy_7_1_0_0_0=4.0)

    By default, `toy` is used as a prefix string.  Using this prefix string,
    one can change the toy-value pairs via attribute access:

    >>> seasonalparameter.toy_1_1_0_0_0
    2.0
    >>> del seasonalparameter.toy_1_1_0_0_0
    >>> seasonalparameter.toy_2_1_0_0_0 = 2.
    >>> seasonalparameter
    seasonalparameter(toy_2_1_0_0_0=2.0,
                      toy_3_1_0_0_0=5.0,
                      toy_7_1_0_0_0=4.0)

    On applying function :func:`len` on :class:`SeasonalParameter` objects,
    the number of toy-value pairs is returned:

    >>> len(seasonalparameter)
    3

    New values are checked to be compatible predefined shape:

    >>> seasonalparameter.toy_1_1_0_0_0 = [1., 2.]
    Traceback (most recent call last):
    ...
    TypeError: While trying to add a new or change an existing toy-value pair for the seasonal parameter `seasonalparameter` of element `?`, the following error occured: float() argument must be a string or a number...
    >>> seasonalparameter = SeasonalParameter()
    >>> seasonalparameter.NDIM = 2
    >>> seasonalparameter.shape = (None, 3)
    >>> seasonalparameter.toy_1_1_0_0_0 = [1., 2.]
    Traceback (most recent call last):
    ...
    ValueError: While trying to add a new or change an existing toy-value pair for the seasonal parameter `seasonalparameter` of element `?`, the following error occured: could not broadcast input array from shape (2) into shape (3)
    >>> seasonalparameter.toy_1_1_0_0_0 = [1., 2., 3.]
    >>> seasonalparameter
    seasonalparameter(toy_1_1_0_0_0=[1.0, 2.0, 3.0])
    """
    def __init__(self):
        MultiParameter.__init__(self)
        self._toy2values = {}

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to :class:`Parameter` instances
        within parameter control files.
        """
        self._toy2values.clear()
        try:
            MultiParameter.__call__(self, *args, **kwargs)
            self._toy2values[timetools.TOY()] = self[0]
        except BaseException as exc:
            if kwargs:
                for (toystr, values) in kwargs.items():
                    try:
                        setattr(self, str(timetools.TOY(toystr)), values)
                    except BaseException:
                        objecttools.augmentexcmessage(
                            'While trying to define parameter `%s` of element '
                            '`%s`' % (self.name, objecttools.devicename(self)))
                self.refresh()
            else:
                raise exc

    def refresh(self):
        """Update the actual simulation values based on the toy-value pairs.

        Usually, one does not need to call refresh explicitly, as it is
        called by methods __call__, __setattr__ and __delattr__ automatically,
        when required.

        Instantiate a 1-dimensional :class:`SeasonalParameter` object:

        >>> sp = SeasonalParameter()
        >>> from hydpy.core.timetools import Period
        >>> sp.simulationstep = Period('1d')
        >>> sp.NDIM = 1
        >>> sp.shape = (None,)

        When a :class:`SeasonalParameter` object does not contain any
        toy-value pairs yet, the method :func:`SeasonalParameter.refresh`
        sets all actual simulation values to zero:

        >>> sp.values = 1.
        >>> sp.refresh()
        >>> sp.values[0]
        0.0

        When there is only one toy-value pair, its values are taken for
        all actual simulation values:

        >>> sp.toy_1 = 2. # calls refresh automatically
        >>> sp.values[0]
        2.0

        Method :func:`SeasonalParameter.refresh` performs a linear
        interpolation for the central time points of each simulation time
        step.  Hence, in the following example the original values of the
        toy-value pairs do not show up:

        >>> sp.toy_12_31 = 4.
        >>> from hydpy.core.objecttools import round_
        >>> round_(sp.values[0])
        2.00274
        >>> round_(sp.values[-2])
        3.99726
        >>> sp.values[-1]
        3.0

        If one wants to preserve the original values in this example, one
        would have to set the corresponding toy instances in the middle of
        some simulation step intervalls:

        >>> del sp.toy_1
        >>> del sp.toy_12_31
        >>> sp.toy_1_1_12 = 2
        >>> sp.toy_12_31_12 = 4.
        >>> sp.values[0]
        2.0
        >>> round_(sp.values[1])
        2.005479
        >>> round_(sp.values[-2])
        3.994521
        >>> sp.values[-1]
        4.0

        """
        if len(self) == 0:
            self.values[:] = 0.
        elif len(self) == 1:
            values = list(self._toy2values.values())[0]
            self.values[:] = self.applytimefactor(values)
        else:
            tt = timetools
            timegrid = tt.Timegrid(tt.TOY._STARTDATE+self.simulationstep/2,
                                   tt.TOY._ENDDATE+self.simulationstep/2,
                                   self.simulationstep)
            for idx, date in enumerate(timegrid):
                values = self.interp(date)
                self.values[idx] = self.applytimefactor(values)

    def interp(self, date):
        """Perform a linear value interpolation for a date defined by the
        passed :class:`~hydpy.core.timetools.Date` object and return the
        result.

        Instantiate a 1-dimensional :class:`SeasonalParameter` object:

        >>> sp = SeasonalParameter()
        >>> from hydpy.core.timetools import Date, Period
        >>> sp.simulationstep = Period('1d')
        >>> sp.NDIM = 1
        >>> sp.shape = (None,)

        Define three toy-value pairs:
        >>> sp(_1=2.0, _2=5.0, _12_31=4.0)

        Passing a :class:`~hydpy.core.timetools.Date` object excatly matching
        a :class:`~hydpy.core.timetools.TOY` object of course simply returns
        the associated value:

        >>> sp.interp(Date('2000.01.01'))
        2.0
        >>> sp.interp(Date('2000.02.01'))
        5.0
        >>> sp.interp(Date('2000.12.31'))
        4.0

        For all intermediate points, a linear interpolation is performed:

        >>> from hydpy.core.objecttools import round_
        >>> round_(sp.interp(Date('2000.01.02')))
        2.096774
        >>> round_(sp.interp(Date('2000.01.31')))
        4.903226
        >>> round_(sp.interp(Date('2000.02.02')))
        4.997006
        >>> round_(sp.interp(Date('2000.12.30')))
        4.002994

        Linear interpolation is also allowed between the first and the
        last pair, when they do not capture the end points of the year:

        >>> sp(_1_2=2.0, _12_30=4.0)
        >>> round_(sp.interp(Date('2000.12.29')))
        3.99449
        >>> sp.interp(Date('2000.12.30'))
        4.0
        >>> round_(sp.interp(Date('2000.12.31')))
        3.333333
        >>> round_(sp.interp(Date('2000.01.01')))
        2.666667
        >>> sp.interp(Date('2000.01.02'))
        2.0
        >>> round_(sp.interp(Date('2000.01.03')))
        2.00551

        The following example briefly shows interpolation performed for
        2-dimensional parameter:

        >>> sp = SeasonalParameter()
        >>> from hydpy.core.timetools import Date, Period
        >>> sp.simulationstep = Period('1d')
        >>> sp.NDIM = 2
        >>> sp.shape = (None, 2)
        >>> sp(_1_1=[1., 2.], _1_3=[-3, 0.])
        >>> result = sp.interp(Date('2000.01.02'))
        >>> round_(result[0])
        -1.0
        >>> round_(result[1])
        1.0
    """
        xnew = timetools.TOY(date)
        xys = list(self)
        for idx, (x1, y1) in enumerate(xys):
            if x1 > xnew:
                x0, y0 = xys[idx-1]
                break
        else:
            x0, y0 = xys[-1]
            x1, y1 = xys[0]
        return y0+(y1-y0)/(x1-x0)*(xnew-x0)

    def _setshape(self, shape):
        try:
            shape = (int(shape),)
        except TypeError:
            pass
        shape = list(shape)
        if self.simulationstep is None:
            raise RuntimeError(
                'It is not possible the set the shape of the seasonal '
                'parameter `%s` of element `%s` at the moment.  You can '
                'define it manually.  In complete HydPy projects it is '
                'indirecty defined via `pub.timegrids.stepsize` automatically.'
                % (self.name, objecttools.devicename(self)))
        shape[0] = timetools.Period('366d')/self.simulationstep
        shape[0] = int(numpy.ceil(round(shape[0], 10)))
        MultiParameter._setshape(self, shape)
    shape = property(MultiParameter._getshape, _setshape)

    def __iter__(self):
        for toy in sorted(self._toy2values.keys()):
            yield (toy, self._toy2values[toy])

    def __getattr__(self, name):
        if name.startswith('toy_'):
            try:
                return self._toy2values[timetools.TOY(name)]
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to get an existing toy-value pair for '
                    'the seasonal parameter `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))
        else:
            return MultiParameter.__getattr__(self, name)

    def __setattr__(self, name, value):
        if name.startswith('toy_'):
            try:
                if self.NDIM == 1:
                    value = float(value)
                else:
                    value = numpy.full(self.shape[1:], value)
                self._toy2values[timetools.TOY(name)] = value
                self.refresh()
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to add a new or change an existing '
                    'toy-value pair for the seasonal parameter `%s` of '
                    'element `%s`' % (self.name, objecttools.devicename(self)))
        else:
            MultiParameter.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name.startswith('toy_'):
            try:
                del self._toy2values[timetools.TOY(name)]
                self.refresh()
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to delete an existing toy-value pair for '
                    'the seasonal parameter `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))
        else:
            MultiParameter.__delattr__(self, name)

    def __repr__(self):
        if (len(self) == 1) and (self.NDIM == 1):
            return '%s(%s)' % (self.name, list(self._toy2values.values())[0])
        elif len(self) > 0:
            lines = []
            blanks = ' '*(len(self.name))
            for idx, (toy, value) in enumerate(self):
                if self.NDIM == 2:
                    value = list(value)
                kwarg = '%s=%s' % (str(toy), repr(value))
                if idx == 0:
                    lines.append('%s(%s' % (self.name, kwarg))
                else:
                    lines.append('%s %s' % (blanks, kwarg))
            lines[-1] += ')'
            return ',\n'.join(lines)
        else:
            return self.name+'()'

    def __len__(self):
        return len(self._toy2values)

    def __dir__(self):
        return objecttools.dir_(self) + [str(toy) for (toy, value) in self]


class KeywordParameter2DType(type):
    """Add the construction of `_ROWCOLMAPPING` to :class:`type`."""

    def __new__(cls, name, parents, dict_):
        rownames = dict_.get('ROWNAMES', getattr(parents[0], 'ROWNAMES', ()))
        colnames = dict_.get('COLNAMES', getattr(parents[0], 'COLNAMES', ()))
        rowcolmappings = {}
        for (idx, rowname) in enumerate(rownames):
            for (jdx, colname) in enumerate(colnames):
                rowcolmappings['_'.join((rowname, colname))] = (idx, jdx)
        dict_['_ROWCOLMAPPINGS'] = rowcolmappings
        return type.__new__(cls, name, parents, dict_)


KeywordParameter2DMetaclass = KeywordParameter2DType(
                          'KeywordParameter2DMetaclass', (MultiParameter,), {})


class KeywordParameter2D(KeywordParameter2DMetaclass):
    """Base class for 2-dimensional model parameters which values which depend
    on two factors.

    When inheriting an actual parameter class from :class:`KeywordParameter2D`
    one needs to define the class attributes
    :const:`~KeywordParameter2D.ROWNAMES` and
    :const:`~KeywordParameter2D.COLNAMES` (both of type :class:`tuple`).
    One usual setting would be that :const:`~KeywordParameter2D.ROWNAMES`
    defines some land use classes and :const:`~KeywordParameter2D.COLNAMES`
    defines seasons, months, or the like.

    Consider the following example, where the boolean parameter `IsWarm` both
    depends on the half-year period and the hemisphere:

    >>> from hydpy.core.parametertools import KeywordParameter2D
    >>> class IsWarm(KeywordParameter2D):
    ...     TYPE = bool
    ...     ROWNAMES = ('north', 'south')
    ...     COLNAMES = ('apr2sep', 'oct2mar')

    Instantiate the defined parameter class and define its shape:

    >>> iswarm = IsWarm()
    >>> iswarm.shape = (2, 2)

    :class:`KeywordParameter2D` allows to set the values of all rows via
    keyword arguments:

    >>> iswarm(north=[True, False],
    ...        south=[False, True])
    >>> iswarm
    iswarm(north=[True, False],
           south=[False, True])
    >>> iswarm.values
    array([[ True, False],
           [False,  True]], dtype=bool)

    If a keyword is missing, a :class:`~exceptions.TypeError` is raised:

    >>> iswarm(north=[True, False])
    Traceback (most recent call last):
    ...
    ValueError: When setting parameter `iswarm` of element `?` via row related keyword arguments, each string defined in `ROWNAMES` must be used as a keyword, but the following keyword is not: `south`.

    But one can modify single rows via attribute access:

    >>> iswarm.north = False, False
    >>> iswarm.north
    array([False, False], dtype=bool)

    The same holds true for the columns:

    >>> iswarm.apr2sep = True, False
    >>> iswarm.apr2sep
    array([ True, False], dtype=bool)

    Even a combined row-column access is supported in the following manner:

    >>> iswarm.north_apr2sep
    True
    >>> iswarm.north_apr2sep = False
    >>> iswarm.north_apr2sep
    False

    All three forms of attribute access define augmented exception messages
    in case anything goes wrong:

    >>> iswarm.north = True, True, True
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign new values to parameter `iswarm` of element `?` via the row related attribute `north`, the following error occured: cannot copy sequence with size 3 to array axis with dimension 2
    >>> iswarm.apr2sep = True, True, True
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign new values to parameter `iswarm` of element `?` via the column related attribute `apr2sep`, the following error occured: cannot copy sequence with size 3 to array axis with dimension 2

    >>> iswarm.shape = (1, 1)
    >>> iswarm.south_apr2sep = False
    Traceback (most recent call last):
    ...
    IndexError: While trying to assign new values to parameter `iswarm` of element `?` via the row and column related attribute `south_apr2sep`, the following error occured: index 1 is out of bounds for axis 0 with size 1
    >>> iswarm.shape = (2, 2)

    Of course, one can define the parameter values in the common manner, e.g.:

    >>> iswarm(True)
    >>> iswarm
    iswarm(north=[True, True],
           south=[True, True])

    For parameters with many columns, string representations are properly
    wrapped:

    >>> iswarm.shape = (2, 10)
    >>> iswarm
    iswarm(north=[False, False, False, False, False, False, False, False,
                  False, False],
           south=[False, False, False, False, False, False, False, False,
                  False, False])
    """
    NDIM = 2
    ROWNAMES = ()
    COLNAMES = ()

    def connect(self, subpars):
        MultiParameter.connect(self, subpars)
        self.shape = (len(self.ROWNAMES), len(self.COLNAMES))

    def __call__(self, *args, **kwargs):
        try:
            MultiParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            for (idx, key) in enumerate(self.ROWNAMES):
                try:
                    values = kwargs[key]
                except KeyError:
                    miss = [key for key in self.ROWNAMES if key not in kwargs]
                    raise ValueError(
                        'When setting parameter `%s` of element `%s` via '
                        'row related keyword arguments, each string '
                        'defined in `ROWNAMES` must be used as a keyword, '
                        'but the following keyword%s not: `%s`.'
                        % (self.name, objecttools.devicename(self),
                           ' is' if len(miss) == 1 else 's are',
                           ', '.join(miss)))
                self.values[idx, :] = values

    def __repr__(self):
        lines = self.commentrepr()
        prefix = '%s(' % self.name
        blanks = ' '*len(prefix)
        for (idx, key) in enumerate(self.ROWNAMES):
            subprefix = ('%s%s=' % (prefix, key) if idx == 0 else
                         '%s%s=' % (blanks, key))
            lines.append(objecttools.assignrepr_list(self.values[idx, :],
                                                     subprefix, 75) + ',')
        lines[-1] = lines[-1][:-1] + ')'
        return '\n'.join(lines)

    def __getattr__(self, key):
        if key in self.ROWNAMES:
            try:
                return self.values[self.ROWNAMES.index(key), :]
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to retrieve values from parameter `%s` of '
                    'element `%s` via the row related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self.COLNAMES:
            try:
                return self.values[:, self.COLNAMES.index(key)]
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to retrieve values from parameter `%s` of '
                    'element `%s` via the columnd related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self._ROWCOLMAPPINGS:
            idx, jdx = self._ROWCOLMAPPINGS[key]
            try:
                return self.values[idx, jdx]
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to retrieve values from parameter `%s` of '
                    'element `%s` via the row and column related attribute '
                    '`%s`' % (self.name, objecttools.devicename(self), key))
        else:
            return MultiParameter.__getattr__(self, key)

    def __setattr__(self, key, values):
        if key in self.ROWNAMES:
            try:
                self.values[self.ROWNAMES.index(key), :] = values
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to assign new values to parameter `%s` of '
                    'element `%s` via the row related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self.COLNAMES:
            try:
                self.values[:, self.COLNAMES.index(key)] = values
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to assign new values to parameter `%s` of '
                    'element `%s` via the column related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self._ROWCOLMAPPINGS:
            idx, jdx = self._ROWCOLMAPPINGS[key]
            try:
                self.values[idx, jdx] = values
            except BaseException:
                objecttools.augmentexcmessage(
                    'While trying to assign new values to parameter `%s` of '
                    'element `%s` via the row and column related attribute '
                    '`%s`' % (self.name, objecttools.devicename(self), key))
        else:
            MultiParameter.__setattr__(self, key, values)

    def __dir__(self):
        return (objecttools.dir_(self) + list(self.ROWNAMES) +
                list(self.COLNAMES) + list(self._ROWCOLMAPPINGS.keys()))


class LeftRightParameter(MultiParameter):
    NDIM = 1

    def __call__(self, *args, **kwargs):
        try:
            MultiParameter.__call__(self, *args, **kwargs)
        except NotImplementedError:
            left = kwargs.get('left', kwargs.get('l'))
            if left is None:
                raise ValueError('When setting the values of parameter `%s`'
                                 'of element `%s` via keyword arguments, '
                                 'either `left` or `l` for the "left" '
                                 'parameter value must be given, but is not.'
                                 % (self.name, objecttools.devicename(self)))
            else:
                self.left = left
            right = kwargs.get('right', kwargs.get('r'))
            if right is None:
                raise ValueError('When setting the values of parameter `%s`'
                                 'of element `%s` via keyword arguments, '
                                 'either `right` or `r` for the "right" '
                                 'parameter value must be given, but is not.'
                                 % (self.name, objecttools.devicename(self)))
            else:
                self.right = right

    def connect(self, subpars):
        MultiParameter.connect(self, subpars)
        self.shape = 2

    def _getleft(self):
        """The "left" value of the actual parameter."""
        return self.values[0]

    def _setleft(self, value):
        self.values[0] = value

    left = property(_getleft, _setleft)
    l = left

    def _getright(self):
        """The "right" value of the actual parameter."""
        return self.values[1]

    def _setright(self, value):
        self.values[1] = value

    right = property(_getright, _setright)
    r = right


class IndexParameter(MultiParameter):

    def setreference(self, indexarray):
        setattr(self.fastaccess, self.name, indexarray)


autodoctools.autodoc_module()
