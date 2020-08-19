# -*- coding: utf-8 -*-
"""This module implements features for calibrating model parameters.

.. _`NLopt`: https://nlopt.readthedocs.io/en/latest/
"""

# import...
# ...from standard library
import abc
import types
from typing import *
from typing_extensions import Literal, Protocol
# ...from site-packages
import numpy
# ...from hydpy
import hydpy
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import selectiontools
from hydpy.core import timetools
from hydpy.auxs import iuhtools


RuleArg = Union[Type['Rule'], Literal['Replace', 'Add', 'Multiply']]


class TargetFunction(Protocol):
    # noinspection PyUnresolvedReferences
    """Protocol class for the target function required by class
    |CalibrationInterface|.

    The target functions must calculate and return a floating-point number
    reflecting the quality of the current parameterisation of the models of
    the given |HydPy| object.  Often, as in the following example, the target
    function relies on objective functions as |nse|, applied on the time
    series of the |Sim| and |Obs| sequences handled by the |HydPy| object:

    >>> from hydpy import nse, TargetFunction
    >>> class Target(TargetFunction):
    ...     def __call__(self, hp):
    ...         return sum(nse(node=node) for node in hp.nodes)
    >>> target = Target()

    See the documentation on class |CalibrationInterface| for more information.
    """

    def __call__(
            self,
            hp: hydpytools.HydPy,
    ) -> float:
        """Return some kind of efficience criterion."""


class Adaptor(Protocol):
    """Protocol class for defining adoptors required by some |Rule| objects.

    Often, one calibration parameter (represented by one |Rule| object)
    depends on other calibration parameters (represented by other |Rule|
    objects).  Please select an existing or define an individual adaptor
    and assign it to a |Rule| object to introduce such dependencies.

    See class |SumAdaptor| for a concrete example.
    """

    def __call__(self) -> float:
        """Return the adapted value."""


class SumAdaptor(Adaptor):
    """Adaptor which returns the sum of the values of multiple |Rule| objects.

    Class |SumAdaptor| helps to introduce "larger than" relationships between
    calibration parameters.  A common use-case is the time of concentration
    of different runoff components.  The time of concentration of base flow
    should be larger than the one of direct runoff.  Accordingly, when
    modelling runoff concentration with linear storages, the recession
    coefficient of direct runoff should be larger. Principally, we could
    ensure this during a calibration process by defining two |Rule| objects
    with fixed non-overlapping parameter ranges.  For example, we could
    search for the best direct runoff delay between 1 and 5 days and the
    base flow delay between 5 and 100 days.  We demonstrate this for the
    recession coefficient parameters |hland_control.K| and |hland_control.K4|
    of application model |hland_v1| (assuming the nonlinearity parameter
    |hland_control.Alpha| to be zero):

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import Replace, SumAdaptor
    >>> k = Replace(
    ...     name='k',
    ...     parameter='k',
    ...     value=2.0**-1,
    ...     lower=5.0**-1,
    ...     upper=1.0**-1,
    ...     parameterstep='1d',
    ...     model='hland_v1',
    ... )
    >>> k4 = Replace(
    ...     name='k4',
    ...     parameter='k4',
    ...     value=10.0**-1,
    ...     lower=100.0**-1,
    ...     upper=5.0**-1,
    ...     parameterstep='1d',
    ...     model='hland_v1',
    ... )

    To allow for non-fixed non-overlapping ranges, we can prepare a
    |SumAdaptor| object, knowing both our |Rule| objects:

    >>> sumadaptor = SumAdaptor(k, k4)

    This function object returns the sum of the values of all of its |Rule|
    objects:

    >>> sumadaptor()
    0.6

    We now can assign the |SumAdaptor| object to the direct runoff-related
    |Rule| object and, for example, set its lower boundary to zero:

    >>> k.adaptor = sumadaptor
    >>> k.lower = 0.0

    The |Rule.adaptedvalue| of the |Rule| object, to be used during
    calibration, is now the sum of the (original) values of both rules:

    >>> k.adaptedvalue
    0.6
    """
    _rules: Tuple['Rule', ...]

    def __init__(
            self,
            *rules: 'Rule',
    ):
        self._rules = tuple(rules)

    def __call__(self) -> float:
        return sum(rule.value for rule in self._rules)


class Rule(abc.ABC):
    """Base class for defining calibration rules.

    Each |Rule| object relates one calibration parameter with some
    model parameters.  We select the class |Replace| as a concrete example
    for the following explanations and use the `Lahn` example project,
    which we prepare by calling function |prepare_full_example_2|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    We define a |Rule| object supposed to replace the values of parameter
    |hland_control.FC| of application model |lland_v1|.  Note that argument
    `name` is the name of the rule itself, whereas the argument `parameter`
    is the name of the parameter:

    >>> from hydpy import Replace
    >>> rule = Replace(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=100.0,
    ...     model='hland_v1',
    ... )

    The following string representation shows us the full list of available
    arguments:

    >>> rule
    Replace(
        name='fc',
        parameter='fc',
        lower=-inf,
        upper=inf,
        parameterstep=None,
        value=100.0,
        model='hland_v1',
        selections=('complete',),
    )

    The initial value of parameter |hland_control.FC| is 206 mm:

    >>> fc = hp.elements.land_lahn_1.model.parameters.control.fc
    >>> fc
    fc(206.0)

    We can modify it by calling method |Rule.apply_value|:

    >>> rule.apply_value()
    >>> fc
    fc(100.0)

    You can change and apply the value at any time:

    >>> rule.value = 200.0
    >>> rule.apply_value()
    >>> fc
    fc(200.0)

    Sometimes, one needs to make a difference between the original value
    to be calibrated and the actually applied value.  Then, define an
    |Adaptor| function and assign it to the relevant |Rule| object (see
    the documentation on class |SumAdaptor| for a more realistic example):

    >>> rule.adaptor = lambda: 2.0*rule.value

    Now, our rule does not apply the original but the adapted calibration
    parameter value:

    >>> rule.value
    200.0
    >>> rule.adaptedvalue
    400.0
    >>> rule.apply_value()
    >>> fc
    fc(400.0)

    Use method |Rule.reset_parameters| to restore the original states of the
    affected parameters ("original" here means at the time of initialisation
    of the |Rule| object):

    >>> rule.reset_parameters()
    >>> fc
    fc(206.0)

    The value of parameter |hland_control.FC| is not time-dependent.
    Any |Options.parameterstep| information given to its |Rule| object
    is ignored (note that we pass an example parameter object of
    type |hland_control.FC| instead of the string `fc` this time):

    >>> Replace(
    ...     name='fc',
    ...     parameter=fc,
    ...     value=100.0,
    ...     model='hland_v1',
    ...     parameterstep='1d',
    ... )
    Replace(
        name='fc',
        parameter='fc',
        lower=-inf,
        upper=inf,
        parameterstep=None,
        value=100.0,
        model='hland_v1',
        selections=('complete',),
    )

    For time-dependent parameters, the rule queries the current global
    |Options.parameterstep| value, if you do not specify one explicitly
    (note that we pass the parameter type |hland_control.PercMax| this
    time):

    >>> from hydpy.models.hland.hland_control import PercMax
    >>> rule = Replace(
    ...     name='percmax',
    ...     parameter=PercMax,
    ...     value=5.0,
    ...     model='hland_v1',
    ... )

    To avoid confusion, the |Rule| object actually handles a copy of
    |Options.parameterstep|:

    The |Rule| object internally handles, to avoid confusion, a copy of
    |Options.parameterstep|.

    >>> from hydpy import pub
    >>> pub.options.parameterstep = None
    >>> rule
    Replace(
        name='percmax',
        parameter='percmax',
        lower=-inf,
        upper=inf,
        parameterstep='1d',
        value=5.0,
        model='hland_v1',
        selections=('complete',),
    )
    >>> rule.apply_value()
    >>> percmax = hp.elements.land_lahn_1.model.parameters.control.percmax
    >>> with pub.options.parameterstep('1d'):
    ...     percmax
    percmax(5.0)

    Alternatively, you can pass a parameter step size yourself:

    >>> rule = Replace(
    ...     name='percmax',
    ...     parameter='percmax',
    ...     value=5.0,
    ...     model='hland_v1',
    ...     parameterstep='2d',
    ... )
    >>> rule.apply_value()
    >>> with pub.options.parameterstep('1d'):
    ...     percmax
    percmax(2.5)

    Missing parameter step-size information results in the following error:

    >>> Replace(
    ...     name='percmax',
    ...     parameter='percmax',
    ...     value=5.0,
    ...     model='hland_v1',
    ... )
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to initialise the `Replace` rule object \
`percmax`, the following error occurred: Rules which handle time-dependent \
parameters require information on the parameter timestep size.  Either \
assign it directly or define it via option `parameterstep`.

    With the following definition, the |Rule| object queries all |Element|
    objects handling |hland_v1| instances from the global |Selections|
    object `pub.selections`:

    >>> rule = Replace(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=100.0,
    ...     model='hland_v1',
    ... )
    >>> rule.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")

    Alternatively, you can specify selections by passing themselves or their
    names (the latter requires them to be a member of `pub.selections`):

    >>> rule = Replace(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=100.0,
    ...     selections=[pub.selections.headwaters, 'nonheadwaters'],
    ... )
    >>> rule.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")

    Without using the `model` argument, you must make sure the selected
    elements handle the correct model instance yourself:

    >>> Replace(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=100.0,
    ... )
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to initialise the `Replace` rule object \
`fc`, the following error occurred: Model `hstream_v1` of element \
`stream_dill_lahn_2` does not define a control parameter named `fc`.

    >>> Replace(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=100.0,
    ...     model='hstream_v1',
    ...     selections=[pub.selections.headwaters, 'nonheadwaters'],
    ... )
    Traceback (most recent call last):
    ...
    ValueError: While trying to initialise the `Replace` rule object `fc`, \
the following error occurred: Object `Selections("headwaters", \
"nonheadwaters")` does not handle any `hstream_v1` model instances.
    """

    name: str
    lower: float
    upper: float
    _value: float
    elements: devicetools.Elements
    adaptor: Optional[Adaptor] = None
    _model: Optional[str]
    _parameter: str
    _parameterstep: Optional[timetools.Period]
    _selections: Tuple[str, ...]
    _original_parameter_values: Tuple[Union[float, numpy.ndarray], ...]

    def __init__(
            self,
            *,
            name: str,
            parameter: Union[
                Type[parametertools.Parameter],
                parametertools.Parameter,
                str
            ],
            value: float,
            lower: Optional[float] = -numpy.inf,
            upper: Optional[float] = numpy.inf,
            parameterstep: Optional[timetools.PeriodConstrArg] = None,
            selections: Optional[
                Iterable[Union[selectiontools.Selection, str]]
            ] = None,
            model: Union[types.ModuleType, str] = None,
    ) -> None:
        try:
            self.name = name
            self._parameter = str(getattr(parameter, 'name', parameter))
            self.upper = upper
            self.lower = lower
            self.value = value
            if model is None:
                self._model = model
            else:
                self._model = str(model)
            if selections is None:
                selections = hydpy.pub.selections
                if 'complete' in selections:
                    selections = selectiontools.Selections(selections.complete)
            else:
                selections = selectiontools.Selections(
                    *(
                        sel if isinstance(sel, selectiontools.Selection)
                        else hydpy.pub.selections[sel]
                        for sel in selections
                    )
                )
            self._selections = selections.names
            if self._model is None:
                self.elements = selections.elements
            else:
                self.elements = devicetools.Elements(
                    element for element in selections.elements
                    if str(element.model) == self._model
                )
            if not self.elements:
                raise ValueError(
                    f'Object `{selections}` does not handle '
                    f'any `{self._model}` model instances.'
                )
            for element in self.elements:
                control = element.model.parameters.control
                if not hasattr(control, self._parameter):
                    raise RuntimeError(
                        f'Model {objecttools.elementphrase(element.model)} '
                        f'does not define a control parameter named '
                        f'`{self._parameter}`.'
                    )
            self.parameterstep = parameterstep
            self._original_parameter_values = \
                self._get_original_parameter_values()
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to initialise the `{type(self).__name__}` '
                f'rule object `{name}`'
            )

    def _get_original_parameter_values(
            self,
    ) -> Tuple[Union[float, numpy.ndarray], ...]:
        with hydpy.pub.options.parameterstep(self.parameterstep):
            return tuple(
                par.revert_timefactor(par.value) for par in self
            )

    @property
    def value(self) -> float:
        """The (original) calibration parameter value.

        Property |Rule.value| checks that the given value adheres to the
        defined lower and upper boundaries:

        >>> from hydpy import Replace
        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> rule = Replace(
        ...     name='fc',
        ...     parameter='fc',
        ...     value=100.0,
        ...     lower=50.0,
        ...     upper=200.0,
        ...     model='hland_v1',
        ... )

        >>> rule.value = 0.0
        Traceback (most recent call last):
        ...
        ValueError: The value of `Replace` object `fc` must not be smaller \
than `50.0` or larger than `200.0`, but the given value is `0.0`.

        >>> rule.value = 300.0
        Traceback (most recent call last):
        ...
        ValueError: The value of `Replace` object `fc` must not be smaller \
than `50.0` or larger than `200.0`, but the given value is `300.0`.

        >>> rule.value
        100.0
        """
        return self._value

    @value.setter
    def value(self, value) -> None:
        if self.lower <= value <= self.upper:
            self._value = value
        else:
            raise ValueError(
                f'The value of `{type(self).__name__}` object `{self}` '
                f'must not be smaller than `{objecttools.repr_(self.lower)}` '
                f'or larger than `{objecttools.repr_(self.upper)}`, but the '
                f'given value is `{objecttools.repr_(value)}`.'
            )

    @abc.abstractmethod
    def apply_value(self) -> None:
        """Apply the current (adapted) value on the relevant |Parameter|
        objects.

        To be overridden by the concrete subclasses.
        """

    @property
    def adaptedvalue(self) -> float:
        """The current (original) value modified by relevant the |Adaptor|
        object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import Replace
        >>> fc = Replace(
        ...     name='fc',
        ...     parameter='fc',
        ...     value=100.0,
        ...     model='hland_v1',
        ... )
        >>> fc.adaptor = lambda: 2.0*fc.value
        >>> fc.adaptedvalue
        200.0

        With no available adaptor, |Rule.adaptedvalue| is identical with the
        current original value:

        >>> fc.adaptor = None
        >>> fc.adaptedvalue
        100.0
        """
        if self.adaptor:
            # pylint: disable=not-callable
            # doesn't pylint understand protocols?
            # better use an abstract base class?
            return self.adaptor()
            # pylint: enable=not-callable
        return self.value

    def reset_parameters(self) -> None:
        """Reset all relevant parameter objects to their original states.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import Replace
        >>> rule = Replace(
        ...     name='fc',
        ...     parameter='fc',
        ...     value=100.0,
        ...     model='hland_v1',
        ... )
        >>> fc = hp.elements.land_lahn_1.model.parameters.control.fc
        >>> fc
        fc(206.0)
        >>> fc(100.0)
        >>> fc
        fc(100.0)
        >>> rule.reset_parameters()
        >>> fc
        fc(206.0)
        """
        with hydpy.pub.options.parameterstep(self.parameterstep):
            for parameter, orig in zip(self, self._original_parameter_values):
                parameter(orig)

    @property
    def _time(self) -> Optional[bool]:
        return getattr(
            tuple(self.elements)[0].model.parameters.control,
            self._parameter,
        ).TIME

    @property
    def parameterstep(self) -> Optional[timetools.Period]:
        """The parameter step size relevant to the related model parameter.

        For non-time-dependent parameters, property |Rule.parameterstep|
        is (usually) |None|.
        """
        return self._parameterstep

    @parameterstep.setter
    def parameterstep(self, value: Optional[timetools.PeriodConstrArg]) -> None:
        if self._time is None:
            self._parameterstep = None
        else:
            if value is None:
                value = hydpy.pub.options.parameterstep
                try:
                    value.check()
                except RuntimeError:
                    raise RuntimeError(
                        'Rules which handle time-dependent parameters '
                        'require information on the parameter timestep '
                        'size.  Either assign it directly or define '
                        'it via option `parameterstep`.'
                    ) from None
            self._parameterstep = timetools.Period(value)

    def assignrepr(
            self,
            prefix: str,
            indent: int = 0,
    ) -> str:
        """Return a string representation of the actual |Rule| object
        prefixed with the given string."""

        def _none_or_string(obj) -> str:
            return f"'{obj}'" if obj else str(obj)

        blanks = (indent+4)*' '
        selprefix = f'{blanks}selections='
        selline = objecttools.assignrepr_tuple(
            values=tuple(f"'{sel}'" for sel in self._selections),
            prefix=selprefix,
        )
        return (
            f"{prefix}{type(self).__name__}(\n"
            f"{blanks}name='{self}',\n"
            f"{blanks}parameter='{self._parameter}',\n"
            f"{blanks}lower={objecttools.repr_(self.lower)},\n"
            f"{blanks}upper={objecttools.repr_(self.upper)},\n"
            f"{blanks}parameterstep={_none_or_string(self.parameterstep)},\n"
            f"{blanks}value={objecttools.repr_(self.value)},\n"
            f"{blanks}model={_none_or_string(self._model)},\n"
            f"{selline},\n"
            f"{indent*' '})"
        )

    def __repr__(self) -> str:
        return self.assignrepr(prefix='')

    def __str__(self) -> str:
        return self.name

    def __iter__(self) -> Iterator[parametertools.Parameter]:
        for element in self.elements:
            yield getattr(
                element.model.parameters.control,
                self._parameter,
            )


class Replace(Rule):
    """|Rule| class which simply replaces the current model parameter
    value(s) with the current calibration parameter value.

    See the documentation on class |Rule| for further information.
    """

    def apply_value(self) -> None:
        """Apply the current (adapted) value on the relevant |Parameter|
        objects."""

        with hydpy.pub.options.parameterstep(self.parameterstep):
            for parameter in self:
                parameter(self.adaptedvalue)


class Add(Rule):
    """|Rule| class which adds its calibration delta to the original model
    parameter value(s).

    Please read the examples of the documentation on class |Rule| first.
    Here, we modify some of these examples to show the unique features
    of class |Add|.

    The first example deals with the non-time-dependent parameter
    |hland_control.FC|.  The following |Add| object adds its current
    (adapted) value to the original value of the parameter:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import Add
    >>> rule = Add(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=100.0,
    ...     model='hland_v1',
    ... )
    >>> rule.adaptor = lambda: 2.0*rule.value
    >>> fc = hp.elements.land_lahn_1.model.parameters.control.fc
    >>> fc
    fc(206.0)
    >>> rule.apply_value()
    >>> fc
    fc(406.0)

    The second example deals with the time-dependent parameter
    |hland_control.PercMax| and shows that everything works even for
    situations where the actual |Options.parameterstep| (2 days) differs
    from the current |Options.simulationstep| (1 day):


    >>> rule = Add(
    ...     name='percmax',
    ...     parameter='percmax',
    ...     value=5.0,
    ...     model='hland_v1',
    ...     parameterstep='2d',
    ... )
    >>> percmax = hp.elements.land_lahn_1.model.parameters.control.percmax
    >>> percmax
    percmax(1.02978)
    >>> rule.apply_value()
    >>> percmax
    percmax(3.52978)
    """

    def apply_value(self) -> None:
        """Apply the current (adapted) value on the relevant |Parameter|
        objects."""
        with hydpy.pub.options.parameterstep(self.parameterstep):
            for parameter, orig in zip(self, self._original_parameter_values):
                parameter(self.adaptedvalue+orig)


class Multiply(Rule):
    """|Rule| class which multiplies the original model parameter value(s)
    by its calibration factor.

    Please read the examples of the documentation on class |Rule| first.
    Here, we modify some of these examples to show the unique features
    of class |Multiply|.

    The first example deals with the non-time-dependent parameter
    |hland_control.FC|.  The following |Multiply| object multiplies the
    original value of the parameter by its current (adapted) calibration
    factor:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import Add
    >>> rule = Multiply(
    ...     name='fc',
    ...     parameter='fc',
    ...     value=2.0,
    ...     model='hland_v1',
    ... )
    >>> rule.adaptor = lambda: 2.0*rule.value
    >>> fc = hp.elements.land_lahn_1.model.parameters.control.fc
    >>> fc
    fc(206.0)
    >>> rule.apply_value()
    >>> fc
    fc(824.0)

    The second example deals with the time-dependent parameter
    |hland_control.PercMax| and shows that everything works even for
    situations where the actual |Options.parameterstep| (2 days) differs
    from the current |Options.simulationstep| (1 day):

    >>> rule = Multiply(
    ...     name='percmax',
    ...     parameter='percmax',
    ...     value=2.0,
    ...     model='hland_v1',
    ...     parameterstep='2d',
    ... )
    >>> percmax = hp.elements.land_lahn_1.model.parameters.control.percmax
    >>> percmax
    percmax(1.02978)
    >>> rule.apply_value()
    >>> percmax
    percmax(2.05956)
    """
    def apply_value(self) -> None:
        """Apply the current (adapted) value on the relevant |Parameter|
        objects."""
        with hydpy.pub.options.parameterstep(self.parameterstep):
            for parameter, orig in zip(self, self._original_parameter_values):
                parameter(self.adaptedvalue*orig)


class CalibrationInterface:
    # noinspection PyUnresolvedReferences
    """Interface for the coupling of *HydPy* to optimisation libraries like
    `NLopt`_.

    Essentially, class |CalibrationInterface| is supposed for the structured
    handling of multiple objects of the different |Rule| subclasses.  Hence,
    please read the documentation on class |Rule| before continuing, on
    which we base the following explanations.

    We work with the `Lahn` example project again:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    First, we create a |CalibrationInterface| object.  Initially, it needs
    to know the relevant |HydPy| object and the target or objective function
    (here, we define the target function sloppily via the `lambda` statement;
    see the documentation on the protocol class |TargetFunction| for a more
    formal definition and further explanations):

    >>> from hydpy import CalibrationInterface, nse
    >>> ci = CalibrationInterface(
    ...     hp=hp,
    ...     targetfunction=lambda hp_: sum(nse(node=node) for node in hp_.nodes)
    ... )

    Next, we use method |CalibrationInterface.make_rules|, which generates
    one |Replace| rule related to parameter |hland_control.FC| and another
    one related to parameter |hland_control.PercMax| in one step:

    >>> ci.make_rules(
    ...     rule='Replace',
    ...     names=['fc', 'percmax'],
    ...     parameters=['fc', 'percmax'],
    ...     values=[100.0, 5.0],
    ...     lowers=[50.0, 1.0],
    ...     uppers=[200.0, 10.0],
    ...     parameterstep='1d',
    ...     model='hland_v1',
    ... )

    >>> print(ci)
    CalibrationInterface
    >>> ci
    Replace(
        name='fc',
        parameter='fc',
        lower=50.0,
        upper=200.0,
        parameterstep=None,
        value=100.0,
        model='hland_v1',
        selections=('complete',),
    )
    Replace(
        name='percmax',
        parameter='percmax',
        lower=1.0,
        upper=10.0,
        parameterstep='1d',
        value=5.0,
        model='hland_v1',
        selections=('complete',),
    )

    You can also add existing rules via method |CalibrationInterface.add_rules|.
    We add one for calibrating parameter |hstream_control.Damp| of application
    model |hstream_v1|:

    >>> len(ci)
    2
    >>> from hydpy import Replace
    >>> ci.add_rules(
    ...     Replace(
    ...         name='damp',
    ...         parameter='damp',
    ...         value=0.2,
    ...         lower=0.0,
    ...         upper=0.5,
    ...         selections=['complete'],
    ...         model='hstream_v1',
    ...     )
    ... )
    >>> len(ci)
    3

    All rules are available via attribute and keyword access:

    >>> ci.fc
    Replace(
        name='fc',
        parameter='fc',
        lower=50.0,
        upper=200.0,
        parameterstep=None,
        value=100.0,
        model='hland_v1',
        selections=('complete',),
    )

    >>> ci.FC
    Traceback (most recent call last):
    ...
    AttributeError: The actual calibration interface does neither \
handle a normal attribute nor a rule object named `FC`.

    >>> ci['damp']
    Replace(
        name='damp',
        parameter='damp',
        lower=0.0,
        upper=0.5,
        parameterstep=None,
        value=0.2,
        model='hstream_v1',
        selections=('complete',),
    )

    >>> ci['Damp']
    Traceback (most recent call last):
    ...
    KeyError: 'The actual calibration interface does not handle a \
rule object named `Damp`.'

    The following properties return consistently sorted information on
    the handles |Rule| objects:

    >>> ci.names
    ('fc', 'percmax', 'damp')
    >>> ci.values
    (100.0, 5.0, 0.2)
    >>> ci.lowers
    (50.0, 1.0, 0.0)
    >>> ci.uppers
    (200.0, 10.0, 0.5)

    All tuples reflect the current state of all rules:

    >>> ci.damp.value = 0.3
    >>> ci.values
    (100.0, 5.0, 0.3)

    For the following examples, we perform a simulation run and assign
    the values of the simulated time-series to the observed series:

    >>> conditions = hp.conditions
    >>> hp.simulate()
    >>> for node in hp.nodes:
    ...     node.sequences.obs.series = node.sequences.sim.series
    >>> hp.conditions = conditions

    As the agreement between the simulated and the "observed" time-series is
    perfect all four gauges, method |CalibrationInterface.calculate_likelihood|
    returns the highest possible sum of four |nse| values and also stores it
    under the attribute `result`:

    >>> from hydpy import round_
    >>> round_(ci.calculate_likelihood())
    4.0
    >>> round_(ci.result)
    4.0

    When performing a manual calibration, it might be convenient to use
    method |CalibrationInterface.apply_values|.  To explain how it works,
    we first show the values of the relevant parameters of some randomly
    selected model instances:

    >>> stream = hp.elements.stream_lahn_1_lahn_2.model
    >>> stream.parameters.control
    lag(0.583)
    damp(0.0)
    >>> stream.parameters.derived
    nmbsegments(1)
    c1(0.0)
    c3(0.0)
    c2(1.0)
    >>> land = hp.elements.land_lahn_1.model
    >>> land.parameters.control.fc
    fc(206.0)
    >>> land.parameters.control.percmax
    percmax(1.02978)

    Method |CalibrationInterface.apply_values| of class |CalibrationInterface|
    calls the method |Rule.apply_value| of all handled |Rule| objects,
    performs some preparations (for example, it derives the values of the
    secondary parameters (see parameter |hstream_derived.NmbSegments|),
    executes a simulation run, calls method
    |CalibrationInterface.calculate_likelihood|, and returns the result:

    >>> result = ci.apply_values()
    >>> stream.parameters.control
    lag(0.583)
    damp(0.3)
    >>> stream.parameters.derived
    nmbsegments(1)
    c1(0.230769)
    c3(0.230769)
    c2(0.538462)

    >>> land.parameters.control.fc
    fc(100.0)
    >>> land.parameters.control.percmax
    percmax(5.0)

    Due to the changes in our parameter values, our simulation is not
    "perfect" anymore:

    >>> round_(ci.result)
    1.605136

    Use method |CalibrationInterface.reset_parameters| to restore the initial
    states of all affected parameters:

    >>> ci.reset_parameters()
    >>> stream.parameters.control
    lag(0.583)
    damp(0.0)
    >>> stream.parameters.derived
    nmbsegments(1)
    c1(0.0)
    c3(0.0)
    c2(1.0)
    >>> land = hp.elements.land_lahn_1.model
    >>> land.parameters.control.fc
    fc(206.0)
    >>> land.parameters.control.percmax
    percmax(1.02978)

    Now we get the same "perfect" efficiency again:

    >>> hp.simulate()
    >>> round_(ci.calculate_likelihood())
    4.0
    >>> hp.conditions = conditions

    Optimisers, like those implemented in `NLopt`_, often provide their new
    parameter estimates via vectors.  Method
    |CalibrationInterface.perform_calibrationstep| accepts such vectors and
    updates the handled |Rule| objects accordingly.  After that, it performs
    the same steps as described for method |CalibrationInterface.apply_values|:

    >>> round_(ci.perform_calibrationstep([100.0, 5.0, 0.3]))
    1.605136

    >>> stream.parameters.control
    lag(0.583)
    damp(0.3)
    >>> stream.parameters.derived
    nmbsegments(1)
    c1(0.230769)
    c3(0.230769)
    c2(0.538462)

    >>> land.parameters.control.fc
    fc(100.0)
    >>> land.parameters.control.percmax
    percmax(5.0)

    Method |CalibrationInterface.perform_calibrationstep| writes intermediate
    results into a log file, if available.  Prepares it beforehand via method
    |CalibrationInterface.prepare_logfile|:

    >>> with TestIO():
    ...     ci.prepare_logfile(logfilepath='example_calibration.log',
    ...                        objectivefunction='NSE',
    ...                        documentation='Just a doctest example.')

    To continue "manually", we now can call method
    |CalibrationInterface.update_logfile| to write the lastly calculated
    efficiency and the corresponding calibration parameter values to the
    log file:

    >>> with TestIO():   # doctest: +NORMALIZE_WHITESPACE
    ...     ci.update_logfile()
    ...     print(open('example_calibration.log').read())
    # Just a doctest example.
    <BLANKLINE>
    NSE           fc    percmax damp
    parameterstep None	1d      None
    1.605136      100.0 5.0     0.3
    <BLANKLINE>

    For automatic calibration, one needs a calibration algorithm like the
    following, which simply checks the lower and upper boundaries as well
    as the initial values of all |Rule| objects:

    >>> def find_max(function, lowers, uppers, inits):
    ...     best_result = -999.0
    ...     best_parameters = None
    ...     for values in (lowers, uppers, inits):
    ...         result = function(values)
    ...         if result > best_result:
    ...             best_result = result
    ...             best_parameters = values
    ...     return best_parameters

    Now we can assign method |CalibrationInterface.perform_calibrationstep|
    to this oversimplified optimiser, which then returns the best examined
    calibration parameter values:

    >>> with TestIO():
    ...     find_max(function=ci.perform_calibrationstep,
    ...              lowers=ci.lowers,
    ...              uppers=ci.uppers,
    ...              inits=ci.values)
    (200.0, 10.0, 0.5)

    The log file now contains one line for our old result and three lines
    for the results of our optimiser:

    >>> with TestIO():   # doctest: +NORMALIZE_WHITESPACE
    ...     print(open('example_calibration.log').read())
    # Just a doctest example.
    <BLANKLINE>
    NSE           fc    percmax damp
    parameterstep None  1d      None
    1.605136      100.0 5.0     0.3
    -0.710211     50.0  1.0     0.0
    2.313934      200.0 10.0    0.5
    1.605136      100.0 5.0     0.3
    <BLANKLINE>

    Class |CalibrationInterface| also provides method
    |CalibrationInterface.read_logfile|, which automatically selects the
    best calibration result.  Therefore, it needs to know that the highest
    result is the best, which we indicate by setting argument `maximisation`
    to |True|:

    >>> with TestIO():
    ...     ci.read_logfile(
    ...         logfilepath='example_calibration.log',
    ...         maximisation=True,
    ...     )
    >>> ci.fc.value
    200.0
    >>> ci.percmax.value
    10.0
    >>> ci.damp.value
    0.5
    >>> round_(ci.result)
    2.313934
    >>> round_(ci.apply_values())
    2.313934

    On the contrary, if we set argument `maximisation` to |False|, method
    |CalibrationInterface.read_logfile| returns the worst result in our
    example:

    >>> with TestIO():
    ...     ci.read_logfile(
    ...         logfilepath='example_calibration.log',
    ...         maximisation=False,
    ...     )
    >>> ci.fc.value
    50.0
    >>> ci.percmax.value
    1.0
    >>> ci.damp.value
    0.0
    >>> round_(ci.result)
    -0.710211
    >>> round_(ci.apply_values())
    -0.710211

    To prevent errors due to different parameter step-sizes, method
    |CalibrationInterface.read_logfile| raises the following error whenever
    it detects inconsistencies:

    >>> ci.percmax.parameterstep = '2d'
    >>> with TestIO():
    ...     ci.read_logfile(
    ...         logfilepath='example_calibration.log',
    ...         maximisation=True,
    ...     )
    Traceback (most recent call last):
    ...
    RuntimeError: The current parameterstep of the `Replace` rule \
`percmax` (`2d`) does not agree with the one documentated in log file \
`example_calibration.log` (`1d`).

    Method |CalibrationInterface.read_logfile| reports inconsistent rule
    names as follows:

    >>> ci.remove_rules(ci.percmax)
    >>> with TestIO():
    ...     ci.read_logfile(
    ...         logfilepath='example_calibration.log',
    ...         maximisation=True,
    ...     )
    Traceback (most recent call last):
    ...
    RuntimeError: The names of the rules handled by the actual calibration \
interface (damp and fc) do not agree with the names in the header of logfile \
`example_calibration.log` (damp, fc, and percmax).
    """

    result: Optional[float]
    conditions: hydpytools.ConditionsType
    _logfilepath: Optional[str]
    _hp: hydpytools.HydPy
    _targetfunction: TargetFunction
    _rules: Dict[str, Rule]
    _elements: devicetools.Elements

    def __init__(
            self,
            hp: hydpytools.HydPy,
            targetfunction: TargetFunction,
    ):
        self._hp = hp
        self._targetfunction = targetfunction
        self.conditions = hp.conditions
        self._rules = {}
        self._elements = devicetools.Elements()
        self._logfilepath = None
        self.result = None

    def add_rules(
            self,
            *rules: Rule,
    ) -> None:
        # noinspection PyTypeChecker
        """Add some |Rule| objects to the actual |CalibrationInterface| object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(
        ...     hp=hp,
        ...     targetfunction=lambda hp_: None,
        ... )
        >>> from hydpy import Replace
        >>> ci.add_rules(
        ...     Replace(
        ...         name='fc',
        ...         parameter='fc',
        ...         value=100.0,
        ...         model='hland_v1',
        ...     ),
        ...     Replace(
        ...         name='percmax',
        ...         parameter='percmax',
        ...         value=5.0,
        ...         model='hland_v1',
        ...     ),
        ... )

        Note that method |CalibrationInterface.add_rules| might change the
        number of |Element| objects relevant for the |CalibrationInterface|
        object:

        >>> damp = Replace(
        ...     name='damp',
        ...     parameter='damp',
        ...     value=0.2,
        ...     model='hstream_v1',
        ... )

        >>> len(ci._elements)
        4
        >>> ci.add_rules(damp)
        >>> len(ci._elements)
        7
        """
        for rule in rules:
            self._rules[rule.name] = rule
            self._update_elements_when_adding_a_rule(rule)

    def remove_rules(self, *rules: Union[str, Rule]) -> None:
        # noinspection PyTypeChecker
        """Remove some |Rule| objects from the actual |CalibrationInterface|
        object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(
        ...     hp=hp,
        ...     targetfunction=lambda hp_: None,
        ... )
        >>> from hydpy import Replace
        >>> ci.add_rules(
        ...     Replace(
        ...         name='fc',
        ...         parameter='fc',
        ...         value=100.0,
        ...         model='hland_v1',
        ...     ),
        ...     Replace(
        ...         name='percmax',
        ...         parameter='percmax',
        ...         value=5.0,
        ...         model='hland_v1',
        ...     ),
        ...     Replace(
        ...         name='damp',
        ...         parameter='damp',
        ...         value=0.2,
        ...         model='hstream_v1',
        ...     )
        ... )

        You can remove each rule either by passing itself or its name (note
        that method |CalibrationInterface.remove_rules| might change the
        number of |Element| objects relevant for the |CalibrationInterface|
        object):

        >>> len(ci._elements)
        7
        >>> ci.remove_rules(ci.fc, 'damp')
        >>> ci
        Replace(
            name='percmax',
            parameter='percmax',
            lower=-inf,
            upper=inf,
            parameterstep='1d',
            value=5.0,
            model='hland_v1',
            selections=('complete',),
        )
        >>> len(ci._elements)
        4

        Trying to remove a non-existing rule results in the following error:

        >>> ci.remove_rules('fc')
        Traceback (most recent call last):
        ...
        RuntimeError: The actual calibration interface object does not handle \
a rule object named `fc`.
        """
        for rule in rules:
            if isinstance(rule, Rule):
                rule = rule.name
            try:
                del self._rules[rule]
            except KeyError:
                raise RuntimeError(
                    f'The actual calibration interface object does '
                    f'not handle a rule object named `{rule}`.'
                ) from None
        self._update_elements_when_deleting_a_rule()

    def make_rules(
            self,
            *,
            rule: RuleArg,
            names: Iterable[str],
            parameters: Iterable[Union[parametertools.Parameter, str]],
            values: Iterable[float],
            lowers: Iterable[float],
            uppers: Iterable[float],
            parameterstep: Optional[timetools.PeriodConstrArg] = None,
            selections: Optional[
                Union[selectiontools.Selections, Iterable[str]]
            ] = None,
            model: Optional[Union[types.ModuleType, str]] = None,
    ) -> None:
        # noinspection PyTypeChecker
        """Create and store new |Rule| objects.

        The main documentation on class |CalibrationInterface| explains
        the usage of method |CalibrationInterface.make_rules| in some
        detail.  The example shows the error message method
        |CalibrationInterface.make_rules| raises in case of a wrong
        `rule` argument:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(
        ...     hp=hp,
        ...     targetfunction=lambda hp_: None,
        ... )
        >>> ci.make_rules(
        ...     rule='Insert',
        ...     names=['fc', 'percmax'],
        ...     parameters=['fc', 'percmax'],
        ...     values=[100.0, 5.0],
        ...     lowers=[50.0, 1.0],
        ...     uppers=[200.0, 10.0],
        ...     parameterstep='1d',
        ...     model='hland_v1',
        ... )
        Traceback (most recent call last):
        ...
        ValueError: No rule of type `Insert` available.

        To avoid passing wrong strings, you can pass the proper |Rule|
        subclass itself:

        >>> from hydpy import Replace
        >>> ci.make_rules(
        ...     rule=Replace,
        ...     names=['fc', 'percmax'],
        ...     parameters=['fc', 'percmax'],
        ...     values=[100.0, 5.0],
        ...     lowers=[50.0, 1.0],
        ...     uppers=[200.0, 10.0],
        ...     parameterstep='1d',
        ...     model='hland_v1',
        ... )
        >>> ci.fc
        Replace(
            name='fc',
            parameter='fc',
            lower=50.0,
            upper=200.0,
            parameterstep=None,
            value=100.0,
            model='hland_v1',
            selections=('complete',),
        )
        """
        if isinstance(rule, str):
            try:
                rule = {
                    'replace': Replace,
                    'add': Add,
                    'multiply': Multiply,
                }[rule.lower()]
            except KeyError:
                raise ValueError(
                    f'No rule of type `{rule}` available.'
                ) from None
        pariter = objecttools.extract(
            values=parameters,
            types_=(parametertools.Parameter, str),
        )
        for name, parameter, lower, upper, value in zip(
            names,
            pariter,
            lowers,
            uppers,
            values,
        ):
            self.add_rules(
                rule(
                    name=name,
                    parameter=parameter,
                    value=value,
                    lower=lower,
                    upper=upper,
                    parameterstep=parameterstep,
                    selections=selections,
                    model=model,
                )
            )

    def prepare_logfile(
            self,
            logfilepath: str,
            objectivefunction: str = 'result',
            documentation: Optional[str] = None
    ) -> None:
        """Prepare a log file.

        Use argument `objectivefunction` to describe the |TargetFunction| used
        for calculating the efficiency and argument `documentation` to add
        some information to the header of the logfile.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        self._logfilepath = logfilepath
        with open(logfilepath, 'w') as logfile:
            if documentation:
                lines = (f'# {line}' for line in documentation.split('\n'))
                logfile.write('\n'.join(lines))
                logfile.write('\n\n')
            logfile.write(f'{objectivefunction}\t')
            names = (rule.name for rule in self)
            logfile.write('\t'.join(names))
            logfile.write('\n')
            steps = [str(rule.parameterstep) for rule in self]
            logfile.write('\t'.join(['parameterstep'] + steps))
            logfile.write('\n')

    def update_logfile(
            self,
    ) -> None:
        """Update the current log file, if available.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        if self._logfilepath:
            with open(self._logfilepath, 'a') as logfile:
                logfile.write(f'{objecttools.repr_(self.result)}\t')
                logfile.write(
                    '\t'.join(objecttools.repr_(value) for value in self.values)
                )
                logfile.write('\n')

    def read_logfile(
            self,
            logfilepath: str,
            maximisation: bool,
    ) -> None:
        """Read the log file with the given file path.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        with open(logfilepath) as logfile:
            # pylint: disable=not-an-iterable
            # because pylint is wrong!?
            lines = tuple(
                line for line in logfile
                if line.strip() and (not line.startswith('#'))
            )
            # pylint: disable=not-an-iterable
        idx2name, idx2rule = {}, {}
        for idx, (name, parameterstep) in enumerate(
                zip(
                    lines[0].split()[1:],
                    lines[1].split()[1:]
                ),
        ):
            if name in self._rules:
                rule = self._rules[name]
                if parameterstep == 'None':
                    parameterstep = None
                else:
                    parameterstep = timetools.Period(parameterstep)
                if parameterstep != rule.parameterstep:
                    raise RuntimeError(
                        f'The current parameterstep of the '
                        f'`{type(rule).__name__}` rule `{rule.name}` '
                        f'(`{rule.parameterstep}`) does not agree with the '
                        f'one documentated in log file `{self._logfilepath}` '
                        f'(`{parameterstep}`).'
                    )
                idx2rule[idx] = rule
            idx2name[idx] = name
        names_int = set(self.names)
        names_ext = set(idx2name.values())
        if names_int != names_ext:
            enumeration = objecttools.enumeration
            raise RuntimeError(
                f'The names of the rules handled by the actual calibration '
                f'interface ({enumeration(sorted(names_int))}) do not agree '
                f'with the names in the header of logfile '
                f'`{self._logfilepath}` ({enumeration(sorted(names_ext))}).'
            )
        jdx_best = 0
        result_best = -numpy.inf if maximisation else numpy.inf
        for jdx, line in enumerate(lines[2:]):
            result = float(line.split()[0])
            if (
                    (maximisation and (result > result_best)) or
                    ((not maximisation) and (result < result_best))
            ):
                jdx_best = jdx
                result_best = result

        for idx, value in enumerate(lines[jdx_best+2].split()[1:]):
            idx2rule[idx].value = float(value)
        self.result = result_best

    def _update_elements_when_adding_a_rule(
            self,
            rule: Rule,
    ) -> None:
        self._elements += rule.elements

    def _update_elements_when_deleting_a_rule(self) -> None:
        self._elements = devicetools.Elements()
        for rule in self:
            self._elements += rule.elements

    @property
    def names(self) -> Tuple[str, ...]:
        """The names of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        return tuple(rule.name for rule in self)

    @property
    def values(self) -> Tuple[float, ...]:
        """The (original) values of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        return tuple(rule.value for rule in self)

    @property
    def lowers(self) -> Tuple[float, ...]:
        """The lower boundaries of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        return tuple(rule.lower for rule in self)

    @property
    def uppers(self) -> Tuple[float, ...]:
        """The upper boundaries of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        return tuple(rule.upper for rule in self)

    def _update_values(
            self,
            values: Iterable[float],
    ) -> None:
        for rule, value in zip(self, values):
            rule.value = value

    def _refresh_hp(self):
        for element in self._elements:
            element.model.parameters.update()
        self._hp.conditions = self.conditions

    def apply_values(self) -> float:
        """Apply all current calibration parameter values on all relevant
        parameters.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        for rule in self:
            rule.apply_value()
        self._refresh_hp()
        self._hp.simulate()
        return self.calculate_likelihood()

    def reset_parameters(self) -> None:
        """Reset all relevant parameters to their original states.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        for rule in self:
            rule.reset_parameters()
        self._refresh_hp()

    def calculate_likelihood(self) -> float:
        """Apply the defined |TargetFunction| and return the result.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        self.result = self._targetfunction(self._hp)
        return self.result

    def perform_calibrationstep(
            self,
            values: Iterable,
            *args: Any,
            **kwargs: Any,
    ) -> float:
        # pylint: disable=unused-argument
        # for optimisers that pass additional informative data
        """Update all calibration parameters with the given values, update
        the |HydPy| object, perform a simulation run, and calculate and
        return the achieved efficiency.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        self._update_values(values)
        likelihood = self.apply_values()
        self.update_logfile()
        return likelihood

    def __len__(self) -> int:
        return len(self._rules)

    def __iter__(self) -> Iterator[Rule]:
        for rule in self._rules.values():
            yield rule

    def __getattr__(self, item: str) -> Any:
        try:
            return self._rules[item]
        except KeyError:
            raise AttributeError(
                f'The actual calibration interface does neither handle a '
                f'normal attribute nor a rule object named `{item}`.'
            ) from None

    def __getitem__(self, key: str) -> Rule:
        try:
            return self._rules[key]
        except KeyError:
            raise KeyError(
                f'The actual calibration interface does not handle '
                f'a rule object named `{key}`.'
            ) from None

    def __repr__(self) -> str:
        return '\n'.join(repr(rule) for rule in self)

    def __str__(self) -> str:
        return objecttools.classname(self)

    def __dir__(self) -> List[str]:
        """

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(
        ...     hp=hp,
        ...     targetfunction=lambda hp_: None,
        ... )
        >>> ci.make_rules(
        ...     rule='Replace',
        ...     names=['fc', 'percmax'],
        ...     parameters=['fc', 'percmax'],
        ...     values=[100.0, 5.0],
        ...     lowers=[50.0, 1.0],
        ...     uppers=[200.0, 10.0],
        ...     parameterstep='1d',
        ...     model='hland_v1',
        ... )
        >>> dir(ci)   # doctest: +ELLIPSIS
        ['add_rules', 'apply_values', 'calculate_likelihood', 'conditions', \
'fc', 'lowers', 'make_rules', 'names', 'percmax', 'perform_calibrationstep', \
'prepare_logfile', 'read_logfile', 'remove_rules', 'reset_parameters', \
'result', 'update_logfile', 'uppers', 'values']
        """
        return objecttools.dir_(self) + list(self._rules.keys())


class ReplaceIUH(Rule):
    """A |Rule| class specialised for |IUH| parameters.

    Usually, it is not a good idea to calibrate the AR and MA coefficients
    of parameters like |arma_control.Responses| of model |arma_v1| individually.
    Instead, we need to calibrate the few coefficients of the underlying |IUH|
    objects, which calculate the ARMA coefficients.  Class |ReplaceIUH| helps
    to accomplish this task.

    .. note::

        Class |ReplaceIUH| is still under development.  For example, it
        does not address the possibility of different ARMA coefficients
        related to different discharge thresholds.  Hence, the usage
        of class |ReplaceIUH| might change in the future.

    So far, there is no example project containing |arma_v1| models
    instances.  Therefore, we generate a simple one consisting of two
    |Element| objects only:

    >>> from hydpy import Element, prepare_model, Selection
    >>> element1 = Element('element1', inlets='in1', outlets='out1')
    >>> element2 = Element('element2', inlets='in2', outlets='out2')
    >>> complete = Selection('complete', elements=[element1, element2])
    >>> element1.model = prepare_model('arma_v1')
    >>> element2.model = prepare_model('arma_v1')

    We focus on class |TranslationDiffusionEquation| in the following.
    We create two separate instances and use to calculate the response
    coefficients of both |arma_v1| instances:

    >>> from hydpy import TranslationDiffusionEquation
    >>> tde1 = TranslationDiffusionEquation(u=5.0, d=15.0, x=1.0)
    >>> tde2 = TranslationDiffusionEquation(u=5.0, d=15.0, x=2.0)
    >>> element1.model.parameters.control.responses(tde1.arma.coefs)
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.906536, -0.197555, 0.002128, 0.000276),
                      (0.842788, -0.631499, 0.061685, 0.015639, 0.0, 0.0, 0.0,
                       -0.000001, 0.0, 0.0, 0.0, 0.0)))
    >>> element2.model.parameters.control.responses(tde2.arma.coefs)
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((1.298097, -0.536702, 0.072903, -0.001207, -0.00004),
                      (0.699212, -0.663835, 0.093935, 0.046177, -0.00854)))

    Next, we define one |ReplaceIUH| for modifying parameter
    |TranslationDiffusionEquation.u| and another one for changing
    |TranslationDiffusionEquation.d|:

    >>> from hydpy import ReplaceIUH
    >>> u = ReplaceIUH(
    ...     name='u',
    ...     parameter='responses',
    ...     value=5.0,
    ...     lower=1.0,
    ...     upper=10.0,
    ...     selections=[complete],
    ... )
    >>> d = ReplaceIUH(
    ...     name='d',
    ...     parameter='responses',
    ...     value=15.0,
    ...     lower=5.0,
    ...     upper=50.0,
    ...     selections=[complete],
    ... )

    We add and thereby connect the |Element| and |TranslationDiffusionEquation|
    objects to both |ReplaceIUH| objects via method |ReplaceIUH.add_iuhs|:

    >>> u.add_iuhs(element1=tde1, element2=tde2)
    >>> d.add_iuhs(element1=tde1, element2=tde2)

    Note that method |ReplaceIUH.add_iuhs| enforces to add all |IUH| objects
    at ones to avoid inconsistencies that might be hard to track later:

    >>> d.add_iuhs(element1=tde1)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add `IUH` objects to the `ReplaceIUH` rule \
`d`, the following error occurred: The given elements (element1) do not \
agree with the complete set of relevant elements (element1 and element2).

    By default, each |ReplaceIUH| objects triggers the calculation of the ARMA
    coefficients during the execution of its method |ReplaceIUH.apply_value|,
    which can be a waste of computation time if we want to calibrate multiple
    |IUH| coefficients.  To save computation time in such cases, set option
    |ReplaceIUH.update_parameters| to |False| for all except the lastly
    executed |ReplaceIUH| objects:

    >>> u.update_parameters = False

    Now, changing the value of rule `u` and calling method
    |ReplaceIUH.apply_value| does not affect the coefficients of both
    |arma_control.Responses| parameters:

    >>> u.value = 10.0
    >>> u.apply_value()
    >>> tde1
    TranslationDiffusionEquation(d=15.0, u=10.0, x=1.0)
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.906536, -0.197555, 0.002128, 0.000276),
                      (0.842788, -0.631499, 0.061685, 0.015639, 0.0, 0.0, 0.0,
                       -0.000001, 0.0, 0.0, 0.0, 0.0)))
    >>> tde2
    TranslationDiffusionEquation(d=15.0, u=10.0, x=2.0)
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((1.298097, -0.536702, 0.072903, -0.001207, -0.00004),
                      (0.699212, -0.663835, 0.093935, 0.046177, -0.00854)))

    On the other side, calling method |ReplaceIUH.apply_value| of rule `d`
    does activate the freshly set value of rule `d` and the previously set
    value of rule `u`, as well:

    >>> d.value = 50.0
    >>> d.apply_value()
    >>> tde1
    TranslationDiffusionEquation(d=50.0, u=10.0, x=1.0)
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.811473, -0.15234, -0.000256, 0.000177),
                      (0.916619, -0.670781, 0.087185, 0.007923)))
    >>> tde2
    TranslationDiffusionEquation(d=50.0, u=10.0, x=2.0)
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((0.832237, -0.167205, 0.002007, 0.000184),
                      (0.836513, -0.555399, 0.037628, 0.014035)))

    Use method |ReplaceIUH.reset_parameters| to restore the original
    ARMA coefficients:

    >>> d.reset_parameters()
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.906536, -0.197555, 0.002128, 0.000276),
                      (0.842788, -0.631499, 0.061685, 0.015639, 0.0, 0.0, 0.0,
                       -0.000001, 0.0, 0.0, 0.0, 0.0)))
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((1.298097, -0.536702, 0.072903, -0.001207, -0.00004),
                      (0.699212, -0.663835, 0.093935, 0.046177, -0.00854)))
    """

    update_parameters: bool = True
    """Flag indicating whether method |ReplaceIUH.apply_value| should 
    calculate the |ARMA.coefs| and pass them to the relevant model parameter
    or not.
    
    Set this flag to |False| for the first |ReplaceIUH| object when another
    one handles the same elements and is applied afterwards.
    """
    _element2iuh: Optional[Dict[str, iuhtools.IUH]] = None

    def _get_original_parameter_values(
            self,
    ) -> Tuple[Union[float, numpy.ndarray], ...]:
        return tuple(
            (par.ar_coefs[0, :].copy(), par.ma_coefs[0, :].copy())
            for par in self
        )

    def add_iuhs(
            self,
            **iuhs: iuhtools.IUH,
    ) -> None:
        """Add one |IUH| object for each relevant |Element| objects.

        See the main documentation on class |ReplaceIUH| for further
        information.
        """
        try:
            names_int = set(self.elements.names)
            names_ext = set(iuhs.keys())
            if names_int != names_ext:
                enumeration = objecttools.enumeration
                raise RuntimeError(
                    f'The given elements ({enumeration(sorted(names_ext))}) '
                    f'do not agree with the complete set of relevant '
                    f'elements ({enumeration(sorted(names_int))}).'
                )
            element2iuh = self._element2iuh = {}
            for element in self.elements:
                element2iuh[element.name] = iuhs[element.name]
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to add `IUH` objects to the '
                f'`{type(self).__name__}` rule `{self}`'
            )

    @property
    def _iuhs(self) -> Iterable[iuhtools.IUH]:
        element2iuh = {} if self._element2iuh is None else self._element2iuh
        for iuh in element2iuh.values():
            yield iuh

    def apply_value(self) -> None:
        """Apply all current calibration parameter values on all relevant
        |IUH| objects and eventually update the ARMA coefficients of the
        related parameter.

        See the main documentation on class |CalibrationInterface| for
        further information.
        """
        for parameter, iuh in zip(self, self._iuhs):
            # entries = self.name.split('_')
            # name = entries[0]
            # threshold = '_'.join(entries[1:])
            # setattr(iuh, self.name, self.value)
            # if self.update_parameters:
            #     try:
            #         parameter(iuh.arma.coefs)
            #     except RuntimeError:
            #         parameter(((), iuh.ma.coefs))
            setattr(iuh, self.name, self.value)
            if self.update_parameters:
                parameter(iuh.arma.coefs)

    def reset_parameters(self) -> None:
        """Reset all relevant parameter objects to their original states.

        See the main documentation on class |ReplaceIUH| for further
        information.
        """
        for parameter, orig in zip(self, self._original_parameter_values):
            parameter(orig)
