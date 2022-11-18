# -*- coding: utf-8 -*-
"""This module implements features for calibrating model parameters.

.. _`NLopt`: https://nlopt.readthedocs.io/en/latest/
"""

# import...
# ...from standard library
from __future__ import annotations
import abc
import collections
import itertools
import time
import types
import warnings
from typing import *
from typing import TextIO
from typing_extensions import Literal  # type: ignore[misc]
from typing_extensions import Protocol  # type: ignore[misc]

# ...from site-packages
import black
import numpy

# ...from hydpy
import hydpy
from hydpy import config
from hydpy.core import devicetools
from hydpy.core import hydpytools
from hydpy.core import masktools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import selectiontools
from hydpy.core import timetools
from hydpy.core import variabletools
from hydpy.auxs import iuhtools
from hydpy.models.arma import arma_control
from hydpy.core.typingtools import *

TypeParameter = TypeVar("TypeParameter", bound=parametertools.Parameter)
TypeRule1 = TypeVar(
    "TypeRule1",
    bound=Union["Replace", "Add", "Multiply", "ReplaceIUH", "MultiplyIUH"],
)
TypeRule2 = TypeVar(
    "TypeRule2",
    bound=Union["Replace", "Add", "Multiply", "ReplaceIUH", "MultiplyIUH"],
)
TypeRule = TypeVar("TypeRule", "Replace", "Add", "Multiply")
Target = Optional[str]


class TargetFunction(Protocol):
    """Protocol class for the target function required by class |CalibrationInterface|.

    The target functions must calculate and return a floating-point number reflecting
    the quality of the current parameterisation of the models of the current project.
    Often, as in the following example, the target function relies on objective
    functions as |nse|, applied on the time series of the |Sim| and |Obs| sequences
    handled by the |HydPy| object:

    >>> from hydpy import HydPy, nse, TargetFunction
    >>> class Target(TargetFunction):
    ...     def __init__(self, hp):
    ...         self.hp = hp
    ...     def __call__(self):
    ...         return sum(nse(node=node) for node in self.hp.nodes)
    >>> target = Target(HydPy())

    See the documentation on class |CalibrationInterface| for more information.
    """

    def __call__(self) -> float:
        """Return some kind of efficience criterion."""


class Adaptor(Protocol):
    """Protocol class for defining adoptors required by |Replace| objects.

    Often, one calibration parameter (represented by one |Replace| object) depends on
    other calibration parameters (represented by other |Replace| objects) or other
    "real" parameter values.  Please select an existing or define a new adaptor and
    assign it to a |Replace| object to introduce such dependencies.

    See class |SumAdaptor| or class |FactorAdaptor| for concrete examples.
    """

    def __call__(self, target: parametertools.Parameter) -> None:
        """Modify the value(s) of the given target |Parameter| object."""


class SumAdaptor(Adaptor):
    """Adaptor, which calculates the sum of the values of multiple |Rule| objects and
    assigns it to the value(s) of the target |Parameter| object.

    Class |SumAdaptor| helps to introduce "larger than" relationships between
    calibration parameters.  A common use case is the time of concentration of
    different runoff components.  For example, the time of concentration of base flow
    should be larger than the one of direct runoff.  Accordingly, when modelling runoff
    concentration with linear storages, the recession coefficient of direct runoff
    should be larger. Principally, we could ensure this during a calibration process by
    defining two |Rule| objects with fixed non-overlapping parameter ranges.  For
    example, we could search for the best direct runoff delay between 1 and 5 days and
    the base flow delay between 5 and 100 days.  We demonstrate this for the recession
    coefficient parameters |hland_control.K| and |hland_control.K4| of application
    model |hland_v1| (assuming the nonlinearity parameter |hland_control.Alpha| to be
    zero):

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import Replace, SumAdaptor
    >>> k = Replace(name="k",
    ...             parameter="k",
    ...             value=2.0**-1,
    ...             lower=5.0**-1,
    ...             upper=1.0**-1,
    ...             parameterstep="1d",
    ...             model="hland_v1")
    >>> k4 = Replace(name="k4",
    ...             parameter="k4",
    ...             value=10.0**-1,
    ...             lower=100.0**-1,
    ...             upper=5.0**-1,
    ...             parameterstep="1d",
    ...             model="hland_v1")

    To allow for non-fixed non-overlapping ranges, we can prepare a |SumAdaptor| object,
    knowing both our |Rule| objects, assign it the direct runoff-related |Rule| object,
    and, for example, set its lower boundary to zero:

    >>> k.adaptor = SumAdaptor(k, k4)
    >>> k.lower = 0.0

    Calling method |Replace.apply_value| of the |Replace| objects makes our
    |SumAdaptor| object apply the sum of the values of all of its |Rule| objects:

    >>> control = hp.elements.land_dill.model.parameters.control
    >>> k.apply_value()
    >>> with pub.options.parameterstep("1d"):
    ...     control.k
    k(0.6)
    """

    _rules: Tuple[Rule[parametertools.Parameter], ...]

    def __init__(self, *rules: Rule[parametertools.Parameter]):
        self._rules = tuple(rules)

    def __call__(self, target: parametertools.Parameter) -> None:
        target(sum(rule.value for rule in self._rules))


class FactorAdaptor(Adaptor):
    """Adaptor, which calculates the product of the value of the parent |Replace|
    object and the value(s) of a given reference |Parameter| object and assigns it to
    the value(s) of the target |Parameter| object.

    Class |FactorAdaptor| helps to respect dependencies between model parameters.  If
    you, for example, aim at calibrating the permanent wilting point
    (|lland_control.PWP|) of model |lland_v1|, you need to make sure it always agrees
    with the maximum soil water storage (|lland_control.WMax|).  Especially, one should
    avoid permanent wilting points larger than total porosity.  Due to the high
    variability of soil properties within most catchments, it is no real option to
    define a fixed upper threshold for |lland_control.PWP|.  By using class
    |FactorAdaptor|, you can instead calibrate a multiplication factor.  Setting the
    bounds of such a factor to 0.0 and 0.5, for example, would result in
    |lland_control.PWP| values ranging from zero up to half of |lland_control.WMax| for
    each respective response unit.

    To show how class |FactorAdaptor| works, we select another use-case based on the
    `Lahn` example project prepared by function |prepare_full_example_2|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    |hland_v1| calculates the "normal" potential snow-melt with the degree-day factor
    |hland_control.CFMax|.  For glacial zones, it also calculates a separate potential
    glacier-melt with the additional degree-day factor |hland_control.GMelt|.  Suppose
    we have |hland_control.CFMax| readily available for the different hydrological
    response units of the Lahn catchment.  We might find it useful to calibrate
    |hland_control.GMelt| based on the spatial pattern of |hland_control.CFMax|.
    Therefore, we first define an |Replace| rule for parameter |hland_control.GMelt|:

    >>> from hydpy import Replace, FactorAdaptor
    >>> gmelt = Replace(name="gmelt",
    ...                 parameter="gmelt",
    ...                 value=2.0,
    ...                 lower=0.5,
    ...                 upper=2.0,
    ...                 parameterstep="1d",
    ...                 model="hland_v1")

    Second, we initialise a |FactorAdaptor| object based on target rule `gmelt` and our
    reference parameter |hland_control.CFMax| and assign it our rule object:

    >>> gmelt.adaptor = FactorAdaptor(gmelt, "cfmax")

    The `Dill` subcatchment, like the whole `Lahn` basin, does not contain any
    glaciers.  Hence it defines (identical) |hland_control.CFMax| values for the zones
    of type |hland_constants.FIELD| and |hland_constants.FOREST| but must not specify
    any value for |hland_control.GMelt|:

    >>> control = hp.elements.land_dill.model.parameters.control
    >>> control.cfmax
    cfmax(field=4.55853, forest=2.735118)
    >>> control.gmelt
    gmelt(nan)

    Next, we call method |Replace.apply_value| of the |Replace| object to apply the
    |FactorAdaptor| object on all relevant |hland_control.GMelt| instances of the `Lahn`
    catchment:

    >>> gmelt.adaptor(control.gmelt)

    The string representation of the |hland_control.GMelt| instance of the Dill
    catchment indicates nothing happened:

    >>> control.gmelt
    gmelt(nan)

    However, inspecting the individual values of the respective response units reveals
    the multiplication was successful:

    >>> from hydpy import print_values
    >>> print_values(control.gmelt.values)
    9.11706, 5.470236, 9.11706, 5.470236, 9.11706, 5.470236, 9.11706,
    5.470236, 9.11706, 5.470236, 9.11706, 5.470236

    Calculating values for response units that do not require these values can be
    misleading.  We can improve the situation by using the masks provided by the
    respective model; in our example, mask |hland_masks.Glacier|.  To make this
    clearer, we set the  first six response units to |hland_control.ZoneType|
    |hland_constants.GLACIER|:

    >>> from hydpy.models.hland_v1 import *
    >>> control.zonetype(GLACIER, GLACIER, GLACIER, GLACIER, GLACIER, GLACIER,
    ...                  FIELD, FOREST, ILAKE, FIELD, FOREST, ILAKE)

    We now can assign the |SumAdaptor| object to the direct runoff-related |Replace|
    object and, for example, set its lower boundary to zero:

    Now we create a new |FactorAdaptor| object, handling the same parameters but also
    the |hland_masks.Glacier| mask:

    >>> gmelt.adaptor = FactorAdaptor(gmelt, "cfmax", "glacier")

    To see the results of our new adaptor object, we change the values both of our
    reference parameter and our rule object:

    >>> control.cfmax(field=5.0, forest=3.0, glacier=6.0)
    >>> gmelt.value = 0.5

    The string representation of our target parameter shows that the glacier-related
    day degree factor of all glacier zones is now half as large as the snow-related one:

    >>> gmelt.apply_value()
    >>> control.gmelt
    gmelt(3.0)

    Note that all remaining values (for zone types |hland_constants.FIELD|,
    |hland_constants.FOREST|, and |hland_constants.ILAKE| are still the same.  This
    intended behaviour allows calibrating, for example, hydrological response units of
    different types with different rule objects:

    >>> print_values(control.gmelt.values)
    3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 9.11706, 5.470236, 9.11706, 5.470236,
    9.11706, 5.470236
    """

    _rule: Rule[parametertools.Parameter]
    _reference: str
    _mask: Optional[str]

    def __init__(
        self,
        rule: Rule[parametertools.Parameter],
        reference: Union[Type[parametertools.Parameter], parametertools.Parameter, str],
        mask: Optional[Union[masktools.BaseMask, str]] = None,
    ):
        self._rule = rule
        self._reference = str(getattr(reference, "name", reference))
        self._mask = mask if ((mask is None) or isinstance(mask, str)) else mask.name

    def __call__(self, target: parametertools.Parameter) -> None:
        ref = target.subpars[self._reference]
        if self._mask:
            mask = ref.get_submask(self._mask)
            values = ref.values[mask] if ref.NDIM else ref.value
            target.values[mask] = self._rule.value * values
        else:
            target.value = self._rule.value * ref.value


class Rule(abc.ABC, Generic[TypeParameter]):
    """Base class for defining calibration rules.

    Each |Rule| object relates one calibration parameter with some model parameters.
    We select the class |Replace| as a concrete example for the following explanations
    and use the `Lahn` example project, which we prepare by calling function
    |prepare_full_example_2|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    We define a |Rule| object supposed to replace the values of parameter
    |hland_control.FC| of application model |lland_v1|.  Note that argument `name` is
    the rule's name, whereas the argument `parameter` is the parameter's name:

    >>> from hydpy import Replace
    >>> rule = Replace(name="fc",
    ...                parameter="fc",
    ...                value=100.0,
    ...                model="hland_v1")

    The following string representation shows us the complete list of available
    arguments:

    >>> rule
    Replace(
        name="fc",
        parameter="fc",
        value=100.0,
        lower=-inf,
        upper=inf,
        keyword=None,
        parameterstep=None,
        model="hland_v1",
        selections=("complete",),
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

    Sometimes, one must differentiate between the original value to be calibrated and
    the actually applied value.  Therefore, (only) the |Replace| class allows for
    defining custom "adaptors". Prepare an |Adaptor| function and assign it to the
    relevant |Replace| object (see the documentation on class |SumAdaptor| or
    |FactorAdaptor| for more realistic examples):

    >>> rule.adaptor = lambda target: target(2.0 * rule.value)

    Now, our rule does not apply the original but the adapted calibration parameter
    value:

    >>> rule.apply_value()
    >>> fc
    fc(400.0)

    Use method |Rule.reset_parameters| to restore the original states of the affected
    parameters ("original" here means at the time of initialisation of the |Rule|
    object):

    >>> rule.reset_parameters()
    >>> fc
    fc(206.0)

    Some parameter types support defining their values via custom keywords.
    |hland_control.FC|, for example, allows setting the values of multiple zones of
    the same land-use type via keyword arguments such as `forest`:

    >>> rule = Replace(name="fc",
    ...                parameter="fc",
    ...                value=100.0,
    ...                keyword="forest",
    ...                model="hland_v1")
    >>> rule.apply_value()
    >>> fc
    fc(field=206.0, forest=100.0)

    The value of parameter |hland_control.FC| is not time-dependent.  Therefore, any
    |Options.parameterstep| information given to its |Rule| object is ignored (note
    that we pass an example parameter object of type |hland_control.FC| instead of the
    string `fc` this time):

    >>> Replace(name="fc",
    ...         parameter=fc,
    ...         value=100.0,
    ...         model="hland_v1",
    ...         parameterstep="1d")
    Replace(
        name="fc",
        parameter="fc",
        value=100.0,
        lower=-inf,
        upper=inf,
        keyword=None,
        parameterstep=None,
        model="hland_v1",
        selections=("complete",),
    )

    For time-dependent parameters, the rule queries the current global
    |Options.parameterstep| value if you do not specify one explicitly (note that we
    pass the parameter type |hland_control.PercMax| and the module |hland_v1| this
    time):

    >>> from hydpy.models import hland_v1
    >>> from hydpy.models.hland.hland_control import PercMax
    >>> rule = Replace(name="percmax",
    ...                parameter=PercMax,
    ...                value=5.0,
    ...                model=hland_v1)

    The |Rule| object internally handles, to avoid confusion, a copy of
    |Options.parameterstep|.

    >>> from hydpy import pub
    >>> pub.options.parameterstep = None
    >>> rule
    Replace(
        name="percmax",
        parameter="percmax",
        value=5.0,
        lower=-inf,
        upper=inf,
        keyword=None,
        parameterstep="1d",
        model="hland_v1",
        selections=("complete",),
    )
    >>> rule.apply_value()
    >>> percmax = hp.elements.land_lahn_1.model.parameters.control.percmax
    >>> with pub.options.parameterstep("1d"):
    ...     percmax
    percmax(5.0)

    Alternatively, you can pass a parameter step size yourself:

    >>> rule = Replace(name="percmax",
    ...                parameter="percmax",
    ...                value=5.0,
    ...                model="hland_v1",
    ...                parameterstep="2d")
    >>> rule.apply_value()
    >>> with pub.options.parameterstep("1d"):
    ...     percmax
    percmax(2.5)

    Missing parameter step-size information results in the following error:

    >>> Replace(name="percmax",
    ...         parameter="percmax",
    ...         value=5.0,
    ...         model="hland_v1")
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to initialise the `Replace` rule object `percmax`, the \
following error occurred: Rules which handle time-dependent parameters require \
information on the parameter timestep size.  Either assign it directly or define it \
via option `parameterstep`.

    With the following definition, the |Rule| object queries all |Element| objects
    handling |hland_v1| instances from the global |Selections| object `pub.selections`:

    >>> rule = Replace(name="fc",
    ...                parameter="fc",
    ...                value=100.0,
    ...                model="hland_v1")
    >>> rule.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")

    Alternatively, you can specify selections by passing themselves or their names (the
    latter requires them to be a member of `pub.selections`):

    >>> rule = Replace(name="fc",
    ...                parameter="fc",
    ...                value=100.0,
    ...                selections=[pub.selections.headwaters, "nonheadwaters"])
    >>> rule.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3")

    Without using the `model` argument, you must ensure the selected elements handle
    the correct model instance yourself:

    >>> Replace(name="fc",
    ...         parameter="fc",
    ...         value=100.0)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to initialise the `Replace` rule object `fc`, the \
following error occurred: Model `musk_classic` of element `stream_dill_lahn_2` does \
not define a control parameter named `fc`.

    >>> Replace(name="fc",
    ...         parameter="fc",
    ...         value=100.0,
    ...         model="musk_classic",
    ...         selections=[pub.selections.headwaters, "nonheadwaters"])
    Traceback (most recent call last):
    ...
    ValueError: While trying to initialise the `Replace` rule object `fc`, the \
following error occurred: Object `Selections("headwaters", "nonheadwaters")` does not \
handle any `musk_classic` model instances.
    """

    name: str
    """The name of the |Rule| object."""

    lower: float
    """Lower boundary value.

    No lower boundary corresponds to minus |numpy.inf|.
    """

    upper: float
    """Upper boundary value.

    No upper boundary corresponds to plus |numpy.inf|.
    """

    parametername: str
    """The name of the addressed |Parameter| objects."""

    parametertype: Type[TypeParameter]
    """The type of the addressed |Parameter| objects."""

    keyword: Optional[str]
    """The name of the addressed keyword argument or, for a positional argument, 
    |None|."""

    elements: devicetools.Elements
    """The |Element| objects, which handle the relevant target |Parameter| instances."""

    selections: Tuple[str, ...]
    """The names of all relevant |Selection| objects."""

    _value: float
    _model: Optional[str]
    _parameterstep: Optional[timetools.Period]
    _original_parameter_values: Tuple[Union[float, Vector[float], Matrix[float]], ...]

    def __init__(
        self,
        *,
        name: str,
        parameter: Union[Type[TypeParameter], TypeParameter, str],
        value: float,
        lower: float = -numpy.inf,
        upper: float = numpy.inf,
        keyword: Optional[str] = None,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        selections: Optional[Iterable[Union[selectiontools.Selection, str]]] = None,
        model: Optional[Union[types.ModuleType, str]] = None,
    ) -> None:
        try:
            self.name = name
            self.parametername = str(getattr(parameter, "name", parameter))
            self.keyword = keyword
            self.upper = upper
            self.lower = lower
            self.value = value
            if model is None:
                self._model = model
            elif isinstance(model, str):
                self._model = model
            else:
                self._model = model.__name__.rpartition(".")[-1]
            if selections is None:
                selections = hydpy.pub.selections
                if "complete" in selections:
                    selections = selectiontools.Selections(selections.complete)
            else:
                selections = selectiontools.Selections(
                    *(
                        sel
                        if isinstance(sel, selectiontools.Selection)
                        else hydpy.pub.selections[sel]
                        for sel in selections
                    )
                )
            self.selections = selections.names
            if self._model is None:
                self.elements = selections.elements
            else:
                self.elements = devicetools.Elements(
                    element
                    for element in selections.elements
                    if str(element.model) == self._model
                )
            if not self.elements:
                raise ValueError(
                    f"Object `{selections}` does not handle any `{self._model}` model "
                    f"instances."
                )
            for element in self.elements:
                control = element.model.parameters.control
                if not hasattr(control, self.parametername):
                    raise RuntimeError(
                        f"Model {objecttools.elementphrase(element.model)} does not "
                        f"define a control parameter named `{self.parametername}`."
                    )
            self.parametertype = type(  # type: ignore[assignment]
                tuple(self.elements)[0].model.parameters.control[self.parametername]
            )
            self.parameterstep = parameterstep  # type: ignore[assignment]
            self._original_parameter_values = self._get_original_parameter_values()
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to initialise the `{type(self).__name__}` rule object "
                f"`{name}`"
            )

    def _get_original_parameter_values(
        self,
    ) -> Tuple[Union[float, Vector[float], Matrix[float]], ...]:
        with hydpy.pub.options.parameterstep(self.parameterstep):
            if self.keyword is None:
                return tuple(par.revert_timefactor(par.value) for par in self)
            return tuple(par.keywordarguments[self.keyword] for par in self)

    @property
    def value(self) -> float:
        """The calibration parameter value.

        Property |Rule.value| ensures that the given value adheres to the defined lower
        and upper boundaries:

        >>> from hydpy import Replace
        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> rule = Replace(name="fc",
        ...                parameter="fc",
        ...                value=100.0,
        ...                lower=50.0,
        ...                upper=200.0,
        ...                model="hland_v1")

        >>> rule.value = 0.0
        >>> rule.value
        50.0

        With option |Options.warntrim| enabled (the default), property |Rule.value|
        also emits a warning like the following:

        >>> from hydpy.core.testtools import warn_later
        >>> with pub.options.warntrim(True), warn_later():
        ...     rule.value = 300.0
        UserWarning: The value of the `Replace` object `fc` must not be smaller than \
`50.0` or larger than `200.0`, but the given value is `300.0`.  Applying the trimmed \
value `200.0` instead.
        >>> rule.value
        200.0
        """
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        if self.lower <= value <= self.upper:
            self._value = value
        else:
            self._value = min(max(value, self.lower), self.upper)
            if hydpy.pub.options.warntrim:
                repr_ = objecttools.repr_
                warnings.warn(
                    f"The value of the `{type(self).__name__}` object `{self}` must "
                    f"not be smaller than `{repr_(self.lower)}` or larger than "
                    f"`{repr_(self.upper)}`, but the given value is `{repr_(value)}`.  "
                    f"Applying the trimmed value `{repr_(self._value)}` instead."
                )

    @abc.abstractmethod
    def apply_value(self) -> None:
        """Apply the current value to the relevant |Parameter| objects.

        To be overridden by the concrete subclasses.
        """

    def _update_parameter(
        self,
        parameter: parametertools.Parameter,
        value: Union[float, Vector[float], Matrix[float]],
    ) -> None:
        if self.keyword is None:
            parameter(value)
        else:
            keywordarguments = parameter.keywordarguments
            keywordarguments.valid = True
            keywordarguments[self.keyword] = value
            parameter(**dict(keywordarguments))

    def reset_parameters(self) -> None:
        """Reset all relevant parameter objects to their original states.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import Replace
        >>> rule = Replace(name="fc",
        ...                parameter="fc",
        ...                value=100.0,
        ...                model="hland_v1")
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
                self._update_parameter(parameter, orig)

    @property
    def parameterstep(self) -> Optional[timetools.Period]:
        """The parameter step size relevant to the related model parameter.

        For non-time-dependent parameters, property |Rule.parameterstep| is (usually)
        |None|.
        """
        return self._parameterstep

    @parameterstep.setter
    def parameterstep(self, value: Optional[timetools.PeriodConstrArg]) -> None:
        if self.keyword is None:
            time_ = self.parametertype.TIME
        else:
            keyword = self.parametertype.KEYWORDS.get(self.keyword, None)
            time_ = self.parametertype.TIME if keyword is None else keyword.time
        if time_ is None:
            self._parameterstep = None
        else:
            if value is None:
                value = hydpy.pub.options.parameterstep
                try:
                    value.check()
                except RuntimeError:
                    raise RuntimeError(
                        "Rules which handle time-dependent parameters require "
                        "information on the parameter timestep size.  Either assign "
                        "it directly or define it via option `parameterstep`."
                    ) from None
            self._parameterstep = timetools.Period(value)

    def assignrepr(self, prefix: str, indent: int = 0) -> str:
        """Return a string representation of the actual |Rule| object prefixed with the
        given string."""

        def _none_or_string(obj: object) -> str:
            return f'"{obj}"' if obj else str(obj)

        blanks = (indent + 4) * " "
        selprefix = f"{blanks}selections="
        selline = objecttools.assignrepr_tuple(
            values=tuple(f'"{sel}"' for sel in self.selections),
            prefix=selprefix,
        )
        return (
            f"{prefix}{type(self).__name__}(\n"
            f'{blanks}name="{self}",\n'
            f'{blanks}parameter="{self.parametername}",\n'
            f"{blanks}value={objecttools.repr_(self.value)},\n"
            f"{blanks}lower={objecttools.repr_(self.lower)},\n"
            f"{blanks}upper={objecttools.repr_(self.upper)},\n"
            f"{blanks}keyword={_none_or_string(self.keyword)},\n"
            f"{blanks}parameterstep={_none_or_string(self.parameterstep)},\n"
            f"{blanks}model={_none_or_string(self._model)},\n"
            f"{selline},\n"
            f"{indent*' '})"
        )

    def __repr__(self) -> str:
        return self.assignrepr(prefix="")

    def __str__(self) -> str:
        return self.name

    def __iter__(self) -> Iterator[TypeParameter]:
        for element in self.elements:
            yield element.model.parameters.control[self.parametername]


class Replace(Rule[parametertools.Parameter]):
    """|Rule| class, which simply replaces the current model parameter value(s) with
    the current calibration parameter value.

    See the documentation on class |Rule| for further information.
    """

    adaptor: Optional[Adaptor] = None
    """An optional function object for customising individual calibration strategies.

    See the documentation on the classes |Rule|, |SumAdaptor|, and |FactorAdaptor| for 
    further information.
    """

    def apply_value(self) -> None:
        """Apply the current value to the relevant |Parameter| objects.

        See the documentation on class |Rule| for further information.
        """
        opt = hydpy.pub.options
        with opt.parameterstep(self.parameterstep):  # pylint: disable=not-callable
            for parameter in self:
                if self.adaptor:
                    self.adaptor(parameter)  # pylint: disable=not-callable
                else:
                    self._update_parameter(parameter, self.value)


class Add(Rule[parametertools.Parameter]):
    """|Rule| class, which adds its calibration delta to the original model parameter
    value(s).

    Please read the examples of the documentation on class |Rule| first.  Here, we
    modify some of these examples to show the unique features of class |Add|.

    The first example deals with the non-time-dependent parameter |hland_control.FC|.
    The following |Add| object adds its current value to the parameter's original
    values:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import Add
    >>> rule = Add(name="fc",
    ...            parameter="fc",
    ...            value=100.0,
    ...            model="hland_v1")
    >>> fc = hp.elements.land_lahn_1.model.parameters.control.fc
    >>> fc
    fc(206.0)
    >>> rule.apply_value()
    >>> fc
    fc(306.0)

    When specifying the keyword `field`, the |Add| rule modifies the field capacity of
    zones of type |hland_constants.FIELD| only:

    >>> fc(206.0)
    >>> rule = Add(name="fc",
    ...            parameter="fc",
    ...            value=100.0,
    ...            keyword="field",
    ...            model="hland_v1")
    >>> rule.apply_value()
    >>> fc
    fc(field=306.0, forest=206.0)

    The second example deals with the time-dependent parameter |hland_control.CFMax|
    and shows that everything works even when the actual |Options.parameterstep|
    (2 days) differs from the current |Options.simulationstep| (1 day):

    >>> rule = Add(name="cfmax",
    ...            parameter="cfmax",
    ...            value=2.0,
    ...            model="hland_v1",
    ...            parameterstep="2d")
    >>> cfmax = hp.elements.land_lahn_1.model.parameters.control.cfmax
    >>> cfmax
    cfmax(field=5.0, forest=3.0)
    >>> rule.apply_value()
    >>> cfmax
    cfmax(field=6.0, forest=4.0)

    This time, we modify the |hland_constants.FOREST| zones only:

    >>> cfmax(field=5.0, forest=3.0)
    >>> rule = Add(name="cfmax",
    ...            parameter="cfmax",
    ...            value=2.0,
    ...            keyword="forest",
    ...            model="hland_v1",
    ...            parameterstep="2d")
    >>> rule.apply_value()
    >>> cfmax
    cfmax(field=5.0, forest=4.0)

    In the third example, we modify the scalar parameter |musk_control.NmbSegments| by
    its optional keyword argument `lag`:

    >>> rule = Add(name="lag",
    ...            parameter="nmbsegments",
    ...            value=1.0,
    ...            keyword="lag",
    ...            model="musk_classic",
    ...            parameterstep="2d")
    >>> nmbsegments = \
hp.elements.stream_lahn_1_lahn_2.model.parameters.control.nmbsegments
    >>> nmbsegments
    nmbsegments(lag=0.583)
    >>> rule.apply_value()
    >>> nmbsegments
    nmbsegments(lag=2.583)
    """

    def apply_value(self) -> None:
        """Apply the current (adapted) value to the relevant |Parameter| objects."""
        with hydpy.pub.options.parameterstep(self.parameterstep):
            for parameter, orig in zip(self, self._original_parameter_values):
                self._update_parameter(parameter, self.value + orig)


class Multiply(Rule[parametertools.Parameter]):
    """|Rule| class for multiplying the original model parameter value(s) by its
    calibration factor.

    Please read the examples of the documentation on class |Rule| first.  Here, we
    modify some of these examples to show the unique features of class |Multiply|.

    The first example deals with the non-time-dependent parameter |hland_control.FC|.
    The following |Multiply| object multiplies the parameter's original values by its
    current calibration factor:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import Add
    >>> rule = Multiply(name="fc",
    ...                 parameter="fc",
    ...                 value=2.0,
    ...                 model="hland_v1")
    >>> fc = hp.elements.land_lahn_1.model.parameters.control.fc
    >>> fc
    fc(206.0)
    >>> rule.apply_value()
    >>> fc
    fc(412.0)

    When specifying the keyword `field`, the |Multiply| rule modifies the field
    capacity of zones of type |hland_constants.FIELD| only:

    >>> fc(206.0)
    >>> rule = Multiply(name="fc",
    ...            parameter="fc",
    ...            value=2.0,
    ...            keyword="field",
    ...            model="hland_v1")
    >>> rule.apply_value()
    >>> fc
    fc(field=412.0, forest=206.0)

    The second example deals with the time-dependent parameter |hland_control.CFMax|
    and shows that everything works even when the actual |Options.parameterstep|
    (2 days) differs from the current |Options.simulationstep| (1 day):

    >>> rule = Multiply(name="cfmax",
    ...                 parameter="cfmax",
    ...                 value=2.0,
    ...                 model="hland_v1",
    ...                 parameterstep="2d")
    >>> cfmax = hp.elements.land_lahn_1.model.parameters.control.cfmax
    >>> cfmax
    cfmax(field=5.0, forest=3.0)
    >>> rule.apply_value()
    >>> cfmax
    cfmax(field=10.0, forest=6.0)

    This time, we modify the |hland_constants.FOREST| zones only:

    >>> cfmax(field=5.0, forest=3.0)
    >>> rule = Multiply(name="cfmax",
    ...                 parameter="cfmax",
    ...                 value=2.0,
    ...                 keyword="forest",
    ...                 model="hland_v1",
    ...                 parameterstep="2d")
    >>> cfmax
    cfmax(field=5.0, forest=3.0)
    >>> rule.apply_value()
    >>> cfmax
    cfmax(field=5.0, forest=6.0)

    In the third example, we modify the scalar parameter |musk_control.NmbSegments| by
    its optional keyword argument `lag`:

    >>> rule = Multiply(name="lag",
    ...            parameter="nmbsegments",
    ...            value=2.0,
    ...            keyword="lag",
    ...            model="musk_classic",
    ...            parameterstep="2d")
    >>> nmbsegments = \
hp.elements.stream_lahn_1_lahn_2.model.parameters.control.nmbsegments
    >>> nmbsegments
    nmbsegments(lag=0.583)
    >>> rule.apply_value()
    >>> nmbsegments
    nmbsegments(lag=1.166)
    """

    def apply_value(self) -> None:
        """Apply the current (adapted) value to the relevant |Parameter| objects."""
        with hydpy.pub.options.parameterstep(self.parameterstep):
            for parameter, orig in zip(self, self._original_parameter_values):
                self._update_parameter(parameter, self.value * orig)


class CalibrationInterface(Generic[TypeRule1]):
    """Interface for the coupling of *HydPy* to optimisation libraries like `NLopt`_.

    Essentially, class |CalibrationInterface| is supposed for the structured handling
    of multiple objects of the different |Rule| subclasses.  Hence, please read the
    documentation on class |Rule| before continuing, on which we base the following
    explanations.

    We work with the `Lahn` example project again:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    First, we create a |CalibrationInterface| object.  Initially, it needs to know the
    relevant |HydPy| object and the target or objective function (here, we define the
    target function sloppily via the `lambda` statement; see the documentation on the
    protocol class |TargetFunction| for a more formal definition and further
    explanations):

    >>> from hydpy import CalibrationInterface, nse
    >>> ci = CalibrationInterface(
    ...     hp=hp,
    ...     targetfunction=lambda: sum(nse(node=node) for node in hp.nodes))

    Next, we use function |make_rules|, which creates one |Replace| rule related to
    parameter |hland_control.FC| and another one related to parameter
    |hland_control.PercMax| in one step, and add them via method
    |CalibrationInterface.add_rules|:

    >>> from hydpy import Replace
    >>> from hydpy.auxs.calibtools import make_rules
    >>> ci.add_rules(*make_rules(rule=Replace,
    ...                          names=["fc", "percmax"],
    ...                          parameters=["fc", "percmax"],
    ...                          values=[100.0, 5.0],
    ...                          keywords=[None, None],
    ...                          lowers=[50.0, 1.0],
    ...                          uppers=[200.0, 10.0],
    ...                          parametersteps="1d",
    ...                          model="hland_v1"))

    >>> print(ci)
    CalibrationInterface
    >>> ci
    Replace(
        name="fc",
        parameter="fc",
        value=100.0,
        lower=50.0,
        upper=200.0,
        keyword=None,
        parameterstep=None,
        model="hland_v1",
        selections=("complete",),
    )
    Replace(
        name="percmax",
        parameter="percmax",
        value=5.0,
        lower=1.0,
        upper=10.0,
        keyword=None,
        parameterstep="1d",
        model="hland_v1",
        selections=("complete",),
    )

    Adding rules later does not remove already available ones.  For demonstration, we
    add one for calibrating parameter |musk_control.Coefficients| of application model
    |musk_classic| via its keyword `damp`:

    >>> len(ci)
    2
    >>> ci.add_rules(Replace(name="damp",
    ...                      parameter="coefficients",
    ...                      value=0.2,
    ...                      lower=0.0,
    ...                      upper=0.5,
    ...                      keyword="damp",
    ...                      selections=["complete"],
    ...                      model="musk_classic"))
    >>> len(ci)
    3

    All rules are available via attribute and keyword access:

    >>> ci.fc
    Replace(
        name="fc",
        parameter="fc",
        value=100.0,
        lower=50.0,
        upper=200.0,
        keyword=None,
        parameterstep=None,
        model="hland_v1",
        selections=("complete",),
    )

    >>> ci.FC
    Traceback (most recent call last):
    ...
    AttributeError: The actual calibration interface does neither handle a normal \
attribute nor a rule object named `FC`.

    >>> ci["damp"]
    Replace(
        name="damp",
        parameter="coefficients",
        value=0.2,
        lower=0.0,
        upper=0.5,
        keyword="damp",
        parameterstep=None,
        model="musk_classic",
        selections=("complete",),
    )

    >>> ci["Damp"]
    Traceback (most recent call last):
    ...
    KeyError: 'The actual calibration interface does not handle a rule object named \
`Damp`.'

    The following properties return consistently sorted information on the handles
    |Rule| objects:

    >>> ci.names
    ('fc', 'percmax', 'damp')
    >>> ci.keywords
    (None, None, 'damp')
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

    For the following examples, we perform a simulation run and assign the values of
    the simulated time series to the observed series:

    >>> conditions = hp.conditions
    >>> hp.simulate()
    >>> for node in hp.nodes:
    ...     node.sequences.obs.series = node.sequences.sim.series
    >>> hp.conditions = conditions

    As the agreement between the simulated and the "observed" time series is perfect
    for all four gauges, method |CalibrationInterface.calculate_likelihood| returns the
    highest possible sum of four |nse| values and also stores it under the attribute
    `result`:

    >>> from hydpy import round_
    >>> round_(ci.calculate_likelihood())
    4.0
    >>> round_(ci.result)
    4.0

    When performing a manual calibration, it might be convenient to use method
    |CalibrationInterface.apply_values|.  To explain how it works, we first show the
    values of the relevant parameters of some randomly selected model instances:

    >>> stream = hp.elements.stream_lahn_1_lahn_2.model
    >>> stream.parameters.control
    nmbsegments(lag=0.583)
    coefficients(damp=0.0)
    >>> land = hp.elements.land_lahn_1.model
    >>> land.parameters.control.fc
    fc(206.0)
    >>> land.parameters.control.percmax
    percmax(1.02978)

    Method |CalibrationInterface.apply_values| of class |CalibrationInterface| calls
    method |Rule.apply_value| of all handled |Rule| objects, performs some preparations
    (for example, it derives the values of the secondary parameters), executes a
    simulation run, calls method |CalibrationInterface.calculate_likelihood|, and
    returns the result:

    >>> result = ci.apply_values()
    >>> stream.parameters.control
    nmbsegments(lag=0.583)
    coefficients(damp=0.3)
    >>> land.parameters.control.fc
    fc(100.0)
    >>> land.parameters.control.percmax
    percmax(5.0)

    Due to the changes in our parameter values, our simulation is not "perfect"
    anymore:

    >>> round_(ci.result)
    1.605136

    Use method |CalibrationInterface.reset_parameters| to restore the initial states of
    all affected parameters:

    >>> ci.reset_parameters()
    >>> stream.parameters.control
    nmbsegments(lag=0.583)
    coefficients(damp=0.0)
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

    Note the `perform_simulation` argument of method
    |CalibrationInterface.apply_values|, which allows changing the model parameter
    values and updating the |HydPy| object only without triggering a simulation run
    (and to calculate and return a new likelihood value):

    >>> ci.apply_values(perform_simulation=False)
    >>> stream.parameters.control
    nmbsegments(lag=0.583)
    coefficients(damp=0.3)
    >>> land.parameters.control.fc
    fc(100.0)
    >>> land.parameters.control.percmax
    percmax(5.0)

    Optimisers, like those implemented in `NLopt`_, often provide their new parameter
    estimates via vectors.  Method |CalibrationInterface.perform_calibrationstep|
    accepts such vectors and updates the handled |Rule| objects accordingly.  After
    that, it performs the same steps as described for method
    |CalibrationInterface.apply_values|:

    >>> round_(ci.perform_calibrationstep([100.0, 5.0, 0.3]))
    1.605136

    >>> stream.parameters.control
    nmbsegments(lag=0.583)
    coefficients(damp=0.3)

    >>> land.parameters.control.fc
    fc(100.0)
    >>> land.parameters.control.percmax
    percmax(5.0)

    Method |CalibrationInterface.perform_calibrationstep| writes intermediate results
    into a log file, if available.  Prepare it beforehand via method
    |CalibrationInterface.prepare_logfile|:

    >>> with TestIO():
    ...     ci.prepare_logfile(logfilepath="example_calibration.log",
    ...                        objectivefunction="NSE",
    ...                        documentation="Just a doctest example.")

    To continue "manually", we now can call method
    |CalibrationInterface.update_logfile| to write the lastly calculated efficiency and
    the corresponding calibration parameter values to the log file:

    >>> with TestIO():   # doctest: +NORMALIZE_WHITESPACE
    ...     ci.update_logfile()
    ...     with open("example_calibration.log") as file_:
    ...         print(file_.read())
    # Just a doctest example.
    <BLANKLINE>
    NSE           fc    percmax damp
    parameterstep None	1d      None
    1.605136      100.0 5.0     0.3
    <BLANKLINE>

    To prevent (automatic) calibration runs from crashing due to IO problems, method
    |CalibrationInterface.update_logfile| raises warnings instead of errors in such
    cases and logs the inwritten data internally:

    >>> import os
    >>> from hydpy.core.testtools import warn_later
    >>> with TestIO(), warn_later():
    ...     ci._logfilepath = "dirname1/filename.log"
    ...     ci.update_logfile()
    UserWarning: While trying to update the logfile `dirname1/filename.log`, the \
following problem occured: [Errno 2] No such file or directory: 'dirname1/filename.log'.

    On subsequent calls, it tries to write both the previously logged and the new data:

    >>> with TestIO():   # doctest: +NORMALIZE_WHITESPACE
    ...     os.makedirs("dirname1", exist_ok=True)
    ...     ci.update_logfile()
    ...     with open("dirname1/filename.log") as file_:
    ...         print(file_.read())
    1.605136 100.0 5.0 0.3
    1.605136 100.0 5.0 0.3
    <BLANKLINE>

    Call method |CalibrationInterface.finalise_logfile| to ensure the
    |CalibrationInterface| object does not withhold data after the end of a calibration
    run.  If you do so, it sleeps until it gets the chance to write the logged data and
    warns you about this problem from time to time (we demonstrate this by mocking the
    |warnings.warn| function and, to keep our test example awake, the |time.sleep|
    function):

    >>> with TestIO():
    ...     ci._logfilepath = "dirname2/filename.log"
    ...     ci.update_logfile()
    Traceback (most recent call last):
    ...
    UserWarning: While trying to update the logfile `dirname2/filename.log`, the \
following problem occured: [Errno 2] No such file or directory: 'dirname2/filename.log'.
    >>> from unittest import mock
    >>> with TestIO():
    ...     with mock.patch("time.sleep") as mocked:
    ...         mocked.side_effect = Exception("time.sleep actually called")
    ...         ci.finalise_logfile()
    Traceback (most recent call last):
    ...
    UserWarning: Trying to finalise logfile `dirname2/filename.log` failed 1 times.
    >>> with TestIO():
    ...     with mock.patch("warnings.warn"), mock.patch("time.sleep") as mocked:
    ...         mocked.side_effect = Exception("time.sleep actually called")
    ...         ci.finalise_logfile()
    Traceback (most recent call last):
    ...
    Exception: time.sleep actually called
    >>> with TestIO():   # doctest: +NORMALIZE_WHITESPACE
    ...     os.makedirs("dirname2", exist_ok=True)
    ...     ci.finalise_logfile()
    ...     with open("dirname2/filename.log") as file_:
    ...         print(file_.read())
    1.605136 100.0 5.0 0.3
    <BLANKLINE>

    >>> ci._logfilepath = "example_calibration.log"

    For automatic calibration, one needs a calibration algorithm like the following,
    which checks the lower and upper boundaries and the initial values of all |Rule|
    objects:

    >>> def find_max(function, lowers, uppers, inits):
    ...     best_result = -999.0
    ...     best_parameters = None
    ...     for values in (lowers, uppers, inits):
    ...         result = function(values)
    ...         if result > best_result:
    ...             best_result = result
    ...             best_parameters = values
    ...     return best_parameters

    Now we can assign method |CalibrationInterface.perform_calibrationstep| to this
    oversimplified optimiser, which then returns the best examined calibration
    parameter values:

    >>> with TestIO():
    ...     find_max(function=ci.perform_calibrationstep,
    ...              lowers=ci.lowers,
    ...              uppers=ci.uppers,
    ...              inits=ci.values)
    (200.0, 10.0, 0.5)

    The log file now contains one line for our old result and three lines for the
    results of our optimiser:

    >>> with TestIO():   # doctest: +NORMALIZE_WHITESPACE
    ...     with open("example_calibration.log") as file_:
    ...         print(file_.read())
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
    |CalibrationInterface.read_logfile|, which automatically selects the best
    calibration result.  Therefore, it needs to know that the highest result is the
    best, which we indicate by setting argument `maximisation` to |True|:

    >>> with TestIO():
    ...     ci.read_logfile(logfilepath="example_calibration.log", maximisation=True)
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
    |CalibrationInterface.read_logfile| returns the worst result in our example:

    >>> with TestIO():
    ...     ci.read_logfile(logfilepath="example_calibration.log", maximisation=False)
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
    |CalibrationInterface.read_logfile| raises the following error whenever it detects
    inconsistencies:

    >>> ci.percmax.parameterstep = "2d"
    >>> with TestIO():
    ...     ci.read_logfile(logfilepath="example_calibration.log",maximisation=True)
    Traceback (most recent call last):
    ...
    RuntimeError: The current parameterstep of the `Replace` rule `percmax` (`2d`) \
does not agree with the one documentated in log file `example_calibration.log` (`1d`).

    Method |CalibrationInterface.read_logfile| reports inconsistent rule names as
    follows:

    >>> ci.remove_rules(ci.percmax)
    >>> with TestIO():
    ...     ci.read_logfile(logfilepath="example_calibration.log",maximisation=True)
    Traceback (most recent call last):
    ...
    RuntimeError: The names of the rules handled by the actual calibration interface \
(damp and fc) do not agree with the names in the header of logfile \
`example_calibration.log` (damp, fc, and percmax).

    The last consistency check is optional.  Set argument `check` to |False| to force
    method |CalibrationInterface.read_logfile| to query all available data instead of
    raising an error:

    >>> ci.add_rules(Replace(name="beta",
    ...                      parameter="beta",
    ...                      value=2.0,
    ...                      lower=1.0,
    ...                      upper=4.0,
    ...                      selections=["complete"],
    ...                      model="hland_v1"))
    >>> ci.fc.value = 0.0
    >>> ci.damp.value = 0.0
    >>> with TestIO():
    ...     ci.read_logfile(
    ...         logfilepath="example_calibration.log",
    ...         maximisation=True,
    ...         check=False,
    ...     )
    >>> ci.beta.value
    2.0
    >>> ci.fc.value
    200.0
    >>> ci.damp.value
    0.5
    """

    result: Optional[float]
    """The last result, as calculated by the target function."""
    conditions: hydpytools.ConditionsType
    """The |HydPy.conditions| of the given |HydPy| object.

    |CalibrationInterface| queries the conditions during its initialisation and uses 
    them later to reset all relevant conditions before each new simulation run.
    """
    _logfilepath: Optional[str]
    _logfilelines: Deque[str]
    _hp: hydpytools.HydPy
    _targetfunction: TargetFunction
    _rules: Dict[str, TypeRule1]
    _elements: devicetools.Elements

    def __init__(self, hp: hydpytools.HydPy, targetfunction: TargetFunction) -> None:
        self._hp = hp
        self._targetfunction = targetfunction
        self.conditions = hp.conditions
        self._rules = {}
        self._elements = devicetools.Elements()
        self._logfilepath = None
        self._logfilelines = collections.deque()
        self.result = None

    def add_rules(self, *rules: TypeRule1) -> None:
        """Add some |Rule| objects to the actual |CalibrationInterface| object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(hp=hp, targetfunction=lambda: None)
        >>> from hydpy import Replace
        >>> ci.add_rules(Replace(name="fc",
        ...                      parameter="fc",
        ...                      value=100.0,
        ...                      model="hland_v1"),
        ...              Replace(name="percmax",
        ...                      parameter="percmax",
        ...                      value=5.0,
        ...                      model="hland_v1"))

        Note that method |CalibrationInterface.add_rules| might change the number of
        |Element| objects relevant for the |CalibrationInterface| object:

        >>> damp = Replace(name="damp",
        ...                parameter="coefficients",
        ...                value=0.2,
        ...                keyword="damp",
        ...                model="musk_classic")
        >>> len(ci._elements)
        4
        >>> ci.add_rules(damp)
        >>> len(ci._elements)
        7
        """
        for rule in rules:
            self._rules[rule.name] = rule
            self._update_elements_when_adding_a_rule(rule)

    @overload
    def get_rule(self, name: str) -> TypeRule1:
        ...

    @overload
    def get_rule(self, name: str, type_: Type[TypeRule2]) -> TypeRule2:
        ...

    def get_rule(
        self, name: str, type_: Optional[Type[TypeRule2]] = None
    ) -> Union[TypeRule1, TypeRule2]:
        """Return a |Rule| object (of a specific type).

        Method |CalibrationInterface.get_rule| is a more typesafe alternative to simple
        keyword access. Besides the name of the required |Rule| object, pass its
        subclass to convince your IDE (and yourself) that the returned rule follows
        this more specific type:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import Add, CalibrationInterface, make_rules, nse, Replace
        >>> ci = CalibrationInterface(
        ...     hp=hp,
        ...     targetfunction=lambda: sum(nse(node=node) for node in hp.nodes))
        >>> ci.add_rules(*make_rules(rule=Replace,
        ...                          names=["fc", "percmax"],
        ...                          parameters=["fc", "percmax"],
        ...                          values=[100.0, 5.0],
        ...                          keywords=["forest", None],
        ...                          lowers=[50.0, 1.0],
        ...                          uppers=[200.0, 10.0],
        ...                          parametersteps="1d",
        ...                          model="hland_v1"))

        >>> ci.get_rule("fc", Replace).name
        'fc'

        >>> ci.get_rule("Fc", Replace).name
        Traceback (most recent call last):
        ...
        RuntimeError: The actual calibration interface does not handle a rule object \
named `Fc`.

        >>> ci.get_rule("fc", Replace).name
        'fc'

        >>> ci.get_rule("fc", Add).name
        Traceback (most recent call last):
        ...
        RuntimeError: The actual calibration interface does not handle a rule object \
named `fc` of type `Add`.
        """
        try:
            rule = self._rules[name]
        except KeyError:
            raise RuntimeError(
                f"The actual calibration interface does not handle a rule object "
                f"named `{name}`."
            ) from None
        if (type_ is None) or isinstance(rule, type_):
            return rule
        raise RuntimeError(
            f"The actual calibration interface does not handle a rule object named "
            f"`{name}` of type `{type_.__name__}`."
        )

    def remove_rules(self, *rules: Union[str, TypeRule1]) -> None:
        """Remove some |Rule| objects from the actual |CalibrationInterface| object.

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(hp=hp, targetfunction=lambda: None)
        >>> from hydpy import Replace
        >>> ci.add_rules(Replace(name="fc",
        ...                      parameter="fc",
        ...                      value=100.0,
        ...                      model="hland_v1"),
        ...              Replace(name="percmax",
        ...                      parameter="percmax",
        ...                      value=5.0,
        ...                      model="hland_v1"),
        ...              Replace(name="damp",
        ...                      parameter="coefficients",
        ...                      value=0.2,
        ...                      keyword="damp",
        ...                      model="musk_classic"))

        You can remove each rule either by passing itself or its name (note that method
        |CalibrationInterface.remove_rules| might change the number of |Element|
        objects relevant for the |CalibrationInterface| object):

        >>> len(ci._elements)
        7
        >>> fc = ci.fc
        >>> fc in ci
        True
        >>> "damp" in ci
        True
        >>> ci.remove_rules(fc, "damp")
        >>> fc in ci
        False
        >>> "damp" in ci
        False
        >>> len(ci._elements)
        4

        Trying to remove a non-existing rule results in the following error:

        >>> ci.remove_rules("fc")
        Traceback (most recent call last):
        ...
        RuntimeError: The actual calibration interface object does not handle a rule \
object named `fc`.
        """
        for rule in rules:
            if not isinstance(rule, str):
                rule = rule.name
            try:
                del self._rules[rule]
            except KeyError:
                raise RuntimeError(
                    f"The actual calibration interface object does not handle a rule "
                    f"object named `{rule}`."
                ) from None
        self._update_elements_when_deleting_a_rule()

    def prepare_logfile(
        self,
        logfilepath: str,
        objectivefunction: str = "result",
        documentation: Optional[str] = None,
    ) -> None:
        """Prepare a log file.

        Use argument `objectivefunction` to describe the |TargetFunction| used for
        calculating the efficiency and argument `documentation` to add some information
        to the header of the logfile.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        self._logfilepath = logfilepath
        self._logfilelines = collections.deque()
        with open(logfilepath, "w", encoding=config.ENCODING) as logfile:
            if documentation:
                lines = (f"# {line}" for line in documentation.split("\n"))
                logfile.write("\n".join(lines))
                logfile.write("\n\n")
            logfile.write(f"{objectivefunction}\t")
            names = (rule.name for rule in self)
            logfile.write("\t".join(names))
            logfile.write("\n")
            steps = [str(rule.parameterstep) for rule in self]
            logfile.write("\t".join(["parameterstep"] + steps))
            logfile.write("\n")

    def update_logfile(self) -> None:
        """Update the current log file, if available.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        if self._logfilepath:
            result = objecttools.repr_(self.result)
            values = "\t".join(objecttools.repr_(value) for value in self.values)
            self._logfilelines.append(f"{result}\t{values}\n")
            try:
                self._write_data_into_logfile()
            except BaseException as exc:
                warnings.warn(
                    f"While trying to update the logfile `{self._logfilepath}`, the "
                    f"following problem occured: {exc}."
                )

    def finalise_logfile(self) -> None:
        """Update the current log file if method |CalibrationInterface.update_logfile|
        was not entirely successful in doing so.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        if self._logfilepath:
            counter = 0
            while self._logfilelines:
                try:
                    self._write_data_into_logfile()
                except BaseException:
                    counter += 1
                    warnings.warn(
                        f"Trying to finalise logfile `{self._logfilepath}` failed "
                        f"{counter} times."
                    )
                    time.sleep(10.0)

    def _write_data_into_logfile(self) -> None:
        assert self._logfilepath
        with open(self._logfilepath, "a", encoding=config.ENCODING) as logfile:
            while self._logfilelines:
                logfile.write(self._logfilelines.popleft())

    def read_logfile(
        self, logfilepath: str, maximisation: bool, check: bool = True
    ) -> None:
        """Read the log file with the given file path.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        with open(logfilepath, encoding=config.ENCODING) as logfile:
            # pylint: disable=not-an-iterable
            # because pylint is sometimes wrong about this
            lines = tuple(
                line for line in logfile if line.strip() and (not line.startswith("#"))
            )
            # pylint: enable=not-an-iterable
        idx2name, idx2rule = {}, {}
        parameterstep: Optional[Union[str, timetools.Period]]
        for idx, (name, parameterstep) in enumerate(
            zip(lines[0].split()[1:], lines[1].split()[1:]),
        ):
            if name in self._rules:
                rule = self._rules[name]
                if parameterstep == "None":
                    parameterstep = None
                else:
                    parameterstep = timetools.Period(parameterstep)
                if parameterstep != rule.parameterstep:
                    raise RuntimeError(
                        f"The current parameterstep of the `{type(rule).__name__}` "
                        f"rule `{rule.name}` (`{rule.parameterstep}`) does not agree "
                        f"with the one documentated in log file `{self._logfilepath}` "
                        f"(`{parameterstep}`)."
                    )
                idx2rule[idx] = rule
            idx2name[idx] = name
        if check:
            names_int = set(self.names)
            names_ext = set(idx2name.values())
            if names_int != names_ext:
                enumeration = objecttools.enumeration
                raise RuntimeError(
                    f"The names of the rules handled by the actual calibration "
                    f"interface ({enumeration(sorted(names_int))}) do not agree with "
                    f"the names in the header of logfile `{self._logfilepath}` "
                    f"({enumeration(sorted(names_ext))})."
                )
        jdx_best = 0
        result_best = -numpy.inf if maximisation else numpy.inf
        for jdx, line in enumerate(lines[2:]):
            result = float(line.split()[0])
            if (maximisation and (result > result_best)) or (
                (not maximisation) and (result < result_best)
            ):
                jdx_best = jdx
                result_best = result

        for idx, value in enumerate(lines[jdx_best + 2].split()[1:]):
            if idx in idx2rule:
                idx2rule[idx].value = float(value)
        self.result = result_best

    def _update_elements_when_adding_a_rule(self, rule: TypeRule1) -> None:
        self._elements += rule.elements

    def _update_elements_when_deleting_a_rule(self) -> None:
        self._elements = devicetools.Elements()
        for rule in self:
            self._elements += rule.elements

    @property
    def names(self) -> Tuple[str, ...]:
        """The names of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        return tuple(rule.name for rule in self)

    @property
    def values(self) -> Tuple[float, ...]:
        """The values of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        return tuple(rule.value for rule in self)

    @property
    def keywords(self) -> Tuple[Optional[str], ...]:
        """The (optional) target keywords of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        return tuple(rule.keyword for rule in self)

    @property
    def lowers(self) -> Tuple[float, ...]:
        """The lower boundaries of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        return tuple(rule.lower for rule in self)

    @property
    def uppers(self) -> Tuple[float, ...]:
        """The upper boundaries of all handled |Rule| objects.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        return tuple(rule.upper for rule in self)

    @property
    def selections(self) -> Tuple[str, ...]:
        """The names of all |Selection| objects addressed at least one of the handled
        |Rule| objects.

        See the documentation on function |make_rules| for further information.
        """
        return tuple(
            sorted(set(itertools.chain.from_iterable(rule.selections for rule in self)))
        )

    @property
    def parametertypes(
        self,
    ) -> Tuple[Tuple[Type[parametertools.Parameter], Target], ...]:
        """The types of all |Parameter| objects addressed by at least one of the
        handled |Rule| objects.

        See the documentation on function |make_rules| for further information.
        """
        parametertypes: List[Tuple[Type[parametertools.Parameter], Target]] = []
        for rule in self:
            if isinstance(rule, RuleIUH):
                parametertypes.append((rule.parametertype, rule.target))
            else:
                parametertypes.append((rule.parametertype, None))
        return variabletools.sort_variables(set(parametertypes))

    def _update_values(self, values: Iterable[float]) -> None:
        for rule, value in zip(self, values):
            rule.value = value

    def _refresh_hp(self) -> None:
        for element in self._elements:
            element.model.parameters.update()
        self._hp.conditions = self.conditions

    @overload
    def apply_values(self, perform_simulation: Literal[True] = ...) -> float:
        ...

    @overload
    def apply_values(self, perform_simulation: Literal[False]) -> None:
        ...

    def apply_values(self, perform_simulation: bool = True) -> Optional[float]:
        """Apply all current calibration parameter values on all relevant parameters.

        Set argument `perform_simulation` to |False| to only change the actual
        parameter values and update the |HydPy| object without performing a simulation
        run.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        for rule in self:
            rule.apply_value()
        self._refresh_hp()
        if perform_simulation:
            self._hp.simulate()
            return self.calculate_likelihood()
        return None

    def reset_parameters(self) -> None:
        """Reset all relevant parameters to their original states.

        See the main documentation on class |CalibrationInterface| for further
         information.
        """
        for rule in self:
            rule.reset_parameters()
        self._refresh_hp()

    def calculate_likelihood(self) -> float:
        """Apply the defined |TargetFunction| and return the result.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        self.result = self._targetfunction()
        return self.result

    def perform_calibrationstep(
        self,
        values: Iterable[float],
        *args: Any,
        **kwargs: Any,
    ) -> float:
        # pylint: disable=unused-argument
        # for optimisers that pass additional informative data
        """Update all calibration parameters with the given values, update the |HydPy|
        object, perform a simulation run, and calculate and return the achieved
        efficiency.

        See the main documentation on class |CalibrationInterface| for further
        information.
        """
        self._update_values(values)
        likelihood = self.apply_values()
        self.update_logfile()
        return likelihood

    def print_table(
        self,
        parametertypes: Optional[
            Sequence[
                Union[
                    Type[parametertools.Parameter],
                    Tuple[Type[parametertools.Parameter], Target],
                ]
            ]
        ] = None,
        selections: Optional[Sequence[str]] = None,
        bounds: Optional[Tuple[str, str]] = ("lower", "upper"),
        fillvalue: str = "/",
        sep: str = "\t",
        file_: Optional[TextIO] = None,
    ) -> None:
        """Print the current calibration parameter values in a table format.

        The following examples combine the base examples of the documentation on class
        |CalibrationInterface| and class |ReplaceIUH|, so please make sure to
        understand them before proceeding.

        We again use the `Lahn` example project but replace the |musk_classic| model
        instances with those of application model |arma_v1|, which allows discussing
        some special cases concerning the handling of |RuleIUH|:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import prepare_model
        >>> for element in hp.elements.river:
        ...     element.model = prepare_model("arma_v1")
        ...     element.model.parameters.control.responses([[], [1.0]])
        ...     element.model.parameters.update()

        We pass a (useless) dummy target function to the |CalibrationInterface| object:

        >>> from hydpy import CalibrationInterface
        >>> ci = CalibrationInterface(hp=hp, targetfunction=lambda: 1.0)

        Regarding |hland_v1|, we intend to calibrate the parameters |hland_control.FC|
        and |hland_control.PercMax| with different values for the selections
        `headwaters` and `nonheadwaters`:

        >>> from hydpy import CalibSpec, CalibSpecs, make_rules, Replace
        >>> calibspecs = CalibSpecs(
        ...     CalibSpec(name="fc", default=100.0, lower=50.0, upper=200.0),
        ...     CalibSpec(name="percmax", default=5.0, lower=1.0, upper=10.0, \
parameterstep="1d"))
        >>> ci.add_rules(*make_rules(rule=Replace,
        ...                          calibspecs=calibspecs,
        ...                          model="hland_v1",
        ...                          selections=("headwaters", "nonheadwaters"),
        ...                          product=True))

        Regarding |arma_v1|, we cannot calibrate the values of parameter
        |arma_control.Responses| in a meaningful way.  So instead, we use the
        |LinearStorageCascade| as a meta-model and calibrate its parameters
        |LinearStorageCascade.k| and |LinearStorageCascade.n|:

        >>> from hydpy import LinearStorageCascade, ReplaceIUH
        >>> k = ReplaceIUH(name="k_global",
        ...                target="k",
        ...                parameter="responses",
        ...                value=2.0,
        ...                lower=1.0,
        ...                parameterstep="1d",
        ...                selections=("streams",))
        >>> n = ReplaceIUH(name="n_global",
        ...                target="n",
        ...                parameter="responses",
        ...                value=4.0,
        ...                lower=1.0,
        ...                upper=100.0,
        ...                selections=("streams",))
        >>> name2lsc = {element.name: LinearStorageCascade(k=1.0, n=1.0)
        ...             for element in hp.elements.river}
        >>> k.add_iuhs(**name2lsc)
        >>> n.add_iuhs(**name2lsc)
        >>> ci.add_rules(k, n)

        We change the values of two |Rule| objects related to |hland_v1| to clarify
        that all values appear in the correct table cells:

        >>> ci["fc_headwaters"].value = 200.0
        >>> ci["percmax_nonheadwaters"].value = 10.0

        By default, method |CalibrationInterface.print_table| prints the values of all
        handled |Rule| objects.  It varies the target control parameters on the first
        axis and the target selections on the second axis.  Row two and three contain
        the (identical) lower and upper boundary values corresponding to the respective
        control parameters:

        >>> ci.print_table()  # doctest: +NORMALIZE_WHITESPACE
    	              lower  upper  headwaters  nonheadwaters  streams
        k->Responses  1.0   inf     /           /              2.0
        n->Responses  1.0   100.0   /           /              4.0
        FC            50.0   200.0  200.0       100.0          /
        PercMax       1.0    10.0   5.0         10.0           /

        For non-identical boundary values, method |CalibrationInterface.print_table|
        prints fill values in the relevant cells.  Besides this, the following example
        shows how to define alternative titles for the boundary value columns:

        >>> ci["fc_headwaters"].lower = 60.0
        >>> ci["percmax_nonheadwaters"].upper = 20.0
        >>> ci.print_table(bounds=("min", "max"))  # doctest: +NORMALIZE_WHITESPACE
    	              min    max    headwaters  nonheadwaters  streams
        k->Responses  1.0    inf    /          /               2.0
        n->Responses  1.0    100.0  /          /               4.0
        FC              /    200.0  200.0      100.0           /
        PercMax       1.0    /      5.0        10.0            /

        Pass |None| to argument `bounds` to omit writing any boundary value column:

        >>> ci.print_table(bounds=None)  # doctest: +NORMALIZE_WHITESPACE
                      headwaters  nonheadwaters  streams
        k->Responses  /           /              2.0
        n->Responses  /           /              4.0
        FC            200.0       100.0          /
        PercMax       5.0         10.0           /

        The next example shows how to change the tabulated target parameters and
        selections.  Method |CalibrationInterface.print_table| uses the (given
        alternative) fill value for each parameter-selection-combination not met by any
        of the available |Rule| objects.  For |RuleIUH|-related parameters, we must
        specify both the control parameter (as a type, in our example
        |arma_control.Responses|) and the meta-parameter (as a string, in our example
        |LinearStorageCascade.k|) within a |tuple|:

        >>> from hydpy.models.hland.hland_control import CFlux, PercMax
        >>> from hydpy.models.arma.arma_control import Responses
        >>> ci.print_table(  # doctest: +NORMALIZE_WHITESPACE
        ...     parametertypes=(PercMax, CFlux, (Responses, "k")),
        ...     selections=("streams", "headwaters"),
        ...     bounds=None,
        ...     fillvalue="-")
    	              streams  headwaters
        PercMax       -        5.0
        CFlux         -        -
        k->Responses  2.0      -

        Note that the value of the same calibration parameter might appear multiple
        times when targeting multiple |Selection| objects:

        >>> ci["fc_headwaters"].selections = ("headwaters", "streams")
        >>> ci.print_table(bounds=None)  # doctest: +NORMALIZE_WHITESPACE
    	              headwaters  nonheadwaters  streams
        k->Responses  /           /              2.0
        n->Responses  /           /              4.0
        FC            200.0       100.0	         200.0
        PercMax       5.0	      10.0	         /
        """
        none = type("_None", (), {})()
        if parametertypes is None:
            parametertypes_ = self.parametertypes
        else:
            parametertypes_ = tuple(
                item if isinstance(item, tuple) else (item, None)
                for item in parametertypes
            )
        if selections is None:
            selections = self.selections
        delta = 3 if bounds else 1
        table = numpy.full(
            shape=(len(parametertypes_) + 1, (len(selections)) + delta),
            fill_value=fillvalue,
            dtype=object,
        )
        table[0, 0] = ""
        table[1:, 0] = tuple(
            f"{target}->{par.__name__}" if target else par.__name__
            for par, target in parametertypes_
        )
        if bounds:
            table[0, 1:3] = bounds
        table[0, delta:] = selections
        par2idx = {par: idx + 1 for idx, par in enumerate(parametertypes_)}
        sel2jdx = {sel: jdx + delta for jdx, sel in enumerate(selections)}
        for rule in self:
            if isinstance(rule, RuleIUH):
                idx = par2idx.get((rule.parametertype, rule.target))
            else:
                idx = par2idx.get((rule.parametertype, None))
            if idx is not None:
                if bounds:
                    if table[idx, 1] in (fillvalue, rule.lower):
                        table[idx, 1] = rule.lower
                    else:
                        table[idx, 1] = none
                    if table[idx, 2] in (fillvalue, rule.upper):
                        table[idx, 2] = rule.upper
                    else:
                        table[idx, 2] = none
                for selection in rule.selections:
                    jdx = sel2jdx.get(selection)
                    if jdx is not None:
                        table[idx, jdx] = rule.value
        table[table == none] = fillvalue
        for row in table:
            print(*row, sep=sep, file=file_)

    def __len__(self) -> int:
        return len(self._rules)

    def __iter__(self) -> Iterator[TypeRule1]:
        for rule in self._rules.values():
            yield rule

    def __getattr__(self, item: str) -> TypeRule1:
        try:
            return self._rules[item]
        except KeyError:
            raise AttributeError(
                f"The actual calibration interface does neither handle a normal "
                f"attribute nor a rule object named `{item}`."
            ) from None

    def __getitem__(self, key: str) -> TypeRule1:
        try:
            return self._rules[key]
        except KeyError:
            raise KeyError(
                f"The actual calibration interface does not handle a rule object "
                f"named `{key}`."
            ) from None

    def __contains__(self, item: Union[str, Rule[Any]]) -> bool:
        return (item in self._rules) or (item in self._rules.values())

    def __repr__(self) -> str:
        return "\n".join(repr(rule) for rule in self)

    def __str__(self) -> str:
        return type(self).__name__

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> from hydpy import CalibrationInterface, make_rules, Replace
        >>> ci = CalibrationInterface[Replace](hp=hp, targetfunction=lambda: None)
        >>> ci.add_rules(*make_rules(rule=Replace,
        ...                          names=["fc", "percmax"],
        ...                          parameters=["fc", "percmax"],
        ...                          values=[100.0, 5.0],
        ...                          keywords=["forest", None],
        ...                          lowers=[50.0, 1.0],
        ...                          uppers=[200.0, 10.0],
        ...                          parametersteps="1d",
        ...                          model="hland_v1"))
        >>> sorted(set(dir(ci)) - set(object.__dir__(ci)))
        ['fc', 'percmax']
        """
        return cast(List[str], super().__dir__()) + list(self._rules.keys())


class RuleIUH(Rule[arma_control.Responses]):
    """A |Rule|, class specialised for |IUH| parameters.

    |RuleIUH| serves as a base class only.  Please see the concrete implementation
    |ReplaceIUH| for further information.
    """

    target: str
    """Name of the addressed property of the relevant |IUH| subclass."""

    update_parameters: bool = True
    """Flag indicating whether method |ReplaceIUH.apply_value| should calculate the 
    |ARMA.coefs| and pass them to the relevant model parameter or not.

    Set this flag to |False| for the first |ReplaceIUH| object when another handles the 
    same elements and is applied afterwards.
    """
    _element2iuh: Optional[Dict[str, iuhtools.IUH]] = None

    def __init__(
        self,
        *,
        name: str,
        target: str,
        parameter: Union[Type[arma_control.Responses], arma_control.Responses, str],
        value: float,
        lower: float = -numpy.inf,
        upper: float = numpy.inf,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
        selections: Optional[Iterable[Union[selectiontools.Selection, str]]] = None,
        model: Optional[Union[types.ModuleType, str]] = None,
    ) -> None:
        super().__init__(
            name=name,
            parameter=parameter,
            value=value,
            lower=lower,
            upper=upper,
            parameterstep=parameterstep,
            selections=selections,
            model=model,
        )
        self.target = target

    def _get_original_parameter_values(
        self,
    ) -> Tuple[Tuple[Vector[float], Vector[float]], ...]:
        return tuple(
            (par.ar_coefs[0, :].copy(), par.ma_coefs[0, :].copy()) for par in self
        )

    def add_iuhs(self, **iuhs: iuhtools.IUH) -> None:
        """Add one |IUH| object for each relevant |Element| object.

        See the main documentation on class |ReplaceIUH| for further information.
        """
        try:
            names_int = set(self.elements.names)
            names_ext = set(iuhs.keys())
            if names_int != names_ext:
                enumeration = objecttools.enumeration
                raise RuntimeError(
                    f"The given elements ({enumeration(sorted(names_ext))}) do not "
                    f"agree with the complete set of relevant elements "
                    f"({enumeration(sorted(names_int))})."
                )
            element2iuh = self._element2iuh = {}
            for element in self.elements:
                element2iuh[element.name] = iuhs[element.name]
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to add `IUH` objects to the `{type(self).__name__}` "
                f"rule `{self}`"
            )

    @property
    def _iuhs(self) -> Iterable[iuhtools.IUH]:
        element2iuh = {} if self._element2iuh is None else self._element2iuh
        for iuh in element2iuh.values():
            yield iuh

    def reset_parameters(self) -> None:
        """Reset all relevant parameter objects to their original states.

        See the main documentation on class |ReplaceIUH| for further information.
        """
        for parameter, orig in zip(self, self._original_parameter_values):
            parameter(orig)


class ReplaceIUH(RuleIUH):
    """A |RuleIUH| class for replacing |IUH| parameter values with the current
    calibration parameter values.

    Usually, it is not a good idea to calibrate the AR and MA coefficients of
    parameters like |arma_control.Responses| of model |arma_v1| individually.  Instead,
    we need to calibrate the few coefficients of the underlying |IUH| objects, which
    calculate the ARMA coefficients.  Class |ReplaceIUH| helps to accomplish this task.

    .. note::

        Class |ReplaceIUH| is still under development.  For example, it does not
        address the possibility of different ARMA coefficients related to different
        discharge thresholds.  Hence, the usage of class |ReplaceIUH| might change in
        the future.

    So far, there is no example project containing |arma_v1| models instances.
    Therefore, we generate a simple one consisting of two |Element| objects only:

    >>> from hydpy import Element, prepare_model, Selection
    >>> element1 = Element("element1", inlets="in1", outlets="out1")
    >>> element2 = Element("element2", inlets="in2", outlets="out2")
    >>> complete = Selection("complete", elements=[element1, element2])
    >>> element1.model = prepare_model("arma_v1")
    >>> element2.model = prepare_model("arma_v1")

    We focus on class |TranslationDiffusionEquation| in the following.  First, we
    create two separate instances and use them to calculate the response coefficients
    of both |arma_v1| instances:

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
    >>> u = ReplaceIUH(name="U",
    ...                target="u",
    ...                parameter="responses",
    ...                value=5.0,
    ...                lower=1.0,
    ...                upper=10.0,
    ...                selections=[complete])
    >>> d = ReplaceIUH(name="D",
    ...                target="d",
    ...                parameter="responses",
    ...                value=15.0,
    ...                lower=5.0,
    ...                upper=50.0,
    ...                selections=[complete])

    We add and thereby connect the |Element| and |TranslationDiffusionEquation| objects
    to both |ReplaceIUH| objects via method |RuleIUH.add_iuhs|:

    >>> u.add_iuhs(element1=tde1, element2=tde2)
    >>> d.add_iuhs(element1=tde1, element2=tde2)

    Note that method |RuleIUH.add_iuhs| enforces to add all |IUH| objects at ones to
    avoid inconsistencies that might be hard to track later:

    >>> d.add_iuhs(element1=tde1)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to add `IUH` objects to the `ReplaceIUH` rule `D`, the \
following error occurred: The given elements (element1) do not agree with the \
complete set of relevant elements (element1 and element2).

    By default, each |ReplaceIUH| object triggers the calculation of the ARMA
    coefficients during the execution of its method |ReplaceIUH.apply_value|, which can
    be a waste of computation time if we want to calibrate multiple |IUH| coefficients.
    To save computation time in such cases, set option |RuleIUH.update_parameters|
    to |False| for all except the lastly executed |ReplaceIUH| objects:

    >>> u.update_parameters = False

    Now, changing the value of rule `U` and calling method |ReplaceIUH.apply_value|
    does not affect the coefficients of both |arma_control.Responses| parameters:

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

    On the other side, calling method |ReplaceIUH.apply_value| of rule `D` does
    activate the freshly set value of rule `D` and the previously set value of rule
    `U`, as well:

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

    Use method |RuleIUH.reset_parameters| to restore the original ARMA coefficients:

    >>> d.reset_parameters()
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.906536, -0.197555, 0.002128, 0.000276),
                      (0.842788, -0.631499, 0.061685, 0.015639, 0.0, 0.0, 0.0,
                       -0.000001, 0.0, 0.0, 0.0, 0.0)))
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((1.298097, -0.536702, 0.072903, -0.001207, -0.00004),
                      (0.699212, -0.663835, 0.093935, 0.046177, -0.00854)))
    """

    def apply_value(self) -> None:
        """Apply all current calibration parameter values to all relevant |IUH| objects
        and eventually update the related parameter's ARMA coefficients.

        See the main documentation on class |ReplaceIUH| for further information.
        """
        for parameter, iuh in zip(self, self._iuhs):
            setattr(iuh, self.target, self.value)
            if self.update_parameters:
                parameter(iuh.arma.coefs)


class MultiplyIUH(RuleIUH):
    """A |RuleIUH| class for replacing |IUH| parameter values with the current
    calibration parameter values, applied on the original |IUH| values as factors.

    Please read the documentation on class |ReplaceIUH| first, from which we take the
    following test configuration:

    >>> from hydpy import Element, prepare_model, Selection
    >>> element1 = Element("element1", inlets="in1", outlets="out1")
    >>> element2 = Element("element2", inlets="in2", outlets="out2")
    >>> complete = Selection("complete", elements=[element1, element2])
    >>> element1.model = prepare_model("arma_v1")
    >>> element2.model = prepare_model("arma_v1")

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

    Initialising |MultiplyIUH| works exactly as for |ReplaceIUH|, except for the
    semantic difference that `value`, `lower`, and `upper` now represent factors:

    >>> from hydpy import MultiplyIUH
    >>> u = MultiplyIUH(name="U",
    ...                 target="u",
    ...                 parameter="responses",
    ...                 value=2.0,
    ...                 lower=1.0,
    ...                 upper=4.0,
    ...                 selections=[complete])
    >>> d = MultiplyIUH(name="D",
    ...                 target="d",
    ...                 parameter="responses",
    ...                 value=0.5,
    ...                 lower=0.2,
    ...                 upper=2.0,
    ...                 selections=[complete])

    >>> u.add_iuhs(element1=tde1, element2=tde2)
    >>> d.add_iuhs(element1=tde1, element2=tde2)
    >>> u.update_parameters = False

    The following examples demonstrate that the current calibration values actually
    as factors, applied to the original  values of the relevant |IUH| properties:

    >>> u.value = 3.0
    >>> u.apply_value()
    >>> d.value = 1.0/3.0
    >>> d.apply_value()
    >>> tde1
    TranslationDiffusionEquation(d=5.0, u=15.0, x=1.0)
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.0, 0.0),
                      (0.933333, 0.066667)))
    >>> tde2
    TranslationDiffusionEquation(d=5.0, u=15.0, x=2.0)
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((0.0, 0.0),
                      (0.866667, 0.133333)))

    >>> u.value = 1.0
    >>> u.apply_value()
    >>> d.value = 1.0
    >>> d.apply_value()
    >>> tde1
    TranslationDiffusionEquation(d=15.0, u=5.0, x=1.0)
    >>> element1.model.parameters.control.responses
    responses(th_0_0=((0.906536, -0.197555, 0.002128, 0.000276),
                      (0.842788, -0.631499, 0.061685, 0.015639, 0.0, 0.0, 0.0,
                       -0.000001, 0.0, 0.0, 0.0, 0.0)))
    >>> tde2
    TranslationDiffusionEquation(d=15.0, u=5.0, x=2.0)
    >>> element2.model.parameters.control.responses
    responses(th_0_0=((1.298097, -0.536702, 0.072903, -0.001207, -0.00004),
                      (0.699212, -0.663835, 0.093935, 0.046177, -0.00854)))
    """

    _original_iuh_values: List[float]

    def add_iuhs(self, **iuhs: iuhtools.IUH) -> None:
        """Add one |IUH| object for each relevant |Element| object.

        See the main documentation on class |ReplaceIUH| for further information.
        """
        super().add_iuhs(**iuhs)
        target = self.target
        original_iuh_values: List[float] = []
        assert self._element2iuh is not None  # ensured by `RuleIUH.add_iuhs`
        for iuh in self._element2iuh.values():
            original_iuh_values.append(getattr(iuh, target))
        self._original_iuh_values = original_iuh_values

    def apply_value(self) -> None:
        """Apply all current calibration parameter values to all relevant |IUH| objects
        and eventually update the related parameter's ARMA coefficients.

        See the main documentation on class |MultiplyIUH| for further information.
        """
        target = self.target
        for parameter, iuh, orig in zip(self, self._iuhs, self._original_iuh_values):
            setattr(iuh, target, self.value * orig)
            if self.update_parameters:
                parameter(iuh.arma.coefs)


class CalibSpec:
    """Helper class for specifying the properties of a single calibration parameter.

    So far, class |CalibSpec| does not provide much functionality besides checking upon
    initialisation that the given default and boundary values are consistent:

    >>> from hydpy import CalibSpec
    >>> CalibSpec(name="par1", default=1.0)
    CalibSpec(name="par1", default=1.0)

    >>> CalibSpec(name="par1", default=1.0, keyword="key1")
    CalibSpec(name="par1", default=1.0, keyword="key1")

    >>> CalibSpec(name="par1", default=1.0, lower=2.0)
    Traceback (most recent call last):
    ...
    ValueError: The following values given for calibration parameter `par1` are not \
consistent: default=1.0, lower=2.0, upper=inf.

    >>> CalibSpec(name="par1", default=1.0, upper=0.5)
    Traceback (most recent call last):
    ...
    ValueError: The following values given for calibration parameter `par1` are not \
consistent: default=1.0, lower=-inf, upper=0.5.

    >>> CalibSpec(name="par1", default=1.0, lower=0.0, upper=2.0)
    CalibSpec(name="par1", default=1.0, lower=0.0, upper=2.0)

    Use the `parameterstep` argument for time-dependent calibration parameters:

    >>> CalibSpec(name="par1", default=1.0/3.0, lower=1.0/3.0, upper=1.0/3.0,
    ...           parameterstep="1d")
    CalibSpec(
        name="par1", default=0.333333, lower=0.333333, upper=0.333333, \
parameterstep="1d"
    )

    See the documentation on class |CalibSpecs| for further information.
    """

    name: str
    """Name of the calibration parameter."""
    default: float
    """The default value of the calibration parameter."""
    keyword: Optional[str]
    """The (optional) target keyword of the calibration parameter."""
    lower: float
    """Lower bound of the allowed calibration parameter value."""
    upper: float
    """Upper bound of the allowed calibration parameter value."""
    parameterstep: Optional[timetools.Period]
    """The parameter step size to be set before applying the defined calibration 
    parameter values."""

    def __init__(
        self,
        *,
        name: str,
        default: float,
        keyword: Optional[None] = None,
        lower: float = -numpy.inf,
        upper: float = numpy.inf,
        parameterstep: Optional[timetools.PeriodConstrArg] = None,
    ) -> None:
        self.name = name
        if not lower <= default <= upper:
            raise ValueError(
                f"The following values given for calibration parameter `{self}` are "
                f"not consistent: default={objecttools.repr_(default)}, lower="
                f"{objecttools.repr_(lower)}, upper={objecttools.repr_(upper)}."
            )
        self.default = default
        self.keyword = keyword
        self.lower = lower
        self.upper = upper
        if parameterstep is None:
            self.parameterstep = None
        else:
            self.parameterstep = timetools.Period(parameterstep)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        arguments = [
            f'name="{self.name}"',
            f"default={objecttools.repr_(self.default)}",
        ]
        if self.keyword is not None:
            arguments.append(f'keyword="{self.keyword}"')
        if not numpy.isinf(self.lower):
            arguments.append(f"lower={objecttools.repr_(self.lower)}")
        if not numpy.isinf(self.upper):
            arguments.append(f"upper={objecttools.repr_(self.upper)}")
        if self.parameterstep is not None:
            arguments.append(f'parameterstep="{self.parameterstep}"')
        return black.format_str(
            f"{type(self).__name__}({', '.join(arguments)})",
            mode=black.FileMode(),
        )[:-1]


class CalibSpecs:
    """Collection class for handling |CalibSpec| objects.

    The primary purpose of class |CalibSpecs| is to handle multiple |CalibSpec| objects
    and to make all their attributes accessible in the same order. See property
    |CalibSpecs.names| as one example.  Note that all such properties are sorted in the
    order or the attachment of the different |CalibSpec| objects:

    >>> from hydpy import CalibSpec, CalibSpecs
    >>> calibspecs = CalibSpecs(
    ...     CalibSpec(
    ...         name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d"
    ...     ),
    ...     CalibSpec(name="second", default=1.0, keyword="kw2", lower=0.0),
    ...     CalibSpec(name="first",default=2.0, upper=2.0))
    >>> calibspecs
    CalibSpecs(
        CalibSpec(name="third", default=3.0, lower=-10.0, upper=10.0, \
parameterstep="1d"),
        CalibSpec(name="second", default=1.0, keyword="kw2", lower=0.0),
        CalibSpec(name="first", default=2.0, upper=2.0),
    )

    You can query and remove |CalibSpec| objects via keyword and attribute access:

    >>> print(calibspecs)
    CalibSpecs("third", "second", "first")

    >>> third = calibspecs["third"]
    >>> third in calibspecs
    True
    >>> del calibspecs["third"]
    >>> third in calibspecs
    False
    >>> calibspecs["third"]
    Traceback (most recent call last):
    ...
    KeyError: 'The current `CalibSpecs` object does not handle a `CalibSpec` object \
named `third`.'
    >>> del calibspecs["third"]
    Traceback (most recent call last):
    ...
    KeyError: 'The current `CalibSpecs` object does not handle a `CalibSpec` object \
named `third`.'

    >>> second = calibspecs.second
    >>> "second" in calibspecs
    True
    >>> del calibspecs.second
    >>> "second" in calibspecs
    False
    >>> calibspecs.second
    Traceback (most recent call last):
    ...
    AttributeError: The current `CalibSpecs` object does neither handle a `CalibSpec` \
object nor a normal attribute named `second`.
    >>> del calibspecs.second
    Traceback (most recent call last):
    ...
    AttributeError: The current `CalibSpecs` object does not handle a `CalibSpec` \
object named `second`.

    >>> len(calibspecs)
    1

    Now we can re-append the previously removed |CalibSpec| objects (and thereby bring
    the order of attachment in agreement with the |CalibSpec| names):

    >>> calibspecs.append(second, third)
    >>> for calibspec in calibspecs:
    ...     print(calibspec)
    first
    second
    third
    """

    _name2parspec: Dict[str, CalibSpec]

    def __init__(self, *parspecs: CalibSpec) -> None:
        self._name2parspec = {parspec.name: parspec for parspec in parspecs}

    def __getitem__(self, name: str) -> CalibSpec:
        try:
            return self._name2parspec[name]
        except KeyError:
            raise KeyError(
                f"The current `{type(self).__name__}` object does not handle a "
                f"`CalibSpec` object named `{name}`."
            ) from None

    def __delitem__(self, name: str) -> None:
        try:
            del self._name2parspec[name]
        except KeyError:
            raise KeyError(
                f"The current `{type(self).__name__}` object does not handle a "
                f"`CalibSpec` object named `{name}`."
            ) from None

    def __getattr__(self, name: str) -> CalibSpec:
        try:
            return self._name2parspec[name]
        except KeyError:
            raise AttributeError(
                f"The current `{type(self).__name__}` object does neither handle a "
                f"`CalibSpec` object nor a normal attribute named `{name}`."
            ) from None

    def __delattr__(self, name: str) -> None:
        try:
            del self._name2parspec[name]
        except KeyError:
            raise AttributeError(
                f"The current `{type(self).__name__}` object does not handle a "
                f"`CalibSpec` object named `{name}`."
            ) from None

    def __contains__(self, item: Union[str, CalibSpec]) -> bool:
        return (item in self._name2parspec) or (item in self._name2parspec.values())

    def __len__(self) -> int:
        return len(self._name2parspec)

    def __iter__(self) -> Iterator[CalibSpec]:
        for value in self._name2parspec.values():
            yield value

    def append(self, *calibspecs: CalibSpec) -> None:
        """Append one or more |CalibSpec| objects.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> first = CalibSpec(name="first", default=1.0, lower=0.0)
        >>> second = CalibSpec(name="second",default=2.0, keyword="kw2", upper=2.0)
        >>> calibspecs = CalibSpecs()
        >>> calibspecs.append(first)
        >>> calibspecs.append(second, third)
        >>> calibspecs
        CalibSpecs(
            CalibSpec(name="first", default=1.0, lower=0.0),
            CalibSpec(name="second", default=2.0, keyword="kw2", upper=2.0),
            CalibSpec(name="third", default=3.0, lower=-10.0, upper=10.0, \
parameterstep="1d"),
        )
        """
        for calibspec in calibspecs:
            self._name2parspec[calibspec.name] = calibspec

    @property
    def names(self) -> Tuple[str, ...]:
        """The names of all |CalibSpec| objects in the order of attachment.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> calibspecs = CalibSpecs(CalibSpec(name="first", default=1.0, lower=0.0),
        ...                         CalibSpec(name="second",default=2.0, upper=2.0))
        >>> calibspecs.append(third)
        >>> calibspecs.names
        ('first', 'second', 'third')
        """
        return tuple(parspec.name for parspec in self._name2parspec.values())

    @property
    def defaults(self) -> Tuple[float, ...]:
        """The default values of all |CalibSpec| objects in the order of attachment.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> calibspecs = CalibSpecs(
        ...     CalibSpec(name="first", default=1.0, lower=0.0),
        ...     CalibSpec(name="second", default=2.0, keyword="kw2", upper=2.0))
        >>> calibspecs.append(third)
        >>> calibspecs.defaults
        (1.0, 2.0, 3.0)
        """
        return tuple(parspec.default for parspec in self._name2parspec.values())

    @property
    def keywords(self) -> Tuple[Optional[str], ...]:
        """The (optional) target keywords of all |CalibSpec| objects in the order of
        attachment.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> calibspecs = CalibSpecs(
        ...     CalibSpec(name="first", default=1.0, lower=0.0),
        ...     CalibSpec(name="second", default=2.0, keyword="kw2", upper=2.0))
        >>> calibspecs.append(third)
        >>> calibspecs.keywords
        (None, 'kw2', None)
        """
        return tuple(parspec.keyword for parspec in self._name2parspec.values())

    @property
    def lowers(self) -> Tuple[float, ...]:
        """The lower boundary values of all |CalibSpec| objects in the order of
        attachment.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> calibspecs = CalibSpecs(
        ...     CalibSpec(name="first", default=1.0, lower=0.0),
        ...     CalibSpec(name="second", default=2.0, keyword="kw2", upper=2.0))
        >>> calibspecs.append(third)
        >>> calibspecs.lowers
        (0.0, -inf, -10.0)
        """
        return tuple(parspec.lower for parspec in self._name2parspec.values())

    @property
    def uppers(self) -> Tuple[float, ...]:
        """The upper boundary values of all |CalibSpec| objects in the order of
        attachment.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> calibspecs = CalibSpecs(
        ...     CalibSpec(name="first", default=1.0, lower=0.0),
        ...     CalibSpec(name="second", default=2.0, keyword="kw2", upper=2.0))
        >>> calibspecs.append(third)
        >>> calibspecs.uppers
        (inf, 2.0, 10.0)
        """
        return tuple(parspec.upper for parspec in self._name2parspec.values())

    @property
    def parametersteps(self) -> Tuple[Optional[timetools.Period], ...]:
        """The parameter steps of all |CalibSpec| objects in the order of attachment.

        >>> from hydpy import CalibSpec, CalibSpecs
        >>> third = CalibSpec(
        ...     name="third", default=3.0, lower=-10.0, upper=10.0, parameterstep="1d")
        >>> calibspecs = CalibSpecs(
        ...     CalibSpec(name="first", default=1.0, lower=0.0),
        ...     CalibSpec(name="second", default=2.0, keyword="kw2", upper=2.0))
        >>> calibspecs.append(third)
        >>> calibspecs.parametersteps
        (None, None, Period("1d"))
        """
        return tuple(parspec.parameterstep for parspec in self._name2parspec.values())

    def __str__(self) -> str:
        arguments = (f'"{name}"' for name in self._name2parspec.keys())
        return black.format_str(
            f"{type(self).__name__}({', '.join(arguments)})",
            mode=black.FileMode(),
        )[:-1]

    def __repr__(self) -> str:
        arguments = (repr(value) for value in self._name2parspec.values())
        return black.format_str(
            f"{type(self).__name__}({', '.join(arguments)})",
            mode=black.FileMode(),
        )[:-1]

    def __dir__(self) -> List[str]:
        """
        >>> from hydpy import CalibSpec, CalibSpecs, print_values
        >>> calibspecs = CalibSpecs(CalibSpec(name="first", default=1.0),
        ...                         CalibSpec(name="second",default=2.0))
        >>> sorted(set(dir(calibspecs)) - set(object.__dir__(calibspecs)))
        ['first', 'second']
        """
        return list(super().__dir__()) + list(self.names)


@overload
def make_rules(
    *,
    rule: Type[TypeRule],
    names: Sequence[str],
    parameters: Sequence[Union[parametertools.Parameter, str]],
    values: Sequence[float],
    lowers: Sequence[float],
    uppers: Sequence[float],
    parametersteps: Sequence1[Optional[timetools.PeriodConstrArg]] = None,
    model: Optional[Union[types.ModuleType, str]] = None,
    selections: Literal[None] = None,
) -> List[TypeRule]:
    ...


@overload
def make_rules(
    *,
    rule: Type[TypeRule],
    names: Sequence[str],
    parameters: Sequence[Union[parametertools.Parameter, str]],
    values: Sequence[float],
    keywords: Optional[Sequence[Optional[str]]] = None,
    lowers: Sequence[float],
    uppers: Sequence[float],
    parametersteps: Sequence1[Optional[timetools.PeriodConstrArg]] = None,
    model: Optional[Union[types.ModuleType, str]] = None,
    selections: Iterable[Union[selectiontools.Selection, str]],
    product: bool = False,
) -> List[TypeRule]:
    ...


@overload
def make_rules(
    *,
    rule: Type[TypeRule],
    calibspecs: CalibSpecs,
    names: Optional[Sequence[str]] = None,
    parameters: Optional[Sequence[Union[parametertools.Parameter, str]]] = None,
    values: Optional[Sequence[float]] = None,
    keywords: Optional[Sequence[Optional[str]]] = None,
    lowers: Optional[Sequence[float]] = None,
    uppers: Optional[Sequence[float]] = None,
    model: Optional[Union[types.ModuleType, str]] = None,
    selections: Literal[None] = None,
) -> List[TypeRule]:
    ...


@overload
def make_rules(
    *,
    rule: Type[TypeRule],
    calibspecs: CalibSpecs,
    names: Optional[Sequence[str]] = None,
    parameters: Optional[Sequence[Union[parametertools.Parameter, str]]] = None,
    values: Optional[Sequence[float]] = None,
    keywords: Optional[Sequence[Optional[str]]] = None,
    lowers: Optional[Sequence[float]] = None,
    uppers: Optional[Sequence[float]] = None,
    model: Optional[Union[types.ModuleType, str]] = None,
    selections: Iterable[Union[selectiontools.Selection, str]],
    product: bool = False,
) -> List[TypeRule]:
    ...


def make_rules(
    *,
    rule: Type[TypeRule],
    calibspecs: Optional[CalibSpecs] = None,
    names: Optional[Sequence[str]] = None,
    parameters: Optional[Sequence[Union[parametertools.Parameter, str]]] = None,
    values: Optional[Sequence[float]] = None,
    keywords: Optional[Sequence[Optional[str]]] = None,
    lowers: Optional[Sequence[float]] = None,
    uppers: Optional[Sequence[float]] = None,
    parametersteps: Sequence1[Optional[timetools.PeriodConstrArg]] = None,
    model: Optional[Union[types.ModuleType, str]] = None,
    selections: Optional[Iterable[Union[selectiontools.Selection, str]]] = None,
    product: bool = False,
) -> List[TypeRule]:
    """Conveniently create multiple |Rule| objects at once.

    Please see the main documentation on class |CalibrationInterface| first, from
    which we borrow the general setup:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> from hydpy import CalibrationInterface, make_rules, nse
    >>> ci = CalibrationInterface(
    ...     hp=hp,
    ...     targetfunction=lambda: sum(nse(node=node) for node in hp.nodes))

    Here, we show only the supplemental features of function |make_rules| in some
    brevity.

    Function |make_rules| checks that all given sequences have the same length:

    >>> from hydpy import Replace
    >>> make_rules(rule=Replace,
    ...            names=["fc", "percmax"],
    ...            parameters=["fc", "percmax"],
    ...            values=[100.0, 5.0],
    ...            keywords=["forest", None],
    ...            lowers=[50.0, 1.0],
    ...            uppers=[200.0],
    ...            parametersteps="1d",
    ...            model="hland_v1")
    Traceback (most recent call last):
    ...
    ValueError: When creating rules via function `make_rules`, all given sequences \
must be of equal length.

    The separate handling of the specifications of all calibration parameters is
    error-prone.  You can bundle all specifications within a |CalibSpecs| object
    instead and pass them at once for more safety and convenience:

    >>> from hydpy import CalibSpec, CalibSpecs
    >>> calibspecs = CalibSpecs(
    ...     CalibSpec(name="fc", default=100.0, keyword="forest", lower=50.0, \
upper=200.0),
    ...     CalibSpec(name="percmax", default=5.0, lower=1.0, upper=10.0, \
parameterstep="1d"))
    >>> make_rules(rule=Replace,
    ...            calibspecs=calibspecs,
    ...            parametersteps="1d",
    ...            model="hland_v1")[1]
    Replace(
        name="percmax",
        parameter="percmax",
        value=5.0,
        lower=1.0,
        upper=10.0,
        keyword=None,
        parameterstep="1d",
        model="hland_v1",
        selections=("complete",),
    )

    You are free also to use the individual arguments (e.g. `names`) to override the
    related specifications defined by the |CalibSpecs| object:

    >>> make_rules(rule=Replace,
    ...            calibspecs=calibspecs,
    ...            names=[name.upper() for name in calibspecs.names],
    ...            parametersteps="1d",
    ...            model="hland_v1")[1]
    Replace(
        name="PERCMAX",
        parameter="percmax",
        value=5.0,
        lower=1.0,
        upper=10.0,
        keyword=None,
        parameterstep="1d",
        model="hland_v1",
        selections=("complete",),
    )

    Function |make_rules| raises the following error if you neither pass a |CalibSpecs|
    object nor the complete list of individual calibration parameter specifications:

    >>> make_rules(rule=Replace,
    ...            names=["fc", "percmax"],
    ...            parameters=["fc", "percmax"],
    ...            values=[100.0, 5.0],
    ...            keywords=["forest", None],
    ...            lowers=[50.0, 1.0],
    ...            parametersteps="1d",
    ...            model="hland_v1")
    Traceback (most recent call last):
    ...
    TypeError: When creating rules via function `make_rules`, you must pass a \
`CalibSpecs` object or provide complete information for the following arguments: \
names, parameters, values, keywords, lowers, and uppers.

    You can run function |make_rules| in "product mode", meaning that its execution
    results in distinct |Rule| objects for all combinations of the given calibration
    parameters and selections:

    >>> make_rules(rule=Replace,
    ...            calibspecs=calibspecs,
    ...            model="hland_v1",
    ...            selections=("headwaters", "nonheadwaters"),
    ...            product=True)
    [Replace(
        name="fc_headwaters",
        parameter="fc",
        value=100.0,
        lower=50.0,
        upper=200.0,
        keyword="forest",
        parameterstep=None,
        model="hland_v1",
        selections=("headwaters",),
    ), Replace(
        name="percmax_headwaters",
        parameter="percmax",
        value=5.0,
        lower=1.0,
        upper=10.0,
        keyword=None,
        parameterstep="1d",
        model="hland_v1",
        selections=("headwaters",),
    ), Replace(
        name="fc_nonheadwaters",
        parameter="fc",
        value=100.0,
        lower=50.0,
        upper=200.0,
        keyword="forest",
        parameterstep=None,
        model="hland_v1",
        selections=("nonheadwaters",),
    ), Replace(
        name="percmax_nonheadwaters",
        parameter="percmax",
        value=5.0,
        lower=1.0,
        upper=10.0,
        keyword=None,
        parameterstep="1d",
        model="hland_v1",
        selections=("nonheadwaters",),
    )]

    Trying to run in "product mode" without defining the target selections results in
    the following error message:

    >>> make_rules(rule=Replace,
    ...            calibspecs=calibspecs,
    ...            parametersteps="1d",
    ...            model="hland_v1",
    ...            product=True)
    Traceback (most recent call last):
    ...
    TypeError: When creating rules via function `make_rules` in "product mode" (with \
the argument `product` being `True`), you must supply all target selection objects \
via argument `selections`.
    """
    if calibspecs is None:
        if (
            (names is None)  # pylint: disable=too-many-boolean-expressions
            or (parameters is None)
            or (values is None)
            or (keywords is None)
            or (lowers is None)
            or (uppers is None)
        ):
            raise TypeError(
                "When creating rules via function `make_rules`, you must pass a "
                "`CalibSpecs` object or provide complete information for the "
                "following arguments: names, parameters, values, keywords, lowers, "
                "and uppers."
            )
    else:
        if names is None:
            names = calibspecs.names
        if parameters is None:
            parameters = calibspecs.names
        if values is None:
            values = calibspecs.defaults
        if keywords is None:
            keywords = calibspecs.keywords
        if lowers is None:
            lowers = calibspecs.lowers
        if uppers is None:
            uppers = calibspecs.uppers
        if parametersteps is None:
            parametersteps = calibspecs.parametersteps
    parameters_ = tuple(
        objecttools.extract(values=parameters, types_=(parametertools.Parameter, str))
    )
    if isinstance(parametersteps, str) or not isinstance(parametersteps, Sequence):
        parametersteps = len(names) * (parametersteps,)
    if not (
        len(names)
        == len(parameters_)
        == len(lowers)
        == len(uppers)
        == len(values)
        == len(keywords)
        == len(parametersteps)
    ):
        raise ValueError(
            "When creating rules via function `make_rules`, all given sequences must "
            "be of equal length."
        )
    nmb_parameters = len(parameters_)
    selections2: Iterable[Optional[Iterable[Union[selectiontools.Selection, str]]]]
    if product:
        if selections is None:
            raise TypeError(
                'When creating rules via function `make_rules` in "product mode" '
                "(with the argument `product` being `True`), you must supply all "
                "target selection objects via argument `selections`."
            )
        selections = tuple(selections)
        names = tuple(
            f"{par}_{sel}" for sel, par in itertools.product(selections, parameters_)
        )
        nmb_selections = len(selections)
        parameters_ = nmb_selections * tuple(parameters_)
        lowers = nmb_selections * tuple(lowers)
        uppers = nmb_selections * tuple(uppers)
        values = nmb_selections * tuple(values)
        keywords = nmb_selections * tuple(keywords)
        parametersteps = nmb_selections * tuple(parametersteps)
        selections2 = itertools.chain.from_iterable(
            itertools.repeat((sel,), nmb_parameters) for sel in selections
        )
    else:
        selections2 = itertools.repeat(selections, nmb_parameters)
    rules = []
    for (
        name,
        parameter,
        lower,
        upper,
        value,
        keyword,
        parameterstep,
        selections_,
    ) in zip(
        names,
        parameters_,
        lowers,
        uppers,
        values,
        keywords,
        parametersteps,
        selections2,
    ):
        rules.append(
            rule(
                name=name,
                parameter=parameter,
                value=value,
                keyword=keyword,
                lower=lower,
                upper=upper,
                parameterstep=parameterstep,
                selections=selections_,
                model=model,
            )
        )
    return rules
