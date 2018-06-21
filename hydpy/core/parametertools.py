# -*- coding: utf-8 -*-
"""This module implements tools for handling the parameters of
hydrological models.
"""
# import...
# ...standard
from __future__ import division, print_function
import inspect
import time
import warnings
# ...third party
import numpy
# ...HydPy specific
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import variabletools

# The import of `_strptime` is not thread save.  The following call of
# `strptime` is supposed to prevent possible problems arising from this bug.
time.strptime('1999', '%Y')


def header_controlfile(model, parameterstep=None, simulationstep=None):
    """Return the header of a normal or auxiliariy parameter control file.

    The header contains the default coding information, the import command
    for the given model and the actual parameter and simulationstep step sizes.

    The first example shows that, if you pass the model argument as a
    string, you have to take care that this string make sense:

    >>> from hydpy.core.parametertools import header_controlfile
    >>> from hydpy import Period
    >>> print(header_controlfile(model='no model class',
    ...                          parameterstep='-1h',
    ...                          simulationstep=Period('1h')))
    # -*- coding: utf-8 -*-
    <BLANKLINE>
    from hydpy.models.no model class import *
    <BLANKLINE>
    simulationstep("1h")
    parameterstep("-1h")
    <BLANKLINE>
    <BLANKLINE>

    The second example shows the saver option to pass the proper model
    object.  It also shows that function |header_controlfile| tries to
    gain the parameter and simulation step sizes from the global
    |Timegrids| object contained in module |pub| when necessary:

    >>> from hydpy.models.lland_v1 import *
    >>> parameterstep('1d')
    >>> from hydpy import pub
    >>> from hydpy import Timegrids, Timegrid
    >>> pub.timegrids = Timegrids(Timegrid('2000.01.01',
    ...                                    '2001.01.01',
    ...                                    '1h'))
    >>> print(header_controlfile(model=model))
    # -*- coding: utf-8 -*-
    <BLANKLINE>
    from hydpy.models.lland_v1 import *
    <BLANKLINE>
    simulationstep("1h")
    parameterstep("1d")
    <BLANKLINE>
    <BLANKLINE>
    """
    with Parameter.parameterstep(parameterstep), \
            Parameter.simulationstep(simulationstep):
        return ('# -*- coding: utf-8 -*-\n\n'
                'from hydpy.models.%s import *\n\n'
                'simulationstep("%s")\n'
                'parameterstep("%s")\n\n'
                % (model, Parameter.simulationstep, Parameter.parameterstep))


class IntConstant(int):
    """Class for |int| objects with individual docstrings."""

    def __new__(cls, value):
        const = int.__new__(cls, value)
        const.__doc__ = None
        frame = inspect.currentframe().f_back
        const.__module__ = frame.f_locals['__name__']
        return const


class Constants(dict):
    """Base class for defining integer constants for a specific model."""

    def __init__(self, *args, **kwargs):
        frame = inspect.currentframe().f_back
        for (key, value) in frame.f_locals.items():
            if key.isupper() and isinstance(value, IntConstant):
                kwargs[key] = value
        dict.__init__(self, *args, **kwargs)
        self.__module__ = frame.f_locals['__name__']
        self._prepare_docstrings(frame)

    @autodoctools.make_autodoc_optional
    def _prepare_docstrings(self, frame):
        """Assign docstrings to the constants handled by |Constants|
        to make them available in the interactive mode of Python."""
        filename = inspect.getsourcefile(frame)
        with open(filename) as file_:
            sources = file_.read().split('"""')
        for code, doc in zip(sources[::2], sources[1::2]):
            code = code.strip()
            key = code.split('\n')[-1].split()[0]
            value = self.get(key)
            if value:
                value.__doc__ = doc


class Parameters(object):
    """Base class for handling all parameters of a specific model."""

    _names_subpars = ('control', 'derived', 'solver')

    def __init__(self, kwargs):
        self.model = kwargs.get('model')
        self.control = None
        self.derived = None
        self.solver = None
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
        """Call the update methods of all derived and solver parameters."""
        for subpars in self.secondary_subpars:
            for par in subpars._PARCLASSES:
                name = objecttools.instancename(par)
                try:
                    subpars.__dict__[name].update()
                except BaseException:
                    objecttools.augment_excmessage(
                        'While trying to update the %s parameter `%s` of '
                        'element `%s`'
                        % (name, subpars.name, objecttools.devicename(self)))

    def save_controls(self, filename=None, parameterstep=None,
                      simulationstep=None, auxfiler=None):
        if self.control:
            if not filename:
                filename = self._controldefaultfilename
            if auxfiler:
                variable2auxfile = getattr(auxfiler, str(self.model), None)
            else:
                variable2auxfile = None
            lines = [
                header_controlfile(self.model, parameterstep, simulationstep)]
            for par in self.control:
                if variable2auxfile:
                    auxfilename = variable2auxfile.get_filename(par)
                    if auxfilename:
                        lines.append("%s(auxfile='%s')\n"
                                     % (par.name, auxfilename))
                        continue
                lines.append(repr(par) + '\n')
            pub.controlmanager.save_file(filename, ''.join(lines))

    @property
    def _controldefaultfilename(self):
        filename = objecttools.devicename(self)
        if filename == '?':
            raise RuntimeError(
                'To save the control parameters of a model to a file, its '
                'filename must be known.  This can be done, by passing '
                'filename to function `save_controls` directly.  '
                'But in complete HydPy applications, it is usally '
                'assumed to be consistent with the name of the element '
                'handling the model.  Actually, neither a filename is given '
                'nor does the model know its master element.')
        else:
            return filename + '.py'

    def verify(self):
        for parameter in self.control:
            parameter.verify()
        for parameter in self.derived:
            parameter.verify()

    @property
    def secondary_subpars(self):
        for subpars in (self.derived, self.solver):
            if subpars is not None:
                yield subpars

    def __iter__(self):
        for name in self._names_subpars:
            subpars = getattr(self, name)
            if subpars is not None:
                yield subpars

    def __len__(self):
        return len(dict(self))

    def __dir__(self):
        return objecttools.dir_(self)


class _MetaSubParametersType(type):

    def __new__(mcs, name, parents, dict_):
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
                lst.append('      * :class:`~%s` %s'
                           % ('.'.join((parclass.__module__,
                                        parclass.__name__)),
                              autodoctools.description(parclass)))
            doc = dict_.get('__doc__', None)
            if doc is None:
                doc = ''
            dict_['__doc__'] = doc + '\n'.join(l for l in lst)
        return type.__new__(mcs, name, parents, dict_)


_MetaSubParametersClass = _MetaSubParametersType('_MetaSubParametersClass',
                                                 (), {'_PARCLASSES': ()})


class SubParameters(_MetaSubParametersClass):
    """Base class for handling subgroups of model parameters.

    When trying to implement a new model, one has to define its parameter
    classes.  Currently, the HydPy framework  distinguishes between control
    parameters and derived parameters.  These parameter classes should be
    collected by subclasses of class |SubParameters| called
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

    If one forgets to define a `_PARCLASSES` tuple so (and maybe tries to
    add the parameters in the constructor of the subclass of |SubParameters|,
    the following error is raised:

    >>> class ControlParameters(SubParameters):
    ...     pass
    Traceback (most recent call last):
    ...
    NotImplementedError: For class `ControlParameters`, the required \
tuple `_PARCLASSES` is not defined.  Please see the documentation of \
class `SubParameters` of module `parametertools` for further information.

    The `in` operator can be used to check if a certain |SubParameters|
    object handles a certain type of parameter:

    >>> Par1 in control
    True
    >>> Par1() in control
    True
    >>> SingleParameter in control
    False
    >>> 1 in control
    Traceback (most recent call last):
    ...
    TypeError: The given value `1` of type `int` is neither a \
parameter class nor a parameter instance.
    """
    _PARCLASSES = ()

    def __init__(self, pars, cls_fastaccess=None, cymodel=None):
        self.pars = pars
        if cls_fastaccess is None:
            self.fastaccess = objecttools.FastAccess()
        else:
            self.fastaccess = cls_fastaccess()
            setattr(cymodel.parameters, self.name, self.fastaccess)
        for par in self._PARCLASSES:
            setattr(self, objecttools.instancename(par), par())

    @classmethod
    def getname(cls):
        return objecttools.instancename(cls)[:-10]

    @property
    def name(self):
        return self.getname()

    def __setattr__(self, name, value):
        """Attributes and methods should usually not be replaced.  Existing
        |Parameter| attributes are protected in a way, that only their
        values are changed through assignements.  For new |Parameter|
        attributes, additional `fastaccess` references are defined.  If you
        actually want to replace a parameter, you have to delete it first.
        """
        try:
            attr = getattr(self, name)
        except AttributeError:
            object.__setattr__(self, name, value)
            if isinstance(value, abctools.ParameterABC):
                value.connect(self)
        else:
            try:
                attr._set_value(value)
            except AttributeError:
                raise RuntimeError(
                    '`%s` instances do not allow the direct replacement of '
                    'their members.  After initialization you should usually '
                    'only change parameter values through assignements.  '
                    'If you really need to replace a object member, '
                    'delete it beforehand.' % objecttools.classname(self))

    def __iter__(self):
        for par in self._PARCLASSES:
            name = objecttools.instancename(par)
            yield getattr(self, name)

    def __contains__(self, parameter):
        if isinstance(parameter, abctools.ParameterABC):
            parameter = type(parameter)
        if parameter in self._PARCLASSES:
            return True
        try:
            if issubclass(parameter, abctools.ParameterABC):
                return False
        except TypeError:
            pass
        raise TypeError(
            'The given %s is neither a parameter class '
            'nor a parameter instance.'
            % objecttools.value_of_type(parameter))

    def __repr__(self):
        lines = []
        if pub.options.reprcomments:
            lines.append('# %s object defined in module %s.'
                         % (objecttools.classname(self),
                            objecttools.modulename(self)))
            lines.append('# The implemented parameters with their actual '
                         'values are:')
        for parameter in self:
            try:
                lines.append('%s' % repr(parameter))
            except BaseException:
                lines.append('%s(?)' % parameter.name)
        return '\n'.join(lines)

    def __dir__(self):
        return objecttools.dir_(self)


class _Period(timetools.Period):

    def __init__(self, stepsize=None):
        self.stepsize = stepsize
        timetools.Period.__init__(self, stepsize.period)
        self.old_period = timetools.Period(self)
        self.__doc__ = stepsize.__doc__

    def __enter__(self):
        return self

    def __call__(self, stepsize):
        if stepsize is not None:
            self.timedelta = stepsize
            self.stepsize.period.timedelta = stepsize
        return self

    def __exit__(self, type_, value, traceback):
        self.stepsize.period = self.old_period

    def check(self):
        if not self:
            raise RuntimeError(self.stepsize.EXC_MESSAGE)

    def delete(self):
        self.timedelta = None
        self.stepsize.period.timedelta = None
        return self


class _Stepsize(object):
    """Base class of the descriptor classes |Parameterstep| and
    |Simulationstep|."""

    def __init__(self):
        self.period = timetools.Period()

    def __set__(self, obj, value):
        self(value)

    def __delete__(self, obj):
        del self.period.timedelta

    def __call__(self, value):
        try:
            period = timetools.Period(value)
            if period >= '1s':
                self.period = period
            else:
                raise ValueError(
                    'The smallest step size allowed is one second.')
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to (re)define the general %s size with %s'
                % (self.name, objecttools.value_of_type(value)))

    @property
    def name(self):
        return objecttools.instancename(self)


class Parameterstep(_Stepsize):
    """The actual parameter time step size.

    Usually, the time step size of the units of certain parameters
    is defined within control files via function |parameterstep|.
    But it can also be changed interactively with the help of any
    |Parameter| object:

    >>> from hydpy.core.parametertools import Parameter
    >>> parameter = Parameter()
    >>> parameter.parameterstep = '1d'
    >>> parameter.parameterstep
    Period('1d')

    Note that setting the step size affects all parameters!

    Getting the step size via the |Parameter| subclasses themselves
    works also fine, but use a method call instead of an assignement to
    change the step size in order to prevent from overwriting the
    descriptor:

    >>> Parameter.parameterstep
    Period('1d')
    >>> Parameter.parameterstep('2d')
    Period('2d')

    Unreasonable assignements result in error messages like the following:

    >>> parameter.parameterstep = '0d'
    Traceback (most recent call last):
    ...
    ValueError: While trying to (re)define the general parameterstep size \
with value `0d` of type `str`, the following error occured: The smallest \
step size allowed is one second.

    After deleting the parameter step size, an empty period object is returned:

    >>> del parameter.parameterstep
    >>> ps = parameter.parameterstep
    >>> ps
    Period()

    In case you prefer an exception instead of an empty period object,
    call its `check` method:

    >>> ps.check()
    Traceback (most recent call last):
    ...
    RuntimeError: No general parameter step size has been defined.

    For temporary step size changes, Pythons `with` statement is supported:

    >>> parameter.parameterstep = '1d'
    >>> with parameter.parameterstep('2h'):
    ...     print(repr(parameter.parameterstep))
    Period('2h')
    >>> parameter.parameterstep
    Period('1d')

    Passing |None| means "change nothing in this context" (usefull for
    defining functions with optional `parameterstep` arguments):

    >>> with parameter.parameterstep(None):
    ...     print(repr(parameter.parameterstep))
    Period('1d')
    >>> parameter.parameterstep
    Period('1d')

    Deleting the stepsize temporarily, requires calling method `delete`:

    >>> with parameter.parameterstep.delete():
    ...     print(repr(parameter.parameterstep))
    Period()
    >>> parameter.parameterstep
    Period('1d')
    """

    EXC_MESSAGE = 'No general parameter step size has been defined.'

    def __get__(self, obj, cls):
        return _Period(self)


class Simulationstep(_Stepsize):
    """The actual (or surrogate) simulation time step size.

    .. testsetup::

       >>> from hydpy import pub
       >>> pub.timegrids = None
       >>> from hydpy.core.parametertools import Parameter
       >>> Parameter.simulationstep.delete()
       Period()

    Usually, the simulation step size is defined globally in module
    |pub| via a |Timegrids| object, or locally via function |simulationstep|
    in separate control files.  But you can also change it interactively
    with the help of |Parameter| objects.

    Generally, the documentation on class |Parameterstep| also holds
    true for class |Simulationstep|.  The following explanations
    focus on the differences only.

    As long as no usual or surrogate simulation time step is defined, an
    empty period object is returned, which can be used to raise the
    following exception:

    >>> from hydpy.core.parametertools import Parameter
    >>> parameter = Parameter()
    >>> ps = parameter.simulationstep
    >>> ps
    Period()
    >>> ps.check()
    Traceback (most recent call last):
    ...
    RuntimeError: Neither a global simulation time grid nor a general \
simulation step size to be used as a surrogate for testing purposes has \
been defined.

    For testing or documentation purposes a surrogate step size can be set:

    >>> parameter.simulationstep = '1d'
    >>> parameter.simulationstep
    Period('1d')

    But in complete HydPy applications, changing the simulation step
    size  would be highly error prone.  Hence, being defined globally
    within the |pub| module, predefined surrogate values are ignored:

    >>> from hydpy import pub
    >>> from hydpy import Timegrids, Timegrid
    >>> pub.timegrids = Timegrids(Timegrid('2000.01.01',
    ...                                    '2001.01.01',
    ...                                    '2h'))
    >>> parameter.simulationstep
    Period('2h')

    This priority remains unchanged, even when one tries to set a surrogate
    value after the timegrid object has been defined:

    >>> parameter.simulationstep = '5s'
    >>> parameter.simulationstep
    Period('2h')

    One has to delete the timegrid object to make the surrogate simulation
    step size accessible:

    >>> del pub.timegrids
    >>> parameter.simulationstep
    Period('5s')
    """
    EXC_MESSAGE = ('Neither a global simulation time grid nor a general '
                   'simulation step size to be used as a surrogate for '
                   'testing purposes has been defined.')

    def __get__(self, obj, cls):
        period = _Period(self)
        try:
            period.timedelta = pub.timegrids.stepsize
        except AttributeError:
            pass
        return period


class Parameter(variabletools.Variable):
    """Base class for |SingleParameter| and |MultiParameter|."""

    NOT_DEEPCOPYABLE_MEMBERS = ('subpars', 'fastaccess')
    TYPE2INITVALUE = {float: numpy.nan,
                      int: variabletools._INT_NAN,
                      bool: False}

    parameterstep = Parameterstep()
    simulationstep = Simulationstep()

    def __init__(self):
        self.subpars = None
        self.fastaccess = objecttools.FastAccess()

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |Parameter| instances
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
            warnings.warn(exceptiontools.HydPyDeprecationWarning(
                'The keyword name to define a parameter value in an auxiliary '
                'control file is now `auxfile`.  The old keyword name '
                '`pyfile` will be banned in the future.'))
            values = self._get_values_from_auxiliaryfile(kwargs['pyfile'])
            self.values = self.apply_timefactor(values)
            del kwargs['pyfile']
        elif 'auxfile' in kwargs:
            values = self._get_values_from_auxiliaryfile(kwargs['auxfile'])
            self.values = self.apply_timefactor(values)
            del kwargs['auxfile']
        elif args:
            self.values = self.apply_timefactor(numpy.array(args))
        else:
            raise NotImplementedError('The value(s) of parameter %s of '
                                      'element %s could not be set based on '
                                      'the given keyword arguments.'
                                      % (self.name,
                                         objecttools.devicename(self)))
        self.trim()

    def _get_values_from_auxiliaryfile(self, pyfile):
        """Tries to return the parameter values from the auxiliary control file
        with the given name.

        Things are a little complicated here.  To understand this method, you
        should first take a look at function |parameterstep|.
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
        """Actual initial value of the given parameter.

        Some |Parameter| subclasses define a class attribute `INIT`.
        Let's define a test class and prepare a function for initializing
        a parameter object and connecting it to a |SubParameters| object:

        >>> from hydpy.core import parametertools
        >>> class Test(parametertools.SingleParameter):
        ...     NDIM, TYPE, TIME, SPAN = 0, float, None, (None, None)
        ...     INIT = 2.0
        >>> def prepare():
        ...     test = Test()
        ...     from hydpy.core.parametertools import SubParameters
        ...     subpars = parametertools.SubParameters(None)
        ...     test.connect(subpars)
        ...     return test

        By default, making use of the `INIT` attribute is disabled:

        >>> test = prepare()
        >>> test
        test(nan)

        This can be changed through setting |Options.usedefaultvalues| to
        `True`:

        >>> from hydpy import pub
        >>> pub.options.usedefaultvalues = True
        >>> test = prepare()
        >>> test
        test(2.0)

        When no `INIT` attribute is defined, enabling
        |Options.usedefaultvalues| has no effect, of course:

        >>> del Test.INIT
        >>> test = prepare()
        >>> test
        test(nan)

        For time dependent parameter values, the `INIT` attribute is assumed
        to be related to a |Parameterstep| of one day:

        >>> test.parameterstep = '2d'
        >>> test.simulationstep = '12h'
        >>> Test.INIT = 2.0
        >>> Test.TIME = True
        >>> test = prepare()
        >>> test
        test(4.0)
        >>> test.value
        1.0

        Note the following `nan` surrogate values for types |bool| and
        |int| (for |bool|, a better solution should be found):

        >>> Test.TIME = None
        >>> Test.TYPE = bool
        >>> del Test.INIT
        >>> test = prepare()
        >>> test
        test(False)
        >>> Test.TYPE = int
        >>> test = prepare()
        >>> test
        test(-999999)

        For not supported types, the following error message is raised:

        >>> Test.TYPE = list
        >>> test = prepare()
        Traceback (most recent call last):
        ...
        AttributeError: For parameter ``test` of element `?`` no `INIT` \
class attribute is defined, but no standard value for its type `list` is \
available.
        """
        initvalue = (getattr(self, 'INIT', None) if
                     pub.options.usedefaultvalues else None)
        if initvalue is None:
            initvalue = self.TYPE2INITVALUE.get(self.TYPE)
            if initvalue is None:
                raise AttributeError(
                    'For parameter `%s` no `INIT` class attribute is defined, '
                    'but no standard value for its type `%s` is available.'
                    % (objecttools.elementphrase(self),
                       objecttools.classname(self.TYPE)))
        else:
            with Parameter.parameterstep('1d'):
                initvalue = self.apply_timefactor(initvalue)
        return initvalue

    def _gettimefactor(self):
        """Factor to adapt a new parameter value related to |parameterstep|
        to a different simulation time step.
        """
        try:
            parfactor = pub.timegrids.parfactor
        except AttributeError:
            if not self.simulationstep:
                raise RuntimeError(
                    'The calculation of the effective value of parameter '
                    '`%s` requires a definition of the actual simulation time '
                    'step.  The simulation time step is project specific.  '
                    'When initializing the HydPy framework, it is '
                    'automatically specified under `pub.timegrids.stepsize`.  '
                    'For testing purposes, one can e.g. alternatively apply '
                    'the function `simulationstep`.  Please see the '
                    'documentation for more details.' % self.name)
            else:
                date1 = timetools.Date('2000.01.01')
                date2 = date1 + self.simulationstep
                parfactor = timetools.Timegrids(timetools.Timegrid(
                    date1, date2, self.simulationstep)).parfactor
        return parfactor(self.parameterstep)

    timefactor = property(_gettimefactor)

    def trim(self, lower=None, upper=None):
        """Apply |trim| of module |variabletools|."""
        variabletools.trim(self, lower, upper)

    def warn_trim(self):
        warnings.warn(
            'For parameter %s of element %s at least one value '
            'needed to be trimmed.  Two possible reasons could be '
            'that the a parameter bound violated or that the values '
            'of two (or more) different parameters are inconsistent.'
            % (self.name, objecttools.devicename(self)))

    def apply_timefactor(self, values):
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

    def revert_timefactor(self, values):
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
        """Returns a list with comments, e.g. for making string
        representations more informative.  When |Options.reprcomments|
        is set to |False|, an empty list is returned.
        """
        lines = variabletools.Variable.commentrepr(self)
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


abctools.ParameterABC.register(Parameter)


class SingleParameter(Parameter):
    """Base class for model parameters handling a single value."""
    NDIM, TYPE, TIME, SPAN, INIT = 0, float, None, (None, None), None

    def connect(self, subpars):
        self.subpars = subpars
        self.fastaccess = subpars.fastaccess
        setattr(self.fastaccess, self.name, self.initvalue)

    @staticmethod
    def _getshape():
        """An empty tuple.  (Only intended for increasing consistent usability
        of |SingleParameter| and |MultiParameter| instances.)
        """
        return ()

    def _setshape(self, shape):
        raise RuntimeError(
            'The shape information of `SingleParameters` '
            'as `%s` cannot be changed.'
            % objecttools.elementphrase(self))

    shape = property(_getshape, _setshape)

    def _get_value(self):
        """The actual parameter value handled by the respective
        |SingleParameter| instance.
        """
        return getattr(self.fastaccess, self.name, numpy.nan)

    def _set_value(self, value):
        try:
            temp = value[0]
            if len(value) > 1:
                raise ValueError(
                    '%d values are assigned to the scalar '
                    'parameter `%s`, which is ambiguous.'
                    % (len(value), objecttools.elementphrase(self)))
            value = temp
        except (TypeError, IndexError):
            pass
        try:
            value = self.TYPE(value)
        except (ValueError, TypeError):
            raise TypeError(
                'When trying to set the value of parameter `%s`, '
                'it was not possible to convert `%s` to type `%s`.'
                % (objecttools.elementphrase(self), value,
                   objecttools.classname(self.TYPE)))
        setattr(self.fastaccess, self.name, value)

    value = property(_get_value, _set_value)
    values = value

    def verify(self):
        """Raises a |RuntimeError| if the value of the instance of the
        respective subclass of |SingleParameter| is `nan`.
        """
        if numpy.isnan(self.value):
            raise RuntimeError('The value of parameter `%s` has not been '
                               'set yet.' % self.name)

    def __len__(self):
        """Returns 1.  (This method is only intended for increasing consistent
        usability of |SingleParameter| and |MultiParameter| instances.)
        """
        return 1

    def __getitem__(self, key):
        if key in (0, slice(None, None, None)):
            return self.value
        else:
            raise IndexError(
                'The only allowed index for scalar parameters '
                'like `%s` is `0` (or `:`), but `%s` is given.'
                % (objecttools.elementphrase(self), key))

    def __setitem__(self, key, value):
        if key in (0, slice(None, None, None)):
            self.value = value
        else:
            raise IndexError(
                'The only allowed index for scalar parameters '
                'like `%s` is `0` (or `:`), but `%s` is given.'
                % (objecttools.elementphrase(self), key))

    def __repr__(self):
        lines = self.commentrepr()
        lines.append(
            '%s(%s)'
            % (self.name,
               objecttools.repr_(self.revert_timefactor(self.value))))
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
            shape = getattr(self.fastaccess, self.name).shape
            return tuple(int(x) for x in shape)
        except AttributeError:
            raise RuntimeError(
                'Shape information for parameter `%s` can only '
                'be retrieved after it has been defined.'
                % objecttools.elementphrase(self))

    def _setshape(self, shape):
        try:
            array = numpy.full(shape, self.initvalue, dtype=self.TYPE)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying create a new numpy ndarray` for parameter `%s`'
                % objecttools.elementphrase(self))
        if array.ndim == self.NDIM:
            setattr(self.fastaccess, self.name, array)
        else:
            raise ValueError(
                'Parameter `%s` is %d-dimensional but the '
                'given shape indicates %d dimensions.'
                % (objecttools.elementphrase(self), self.NDIM, array.ndim))

    shape = property(_getshape, _setshape)

    def _get_value(self):
        """The actual parameter value(s) handled by the respective
        |Parameter| instance.  For consistency, `value` and `values`
        can always be used interchangeably.
        """
        value = getattr(self.fastaccess, self.name, None)
        if value is None:
            return value
        return numpy.asarray(value)

    def _set_value(self, value):
        try:
            value = value.value
        except AttributeError:
            pass
        try:
            value = numpy.full(self.shape, value, dtype=self.TYPE)
        except ValueError:
            raise ValueError(
                'The values `%s` cannot be converted to a numpy ndarray '
                'with shape %s containing entries of type %s.'
                % (value, self.shape, objecttools.classname(self.TYPE)))
        setattr(self.fastaccess, self.name, value)

    value = property(_get_value, _set_value)
    values = value

    def _getverifymask(self):
        """A numpy array with all entries being |True| of the same
        shape as the values handled by the respective parameter.  All entries
        being |True| indicates that the method |MultiParameter.verify|
        checks all entries of the numpy array storing the parameter values.
        Overwrite |MultiParameter.verify| for |MultiParameter|
        subclasses, where certain entries do not to be checked.
        """
        return numpy.full(self.shape, True, dtype=bool)

    verifymask = property(_getverifymask)

    def verify(self):
        """Raises a |RuntimeError| if at least one of the required values
        of the instance of the respective subclass of |MultiParameter| is
        |None| or |numpy.nan|. The property |MultiParameter.verifymask|
        defines, which values are considered to be necessary.
        """
        if self.values is None:
            raise RuntimeError(
                'The values of parameter `%s` have not been set yet.'
                % self.name)
        nmbnan = sum(numpy.isnan(self.values[self.verifymask]))
        if nmbnan:
            raise RuntimeError(
                'For parameter `%s`, %d required values have '
                'not been set yet.'
                % (self.name, nmbnan))

    def __len__(self):
        """Returns the number of values handled by the |MultiParameter|
        instance.  It is required, that the `shape` has been set beforehand,
        which specifies the length in each dimension.
        """
        return numpy.cumprod(self.shape)[-1]

    def __getitem__(self, key):
        try:
            return self.values[key]
        except BaseException:
            self._raiseitemexception()

    def __setitem__(self, key, values):
        try:
            self.values[key] = values
        except BaseException:
            self._raiseitemexception()

    def _raiseitemexception(self):
        if self.values is None:
            raise RuntimeError(
                'Parameter `%s` has no values so far.'
                % self.name)
        else:
            objecttools.augment_excmessage(
                'While trying to item access the values of parameter `%s`'
                % self.name)

    def compress_repr(self):
        """Returns a compressed parameter value string, which is (in
        accordance with |MultiParameter.NDIM|) contained in a nested list.
        If the compression fails, a |NotImplementedError| is raised.
        """
        if self.value is None:
            unique = numpy.array([self.TYPE2INITVALUE.get(self.TYPE)])
        elif self.length == 0:
            return ['']
        else:
            unique = numpy.unique(self.values[self.mask])
        if sum(numpy.isnan(unique)) == len(unique.flatten()):
            unique = numpy.array([numpy.nan])
        else:
            unique = self.revert_timefactor(unique)
        if len(unique) == 1:
            result = objecttools.repr_(unique[0])
            for dummy in range(self.NDIM):
                result = [result]
            return result
        else:
            raise NotImplementedError(
                'For parameter %s there is no compression method '
                'implemented, working for its actual values.'
                % objecttools.elementphrase(self))

    def __repr__(self):
        try:
            values = self.compress_repr()
        except NotImplementedError:
            islong = self.length > 255
            values = self.revert_timefactor(self.values)
        except BaseException:
            objecttools.augment_excmessage(
                'While trying to find a compressed '
                'string representation for parameter `%s`'
                % self.name)
        else:
            islong = False
        return Parameter.to_repr(self, values, islong)


class ZipParameter(MultiParameter):
    """Base class for model parameters handling multiple values that
    offers additional keyword zipping fuctionality.

    When inheriting an actual parameter class from |ZipParameter| one
    needs to define suitable class constants |ZipParameter.REQUIRED_VALUES|
    (a |tuple|) and |ZipParameter.MODEL_CONSTANTS| (a |dict|).
    Additionally, property |ZipParameter.refparameter| must be overwritten.

    The implementation and functioning of subclasses of |ZipParameter|
    is best illustrated by an example: see the documentation of the class
    |hland_parameters.MultiParameter| of base model |hland|.
    """
    REQUIRED_VALUES = ()
    MODEL_CONSTANTS = {}

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |Parameter| instances
        within parameter control files.
        """
        try:
            Parameter.__call__(self, *args, **kwargs)
        except NotImplementedError as exc:
            if kwargs:
                refvalues = self.refparameter.values
                if min(refvalues) < 1:
                    raise RuntimeError(
                        'Parameter %s does not seem to be prepared properly '
                        'for %s.  Hence, setting values for parameter %s '
                        'via keyword arguments is not possible.'
                        % (self.refparameter.name,
                           objecttools.elementphrase(self),
                           self.name))
                self.values = kwargs.pop('default', numpy.nan)
                for (key, value) in kwargs.items():
                    sel = self.MODEL_CONSTANTS.get(key.upper())
                    if sel is None:
                        raise exc
                    else:
                        self.values[refvalues == sel] = value
                self.values = self.apply_timefactor(self.values)
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
            raise RuntimeError(
                'Shape information for parameter `%s` can only be '
                'retrieved after it has been defined.  You can do '
                'this manually, but usually it is done automatically '
                'by defining the value of parameter `%s` first in '
                'each parameter control file.'
                % (self.name, self.shapeparameter.name))

    shape = property(_getshape, MultiParameter._setshape)

    @property
    def verifymask(self):
        """A |numpy.ndarray| of the same shape as the value array handled
        by the respective |ZipParameter| object.  |True| entries indicate
        that certain parameter values are required, which depends on the
        tuple |ZipParameter.REQUIRED_VALUES| of the respective subclass.
        """
        mask = numpy.full(self.shape, False, dtype=bool)
        refvalues = self.refparameter.values
        for reqvalue in self.REQUIRED_VALUES:
            mask[refvalues == reqvalue] = True
        return mask

    def compress_repr(self):
        """Return a compressed parameter value string, which is (in
        accordance with `NDIM`) contained in a nested list.  If the
        compression fails, a |NotImplementedError| is raised.
        """
        try:
            return MultiParameter.compress_repr(self)
        except NotImplementedError as exc:
            results = []
            refvalues = self.refparameter.values
            if min(refvalues) < 1:
                raise NotImplementedError(
                    'Parameter %s is not defined poperly, which '
                    'circumvents finding a suitable compressed.')
            for (key, value) in self.MODEL_CONSTANTS.items():
                if value in self.REQUIRED_VALUES:
                    unique = numpy.unique(self.values[refvalues == value])
                    unique = self.revert_timefactor(unique)
                    if len(unique) == 1:
                        results.append('%s=%s'
                                       % (key.lower(),
                                          objecttools.repr_(unique[0])))
                    elif len(unique) > 1:
                        raise exc
            result = ', '.join(sorted(results))
            for dummy in range(self.NDIM):
                result = [result]
            return result

    @property
    def refparameter(self):
        """Reference to the associated |MultiParameter| object providing
        the actual constant values.

        Needs to be overwritten by subclasses:

        >>> from hydpy.core.parametertools import ZipParameter
        >>> class Test(ZipParameter):
        ...     pass
        >>> Test().refparameter
        Traceback (most recent call last):
        ...
        NotImplementedError: Property `refparameter` of class \
`ZipParameter` must be overwritten by subclasses, which is not \
the case for class `Test`.
        """
        raise NotImplementedError(
            'Property `refparameter` of class `ZipParameter` '
            'must be overwritten by subclasses, which is not '
            'the case for class `%s`.'
            % objecttools.classname(self))


class SeasonalParameter(MultiParameter):
    """Class for the flexible handling of parameters with anual cycles.

    Let us prepare a 1-dimensional |SeasonalParameter| instance:

    >>> from hydpy.core.parametertools import SeasonalParameter
    >>> seasonalparameter = SeasonalParameter()
    >>> seasonalparameter.NDIM = 1

    For the following examples, we assume a simulation step size of one day:

    >>> seasonalparameter.simulationstep = '1d'

    To define its shape, the first entry of the assigned |tuple|
    object is ignored:

    >>> seasonalparameter.shape = (None,)

    Instead it is derived from the `simulationstep` defined above:

    >>> seasonalparameter.shape
    (366,)

    The annual pattern of seasonal parameters is defined through pairs of
    |TOY| objects and different values (e.g. of type |float|).  One can
    define them all at once in the following manner:

    >>> seasonalparameter(_1=2., _7_1=4., _3_1_0_0_0=5.)

    Note that, as |str| objects, all keywords in the call above would
    be proper |TOY| initialization arguments. If they are not properly
    written, the following exception is raised:

    >>> SeasonalParameter()(_a=1.)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the seasonal parameter value \
`seasonalparameter` of element `?` for time of year `_a`, the following \
error occured: While trying to retrieve the month for TOY (time of year) \
object based on the string `_a`, the following error occured: \
For TOY (time of year) objects, all properties must be of type `int`, \
but the value `a` of type `str` given for property `month` cannot be \
converted to `int`.

    As the following string representation shows, are the pairs of each
    |SeasonalParameter| instance automatically sorted:

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

    On applying function |len| on |SeasonalParameter| objects, the number
    of toy-value pairs is returned:

    >>> len(seasonalparameter)
    3

    New values are checked to be compatible predefined shape:

    >>> seasonalparameter.toy_1_1_0_0_0 = [1., 2.]
    Traceback (most recent call last):
    ...
    TypeError: While trying to add a new or change an existing toy-value \
pair for the seasonal parameter `seasonalparameter` of element `?`, the \
following error occured: float() argument must be a string or a number...
    >>> seasonalparameter = SeasonalParameter()
    >>> seasonalparameter.NDIM = 2
    >>> seasonalparameter.shape = (None, 3)
    >>> seasonalparameter.toy_1_1_0_0_0 = [1., 2.]
    Traceback (most recent call last):
    ...
    ValueError: While trying to add a new or change an existing toy-value \
pair for the seasonal parameter `seasonalparameter` of element `?`, the \
following error occured: could not broadcast input array from shape (2) \
into shape (3)
    >>> seasonalparameter.toy_1_1_0_0_0 = [1., 2., 3.]
    >>> seasonalparameter
    seasonalparameter(toy_1_1_0_0_0=[1.0, 2.0, 3.0])
    """
    def __init__(self):
        MultiParameter.__init__(self)
        self._toy2values = {}

    def __call__(self, *args, **kwargs):
        """The prefered way to pass values to |Parameter| instances
        within parameter control files.
        """
        self._toy2values.clear()
        if self.NDIM == 1:
            self.shape = (None,)
        try:
            MultiParameter.__call__(self, *args, **kwargs)
            self._toy2values[timetools.TOY()] = self[0]
        except BaseException as exc:
            if kwargs:
                for (toystr, values) in kwargs.items():
                    try:
                        setattr(self, str(timetools.TOY(toystr)), values)
                    except BaseException:
                        objecttools.augment_excmessage(
                            'While trying to define the seasonal parameter '
                            'value `%s` of element `%s` for time of year `%s`'
                            % (self.name,
                               objecttools.devicename(self),
                               toystr))
                self.refresh()
            else:
                raise exc

    def refresh(self):
        """Update the actual simulation values based on the toy-value pairs.

        Usually, one does not need to call refresh explicitly, as it is
        called by methods __call__, __setattr__ and __delattr__ automatically,
        when required.

        Instantiate a 1-dimensional |SeasonalParameter| object:

        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> sp = SeasonalParameter()
        >>> sp.simulationstep = '1d'
        >>> sp.NDIM = 1
        >>> sp.shape = (None,)

        When a |SeasonalParameter| object does not contain any toy-value
        pairs yet, the method |SeasonalParameter.refresh| sets all actual
        simulation values to zero:

        >>> sp.values = 1.
        >>> sp.refresh()
        >>> sp.values[0]
        0.0

        When there is only one toy-value pair, its values are taken for
        all actual simulation values:

        >>> sp.toy_1 = 2. # calls refresh automatically
        >>> sp.values[0]
        2.0

        Method |SeasonalParameter.refresh| performs a linear interpolation
        for the central time points of each simulation time step.  Hence,
        in the following example the original values of the toy-value pairs
        do not show up:

        >>> sp.toy_12_31 = 4.
        >>> from hydpy import round_
        >>> round_(sp.values[0])
        2.00274
        >>> round_(sp.values[-2])
        3.99726
        >>> sp.values[-1]
        3.0

        If one wants to preserve the original values in this example, one
        would have to set the corresponding toy instances in the middle of
        some simulation step intervals:

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
        if not len(self):
            self.values[:] = 0.
        elif len(self) == 1:
            values = list(self._toy2values.values())[0]
            self.values[:] = self.apply_timefactor(values)
        else:
            for idx, date in enumerate(
                    timetools.TOY.centred_timegrid(self.simulationstep)):
                values = self.interp(date)
                self.values[idx] = self.apply_timefactor(values)

    def interp(self, date):
        """Perform a linear value interpolation for a date defined by the
        passed |Date| object and return the result.

        Instantiate a 1-dimensional |SeasonalParameter| object:

        >>> sp = SeasonalParameter()
        >>> from hydpy import Date, Period
        >>> sp.simulationstep = Period('1d')
        >>> sp.NDIM = 1
        >>> sp.shape = (None,)

        Define three toy-value pairs:
        >>> sp(_1=2.0, _2=5.0, _12_31=4.0)

        Passing a |Date| object excatly matching a |TOY| object of course
        simply returns the associated value:

        >>> sp.interp(Date('2000.01.01'))
        2.0
        >>> sp.interp(Date('2000.02.01'))
        5.0
        >>> sp.interp(Date('2000.12.31'))
        4.0

        For all intermediate points, a linear interpolation is performed:

        >>> from hydpy import round_
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
        >>> from hydpy import Date, Period
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
        for idx, (x_1, y_1) in enumerate(xys):
            if x_1 > xnew:
                x_0, y_0 = xys[idx-1]
                break
        else:
            x_0, y_0 = xys[-1]
            x_1, y_1 = xys[0]
        return y_0+(y_1-y_0)/(x_1-x_0)*(xnew-x_0)

    def _setshape(self, shape):
        try:
            shape = (int(shape),)
        except TypeError:
            pass
        shape = list(shape)
        if not self.simulationstep:
            raise RuntimeError(
                'It is not possible the set the shape of the seasonal '
                'parameter `%s` of element `%s` at the moment.  You can '
                'define it manually.  In complete HydPy projects it is '
                'indirectly defined via `pub.timegrids.stepsize` '
                'automatically.'
                % (self.name, objecttools.devicename(self)))
        shape[0] = timetools.Period('366d')/self.simulationstep
        shape[0] = int(numpy.ceil(round(shape[0], 10)))
        MultiParameter._setshape(self, shape)

    shape = property(MultiParameter._getshape, _setshape)

    def __iter__(self):
        for toy in sorted(self._toy2values.keys()):
            yield (toy, self._toy2values[toy])

    def __getattribute__(self, name):
        if name.startswith('toy_'):
            try:
                return self._toy2values[timetools.TOY(name)]
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to get an existing toy-value pair for '
                    'the seasonal parameter `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))
        else:
            return MultiParameter.__getattribute__(self, name)

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
                objecttools.augment_excmessage(
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
                objecttools.augment_excmessage(
                    'While trying to delete an existing toy-value pair for '
                    'the seasonal parameter `%s` of element `%s`'
                    % (self.name, objecttools.devicename(self)))
        else:
            MultiParameter.__delattr__(self, name)

    def __repr__(self):
        if self.NDIM == 1:
            assign = objecttools.assignrepr_value
        elif self.NDIM == 2:
            assign = objecttools.assignrepr_list
        elif self.NDIM == 3:
            assign = objecttools.assignrepr_list2
        else:
            def assign(values, prefix):
                return prefix+str(values)
        if not len(self):
            return self.name+'()'
        lines = []
        blanks = ' '*(len(self.name)+1)
        for idx, (toy, value) in enumerate(self):
            if idx == 0:
                prefix = '%s(%s=' % (self.name, toy)
            else:
                prefix = '%s%s=' % (blanks, toy)
            if self.NDIM == 1:
                lines.append(assign(value, prefix))
            else:
                lines.append(assign(value, prefix, width=79))
        lines[-1] += ')'
        return ',\n'.join(lines)

    def __len__(self):
        return len(self._toy2values)

    def __dir__(self):
        return objecttools.dir_(self) + [str(toy) for (toy, dummy) in self]

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

    When inheriting an actual parameter class from |KeywordParameter2D|
    one needs to define the class attributes |KeywordParameter2D.ROWNAMES|
    and |KeywordParameter2D.COLNAMES| (both of type |tuple|).  One usual
    setting would be that |KeywordParameter2D.ROWNAMES| defines some land
    use classes and |KeywordParameter2D.COLNAMES| defines seasons, months,
    or the like.

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

    |KeywordParameter2D| allows to set the values of all rows via
    keyword arguments:

    >>> iswarm(north=[True, False],
    ...        south=[False, True])
    >>> iswarm
    iswarm(north=[True, False],
           south=[False, True])
    >>> iswarm.values
    array([[ True, False],
           [False,  True]], dtype=bool)

    If a keyword is missing, a |TypeError| is raised:

    >>> iswarm(north=[True, False])
    Traceback (most recent call last):
    ...
    ValueError: When setting parameter `iswarm` of element `?` via row \
related keyword arguments, each string defined in `ROWNAMES` must be used \
as a keyword, but the following keyword is not: `south`.

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
    ValueError: While trying to assign new values to parameter `iswarm` of \
element `?` via the row related attribute `north`, the following error \
occured: cannot copy sequence with size 3 to array axis with dimension 2
    >>> iswarm.apr2sep = True, True, True
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign new values to parameter `iswarm` of \
element `?` via the column related attribute `apr2sep`, the following error \
occured: cannot copy sequence with size 3 to array axis with dimension 2

    >>> iswarm.shape = (1, 1)
    >>> iswarm.south_apr2sep = False
    Traceback (most recent call last):
    ...
    IndexError: While trying to assign new values to parameter `iswarm` of \
element `?` via the row and column related attribute `south_apr2sep`, the \
following error occured: index 1 is out of bounds for axis 0 with size 1
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
                objecttools.augment_excmessage(
                    'While trying to retrieve values from parameter `%s` of '
                    'element `%s` via the row related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self.COLNAMES:
            try:
                return self.values[:, self.COLNAMES.index(key)]
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to retrieve values from parameter `%s` of '
                    'element `%s` via the columnd related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self._ROWCOLMAPPINGS:
            idx, jdx = self._ROWCOLMAPPINGS[key]
            try:
                return self.values[idx, jdx]
            except BaseException:
                objecttools.augment_excmessage(
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
                objecttools.augment_excmessage(
                    'While trying to assign new values to parameter `%s` of '
                    'element `%s` via the row related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self.COLNAMES:
            try:
                self.values[:, self.COLNAMES.index(key)] = values
            except BaseException:
                objecttools.augment_excmessage(
                    'While trying to assign new values to parameter `%s` of '
                    'element `%s` via the column related attribute `%s`'
                    % (self.name, objecttools.devicename(self), key))
        elif key in self._ROWCOLMAPPINGS:
            idx, jdx = self._ROWCOLMAPPINGS[key]
            try:
                self.values[idx, jdx] = values
            except BaseException:
                objecttools.augment_excmessage(
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

    def _getright(self):
        """The "right" value of the actual parameter."""
        return self.values[1]

    def _setright(self, value):
        self.values[1] = value

    right = property(_getright, _setright)


class IndexParameter(MultiParameter):

    def setreference(self, indexarray):
        setattr(self.fastaccess, self.name, indexarray)


class SolverParameter(SingleParameter):

    def __init__(self):
        SingleParameter.__init__(self)
        self._alternative_initvalue = None

    def __call__(self, *args, **kwargs):
        SingleParameter.__call__(self, *args, **kwargs)
        self.alternative_initvalue = self.value

    def update(self):
        try:
            self(self.alternative_initvalue)
        except RuntimeError:
            self(self.modify_init())

    def modify_init(self):
        return self.INIT

    def _get_alternative_initvalue(self):
        if self._alternative_initvalue is None:
            raise RuntimeError(
                'No alternative initial value for solver parameter `%s` of '
                'element `%s` has been defined so far.'
                % (self.name, objecttools.devicename(self)))
        else:
            return self._alternative_initvalue

    def _set_alternative_initvalue(self, value):
        self._alternative_initvalue = value

    def _del_alternative_initvalue(self):
        self._alternative_initvalue = None

    alternative_initvalue = property(_get_alternative_initvalue,
                                     _set_alternative_initvalue,
                                     _del_alternative_initvalue)


autodoctools.autodoc_module()
