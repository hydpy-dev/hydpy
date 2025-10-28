"""This module implements tools for testing *HydPy* and its models."""

# import...
# ...from standard library
from __future__ import annotations
import abc
import builtins
import contextlib
import copy
import datetime
import doctest
import importlib
import inspect
import io
import itertools
import os
import shutil
import sys
import types
import warnings

# ...from site-packages
import numpy

# ...from HydPy
import hydpy

# from hydpy import aliases  actual import below
from hydpy import config
from hydpy import data
from hydpy import docs
from hydpy.docs import autofigs
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import hydpytools
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core import objecttools
from hydpy.core import pubtools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core import typingtools
from hydpy.core import variabletools
from hydpy.core.typingtools import *
from hydpy.auxs import ppolytools
from hydpy.tests import iotesting

# from hydpy.models import hland  actual import below
# from hydpy.models import lland  actual import below


if TYPE_CHECKING:
    import matplotlib
    from matplotlib import pyplot
    import pandas
    import plotly
    from plotly import subplots

    class TestIOSequence(sequencetools.IOSequence):
        """|IOSequence| subclass for testing purposes."""

        testarray: NDArrayFloat
        descr_device = "just_for_testing"
        descr_sequence = "just_for_testing"

else:
    matplotlib = exceptiontools.OptionalImport("matplotlib", ["matplotlib"], locals())
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())
    pandas = exceptiontools.OptionalImport("pandas", ["pandas"], locals())
    plotly = exceptiontools.OptionalImport("plotly", ["plotly"], locals())
    subplots = exceptiontools.OptionalImport("subplots", ["plotly.subplots"], locals())


class StdOutErr:
    """Replaces `sys.stdout` and `sys.stderr` temporarily when calling
    method |Tester.perform_tests| of class |Tester|."""

    indent: int
    texts: list[str]

    def __init__(self, indent: int = 0):
        self.indent = indent
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.encoding = sys.stdout.encoding
        self.texts = []

    def __enter__(self) -> None:
        self.encoding = sys.stdout.encoding
        # just for testing:
        sys.stdout = self
        sys.stderr = self

    def __exit__(
        self,
        exception_type: type[BaseException],
        exception_value: BaseException,
        traceback: types.TracebackType,
    ) -> None:
        if not self.texts:
            self.print_("no failures occurred")
        else:
            for text in self.texts:
                self.print_(text)
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def write(self, text: str) -> None:
        """Memorise the given text for later writing."""
        self.texts.extend(text.split("\n"))

    def print_(self, text: str) -> None:
        """Print the memorised text to the original `sys.stdout`."""
        if text.strip():
            self.stdout.write(self.indent * " " + text + "\n")

    def flush(self) -> None:
        """Do nothing."""


class Tester:
    """Tests either a base or an application model.

    Usually, a |Tester| object is initialised at the end of the `__init__`
    file of its base model or the end of the module of an application model.

    >>> from hydpy.models import hland, hland_96

    >>> hland.tester.package
    'hydpy.models.hland'
    >>> hland_96.tester.package
    'hydpy.models'
    """

    filepath: str
    package: str
    ispackage: bool

    def __init__(self) -> None:
        frame = inspect.currentframe()
        assert isinstance(frame, types.FrameType)
        frame = frame.f_back
        assert isinstance(frame, types.FrameType)
        self.filepath = frame.f_code.co_filename
        self.package = frame.f_locals["__package__"]
        self.ispackage = os.path.split(self.filepath)[-1] == "__init__.py"

    @property
    def filenames(self) -> list[str]:
        """The filenames which define the considered base or application model.

        >>> from hydpy.models import hland, hland_96
        >>> from pprint import pprint
        >>> pprint(hland.tester.filenames)
        ['__init__.py',
         'hland_aides.py',
         'hland_constants.py',
         'hland_control.py',
         'hland_derived.py',
         'hland_factors.py',
         'hland_fixed.py',
         'hland_fluxes.py',
         'hland_inputs.py',
         'hland_masks.py',
         'hland_model.py',
         'hland_outlets.py',
         'hland_parameters.py',
         'hland_sequences.py',
         'hland_states.py']
        >>> hland_96.tester.filenames
        ['hland_96.py']
        """
        if self.ispackage:
            filenames = os.listdir(os.path.dirname(self.filepath))
            return sorted(fn for fn in filenames if fn.endswith(".py"))
        return [os.path.split(self.filepath)[1]]

    @property
    def modulenames(self) -> list[str]:
        """The module names to be taken into account for testing.

        >>> from hydpy.models import hland, hland_96
        >>> from pprint import pprint
        >>> pprint(hland.tester.modulenames)
        ['hland_aides',
         'hland_constants',
         'hland_control',
         'hland_derived',
         'hland_factors',
         'hland_fixed',
         'hland_fluxes',
         'hland_inputs',
         'hland_masks',
         'hland_model',
         'hland_outlets',
         'hland_parameters',
         'hland_sequences',
         'hland_states']
        >>> hland_96.tester.modulenames
        ['hland_96']
        """
        return [
            os.path.split(fn)[-1].split(".")[0]
            for fn in self.filenames
            if (fn.endswith(".py") and not fn.startswith("_"))
        ]

    def perform_tests(self) -> None:
        """Perform all doctests either in Python or in Cython mode depending
        on the state of |Options.usecython| set in module |pub|.

        Usually, |Tester.perform_tests| is triggered automatically by a |Cythonizer|
        object assigned to the same base or application model as a |Tester| object.
        However, you are free to call it any time when in doubt of the functionality
        of a particular base or application model.  Doing so might change some of the
        states of your current configuration, but only temporarily (besides
        "projectname") we pick the |Timegrids| object of module |pub| as an example,
        which is changed multiple times during testing but finally reset to the
        original value):

        >>> from hydpy import pub
        >>> pub.projectname = "test"
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"

        >>> from hydpy.models import hland, hland_96
        >>> hland.tester.perform_tests()  # doctest: +ELLIPSIS
        Test package hydpy.models.hland in ...ython mode.
            * hland_aides:
                no failures occurred
            * hland_constants:
                no failures occurred
            * hland_control:
                no failures occurred
            * hland_derived:
                no failures occurred
            * hland_factors:
                no failures occurred
            * hland_fixed:
                no failures occurred
            * hland_fluxes:
                no failures occurred
            * hland_inputs:
                no failures occurred
            * hland_masks:
                no failures occurred
            * hland_model:
                no failures occurred
            * hland_outlets:
                no failures occurred
            * hland_parameters:
                no failures occurred
            * hland_sequences:
                no failures occurred
            * hland_states:
                no failures occurred

        >>> hland_96.tester.perform_tests()  # doctest: +ELLIPSIS
        Test module hland_96 in ...ython mode.
            * hland_96:
                no failures occurred

        >>> pub.projectname
        'test'
        >>> pub.timegrids
        Timegrids("2000-01-01 00:00:00",
                  "2001-01-01 00:00:00",
                  "1d")

        To show the reporting of possible errors, we change the string representation
        of parameter |hland_control.ZoneType| temporarily.  Again, the |Timegrids|
        object is reset to its initial state after testing:

        >>> from unittest import mock
        >>> with mock.patch(
        ...     "hydpy.models.hland.hland_control.ZoneType.__repr__",
        ...     return_value="damaged"):
        ...     hland.tester.perform_tests()  # doctest: +ELLIPSIS
        Test package hydpy.models.hland in ...ython mode.
            * hland_aides:
                no failures occurred
            * hland_constants:
                no failures occurred
            * hland_control:
                ******...hland_control.py", line ..., in \
hydpy.models.hland.hland_control.ZoneType
                Failed example:
                    zonetype
                Expected:
                    zonetype(FIELD, FOREST, GLACIER, ILAKE, ILAKE, FIELD)
                Got:
                    damaged
                ************************************************************\
**********
                ...
            * hland_derived:
                no failures occurred
            ...
            * hland_states:
                no failures occurred

        >>> pub.projectname
        'test'
        >>> pub.timegrids
        Timegrids("2000-01-01 00:00:00",
                  "2001-01-01 00:00:00",
                  "1d")
        """
        opt = hydpy.pub.options
        print(
            f"Test {'package' if self.ispackage else 'module'} "
            f"{self.package if self.ispackage else self.modulenames[0]} "
            f"in {'C' if hydpy.pub.options.usecython else 'P'}ython mode."
        )
        for name in self.modulenames:
            print(f"    * {name}:")
            with (
                StdOutErr(indent=8),
                opt.ellipsis(0),
                opt.printprogress(False),
                opt.reprdigits(6),
                opt.usedefaultvalues(False),
                opt.utclongitude(15),
                opt.utcoffset(60),
                opt.timestampleft(True),
                opt.warnsimulationstep(False),
                opt.warntrim(False),
                opt.parameterstep(timetools.Period("1d")),
                opt.simulationstep(timetools.Period()),
                devicetools.clear_registries_temporarily(),
            ):
                projectname = exceptiontools.getattr_(
                    hydpy.pub, "projectname", None, str
                )
                del hydpy.pub.projectname
                timegrids = exceptiontools.getattr_(hydpy.pub, "timegrids", None)
                del hydpy.pub.timegrids
                plotting_options = IntegrationTest.plotting_options
                IntegrationTest.plotting_options = PlottingOptions()
                try:
                    modulename = ".".join((self.package, name))
                    module = importlib.import_module(modulename)
                    with warnings.catch_warnings():
                        doctest.testmod(
                            module,
                            extraglobs={"testing": True},
                            optionflags=doctest.ELLIPSIS,
                        )
                finally:
                    if projectname is not None:
                        hydpy.pub.projectname = projectname
                    if timegrids is not None:
                        hydpy.pub.timegrids = timegrids
                    IntegrationTest.plotting_options = plotting_options


class Array:
    """Assures that attributes are |numpy.ndarray| objects."""

    def __setattr__(self, name: str, value: NDArrayFloat) -> None:
        object.__setattr__(self, name, numpy.array(value))


class ArrayDescriptor:
    """A descriptor for handling values of |Array| objects."""

    def __init__(self) -> None:
        self.values = Array()

    def __set__(
        self,
        obj: Test,
        sequence2value: (
            Sequence[tuple[sequencetools.ConditionSequence, ArrayFloat]]
        ) | None,
    ) -> None:
        self.__delete__(obj)
        if sequence2value is not None:
            names = [value[0].name for value in sequence2value]
            duplicates = tuple(name for name in set(names) if names.count(name) > 1)
            for i, (name, (seq, _)) in enumerate(tuple(zip(names, sequence2value))):
                if name in duplicates:
                    names[i] = f"{name}_{objecttools.devicename(seq)}"
            duplicates = tuple(name for name in set(names) if names.count(name) > 1)
            for i, (name, (seq, _)) in enumerate(tuple(zip(names, sequence2value))):
                if name in duplicates:
                    names[i] = f"{name}_{id(seq)}"
            for name, (_, value) in zip(names, sequence2value):
                setattr(self.values, name, value)

    def __get__(self, obj: Test, type_: type[Test] | None = None) -> Array:
        return self.values

    def __delete__(self, obj: Test) -> None:
        for name in tuple(vars(self.values).keys()):
            delattr(self.values, name)


class Test:
    """Base class for |IntegrationTest| and |UnitTest|.

    This base class defines the printing of the test results primarily.
    How the tests shall be prepared and performed is to be defined in
    its subclasses.
    """

    parseqs: Any
    HEADER_OF_FIRST_COL: Any

    inits = ArrayDescriptor()
    """Stores arrays for setting the same values of parameters and/or sequences before 
    each new experiment."""

    @property
    @abc.abstractmethod
    def raw_first_col_strings(self) -> tuple[str, ...]:
        """To be implemented by the subclasses of |Test|."""

    @abc.abstractmethod
    def get_output_array(self, parseqs):
        """To be implemented by the subclasses of |Test|."""

    @property
    def nmb_rows(self) -> int:
        """The number of rows of the table."""
        return len(self.raw_first_col_strings) + 1

    @property
    def nmb_cols(self) -> int:
        """The number of columns in the table."""
        nmb = 1
        for parseq in self.parseqs:
            nmb += max(parseq.numberofvalues, 1)
        return nmb

    @property
    def raw_header_strings(self) -> list[str]:
        """All raw strings for the tables header."""
        strings = [self.HEADER_OF_FIRST_COL]
        for parseq in self.parseqs:
            for dummy in range(parseq.numberofvalues - 1):
                strings.append("")
            if (parseq.name == "sim") and isinstance(parseq, sequencetools.Sequence_):
                strings.append(parseq.subseqs.node.name)
            else:
                strings.append(parseq.name)
        return strings

    @property
    def raw_body_strings(self) -> list[list[str]]:
        """All raw strings for the body of the table."""
        strings = []
        for idx, first_string in enumerate(self.raw_first_col_strings):
            strings.append([first_string])
            for parseq in self.parseqs:
                array = self.get_output_array(parseq)
                if parseq.NDIM == 0:
                    strings[-1].append(objecttools.repr_(array[idx]))
                elif len(parseq) == 0:
                    strings[-1].append("-")
                else:
                    strings[-1].extend(
                        objecttools.repr_(value) for value in array[idx].flatten()
                    )
        return strings

    @property
    def raw_strings(self) -> list[list[str]]:
        """All raw strings for the complete table."""
        return [self.raw_header_strings] + self.raw_body_strings

    @property
    def col_widths(self) -> list[int]:
        """The widths of all columns of the table."""
        strings = self.raw_strings
        widths: list[int] = []
        for jdx in range(self.nmb_cols):
            widths.append(0)
            for idx in range(self.nmb_rows):
                widths[-1] = max(len(strings[idx][jdx]), widths[-1])
        return widths

    @property
    def col_separators(self) -> list[str]:
        """The separators for adjacent columns."""
        seps = ["| "]
        for parseq in self.parseqs:
            seps.append(" | ")
            for dummy in range(parseq.numberofvalues - 1):
                seps.append("  ")
        seps.append(" |")
        return seps

    @property
    def row_nmb_characters(self) -> int:
        """The number of characters of a single row of the table."""
        return sum(self.col_widths) + sum(len(sep) for sep in self.col_separators)

    @staticmethod
    def _interleave(
        separators: Sequence[str], strings: Iterable[str], widths: Iterable[int]
    ) -> str:
        """Generate a table line from the given arguments."""
        lst = [
            value
            for (separator, string, width) in zip(separators, strings, widths)
            for value in (separator, string.rjust(width))
        ]
        lst.append(separators[-1])
        return "".join(lst)

    def make_table(self, idx1: int | None = None, idx2: int | None = None) -> str:
        """Return the result table between the given indices."""
        lines = []
        col_widths = self.col_widths
        col_separators = self.col_separators
        lines.append(
            self._interleave(self.col_separators, self.raw_header_strings, col_widths)
        )
        lines.append("-" * self.row_nmb_characters)
        for strings_in_line in self.raw_body_strings[idx1:idx2]:
            lines.append(self._interleave(col_separators, strings_in_line, col_widths))
        return "\n".join(lines)

    def print_table(self, idx1: int | None = None, idx2: int | None = None) -> None:
        """Print the result table between the given indices."""
        print(self.make_table(idx1=idx1, idx2=idx2))


class PlottingOptions:
    """Plotting options of class |IntegrationTest|."""

    width: int
    height: int
    axis1: typingtools.MayNonerable1[sequencetools.IOSequence]
    axis2: typingtools.MayNonerable1[sequencetools.IOSequence]
    activated: tuple[sequencetools.IOSequence, ...] | None

    def __init__(self) -> None:
        self.width = 600
        self.height = 300
        self.selected = None
        self.activated = None
        self.axis1 = None
        self.axis2 = None


class IntegrationTest(Test):
    """Defines model integration doctests.

    The functionality of |IntegrationTest| is easiest to understand by inspecting
    doctests like the ones of modules |arma_rimorido|.

    Note that all condition sequences (state and logging sequences) are initialised in
    accordance with the values are given as `inits` values.  The values of the
    simulation sequences of outlet and sender nodes are always set to zero before each
    test run.  All other parameter and sequence values can be changed between different
    test runs.
    """

    HEADER_OF_FIRST_COL = "date"
    """The header of the first column containing dates."""

    plotting_options = PlottingOptions()
    element: devicetools.Element
    elements: devicetools.Devices[devicetools.Element]
    nodes: devicetools.Devices[devicetools.Node]
    parseqs: tuple[sequencetools.IOSequence, ...]

    def __init__(
        self,
        element: devicetools.Element | None = None,
        seqs: tuple[sequencetools.IOSequence, ...] | None = None,
        inits=None,
    ) -> None:
        """Prepare the element and its nodes, put them into a HydPy object, and make
        their sequences ready for use for integration testing."""
        del self.inits
        self.elements = devicetools.Element.query_all()
        self.nodes = devicetools.Node.query_all()
        self.hydpy = hydpytools.HydPy()
        self.hydpy.update_devices(nodes=self.nodes, elements=self.elements)
        if element is None:
            self.element = self.hydpy.collectives[0]
        else:
            self.element = element
        self.model = self.element.model
        self.prepare_node_sequences()
        self.prepare_input_model_sequences()
        self.parseqs = seqs if seqs else self.extract_print_sequences()
        self.inits = inits
        self._src = None

    @overload
    def __call__(
        self,
        filename: str | None = None,
        *,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        update_parameters: bool = True,
        get_conditions: Literal[None] = ...,
        use_conditions: ConditionsModel | None = None,
    ) -> None:
        """do not return conditions"""

    @overload
    def __call__(
        self,
        filename: str | None = None,
        *,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        update_parameters: bool = True,
        get_conditions: timetools.DateConstrArg,
        use_conditions: ConditionsModel | None,
    ) -> ConditionsModel:
        """do return conditions"""

    def __call__(
        self,
        filename: str | None = None,
        *,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        update_parameters: bool = True,
        get_conditions: timetools.DateConstrArg | None = None,
        use_conditions: ConditionsModel | None = None,
    ) -> ConditionsModel | None:
        """Prepare and perform an integration test and print and eventually plot its
        results.

        Note that the conditions defined under |IntegrationTest.inits| override the
        ones given via keyword `use_conditions`.
        """
        self.prepare_model(
            update_parameters=update_parameters, use_conditions=use_conditions
        )
        seq2value = self._perform_simulation(get_conditions)
        self.print_table()
        if filename:
            self.plot(filename=filename, axis1=axis1, axis2=axis2)
        return seq2value

    def _perform_simulation(
        self, get_conditions: timetools.DateConstrArg | None
    ) -> ConditionsModel | None:
        if get_conditions:
            sim = copy.deepcopy(hydpy.pub.timegrids.sim)
            date = timetools.Date(get_conditions)
            if date > hydpy.pub.timegrids.init.firstdate:
                hydpy.pub.timegrids.sim.lastdate = date
                self.hydpy.simulate()
            conditions = self.element.model.conditions
            if date < hydpy.pub.timegrids.init.lastdate:
                hydpy.pub.timegrids.sim.dates = date, sim.lastdate
                self.hydpy.simulate()
            hydpy.pub.timegrids.sim.firstdate = sim.firstdate
            return conditions
        self.hydpy.simulate()
        return None

    @property
    def _datetimes(self) -> tuple[datetime.datetime, ...]:
        return tuple(date.datetime for date in hydpy.pub.timegrids.sim)

    @property
    def raw_first_col_strings(self) -> tuple[str, ...]:
        """The raw date strings of the first column, except the header."""
        return tuple(_.strftime(self.dateformat) for _ in self._datetimes)

    @property
    def dateformat(self) -> str:
        """Format string for printing dates in the first column of the table.

        See the documentation on module |datetime| for the format strings allowed.

        You can query and change property |IntegrationTest.dateformat|:

        >>> from hydpy import Element, IntegrationTest, prepare_model, pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> element = Element("element", outlets="node")
        >>> element.model = prepare_model("hland_96")
        >>> __package__ = "testpackage"
        >>> tester = IntegrationTest(element)
        >>> tester.dateformat
        '%Y-%m-%d %H:%M:%S'

        Passing an ill-defined format string leads to the following error:

        >>> tester.dateformat = 999
        Traceback (most recent call last):
        ...
        ValueError: The given date format `999` is not a valid format string for \
`datetime` objects.  Please read the documentation on module datetime of the Python \
standard library for for further information.

        >>> tester.dateformat = "%x"
        >>> tester.dateformat
        '%x'
        """
        dateformat = vars(self).get("dateformat")
        if dateformat is None:
            return timetools.Date.formatstrings["iso2"]
        return dateformat

    @dateformat.setter
    def dateformat(self, dateformat: str) -> None:
        try:
            datetime.datetime(2000, 1, 1).strftime(dateformat)
        except BaseException as exc:
            raise ValueError(
                f"The given date format `{dateformat}` is not a valid format string "
                f"for `datetime` objects.  Please read the documentation on module "
                f"datetime of the Python standard library for for further information."
            ) from exc
        vars(self)["dateformat"] = dateformat

    def get_output_array(self, parseqs: sequencetools.IOSequence):
        """Return the array containing the output results of the given sequence."""
        return parseqs.series

    def prepare_node_sequences(self) -> None:
        """Prepare the simulations series of all nodes.

        This preparation might not be suitable for all types of integration tests.
        Prepare those node sequences manually, for which this method does not result in
        the desired outcome."""
        for node in self.nodes:
            if not node.entries:
                node.deploymode = "oldsim"
            sim = node.sequences.sim
            sim.prepare_series(allocate_ram=False)
            sim.prepare_series(allocate_ram=True)

    def prepare_input_model_sequences(self) -> None:
        """Configure the input sequences of the model in a manner that allows for
        applying their time series data in integration tests."""
        prepare_inputseries = self.element.prepare_inputseries
        prepare_inputseries(allocate_ram=False)
        prepare_inputseries(allocate_ram=True)

    def extract_print_sequences(self) -> tuple[sequencetools.IOSequence, ...]:
        """Return a list of all input, factor, flux, and state sequences of the model
        and the simulation sequences of all nodes."""
        seqs = []
        for name in ("inputs", "factors", "fluxes", "states"):
            subseqs = getattr(self.element.model.sequences, name, ())
            for seq in subseqs:
                seqs.append(seq)
        for node in self.nodes:
            seqs.append(node.sequences.sim)
        return tuple(seqs)

    def prepare_model(
        self, update_parameters: bool, use_conditions: ConditionsModel | None
    ) -> None:
        """Derive the secondary parameter values, prepare all required time series and
        set the initial conditions."""
        if update_parameters:
            self.model.update_parameters()
        self.reset_values()
        self.reset_series()
        self.reset_outputs()
        if use_conditions:
            with hydpy.pub.options.trimvariables(False):
                self.element.model.conditions = use_conditions
        self.reset_inits()

    def reset_values(self) -> None:
        """Set the current values of all factor and flux sequences to |numpy.nan|."""
        for model in self.model.find_submodels(include_mainmodel=True).values():
            for seqs in (model.sequences.factors, model.sequences.fluxes):
                for seq in seqs:
                    seq.value = numpy.nan

    def reset_series(self) -> None:
        """Initialise all time series with |numpy.nan| values."""
        for flag in (False, True):
            self.element.prepare_factorseries(allocate_ram=flag)
            self.element.prepare_fluxseries(allocate_ram=flag)
            self.element.prepare_stateseries(allocate_ram=flag)

    def reset_outputs(self) -> None:
        """Set the values of the simulation sequences of all outlet nodes to zero."""
        for node in self.nodes:
            if (node in self.element.outlets) or (node in self.element.senders):
                node.sequences.sim[:] = 0.0

    def reset_inits(self) -> None:
        """Set all initial conditions of all models."""
        with hydpy.pub.options.trimvariables(False):
            inits = self.inits
            for subname in ("states", "logs"):
                for element in self.elements:
                    for model in element.model.find_submodels(
                        include_mainmodel=True
                    ).values():
                        for seq in getattr(model.sequences, subname, ()):
                            value = getattr(inits, seq.name, None)
                            if value is None:
                                name = f"{seq.name}_{element.name}"
                                value = getattr(inits, name, None)
                            if value is None:
                                name = f"{seq.name}_{element.name}_{id(seq)}"
                                value = getattr(inits, name, None)
                            if value is not None:
                                seq(value)

    def plot(
        self,
        filename: str,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
    ) -> None:
        """Save a plotly HTML file plotting the current test results.

        (Optional) arguments:
            * filename: Name of the file.  If necessary, the file ending `html` is
              added automatically.  The file is stored in the `html_` folder of
              subpackage `docs`.
            * act_sequences: List of the sequences to be shown initially (deprecated).
            * axis1: sequences to be shown initially on the first axis.
            * axis2: sequences to be shown initially on the second axis.
        """

        def _update_act_names(sequence_: sequencetools.IOSequence, name_: str) -> None:
            if isinstance(sequence_, act_types1):
                act_names1.append(name_)
            if isinstance(sequence_, act_types2):
                act_names2.append(name_)

        if not filename.endswith(".html"):
            filename += ".html"
        if self.plotting_options.activated:
            axis1 = self.plotting_options.activated
            axis2 = ()
        else:
            if not (axis1 or axis2):
                axis1 = self.plotting_options.axis1
                axis2 = self.plotting_options.axis2
            if axis1 is None:
                axis1 = self.parseqs
            if axis2 is None:
                axis2 = ()
            axis1 = objecttools.extract(
                axis1, (sequencetools.IOSequence,)  # type: ignore[type-abstract]
            )
            axis2 = objecttools.extract(
                axis2, (sequencetools.IOSequence,)  # type: ignore[type-abstract]
            )
        sel_sequences = self.plotting_options.selected
        if sel_sequences is None:
            sel_sequences = self.parseqs
        sel_sequences = tuple(sorted(sel_sequences, key=lambda seq_: seq_.name))
        act_types1 = tuple(type(seq_) for seq_ in axis1)
        act_types2 = tuple(type(seq_) for seq_ in axis2)
        sel_names, sel_series, sel_units = [], [], []
        act_names1: list[str] = []
        act_names2: list[str] = []
        for sequence in sel_sequences:
            name = type(sequence).__name__
            if sequence.NDIM == 0:
                sel_names.append(name)
                sel_units.append(sequence.unit)
                sel_series.append(list(sequence.series))
                _update_act_names(sequence, name)
            elif all(length == 1 for length in sequence.shape):
                sel_names.append(name)
                sel_units.append(sequence.unit)
                sel_series.append(list(sequence.series[:, 0]))
                _update_act_names(sequence, name)
            else:
                ranges = (range(length) for length in sequence.shape)
                for idxs in itertools.product(*ranges):
                    subname = f"{name}_{'-'.join(str(idx+1) for idx in idxs)}"
                    sel_names.append(subname)
                    sel_units.append(sequence.unit)
                    series = sequence.series
                    for idx in idxs:
                        series = series[:, idx]
                    sel_series.append(list(series))
                    _update_act_names(sequence, subname)

        fig = subplots.make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)
        fig.update_layout(showlegend=True)

        cmap = pyplot.get_cmap("tab20", 2 * len(sel_names))
        dates = list(
            pandas.date_range(
                start=hydpy.pub.timegrids.eval_.firstdate.datetime,
                end=hydpy.pub.timegrids.eval_.lastdate.datetime,
                freq=hydpy.pub.timegrids.eval_.stepsize.timedelta,
            )
        )
        for idx, (name, series, unit) in enumerate(
            zip(sel_names, sel_series, sel_units)
        ):
            fig.add_trace(
                plotly.graph_objects.Scattergl(
                    x=dates,
                    y=series,
                    name=f"{name} [{unit}] (1)",
                    visible=name in act_names1,
                    legendgroup="axis 1",
                    line={"color": matplotlib.colors.rgb2hex(cmap(2 * idx))},
                )
            )
            fig.add_trace(
                plotly.graph_objects.Scattergl(
                    x=dates,
                    y=series,
                    name=f"{name} [{unit}] (2)",
                    visible=name in act_names2,
                    legendgroup="axis 2",
                    line={"color": matplotlib.colors.rgb2hex(cmap(2 * idx + 1))},
                ),
                secondary_y=True,
            )

        buttons = []
        for label, visibles in (
            ("add all to y-axis 1", (True, False)),
            ("remove all", (False, False)),
            ("add all to y-axis 2", (False, True)),
        ):
            subbuttons: list[dict[str, str | list[Any]]] = [
                {
                    "label": label,
                    "method": "restyle",
                    "args": [{"visible": len(sel_sequences) * visibles}],
                }
            ]
            for idx, name in enumerate(sel_names):
                subbuttons.append(
                    {
                        "label": name,
                        "method": "restyle",
                        "args": [{"visible": visibles}, [2 * idx, 2 * idx + 1]],
                    }
                )
            buttons.append(subbuttons)

        fig.update_layout(
            hovermode="x unified",
            updatemenus=[
                {
                    "active": 0,
                    "xanchor": "left",
                    "x": 0.0,
                    "yanchor": "bottom",
                    "y": 1.02,
                    "buttons": buttons[0],
                },
                {
                    "active": 0,
                    "xanchor": "center",
                    "x": 0.5,
                    "yanchor": "bottom",
                    "y": 1.02,
                    "buttons": buttons[1],
                },
                {
                    "active": 0,
                    "xanchor": "right",
                    "x": 1.0,
                    "yanchor": "bottom",
                    "y": 1.02,
                    "buttons": buttons[2],
                },
            ],
            legend={"tracegroupgap": 100},
        )

        docspath = docs.__path__[0]
        fig.write_html(
            os.path.join(docspath, "html_", filename), include_plotlyjs="directory"
        )


class UnitTest(Test):
    """Defines unit doctests for a single model method."""

    HEADER_OF_FIRST_COL = "ex."
    """The header of the first column containing sequential numbers."""

    nexts = ArrayDescriptor()
    """Stores arrays for setting different values of parameters and/or
    sequences before each new experiment."""

    results = ArrayDescriptor()
    """Stores arrays with the resulting values of parameters and/or
    sequences of each new experiment."""

    def __init__(self, model, method, *, first_example=1, last_example=1, parseqs=None):
        del self.inits
        del self.nexts
        del self.results
        self.model = model
        self.method = method
        self.first_example_calc = first_example
        self.last_example_calc = last_example
        self.first_example_plot = first_example
        self.last_example_plot = last_example
        self.parseqs = parseqs
        self.memorise_inits()
        self.prepare_output_arrays()

    @property
    def nmb_examples(self):
        """The number of examples to be calculated."""
        return self.last_example_calc - self.first_example_calc + 1

    @property
    def idx0(self):
        """The first index of the examples selected for printing."""
        return self.first_example_plot - self.first_example_calc

    @property
    def idx1(self):
        """The last index of the examples selected for printing."""
        return self.nmb_examples - (self.last_example_calc - self.last_example_plot)

    def __call__(self, first_example=None, last_example=None) -> None:
        if first_example is None:
            self.first_example_plot = self.first_example_calc
        else:
            self.first_example_plot = first_example
        if last_example is None:
            self.last_example_plot = self.last_example_calc
        else:
            self.last_example_plot = last_example
        for idx in range(self.nmb_examples):
            self.reset_inits()
            self._update_inputs(idx)
            self.method()
            self._update_outputs(idx)
        self.print_table(self.idx0, self.idx1)

    def get_output_array(self, parseqs):
        """Return the array containing the output results of the given
        parameter or sequence."""
        return getattr(self.results, parseqs.name)

    @property
    def raw_first_col_strings(self):
        """The raw integer strings of the first column, except the header."""
        return [
            str(example)
            for example in range(self.first_example_plot, self.last_example_plot + 1)
        ]

    def memorise_inits(self):
        """Memorise all initial conditions."""
        for parseq in self.parseqs:
            value = exceptiontools.getattr_(parseq, "value", None)
            if value is not None:
                setattr(self.inits, parseq.name, value)

    def prepare_output_arrays(self):
        """Prepare arrays for storing the calculated results for the
        respective parameters and/or sequences."""
        for parseq in self.parseqs:
            shape = [len(self.raw_first_col_strings)] + list(parseq.shape)
            type_ = getattr(parseq, "TYPE", float)
            init = 0 if issubclass(type_, int) else numpy.nan
            array = numpy.full(shape, init, type_)
            setattr(self.results, parseq.name, array)

    def reset_inits(self):
        """Set all initial conditions."""
        for parseq in self.parseqs:
            inits = getattr(self.inits, parseq.name, None)
            if inits is not None:
                parseq(inits)

    def _update_inputs(self, idx):
        """Update the actual values with the |UnitTest.nexts| data of
        the given index."""
        for parseq in self.parseqs:
            if hasattr(self.nexts, parseq.name):
                parseq(getattr(self.nexts, parseq.name)[idx])

    def _update_outputs(self, idx):
        """Update the |UnitTest.results| data with the actual values of
        the given index."""
        for parseq in self.parseqs:
            if hasattr(self.results, parseq.name):
                getattr(self.results, parseq.name)[idx] = parseq.values


class _Open:
    __readingerror = (
        "Reading is not possible at the moment.  Please see the "
        "documentation on class `Open` of module `testtools` "
        "for further information."
    )

    def __init__(self, path, mode, *args, **kwargs):
        # pylint: disable=unused-argument
        # all further positional and keyword arguments are ignored.
        self.path = path.replace(os.sep, "/")
        self.mode = mode
        self.texts = []
        self.entered = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exception, message, traceback_):
        self.close()

    def read(self):
        """Raise a |NotImplementedError| in any case."""
        raise NotImplementedError(self.__readingerror)

    def readline(self):
        """Raise a |NotImplementedError| in any case."""
        raise NotImplementedError(self.__readingerror)

    def readlines(self):
        """Raise a |NotImplementedError| in any case."""
        raise NotImplementedError(self.__readingerror)

    def write(self, text):
        """Replace the `write` method of file objects."""
        self.texts.append(text)

    def writelines(self, lines):
        """Replace the `writelines` method of file objects."""
        self.texts.extend(lines)

    def close(self):
        """Replace the `close` method of file objects."""
        text = "".join(self.texts)
        maxchars = len(self.path)
        lines = []
        for line in text.split("\n"):
            if not line:
                line = "<BLANKLINE>"
            lines.append(line)
            maxchars = max(maxchars, len(line))
        text = "\n".join(lines)
        print("~" * maxchars)
        print(self.path)
        print("-" * maxchars)
        print(text)
        print("~" * maxchars)


class Open:
    """Replace |open| in doctests temporarily.

    Class |Open| to intended to make writing to files visible and testable
    in docstrings.  Therefore, Python's built-in function |open| is
    temporarily replaced by another object, printing the filename and the
    file content, as shown in the following example:

    >>> import os
    >>> path = os.path.join("folder", "test.py")
    >>> from hydpy import Open
    >>> with Open():
    ...     with open(path, "w") as file_:
    ...         file_.write("first line\\n")
    ...         file_.writelines(["\\n", "third line\\n"])
    ~~~~~~~~~~~~~~
    folder/test.py
    --------------
    first line
    <BLANKLINE>
    third line
    <BLANKLINE>
    ~~~~~~~~~~~~~~

    Note that, for simplicity, the UNIX style path separator `/` is used
    to print the file path on all systems.

    Class |Open| is rather restricted at the moment.  Functionalities
    like reading are not supported so far:

    >>> with Open():
    ...     with open(path, "r") as file_:
    ...         file_.read()
    Traceback (most recent call last):
    ...
    NotImplementedError: Reading is not possible at the moment.  \
Please see the documentation on class `Open` of module `testtools` \
for further information.

    >>> with Open():
    ...     with open(path, "r") as file_:
    ...         file_.readline()
    Traceback (most recent call last):
    ...
    NotImplementedError: Reading is not possible at the moment.  \
Please see the documentation on class `Open` of module `testtools` \
for further information.

    >>> with Open():
    ...     with open(path, "r") as file_:
    ...         file_.readlines()
    Traceback (most recent call last):
    ...
    NotImplementedError: Reading is not possible at the moment.  \
Please see the documentation on class `Open` of module `testtools` \
for further information.
    """

    def __init__(self):
        self.open = builtins.open

    def __enter__(self):
        builtins.open = _Open
        return self

    def __exit__(self, exception, message, traceback_):
        builtins.open = self.open


class TestIO:
    """Prepare an environment for testing IO functionalities.

    Primarily, |TestIO| changes the current working during the
    execution of with| blocks.  Inspecting your current working
    directory, |os| will likely find no file called `testfile.txt`:

    >>> import os
    >>> os.path.exists("testfile.txt")
    False

    If some tests require writing such a file, this should be done
    within HydPy's `iotesting` folder in subpackage `tests`, which
    is achieved by applying the `with` statement on |TestIO|:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     open("testfile.txt", "w").close()
    ...     print(os.path.exists("testfile.txt"))
    True

    After the `with` block, the working directory is reset automatically:

    >>> os.path.exists("testfile.txt")
    False

    Nevertheless, `testfile.txt` still exists in the folder `iotesting`:

    >>> with TestIO():
    ...     print(os.path.exists("testfile.txt"))
    True

    Optionally, files and folders created within the current `with` block
    can be removed automatically by setting `clear_own` to |True|
    (modified files and folders are not affected):

    >>> with TestIO(clear_own=True):
    ...     open("testfile.txt", "w").close()
    ...     os.makedirs("testfolder")
    ...     print(os.path.exists("testfile.txt"),
    ...           os.path.exists("testfolder"))
    True True
    >>> with TestIO(clear_own=True):
    ...     print(os.path.exists("testfile.txt"),
    ...           os.path.exists("testfolder"))
    True False

    Alternatively, all files and folders contained in folder `iotesting`
    can be removed after leaving the `with` block:

    >>> with TestIO(clear_all=True):
    ...     os.makedirs("testfolder")
    ...     print(os.path.exists("testfile.txt"),
    ...           os.path.exists("testfolder"))
    True True
    >>> with TestIO(clear_own=True):
    ...     print(os.path.exists("testfile.txt"),
    ...           os.path.exists("testfolder"))
    False False

    For just clearing the `iofolder`, one can call method |TestIO.clear|
    alternatively:

    >>> with TestIO():
    ...     open("testfile.txt", "w").close()
    ...     print(os.path.exists("testfile.txt"))
    True
    >>> TestIO.clear()
    >>> with TestIO():
    ...     print(os.path.exists("testfile.txt"))
    False

    Note that class |TestIO| copies all eventually generated `.coverage`
    files into the `test` subpackage to assure no covered lines are
    reported as uncovered.
    """

    _clear_own: bool
    _clear_all: bool
    _path: str | None
    _olds: list[str] | None

    def __init__(self, clear_own: bool = False, clear_all: bool = False) -> None:
        self._clear_own = clear_own
        self._clear_all = clear_all
        self._path = None
        self._olds = None

    def __enter__(self) -> TestIO:
        assert (path := os.getcwd()) is not None
        self._path = path
        iotestingpath: str = iotesting.__path__[0]
        os.chdir(os.path.join(iotestingpath))
        if self._clear_own:
            self._olds = sorted(os.listdir("."))
        return self

    def __exit__(
        self,
        exception_type: type[BaseException],
        exception_value: BaseException,
        traceback_: types.TracebackType,
    ) -> None:
        for file in sorted(os.listdir(".")):
            if (file != "__init__.py") and (
                self._clear_all
                or (
                    self._clear_own
                    and ((olds := self._olds) is not None)
                    and (file not in olds)
                )
            ):
                if os.path.exists(file):
                    if os.path.isfile(file):
                        os.remove(file)
                    else:
                        shutil.rmtree(file)
        assert (path := self._path) is not None
        os.chdir(path)

    @classmethod
    def clear(cls) -> None:
        """Remove all files from the `iotesting` folder."""
        with cls(clear_all=True):
            pass


def make_abc_testable(abstract: type[T]) -> type[T]:
    """Return a concrete version of the given abstract base class for testing purposes.

    Abstract base classes cannot be (and, at least in production code, should not be)
    instantiated:

    >>> from hydpy.core.netcdftools import NetCDFVariable
    >>> var = NetCDFVariable()  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: Can't instantiate abstract class NetCDFVariable with...

    However, it is convenient to do so for testing (partly) abstract base classes in
    doctests.  The derived class returned by function |make_abc_testable| is identical
    with the original one, except that its protection against initialisation is
    disabled:

    >>> from hydpy import make_abc_testable, classname
    >>> var = make_abc_testable(NetCDFVariable)("filepath")

    To avoid confusion, |make_abc_testable| appends an underscore to the original class
    name:

    >>> classname(var)
    'NetCDFVariable_'
    """
    concrete = type(abstract.__name__ + "_", (abstract,), {})
    concrete.__abstractmethods__ = frozenset()  # type: ignore[attr-defined]
    return concrete


@contextlib.contextmanager
def mock_datetime_now(testdatetime):
    """Let class method |datetime.datetime.now| of class |datetime.datetime|
    of module |datetime| return the given date for testing purposes within
    a "with-block".

    >>> import datetime
    >>> testdate = datetime.datetime(2000, 10, 1, 12, 30, 0, 999)
    >>> testdate == datetime.datetime.now()
    False
    >>> from hydpy import classname
    >>> classname(datetime.datetime)
    'datetime'
    >>> from hydpy.core.testtools import mock_datetime_now
    >>> with mock_datetime_now(testdate):
    ...     testdate == datetime.datetime.now()
    ...     classname(datetime.datetime)
    True
    '_DateTime'
    >>> testdate == datetime.datetime.now()
    False
    >>> classname(datetime.datetime)
    'datetime'

    The following test shows that mocking |datetime.datetime| does not
    interfere with initialising |Date| objects and that the relevant
    exceptions are properly handled:

    >>> from hydpy import Date
    >>> with mock_datetime_now(testdate):
    ...     Date(datetime.datetime(2000, 10, 1, 12, 30, 0, 999))
    Traceback (most recent call last):
    ...
    ValueError: While trying to initialise a `Date` object based on \
argument `2000-10-01 12:30:00.000999`, the following error occurred: \
For `Date` instances, the microsecond must be zero, \
but for the given `datetime` object it is `999` instead.

    >>> classname(datetime.datetime)
    'datetime'
    """
    _datetime = datetime.datetime

    class _DateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):  # pylint: disable=unused-argument
            return testdatetime

    try:
        datetime.datetime = _DateTime
        yield
    finally:
        datetime.datetime = _datetime


class NumericalDifferentiator:
    """Approximate the derivatives of |ModelSequence| values based on the finite
    difference approach.

    .. _`here`: https://en.wikipedia.org/wiki/Finite_difference_coefficient

    Class |NumericalDifferentiator| is thought for testing purposes only.  See, for
    example, the documentation on method |kinw_model.Calc_RHMDH_V1|, which uses a
    |NumericalDifferentiator| object to validate that this method calculates the
    derivative of sequence |kinw_aides.RHM| (`ysequence`) with respect to sequence
    |kinw_states.H| (`xsequence`) correctly. Therefore, it must know the relationship
    between |kinw_aides.RHM| and |kinw_states.H|, being defined by method
    |kinw_model.Calc_RHM_V1|.

    See also the documentation on method |kinw_model.Calc_AMDH_UMDH_V1|, which explains
    how to apply class |NumericalDifferentiator| on multiple target sequences
    (`ysequences`).  Note that, in order to calculate the correct derivatives of
    sequences |kinw_aides.AM| and |kinw_aides.UM|, we need not only to pass
    |kinw_model.Calc_AM_UM_V1|, but also methods |kinw_model.Calc_RHM_V1| and
    |kinw_model.Calc_RHV_V1|, as sequences |kinw_aides.RHM| and |kinw_aides.RHV|, which
    are required for calculating |kinw_aides.AM| and |kinw_aides.UM|, depend on
    |kinw_states.H| themselves.

    Numerical approximations of derivatives are of limited precision.
    |NumericalDifferentiator| achieves the second order of accuracy due to using the
    coefficients given `here`_.  If results are too inaccurate, you might improve them
    by changing the finite difference method (`backward` or `central` instead of
    `forward`) or by changing the default interval width `dx`.
    """

    __NMBNODES = 3
    __XSHIFTS = {
        "forward": numpy.array([0.0, 1.0, 2.0]),
        "backward": numpy.array([-2.0, -1.0, 0.0]),
        "central": numpy.array([-1.0, 0.0, 1.0]),
    }
    __YCOEFFS = {
        "forward": numpy.array([-3.0, 4.0, -1.0]) / 2.0,
        "backward": numpy.array([1.0, -4.0, 3]) / 2.0,
        "central": numpy.array([-1.0, 0.0, 1]) / 2.0,
    }

    def __init__(
        self,
        *,
        xsequence: sequencetools.ModelSequence,
        ysequences: Iterable[sequencetools.ModelSequence],
        methods: Iterable[modeltools.Method],
        dx: float = 1e-6,
        method: Literal["forward", "central", "backward"] = "forward",
    ):
        self._xsequence = xsequence
        self._ysequences = tuple(ysequences)
        self._methods = tuple(methods)
        self._span = dx / 2.0
        self._method = method

    @property
    def _ycoeffs(self) -> NDArrayFloat:
        return self.__YCOEFFS[self._method] / self._span

    @property
    def _xshifts(self) -> NDArrayFloat:
        return self.__XSHIFTS[self._method] * self._span

    @property
    def _yvalues(self) -> dict[sequencetools.ModelSequence, NDArrayFloat]:
        xvalues = copy.deepcopy(self._xsequence.values)
        ndim = self._ysequences[0].NDIM
        assert all(ndim == seq.NDIM for seq in self._ysequences)
        nmb = self._ysequences[0].numberofvalues
        assert all(nmb == seq.numberofvalues for seq in self._ysequences)
        yvalues = {
            ysequence: numpy.empty((nmb, self.__NMBNODES))
            for ysequence in self._ysequences
        }
        try:
            for idx, shift in enumerate(self._xshifts):
                self._xsequence.values = xvalues + shift
                for method in self._methods:
                    method()
                for ysequence in self._ysequences:
                    yvalues[ysequence][:, idx] = copy.deepcopy(ysequence.values)
            return yvalues
        finally:
            self._xsequence.values = xvalues

    @property
    def _derivatives(self) -> dict[sequencetools.ModelSequence, NDArrayFloat]:
        return {
            ysequence: numpy.dot(self._ycoeffs, yvalues.T)
            for ysequence, yvalues in self._yvalues.items()
        }

    def __call__(self) -> None:
        for ysequence, derivatives in self._derivatives.items():
            print(f"d_{ysequence.name}/d_{self._xsequence.name}", end=": ")
            objecttools.print_vector(derivatives, width=1000)


def update_integrationtests(
    applicationmodel: types.ModuleType | str,
    resultfilepath: str = "update_integrationtests.txt",
) -> None:
    """Write the docstring of the given application model, updated with the current
    simulation results, to file.

    Sometimes, even tiny model-related changes bring a great deal of work concerning
    *HydPy's* integration test strategy.  For example, if you modify the value of a
    fixed parameter, the results of possibly dozens of integration tests of your
    application model might become wrong.  In such situations, function
    |update_integrationtests| helps you in replacing all integration tests results at
    once.  Therefore, it calculates the new results, updates the old module docstring
    and writes it.  You only need to copy-paste the printed result into the affected
    module.  But be aware that function |update_integrationtests| cannot guarantee the
    correctness of the new results.  Whenever in doubt if the new results are really
    correct under all possible conditions, you should inspect and replace each
    integration test result manually.

    In the following example, we disable method |hydpytools.HydPy.simulate|
    temporarily.  Accordingly, application model |conv_nn| does not pass any output to
    its outlet nodes, which is why the last four columns of both integration test
    tables now contain zero value only (we can perform this mocking-based test in
    Python-mode only):

    >>> from hydpy import pub, TestIO, update_integrationtests
    >>> from unittest import mock
    >>> pass_output = "hydpy.core.hydpytools.HydPy.simulate"
    >>> with TestIO(), pub.options.usecython(False), mock.patch(pass_output):
    ...     update_integrationtests("conv_nn", "temp.txt")
    ...     with open("temp.txt") as resultfile:
    ...         print(resultfile.read())  # doctest: +ELLIPSIS
    Number of replacements: 2
    <BLANKLINE>
    ... test()
    |       date |      inputs |                outputs | in1 | in2 | out1 | out2 \
| out3 | out4 |
    ------------------------------------------------------------------------------\
---------------
    | 2000-01-01 | nan     nan | nan  nan  nan      nan | 1.0 | 4.0 |  nan |  nan \
|  nan |  nan |
    | 2000-01-02 | nan     nan | nan  nan  nan      nan | 2.0 | nan |  nan |  nan \
|  nan |  nan |
    | 2000-01-03 | nan     nan | nan  nan  nan      nan | nan | nan |  nan |  nan \
|  nan |  nan |
    <BLANKLINE>
    ... test()
    |       date |      inputs |                outputs | in1 | in2 | out1 | out2 \
| out3 | out4 |
    ------------------------------------------------------------------------------\
---------------
    | 2000-01-01 | nan     nan | nan  nan  nan      nan | 1.0 | 4.0 |  nan |  nan \
|  nan |  nan |
    | 2000-01-02 | nan     nan | nan  nan  nan      nan | 2.0 | nan |  nan |  nan \
|  nan |  nan |
    | 2000-01-03 | nan     nan | nan  nan  nan      nan | nan | nan |  nan |  nan \
|  nan |  nan |
    <BLANKLINE>
    """
    module = importtools.load_modelmodule(applicationmodel)
    assert (docstring := module.__doc__) is not None
    stringio = io.StringIO
    with stringio() as file_, contextlib.redirect_stdout(file_):
        module.tester.perform_tests()
        result = file_.getvalue()
    oldlines: list[str] = []
    newlines: list[str] = []
    expected, got = False, False
    nmb_replacements = 0
    for line in result.split("\n"):
        line = line.strip()
        if line == "Expected:":
            expected = True
        elif line == "Got:":
            expected = False
            got = True
        elif got and ("***********************************" in line):
            expected = False
            got = False
            if oldlines or newlines:
                nmb_replacements += 1
                docstring = docstring.replace("\n".join(oldlines), "\n".join(newlines))
                docstring = docstring.replace(
                    "\n".join(f"    {line}" for line in oldlines),
                    "\n".join(f"    {line}" for line in newlines),
                )
            oldlines, newlines = [], []
        elif expected:
            oldlines.append(line)
        elif got:
            newlines.append(line)
    with open(resultfilepath, "w", encoding="utf-8") as resultfile:
        resultfile.write(f"Number of replacements: {nmb_replacements}\n\n")
        resultfile.write(docstring)


def _enumerate(variables: tuple[type[variabletools.Variable], ...]) -> str:
    return objecttools.enumeration(
        v.__name__ for v in variabletools.sort_variables(variables)
    )


def check_methodorder(model: modeltools.Model, indent: int = 0) -> str:
    """Check that *HydPy* calls the methods of the given application model in the
    correct order for each simulation step.

    The purpose of this function is to help model developers ensure that each method
    uses only the values of those sequences that have been calculated by other methods
    beforehand.  *HydPy's* test routines apply |check_methodorder| automatically on
    each available application model. Alternatively, you can also execute it at the end
    of the docstring of an individual application model "manually", which suppresses
    the automatic execution and allows to check and discuss exceptional cases where
    |check_methodorder| generates false alarms.

    Function |check_methodorder| relies on the class constants `REQUIREDSEQUENCES`,
    `UPDATEDSEQUENCES`, and `RESULTSEQUENCES` of all relevant |Method| subclasses.
    Hence, the correctness of its results depends on the correctness of these tuples.
    However, even if those tuples are well-defined, one cannot expect
    |check_methodorder| to catch all kinds of order-related errors.  For example,
    consider the case where one method calculates only some values of a
    multi-dimensional sequence and another method the  remaining ones.
    |check_methodorder|  would not report anything when a third method, relying on the
    completeness of the sequence's values, were called after the first but before the
    second method.

    We use the quite complex model |lland_knauf| as an example.  |check_methodorder|
    does not report any problems:

    >>> from hydpy.core.testtools import check_methodorder
    >>> from hydpy.models.lland_knauf import Model
    >>> print(check_methodorder(Model))
    <BLANKLINE>

    To show how |check_methodorder| reports errors, we modify the `RESULTSEQUENCES`
    tuples of methods |lland_model.Calc_TKor_V1|, |lland_model.Calc_TZ_V1|, and
    |lland_model.Calc_QA_V1|:

    >>> from hydpy.models.lland.lland_model import (
    ...     Calc_TKor_V1, Calc_TZ_V1, Calc_QA_V1)
    >>> results_tkor = Calc_TKor_V1.RESULTSEQUENCES
    >>> results_tz = Calc_TZ_V1.RESULTSEQUENCES
    >>> results_qa = Calc_QA_V1.RESULTSEQUENCES
    >>> Calc_TKor_V1.RESULTSEQUENCES = ()
    >>> Calc_TZ_V1.RESULTSEQUENCES = ()
    >>> Calc_QA_V1.RESULTSEQUENCES += results_tkor

    Now, none of the relevant models calculates the value of sequence
    |lland_fluxes.TZ|.  For |lland_fluxes.TKor|, there is still a method
    (|lland_model.Calc_QA_V1|) calculating its values, but at a too-late stage of the
    simulation step:

    >>> print(check_methodorder(Model))  # doctest: +ELLIPSIS
    Method Calc_SaturationVapourPressure_V1 requires the following sequences, which \
are not among the result sequences of any of its predecessors: TKor
    ...
    Method Update_ESnow_V1 requires the following sequences, which are not among the \
result sequences of any of its predecessors: TKor and TZ

    To tidy up, we need to revert the above changes:

    >>> Calc_TKor_V1.RESULTSEQUENCES = results_tkor
    >>> Calc_TZ_V1.RESULTSEQUENCES = results_tz
    >>> Calc_QA_V1.RESULTSEQUENCES = results_qa
    >>> print(check_methodorder(Model))
    <BLANKLINE>
    """
    blanks = " " * indent
    results: list[str] = []
    excluded = (
        sequencetools.InputSequence,
        sequencetools.InletSequence,
        sequencetools.ObserverSequence,
        sequencetools.ReceiverSequence,
        sequencetools.StateSequence,
        sequencetools.LogSequence,
    )
    methods = tuple(model.get_methods(skip=("ADD_METHODS", "INTERFACE_METHODS")))
    for idx, method1 in enumerate(methods):
        required = {
            seq for seq in method1.REQUIREDSEQUENCES if not issubclass(seq, excluded)
        }
        for method0 in methods[:idx]:
            for seq in itertools.chain(
                method0.RESULTSEQUENCES, method0.UPDATEDSEQUENCES
            ):
                if seq in required:
                    required.remove(seq)
        if required:
            results.append(
                f"{blanks}Method {method1.__name__} requires the following sequences, "
                f"which are not among the result sequences of any of its "
                f"predecessors: {_enumerate(tuple(required))}"
            )
    return "\n".join(results)


def check_selectedvariables(method: type[modeltools.Method], indent: int = 0) -> str:
    """Perform consistency checks regarding the |Parameter| and |Sequence_|
    subclasses selected by the given |Method| subclass.

    The purpose of this function is to help model developers ensure that the class
    tuples `CONTROLPARAMETERS`, `DERIVEDPARAMETERS`, `FIXEDPARAMETERS`,
    `SOLVERPARAMETERS`, `REQUIREDSEQUENCES`, `UPDATEDSEQUENCES`, and `RESULTSEQUENCES`
    contain the correct parameter and sequence subclasses.  *HydPy's* test routines
    apply |check_selectedvariables| automatically on each method of each available
    application model.  Alternatively, you can also execute it at the end of the
    docstring of an individual |Method| subclass "manually", which suppresses the
    automatic execution and allows to check and discuss exceptional cases where
    |check_selectedvariables| generates false alarms.

    Do not expect |check_selectedvariables| to catch all possible errors.  Also, false
    positives might occur.  However, in our experience, function
    |check_selectedvariables| is of great help to prevent the most common mistakes when
    defining the parameter and sequence classes relevant for a specific method.

    As an example, we select method |evap_model.Calc_WindSpeed2m_V1| of base model
    |evap|.  |check_selectedvariables| does not reportany problems:

    >>> from hydpy.core.testtools import check_selectedvariables
    >>> from hydpy.models.evap.evap_model import Calc_WindSpeed10m_V1
    >>> print(check_selectedvariables(Calc_WindSpeed10m_V1))
    <BLANKLINE>

    To show how |check_selectedvariables| reports errors, we clear the
    `RESULTSEQUENCES` tuple of method |evap_model.Calc_WindSpeed10m_V1|.  Now
    |check_selectedvariables| realises the usage of the factor sequence object
    `windspeed10m` within the source code of method |evap_model.Calc_WindSpeed10m_V1|,
    which is neither available within the `REQUIREDSEQUENCES`, the `UPDATEDSEQUENCES`,
    nor the`RESULTSEQUENCES` tuple:

    >>> resultseqs = Calc_WindSpeed10m_V1.RESULTSEQUENCES
    >>> Calc_WindSpeed10m_V1.RESULTSEQUENCES = ()
    >>> print(check_selectedvariables(Calc_WindSpeed10m_V1))
    Definitely missing: windspeed10m

    After putting the wrong flux sequence class |evap_factors.WindSpeed2m| into the
    tuple, we get an additional warning pointing to our mistake:

    >>> from hydpy.models.evap.evap_factors import WindSpeed2m
    >>> Calc_WindSpeed10m_V1.RESULTSEQUENCES = WindSpeed2m,
    >>> print(check_selectedvariables(Calc_WindSpeed10m_V1))
    Definitely missing: windspeed10m
    Possibly erroneously selected (RESULTSEQUENCES): WindSpeed2m

    Method |evap_model.Calc_WindSpeed10m_V1| uses
    |evap_model.Return_AdjustedWindSpeed_V1| as a submethod.  Hence,
    |evap_model.Calc_WindSpeed10m_V1| most likely needs to select each variable
    selected by |evap_model.Return_AdjustedWindSpeed_V1|.  After adding additional
    variables to the `DERIVEDPARAMETERS` tuple of
    |evap_model.Return_AdjustedWindSpeed_V1|, we get another warning message:

    >>> from hydpy.models.evap.evap_model import Return_AdjustedWindSpeed_V1
    >>> from hydpy.models.evap.evap_derived import Days, Hours, Seconds
    >>> derivedpars = Return_AdjustedWindSpeed_V1.DERIVEDPARAMETERS
    >>> Return_AdjustedWindSpeed_V1.DERIVEDPARAMETERS = Days, Hours, Seconds
    >>> print(check_selectedvariables(Calc_WindSpeed10m_V1))
    Definitely missing: windspeed10m
    Possibly missing (DERIVEDPARAMETERS):
        Return_AdjustedWindSpeed_V1: Seconds, Hours, and Days
    Possibly erroneously selected (RESULTSEQUENCES): WindSpeed2m

    Finally, |check_selectedvariables| checks for duplicates both within and between
    the different tuples:

    >>> from hydpy.models.evap.evap_inputs import WindSpeed, RelativeHumidity
    >>> requiredseqs = Calc_WindSpeed10m_V1.REQUIREDSEQUENCES
    >>> Calc_WindSpeed10m_V1.REQUIREDSEQUENCES = WindSpeed, WindSpeed, RelativeHumidity
    >>> Calc_WindSpeed10m_V1.UPDATEDSEQUENCES = RelativeHumidity,
    >>> print(check_selectedvariables(Calc_WindSpeed10m_V1))
    Definitely missing: windspeed10m
    Possibly missing (DERIVEDPARAMETERS):
        Return_AdjustedWindSpeed_V1: Seconds, Hours, and Days
    Possibly erroneously selected (REQUIREDSEQUENCES): RelativeHumidity
    Possibly erroneously selected (UPDATEDSEQUENCES): RelativeHumidity
    Possibly erroneously selected (RESULTSEQUENCES): WindSpeed2m
    Duplicates: RelativeHumidity and WindSpeed

    To tidy up, we need to revert the above changes:

    >>> Calc_WindSpeed10m_V1.RESULTSEQUENCES = resultseqs
    >>> Return_AdjustedWindSpeed_V1.DERIVEDPARAMETERS = derivedpars
    >>> Calc_WindSpeed10m_V1.REQUIREDSEQUENCES = requiredseqs
    >>> Calc_WindSpeed10m_V1.UPDATEDSEQUENCES = ()
    >>> print(check_selectedvariables(Calc_WindSpeed10m_V1))
    <BLANKLINE>

    Some methods, such as |arma_model.Pick_Q_V1|, of base model |arma| rely on the
    `len` attribute of 1-dimensional sequences.  Function |check_selectedvariables|
    does not report false alarms in such cases:

    >>> from hydpy.models.arma.arma_model import Pick_Q_V1
    >>> print(check_selectedvariables(Pick_Q_V1))
    <BLANKLINE>

    Some methods such as |evap_model.Calc_PotentialEvapotranspiration_V1| of base model
    |evap| rely on the |KeywordParameter1D.entrymin| attribute of |KeywordParameter1D|
    instances.  Function |check_selectedvariables| does not report false alarms in such
    cases:

    >>> from hydpy.models.evap.evap_model import Calc_PotentialEvapotranspiration_V1
    >>> from hydpy.models.evap.evap_control import MonthFactor
    >>> MonthFactor in Calc_PotentialEvapotranspiration_V1.CONTROLPARAMETERS
    True
    >>> print(check_selectedvariables(Calc_PotentialEvapotranspiration_V1))
    <BLANKLINE>

    Some methods, such as |evap_model.Calc_PotentialEvapotranspiration_V2| of base
    model |evap|, rely on the |KeywordParameter2D.rowmin| or the
    |KeywordParameter2D.columnmin| attribute of |KeywordParameter2D| instances.
    Function |check_selectedvariables| does not report false alarms in such cases:

    >>> from hydpy.models.evap.evap_model import Calc_PotentialEvapotranspiration_V2
    >>> from hydpy.models.evap.evap_control import LandMonthFactor
    >>> LandMonthFactor in Calc_PotentialEvapotranspiration_V2.CONTROLPARAMETERS
    True
    >>> print(check_selectedvariables(Calc_PotentialEvapotranspiration_V2))
    <BLANKLINE>

    Some methods, such as |lland_model.Update_ESnow_V1| of base model |lland|, update a
    sequence (meaning, they require its old value and calculate a new one), but their
    submethods (in this case |lland_model.Return_BackwardEulerError_V1|) just require
    them as input.  Function |check_selectedvariables| does not report false alarms in
    such cases:

    >>> from hydpy.models.lland.lland_model import Update_ESnow_V1
    >>> print(check_selectedvariables(Update_ESnow_V1))
    <BLANKLINE>

    Similarly, methods such as |ga_model.Perform_GARTO_V1| calculate sequence values
    from scratch but require submethods for updating them:

    >>> from hydpy.models.ga.ga_model import Perform_GARTO_V1
    >>> print(check_selectedvariables(Perform_GARTO_V1))
    <BLANKLINE>

    If a |AutoMethod| subclass selects multiple submethods and one requires sequence
    values that are calculated by another one, |check_selectedvariables| does not
    report this as a problem if they are listed in the correct order, as is the case
    for method |evap_model.Determine_InterceptionEvaporation_V1|:

    >>> from hydpy.models.evap.evap_model import Determine_InterceptionEvaporation_V1
    >>> print(check_selectedvariables(Determine_InterceptionEvaporation_V1))
    <BLANKLINE>

    However, when reversing the submethod order, |check_selectedvariables| complains
    that |evap_model.Determine_InterceptionEvaporation_V1| does not specify all
    requirements of the first submethod |evap_model.Calc_InterceptionEvaporation_V1|,
    which would be calculated too late by the second
    (|evap_model.Calc_InterceptedWater_V1|) and the third
    (|evap_model.Calc_PotentialInterceptionEvaporation_V3|) submethod:

    >>> submethods = Determine_InterceptionEvaporation_V1.SUBMETHODS
    >>> Determine_InterceptionEvaporation_V1.SUBMETHODS = tuple(reversed(submethods))
    >>> print(check_selectedvariables(Determine_InterceptionEvaporation_V1))
    Possibly missing (REQUIREDSEQUENCES):
        Calc_InterceptionEvaporation_V1: InterceptedWater and \
PotentialInterceptionEvaporation

    >>> Determine_InterceptionEvaporation_V1.SUBMETHODS = submethods
    """
    # pylint: disable=too-many-branches
    # ToDo: needs refactoring
    prefixes = (
        "con",
        "der",
        "fix",
        "sol",
        "inp",
        "fac",
        "flu",
        "sta",
        "old",
        "new",
        "log",
        "aid",
        "inl",
        "out",
        "rec",
        "sen",
    )
    groups = (
        "CONTROLPARAMETERS",
        "DERIVEDPARAMETERS",
        "FIXEDPARAMETERS",
        "SOLVERPARAMETERS",
        "REQUIREDSEQUENCES",
        "UPDATEDSEQUENCES",
        "RESULTSEQUENCES",
    )
    blanks = " " * indent
    results: list[str] = []
    # search for variables that are used in the source code but not among the selected
    # variables:
    source = inspect.getsource(method.__call__)
    varnames_source: set[str] = set()
    varnames_candidates: set[str] = set(method.__call__.__code__.co_names)
    names_builtin = set(dir(builtins))
    for varname in tuple(varnames_candidates):
        if (varname in names_builtin) or (f"modelutils.{varname}" in source):
            varnames_candidates.remove(varname)
    for varname, prefix in itertools.product(varnames_candidates, prefixes):
        if f"{prefix}.{varname}" in source:
            if varname.startswith("len_"):
                varname = varname[4:]
            else:
                for suffix in ("_rowmin", "_columnmin", "_entrymin"):
                    if varname.endswith(suffix):
                        varname = varname[1 : -len(suffix)]
                varname = varname.replace("_callback", "")
            varnames_source.add(varname)
    varnames_selected: set[str] = set()
    for group in groups:
        varnames_selected.update(g.__name__.lower() for g in getattr(method, group))
    varnames_diff: list[str] = sorted(varnames_source - varnames_selected)
    if varnames_diff:
        results.append(
            f"{blanks}Definitely missing: {objecttools.enumeration(varnames_diff)}"
        )

    # search for variables selected by at least one submethod but not by the method
    # calling these submethods:
    vars_method: set[type[variabletools.Variable]]
    vars_submethods: set[type[variabletools.Variable]]
    for group in groups:
        vars_method = set(getattr(method, group))
        found_problem = False
        for idx_submethod, submethod in enumerate(method.SUBMETHODS):
            vars_submethods = set(getattr(submethod, group))
            if group == "REQUIREDSEQUENCES":
                vars_method.update(
                    set(method.UPDATEDSEQUENCES).intersection(
                        submethod.REQUIREDSEQUENCES
                    )
                )
                if issubclass(
                    method, (modeltools.AutoMethod, modeltools.SetAutoMethod)
                ):
                    for previous in method.SUBMETHODS[:idx_submethod]:
                        vars_submethods.difference_update(previous.RESULTSEQUENCES)
            diff = vars_submethods - vars_method
            if diff and (group == "UPDATEDSEQUENCES"):
                diff.difference_update(set(method.RESULTSEQUENCES))
            if diff:
                if not found_problem:
                    found_problem = True
                    results.append(f"{blanks}Possibly missing ({group}):")
                results.append(
                    f"{blanks}    {submethod.__name__}: {_enumerate(tuple(diff))}"
                )

    # search for selected variables that are neither used within the source code nor
    # selected by any submethod:
    group2vars_method: dict[str, set[type[variabletools.Variable]]] = {
        g: set(getattr(method, g)) for g in groups
    }
    group2vars_submethods: dict[str, set[type[variabletools.Variable]]] = {
        g: set() for g in groups
    }
    for submethod in method.SUBMETHODS:
        for group, vars_submethods in group2vars_submethods.items():
            vars_submethods.update(getattr(submethod, group))
    for group, vars_method in group2vars_method.items():
        vars_submethods = group2vars_submethods[group]
        diff_ = tuple(
            method
            for method in vars_method - vars_submethods
            if method.__name__.lower() not in varnames_source
        )
        if diff_:
            results.append(
                f"{blanks}Possibly erroneously selected ({group}): "
                f"{_enumerate(diff_)}"
            )

    # search for variables that are selected multiple times:
    vars1: tuple[type[variabletools.Variable], ...]
    vars2: tuple[type[variabletools.Variable], ...]
    dupl: set[type[variabletools.Variable]] = set()
    for group1 in groups:
        vars1 = getattr(method, group1)
        for var in vars1:
            if vars1.count(var) > 1:
                dupl.add(var)
        for group2 in groups:
            if group1 is not group2:
                vars2 = getattr(method, group2)
                dupl.update(set(vars1).intersection(vars2))
    if dupl:
        results.append(f"{blanks}Duplicates: {_enumerate(tuple(dupl))}")
    return "\n".join(results)


def perform_consistencychecks(
    applicationmodel: types.ModuleType | str, indent: int = 0
) -> str:
    """Perform all available consistency checks for the given application model.

    At the moment, function |perform_consistencychecks| calls function
    |check_selectedvariables| for each relevant model method and function
    |check_methodorder| for the application model itself.  Note that
    |perform_consistencychecks| executes only those checks not already executed in the
    doctest of the respective method or model.  This alternative allows model
    developers to perform the tests themselves whenever exceptional cases result in
    misleading error reports and discuss any related potential pitfalls in the official
    documentation.

    As an example, we apply |perform_consistencychecks| on the application model
    |lland_knauf|.  It does not report any potential problems (not already discussed in
    the documentation on the individual model methods):

    >>> from hydpy.core.testtools import perform_consistencychecks
    >>> print(perform_consistencychecks("lland_knauf"))
    <BLANKLINE>

    To show how |perform_consistencychecks| reports errors, we modify the
    `RESULTSEQUENCES` tuple of method |lland_model.Calc_NKor_V1|:

    >>> from hydpy.models.lland.lland_model import Calc_NKor_V1
    >>> resultsequences = Calc_NKor_V1.RESULTSEQUENCES
    >>> Calc_NKor_V1.RESULTSEQUENCES = ()
    >>> print(perform_consistencychecks("lland_knauf"))
    Potential consistency problems for individual methods:
       Method Calc_NKor_V1:
            Definitely missing: nkor
    Potential consistency problems between methods:
        Method Calc_NBes_Inzp_V1 requires the following sequences, which are not among \
the result sequences of any of its predecessors: NKor
        Method Calc_QBGZ_V1 requires the following sequences, which are not among the \
result sequences of any of its predecessors: NKor
        Method Calc_QDGZ_V1 requires the following sequences, which are not among the \
result sequences of any of its predecessors: NKor
        Method Calc_QAH_V1 requires the following sequences, which are not among the \
result sequences of any of its predecessors: NKor

    To tidy up, we need to revert the above changes:

    >>> Calc_NKor_V1.RESULTSEQUENCES = resultsequences
    >>> print(perform_consistencychecks("lland_knauf"))
    <BLANKLINE>
    """
    blanks = " " * indent
    model = importtools.prepare_model(applicationmodel)
    results: list[str] = []
    method2errors: dict[str, str] = {}
    for method in model.get_methods():
        assert (methoddoc := method.__doc__) is not None
        if "check_selectedvariables(" not in methoddoc:
            subresult = check_selectedvariables(method=method, indent=indent + 8)
            if subresult:
                method2errors[method.__name__] = subresult
    if method2errors:
        results.append(
            f"{blanks}Potential consistency problems for individual methods:"
        )
        for methodname, errors in method2errors.items():
            results.append(f"{blanks}   Method {methodname}:")
            results.append(errors)
    assert (modeldoc := model.__doc__) is not None
    if "check_methodorder(" not in modeldoc:
        subresult = check_methodorder(model, indent + 4)
        if subresult:
            results.append(f"{blanks}Potential consistency problems between methods:")
            results.append(subresult)
    return "\n".join(results)


def save_autofig(filename: str, figure: pyplot.Figure | None = None) -> None:
    """Save a figure automatically generated during testing in the special `autofig`
    sub-package so that Sphinx can include it into the documentation later.

    When passing no figure, function |save_autofig| takes the currently active one.
    """
    filepath = f"{autofigs.__path__[0]}/{filename}"
    if figure:
        figure.savefig(filepath)
        figure.clear()
    else:
        pyplot.savefig(filepath)
        pyplot.close()


@contextlib.contextmanager
def warn_later() -> Iterator[None]:
    """Suppress warnings and print them upon exit.

    The context manager |warn_later| helps demonstrate functionalities in doctests that
    emit warnings:

    >>> import warnings
    >>> def get_number():
    ...     warnings.warn("This is a warning.")
    ...     return 1

    >>> get_number()
    Traceback (most recent call last):
    ...
    UserWarning: This is a warning.

    >>> from hydpy.core.testtools import warn_later
    >>> with warn_later():
    ...     get_number()
    1
    UserWarning: This is a warning.
    """
    with warnings.catch_warnings(record=True) as records:
        warnings.resetwarnings()
        yield
    for record in records:
        print(record.category.__name__, record.message, sep=": ")


def print_filestructure(dirpath: str) -> None:
    """Print the file structure of the given directory path in alphabetical order.

    >>> import os
    >>> dirpath = os.path.join(data.__path__[0], "HydPy-H-Lahn")
    >>> from hydpy import data
    >>> from hydpy.core.testtools import print_filestructure
    >>> print_filestructure(dirpath)  # doctest: +ELLIPSIS
    * ...hydpy/data/HydPy-H-Lahn
        - conditions
            - init_1996_01_01_00_00_00
                + land_dill_assl.py
                ...
                + stream_lahn_marb_lahn_leun.py
        - control
            - default
                + land.py
                ...
                + stream_lahn_marb_lahn_leun.py
        + multiple_runs.xml
        + multiple_runs_alpha.xml
        - network
            - default
                + headwaters.py
                + nonheadwaters.py
                + streams.py
        - series
            - default
                + dill_assl_obs_q.asc
                ...
                + obs_q.nc
        + single_run.xml
        + single_run.xmlt
    """

    def _print_filestructure(dirpath: str, indent: int, /) -> None:
        prefix = indent * " "
        for name in sorted(os.listdir(dirpath)):
            if name != "__pycache__":
                subpath = os.path.join(dirpath, name)
                if os.path.isdir(subpath):
                    print(f"{prefix}- {name}")
                    _print_filestructure(subpath, indent + 4)
                else:
                    print(f"{prefix}+ {name}")

    dirpath = os.path.abspath(dirpath)
    print(objecttools.repr_(f"* {dirpath}"))
    _print_filestructure(dirpath, 4)


def prepare_io_example_1() -> tuple[devicetools.Nodes, devicetools.Elements]:
    """Prepare an IO example configuration for testing purposes.

    Function |prepare_io_example_1| is thought for testing the functioning of *HydPy*
    and thus should be of interest for framework developers only.  It uses the main
    models |lland_dd|, |lland_knauf|, and |hland_96| and the submodel
    |evap_aet_morsim|.  Here, we apply |prepare_io_example_1| and shortly discuss
    different aspects of its generated data:

    >>> from hydpy.core.testtools import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()

    It defines a short initialisation period of five days:

    >>> from hydpy import pub
    >>> pub.timegrids
    Timegrids("2000-01-01 00:00:00",
              "2000-01-05 00:00:00",
              "1d")

    It prepares an empty directory for IO testing:

    >>> import os
    >>> from hydpy import repr_, TestIO
    >>> with TestIO():  # doctest: +ELLIPSIS
    ...     repr_(pub.sequencemanager.currentpath)
    ...     os.listdir("project/series/default")
    '...iotesting/project/series/default'
    []

    It returns four |Element| objects handling either application model |lland_dd|
    |lland_knauf|, or |hland_96|:

    >>> for element in elements:
    ...     print(element.name, element.model)
    element1 lland_dd
    element2 lland_dd
    element3 lland_knauf
    element4 hland_96

    The |lland_knauf| instance has a submodel of type |evap_aet_morsim|:

    >>> print(elements.element3.model.aetmodel.name)
    evap_aet_morsim

    Two |Node| objects handling variables `Q` and `T`:

    >>> for node in nodes:
    ...     print(node.name, node.variable)
    node1 Q
    node2 T

    It generates artificial time series data for the input sequence
    |lland_inputs.Nied|, the flux sequence |lland_fluxes.NKor|, and the state sequence
    |lland_states.BoWa| of each |lland| model instance, the equally named wind speed
    sequences of |lland_knauf| and |evap_aet_morsim|, the state sequence
    |hland_states.SP| of the |hland_96| model instance, and the |Sim| sequence of each
    node instance.  For precise test results, all generated values are unique:

    >>> nied1 = elements.element1.model.sequences.inputs.nied
    >>> nied1.series
    InfoArray([0., 1., 2., 3.])
    >>> nkor1 = elements.element1.model.sequences.fluxes.nkor
    >>> nkor1.series
    InfoArray([[12.],
               [13.],
               [14.],
               [15.]])
    >>> bowa3 = elements.element3.model.sequences.states.bowa
    >>> bowa3.series
    InfoArray([[48., 49., 50.],
               [51., 52., 53.],
               [54., 55., 56.],
               [57., 58., 59.]])
    >>> sim2 = nodes.node2.sequences.sim
    >>> sim2.series
    InfoArray([64., 65., 66., 67.])
    >>> sp4 = elements.element4.model.sequences.states.sp
    >>> sp4.series
    InfoArray([[[68., 69., 70.],
                [71., 72., 73.]],
    <BLANKLINE>
               [[74., 75., 76.],
                [77., 78., 79.]],
    <BLANKLINE>
               [[80., 81., 82.],
                [83., 84., 85.]],
    <BLANKLINE>
               [[86., 87., 88.],
                [89., 90., 91.]]])
    >>> v_l = elements.element3.model.sequences.inputs.windspeed
    >>> v_l.series
    InfoArray([68., 69., 70., 71.])
    >>> v_e = elements.element3.model.aetmodel.sequences.inputs.windspeed
    >>> v_e.series
    InfoArray([68., 69., 70., 71.])

    All sequences carry |numpy.ndarray| objects with (deep) copies of the time
    series data for testing:

    >>> import numpy
    >>> assert numpy.all(nied1.series == nied1.testarray)
    >>> assert numpy.all(nkor1.series == nkor1.testarray)
    >>> assert numpy.all(bowa3.series == bowa3.testarray)
    >>> assert numpy.all(sim2.series == sim2.testarray)
    >>> assert numpy.all(sp4.series == sp4.testarray)
    >>> assert numpy.all(v_l.series == v_l.testarray)
    >>> assert numpy.all(v_e.series == v_e.testarray)
    >>> bowa3.series[1, 2] = -999.0
    >>> assert not numpy.all(bowa3.series == bowa3.testarray)
    """
    from hydpy.models import hland  # pylint: disable=import-outside-toplevel
    from hydpy.models import lland  # pylint: disable=import-outside-toplevel

    TestIO.clear()
    devicetools.Node.clear_all()
    devicetools.Element.clear_all()

    hydpy.pub.projectname = "project"
    hydpy.pub.sequencemanager = filetools.SequenceManager()
    with TestIO():
        os.makedirs("project/series/default")

    hydpy.pub.timegrids = "2000-01-01", "2000-01-05", "1d"

    node1 = devicetools.Node("node1")
    node2 = devicetools.Node("node2", variable="T")
    nodes = devicetools.Nodes(node1, node2)
    element1 = devicetools.Element("element1", outlets=node1)
    element2 = devicetools.Element("element2", outlets=node1)
    element3 = devicetools.Element("element3", outlets=node1)
    element4 = devicetools.Element("element4", outlets=node1)
    elements_lland = devicetools.Elements(element1, element2, element3)
    elements = elements_lland + element4

    element1.model = importtools.prepare_model("lland_dd")
    element2.model = importtools.prepare_model("lland_dd")
    element3.model = importtools.prepare_model("lland_knauf")
    element4.model = importtools.prepare_model("hland_96")

    control3 = element3.model.parameters.control
    control3.nhru(1)
    control3.ft(1.0)
    control3.fhru(1.0)
    control3.gh(100.0)
    control3.lnk(lland.ACKER)
    control3.measuringheightwindspeed(10.0)
    control3.lai(3.0)
    control3.wmax(300.0)
    with element3.model.add_aetmodel_v1("evap_aet_morsim"):
        pass

    for idx, element in enumerate(elements_lland):
        parameters = element.model.parameters
        parameters.control.nhru(idx + 1)
        parameters.control.lnk(lland.ACKER)
        parameters.derived.absfhru(10.0)
    control4 = element4.model.parameters.control
    control4.nmbzones(3)
    control4.sclass(2)
    control4.zonetype(hland.FIELD)
    control4.zonearea.values = 10.0

    with hydpy.pub.options.printprogress(False):
        nodes.prepare_simseries(allocate_ram=False)  # ToDo: add option "reset"
        nodes.prepare_simseries(allocate_ram=True)
        elements.prepare_inputseries(allocate_ram=False)
        elements.prepare_inputseries(allocate_ram=True)
        elements.prepare_factorseries(allocate_ram=False)
        elements.prepare_factorseries(allocate_ram=True)
        elements.prepare_fluxseries(allocate_ram=False)
        elements.prepare_fluxseries(allocate_ram=True)
        elements.prepare_stateseries(allocate_ram=False)
        elements.prepare_stateseries(allocate_ram=True)

    def init_values(seq: TestIOSequence, value1_: float) -> float:
        value2_ = value1_ + len(seq.series.flatten())
        values_ = numpy.arange(value1_, value2_, dtype=config.NP_FLOAT)
        seq.testarray = values_.reshape(seq.seriesshape)
        seq.series = seq.testarray.copy()
        return value2_

    value1 = 0.0
    for subname, seqname in zip(
        ["inputs", "fluxes", "states"], ["nied", "nkor", "bowa"]
    ):
        for element in elements_lland:
            subseqs = getattr(element.model.sequences, subname)
            value1 = init_values(getattr(subseqs, seqname), value1)
    for node in nodes:
        value1 = init_values(node.sequences.sim, value1)  # type: ignore[arg-type]
    init_values(element4.model.sequences.states.sp, value1)  # type: ignore[arg-type]
    init_values(
        element3.model.sequences.inputs.windspeed, value1  # type: ignore[arg-type]
    )
    init_values(element3.model.aetmodel.sequences.inputs.windspeed, value1)

    return nodes, elements


def prepare_full_example_1(dirpath: str | None = None) -> None:
    """Prepare the `HydPy-H-Lahn` example project on disk.

    By default, function |prepare_full_example_1| copies the original project data into
    the `iotesting` directory, thought for performing automated tests on real-world
    data.  The following doctest shows the generated folder structure:

    >>> from hydpy.core.testtools import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import TestIO
    >>> import os
    >>> with TestIO():
    ...     print("root:", *sorted(os.listdir(".")))
    ...     for folder in ("control", "conditions", "series"):
    ...         print(f"HydPy-H-Lahn/{folder}:",
    ...               *sorted(os.listdir(f"HydPy-H-Lahn/{folder}")))
    root: HydPy-H-Lahn __init__.py
    HydPy-H-Lahn/control: default
    HydPy-H-Lahn/conditions: init_1996_01_01_00_00_00
    HydPy-H-Lahn/series: default

    Pass an alternative path if you prefer to work in another directory:

    .. testsetup::

        >>> "HydPy-H-Lahn" in os.listdir(".")
        False

    >>> prepare_full_example_1(dirpath=".")

    .. testsetup::

        >>> "HydPy-H-Lahn" in os.listdir(".")
        True
        >>> import shutil
        >>> shutil.rmtree("HydPy-H-Lahn")
    """
    devicetools.Node.clear_all()
    devicetools.Element.clear_all()
    if dirpath is None:
        TestIO.clear()
        dirpath = iotesting.__path__[0]
    datapath: str = data.__path__[0]
    shutil.copytree(
        os.path.join(datapath, "HydPy-H-Lahn"), os.path.join(dirpath, "HydPy-H-Lahn")
    )


def prepare_full_example_2(
    lastdate: timetools.DateConstrArg = "1996-01-05",
) -> tuple[hydpytools.HydPy, pubtools.Pub, type[TestIO]]:
    """Prepare the `HydPy-H-Lahn` project on disk and in RAM.

    Function |prepare_full_example_2| is an extensions of function
    |prepare_full_example_1|.  Besides preparing the project data of the `HydPy-H-Lahn`
    example project, it performs all necessary steps to start a simulation run.
    Therefore, it returns a readily prepared |HydPy| instance, as well as, for
    convenience, module |pub| and class |TestIO|:

    >>> from hydpy.core.testtools import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()
    >>> hp.nodes
    Nodes("dill_assl", "lahn_kalk", "lahn_leun", "lahn_marb")
    >>> hp.elements
    Elements("land_dill_assl", "land_lahn_kalk", "land_lahn_leun",
             "land_lahn_marb", "stream_dill_assl_lahn_leun",
             "stream_lahn_leun_lahn_kalk", "stream_lahn_marb_lahn_leun")
    >>> pub.timegrids
    Timegrids("1996-01-01 00:00:00",
              "1996-01-05 00:00:00",
              "1d")
    >>> from hydpy import classname
    >>> classname(TestIO)
    'TestIO'

    Function |prepare_full_example_2| is primarily thought for testing and thus does
    not allow for many configurations except changing the end date of the
    initialisation period:

    >>> hp, pub, TestIO = prepare_full_example_2(lastdate="1996-01-02")
    >>> pub.timegrids
    Timegrids("1996-01-01 00:00:00",
              "1996-01-02 00:00:00",
              "1d")
    """
    prepare_full_example_1()
    with TestIO():
        hp = hydpytools.HydPy("HydPy-H-Lahn")
        hydpy.pub.timegrids = "1996-01-01", lastdate, "1d"
        hp.prepare_everything()
    return hp, hydpy.pub, TestIO


def prepare_interpolation_example() -> tuple[hydpytools.HydPy, pubtools.Pub]:
    """Prepare an example project that combines a |conv_nn| model and the
    input/output node mechanism to interpolate precipitation.

    >>> from hydpy.core.testtools import prepare_interpolation_example
    >>> hp, pub = prepare_interpolation_example()
    >>> hp.print_networkproperties()
    Number of nodes: 7
    Number of elements: 4
    Number of end nodes: 1
    Number of distinct networks: 1
    Applied node variables: P (4) and Q (3)
    Applied model types: conv_nn (1), dummy_node2node (1), and gland_gr4 (2)

    The example project consists of two nodes that receive the original precipitation
    series (`in1` and `in2`), an interpolation element (`conv`) that handles the
    |conv_nn| model instance, and two nodes (`out1` and `out2`) that pass the
    interpolated precipitation to two elements (`gr4_1` and `gr4_2`) that handle
    |gland_gr4| model instances.

    >>> hp.elements.conv
    Element("conv",
            inlets=["in1", "in2"],
            outlets=["out1", "out2"])

    The |gland_gr4| models pass their outflows to the nodes `q1` and `q2`, which are
    then combined by an application model of type |dummy_node2node| handled by element
    `dummy`:

    >>> hp.elements.gr4_1
    Element("gr4_1",
            outlets="q1",
            inputs="out1")
    >>> hp.elements.gr4_2
    Element("gr4_2",
            outlets="q2",
            inputs="out2")
    >>> hp.elements.dummy
    Element("dummy",
            inlets=["q1", "q2"],
            outlets="q12")

    `in1` and `in2` work with different deploy modes:

    >>> hp.nodes.in1.deploymode
    'obs'
    >>> hp.nodes.in2.deploymode
    'oldsim'

    The simulation spans only three days:

    >>> pub.timegrids
    Timegrids("2000-01-01 00:00:00",
              "2000-01-04 00:00:00",
              "1d")

    The simulation results:

    >>> hp.simulate()
    >>> from hydpy import print_vector
    >>> print_vector(hp.nodes.in1.sequences.obs.series)
    10.0, 20.0, 30.0
    >>> print_vector(hp.nodes.in2.sequences.sim.series)
    40.0, 50.0, 60.0
    >>> print_vector(hp.nodes.out1.sequences.sim.series)
    10.0, 20.0, 30.0
    >>> print_vector(hp.nodes.out2.sequences.sim.series)
    40.0, 50.0, 60.0
    >>> print_vector(hp.nodes.q1.sequences.sim.series)
    0.287977, 0.267212, 0.336692
    >>> print_vector(hp.nodes.q2.sequences.sim.series)
    0.565738, 0.597421, 0.700953
    >>> print_vector(hp.nodes.q12.sequences.sim.series)
    0.853716, 0.864633, 1.037645
    """

    devicetools.Node.clear_all()
    devicetools.Element.clear_all()

    with hydpy.pub.options.checkprojectstructure(False):
        hp = hydpytools.HydPy("InterpolationExample")
    hydpy.pub.timegrids = "2000-01-01", "2000-01-04", "1d"

    n_in1, n_in2 = devicetools.Nodes("in1", "in2", defaultvariable="P")
    n_out1, n_out2 = devicetools.Nodes("out1", "out2", defaultvariable="P")
    n_q1, n_q12, n_q2 = devicetools.Nodes("q1", "q12", "q2")
    element_conv = devicetools.Element(
        "conv", inlets=(n_in1, n_in2), outlets=(n_out1, n_out2)
    )
    e_gr4_1 = devicetools.Element("gr4_1", inputs=n_out1, outlets=n_q1)
    e_gr4_2 = devicetools.Element("gr4_2", inputs=n_out2, outlets=n_q2)
    e_dummy = devicetools.Element("dummy", inlets=(n_q1, n_q2), outlets=n_q12)

    convmodel = importtools.prepare_model("conv_nn")
    control = convmodel.parameters.control
    control.inputcoordinates(in1=(1.0, 3.0), in2=(5.0, 7.0))
    control.outputcoordinates(out1=(2.0, 2.0), out2=(6.0, 6.0))
    control.maxnmbinputs(1)

    gr4models = []
    for _ in range(2):
        gr4model = importtools.prepare_model("gland_gr4")
        control = gr4model.parameters.control
        with hydpy.pub.options.parameterstep("1d"):
            control.area(1.0)
            control.imax(0.0)
            control.x1(100.0)
            control.x2(1.0)
            control.x3(100.0)
        states = gr4model.sequences.states
        states.i(control.imax)
        states.s(control.x1)
        states.r(control.x3)
        with gr4model.add_petmodel_v1("evap_ret_io") as evapmodel:
            evapmodel.parameters.control.evapotranspirationfactor(1.0)
        gr4models.append(gr4model)

    dummymodel = importtools.prepare_model("dummy_node2node")

    element_conv.model = convmodel
    e_gr4_1.model = gr4models[0]
    e_gr4_2.model = gr4models[1]
    e_dummy.model = dummymodel

    hp.update_devices(
        nodes=(n_in1, n_in2, n_out1, n_out2, n_q1, n_q2, n_q12),
        elements=(element_conv, e_gr4_1, e_gr4_2, e_dummy),
    )
    hp.update_parameters()

    hp.prepare_allseries()
    n_in1.deploymode = "obs"
    n_in1.sequences.obs.series = 10.0, 20.0, 30.0
    n_in2.deploymode = "oldsim"
    n_in2.sequences.sim.series = 40.0, 50.0, 60.0
    e_gr4_1.model.petmodel.sequences.inputs.referenceevapotranspiration.series = 0.0
    e_gr4_2.model.petmodel.sequences.inputs.referenceevapotranspiration.series = 0.0

    return hp, hydpy.pub


def prepare_receiver_example() -> tuple[hydpytools.HydPy, pubtools.Pub]:
    """Prepare an example project that combines a |dam_v001| model and the receiver
    node mechanism to simulate the interaction between the controlled water release of
    a dam and the discharge at a remote downstream gauge.

    >>> from hydpy.core.testtools import prepare_receiver_example
    >>> hp, pub = prepare_receiver_example()
    >>> hp.print_networkproperties()
    Number of nodes: 5
    Number of elements: 7
    Number of end nodes: 1
    Number of distinct networks: 1
    Applied node variables: Q (5)
    Applied model types: dam_v001 (1), dummy_node2node (3), and gland_gr4 (3)

    The runoff generation is left to three |gland_gr4| model instances, handled by the
    elements `l1`, `l2`, and `l3`:

    >>> hp.elements.l1
    Element("l1",
            outlets="n1a")
    >>> hp.elements.l2
    Element("l2",
            outlets="n2")
    >>> hp.elements.l3
    Element("l3",
            outlets="n3")

    The runoff generated by `l1` flows into a dam, represented by a |dam_v001| model
    instance handled by element `d`:

    >>> hp.elements.d
    Element("d",
            inlets="n1a",
            outlets="n1b",
            receivers="n2")

    The uncontrolled outflow of `l2` and `l2` and the controlled water release of `d`
    reach a channel consisting of three segments, represented by individual
    |dummy_node2node| model instances handled by elements `s12`, `s23`, and `s34`:

    >>> hp.elements.s12
    Element("s12",
            inlets="n1b",
            outlets="n2")
    >>> hp.elements.s23
    Element("s23",
            inlets="n2",
            outlets="n3")
    >>> hp.elements.s34
    Element("s34",
            inlets="n3",
            outlets="n4")

    Node `n2` is responsible for routing water further downstream and informing the dam
    about the current discharge via the receiver mechanism, so that it can adjust its
    release to prevent severe low-flow situations.

    The simulation results:

    >>> hp.simulate()
    >>> from hydpy import print_vector
    >>> print_vector(hp.nodes.n1a.sequences.sim.series)
    2.324939, 2.0521, 1.834626, 1.657529, 1.510731, 1.387219
    >>> print_vector(hp.nodes.n1b.sequences.sim.series)
    0.0, 0.0, 0.0, 0.165374, 0.342471, 0.489269
    >>> print_vector(hp.nodes.n2.sequences.sim.series)
    2.324939, 2.0521, 1.834626, 1.822902, 1.853202, 1.876488
    >>> print_vector(hp.nodes.n3.sequences.sim.series)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707
    >>> print_vector(hp.nodes.n4.sequences.sim.series)
    4.649878, 4.1042, 3.669253, 3.480431, 3.363932, 3.263707
    """

    devicetools.Node.clear_all()
    devicetools.Element.clear_all()

    with hydpy.pub.options.checkprojectstructure(False):
        hp = hydpytools.HydPy("ReceiverExample")
    hydpy.pub.timegrids = "2000-01-01", "2000-01-07", "1d"

    n1a, n1b, n2, n3, n4 = devicetools.Nodes("n1a", "n1b", "n2", "n3", "n4")
    l1_ = devicetools.Element("l1", outlets="n1a")
    l2 = devicetools.Element("l2", outlets="n2")
    l3 = devicetools.Element("l3", outlets="n3")
    d = devicetools.Element("d", inlets="n1a", outlets="n1b", receivers="n2")
    s12 = devicetools.Element("s12", inlets="n1b", outlets="n2")
    s23 = devicetools.Element("s23", inlets="n2", outlets="n3")
    s34 = devicetools.Element("s34", inlets="n3", outlets="n4")

    lmodels = []
    for _ in range(3):
        lmodel = importtools.prepare_model("gland_gr4")
        control = lmodel.parameters.control
        with hydpy.pub.options.parameterstep("1d"):
            control.area(100.0)
            control.imax(0.0)
            control.x1(100.0)
            control.x2(1.0)
            control.x3(100.0)
        states = lmodel.sequences.states
        states.i(control.imax)
        states.s(0.6 * control.x1)
        states.r(0.6 * control.x3)
        with lmodel.add_petmodel_v1("evap_ret_io") as evapmodel:
            evapmodel.parameters.control.evapotranspirationfactor(1.0)
        lmodels.append(lmodel)

    dmodel = importtools.prepare_model("dam_v001")
    with hydpy.pub.options.parameterstep("1d"):
        control = dmodel.parameters.control
        from_data = ppolytools.PPoly.from_data
        control.watervolume2waterlevel(from_data(xs=[0.0, 1.0], ys=[0.0, 0.25]))
        control.waterlevel2flooddischarge(from_data(xs=[0.0], ys=[0.0]))
        control.catchmentarea(100.0)
        control.surfacearea(1.0)
        control.correctionprecipitation(1.0)
        control.correctionevaporation(1.0)
        control.weightevaporation(1.0)
        control.thresholdevaporation(0.0)
        control.toleranceevaporation(0.001)
        control.nmblogentries(1)
        control.remotedischargeminimum(2.0)
        control.remotedischargesafety(0.0)
        control.neardischargeminimumthreshold(0.0)
        control.neardischargeminimumtolerance(0.0)
        control.waterlevelminimumthreshold(0.0)
        control.waterlevelminimumtolerance(0.0)
        control.restricttargetedrelease(True)
        states = dmodel.sequences.states
        states.watervolume(1.0)
        logs = dmodel.sequences.logs
        logs.loggedadjustedevaporation(0.0)
        logs.loggedtotalremotedischarge(2.0)
        logs.loggedoutflow(0.0)

    l1_.model = lmodels[0]
    l2.model = lmodels[1]
    l3.model = lmodels[2]
    d.model = dmodel
    s12.model = importtools.prepare_model("dummy_node2node")
    s23.model = importtools.prepare_model("dummy_node2node")
    s34.model = importtools.prepare_model("dummy_node2node")

    hp.update_devices(
        nodes=(n1a, n1b, n2, n3, n4), elements=(l1_, l2, l3, d, s12, s23, s34)
    )
    hp.update_parameters()

    hp.prepare_allseries()
    for lmodel in lmodels:
        lmodel.sequences.inputs.p.series = 0.0
        lmodel.petmodel.sequences.inputs.referenceevapotranspiration.series = 0.0

    return hp, hydpy.pub


def prepare_collective_example() -> tuple[hydpytools.HydPy, pubtools.Pub]:
    """Prepare a complex example project that consists of multiple |sw1d_channel|
    models that are combined into a |sw1d_network| model during simulation via the
    :ref:`collective` approach and involves feedback effects over short and long
    distances via the receiver mechanism.

    >>> from hydpy.core.testtools import prepare_collective_example
    >>> hp, pub = prepare_collective_example()
    >>> hp.print_networkproperties()
    Number of nodes: 16
    Number of elements: 11
    Number of end nodes: 6
    Number of distinct networks: 0
    Applied node variables: Q (3), latq (3), longq (5), owl (3), and rwl (2)
    Applied model types: dam_sluice (3), gland_gr4 (5), and sw1d_channel (3)

    The "SW1D" collective consists of three channel segments.  The elements `c1` and
    `c2` rely on "normal" routing models of type |sw1d_lias|.  Both are directly
    connected to the outlet reach `c3`, which relies on a |sw1d_gate_out| model
    instance to use the water levels provided by node `out_c3_s1` as a lower boundary
    condition for solving the shallow water equations:

    >>> hp.elements.c1
    Element("c1",
            collective="SW1D",
            inlets=["g12_c1", "s1_c1"],
            outlets="c1_c3",
            senders="c1_s1")
    >>> hp.elements.c2
    Element("c2",
            collective="SW1D",
            inlets=["g22_c2", "s2_c2"],
            outlets="c2_c3",
            senders="c2_s2")
    >>> hp.elements.c3
    Element("c3",
            collective="SW1D",
            inlets=["c1_c3", "c2_c3", "s3_c3"],
            outlets="c3_out",
            receivers="out_c3_s1",
            senders="c3_s3")

    `c1` and `c2` receive uncontrolled "longitudinal" inflow generated by |gland_gr4|
    models handled by the elements `g12` and `g22`:

    >>> hp.elements.g12
    Element("g12",
            outlets="g12_c1")
    >>> hp.elements.g22
    Element("g22",
            outlets="g22_c2")

    Besides this, all channel segments receive the water released by "laterally"
    connected |dam_sluice| model instances handled by the elements `p1`, `p2`, and
    `p3`.  Each sluice model requires the water level of its connected channel model to
    determine the current water level gradient and so its current water release, which
    is made available via the nodes `c1_s1`, `c2_s2`, and `c3_s3`, respectively.
    Additionally, the sluice model of element `s1` receives the lower boundary
    water level provided by node `out_c3_s1`, which allows to stop the release of water
    as soon as a critical outer water level is exceeded:

    >>> hp.elements.s1
    Element("s1",
            inlets="g11_s1",
            outlets="s1_c1",
            receivers=["c1_s1", "out_c3_s1"])
    >>> hp.elements.s2
    Element("s2",
            inlets="g21_s2",
            outlets="s2_c2",
            receivers=["c2_s2", "no_s1"])
    >>> hp.elements.s3
    Element("s3",
            inlets="g31_s3",
            outlets="s3_c3",
            receivers=["c3_s3", "no_s1"])

    The inflow of `s1`, `s2`, and `s3` stems also from the |gland_gr4| models, which
    are handled by the elements `g11`, `g21`, and `g31`:

    >>> hp.elements.g11
    Element("g11",
            outlets="g11_s1")
    >>> hp.elements.g21
    Element("g21",
            outlets="g21_s2")
    >>> hp.elements.g31
    Element("g31",
            outlets="g31_s3")

    The simulation results:

    >>> hp.simulate()
    >>> from hydpy import print_vector
    >>> print_vector(hp.nodes.g11_s1.sequences.sim.series)
    0.232494, 0.20521, 0.183463, 0.165753, 0.151073, 0.138722
    >>> print_vector(hp.nodes.g21_s2.sequences.sim.series)
    0.232494, 0.20521, 0.183463, 0.165753, 0.151073, 0.138722
    >>> print_vector(hp.nodes.g31_s3.sequences.sim.series)
    0.232494, 0.20521, 0.183463, 0.165753, 0.151073, 0.138722
    >>> print_vector(hp.nodes.g12_c1.sequences.sim.series)
    0.232494, 0.20521, 0.183463, 0.165753, 0.151073, 0.138722
    >>> print_vector(hp.nodes.g22_c2.sequences.sim.series)
    0.232494, 0.20521, 0.183463, 0.165753, 0.151073, 0.138722

    >>> print_vector(hp.nodes.s1_c1.sequences.sim.series)
    0.20014, 0.081896, 0.075122, 0.068673, 0.0, 0.0
    >>> print_vector(hp.nodes.s2_c2.sequences.sim.series)
    0.20014, 0.081896, 0.075122, 0.068673, 0.062057, 0.05637
    >>> print_vector(hp.nodes.s3_c3.sequences.sim.series)
    0.20014, 0.08195, 0.07516, 0.0687, 0.062074, 0.056383

    >>> print_vector(hp.nodes.c1_c3.sequences.sim.series)
    0.213689, 0.197114, 0.173684, 0.148542, 0.07705, 0.03247
    >>> print_vector(hp.nodes.c2_c3.sequences.sim.series)
    0.213689, 0.197114, 0.173684, 0.148542, 0.138743, 0.088823
    >>> print_vector(hp.nodes.c3_out.sequences.sim.series)
    0.409196, 0.386017, 0.337494, 0.279784, 0.203433, 0.071322

    >>> print_vector(hp.nodes.c1_s1.sequences.sim.series)
    2.189168, 2.266922, 2.340276, 2.41448, 2.478436, 2.570237
    >>> print_vector(hp.nodes.c2_s2.sequences.sim.series)
    2.189168, 2.266922, 2.340276, 2.41448, 2.47875, 2.570566
    >>> print_vector(hp.nodes.c3_s3.sequences.sim.series)
    2.188631, 2.266529, 2.339998, 2.414303, 2.478613, 2.570503

    >>> print_vector(hp.nodes.no_s1.sequences.sim.series)
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    >>> print_vector(hp.nodes.out_c3_s1.sequences.sim.series)
    1.5, 1.7, 1.9, 2.1, 2.3, 2.5
    """

    # pylint: disable=too-many-statements

    from hydpy import aliases  # pylint: disable=import-outside-toplevel

    devicetools.Node.clear_all()
    devicetools.Element.clear_all()

    with hydpy.pub.options.checkprojectstructure(False):
        hp = hydpytools.HydPy("CollectiveExample")
    hydpy.pub.timegrids = "2000-01-01", "2000-01-07", "1d"

    longq = devicetools.FusedVariable(
        "longq",
        aliases.gland_outlets_Q,
        aliases.sw1d_inlets_LongQ,
        aliases.sw1d_outlets_LongQ,
    )
    latq = devicetools.FusedVariable(
        "latq", aliases.dam_outlets_Q, aliases.sw1d_inlets_LatQ
    )
    owl = devicetools.FusedVariable(
        "owl", aliases.sw1d_senders_WaterLevel, aliases.dam_receivers_OWL
    )
    rwl = devicetools.FusedVariable(
        "rwl", aliases.sw1d_inlets_WaterLevel, aliases.dam_receivers_RWL
    )

    g11_s1, g21_s2, g31_s3 = devicetools.Nodes("g11_s1", "g21_s2", "g31_s3")
    g12_c1, g22_c2 = devicetools.Nodes("g12_c1", "g22_c2", defaultvariable=longq)
    s1_c1, s2_c2, s3_c3 = devicetools.Nodes(
        "s1_c1", "s2_c2", "s3_c3", defaultvariable=latq
    )
    c1_c3, c2_c3, c3_out = devicetools.Nodes(
        "c1_c3", "c2_c3", "c3_out", defaultvariable=longq
    )
    c1_s1, c2_s2, c3_s3 = devicetools.Nodes(
        "c1_s1", "c2_s2", "c3_s3", defaultvariable=owl
    )
    no_s1, out_c3_s1 = devicetools.Nodes("no_s1", "out_c3_s1", defaultvariable=rwl)

    g11 = devicetools.Element("g11", outlets=g11_s1)
    g12 = devicetools.Element("g12", outlets=g12_c1)
    g21 = devicetools.Element("g21", outlets=g21_s2)
    g22 = devicetools.Element("g22", outlets=g22_c2)
    g31 = devicetools.Element("g31", outlets=g31_s3)
    s1 = devicetools.Element(
        "s1", inlets=g11_s1, outlets=s1_c1, receivers=(c1_s1, out_c3_s1)
    )
    s2 = devicetools.Element(
        "s2", inlets=g21_s2, outlets=s2_c2, receivers=(c2_s2, no_s1)
    )
    s3 = devicetools.Element(
        "s3", inlets=g31_s3, outlets=s3_c3, receivers=(c3_s3, no_s1)
    )
    c1 = devicetools.Element(
        "c1", inlets=(g12_c1, s1_c1), outlets=c1_c3, senders=c1_s1, collective="SW1D"
    )
    c2 = devicetools.Element(
        "c2", inlets=(g22_c2, s2_c2), outlets=c2_c3, senders=c2_s2, collective="SW1D"
    )
    c3 = devicetools.Element(
        "c3",
        inlets=(s3_c3, c1_c3, c2_c3),
        outlets=c3_out,
        receivers=out_c3_s1,
        senders=c3_s3,
        collective="SW1D",
    )

    gr_models = []
    for _ in range(5):
        gr_model = importtools.prepare_model("gland_gr4")
        control = gr_model.parameters.control
        with hydpy.pub.options.parameterstep("1d"):
            control.area(10.0)
            control.imax(0.0)
            control.x1(100.0)
            control.x2(1.0)
            control.x3(100.0)
        states = gr_model.sequences.states
        states.i(control.imax)
        states.s(0.6 * control.x1)
        states.r(0.6 * control.x3)
        with gr_model.add_petmodel_v1("evap_ret_io") as evap_model:
            evap_model.parameters.control.evapotranspirationfactor(1.0)
        gr_models.append(gr_model)

    sluice_models = []
    for _ in range(3):
        sluice_model = importtools.prepare_model("dam_sluice")
        control = sluice_model.parameters.control
        with hydpy.pub.options.parameterstep("1d"):
            control.surfacearea(1.44)
            control.catchmentarea(86.4)
            control.watervolume2waterlevel(
                ppolytools.PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 1.0])
            )
            control.remotewaterlevelmaximumthreshold(2.0)
            control.remotewaterlevelmaximumtolerance(0.0)
            control.correctionprecipitation(1.0)
            control.correctionevaporation(1.0)
            control.weightevaporation(0.8)
            control.thresholdevaporation(0.0)
            control.toleranceevaporation(0.001)
            control.crestlevel(1.0)
            control.waterleveldifference2maxfreedischarge(
                ppolytools.PPoly.from_data(xs=[0.0, 1.0], ys=[0.0, 0.1])
            )
            control.crestleveltolerance(0.1)
            control.dischargetolerance(0.0)
        sluice_model.sequences.states.watervolume(3.0)
        logs = sluice_model.sequences.logs
        logs.loggedadjustedevaporation(0.0)
        logs.loggedouterwaterlevel(0.0)
        logs.loggedremotewaterlevel(0.0)
        sluice_models.append(sluice_model)

    channel_models = []
    for _ in range(3):
        channel_model = importtools.prepare_model("sw1d_channel")
        channel_model.parameters.control.nmbsegments(1)
        with channel_model.add_storagemodel_v1(
            "sw1d_storage", position=0
        ) as storage_model:
            storage_model.parameters.control.length(10.0)
            storage_model.sequences.states.watervolume(200.0)
        channel_models.append(channel_model)
    for i in range(2):
        channel_model = channel_models[i]
        with channel_model.add_routingmodel_v1("sw1d_q_in", position=0) as q_model:
            control = q_model.parameters.control
            control.lengthdownstream(10.0)
            control.timestepfactor(0.7)
        with channel_model.add_routingmodel_v2("sw1d_lias", position=1) as lias_model:
            control = lias_model.parameters.control
            control.lengthupstream(10.0)
            control.lengthdownstream(10.0)
            control.stricklercoefficient(1.0 / 0.03)
            control.timestepfactor(0.7)
            control.diffusionfactor(0.2)
            lias_model.sequences.states.discharge(0.0)
    channel_model = channel_models[2]
    with channel_model.add_routingmodel_v3("sw1d_gate_out", position=1) as gate_model:
        control = gate_model.parameters.control
        control.lengthupstream(10.0)
        control.bottomlevel(0.0)
        control.gateheight(0.1)
        control.gatewidth(2.0)
        control.flowcoefficient(0.6)
        control.timestepfactor(0.7)
        control.dampingradius(0.0)
    for channel_model in channel_models:
        for submodel in (
            channel_model.storagemodels[0],
            channel_model.routingmodels[0],
            channel_model.routingmodels[1],
        ):
            if hasattr(submodel, "add_crosssection_v2"):
                with submodel.add_crosssection_v2("wq_trapeze") as trapeze_model:
                    control = trapeze_model.parameters.control
                    control.nmbtrapezes(1)
                    control.bottomlevels(0.0)
                    control.bottomwidths(10.0)
                    control.sideslopes(0.0)

    # pylint: disable=unbalanced-tuple-unpacking
    g11.model, g12.model, g21.model, g22.model, g31.model = gr_models
    s1.model, s2.model, s3.model = sluice_models
    c1.model, c2.model, c3.model = channel_models

    hp.update_devices(
        # fmt: off
        nodes=(
            g11_s1, g21_s2, g12_c1, g22_c2, g31_s3, s1_c1, s2_c2, s3_c3,
            c1_c3, c2_c3, c3_out, c1_s1, c2_s2, c3_s3, no_s1, out_c3_s1,
        ),
        # fmt: on
        elements=(g11, g12, g21, g22, g31, s1, s2, s3, c1, c2, c3)
    )
    hp.update_parameters()

    hp.prepare_allseries()
    for gr_model in gr_models:
        gr_model.sequences.inputs.p.series = 0.0
        gr_model.petmodel.sequences.inputs.referenceevapotranspiration.series = 0.0
    out_c3_s1.deploymode = "oldsim"
    out_c3_s1.sequences.sim.series = numpy.linspace(1.5, 2.5, 6)

    return hp, hydpy.pub
