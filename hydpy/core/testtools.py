# -*- coding: utf-8 -*-
"""This module implements tools for testing *HydPy* and its models."""
# import...
# ...from standard library
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
from typing import *
from typing_extensions import Literal  # type: ignore[misc]

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import docs
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import hydpytools
from hydpy.core import importtools
from hydpy.core import objecttools
from hydpy.core import printtools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core import typingtools
from hydpy.core import variabletools
from hydpy.tests import iotesting

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    import matplotlib
    from matplotlib import pyplot
    import pandas
    import plotly
    from plotly import subplots
    from hydpy.core import modeltools
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
    texts: List[str]

    def __init__(self, indent: int = 0):
        self.indent = indent
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.encoding = sys.stdout.encoding
        self.texts = []

    def __enter__(self):
        self.encoding = sys.stdout.encoding
        sys.stdout = self
        sys.stderr = self

    def __exit__(self, exception, message, traceback_):
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

    >>> from hydpy.models import hland, hland_v1

    >>> hland.tester.package
    'hydpy.models.hland'
    >>> hland_v1.tester.package
    'hydpy.models'
    """

    filepath: str
    package: str
    ispackage: bool

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.filepath = frame.f_code.co_filename
        self.package = frame.f_locals["__package__"]
        self.ispackage = os.path.split(self.filepath)[-1] == "__init__.py"

    @property
    def filenames(self) -> List[str]:
        """The filenames which define the considered base or application model.

        >>> from hydpy.models import hland, hland_v1
        >>> from pprint import pprint
        >>> pprint(hland.tester.filenames)
        ['__init__.py',
         'hland_constants.py',
         'hland_control.py',
         'hland_derived.py',
         'hland_fluxes.py',
         'hland_inputs.py',
         'hland_logs.py',
         'hland_masks.py',
         'hland_model.py',
         'hland_outlets.py',
         'hland_parameters.py',
         'hland_sequences.py',
         'hland_states.py']
        >>> hland_v1.tester.filenames
        ['hland_v1.py']
        """
        if self.ispackage:
            return sorted(
                fn
                for fn in os.listdir(os.path.dirname(self.filepath))
                if fn.endswith(".py")
            )
        return [os.path.split(self.filepath)[1]]

    @property
    def modulenames(self) -> List[str]:
        """The module names to be taken into account for testing.

        >>> from hydpy.models import hland, hland_v1
        >>> from pprint import pprint
        >>> pprint(hland.tester.modulenames)
        ['hland_constants',
         'hland_control',
         'hland_derived',
         'hland_fluxes',
         'hland_inputs',
         'hland_logs',
         'hland_masks',
         'hland_model',
         'hland_outlets',
         'hland_parameters',
         'hland_sequences',
         'hland_states']
        >>> hland_v1.tester.modulenames
        ['hland_v1']
        """
        return [
            os.path.split(fn)[-1].split(".")[0]
            for fn in self.filenames
            if (fn.endswith(".py") and not fn.startswith("_"))
        ]

    def perform_tests(self):
        """Perform all doctests either in Python or in Cython mode depending
        on the state of |Options.usecython| set in module |pub|.

        Usually, |Tester.perform_tests| is triggered automatically by a
        |Cythonizer| object assigned to the same base or application
        model as a |Tester| object.  However, you are free to call
        it any time when in doubt of the functionality of a particular
        base or application model.  Doing so might change some of the
        states of your current configuration, but only temporarily
        (we pick the |Timegrids| object of module |pub| as an example,
        which is changed multiple times during testing but finally
        reset to the original value):

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"

        >>> from hydpy.models import hland, hland_v1
        >>> hland.tester.perform_tests()   # doctest: +ELLIPSIS
        Test package hydpy.models.hland in ...ython mode.
            * hland_constants:
                no failures occurred
            * hland_control:
                no failures occurred
            * hland_derived:
                no failures occurred
            * hland_fluxes:
                no failures occurred
            * hland_inputs:
                no failures occurred
            * hland_logs:
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

        >>> hland_v1.tester.perform_tests()   # doctest: +ELLIPSIS
        Test module hland_v1 in ...ython mode.
            * hland_v1:
                no failures occurred

        >>> pub.timegrids
        Timegrids(Timegrid("2000-01-01 00:00:00",
                           "2001-01-01 00:00:00",
                           "1d"))

        To show the reporting of possible errors, we change the
        string representation of parameter |hland_control.ZoneType|
        temporarily.  Again, the |Timegrids| object is reset to its
        initial state after testing:

        >>> from unittest import mock
        >>> with mock.patch(
        ...     "hydpy.models.hland.hland_control.ZoneType.__repr__",
        ...     return_value="damaged"):
        ...     hland.tester.perform_tests()   # doctest: +ELLIPSIS
        Test package hydpy.models.hland in ...ython mode.
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
                1
                items had failures:
                   1 of   6 in hydpy.models.hland.hland_control.ZoneType
                ***Test Failed***
                1
                failures.
            * hland_derived:
                no failures occurred
            ...
            * hland_states:
                no failures occurred

        >>> pub.timegrids
        Timegrids(Timegrid("2000-01-01 00:00:00",
                           "2001-01-01 00:00:00",
                           "1d"))
        """
        opt = hydpy.pub.options
        color = 34 if hydpy.pub.options.usecython else 36
        with printtools.PrintStyle(color=color, font=4):
            print(
                "Test %s %s in %sython mode."
                % (
                    "package" if self.ispackage else "module",
                    self.package if self.ispackage else self.modulenames[0],
                    "C" if hydpy.pub.options.usecython else "P",
                )
            )
        with printtools.PrintStyle(color=color, font=2):
            for name in self.modulenames:
                print(
                    "    * %s:" % name,
                )
                # pylint: disable=not-callable
                # pylint does understand that all options are callable
                # except option `printincolor`!?
                with StdOutErr(indent=8), opt.ellipsis(0), opt.printincolor(
                    False
                ), opt.printprogress(False), opt.reprcomments(False), opt.reprdigits(
                    6
                ), opt.usedefaultvalues(
                    False
                ), opt.utclongitude(
                    15
                ), opt.utcoffset(
                    60
                ), opt.warnsimulationstep(
                    False
                ), opt.warntrim(
                    False
                ), opt.parameterstep(
                    timetools.Period("1d")
                ), opt.simulationstep(
                    timetools.Period()
                ), devicetools.clear_registries_temporarily():
                    # pylint: enable=not-callable
                    projectname = exceptiontools.getattr_(
                        hydpy.pub,
                        "projectname",
                        None,
                    )
                    del hydpy.pub.projectname
                    timegrids = exceptiontools.getattr_(
                        hydpy.pub,
                        "timegrids",
                        None,
                    )
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
                        hydpy.pub.projectname = projectname
                        if timegrids is not None:
                            hydpy.pub.timegrids = timegrids
                        IntegrationTest.plotting_options = plotting_options
                        hydpy.dummies.clear()


class Array:
    """Assures that attributes are |numpy.ndarray| objects."""

    def __setattr__(self, name, value):
        object.__setattr__(self, name, numpy.array(value))


class ArrayDescriptor:
    """A descriptor for handling values of |Array| objects."""

    def __init__(self):
        self.values = Array()

    def __set__(self, obj, values):
        self.__delete__(obj)
        if values is not None:
            for (key, value) in values:
                setattr(self.values, key.name, value)

    def __get__(self, obj, type_=None):
        return self.values

    def __delete__(self, obj):
        for name in list(vars(self.values).keys()):
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
    """Stores arrays for setting the same values of parameters and/or
    sequences before each new experiment."""

    @property
    @abc.abstractmethod
    def raw_first_col_strings(self):
        """To be implemented by the subclasses of |Test|."""

    @staticmethod
    @abc.abstractmethod
    def get_output_array(parseqs):
        """To be implemented by the subclasses of |Test|."""

    @property
    def nmb_rows(self):
        """The number of rows of the table."""
        return len(self.raw_first_col_strings) + 1

    @property
    def nmb_cols(self):
        """The number of columns in the table."""
        nmb = 1
        for parseq in self.parseqs:
            nmb += max(len(parseq), 1)
        return nmb

    @property
    def raw_header_strings(self):
        """All raw strings for the tables header."""
        strings = [self.HEADER_OF_FIRST_COL]
        for parseq in self.parseqs:
            for dummy in range(len(parseq) - 1):
                strings.append("")
            if (parseq.name == "sim") and isinstance(parseq, sequencetools.Sequence_):
                strings.append(parseq.subseqs.node.name)
            else:
                strings.append(parseq.name)
        return strings

    @property
    def raw_body_strings(self):
        """All raw strings for the body of the table."""
        strings = []
        for (idx, first_string) in enumerate(self.raw_first_col_strings):
            strings.append([first_string])
            for parseq in self.parseqs:
                array = self.get_output_array(parseq)
                if parseq.NDIM == 0:
                    strings[-1].append(objecttools.repr_(array[idx]))
                else:
                    strings[-1].extend(objecttools.repr_(value) for value in array[idx])
        return strings

    @property
    def raw_strings(self):
        """All raw strings for the complete table."""
        return [self.raw_header_strings] + self.raw_body_strings

    @property
    def col_widths(self):
        """The widths of all columns of the table."""
        strings = self.raw_strings
        widths = []
        for jdx in range(self.nmb_cols):
            widths.append(0)
            for idx in range(self.nmb_rows):
                widths[-1] = max(len(strings[idx][jdx]), widths[-1])
        return widths

    @property
    def col_separators(self):
        """The separators for adjacent columns."""
        seps = ["| "]
        for parseq in self.parseqs:
            seps.append(" | ")
            for dummy in range(len(parseq) - 1):
                seps.append("  ")
        seps.append(" |")
        return seps

    @property
    def row_nmb_characters(self):
        """The number of characters of a single row of the table."""
        return sum(self.col_widths) + sum((len(sep) for sep in self.col_separators))

    @staticmethod
    def _interleave(separators, strings, widths):
        """Generate a table line from the given arguments."""
        lst = [
            value
            for (separator, string, width) in zip(separators, strings, widths)
            for value in (separator, string.rjust(width))
        ]
        lst.append(separators[-1])
        return "".join(lst)

    def make_table(self, idx1=None, idx2=None) -> str:
        """Return the result table between the given indices."""
        lines = []
        col_widths = self.col_widths
        col_separators = self.col_separators
        lines.append(
            self._interleave(
                self.col_separators,
                self.raw_header_strings,
                col_widths,
            )
        )
        lines.append("-" * self.row_nmb_characters)
        for strings_in_line in self.raw_body_strings[idx1:idx2]:
            lines.append(
                self._interleave(
                    col_separators,
                    strings_in_line,
                    col_widths,
                )
            )
        return "\n".join(lines)

    def print_table(self, idx1=None, idx2=None):
        """Print the result table between the given indices."""
        print(self.make_table(idx1=idx1, idx2=idx2))


class PlottingOptions:
    """Plotting options of class |IntegrationTest|."""

    def __init__(self):
        self.width = 600
        self.height = 300
        self.selected = None
        self.activated = None
        self.axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None
        self.axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None


class IntegrationTest(Test):
    """Defines model integration doctests.

    The functionality of |IntegrationTest| is easiest to understand by
    inspecting doctests like the ones of modules |llake_v1| or |arma_v1|.

    Note that all condition sequences (state and logging sequences) are
    initialised in accordance with the values are given as `inits` values.
    The values of the simulation sequences of outlet and sender nodes are
    always set to zero before each test run.  All other parameter and
    sequence values can be changed between different test runs.
    """

    HEADER_OF_FIRST_COL = "date"
    """The header of the first column containing dates."""

    plotting_options = PlottingOptions()

    def __init__(self, element, seqs=None, inits=None):
        """Prepare the element and its nodes and put them into a HydPy object
        and make their sequences ready for use for integration testing."""
        del self.inits
        self.element = element
        self.elements = devicetools.Element.query_all()
        self.nodes = devicetools.Node.query_all()
        self.prepare_node_sequences()
        self.prepare_input_model_sequences()
        self.parseqs = seqs if seqs else self.extract_print_sequences()
        self.inits = inits
        self.model = element.model
        hydpytools.HydPy.nmb_instances = 0
        self.hydpy = hydpytools.HydPy()
        self.hydpy.update_devices(
            nodes=self.nodes,
            elements=self.elements,
        )
        self._src = None

    @overload
    def __call__(
        self,
        filename: Optional[str] = None,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        update_parameters: bool = True,
        get_conditions: Literal[None] = None,
        use_conditions: Optional[timetools.DateConstrArg] = None,
    ) -> None:
        """do not return conditions"""

    @overload
    def __call__(
        self,
        filename: Optional[str] = None,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        update_parameters: bool = True,
        get_conditions: timetools.DateConstrArg = None,
        use_conditions: Optional[timetools.DateConstrArg] = None,
    ) -> Dict[sequencetools.IOSequence, Union[float, numpy.array]]:
        """do return conditions"""

    def __call__(
        self,
        filename=None,
        axis1=None,
        axis2=None,
        update_parameters=True,
        get_conditions=None,
        use_conditions=None,
    ):
        """Prepare and perform an integration test and print and eventually
        plot its results.

        Note that the conditions defined under |IntegrationTest.inits|
        override the ones given via keyword `use_conditions`.
        """
        self.prepare_model(
            update_parameters=update_parameters,
            use_conditions=use_conditions,
        )
        seq2value = self._perform_simulation(get_conditions)
        self.print_table()
        if filename:
            self.plot(
                filename=filename,
                axis1=axis1,
                axis2=axis2,
            )
        return seq2value

    def _perform_simulation(self, get_conditions):
        if get_conditions:
            date = timetools.Date(get_conditions)
            hydpy.pub.timegrids.sim = timetools.Timegrid(
                firstdate=hydpy.pub.timegrids.init.firstdate,
                lastdate=date,
                stepsize=hydpy.pub.timegrids.stepsize,
            )
            self.hydpy.simulate()
            seq2value = {}
            for seq in self.element.model.sequences.conditionsequences:
                seq2value[seq] = copy.deepcopy(seq.value)
            hydpy.pub.timegrids.sim = timetools.Timegrid(
                firstdate=date,
                lastdate=hydpy.pub.timegrids.init.lastdate,
                stepsize=hydpy.pub.timegrids.stepsize,
            )
            self.hydpy.simulate()
            hydpy.pub.timegrids.sim = timetools.Timegrid(
                firstdate=hydpy.pub.timegrids.init.firstdate,
                lastdate=hydpy.pub.timegrids.init.lastdate,
                stepsize=hydpy.pub.timegrids.stepsize,
            )
            return seq2value
        self.hydpy.simulate()
        return None

    @property
    def _datetimes(self):
        return tuple(date.datetime for date in hydpy.pub.timegrids.sim)

    @property
    def raw_first_col_strings(self):
        """The raw date strings of the first column, except the header."""
        return tuple(_.strftime(self.dateformat) for _ in self._datetimes)

    @property
    def dateformat(self) -> str:
        """Format string for printing dates in the first column of the table.

        See the documentation on module |datetime| for the format strings
        allowed.

        You can query and change property |IntegrationTest.dateformat|:

        >>> from hydpy import Element, IntegrationTest, prepare_model, pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> element = Element("element", outlets="node")
        >>> element.model = prepare_model("hland_v1")
        >>> __package__ = "testpackage"
        >>> tester = IntegrationTest(element)
        >>> tester.dateformat
        '%Y-%m-%d %H:%M:%S'

        Passing an ill-defined format string leads to the following error:

        >>> tester.dateformat = 999
        Traceback (most recent call last):
        ...
        ValueError: The given date format `999` is not a valid format \
string for `datetime` objects.  Please read the documentation on module \
datetime of the Python standard library for for further information.

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
                f"The given date format `{dateformat}` is not a valid "
                f"format string for `datetime` objects.  Please read "
                f"the documentation on module datetime of the Python "
                f"standard library for for further information."
            ) from exc
        vars(self)["dateformat"] = dateformat

    @staticmethod
    def get_output_array(parseqs):
        """Return the array containing the output results of the given
        sequence."""
        return parseqs.series

    def prepare_node_sequences(self):
        """Prepare the simulations sequences of all nodes in.

        This preparation might not be suitable for all types of integration
        tests.  Prepare those node sequences manually, for which this method
        does not result in the desired outcome."""
        for node in self.nodes:
            if not node.entries:
                node.deploymode = "oldsim"
            sim = node.sequences.sim
            sim.activate_ram()

    def prepare_input_model_sequences(self):
        """Configure the input sequences of the model in a manner that allows
        for applying their time-series data in integration tests."""
        subseqs = getattr(self.element.model.sequences, "inputs", ())
        for seq in subseqs:
            seq.activate_ram()

    def extract_print_sequences(self):
        """Return a list of all input, flux and state sequences of the model
        as well as the simulation sequences of all nodes."""
        seqs = []
        for name in ("inputs", "fluxes", "states"):
            subseqs = getattr(self.element.model.sequences, name, ())
            for seq in subseqs:
                seqs.append(seq)
        for node in self.nodes:
            seqs.append(node.sequences.sim)
        return seqs

    def prepare_model(
        self,
        update_parameters: bool,
        use_conditions: Optional[timetools.DateConstrArg],
    ) -> None:
        """Derive the secondary parameter values, prepare all required time
        series and set the initial conditions."""
        if update_parameters:
            self.model.parameters.update()
        self.element.prepare_fluxseries()
        self.element.prepare_stateseries()
        self.reset_outputs()
        if use_conditions:
            with hydpy.pub.options.trimvariables(False):
                for seq in self.element.model.sequences.conditionsequences:
                    seq(use_conditions[seq])
        self.reset_inits()

    def reset_outputs(self):
        """Set the values of the simulation sequences of all outlet nodes to
        zero."""
        for node in self.nodes:
            if (node in self.element.outlets) or (node in self.element.senders):
                node.sequences.sim[:] = 0.0

    def reset_inits(self):
        """Set all initial conditions of all models."""
        with hydpy.pub.options.trimvariables(False):
            for subname in ("states", "logs"):
                for element in self.elements:
                    for seq in getattr(element.model.sequences, subname, ()):
                        try:
                            seq(getattr(self.inits, seq.name))
                        except AttributeError:
                            pass

    def plot(
        self,
        filename: str,
        axis1: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
        axis2: typingtools.MayNonerable1[sequencetools.IOSequence] = None,
    ):
        """Save a plotly HTML file plotting the current test results.

        (Optional) arguments:
            * filename: Name of the file.  If necessary, the file ending
              `html` is added automatically.  The file is stored in the
              `html_` folder of subpackage `docs`.
            * act_sequences: List of the sequences to be shown initially
              (deprecated).
            * axis1: sequences to be shown initially on the first axis.
            * axis2: sequences to be shown initially on the second axis.
        """

        def _update_act_names(sequence_) -> None:
            if isinstance(sequence_, act_types1):
                act_names1.append(name)
            if isinstance(sequence_, act_types2):
                act_names2.append(name)

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
            axis1 = objecttools.extract(axis1, sequencetools.IOSequence)
            axis2 = objecttools.extract(axis2, sequencetools.IOSequence)
        sel_sequences = self.plotting_options.selected
        if sel_sequences is None:
            sel_sequences = self.parseqs
        sel_sequences = sorted(sel_sequences, key=lambda seq_: seq_.name)
        act_types1 = tuple(type(seq_) for seq_ in axis1)
        act_types2 = tuple(type(seq_) for seq_ in axis2)
        sel_names, sel_series, sel_units = [], [], []
        act_names1, act_names2 = [], []
        for sequence in sel_sequences:
            name = type(sequence).__name__
            if sequence.NDIM == 0:
                sel_names.append(name)
                sel_units.append(sequence.unit)
                sel_series.append(list(sequence.series))
                _update_act_names(sequence)
            elif sequence.shape[0] == 1:
                sel_names.append(name)
                sel_units.append(sequence.unit)
                sel_series.append(list(sequence.series[:, 0]))
                _update_act_names(sequence)
            else:
                for idx in range(sequence.shape[0]):
                    subname = f"{name}_{idx+1}"
                    sel_names.append(subname)
                    sel_units.append(sequence.unit)
                    sel_series.append(list(sequence.series[:, idx]))
                    _update_act_names(sequence)

        fig = subplots.make_subplots(
            rows=1,
            cols=1,
            specs=[[{"secondary_y": True}]],
        )
        fig.update_xaxes(
            showgrid=False,
            zeroline=False,
        )
        fig.update_yaxes(
            showgrid=False,
            zeroline=False,
        )
        fig.update_layout(
            showlegend=True,
        )

        cmap = pyplot.get_cmap("tab20", 2 * len(sel_names))
        dates = list(
            pandas.date_range(
                start=hydpy.pub.timegrids.init.firstdate.datetime,
                end=hydpy.pub.timegrids.init.lastdate.datetime,
                freq=hydpy.pub.timegrids.init.stepsize.timedelta,
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
                ),
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
            ["add all to y-axis 1", [True, False]],
            ["remove all", [False, False]],
            ["add all to y-axis 2", [False, True]],
        ):
            subbuttons = [
                {
                    "label": label,
                    "method": "restyle",
                    "args": [
                        {
                            "visible": len(sel_sequences) * visibles,
                        }
                    ],
                }
            ]
            for idx, name in enumerate(sel_names):
                subbuttons.append(
                    {
                        "label": name,
                        "method": "restyle",
                        "args": [
                            {
                                "visible": visibles,
                            },
                            [2 * idx, 2 * idx + 1],
                        ],
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
            legend={
                "tracegroupgap": 100,
            },
        )

        docspath = docs.__path__[0]  # type: ignore[attr-defined, name-defined]
        fig.write_html(os.path.join(docspath, "html_", filename))


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

    def __init__(self, model, method, first_example=1, last_example=1, parseqs=None):
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

    def __call__(self, first_example=None, last_example=None):
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
            setattr(self.inits, parseq.name, parseq.values)

    def prepare_output_arrays(self):
        """Prepare arrays for storing the calculated results for the
        respective parameters and/or sequences."""
        for parseq in self.parseqs:
            shape = [len(self.raw_first_col_strings)] + list(parseq.shape)
            type_ = getattr(parseq, "TYPE", float)
            array = numpy.full(shape, numpy.nan, type_)
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

    Nevertheless, `testfile.txt` still exists in folder `iotesting`:

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

    def __init__(self, clear_own=False, clear_all=False):
        self._clear_own = clear_own
        self._clear_all = clear_all
        self._path = None
        self._olds = None

    def __enter__(self):
        self._path = os.getcwd()
        iotestingpath: str = iotesting.__path__[0]  # type: ignore[attr-defined, name-defined] # pylint: disable=line-too-long
        os.chdir(os.path.join(iotestingpath))
        if self._clear_own:
            self._olds = os.listdir(".")
        return self

    def __exit__(self, exception, message, traceback_):
        for file in os.listdir("."):
            if file.startswith(".coverage"):
                shutil.move(file, os.path.join(self._path, file))
            if (file != "__init__.py") and (
                self._clear_all or (self._clear_own and (file not in self._olds))
            ):
                if os.path.exists(file):
                    if os.path.isfile(file):
                        os.remove(file)
                    else:
                        shutil.rmtree(file)
        os.chdir(self._path)

    @classmethod
    def clear(cls):
        """Remove all files from the `iotesting` folder."""
        with cls(clear_all=True):
            pass


def make_abc_testable(abstract: Type) -> Type:
    """Return a concrete version of the given abstract base class for
    testing purposes.

    Abstract base classes cannot be (and, at least in production code,
    should not be) instantiated:

    >>> from hydpy.core.netcdftools import NetCDFVariableBase
    >>> ncvar = NetCDFVariableBase()
    Traceback (most recent call last):
    ...
    TypeError: Can't instantiate abstract class NetCDFVariableBase with \
abstract methods array, dimensions, read, subdevicenames, write

    However, it is convenient to do so for testing (partly) abstract
    base classes in doctests.  The derived class returned by function
    |make_abc_testable| is identical with the original one, except that
    its protection against initialisation is disabled:

    >>> from hydpy import make_abc_testable, classname
    >>> ncvar = make_abc_testable(NetCDFVariableBase)(False, False, 1)

    To avoid confusion, |make_abc_testable| appends an underscore the
    original class-name:

    >>> classname(ncvar)
    'NetCDFVariableBase_'
    """
    concrete = type(abstract.__name__ + "_", (abstract,), {})
    concrete.__abstractmethods__ = frozenset()
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
        def now(cls, tz=None):
            return testdatetime

    try:
        datetime.datetime = _DateTime
        yield
    finally:
        datetime.datetime = _datetime


class NumericalDifferentiator:
    """Approximate the derivatives of |ModelSequence| values based on
    the finite difference approach.

    .. _`here`: https://en.wikipedia.org/wiki/Finite_difference_coefficient

    Class |NumericalDifferentiator| is thought for testing purposes only.
    See, for example, the documentation on method |lstream_model.Calc_RHMDH_V1|,
    which uses a |NumericalDifferentiator| object to validate that this method
    calculates the derivative of sequence |lstream_aides.RHM| (`ysequence`)
    with respect to sequence |lstream_states.H| (`xsequence`) correctly.
    Therefore, it must know the relationship between |lstream_aides.RHM| and
    |lstream_states.H|, being defined by method |lstream_model.Calc_RHM_V1|.

    See also the documentation on method |lstream_model.Calc_AMDH_UMDH_V1|
    which how to apply class |NumericalDifferentiator| on multiple target
    sequences (`ysequences`).  Note that, in order to calculate the correct
    derivatives of sequences |lstream_aides.AM| and |lstream_aides.UM|, we
    need not only to pass |lstream_model.Calc_AM_UM_V1|, but also methods
    |lstream_model.Calc_RHM_V1| and |lstream_model.Calc_RHV_V1|, as sequences
    |lstream_aides.RHM| and |lstream_aides.RHV|, which are required for
    calculating |lstream_aides.AM| and |lstream_aides.UM|, depend on
    |lstream_states.H| themselves.

    Numerical approximations of derivatives are of limited precision.
    |NumericalDifferentiator| achieves the second order of accuracy, due to
    using the coefficients given `here`_.  If results are too inaccurate,
    you might improve them by changing the finite difference method
    (`backward` or `central` instead of `forward`) or by changing the
    default interval width `dx`.
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
        xsequence: sequencetools.ModelSequence,
        ysequences: Iterable[sequencetools.ModelSequence],
        methods: Iterable["modeltools.Method"],
        dx: float = 1e-6,
        method: Literal["forward", "central", "backward"] = "forward",
    ):
        self._xsequence = xsequence
        self._ysequences = tuple(ysequences)
        self._methods = tuple(methods)
        self._span = dx / 2.0
        self._method = method

    @property
    def _ycoeffs(self) -> numpy.ndarray:
        return self.__YCOEFFS[self._method] / self._span

    @property
    def _xshifts(self) -> numpy.ndarray:
        return self.__XSHIFTS[self._method] * self._span

    @property
    def _yvalues(self) -> Dict[sequencetools.ModelSequence, numpy.ndarray]:
        xvalues = copy.deepcopy(self._xsequence.values)
        if not self._xsequence.NDIM:
            nmb = 1
        else:
            nmb = len(xvalues)
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
    def _derivatives(self) -> Dict[sequencetools.ModelSequence, numpy.ndarray]:
        return {
            ysequence: numpy.dot(self._ycoeffs, yvalues.T)
            for ysequence, yvalues in self._yvalues.items()
        }

    def __call__(self):
        for ysequence, derivatives in self._derivatives.items():
            print(f"d_{ysequence.name}/d_{self._xsequence.name}", end=": ")
            objecttools.print_values(derivatives, width=1000)


def update_integrationtests(
    applicationmodel: Union[types.ModuleType, str],
    resultfilepath: str,
) -> None:
    """Write the docstring of the given application model, updated with
    the current simulation results, to file.

    Sometimes, even tiny model-related changes bring a great deal of work
    concerning *HydPy's* integration test strategy.  For example, if you
    modify the value of a fixed parameter, the results of possibly dozens
    of integration tests of your application model might become wrong.
    In such situations, function |update_integrationtests| helps you in
    replacing all integration tests results at ones.  Therefore, it
    calculates the new results, updates the old module docstring and
    writes it.  You only need to copy-paste the printed result into the
    affected module.  But be aware that function |update_integrationtests|
    cannot guarantee the correctness of the new results.  Whenever in doubt
    if the new results are really correct under all possible conditions,
    you should inspect and replace each integration test result manually.

    The following example, we disable method |conv_model.Pass_Outputs_V1|
    temporarily.  Accordingly, application model |conv_v001| does not pass
    any output to its outlet nodes, which is why the last four columns of
    both integration test tables now contain zero value only (we can perform
    this mocking-based test in Python-mode only):

    >>> from hydpy import pub, TestIO, update_integrationtests
    >>> from unittest import mock
    >>> pass_output = "hydpy.models.conv.conv_model.Pass_Outputs_V1.__call__"
    >>> with TestIO(), pub.options.usecython(False), mock.patch(pass_output):
    ...     update_integrationtests("conv_v001", "temp.txt")
    ...     with open("temp.txt") as resultfile:
    ...         print(resultfile.read())   # doctest: +ELLIPSIS
    Number of replacements: 2
    <BLANKLINE>
    Nearest-neighbour interpolation.
    ... test()
    |       date |      inputs |                outputs | in1 | in2 | out1 \
| out2 | out3 | out4 |
    -----------------------------------------------------------------------\
----------------------
    | 2000-01-01 | 1.0     4.0 | 1.0  4.0  1.0      1.0 | 1.0 | 4.0 |  0.0 \
|  0.0 |  0.0 |  0.0 |
    | 2000-01-02 | 2.0     nan | 2.0  nan  2.0      2.0 | 2.0 | nan |  0.0 \
|  0.0 |  0.0 |  0.0 |
    | 2000-01-03 | nan     nan | nan  nan  nan      nan | nan | nan |  0.0 \
|  0.0 |  0.0 |  0.0 |
    <BLANKLINE>
    ... test()
    |       date |      inputs |                outputs | in1 | in2 | out1 \
| out2 | out3 | out4 |
    -----------------------------------------------------------------------\
----------------------
    | 2000-01-01 | 1.0     4.0 | 1.0  4.0  1.0      1.0 | 1.0 | 4.0 |  0.0 \
|  0.0 |  0.0 |  0.0 |
    | 2000-01-02 | 2.0     nan | 2.0  2.0  2.0      2.0 | 2.0 | nan |  0.0 \
|  0.0 |  0.0 |  0.0 |
    | 2000-01-03 | nan     nan | nan  nan  nan      nan | nan | nan |  0.0 \
|  0.0 |  0.0 |  0.0 |
    <BLANKLINE>
    """
    module = importlib.import_module(f"hydpy.models.{applicationmodel}")
    docstring: str = module.__doc__
    stringio = io.StringIO  # pylint: disable=no-member
    with stringio() as resultfile, contextlib.redirect_stdout(resultfile):
        module.tester.perform_tests()
        result = resultfile.getvalue()
    oldlines, newlines = [], []
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
                docstring = docstring.replace(
                    "\n".join(oldlines),
                    "\n".join(newlines),
                )
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


def _enumerate(variables: Iterable[variabletools.Variable]) -> str:
    return objecttools.enumeration(
        v.__name__ for v in variabletools.sort_variables(variables)
    )


def check_methodorder(
    model: "modeltools.Model",
    indent: int = 0,
) -> str:
    """Check that *HydPy* calls the methods of the given application model
    in the correct order for each simulation step.

    The purpose of this function is to help model developers to ensure
    that each method uses only the values of those sequences that have
    been calculated by other methods beforehand.  *HydPy's* test routines
    apply |check_methodorder| automatically on each available application
    model. Alternatively, you can also execute it at the end of the
    docstring of an individual application model "manually", which
    suppresses the automatic execution and allows to check and discuss
    exceptional cases were |check_methodorder| generates false alarms.

    Function |check_methodorder| relies on the class constants
    `REQUIREDSEQUENCES`, `UPDATEDSEQUENCES`, and `RESULTSEQUENCES` of
    all relevant |Method| subclasses.  Hence, the correctness of its
    results depends on the correctness of these tuples.  However, even
    of those tuples are well-defined, one cannot expect |check_methodorder|
    to catch all kinds of order-related errors.  For example, consider the
    case where one method calculates only some values of a multi-dimensional
    sequence and another method the  remaining ones.  |check_methodorder|
    would not report anything when a third method, relying on the completeness
    of the sequence's values, were called after the first but before
    the second method.

    We use the quite complex model |lland_v3| as an example.
    |check_methodorder| does not report any problems:

    >>> from hydpy.core.testtools import check_methodorder
    >>> from hydpy.models.lland_v3 import Model
    >>> print(check_methodorder(Model))
    <BLANKLINE>

    To show how |check_methodorder| reports errors, we modify the
    `RESULTSEQUENCES` tuples of methods |lland_model.Calc_TKor_V1|,
    |lland_model.Calc_DryAirPressure_V1|, and |lland_model.Calc_QA_V1|:

    >>> from hydpy.models.lland.lland_model import (
    ...     Calc_TKor_V1, Calc_DryAirPressure_V1, Calc_QA_V1)
    >>> results_tkor = Calc_TKor_V1.RESULTSEQUENCES
    >>> results_dryairpressure = Calc_DryAirPressure_V1.RESULTSEQUENCES
    >>> results_qa = Calc_QA_V1.RESULTSEQUENCES
    >>> Calc_TKor_V1.RESULTSEQUENCES = ()
    >>> Calc_DryAirPressure_V1.RESULTSEQUENCES = ()
    >>> Calc_QA_V1.RESULTSEQUENCES += results_tkor

    Now, none of the relevant models calculates the value of sequence
    |lland_fluxes.DryAirPressure|.  For |lland_fluxes.TKor|, there is
    still a method (|lland_model.Calc_QA_V1|) calculating its values,
    but at a too-late stage of the simulation step:

    >>> print(check_methodorder(Model))    # doctest: +ELLIPSIS
    Method Calc_SaturationVapourPressure_V1 requires the following \
sequences, which are not among the result sequences of any of its \
predecessors: TKor
    ...
    Method Calc_DensityAir_V1 requires the following sequences, \
which are not among the result sequences of any of its predecessors: \
TKor and DryAirPressure
    ...
    Method Calc_EvB_V2 requires the following sequences, \
which are not among the result sequences of any of its predecessors: TKor

    To tidy up, we need to revert the above changes:

    >>> Calc_TKor_V1.RESULTSEQUENCES = results_tkor
    >>> Calc_DryAirPressure_V1.RESULTSEQUENCES = results_dryairpressure
    >>> Calc_QA_V1.RESULTSEQUENCES = results_qa
    >>> print(check_methodorder(Model))
    <BLANKLINE>
    """
    blanks = " " * indent
    results: List[str] = []
    excluded = (
        sequencetools.InputSequence,
        sequencetools.InletSequence,
        sequencetools.ReceiverSequence,
        sequencetools.StateSequence,
        sequencetools.LogSequence,
    )
    methods = tuple(model.get_methods())
    for idx, method1 in enumerate(methods):
        required = set(
            seq for seq in method1.REQUIREDSEQUENCES if not issubclass(seq, excluded)
        )
        for method0 in methods[:idx]:
            for seq in itertools.chain(
                method0.RESULTSEQUENCES,
                method0.UPDATEDSEQUENCES,
            ):
                if seq in required:
                    required.remove(seq)
        if required:
            results.append(
                f"{blanks}Method {method1.__name__} requires the following "
                f"sequences, which are not among the result sequences of any "
                f"of its predecessors: {_enumerate(required)}"
            )
    return "\n".join(results)


def check_selectedvariables(
    method: "modeltools.Method",
    indent: int = 0,
) -> str:
    """Perform consistency checks regarding the |Parameter| and |Sequence_|
    subclasses selected by the given |Method| subclass.

    The purpose of this function is to help model developers to ensure
    that the class tuples `CONTROLPARAMETERS`, `DERIVEDPARAMETERS`,
    `FIXEDPARAMETERS`, `REQUIREDSEQUENCES`, `UPDATEDSEQUENCES`, and
    `RESULTSEQUENCES` contain the correct parameter and sequence
    subclasses.  *HydPy's* test routines apply |check_selectedvariables|
    automatically on each method of each available application model.
    Alternatively, you can also execute it at the end of the docstring
    of an individual |Method| subclass "manually", which suppresses
    the automatic execution and allows to check and discuss exceptional
    cases were |check_selectedvariables| generates false alarms.

    Do not expect |check_selectedvariables| to catch all possible
    errors.  Also, false positives might occur.  However, in our experience
    functions |check_selectedvariables| is of great help to prevent most
    common mistakes when defining the parameter and sequence classes
    relevant for a specific method.

    As an example, we select method |lland_model.Calc_WindSpeed2m_V1| of base
    model |lland|.  |check_selectedvariables| does not reportany problems:

    >>> from hydpy.core.testtools import check_selectedvariables
    >>> from hydpy.models.lland.lland_model import (
    ...     Calc_WindSpeed2m_V1, Return_AdjustedWindSpeed_V1)
    >>> print(check_selectedvariables(Calc_WindSpeed2m_V1))
    <BLANKLINE>

    To show how |check_selectedvariables| reports errors, we clear the
    `RESULTSEQUENCES` tuple of method |lland_model.Calc_WindSpeed2m_V1|.
    Now |check_selectedvariables| realises the usage of the flux sequence
    object `windspeed2m` within the source code of method
    |lland_model.Calc_WindSpeed2m_V1|, which is neither available within
    the `REQUIREDSEQUENCES`, the `UPDATEDSEQUENCES`, nor the`RESULTSEQUENCES`
    tuple:

    >>> resultseqs = Calc_WindSpeed2m_V1.RESULTSEQUENCES
    >>> Calc_WindSpeed2m_V1.RESULTSEQUENCES = ()
    >>> print(check_selectedvariables(Calc_WindSpeed2m_V1))
    Definitely missing: windspeed2m

    After putting the wrong flux sequence class |lland_fluxes.WindSpeed10m|
    into the tuple, we get an additional warning pointing to our mistake:

    >>> from hydpy.models.lland.lland_fluxes import WindSpeed10m
    >>> Calc_WindSpeed2m_V1.RESULTSEQUENCES = WindSpeed10m,
    >>> print(check_selectedvariables(Calc_WindSpeed2m_V1))
    Definitely missing: windspeed2m
    Possibly erroneously selected (RESULTSEQUENCES): WindSpeed10m

    Method |lland_model.Calc_WindSpeed2m_V1| uses
    |lland_model.Return_AdjustedWindSpeed_V1| as a submethod.  Hence,
    |lland_model.Calc_WindSpeed2m_V1| most likely needs to select
    each variable selected by |lland_model.Return_AdjustedWindSpeed_V1|.
    After adding additional variables to the `DERIVEDPARAMETERS` tuple of
    |lland_model.Return_AdjustedWindSpeed_V1|, we get another warning message:

    >>> from hydpy.models.lland.lland_derived import (
    ...     Days, Hours, Seconds)
    >>> derivedpars = Return_AdjustedWindSpeed_V1.DERIVEDPARAMETERS
    >>> Return_AdjustedWindSpeed_V1.DERIVEDPARAMETERS = Days, Hours, Seconds
    >>> print(check_selectedvariables(Calc_WindSpeed2m_V1))
    Definitely missing: windspeed2m
    Possibly missing (DERIVEDPARAMETERS):
        Return_AdjustedWindSpeed_V1: Seconds, Hours, and Days
    Possibly erroneously selected (RESULTSEQUENCES): WindSpeed10m

    Finally, |check_selectedvariables| checks for duplicates both within
    and between the different tuples:

    >>> from hydpy.models.lland.lland_inputs import WindSpeed, TemL
    >>> requiredseqs = Calc_WindSpeed2m_V1.REQUIREDSEQUENCES
    >>> Calc_WindSpeed2m_V1.REQUIREDSEQUENCES = WindSpeed, WindSpeed, TemL
    >>> Calc_WindSpeed2m_V1.UPDATEDSEQUENCES = TemL,
    >>> print(check_selectedvariables(Calc_WindSpeed2m_V1))
    Definitely missing: windspeed2m
    Possibly missing (DERIVEDPARAMETERS):
        Return_AdjustedWindSpeed_V1: Seconds, Hours, and Days
    Possibly erroneously selected (REQUIREDSEQUENCES): TemL
    Possibly erroneously selected (UPDATEDSEQUENCES): TemL
    Possibly erroneously selected (RESULTSEQUENCES): WindSpeed10m
    Duplicates: TemL and WindSpeed

    To tidy up, we need to revert the above changes:

    >>> Calc_WindSpeed2m_V1.RESULTSEQUENCES = resultseqs
    >>> Return_AdjustedWindSpeed_V1.DERIVEDPARAMETERS = derivedpars
    >>> Calc_WindSpeed2m_V1.REQUIREDSEQUENCES = requiredseqs
    >>> Calc_WindSpeed2m_V1.UPDATEDSEQUENCES = ()
    >>> print(check_selectedvariables(Calc_WindSpeed2m_V1))
    <BLANKLINE>

    Some methods as |arma_model.Pick_Q_V1| of base model |arma| rely on
    the `len` attribute of 1-dimensional sequences.  Function
    |check_selectedvariables| does not report false alarms in such cases:

    >>> from hydpy.models.arma.arma_model import Pick_Q_V1
    >>> print(check_selectedvariables(Pick_Q_V1))
    <BLANKLINE>

    Some methods as |lland_model.Update_ESnow_V1| of base model |lland| update a
    sequence (meaning, they require its old value and calculate a new one), but
    their submethods (in this case |lland_model.Return_BackwardEulerError_V1|)
    just require them as input.  Function |check_selectedvariables| does not
    report false alarms in such cases:

    >>> from hydpy.models.lland.lland_model import Update_ESnow_V1
    >>> print(check_selectedvariables(Update_ESnow_V1))
    <BLANKLINE>
    """
    prefixes = (
        "con",
        "der",
        "fix",
        "inp",
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
        "REQUIREDSEQUENCES",
        "UPDATEDSEQUENCES",
        "RESULTSEQUENCES",
    )
    blanks = " " * indent
    results: List[str] = []
    # search for variables that are used in the source code but not
    # among the selected variables:
    source = inspect.getsource(method.__call__)
    vars_source = set()
    unbound_vars = inspect.getclosurevars(method.__call__).unbound
    for var, prefix in itertools.product(unbound_vars, prefixes):
        if f"{prefix}.{var}" in source:
            if var.startswith("len_"):
                var = var[4:]
            vars_source.add(var)
    vars_selected = set()
    for group in groups:
        vars_selected.update(g.__name__.lower() for g in getattr(method, group))
    diff = vars_source - vars_selected
    if diff:
        results.append(f"{blanks}Definitely missing: {objecttools.enumeration(diff)}")

    # search for variables selected by at least one submethod
    # but not by the method calling these submethods:
    for group in groups:
        vars_method = set(getattr(method, group))
        found_problem = False
        for submethod in method.SUBMETHODS:
            vars_submethods = set(getattr(submethod, group))
            if group == "REQUIREDSEQUENCES":
                vars_method.update(
                    set(method.UPDATEDSEQUENCES).intersection(
                        submethod.REQUIREDSEQUENCES
                    )
                )
            diff = vars_submethods - vars_method
            if diff:
                if not found_problem:
                    found_problem = True
                    results.append(f"{blanks}Possibly missing ({group}):")
                results.append(f"{blanks}    {submethod.__name__}: {_enumerate(diff)}")

    # search for selected variables that are neither used within the
    # source code nor selected by any submethod:
    group2vars_method = {g: set(getattr(method, g)) for g in groups}
    group2vars_submethods = {g: set() for g in groups}
    for submethod in method.SUBMETHODS:
        for group, vars_submethods in group2vars_submethods.items():
            vars_submethods.update(getattr(submethod, group))
    for group, vars_method in group2vars_method.items():
        vars_submethods = group2vars_submethods[group]
        diff = [
            method
            for method in vars_method - vars_submethods
            if method.__name__.lower() not in vars_source
        ]
        if diff:
            results.append(
                f"{blanks}Possibly erroneously selected ({group}): "
                f"{_enumerate(diff)}"
            )

    # search for variables that are selected multiple times:
    dupl = set()
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
        results.append(f"{blanks}Duplicates: {_enumerate(dupl)}")
    return "\n".join(results)


def perform_consistencychecks(
    applicationmodel=Union[types.ModuleType, str],
    indent: int = 0,
) -> str:
    """Perform all available consistency checks for the given application model.

    At the moment, function |perform_consistencychecks| calls function
    |check_selectedvariables| for each relevant model methods and function
    |check_methodorder| for the application model itself.  Note that
    |perform_consistencychecks| executes only those checks not already
    executed in the doctest of the respective method or model.  This
    alternative allows model developers to perform the tests themselves
    whenever exceptional cases result in misleading error reports and
    discuss any related potential pitfalls in the official documentation.

    As an example, we apply |perform_consistencychecks| on the application
    model |lland_v3|.  It does not report any potential problems (not
    already discussed in the documentation on the individual model methods):

    >>> from hydpy.core.testtools import perform_consistencychecks
    >>> print(perform_consistencychecks("lland_v3"))
    <BLANKLINE>

    To show how |perform_consistencychecks| reports errors, we modify the
    `RESULTSEQUENCES` tuple of method |lland_model.Calc_DryAirPressure_V1|:

    >>> from hydpy.models.lland.lland_model import (
    ...     Calc_DryAirPressure_V1)
    >>> results_dryairpressure = Calc_DryAirPressure_V1.RESULTSEQUENCES
    >>> Calc_DryAirPressure_V1.RESULTSEQUENCES = ()
    >>> print(perform_consistencychecks("lland_v3"))
    Potential consistency problems for individual methods:
       Method Calc_DryAirPressure_V1:
            Definitely missing: dryairpressure
    Potential consistency problems between methods:
        Method Calc_DensityAir_V1 requires the following sequences, which are \
not among the result sequences of any of its predecessors: DryAirPressure

    To tidy up, we need to revert the above changes:

    >>> Calc_DryAirPressure_V1.RESULTSEQUENCES = results_dryairpressure
    >>> print(perform_consistencychecks("lland_v3"))
    <BLANKLINE>
    """
    blanks = " " * indent
    model = importtools.prepare_model(applicationmodel)
    results: List[str] = []
    method2errors: Dict[str, str] = {}
    for method in model.get_methods():
        if "check_selectedvariables(" not in method.__doc__:
            subresult = check_selectedvariables(
                method=method,
                indent=indent + 8,
            )
            if subresult:
                method2errors[method.__name__] = subresult
    if method2errors:
        results.append(
            f"{blanks}Potential consistency problems for individual methods:"
        )
        for method, errors in method2errors.items():
            results.append(f"{blanks}   Method {method}:")
            results.append(errors)
    if "check_methodorder(" not in model.__doc__:
        subresult = check_methodorder(model, indent + 4)
        if subresult:
            results.append(f"{blanks}Potential consistency problems between methods:")
            results.append(subresult)
    return "\n".join(results)
