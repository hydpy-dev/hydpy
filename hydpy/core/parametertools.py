# -*- coding: utf-8 -*-
"""This module provides tools for defining and handling different kinds
of the parameters of hydrological models."""
# import...
# ...from standard library
import inspect
import textwrap
import time
from typing import *
# ...from site-packages
import numpy
# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import filetools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import variabletools
if TYPE_CHECKING:
    from hydpy.core import auxfiletools
    from hydpy.core import masktools
    from hydpy.core import modeltools
    from hydpy.core import typingtools

# The import of `_strptime` is not thread save.  The following call of
# `strptime` is supposed to prevent possible problems arising from this bug.
time.strptime('1999', '%Y')


def get_controlfileheader(
        model: Union[str, 'modeltools.Model'],
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        simulationstep: Optional[timetools.PeriodConstrArg] = None) -> str:
    """Return the header of a regular or auxiliary parameter control file.

    The header contains the default coding information, the import command
    for the given model and the actual parameter and simulation step sizes.

    The first example shows that, if you pass the model argument as a
    string, you have to take care that this string makes sense:

    >>> from hydpy.core.parametertools import get_controlfileheader, Parameter
    >>> from hydpy import Period, prepare_model, pub, Timegrids, Timegrid
    >>> print(get_controlfileheader(model='no model class',
    ...                             parameterstep='-1h',
    ...                             simulationstep=Period('1h')))
    # -*- coding: utf-8 -*-
    <BLANKLINE>
    from hydpy.models.no model class import *
    <BLANKLINE>
    simulationstep('1h')
    parameterstep('-1h')
    <BLANKLINE>
    <BLANKLINE>

    The second example shows the saver option to pass the proper model
    object.  It also shows that function |get_controlfileheader| tries
    to gain the parameter and simulation step sizes from the global
    |Timegrids| object contained in the module |pub| when necessary:

    >>> model = prepare_model('lland_v1')
    >>> _ = Parameter.parameterstep('1d')
    >>> pub.timegrids = '2000.01.01', '2001.01.01', '1h'
    >>> print(get_controlfileheader(model=model))
    # -*- coding: utf-8 -*-
    <BLANKLINE>
    from hydpy.models.lland_v1 import *
    <BLANKLINE>
    simulationstep('1h')
    parameterstep('1d')
    <BLANKLINE>
    <BLANKLINE>

    .. testsetup::

        >>> del pub.timegrids
    """
    with Parameter.parameterstep(parameterstep):
        if simulationstep is None:
            simulationstep = Parameter.simulationstep
        else:
            simulationstep = timetools.Period(simulationstep)
        return (f"# -*- coding: utf-8 -*-\n\n"
                f"from hydpy.models.{model} import *\n\n"
                f"simulationstep('{simulationstep}')\n"
                f"parameterstep('{Parameter.parameterstep}')\n\n")


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

    def _prepare_docstrings(self, frame):
        """Assign docstrings to the constants handled by |Constants|
        to make them available in the interactive mode of Python."""
        if config.USEAUTODOC:
            filename = inspect.getsourcefile(frame)
            with open(filename) as file_:
                sources = file_.read().split('"""')
            for code, doc in zip(sources[::2], sources[1::2]):
                code = code.strip()
                key = code.split('\n')[-1].split()[0]
                value = self.get(key)
                if value:
                    value.__doc__ = doc


class Parameters:
    """Base class for handling all parameters of a specific model.

    |Parameters| objects handle three parameter subgroups as attributes:
    the `control` subparameters, the `derived` subparameters, and the
    `solver` subparameters:

    >>> from hydpy.models.hstream_v1 import *
    >>> parameterstep('1d')
    >>> bool(model.parameters.control)
    True
    >>> bool(model.parameters.solver)
    False

    Iterations makes only the non-empty subgroups available, which
    are actually handling |Sequence| objects:

    >>> for subpars in model.parameters:
    ...     print(subpars.name)
    control
    derived
    >>> len(model.parameters)
    2
    """

    model: 'modeltools.Model'
    control: 'SubParameters'
    derived: 'SubParameters'
    fixed: 'SubParameters'
    solver: 'SubParameters'

    def __init__(self, kwargs):
        self.model = kwargs.get('model')
        self.control = self._prepare_subpars('control', kwargs)
        self.derived = self._prepare_subpars('derived', kwargs)
        self.fixed = self._prepare_subpars('fixed', kwargs)
        self.solver = self._prepare_subpars('solver', kwargs)

    def _prepare_subpars(self, shortname, kwargs):
        fullname = f'{shortname.capitalize()}Parameters'
        cls = kwargs.get(
            fullname, type(fullname, (SubParameters,), {'CLASSES': ()}))
        return cls(self,
                   getattr(kwargs.get('cythonmodule'), fullname, None),
                   kwargs.get('cymodel'))

    def update(self) -> None:
        """Call method |Parameter.update| of all "secondary" parameters.

        Directly after initialisation, neither the primary (`control`)
        parameters nor the secondary (`derived`)  parameters of
        application model |hstream_v1| are ready for usage:

        >>> from hydpy.models.hstream_v1 import *
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> derived
        nmbsegments(?)
        c1(?)
        c3(?)
        c2(?)

        Trying to update the values of the secondary parameters while the
        primary ones are still not defined, raises errors like the following:

        >>> model.parameters.update()
        Traceback (most recent call last):
        ...
        AttributeError: While trying to update parameter `nmbsegments` \
of element `?`, the following error occurred: For variable `lag`, \
no value has been defined so far.

        With proper values both for parameter |hstream_control.Lag| and
        |hstream_control.Damp|, updating the derived parameters succeeds:

        >>> lag(0.0)
        >>> damp(0.0)
        >>> model.parameters.update()
        >>> derived
        nmbsegments(0)
        c1(0.0)
        c3(0.0)
        c2(1.0)
        """
        for subpars in self.secondary_subpars:
            for par in subpars:
                try:
                    par.update()
                except BaseException:
                    objecttools.augment_excmessage(
                        f'While trying to update parameter '
                        f'{objecttools.elementphrase(par)}')

    def save_controls(
            self, filepath: Optional[str] = None,
            parameterstep: Optional[timetools.PeriodConstrArg] = None,
            simulationstep: Optional[timetools.PeriodConstrArg] = None,
            auxfiler: 'auxfiletools.Auxfiler' = None):
        """Write the control parameters to file.

        Usually, a control file consists of a header (see the documentation
        on the method |get_controlfileheader|) and the string representations
        of the individual |Parameter| objects handled by the `control`
        |SubParameters| object.

        The main functionality of method |Parameters.save_controls| is
        demonstrated in the documentation on the method |HydPy.save_controls|
        of class |HydPy|, which one would apply to write the parameter
        information of complete *HydPy* projects.  However, to call
        |Parameters.save_controls| on individual |Parameters| objects
        offers the advantage to choose an arbitrary file path, as shown
        in the following example:

        >>> from hydpy.models.hstream_v1 import *
        >>> parameterstep('1d')
        >>> simulationstep('1h')
        >>> lag(1.0)
        >>> damp(0.5)

        >>> from hydpy import Open
        >>> with Open():
        ...     model.parameters.save_controls('otherdir/otherfile.py')
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        otherdir/otherfile.py
        -------------------------------------
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1h')
        parameterstep('1d')
        <BLANKLINE>
        lag(1.0)
        damp(0.5)
        <BLANKLINE>
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Without a given file path and a proper project configuration,
        method |Parameters.save_controls| raises the following error:

        >>> model.parameters.save_controls()
        Traceback (most recent call last):
        ...
        RuntimeError: To save the control parameters of a model to a file, \
its filename must be known.  This can be done, by passing a filename to \
function `save_controls` directly.  But in complete HydPy applications, \
it is usally assumed to be consistent with the name of the element \
handling the model.
        """
        variable2auxfile = getattr(auxfiler, str(self.model), None)
        lines = [get_controlfileheader(
            self.model, parameterstep, simulationstep)]
        with Parameter.parameterstep(parameterstep):
            for par in self.control:
                if variable2auxfile:
                    auxfilename = variable2auxfile.get_filename(par)
                    if auxfilename:
                        lines.append(
                            f"{par.name}(auxfile='{auxfilename}')\n")
                        continue
                lines.append(repr(par) + '\n')
        text = ''.join(lines)
        if filepath:
            with open(filepath, mode='w', encoding='utf-8') as controlfile:
                controlfile.write(text)
        else:
            filename = objecttools.devicename(self)
            if filename == '?':
                raise RuntimeError(
                    'To save the control parameters of a model to a file, '
                    'its filename must be known.  This can be done, by '
                    'passing a filename to function `save_controls` '
                    'directly.  But in complete HydPy applications, it is '
                    'usally assumed to be consistent with the name of the '
                    'element handling the model.')
            hydpy.pub.controlmanager.save_file(filename, text)


    def verify(self) -> None:
        """Call method |Variable.verify| of all |Parameter| objects
        handled by the actual model.

        When calling method |Parameters.verify| directly after initialising
        model |hstream_v1| (without using default values), it raises an
        |AttributeError|, due to undefined control parameter values:

        >>> from hydpy.models.hstream_v1 import *
        >>> parameterstep('1d')
        >>> simulationstep('1d')
        >>> model.parameters.verify()
        Traceback (most recent call last):
        ...
        AttributeError: For variable `lag`, no value has been defined so far.

        After defining suitable control parameter values, the derived
        parameters are still not ready:

        >>> model.parameters.control.lag(0.0)
        >>> model.parameters.control.damp(0.0)
        >>> model.parameters.verify()
        Traceback (most recent call last):
        ...
        AttributeError: For variable `nmbsegments`, \
no value has been defined so far.

        After updating the derived parameters, method |Parameters.verify|
        has no reason to complain anymore:

        >>> model.parameters.update()
        >>> model.parameters.verify()
        """
        for subpars in self:
            for par in subpars:
                par.verify()

    @property
    def secondary_subpars(self) -> Iterator['SubParameters']:
        """Iterate through all subgroups of "secondary" parameters.

        These secondary parameter subgroups are the `derived` parameters
        and the `solver` parameters, at the moment:

        >>> from hydpy.models.hstream_v1 import *
        >>> parameterstep('1d')
        >>> for subpars in model.parameters.secondary_subpars:
        ...     print(subpars.name)
        derived
        solver
        """
        for subpars in (self.derived, self.solver):
            yield subpars

    def __iter__(self) -> Iterator['SubParameters']:
        for subpars in (self.control, self.derived, self.fixed, self.solver):
            if subpars:
                yield subpars

    def __len__(self):
        return sum(1 for _ in self)

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy.models.hstream_v1 import *
        >>> parameterstep()
        >>> dir(model.parameters)
        ['control', 'derived', 'fixed', 'model', 'save_controls', \
'secondary_subpars', 'solver', 'update', 'verify']
        """
        return objecttools.dir_(self)


class SubParameters(variabletools.SubVariables[Parameters]):
    """Base class for handling subgroups of model parameters.

    When trying to implement a new model, one has to define its
    specific |Parameter| subclasses. Currently, the HydPy framework
    distinguishes between control parameters, derived parameters,
    and solver parameters. Each |Parameter| subclass is a member
    of a collection class derived from |SubParameters|, called
    "ControlParameters", "DerivedParameters", or "SolverParameters",
    respectively.  Indicate membership by putting the parameter
    subclasses into the |tuple| "CLASSES":

    >>> from hydpy.core.parametertools import Parameter, SubParameters
    >>> class Par2(Parameter):
    ...     'Parameter 2 [-]'
    ...     NDIM = 1
    ...     TYPE = float
    ...     TIME = None
    >>> class Par1(Parameter):
    ...     'Parameter 1 [-]'
    ...     NDIM = 1
    ...     TYPE = float
    ...     TIME = None
    >>> class ControlParameters(SubParameters):
    ...     'Control Parameters'
    ...     CLASSES = (Par2,
    ...                Par1)

    The order within the tuple determines the order of iteration:

    >>> control = ControlParameters(None)
    >>> control
    par2(?)
    par1(?)

    Each |SubParameters| object has a `fastaccess` attribute.  When
    working in pure Python mode, this is an instance of class
    |FastAccessParameter|:

    >>> from hydpy import classname, prepare_model, pub
    >>> with pub.options.usecython(False):
    ...     model = prepare_model('lland_v1')
    >>> classname(model.parameters.control.fastaccess)
    'FastAccessParameter'

    When working in Cython mode (which is the default mode and much
    faster), `fastaccess` is an object of a Cython extension class
    specialised for the respective model and sequence group:

    >>> with pub.options.usecython(True):
    ...     model = prepare_model('lland_v1')
    >>> classname(model.parameters.control.fastaccess)
    'ControlParameters'
    """

    pars: Parameters
    fastaccess: Union[
        'FastAccessParameter', 'typingtools.FastAccessParameterProtocol']
    _cls_fastaccess: Optional[Type[
        'typingtools.FastAccessParameterProtocol']]
    _cymodel: Optional['typingtools.CyModelProtocol']

    def __init__(
            self,
            master: Parameters,
            cls_fastaccess: Optional[Type[
                'typingtools.FastAccessParameterProtocol']] = None,
            cymodel: Optional['typingtools.CyModelProtocol'] = None):
        self.pars = master
        self._cls_fastaccess = cls_fastaccess
        self._cymodel = cymodel
        super().__init__(master)

    def __hydpy__initialise_fastaccess__(self) -> None:
        if (self._cls_fastaccess is None) or (self._cymodel is None):
            self.fastaccess = FastAccessParameter()
        else:
            self.fastaccess = self._cls_fastaccess()
            setattr(self._cymodel.parameters, self.name, self.fastaccess)

    @property
    def name(self) -> str:
        """The class name in lower case letters omitting the last
        ten characters ("parameters").

        >>> from hydpy.core.parametertools import SubParameters
        >>> class ControlParameters(SubParameters):
        ...     CLASSES = ()
        >>> ControlParameters(None).name
        'control'
        """
        return type(self).__name__[:-10].lower()


class _Period(timetools.Period):
    """Extends class |Period| with context manager functionalities.

    To be used by classes |Parameterstep| and |Simulationstep| only.
    """

    def __init__(self, stepsize=None):
        self.stepsize = stepsize
        self.timedelta = stepsize.period
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

    def check(self) -> None:
        """Raise a |RuntimeError|, if no (parameter or simulation)
        step size is defined at the moment.

        For details, see the documentation on class |Parameterstep|.
        """
        if not self:
            raise RuntimeError(self.stepsize.EXC_MESSAGE)

    def delete(self) -> '_Period':
        """Delete the current (parameter or simulation) step size information.

        For details, see the documentation on class |Parameterstep|.
        """
        del self.timedelta
        del self.stepsize.period.timedelta
        return self


class _Stepsize(timetools.Period):
    """Base class of the descriptor classes |Parameterstep| and
    |Simulationstep|."""

    def __init__(self):
        self.period = timetools.Period()

    def __set__(self, obj, value):
        self(value)

    def __delete__(self, obj):
        del self.period.timedelta

    def __call__(self, value: timetools.PeriodConstrArg) -> None:
        try:
            period = timetools.Period(value)
            if period >= '1s':
                self.period = period
            else:
                raise ValueError(
                    'The smallest step size allowed is one second.')
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to (re)define the general {self.name} '
                f'size with { objecttools.value_of_type(value)}')

    @property
    def name(self) -> str:
        """The class name in lower case letters.

        >>> from hydpy.core.parametertools import Parameterstep
        >>> Parameterstep().name
        'parameterstep'
        """
        return type(self).__name__.lower()


class Parameterstep(_Stepsize):
    """The actual parameter time step size.

    Usually, one defines the time step size of the units of
    time-dependent parameters within control files via function
    |parameterstep|, but it can also be changed interactively
    with the help of any |Parameter| object:

    >>> from hydpy.core.parametertools import Parameter
    >>> parameter = Parameter(None)
    >>> parameter.parameterstep = '1d'
    >>> parameter.parameterstep
    Period('1d')

    Note that setting the step size affects all parameters!

    Getting the step size via the |Parameter| subclasses themselves
    also works fine, but use a method call instead of an assignment to
    change the step size to prevent from overwriting the descriptor:

    >>> Parameter.parameterstep
    Period('1d')
    >>> Parameter.parameterstep('2d')
    Period('2d')

    Unreasonable assignments result in error messages like the following:

    >>> parameter.parameterstep = '0d'
    Traceback (most recent call last):
    ...
    ValueError: While trying to (re)define the general parameterstep size \
with value `0d` of type `str`, the following error occurred: The smallest \
step size allowed is one second.

    After deleting the parameter step size, we receive an empty
    |Period| object:

    >>> del parameter.parameterstep
    >>> ps = parameter.parameterstep
    >>> ps
    Period()

    In case you prefer an exception instead of an empty |Period| object,
    call its `check` method:

    >>> ps.check()
    Traceback (most recent call last):
    ...
    RuntimeError: No general parameter step size has been defined.

    Use Pythons `with` statement for temporary step size changes:

    >>> parameter.parameterstep = '1d'
    >>> with parameter.parameterstep('2h'):
    ...     print(repr(parameter.parameterstep))
    Period('2h')
    >>> parameter.parameterstep
    Period('1d')

    Passing |None| means "change nothing in this context" (useful for
    defining functions with optional `parameterstep` arguments):

    >>> with parameter.parameterstep(None):
    ...     print(repr(parameter.parameterstep))
    Period('1d')
    >>> parameter.parameterstep
    Period('1d')

    Use the `with` statement in combination with method `delete` to
    delete the stepsize temporarily:

    >>> with parameter.parameterstep.delete():
    ...     print(repr(parameter.parameterstep))
    Period()
    >>> parameter.parameterstep
    Period('1d')
    """

    EXC_MESSAGE = 'No general parameter step size has been defined.'

    def __get__(self, obj, cls) -> _Period:
        return _Period(self)


class Simulationstep(_Stepsize):
    """The actual (or surrogate) simulation time step size.

    .. testsetup::

        >>> from hydpy.core.parametertools import Parameter
        >>> Parameter.simulationstep.delete()
        Period()

    Usually, the simulation step size is defined globally in module
    |pub| via a |Timegrids| object, or locally via function |simulationstep|
    in separate control files.  However, you can also change it
    interactively with the help of |Parameter| objects.

    Generally, the documentation on class |Parameterstep| also holds
    for class |Simulationstep|.  The following explanations focus on
    the differences only.

    As long as no actual or surrogate simulation time step is defined, an
    empty period object is returned, which can be used to raise the
    following exception:

    >>> from hydpy.core.parametertools import Parameter
    >>> parameter = Parameter(None)
    >>> ps = parameter.simulationstep
    >>> ps
    Period()
    >>> ps.check()
    Traceback (most recent call last):
    ...
    RuntimeError: Neither a global simulation time grid nor a general \
simulation step size to be used as a surrogate for testing purposes has \
been defined.

    For testing or documentation purposes, you can set a surrogate step size:

    >>> parameter.simulationstep = '1d'
    >>> parameter.simulationstep
    Period('1d')

    When working with complete HydPy applications, changing the simulation
    step size would be highly error-prone.  Hence, being defined globally
    within the |pub| module, predefined surrogate values are ignored:

    >>> from hydpy import pub
    >>> pub.timegrids = '2000.01.01', '2001.01.01', '2h'
    >>> parameter.simulationstep
    Period('2h')

    This priority remains unchanged, even when one tries to set a surrogate
    value after the |Timegrid| object has been defined:

    >>> parameter.simulationstep = '5s'
    >>> parameter.simulationstep
    Period('2h')

    One has to delete the |Timegrid| object to make the surrogate simulation
    step size accessible:

    >>> del pub.timegrids
    >>> parameter.simulationstep
    Period('5s')
    """
    EXC_MESSAGE = ('Neither a global simulation time grid nor a general '
                   'simulation step size to be used as a surrogate for '
                   'testing purposes has been defined.')

    def __get__(self, obj, cls) -> _Period:
        period = _Period(self)
        try:
            period.timedelta = hydpy.pub.timegrids.stepsize
        except RuntimeError:
            pass
        return period


class Parameter(variabletools.Variable[SubParameters]):
    """Base class for model parameters.

    In *HydPy*, each kind of model parameter is represented by a unique
    class.  In almost all cases, you should derive such a class,
    directly or indirectly, from class |Parameter|, which provides
    all necessary features that assure the new parameter class works
    well when applied in different contexts.

    In most cases, the functionalities of class |Parameter| are sufficient
    for deriving new classes without doing any real coding (writing
    new or extending existing methods).  However, one sometimes prefers
    to do some extensions to simplify the usage of the parameter class.
    Before doing so on your own, have a look at the specialised
    subclasses already available in module |parametertools|.  One
    example is class |SeasonalParameter|, which allows defining
    parameter values that vary seasonally (e.g. the leaf area index).

    Class |Parameter| itself extends class |Variable|.  Hence, all
    model-specific |Parameter| subclasses must define both a value
    dimensionality and a type via class constants `NDIM` and `TYPE`,
    respectively.  Additionally, one has to define the class constant
    `TIME`, telling how parameter values depend on the simulation
    step size (see methods |Parameter.get_timefactor| and
    |Parameter.apply_timefactor|). Also, model developers might find
    it useful to define initial default values via `INIT` or minimum
    and maximum values via `SPAN`:

    .. testsetup::

        >>> from hydpy.core.parametertools import Parameter
        >>> Parameter.simulationstep.delete()
        Period()
        
    Let us first prepare a new parameter class without time-dependency
    (indicated by assigning |None|) and initialise it:

    >>> from hydpy.core.parametertools import Parameter
    >>> class Par(Parameter):
    ...     NDIM = 0
    ...     TYPE = float
    ...     TIME = None
    ...     SPAN = 0.0, 5.0
    >>> par = Par(None)

    As described in the documentation on base class |Variable|, one
    can directly assign values via property |Variable.value|:

    >>> par.value = 6.0
    >>> par
    par(6.0)

    For |Parameter| objects, there is an alternative way to define
    new values, which should be preferred in most cases (especially
    when writing control files), by "calling" the parameter with
    suitable arguments.  For example, this offers the advantage of
    automatical trimming.  In the example above, the assigned value
    (6.0) violates the upper bound (5.0) of our test parameter.  When
    using the "call" syntax, the wrong value is corrected immediately:

    >>> from hydpy import pub
    >>> with pub.options.warntrim(True):
    ...     par(7.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `7.0` and `5.0`, respectively.
    >>> par
    par(5.0)

    .. testsetup::

        >>> try:
        ...     del model
        ... except NameError:
        ...     pass

    The "call" syntax provides some additional features and related
    error messages.  Use the `auxfile` keyword argument to tell that
    another control file defines the actual parameter value.  Note
    that you cannot use this feature in the interactive mode:

    >>> par(auxfile='test')
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to extract information for parameter `par` \
from file `test`, the following error occurred: Cannot determine the \
corresponding model.  Use the `auxfile` keyword in usual parameter \
control files only.

    Some |Parameter| subclasses support other keyword arguments.
    The standard error message for unsupported arguments is the following:

    >>> par(wrong=1.0)
    Traceback (most recent call last):
    ...
    NotImplementedError: The value(s) of parameter `par` of element `?` \
could not be set based on the given keyword arguments.

    Passing a wrong number of positional arguments results in the
    following error:

    >>> par(1.0, 2.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the value(s) of variable `par`, the \
following error occurred: The given value `[ 1.  2.]` cannot be converted \
to type `float`.

    Passing no argument or both positional and keyword arguments are also
    disallowed:

    >>> par()
    Traceback (most recent call last):
    ...
    ValueError: For parameter `par` of element `?` neither a positional \
nor a keyword argument is given.

    >>> par(1.0, auxfile='test')
    Traceback (most recent call last):
    ...
    ValueError: For parameter `par` of element `?` both positional and \
keyword arguments are given, which is ambiguous.

    Our next |Parameter| test class is a little more complicated, as it
    handles a (1-dimensional) vector of time-dependent values (indicated
    by setting the class attribute `TIME` to |True|):

    >>> class Par(Parameter):
    ...     NDIM = 1
    ...     TYPE = float
    ...     TIME = True
    ...     SPAN = 0.0, None

    We prepare a shape of length 2 and set different simulation and
    parameter step sizes, to see that the required time-related
    adjustments work correctly:

    >>> par = Par(None)
    >>> par.shape = (2,)
    >>> par.parameterstep = '1d'
    >>> par.simulationstep = '2d'

    Now you can pass one single value, an iterable containing two
    values, or two separate values as positional arguments, to set
    both required values.  Note that the given values are assumed to
    agree with the actual parameter step size, and are converted
    internally to agree with the actual simulation step size.  The
    string representation shows values that agree with the parameter
    step size; the |Variable.values| property shows the values that
    agree with the simulation step size, relevant during simulation
    runs.  Also, the string representation shows only one value, in
    case all (relevant) values are identical:

    >>> par(3.0)
    >>> par
    par(3.0)
    >>> par.values
    array([ 6.,  6.])

    >>> par([0.0, 4.0])
    >>> par
    par(0.0, 4.0)
    >>> par.values
    array([ 0.,  8.])

    >>> par(1.0, 2.0)
    >>> par
    par(1.0, 2.0)
    >>> par.values
    array([ 2.,  4.])

    Using the `call` syntax to set parameter values triggers method
    |trim| automatically:

    >>> with pub.options.warntrim(True):
    ...     par(-1.0, 3.0)
    Traceback (most recent call last):
    ...
    UserWarning: For variable `par` at least one value needed to be trimmed.  \
The old and the new value(s) are `-2.0, 6.0` and `0.0, 6.0`, respectively.
    >>> par
    par(0.0, 3.0)
    >>> par.values
    array([ 0.,  6.])

    You are free to change the parameter step size (temporarily) to change
    the string representation of |Parameter| handling time-dependent values
    without a risk to change the actual values relevant for simulation:

    >>> with par.parameterstep('2d'):
    ...     print(par)
    ...     print(repr(par.values))
    par(0.0, 6.0)
    array([ 0.,  6.])
    >>> par
    par(0.0, 3.0)
    >>> par.values
    array([ 0.,  6.])

    The highest number of dimensions of |Parameter| subclasses supported
    is currently two.  The following examples repeat some examples from
    above for a 2-dimensional parameter that handles that values inversely
    related to the simulation step size (indicated by setting the class
    attribute `TIME` to |False|):

    >>> class Par(Parameter):
    ...     NDIM = 2
    ...     TYPE = float
    ...     TIME = False
    ...     SPAN = 0.0, 5.0

    >>> par = Par(None)
    >>> par.shape = (2, 3)

    >>> par(9.0)
    >>> par
    par(9.0)
    >>> par.values
    array([[ 4.5,  4.5,  4.5],
           [ 4.5,  4.5,  4.5]])

    >>> par([[1.0, 2.0, 3.0],
    ...      [4.0, 5.0, 6.0]])
    >>> par
    par([[1.0, 2.0, 3.0],
         [4.0, 5.0, 6.0]])
    >>> par.values
    array([[ 0.5,  1. ,  1.5],
           [ 2. ,  2.5,  3. ]])

    >>> par(1.0, 2.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `par`, \
the following error occurred: While trying to convert the value(s) \
`[ 0.5  1. ]` to a numpy ndarray with shape `(2, 3)` and type `float`, \
the following error occurred: could not broadcast input array from \
shape (2) into shape (2,3)
    """
    TIME: Optional[bool]

    fastaccess: Union[
        'FastAccessParameter',
        'typingtools.FastAccessParameterProtocol']

    parameterstep = Parameterstep()
    simulationstep = Simulationstep()

    def __call__(self, *args, **kwargs):
        if args and kwargs:
            raise ValueError(
                f'For parameter {objecttools.elementphrase(self)} '
                f'both positional and keyword arguments are given, '
                f'which is ambiguous.')
        if not args and not kwargs:
            raise ValueError(
                f'For parameter {objecttools.elementphrase(self)} neither '
                f'a positional nor a keyword argument is given.')
        if 'auxfile' in kwargs:
            values = self._get_values_from_auxiliaryfile(kwargs['auxfile'])
            self.values = self.apply_timefactor(values)
            del kwargs['auxfile']
        elif args:
            if len(args) == 1:
                args = args[0]
            self.values = self.apply_timefactor(numpy.array(args))
        else:
            raise NotImplementedError(
                f'The value(s) of parameter {objecttools.elementphrase(self)} '
                f'could not be set based on the given keyword arguments.')
        self.trim()

    def _get_values_from_auxiliaryfile(self, auxfile):
        """Try to return the parameter values from the auxiliary control file
        with the given name.

        Things are a little complicated here.  To understand this method, you
        should first take a look at the |parameterstep| function.
        """
        try:
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
                raise RuntimeError(
                    'Cannot determine the corresponding model.  Use the '
                    '`auxfile` keyword in usual parameter control files only.')
            filetools.ControlManager.read2dict(auxfile, subnamespace)
            subself = subnamespace[self.name]
            try:
                return subself.__hydpy__get_value__()
            except AttributeError:
                raise RuntimeError(
                    f'The selected auxiliary file does not define '
                    f'value(s) for parameter `{self.name}`.')
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to extract information for parameter '
                f'`{self.name}` from file `{auxfile}`')

    @property
    def subpars(self) -> SubParameters:
        """Alias for attribute `subvars`."""
        return self.subvars

    def __hydpy__connect_variable2subgroup__(self) -> None:
        self.fastaccess = self.subvars.fastaccess
        if self.NDIM:
            setattr(self.fastaccess, self.name, None)
        else:
            initvalue, initflag = self.initinfo
            if initflag:
                setattr(self, 'value', initvalue)
            else:
                setattr(self.fastaccess, self.name, initvalue)

    @property
    def initinfo(self) -> Tuple[Union[float, int, bool], bool]:
        """A |tuple| containing the initial value and |True| or a missing
        value and |False|, depending on the actual |Parameter| subclass and
        the actual value of option |Options.usedefaultvalues|.

        In the following we show how method the effects of property
        |Parameter.initinfo| when initiasing new |Parameter| objects.
        Let's define a parameter test class and prepare a function for
        initialising it and connecting the resulting instance to a
        |SubParameters| object:

        >>> from hydpy.core.parametertools import Parameter, SubParameters
        >>> class Test(Parameter):
        ...     NDIM = 0
        ...     TYPE = float
        ...     TIME = None
        ...     INIT = 2.0
        >>> class SubGroup(SubParameters):
        ...     CLASSES = (Test,)
        >>> def prepare():
        ...     subpars = SubGroup(None)
        ...     test = Test(subpars)
        ...     test.__hydpy__connect_variable2subgroup__()
        ...     return test

        By default, making use of the `INIT` attribute is disabled:

        >>> test = prepare()
        >>> test
        test(?)

        Enable it through setting |Options.usedefaultvalues| to |True|:

        >>> from hydpy import pub
        >>> pub.options.usedefaultvalues = True
        >>> test = prepare()
        >>> test
        test(2.0)

        When no `INIT` attribute is defined (indicated by |None|), enabling
        |Options.usedefaultvalues| has no effect, of course:

        >>> Test.INIT = None
        >>> test = prepare()
        >>> test
        test(?)

        For time-dependent parameter values, the `INIT` attribute is assumed
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
        """
        init = self.INIT
        if (init is not None) and hydpy.pub.options.usedefaultvalues:
            with Parameter.parameterstep('1d'):
                return self.apply_timefactor(init), True
        return variabletools.TYPE2MISSINGVALUE[self.TYPE], False

    @classmethod
    def get_timefactor(cls) -> float:
        """Factor to adjust a new value of a time-dependent parameter.

        For a time-dependent parameter, its effective value depends on the
        simulation step size.  Method |Parameter.get_timefactor| returns
        the fraction between the current simulation step size and the
        current parameter step size.

        .. testsetup::

            >>> from hydpy.core.parametertools import Parameter
            >>> Parameter.simulationstep.delete()
            Period()

        Method |Parameter.get_timefactor| raises the following error
        when time information is not available:

        >>> from hydpy.core.parametertools import Parameter
        >>> Parameter.get_timefactor()
        Traceback (most recent call last):
        ...
        RuntimeError: To calculate the conversion factor for adapting the \
values of the time-dependent parameters, you need to define both a \
parameter and a simulation time step size first.

        One can define both time step sizes directly:

        >>> _ = Parameter.parameterstep('1d')
        >>> _ = Parameter.simulationstep('6h')
        >>> Parameter.get_timefactor()
        0.25

        As usual, the "global" simulation step size of the |Timegrids|
        object of module |pub| is prefered:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '12h'
        >>> Parameter.get_timefactor()
        0.5

        .. testsetup::

            >>> del pub.timegrids
        """
        try:
            parfactor = hydpy.pub.timegrids.parfactor
        except RuntimeError:
            if not (cls.parameterstep and cls.simulationstep):
                raise RuntimeError(
                    'To calculate the conversion factor for adapting '
                    'the values of the time-dependent parameters, '
                    'you need to define both a parameter and a simulation '
                    'time step size first.')
            date1 = timetools.Date('2000.01.01')
            date2 = date1 + cls.simulationstep
            parfactor = timetools.Timegrids(timetools.Timegrid(
                date1, date2, cls.simulationstep)).parfactor
        return parfactor(cls.parameterstep)

    def trim(self, lower=None, upper=None) -> None:
        """Apply function |trim| of module |variabletools|."""
        variabletools.trim(self, lower, upper)

    @classmethod
    def apply_timefactor(cls, values):
        """Change and return the given value(s) in accordance with
        |Parameter.get_timefactor| and the type of time-dependence
        of the actual parameter subclass.

        For the same conversion factor returned by method
        |Parameter.get_timefactor|, method |Parameter.apply_timefactor|
        behaves differently depending on the `TIME` attribute of the
        respective |Parameter| subclass.  We first prepare a parameter
        test class and define both the parameter and simulation step size:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     TIME = None
        >>> Par.parameterstep = '1d'
        >>> Par.simulationstep = '6h'

        |None| means the value(s) of the parameter are not time-dependent
        (e.g. maximum storage capacity).  Hence, |Parameter.apply_timefactor|
        returns the original value(s):

        >>> Par.apply_timefactor(4.0)
        4.0

        |True| means the effective parameter value is proportional to
        the simulation step size (e.g. travel time). Hence,
        |Parameter.apply_timefactor| returns a reduced value in the
        next example (where the simulation step size is smaller than
        the parameter step size):

        >>> Par.TIME = True
        >>> Par.apply_timefactor(4.0)
        1.0

        |False| means the effective parameter value is inversely
        proportional to the simulation step size (e.g. storage
        coefficient). Hence, |Parameter.apply_timefactor| returns
        an increased value in the next example:

        >>> Par.TIME = False
        >>> Par.apply_timefactor(4.0)
        16.0
        """
        if cls.TIME is True:
            return values * cls.get_timefactor()
        if cls.TIME is False:
            return values / cls.get_timefactor()
        return values

    @classmethod
    def revert_timefactor(cls, values):
        """The inverse version of method |Parameter.apply_timefactor|.

        See the explanations on method Parameter.apply_timefactor| to
        understand the following examples:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     TIME = None
        >>> Par.parameterstep = '1d'
        >>> Par.simulationstep = '6h'
        >>> Par.revert_timefactor(4.0)
        4.0

        >>> Par.TIME = True
        >>> Par.revert_timefactor(4.0)
        16.0

        >>> Par.TIME = False
        >>> Par.revert_timefactor(4.0)
        1.0
        """
        if cls.TIME is True:
            return values / cls.get_timefactor()
        if cls.TIME is False:
            return values * cls.get_timefactor()
        return values

    def update(self):
        """To be overridden by all "secondary" parameters.

        |Parameter| subclasses to be used as "primary" parameters (control
        parameters) do not need to implement method |Parameter.update|.
        For such classes, invoking the method results in the following
        error message:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     pass
        >>> Par(None).update()
        Traceback (most recent call last):
        ...
        RuntimeError: Parameter `par` of element `?` does not \
implement method `update`.
        """
        raise RuntimeError(
            f'Parameter {objecttools.elementphrase(self)} does not '
            f'implement method `update`.')

    def compress_repr(self) -> Optional[str]:
        """Try to find a compressed parameter value representation and
        return it.

        |Parameter.compress_repr| raises a |NotImplementedError| when
        failing to find a compressed representation.

        For the following examples, we define a 1-dimensional sequence
        handling time-dependent floating-point values:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Test(Parameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = True
        >>> test = Test(None)

        Before and directly after defining the parameter shape, `nan`
        is returned:

        >>> test.compress_repr()
        '?'
        >>> test
        test(?)
        >>> test.shape = 4
        >>> test
        test(?)

        Due to the time-dependence of the values of our test class,
        we need to specify a parameter and a simulation time step:

        >>> test.parameterstep = '1d'
        >>> test.simulationstep = '8h'

        Compression succeeds when all required values are identical:

        >>> test(3.0, 3.0, 3.0, 3.0)
        >>> test.values
        array([ 1.,  1.,  1.,  1.])
        >>> test.compress_repr()
        '3.0'
        >>> test
        test(3.0)

        Method |Parameter.compress_repr| returns |None| in case the
        required values are not identical:

        >>> test(1.0, 2.0, 3.0, 3.0)
        >>> test.compress_repr()
        >>> test
        test(1.0, 2.0, 3.0, 3.0)

        If some values are not required, indicate this by the `mask`
        descriptor:

        >>> import numpy
        >>> test(3.0, 3.0, 3.0, numpy.nan)
        >>> test
        test(3.0, 3.0, 3.0, nan)
        >>> Test.mask = numpy.array([True, True, True, False])
        >>> test
        test(3.0)

        For a shape of zero, the string representing includes an empty list:

        >>> test.shape = 0
        >>> test.compress_repr()
        '[]'
        >>> test
        test([])

        Method |Parameter.compress_repr| works similarly for different
        |Parameter| subclasses.  The following examples focus on a
        2-dimensional parameter handling integer values:

        >>> from hydpy.core.parametertools import Parameter
        >>> class Test(Parameter):
        ...     NDIM = 2
        ...     TYPE = int
        ...     TIME = None
        >>> test = Test(None)

        >>> test.compress_repr()
        '?'
        >>> test
        test(?)
        >>> test.shape = (2, 3)
        >>> test
        test(?)

        >>> test([[3, 3, 3],
        ...       [3, 3, 3]])
        >>> test
        test(3)

        >>> test([[3, 3, -999999],
        ...       [3, 3, 3]])
        >>> test
        test([[3, 3, -999999],
              [3, 3, 3]])

        >>> Test.mask = numpy.array([
        ...     [True, True, False],
        ...     [True, True, True]])
        >>> test
        test(3)

        >>> test.shape = (0, 0)
        >>> test
        test([[]])
        """
        if not hasattr(self, 'value'):
            return '?'
        if not self:
            return f"{self.NDIM * '['}{self.NDIM * ']'}"
        unique = numpy.unique(self[self.mask])
        if sum(numpy.isnan(unique)) == len(unique.flatten()):
            unique = numpy.array([numpy.nan])
        else:
            unique = self.revert_timefactor(unique)
        if len(unique) == 1:
            return objecttools.repr_(unique[0])
        return None

    def __repr__(self):
        if self.NDIM:
            values = self.compress_repr()
            if values is None:
                values = self.revert_timefactor(self.values)
            islong = (len(self) > 255) if (values is None) else False
            return variabletools.to_repr(self, values, islong)
        lines = self.commentrepr
        if hasattr(self, 'value'):
            value = self.revert_timefactor(self.value)
        else:
            value = '?'
        lines.append(f'{self.name}({objecttools.repr_(value)})')
        return '\n'.join(lines)

    def __dir__(self):
        """
        >>> from hydpy.core.parametertools import Parameter
        >>> class Par(Parameter):
        ...     pass
        >>> dir(Par(None))
        ['INIT', 'NOT_DEEPCOPYABLE_MEMBERS', 'SPAN', 'apply_timefactor', \
'availablemasks', 'average_values', 'commentrepr', 'compress_repr', \
'fastaccess', 'get_submask', 'get_timefactor', 'initinfo', 'mask', 'name', \
'parameterstep', 'refweights', 'revert_timefactor', 'shape', \
'simulationstep', 'strict_valuehandling', 'subpars', 'subvars', 'trim', \
'unit', 'update', 'value', 'values', 'verify']
        """
        return objecttools.dir_(self)


class NameParameter(Parameter):
    """Parameter displaying the names of constants instead of their values.

    For demonstration, we define the test class `LandType`, covering
    three different types of land covering.  For this purpose, we need
    to prepare a dictionary (class attribute `CONSTANTS`), mapping the
    land type names to identity values.  The entries of the `SPAN`
    tuple should agree with the lowest and highest identity values.
    The class attributes `NDIM`, `TYPE`, and `TIME` are already set
    to `1`, `float`, and `None` by base class |NameParameter|:

    >>> from hydpy.core.parametertools import NameParameter
    >>> class LandType(NameParameter):
    ...     SPAN = (1, 3)
    ...     CONSTANTS = {'SOIL':  1, 'WATER': 2, 'GLACIER': 3}

    Additionally, we make the constants available within the local
    namespace (which is usually done by importing the constants
    from the selected application model automatically):

    >>> SOIL, WATER, GLACIER = 1, 2, 3

    For parameters of zero length, unprepared values, and identical
    required values, the string representations of |NameParameter|
    subclasses equal the string representations of other |Parameter|
    subclasses:

    >>> landtype = LandType(None)
    >>> landtype.shape = 0
    >>> landtype
    landtype([])
    >>> landtype.shape = 5
    >>> landtype
    landtype(?)
    >>> landtype(SOIL)
    >>> landtype
    landtype(SOIL)

    For non-identical required values, class |NameParameter| replaces
    the identity values with their names:

    >>> landtype(SOIL, WATER, GLACIER, WATER, SOIL)
    >>> landtype
    landtype(SOIL, WATER, GLACIER, WATER, SOIL)

    For high numbers of entries, the string representation puts the
    names of the constants within a list (to make the string representations
    executable under Python 3.6; this behaviour will change as soon
    as Python 3.7 becomes the oldest supported version):

    >>> landtype.shape = 300
    >>> landtype(SOIL)
    >>> landtype.values[0] = WATER
    >>> landtype.values[-1] = GLACIER
    >>> landtype   # doctest: +ELLIPSIS
    landtype([WATER, SOIL, ..., SOIL, GLACIER])
    """
    NDIM = 1
    TYPE = int
    TIME = None
    CONSTANTS: Dict[str, int]

    def compress_repr(self) -> str:
        """Works as |Parameter.compress_repr|, but returns a
        string with constant names instead of constant values.

        See the main documentation on class |NameParameter| for
        further information.
        """
        string = super().compress_repr()
        if string in ('?', '[]'):
            return string
        if string is None:
            values = self.values
        else:
            values = [int(string)]
        invmap = {value: key for key, value in
                  self.CONSTANTS.items()}
        result = ', '.join(
            invmap.get(value, repr(value)) for value in values)
        if len(self) > 255:
            result = f'[{result}]'
        return result


class ZipParameter(Parameter):
    """Base class for 1-dimensional model parameters that offers an
    additional keyword-based zipping functionality.

    Many models implemented in the *HydPy* framework realise the concept
    of hydrological response units via 1-dimensional |Parameter| objects,
    each entry corresponding with an individual unit.  To allow for a
    maximum of flexibility, one can define their values independently,
    which allows, for example, for applying arbitrary relationships between
    the altitude of individual response units and a precipitation correction
    factor to be parameterised.

    However, very often, hydrological modellers set identical values for
    different hydrological response units of the same type. One could,
    for example, set the same leaf area index for all units of the same
    land-use type.  Class |ZipParameter| allows defining parameters,
    which conveniently support this parameterisation strategy.

    .. testsetup::

        >>> from hydpy.core.parametertools import Parameter
        >>> Parameter.simulationstep.delete()
        Period()

    To see how base class |ZipParameter| works, we need to create some
    additional subclasses.  First, we need a parameter defining the
    type of the individual hydrological response units, which can be
    done by subclassing from |NameParameter|.  We do so by taking
    the example from the documentation of the |NameParameter| class:

    >>> from hydpy.core.parametertools import NameParameter
    >>> SOIL, WATER, GLACIER = 1, 2, 3
    >>> class LandType(NameParameter):
    ...     SPAN = (1, 3)
    ...     CONSTANTS = {'SOIL':  SOIL, 'WATER': WATER, 'GLACIER': GLACIER}
    >>> landtype = LandType(None)

    Second, we need an |IndexMask| subclass.  Our subclass `Land` references
    the respective `LandType` parameter object (we do this in a simplified
    manner, see class |hland_parameters.ParameterComplete| for a "real
    world" example) but is supposed to focus on the response units of
    type `soil` or `glacier` only:


    >>> from hydpy.core.masktools import IndexMask
    >>> class Land(IndexMask):
    ...     RELEVANT_VALUES = (SOIL, GLACIER)
    ...     @staticmethod
    ...     def get_refindices(variable):
    ...         return variable.landtype

    Third, we prepare the actual |ZipParameter| subclass, holding
    the same `constants` dictionary as the `LandType` parameter and
    the `Land` mask as attributes.  We assume that the values of our
    test class `Par` are time-dependent and set different parameter
    and simulation step sizes, to show that the related value
    adjustments work.  Also, we make the `LandType` object available
    via attribute access, which is a hack to make the above
    simplification work:

    >>> from hydpy.core.parametertools import ZipParameter
    >>> class Par(ZipParameter):
    ...     TYPE = float
    ...     TIME = True
    ...     SPAN = (0.0, None)
    ...     MODEL_CONSTANTS = LandType.CONSTANTS
    ...     mask = Land()
    ...     landtype = landtype
    >>> par = Par(None)
    >>> par.parameterstep = '1d'
    >>> par.simulationstep = '12h'

    For parameters with zero-length or with unprepared or identical
    parameter values, the string representation looks as usual:

    >>> landtype.shape = 0
    >>> par.shape = 0
    >>> par
    par([])
    >>> landtype.shape = 5
    >>> landtype(SOIL, WATER, GLACIER, WATER, SOIL)
    >>> par.shape = 5
    >>> par
    par(?)
    >>> par(2.0)
    >>> par
    par(2.0)
    >>> par.values
    array([ 1.,  1.,  1.,  1.,  1.])

    The extended feature of class |ZipParameter| is to allow passing
    values via keywords, each keyword corresponding to one of the
    relevant constants (in our example: `SOIL` and `GLACIER`) in
    lower case letters:

    >>> par(soil=4.0, glacier=6.0)
    >>> par
    par(glacier=6.0, soil=4.0)
    >>> par.values
    array([  2.,  nan,   3.,  nan,   2.])

    Use the `default` argument if you want to assign the same value
    to entries with different constants:

    >>> par(soil=2.0, default=8.0)
    >>> par
    par(glacier=8.0, soil=2.0)
    >>> par.values
    array([  1.,  nan,   4.,  nan,   1.])

    Using a keyword argument corresponding to an existing, but not
    relevant constant (in our example: `WATER`) is silently ignored:

    >>> par(soil=4.0, glacier=6.0, water=8.0)
    >>> par
    par(glacier=6.0, soil=4.0)
    >>> par.values
    array([  2.,  nan,   3.,  nan,   2.])

    However, using a keyword not corresponding to any constant raises
    an exception:

    >>> par(soil=4.0, glacier=6.0, wrong=8.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `par` of \
element `?` based on keyword arguments `soil, glacier, and wrong`, \
the following error occurred: \
Keyword `wrong` is not among the available model constants.

    The same is true when passing incomplete information:

    >>> par(soil=4.0)
    Traceback (most recent call last):
    ...
    TypeError: While trying to set the values of parameter `par` of element \
`?` based on keyword arguments `soil`, the following error occurred: \
The given keywords are incomplete and no default value is available.

    Values exceeding the bounds defined by class attribute `SPAN`
    are trimmed as usual:

    >>> from hydpy import pub
    >>> with pub.options.warntrim(False):
    ...     par(soil=-10.0, glacier=10.0)
    >>> par
    par(glacier=10.0, soil=0.0)
    """
    NDIM = 1
    MODEL_CONSTANTS: Dict[str, int]

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            try:
                self._own_call(kwargs)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to set the values of parameter '
                    f'{objecttools.elementphrase(self)} based on keyword '
                    f'arguments `{objecttools.enumeration(kwargs)}`')

    def _own_call(self, kwargs: Dict[str, Any]) -> None:
        mask = self.mask
        self.values = numpy.nan
        values = self.values
        allidxs = mask.refindices.values
        relidxs = mask.relevantindices
        counter = 0
        if 'default' in kwargs:
            check = False
            values[mask] = kwargs.pop('default')
        else:
            check = True
        for (key, value) in kwargs.items():
            try:
                selidx = self.MODEL_CONSTANTS[key.upper()]
                if selidx in relidxs:
                    values[allidxs == selidx] = value
                    counter += 1
            except KeyError:
                raise TypeError(
                    f'Keyword `{key}` is not among the '
                    f'available model constants.')
        if check and (counter < len(relidxs)):
            raise TypeError(
                'The given keywords are incomplete '
                'and no default value is available.')
        values[:] = self.apply_timefactor(values)
        self.trim()

    def compress_repr(self) -> Optional[str]:
        """Works as |Parameter.compress_repr|, but alternatively
        tries to compress by following an external classification.

        See the main documentation on class |ZipParameter| for
        further information.
        """
        string = super().compress_repr()
        if string is not None:
            return string
        results = []
        mask = self.mask
        refindices = mask.refindices.values
        for (key, value) in self.MODEL_CONSTANTS.items():
            if value in mask.RELEVANT_VALUES:
                unique = numpy.unique(self.values[refindices == value])
                unique = self.revert_timefactor(unique)
                length = len(unique)
                if length == 1:
                    results.append(
                        f'{key.lower()}={objecttools.repr_(unique[0])}')
                elif length > 1:
                    return None
        return ', '.join(sorted(results))


class SeasonalParameter(Parameter):
    """Base class for parameters handling values showing a seasonal variation.

    Quite a lot of model parameter values change on an annual basis.
    One example is the leaf area index.  For deciduous forests within
    temperate climatic regions, it shows a clear peak during the summer
    season.

    If you want to vary the parameter values on a fixed (for example,
    a monthly) basis, |KeywordParameter2D| might be the best starting
    point.  See the |lland_parameters.LanduseMonthParameter| class of
    the |lland| base model as an example, which is used to define
    parameter |lland_control.LAI|, handling monthly leaf area index
    values for different land-use classes.

    However, class |SeasonalParameter| offers more flexibility in
    defining seasonal patterns, which is often helpful for modelling
    technical control systems.  One example is the parameter pair
    |llake_control.W| and |llake_control.Q| of base model |llake|,
    defining the desired water stage to discharge relationship
    throughout the year.

    .. testsetup::

        >>> from hydpy.core.parametertools import Parameter
        >>> Parameter.simulationstep.delete()
        Period()

    For the following examples, we assume a simulation step size of one day:

    >>> from hydpy import pub
    >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'

    Let us prepare an empty 1-dimensional |SeasonalParameter| instance:

    >>> from hydpy.core.parametertools import SeasonalParameter
    >>> class Par(SeasonalParameter):
    ...     NDIM = 1
    ...     TIME = None
    >>> par = Par(None)
    >>> par.NDIM = 1
    >>> par
    par()

    The shape is determined automatically, as described in the
    documentation on property |SeasonalParameter.shape| in more detail:

    >>> par.shape = (None,)
    >>> par.shape
    (366,)

    Pairs of |TOY| objects and |float| values define the seasonal pattern.
    One can assign them all at once via keyword arguments:

    >>> par(_1=2., _7_1=4., _3_1_0_0_0=5.)

    Note that all keywords in the call above are proper |TOY|
    initialisation arguments. Misspelt keywords result in error
    messages like the following:

    >>> Par(None)(_a=1.)
    Traceback (most recent call last):
    ...
    ValueError: While trying to define the seasonal parameter value `par` \
of element `?` for time of year `_a`, the following error occurred: \
While trying to initialise a TOY object based on argument value `_a` \
of type `str`, the following error occurred: While trying to retrieve \
the month, the following error occurred: For TOY (time of year) objects, \
all properties must be of type `int`, but the value `a` of type `str` \
given for property `month` cannot be converted to `int`.

    As the following string representation shows are the pairs of each
    |SeasonalParameter| instance automatically sorted:

    >>> par
    par(toy_1_1_0_0_0=2.0,
        toy_3_1_0_0_0=5.0,
        toy_7_1_0_0_0=4.0)

    By default, `toy` is used as a prefix string.  Using this prefix string,
    one can change the toy-value pairs via attribute access:

    >>> par.toy_1_1_0_0_0
    2.0
    >>> del par.toy_1_1_0_0_0
    >>> par.toy_2_1_0_0_0 = 2.
    >>> par
    par(toy_2_1_0_0_0=2.0,
        toy_3_1_0_0_0=5.0,
        toy_7_1_0_0_0=4.0)

    For attribute access, zero hours, minutes, or seconds can be left out:

    >>> par.toy_2_1
    2.0

    When using functions |getattr| and |delattr|, one can also omit the
    "toy" prefix:

    >>> getattr(par, '2_1')
    2.0
    >>> delattr(par, '2_1')
    >>> getattr(par, '2_1')
    Traceback (most recent call last):
    ...
    AttributeError: Seasonal parameter `par` of element `?` has neither \
a normal attribute nor does it handle a "time of year" named `2_1`.
    >>> delattr(par, '2_1')
    Traceback (most recent call last):
    ...
    AttributeError: Seasonal parameter `par` of element `?` has neither \
a normal attribute nor does it handle a "time of year" named `2_1`.

    Applying the |len| operator on |SeasonalParameter| objects returns
    the number of toy-value pairs.

    >>> len(par)
    2

    New values are checked to be compatible with the predefined shape:

    >>> par.toy_1_1_0_0_0 = [1., 2.]   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: While trying to add a new or change an existing toy-value \
pair for the seasonal parameter `par` of element `?`, the \
following error occurred: float() argument must be a string or a number...
    >>> par = Par(None)
    >>> par.NDIM = 2
    >>> par.shape = (None, 3)
    >>> par.toy_1_1_0_0_0 = [1., 2.]
    Traceback (most recent call last):
    ...
    ValueError: While trying to add a new or change an existing toy-value \
pair for the seasonal parameter `par` of element `?`, the \
following error occurred: could not broadcast input array from shape (2) \
into shape (3)

    If you do not require seasonally varying parameter values in a specific
    situation, you can pass a single positional argument:

    >>> par(5.0)
    >>> par
    par([5.0, 5.0, 5.0])

    Note that class |SeasonalParameter| associates the given value(s) to the
    "first" time of the year, internally:

    >>> par.toys
    (TOY('1_1_0_0_0'),)

    Incompatible positional arguments result in errors like the following:

    >>> par(1.0, 2.0)
    Traceback (most recent call last):
    ...
    ValueError: While trying to set the value(s) of variable `par`, \
the following error occurred: While trying to convert the value(s) \
`[ 1.  2.]` to a numpy ndarray with shape `(366, 3)` and type `float`, \
the following error occurred: could not broadcast input array from \
shape (2) into shape (366,3)

    .. testsetup::

        >>> del pub.timegrids
    """
    TYPE = float

    strict_valuehandling: ClassVar[bool] = False

    def __init__(self, subvars):
        super().__init__(subvars)
        self._toy2values = {}

    def __call__(self, *args, **kwargs) -> None:
        self._toy2values.clear()
        if self.NDIM == 1:
            self.shape = (None,)
        try:
            super().__call__(*args, **kwargs)
            self._toy2values[timetools.TOY()] = self[0]
        except BaseException as exc:
            if args:
                raise exc
            for (toystr, values) in kwargs.items():
                try:
                    setattr(self, str(timetools.TOY(toystr)), values)
                except BaseException:
                    objecttools.augment_excmessage(
                        f'While trying to define the seasonal parameter '
                        f'value {objecttools.elementphrase(self)} for '
                        f'time of year `{toystr}`')
            self.refresh()

    def refresh(self) -> None:
        """Update the actual simulation values based on the toy-value pairs.

        Usually, one does not need to call refresh explicitly.  The
        "magic" methods `__call__`, `__setattr__`, and `__delattr__`
        invoke it automatically, when required.

        Method |SeasonalParameter.refresh| calculates only those time
        variable parameter values required for the defined
        initialisation period.  We start with an initialisation period
        covering a full year, making a complete calculation necessary:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'

        Instantiate a 1-dimensional |SeasonalParameter| object:

        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        >>> par = Par(None)
        >>> par.shape = (None,)

        When a |SeasonalParameter| object does not contain any toy-value
        pairs yet, the method |SeasonalParameter.refresh| sets all actual
        simulation values to zero:

        >>> par.values = 1.
        >>> par.refresh()
        >>> par.values[0]
        0.0

        When there is only one toy-value pair, its values are relevant
        for all actual simulation values:

        >>> par.toy_1 = 2. # calls refresh automatically
        >>> par.values[0]
        2.0

        Method |SeasonalParameter.refresh| performs a linear interpolation
        for the central time points of each simulation time step.  Hence,
        in the following example, the original values of the toy-value
        pairs do not show up:

        >>> par.toy_12_31 = 4.
        >>> from hydpy import round_
        >>> round_(par.values[0])
        2.00274
        >>> round_(par.values[-2])
        3.99726
        >>> par.values[-1]
        3.0

        If one wants to preserve the original values in this example, one
        would have to set the corresponding toy instances in the middle of
        some simulation step intervals:

        >>> del par.toy_1
        >>> del par.toy_12_31
        >>> par.toy_1_1_12 = 2
        >>> par.toy_12_31_12 = 4.
        >>> par.values[0]
        2.0
        >>> round_(par.values[1])
        2.005479
        >>> round_(par.values[-2])
        3.994521
        >>> par.values[-1]
        4.0

        For short initialisation periods, method |SeasonalParameter.refresh|
        performs only the required interpolations for efficiency reasons:

        >>> pub.timegrids = '2000-01-02', '2000-01-05', '1d'
        >>> Par.NDIM = 2
        >>> par = Par(None)
        >>> par.shape = (None, 3)
        >>> par.toy_1_2_12 = 2.0
        >>> par.toy_1_6_12 = 0.0, 2.0, 4.0
        >>> par.values[:6]
        array([[ nan,  nan,  nan],
               [ 2. ,  2. ,  2. ],
               [ 1.5,  2. ,  2.5],
               [ 1. ,  2. ,  3. ],
               [ nan,  nan,  nan],
               [ nan,  nan,  nan]])

        .. testsetup::

            >>> del pub.timegrids
        """
        self._toy2values = {toy: self._toy2values[toy] for toy
                            in sorted(self._toy2values.keys())}
        if not self:
            self.values[:] = 0.
        elif len(self) == 1:
            values = list(self._toy2values.values())[0]
            self.values[:] = self.apply_timefactor(values)
        else:
            centred = timetools.TOY.centred_timegrid()
            values = self.values
            for idx, (date, rel) in enumerate(zip(*centred)):
                values[idx] = self.interp(date) if rel else numpy.nan
            values = self.apply_timefactor(values)
            self.__hydpy__set_value__(values)

    def interp(self, date: timetools.Date) -> float:
        """Perform a linear value interpolation for the given `date` and
        return the result.

        Instantiate a 1-dimensional |SeasonalParameter| object:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'
        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        >>> par = Par(None)
        >>> par.shape = (None,)

        Define three toy-value pairs:

        >>> par(_1=2.0, _2=5.0, _12_31=4.0)

        Passing a |Date| object matching a |TOY| object exactly returns
        the corresponding |float| value:

        >>> from hydpy import Date
        >>> par.interp(Date('2000.01.01'))
        2.0
        >>> par.interp(Date('2000.02.01'))
        5.0
        >>> par.interp(Date('2000.12.31'))
        4.0

        For all intermediate points, |SeasonalParameter.interp| performs
        a linear interpolation:

        >>> from hydpy import round_
        >>> round_(par.interp(Date('2000.01.02')))
        2.096774
        >>> round_(par.interp(Date('2000.01.31')))
        4.903226
        >>> round_(par.interp(Date('2000.02.02')))
        4.997006
        >>> round_(par.interp(Date('2000.12.30')))
        4.002994

        Linear interpolation is also allowed between the first and the
        last pair when they do not capture the endpoints of the year:

        >>> par(_1_2=2.0, _12_30=4.0)
        >>> round_(par.interp(Date('2000.12.29')))
        3.99449
        >>> par.interp(Date('2000.12.30'))
        4.0
        >>> round_(par.interp(Date('2000.12.31')))
        3.333333
        >>> round_(par.interp(Date('2000.01.01')))
        2.666667
        >>> par.interp(Date('2000.01.02'))
        2.0
        >>> round_(par.interp(Date('2000.01.03')))
        2.00551

        The following example briefly shows interpolation performed for
        a 2-dimensional parameter:

        >>> Par.NDIM = 2
        >>> par = Par(None)
        >>> par.shape = (None, 2)
        >>> par(_1_1=[1., 2.], _1_3=[-3, 0.])
        >>> result = par.interp(Date('2000.01.02'))
        >>> round_(result[0])
        -1.0
        >>> round_(result[1])
        1.0

        .. testsetup::

            >>> del pub.timegrids
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
        return y0 + (y1-y0) / (x1 - x0) * (xnew - x0)

    @property
    def toys(self) -> Tuple[timetools.TOY, ...]:
        """A sorted |tuple| of all contained |TOY| objects."""
        return tuple(sorted(self._toy2values.keys()))

    def __hydpy__get_shape__(self) -> Tuple[int, ...]:
        """A tuple containing the actual lengths of all dimensions.

        .. testsetup::

            >>> from hydpy.core.parametertools import Parameter
            >>> Parameter.simulationstep.delete()
            Period()

        Setting the shape of |SeasonalParameter| objects differs from
        setting the shape of other |Variable| subclasses, due to handling
        time on the first axis.  The simulation step size determines the
        length of this axis.  Hence, trying to set the shape before the
        simulation step size is known does not work:

        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TYPE = float
        ...     TIME = None
        >>> par = Par(None)
        >>> par.shape = (None,)
        Traceback (most recent call last):
        ...
        RuntimeError: It is not possible the set the shape of the seasonal \
parameter `par` of element `?` at the moment.  You need to define the \
simulation step size first.  However, in complete HydPy projects this \
stepsize is indirectly defined via `pub.timegrids.stepsize` automatically.

        After preparing the simulation step size, you can pass a tuple
        with a single entry of any value to define the shape of the
        defined 1-dimensional test class.  Property |SeasonalParameter.shape|
        replaces this arbitrary value by the number of simulation
        steps fitting into a leap year:

        >>> par.simulationstep = '1d'
        >>> par.shape = (123,)
        >>> par.shape
        (366,)

        Assigning a single, arbitrary value also works well:

        >>> par.shape = None
        >>> par.shape
        (366,)

        For higher-dimensional parameters, property |SeasonalParameter.shape|
        replaces the first entry of the assigned iterable, accordingly:

        >>> Par.NDIM = 2
        >>> par.shape = (None, 3)
        >>> par.shape
        (366, 3)

        For simulation steps not cleanly fitting into a leap year,
        the ceil-operation determines the number of entries:

        >>> par.simulationstep = '100d'
        >>> par.shape = (None, 3)
        >>> par.shape
        (4, 3)
        """
        return super().__hydpy__get_shape__()

    def __hydpy__set_shape__(self, shape: Union[int, Iterable[int]]):
        if isinstance(shape, Iterable):
            shape_ = list(shape)
        else:
            shape_ = [-1]
        if not self.simulationstep:
            raise RuntimeError(
                f'It is not possible the set the shape of the seasonal '
                f'parameter {objecttools.elementphrase(self)} at the '
                f'moment.  You need to define the simulation step size '
                f'first.  However, in complete HydPy projects this step'
                f'size is indirectly defined via `pub.timegrids.stepsize` '
                f'automatically.')
        shape_[0] = int(numpy.ceil(
            timetools.Period('366d') / self.simulationstep))
        shape_[0] = int(numpy.ceil(round(shape_[0], 10)))
        super().__hydpy__set_shape__(shape_)

    shape = property(fget=__hydpy__get_shape__, fset=__hydpy__set_shape__)

    def __iter__(self) -> Iterator[Tuple[timetools.TOY, Any]]:
        return iter(self._toy2values.items())

    def __getattr__(self, name):
        try:
            return self._toy2values[timetools.TOY(name)]
        except KeyError:
            raise AttributeError(
                f'Seasonal parameter {objecttools.elementphrase(self)} '
                f'has neither a normal attribute nor does it handle a '
                f'"time of year" named `{name}`.')

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
                    f'While trying to add a new or change an existing '
                    f'toy-value pair for the seasonal parameter '
                    f'{objecttools.elementphrase(self)}')
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        try:
            super().__delattr__(name)
        except AttributeError:
            try:
                del self._toy2values[timetools.TOY(name)]
                self.refresh()
            except KeyError:
                raise AttributeError(
                    f'Seasonal parameter {objecttools.elementphrase(self)} '
                    f'has neither a normal attribute nor does it handle a '
                    f'"time of year" named `{name}`.')

    def __repr__(self):

        def assignrepr(value_, prefix_):
            if self.NDIM == 1:
                return objecttools.assignrepr_value(value_, prefix_)
            return objecttools.assignrepr_list(value_, prefix_, width=79)

        if not self:
            return f'{self.name}()'
        if self.NDIM == 1:
            assignrepr = objecttools.assignrepr_value
        else:
            assignrepr = objecttools.assignrepr_list
        toy0 = timetools.TOY0
        if (len(self) == 1) and (toy0 in self._toy2values):
            return f'{assignrepr(self._toy2values[toy0], f"{self.name}(")})'
        lines = []
        blanks = ' '*(len(self.name)+1)
        for idx, (toy, value) in enumerate(self):
            if idx == 0:
                lines.append(assignrepr(value, f'{self.name}({toy}='))
            else:
                lines.append(assignrepr(value, f'{blanks}{toy}='))
        lines[-1] += ')'
        return ',\n'.join(lines)

    def __len__(self):
        return len(self._toy2values)

    def __dir__(self):
        """

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'
        >>> from hydpy.core.parametertools import SeasonalParameter
        >>> class Par(SeasonalParameter):
        ...     NDIM = 1
        ...     TIME = None
        >>> par = Par(None)
        >>> par.NDIM = 1
        >>> par.simulationstep = '1d'
        >>> par.shape = (None,)
        >>> par(_1=2., _7_1=4., _3_1_0_0_0=5.)
        >>> dir(par)   # doctest: +ELLIPSIS
        [... 'subvars', 'toy_1_1_0_0_0', 'toy_3_1_0_0_0', \
'toy_7_1_0_0_0', 'toys', 'trim', ...]

        .. testsetup::

            >>> del pub.timegrids
        """
        return objecttools.dir_(self) + [str(toy) for (toy, dummy) in self]


class KeywordParameter1D(Parameter):
    """Base class for 1-dimensional model parameters with values depending
    on one factor.

    When subclassing from |KeywordParameter1D| one needs to define the
    class attribute `ENTRYNAMES`.  A typical use case is that `ENTRYNAMES`
    defines seasons like the months or, as in our example, half-years:

    >>> from hydpy.core.parametertools import KeywordParameter1D
    >>> class IsHot(KeywordParameter1D):
    ...     TYPE = bool
    ...     TIME = None
    ...     ENTRYNAMES = ('winter', 'summer')

    Usually, |KeywordParameter1D| objects prepare their shape automatically.
    However, to simplify this test case, we define it manually:

    >>> ishot = IsHot(None)
    >>> ishot.shape = 2

    You can pass all parameter values both via positional or keyword arguments:

    >>> ishot(True)
    >>> ishot
    ishot(True)

    >>> ishot(False, True)
    >>> ishot
    ishot(winter=False, summer=True)

    >>> ishot(winter=True, summer=False)
    >>> ishot
    ishot(winter=True, summer=False)
    >>> ishot.values
    array([ True, False], dtype=bool)

    We check the given keyword arguments for correctness and completeness:

    >>> ishot(winter=True)
    Traceback (most recent call last):
    ...
    ValueError: When setting parameter `ishot` of element `?` via keyword \
arguments, each string defined in `ENTRYNAMES` must be used as a keyword, \
but the following keywords are not: `summer`.

    >>> ishot(winter=True, summer=False, spring=True, autumn=False)
    Traceback (most recent call last):
    ...
    ValueError: When setting parameter `ishot` of element `?` via keyword \
arguments, each keyword must be defined in `ENTRYNAMES`, but the following \
keywords are not: `spring and autumn`.

    Class |KeywordParameter1D| implements attribute access, including
    specialised error messages:

    >>> ishot.winter, ishot.summer = ishot.summer, ishot.winter
    >>> ishot
    ishot(winter=False, summer=True)

    >>> ishot.spring
    Traceback (most recent call last):
    ...
    AttributeError: Parameter `ishot` of element `?` does not handle an \
attribute named `spring`.

    >>> ishot.shape = 1
    >>> ishot.summer
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve a value from parameter `ishot` of \
element `?` via the attribute `summer`, the following error occurred: \
index 1 is out of bounds for axis 0 with size 1

    >>> ishot.summer = True
    Traceback (most recent call last):
    ...
    IndexError: While trying to assign a new value to parameter `ishot` of \
element `?` via attribute `summer`, the following error occurred: \
index 1 is out of bounds for axis 0 with size 1
    """
    NDIM = 1
    ENTRYNAMES: ClassVar[Tuple[str, ...]]

    strict_valuehandling: ClassVar[bool] = False

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self.shape = len(self.ENTRYNAMES)

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            for (idx, key) in enumerate(self.ENTRYNAMES):
                try:
                    self.values[idx] = self.apply_timefactor(kwargs[key])
                except KeyError:
                    err = (key for key in self.ENTRYNAMES if key not in kwargs)
                    raise ValueError(
                        f'When setting parameter '
                        f'{objecttools.elementphrase(self)} via keyword '
                        f'arguments, each string defined '
                        f'in `ENTRYNAMES` must be used as a keyword, '
                        f'but the following keywords are not: '
                        f'`{objecttools.enumeration(err)}`.')
            if len(kwargs) != len(self.ENTRYNAMES):
                err = (key for key in kwargs if key not in self.ENTRYNAMES)
                raise ValueError(
                    f'When setting parameter '
                    f'{objecttools.elementphrase(self)} via keyword '
                    f'arguments, each keyword must be defined in '
                    f'`ENTRYNAMES`, but the following keywords are not: '
                    f'`{objecttools.enumeration(err)}`.'
                )

    def __getattr__(self, key):
        if key in self.ENTRYNAMES:
            try:
                return self.values[self.ENTRYNAMES.index(key)]
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to retrieve a value from parameter '
                    f'{objecttools.elementphrase(self)} via the '
                    f'attribute `{key}`')
        raise AttributeError(
            f'Parameter {objecttools.elementphrase(self)} does '
            f'not handle an attribute named `{key}`.')

    def __setattr__(self, key, values):
        if key in self.ENTRYNAMES:
            try:
                self.values[self.ENTRYNAMES.index(key)] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to assign a new value to parameter '
                    f'{objecttools.elementphrase(self)} via attribute `{key}`')
        else:
            super().__setattr__(key, values)

    def __repr__(self):
        lines = self.commentrepr
        values = self.revert_timefactor(self.values)
        prefix = f'{self.name}('
        if len(numpy.unique(values)) == 1:
            lines.append(f'{prefix}{objecttools.repr_(values[0])})')
        else:
            blanks = ' '*len(prefix)
            string = ', '.join(f'{key}={objecttools.repr_(value)}'
                               for key, value in zip(self.ENTRYNAMES, values))
            nmb = max(70-len(prefix), 30)
            for idx, substring in enumerate(textwrap.wrap(string, nmb)):
                if idx:
                    lines.append(f'{blanks}{substring}')
                else:
                    lines.append(f'{prefix}{substring}')
            lines[-1] += ')'
        return '\n'.join(lines)

    def __dir__(self):
        """
        >>> from hydpy.core.parametertools import KeywordParameter1D
        >>> class Season(KeywordParameter1D):
        ...     TYPE = bool
        ...     TIME = None
        ...     ENTRYNAMES = ('winter', 'summer')
        >>> dir(Season(None))   # doctest: +ELLIPSIS
        [...'subvars', 'summer', 'trim', ... 'verify', 'winter']
        """
        return tuple(objecttools.dir_(self)) + self.ENTRYNAMES


class MonthParameter(KeywordParameter1D):
    """Base class for parameters which values depend on the actual month.

    Please see the documentation on class |KeywordParameter1D| on how to
    use |MonthParameter| objects and class |lland_control.WG2Z| of base
    model |lland| as an example implementation:

    >>> from hydpy.models.lland import *
    >>> simulationstep('12h')
    >>> parameterstep('1d')
    >>> wg2z(3.0, 2.0, 1.0, 0.0, -1.0, -2.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0)
    >>> wg2z
    wg2z(jan=3.0, feb=2.0, mar=1.0, apr=0.0, mai=-1.0, jun=-2.0, jul=-3.0,
         aug=-2.0, sep=-1.0, oct=0.0, nov=1.0, dec=2.0)

    Note that attribute access provides access to the "real" values related
    to the current simulation time step:

    >>> wg2z.feb
    2.0
    >>> wg2z.feb = 4.0
    >>> wg2z
    wg2z(jan=3.0, feb=4.0, mar=1.0, apr=0.0, mai=-1.0, jun=-2.0, jul=-3.0,
         aug=-2.0, sep=-1.0, oct=0.0, nov=1.0, dec=2.0)
    """
    ENTRYNAMES = ('jan', 'feb', 'mar', 'apr', 'mai', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec')


class KeywordParameter2D(Parameter):
    """Base class for 2-dimensional model parameters with values depending
    on two factors.

    When subclassing from |KeywordParameter2D| one needs to define the
    class attributes `ROWNAMES` and `COLNAMES` (both of type |tuple|).
    A typical use case is that `ROWNAMES` defines some land-use classes
    and `COLNAMES` defines seasons, months, or the like.  Here, we
    consider a simple corresponding example, where the values of the
    boolean parameter  `IsWarm` both depend on the on the hemisphere
    and the half-year period:

    >>> from hydpy.core.parametertools import KeywordParameter2D
    >>> class IsWarm(KeywordParameter2D):
    ...     TYPE = bool
    ...     TIME = None
    ...     ROWNAMES = ('north', 'south')
    ...     COLNAMES = ('apr2sep', 'oct2mar')

    Instantiate the defined parameter class and define its shape:

    >>> iswarm = IsWarm(None)
    >>> iswarm.shape = (2, 2)

    |KeywordParameter2D| allows us to set the values of all rows via
    keyword arguments:

    >>> iswarm(north=[True, False],
    ...        south=[False, True])
    >>> iswarm
    iswarm(north=[True, False],
           south=[False, True])
    >>> iswarm.values
    array([[ True, False],
           [False,  True]], dtype=bool)

    If a keyword is missing, it raises a |ValueError|:

    >>> iswarm(north=[True, False])
    Traceback (most recent call last):
    ...
    ValueError: While setting parameter `iswarm` of element `?` via row \
related keyword arguments, each string defined in `ROWNAMES` must be used \
as a keyword, but the following keywords are not: `south`.

    One can modify single rows via attribute access:

    >>> iswarm.north = False, False
    >>> iswarm.north
    array([False, False], dtype=bool)

    The same holds for the columns:

    >>> iswarm.apr2sep = True, False
    >>> iswarm.apr2sep
    array([ True, False], dtype=bool)

    Also, combined row-column access is possible:

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
occurred: cannot copy sequence with size 3 to array axis with dimension 2
    >>> iswarm.apr2sep = True, True, True
    Traceback (most recent call last):
    ...
    ValueError: While trying to assign new values to parameter `iswarm` of \
element `?` via the column related attribute `apr2sep`, the following error \
occurred: cannot copy sequence with size 3 to array axis with dimension 2

    >>> iswarm.shape = (1, 1)

    >>> iswarm.south_apr2sep = False
    Traceback (most recent call last):
    ...
    IndexError: While trying to assign new values to parameter `iswarm` of \
element `?` via the row and column related attribute `south_apr2sep`, the \
following error occurred: index 1 is out of bounds for axis 0 with size 1

    >>> iswarm.south
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve values from parameter `iswarm` of \
element `?` via the row related attribute `south`, the following error \
occurred: index 1 is out of bounds for axis 0 with size 1
    >>> iswarm.oct2mar
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve values from parameter `iswarm` of \
element `?` via the column related attribute `oct2mar`, the following error \
occurred: index 1 is out of bounds for axis 1 with size 1
    >>> iswarm.south_oct2mar
    Traceback (most recent call last):
    ...
    IndexError: While trying to retrieve values from parameter `iswarm` of \
element `?` via the row and column related attribute `south_oct2mar`, the \
following error occurred: index 1 is out of bounds for axis 0 with size 1

    >>> iswarm.shape = (2, 2)

    Unknown attribute names result in the following error:

    >>> iswarm.wrong
    Traceback (most recent call last):
    ...
    AttributeError: Parameter `iswarm` of element `?` does neither handle \
a normal attribute nor a row or column related attribute named `wrong`.

    One still can define the parameter values  via positional arguments:

    >>> iswarm(True)
    >>> iswarm
    iswarm(north=[True, True],
           south=[True, True])

    For parameters with many columns, string representations are adequately
    wrapped:

    >>> iswarm.shape = (2, 10)
    >>> iswarm
    iswarm(north=[False, False, False, False, False, False, False, False,
                  False, False],
           south=[False, False, False, False, False, False, False, False,
                  False, False])
    """
    NDIM = 2
    ROWNAMES: ClassVar[Tuple[str, ...]]
    COLNAMES: ClassVar[Tuple[str, ...]]

    strict_valuehandling: ClassVar[bool] = False

    def __init_subclass__(cls):
        super().__init_subclass__()
        rownames = cls.ROWNAMES
        colnames = cls.COLNAMES
        rowcolmappings = {}
        for (idx, rowname) in enumerate(rownames):
            for (jdx, colname) in enumerate(colnames):
                rowcolmappings['_'.join((rowname, colname))] = (idx, jdx)
        cls._ROWCOLMAPPINGS = rowcolmappings

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self.shape = (len(self.ROWNAMES), len(self.COLNAMES))

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            for (idx, key) in enumerate(self.ROWNAMES):
                try:
                    self.values[idx, :] = self.apply_timefactor(kwargs[key])
                except KeyError:
                    miss = [key for key in self.ROWNAMES if key not in kwargs]
                    raise ValueError(
                        f'While setting parameter '
                        f'{objecttools.elementphrase(self)} via row '
                        f'related keyword arguments, each string defined '
                        f'in `ROWNAMES` must be used as a keyword, '
                        f'but the following keywords are not: '
                        f'`{objecttools.enumeration(miss)}`.')

    def __getattr__(self, key):
        if key in self.ROWNAMES:
            try:
                return self.values[self.ROWNAMES.index(key), :]
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to retrieve values from parameter '
                    f'{objecttools.elementphrase(self)} via the row '
                    f'related attribute `{key}`')
        if key in self.COLNAMES:
            try:
                return self.values[:, self.COLNAMES.index(key)]
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to retrieve values from parameter '
                    f'{objecttools.elementphrase(self)} via the column '
                    f'related attribute `{key}`')
        if key in self._ROWCOLMAPPINGS:
            idx, jdx = self._ROWCOLMAPPINGS[key]
            try:
                return self.values[idx, jdx]
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to retrieve values from parameter '
                    f'{objecttools.elementphrase(self)} via the row '
                    f'and column related attribute `{key}`')
        raise AttributeError(
            f'Parameter {objecttools.elementphrase(self)} does neither '
            f'handle a normal attribute nor a row or column related '
            f'attribute named `{key}`.')

    def __setattr__(self, key, values):
        if key in self.ROWNAMES:
            try:
                self.values[self.ROWNAMES.index(key), :] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to assign new values to parameter '
                    f'{objecttools.elementphrase(self)} via the row '
                    f'related attribute `{key}`')
        elif key in self.COLNAMES:
            try:
                self.values[:, self.COLNAMES.index(key)] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to assign new values to parameter '
                    f'{objecttools.elementphrase(self)} via the column '
                    f'related attribute `{key}`')
        elif key in self._ROWCOLMAPPINGS:
            idx, jdx = self._ROWCOLMAPPINGS[key]
            try:
                self.values[idx, jdx] = values
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying to assign new values to parameter '
                    f'{objecttools.elementphrase(self)} via the row '
                    f'and column related attribute `{key}`')
        else:
            super().__setattr__(key, values)

    def __repr__(self):
        lines = self.commentrepr
        values = self.revert_timefactor(self.values)
        prefix = f'{self.name}('
        blanks = ' '*len(prefix)
        for (idx, key) in enumerate(self.ROWNAMES):
            subprefix = f'{prefix}{key}=' if idx == 0 else f'{blanks}{key}='
            lines.append(objecttools.assignrepr_list(
                values[idx, :], subprefix, 75) + ',')
        lines[-1] = lines[-1][:-1] + ')'
        return '\n'.join(lines)

    def __dir__(self):
        """
        >>> from hydpy.core.parametertools import KeywordParameter2D
        >>> class IsWarm(KeywordParameter2D):
        ...     TYPE = bool
        ...     TIME = None
        ...     ROWNAMES = ('north', 'south')
        ...     COLNAMES = ('apr2sep', 'oct2mar')
        >>> dir(IsWarm(None))   # doctest: +ELLIPSIS
        [...'apply_timefactor', 'apr2sep'...'north', 'north_apr2sep', \
'north_oct2mar', 'oct2mar'...'south', 'south_apr2sep', 'south_oct2mar', \
'strict_valuehandling'...]
        """
        return (tuple(objecttools.dir_(self)) + self.ROWNAMES +
                self.COLNAMES + tuple(self._ROWCOLMAPPINGS.keys()))


class RelSubweightsMixin:
    """Mixin class for derived parameters reflecting some absolute
    values of the referenced weighting parameter in relative terms.

    |RelSubweightsMixin| is supposed to be combined with parameters
    implementing property `refweights`.

    The documentation on base model |hland| provides some example
    implementations like class |hland_derived.RelSoilZoneArea|.
    """

    mask: 'masktools.BaseMask'
    refweights: Parameter
    __setitem__: Callable

    def update(self) -> None:
        """Update subclass of |RelSubweightsMixin| based on `refweights`."""
        mask = self.mask
        weights = self.refweights[mask]
        self[~mask] = numpy.nan
        self[mask] = weights/numpy.sum(weights)


class LeftRightParameter(Parameter):
    """Base class for handling two values, a left one and a right one.

    The original purpose of class |LeftRightParameter| is to make the
    handling of river channel related parameters with different values
    for both river banks a little more convenient.

    As an example, we define a parameter class describing the width
    both of the left and the right flood plain of a river segment:

    >>> from hydpy.core.parametertools import LeftRightParameter
    >>> class FloodPlainWidth(LeftRightParameter):
    ...     TYPE = float
    ...     TIME = None
    >>> floodplainwidth = FloodPlainWidth(None)

    Here, we need to set the shape of the parameter to 2, which is an
    automated procedure in full model setups:

    >>> floodplainwidth.shape = 2

    Parameter values can be defined as usual:

    >>> floodplainwidth(3.0)
    >>> floodplainwidth
    floodplainwidth(3.0)

    Alternatively, use the keywords `left` or `l` and `right` or
    `r` to define both values individually:

    >>> floodplainwidth(left=1.0, right=2.0)
    >>> floodplainwidth
    floodplainwidth(left=1.0, right=2.0)
    >>> floodplainwidth(l=2.0, r=1.0)
    >>> floodplainwidth
    floodplainwidth(left=2.0, right=1.0)

    Incomplete information results in the following errors:

    >>> floodplainwidth(left=2.0)
    Traceback (most recent call last):
    ...
    ValueError: When setting the values of parameter `floodplainwidth` of \
element `?` via keyword arguments, either `right` or `r` for the "right" \
parameter value must be given, but is not.
    >>> floodplainwidth(right=1.0)
    Traceback (most recent call last):
    ...
    ValueError: When setting the values of parameter `floodplainwidth` of \
element `?` via keyword arguments, either `left` or `l` for the "left" \
parameter value must be given, but is not.

    Additionally, one can query and modify the individual values via the
    attribute names `left` and `right`:

    >>> floodplainwidth.left
    2.0
    >>> floodplainwidth.left = 3.0
    >>> floodplainwidth.right
    1.0
    >>> floodplainwidth.right = 4.0
    >>> floodplainwidth
    floodplainwidth(left=3.0, right=4.0)
    """
    NDIM = 1
    strict_valuehandling: ClassVar[bool] = False

    def __call__(self, *args, **kwargs) -> None:
        try:
            super().__call__(*args, **kwargs)
        except NotImplementedError:
            left = kwargs.get('left', kwargs.get('l'))
            if left is None:
                raise ValueError(
                    f'When setting the values of parameter '
                    f'{objecttools.elementphrase(self)} via keyword '
                    f'arguments, either `left` or `l` for the "left" '
                    f'parameter value must be given, but is not.')
            self.left = left
            right = kwargs.get('right', kwargs.get('r'))
            if right is None:
                raise ValueError(
                    f'When setting the values of parameter '
                    f'{objecttools.elementphrase(self)} via keyword '
                    f'arguments, either `right` or `r` for the "right" '
                    f'parameter value must be given, but is not.')
            self.right = right

    def __hydpy__connect_variable2subgroup__(self) -> None:
        super().__hydpy__connect_variable2subgroup__()
        self.shape = 2

    @property
    def left(self) -> float:
        """The "left" value of the actual parameter object."""
        return self.values[0]

    @left.setter
    def left(self, value):
        self.values[0] = value

    @property
    def right(self) -> float:
        """The "right" value of the actual parameter object."""
        return self.values[1]

    @right.setter
    def right(self, value):
        self.values[1] = value

    def __repr__(self):
        lines = self.commentrepr
        values = [objecttools.repr_(value) for value in self.values]
        if values[0] == values[1]:
            lines.append(f'{self.name}({values[0]})')
        else:
            lines.append(f'{self.name}(left={values[0]}, right={values[1]})')
        return '\n'.join(lines)


class FixedParameter(Parameter):
    """Base class for defining parameters with fixed values.

    Model model-users usually do not modify the values of |FixedParameter|
    objects.  Hence, such objects prepare their "initial" values automatically
    whenever possible, even when option |Options.usedefaultvalues| is disabled.
    """

    @property
    def initinfo(self) -> Tuple[Union[float, int, bool], bool]:
        """A |tuple| always containing the fixed value and |True|, except
        for time-dependent parameters and incomplete time-information.

        .. testsetup::

            >>> from hydpy.core.parametertools import Parameter
            >>> Parameter.simulationstep.delete()
            Period()

        >>> from hydpy.core.parametertools import FixedParameter
        >>> class Par(FixedParameter):
        ...   NDIM, TYPE, TIME, SPAN = 0, float, True, (0., None)
        ...   INIT = 100.0
        >>> par = Par(None)
        >>> par.initinfo
        (nan, False)
        >>> par.parameterstep = '1d'
        >>> par.simulationstep = '12h'
        >>> par.initinfo
        (50.0, True)
        """
        try:
            with self.parameterstep('1d'):
                return self.apply_timefactor(self.INIT), True
        except (AttributeError, RuntimeError):
            return variabletools.TYPE2MISSINGVALUE[self.TYPE], False

    def restore(self) -> None:
        """Restore the original parameter value.

        Method |FixedParameter.restore| is relevant for testing mainly.
        Note that it might be necessary to call it after changing the
        simulation step size, as shown in the following example using
        the parameter |lland_fixed.LambdaG| of base model |lland|:

        >>> from hydpy.models.lland import *
        >>> simulationstep('1d')
        >>> parameterstep('1d')
        >>> from hydpy import round_
        >>> fixed.lambdag
        lambdag(0.05184)
        >>> round_(fixed.lambdag.value)
        0.05184
        >>> simulationstep('12h')
        >>> fixed.lambdag
        lambdag(0.10368)
        >>> round_(fixed.lambdag.value)
        0.05184
        >>> fixed.lambdag.restore()
        >>> fixed.lambdag
        lambdag(0.05184)
        >>> round_(fixed.lambdag.value)
        0.02592
        """
        with self.parameterstep('1d'):
            self(self.INIT)


class SolverParameter(Parameter):
    """Base class for defining parameters controlling numerical algorithms
    for solving model equations.

    So far, the equation systems of most models implemented into *HydPy*
    are primarily coded as approximative solutions.  However, there are also
    some models stating the original equations only.  One example
    is the |dam| model. Its code consists of the original differential
    equations, which must be solved by a separate algorithm.  Such
    algorithms, like the Runge Kutta schema implemented in class
    |ELSModel|, often come with some degrees of freedom, for example,
    to control the striven numerical accuracy.

    On the one hand, the model developer should know best how to configure
    a numerical algorithm he selects for solving the model equations.  On the
    other hand, there might be situations when the model user has diverging
    preferences.  For example, he might favour higher numerical accuracies
    in one project and faster computation times in another one.  Therefore,
    the |SolverParameter.update| method of class |SolverParameter| relies
    on an `INIT` value defined by the model developer as long as the user
    does not define an alternative value in his control files.

    As an example, we derive the numerical tolerance parameter `Tol`:

    >>> from hydpy.core.parametertools import SolverParameter
    >>> class Tol(SolverParameter):
    ...     NDIM = 0
    ...     TYPE = float
    ...     TIME = None
    ...     SPAN = (0.0, None)
    ...     INIT = 0.1

    Initially, the method |SolverParameter.update| applies the value of the
    class constant `INIT`:

    >>> tol = Tol(None)
    >>> tol.update()
    >>> tol
    tol(0.1)

    One can define an alternative value via "calling" the parameter as usual:

    >>> tol(0.01)
    >>> tol
    tol(0.01)

    Afterwards, |SolverParameter.update| reuses the alternative value
    instead of the value of class constant `INIT`:

    >>> tol.update()
    >>> tol
    tol(0.01)

    This alternative value is accessible and changeable via property
    |SolverParameter.alternative_initvalue|:

    >>> tol.alternative_initvalue
    0.01

    >>> tol.alternative_initvalue = 0.001
    >>> tol.update()
    >>> tol
    tol(0.001)

    One must delete the alternative value to make `INIT` relevant again:

    >>> del tol.alternative_initvalue
    >>> tol.alternative_initvalue
    Traceback (most recent call last):
    ...
    AttributeError: No alternative initial value for solver parameter \
`tol` of element `?` has been defined so far.
    >>> tol.update()
    >>> tol
    tol(0.1)

    Very often, solver parameters depend on other model settings as the
    simulation step size or the catchment size, but `INIT` is always
    constant.  To allow for more flexibility, model developers can
    override the method |SolverParameter.modify_init|, which allows
    adapting the effective parameter value to the actual project settings.

    As a most simple example, we extend our class `Tol` with a
    |SolverParameter.modify_init| method that doubles the original
    `INIT` value:

    >>> class ModTol(Tol):
    ...     def modify_init(self):
    ...         return 2.0 * self.INIT
    >>> modtol = ModTol(None)
    >>> modtol.update()
    >>> modtol
    modtol(0.2)

    Note that |SolverParameter.modify_init| changes the value of `INIT`
    only, not the value of |SolverParameter.alternative_initvalue|:

    >>> modtol.alternative_initvalue = 0.01
    >>> modtol.update()
    >>> modtol
    modtol(0.01)
    """
    INIT: Union[int, float, bool]

    def __init__(self, subvars):
        super().__init__(subvars)
        self._alternative_initvalue = None

    def __call__(self, *args, **kwargs) -> None:
        super().__call__(*args, **kwargs)
        self.alternative_initvalue = self.value

    def update(self) -> None:
        """Update the actual parameter value based on `INIT` or, if
        available, on |SolverParameter.alternative_initvalue|.

        See the main documentation on class |SolverParameter| for more
        information.
        """
        try:
            self(self.alternative_initvalue)
        except AttributeError:
            self(self.modify_init())

    def modify_init(self) -> Union[bool, int, float]:
        """Return the value of class constant `INIT`.

        Override this method to support project-specific solver parameters.
        See the main documentation on class |SolverParameter| for more
        information.
        """
        return self.INIT

    @property
    def alternative_initvalue(self) -> Union[bool, int, float]:
        """A user-defined value to be used instead of the value of class
        constant `INIT`.

        See the main documentation on class |SolverParameter| for more
        information.
        """
        if self._alternative_initvalue is None:
            raise AttributeError(
                f'No alternative initial value for solver parameter '
                f'{objecttools.elementphrase(self)} has been defined so far.')
        return self._alternative_initvalue

    @alternative_initvalue.setter
    def alternative_initvalue(self, value):
        self._alternative_initvalue = value

    @alternative_initvalue.deleter
    def alternative_initvalue(self):
        self._alternative_initvalue = None


class SecondsParameter(Parameter):
    """The length of the actual simulation step size in seconds [s]."""
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0., None)

    def update(self) -> None:
        """Take the number of seconds from the current simulation time step.

        >>> from hydpy.core.parametertools import SecondsParameter
        >>> secondsparameter = SecondsParameter(None)
        >>> secondsparameter.parameterstep = '1d'
        >>> secondsparameter.simulationstep = '12h'
        >>> secondsparameter.update()
        >>> secondsparameter
        secondsparameter(43200.0)
        """
        self.value = self.simulationstep.seconds


class HoursParameter(Parameter):
    """The length of the actual simulation step size in hours [h]."""
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0., None)

    def update(self) -> None:
        """Take the number of hours from the current simulation time step.

        >>> from hydpy.core.parametertools import HoursParameter
        >>> hoursparameter = HoursParameter(None)
        >>> hoursparameter.parameterstep = '1d'
        >>> hoursparameter.simulationstep = '12h'
        >>> hoursparameter.update()
        >>> hoursparameter
        hoursparameter(12.0)
        """
        self.value = self.simulationstep.hours


class DaysParameter(Parameter):
    """The length of the actual simulation step size in days [d]."""
    NDIM = 0
    TYPE = float
    TIME = None
    SPAN = (0., None)

    def update(self) -> None:
        """Take the number of days from the current simulation time step.

        >>> from hydpy.core.parametertools import DaysParameter
        >>> daysparameter = DaysParameter(None)
        >>> daysparameter.parameterstep = '1d'
        >>> daysparameter.simulationstep = '12h'
        >>> daysparameter.update()
        >>> daysparameter
        daysparameter(0.5)
        """
        self.value = self.simulationstep.days


class TOYParameter(Parameter):
    """References the |Indexer.timeofyear| index array provided by the
    instance of class |Indexer| available in module |pub|. [-]."""
    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (0, None)

    def update(self) -> None:
        """Reference the actual |Indexer.timeofyear| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
        >>> from hydpy.core.parametertools import TOYParameter
        >>> toyparameter = TOYParameter(None)
        >>> toyparameter.update()
        >>> toyparameter
        toyparameter(57, 58, 59, 60, 61)

        .. testsetup::

            >>> del pub.timegrids
        """
        # pylint: disable=no-member
        # pylint does not understand descriptors well enough, so far
        indexarray = hydpy.pub.indexer.timeofyear
        self.__hydpy__set_shape__(indexarray.shape)
        self.__hydpy__set_value__(indexarray)


class MOYParameter(Parameter):
    """References the |Indexer.monthofyear| index array provided by the
    instance of class |Indexer| available in module |pub| [-]."""
    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (0, 11)

    def update(self) -> None:
        """Reference the actual |Indexer.monthofyear| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
        >>> from hydpy.core.parametertools import MOYParameter
        >>> moyparameter = MOYParameter(None)
        >>> moyparameter.update()
        >>> moyparameter
        moyparameter(1, 1, 1, 2, 2)

        .. testsetup::

            >>> del pub.timegrids
        """
        # pylint: disable=no-member
        # pylint does not understand descriptors well enough, so far
        indexarray = hydpy.pub.indexer.monthofyear
        self.__hydpy__set_shape__(indexarray.shape)
        self.__hydpy__set_value__(indexarray)


class DOYParameter(Parameter):
    """References the |Indexer.dayofyear| index array provided by the
    instance of class |Indexer| available in module |pub| [-]."""
    NDIM = 1
    TYPE = int
    TIME = None
    SPAN = (0, 365)

    def update(self) -> None:
        """Reference the actual |Indexer.dayofyear| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = '27.02.2004', '3.03.2004', '1d'
        >>> from hydpy.core.parametertools import DOYParameter
        >>> doyparameter = DOYParameter(None)
        >>> doyparameter.update()
        >>> doyparameter
        doyparameter(57, 58, 59, 60, 61)

        .. testsetup::

            >>> del pub.timegrids
        """
        # pylint: disable=no-member
        # pylint does not understand descriptors well enough, so far
        indexarray = hydpy.pub.indexer.dayofyear
        self.__hydpy__set_shape__(indexarray.shape)
        self.__hydpy__set_value__(indexarray)


class SCTParameter(Parameter):
    """References the |Indexer.standardclocktime| array provided by the
    instance of class |Indexer| available in module |pub| [h]."""
    NDIM = 1
    TYPE = float
    TIME = None
    SPAN = (0., 86400.)

    def update(self) -> None:
        """Reference the actual |Indexer.standardclocktime| array of the
        |Indexer| object available in module |pub|.

        >>> from hydpy import pub
        >>> pub.timegrids = '27.02.2004 21:00', '28.02.2004 03:00', '1h'
        >>> from hydpy.core.parametertools import SCTParameter
        >>> sctparameter = SCTParameter(None)
        >>> sctparameter.update()
        >>> sctparameter
        sctparameter(21.5, 22.5, 23.5, 0.5, 1.5, 2.5)

        .. testsetup::

            >>> del pub.timegrids
        """
        # pylint: disable=no-member
        # pylint does not understand descriptors well enough, so far
        array = hydpy.pub.indexer.standardclocktime
        self.__hydpy__set_shape__(array.shape)
        self.__hydpy__set_value__(array)


class UTCLongitudeParameter(Parameter):
    """References the current "UTC longitude" defined by option
    |Options.utclongitude|."""
    NDIM = 0
    TYPE = int
    TIME = None
    SPAN = (-180, 180)

    def update(self):
        """Apply the current value of option |Options.utclongitude|.

        >>> from hydpy import pub
        >>> pub.options.utclongitude
        15
        >>> from hydpy.core.parametertools import UTCLongitudeParameter
        >>> utclongitudeparameter = UTCLongitudeParameter(None)
        >>> utclongitudeparameter.update()
        >>> utclongitudeparameter
        utclongitudeparameter(15)

        Note that changing the value of option |Options.utclongitude|
        might makes re-calling method |UTCLongitudeParameter.update| necessary:

        >>> pub.options.utclongitude = 0
        >>> utclongitudeparameter
        utclongitudeparameter(15)
        >>> utclongitudeparameter.update()
        >>> utclongitudeparameter
        utclongitudeparameter(0)
        """
        self(hydpy.pub.options.utclongitude)


class FastAccessParameter(variabletools.FastAccess):
    """Used as a surrogate for typed Cython classes handling parameters
    when working in pure Python mode."""
