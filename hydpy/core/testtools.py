# -*- coding: utf-8 -*-
"""This module implements tools for making doctests clearer."""
# import...
# ...from standard library
import abc
import builtins
import contextlib
import datetime
import doctest
import importlib
import inspect
import os
import shutil
import sys
import warnings
from typing import *
# ...from site-packages
import numpy
# ...from HydPy
import hydpy
from hydpy import docs
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import hydpytools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import printtools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.tests import iotesting
models = exceptiontools.OptionalImport(
    'models', ['bokeh.models'], locals())
palettes = exceptiontools.OptionalImport(
    'palettes', ['bokeh.palettes'], locals())
plotting = exceptiontools.OptionalImport(
    'plotting', ['bokeh.plotting'], locals())


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
            self.print_('no failures occurred')
        else:
            for text in self.texts:
                self.print_(text)
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def write(self, text: str) -> None:
        """Memorise the given text for later writing."""
        self.texts.extend(text.split('\n'))

    def print_(self, text: str) -> None:
        """Print the memorised text to the original `sys.stdout`."""
        if text.strip():
            self.stdout.write(self.indent*' ' + text + '\n')

    def flush(self) -> None:
        """Do nothing."""


class Tester:
    """Tests either a base or an application model.

    Usually, a |Tester| object is initialised at the end of the `__init__`
    file of its base model or at the end of the module of an application
    model.

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
        self.package = frame.f_locals['__package__']
        self.ispackage = os.path.split(self.filepath)[-1] == '__init__.py'

    @property
    def filenames(self) -> List[str]:
        """The filenames defining the considered base or application model.

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
                fn for fn in os.listdir(os.path.dirname(self.filepath))
                if fn.endswith('.py'))
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
        return [os.path.split(fn)[-1].split('.')[0] for fn in self.filenames
                if (fn.endswith('.py') and not fn.startswith('_'))]

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
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'

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
        Timegrids(Timegrid('2000-01-01 00:00:00',
                           '2001-01-01 00:00:00',
                           '1d'))

        To show the reporting of possible errors, we change the
        string representation of parameter |hland_control.ZoneType|
        temporarily.  Again, the |Timegrids| object is reset to its
        initial state after testing:

        >>> from unittest import mock
        >>> with mock.patch(
        ...     'hydpy.models.hland.hland_control.ZoneType.__repr__',
        ...     return_value='damaged'):
        ...     hland.tester.perform_tests()   # doctest: +ELLIPSIS
        Test package hydpy.models.hland in ...ython mode.
            * hland_constants:
                no failures occurred
            * hland_control:
                ******...hland_control.py", line 72, in \
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
        Timegrids(Timegrid('2000-01-01 00:00:00',
                           '2001-01-01 00:00:00',
                           '1d'))
        """
        opt = hydpy.pub.options
        par = parametertools.Parameter
        color = 34 if hydpy.pub.options.usecython else 36
        with printtools.PrintStyle(color=color, font=4):
            print(
                'Test %s %s in %sython mode.'
                % ('package' if self.ispackage else 'module',
                   self.package if self.ispackage else
                   self.modulenames[0],
                   'C' if hydpy.pub.options.usecython else 'P'))
        with printtools.PrintStyle(color=color, font=2):
            for name in self.modulenames:
                print('    * %s:' % name, )
                # pylint: disable=not-callable
                # pylint does understand that all options are callable
                # except option `printincolor`!?
                with StdOutErr(indent=8), \
                        opt.ellipsis(0), \
                        opt.printincolor(False), \
                        opt.printprogress(False), \
                        opt.reprcomments(False), \
                        opt.reprdigits(6), \
                        opt.usedefaultvalues(False), \
                        opt.utclongitude(15), \
                        opt.utcoffset(60), \
                        opt.warnsimulationstep(False), \
                        opt.warntrim(False), \
                        par.parameterstep.delete(), \
                        par.simulationstep.delete():
                    # pylint: enable=not-callable
                    projectname = hydpy.pub.get('projectname')
                    del hydpy.pub.projectname
                    timegrids = hydpy.pub.get('timegrids')
                    del hydpy.pub.timegrids
                    registry = devicetools.gather_registries()
                    plotting_options = IntegrationTest.plotting_options
                    IntegrationTest.plotting_options = PlottingOptions()
                    try:
                        modulename = '.'.join((self.package, name))
                        module = importlib.import_module(modulename)
                        with warnings.catch_warnings():
                            warnings.filterwarnings(
                                'error', module=modulename)
                            warnings.filterwarnings(
                                'error', category=UserWarning)
                            warnings.filterwarnings(
                                'ignore', category=ImportWarning)
                            doctest.testmod(
                                module, extraglobs={'testing': True},
                                optionflags=doctest.ELLIPSIS)
                    finally:
                        hydpy.pub.projectname = projectname
                        if timegrids is not None:
                            hydpy.pub.timegrids = timegrids
                        devicetools.reset_registries(registry)
                        IntegrationTest.plotting_options = plotting_options
                        hydpy.dummies.clear()


class Array:
    """Assures that attributes are |numpy.ndarray| objects."""

    def __setattr__(self, name, value):
        object.__setattr__(self, name, numpy.array(value))


class ArrayDescriptor:
    """Descriptor for handling values of |Array| objects."""

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
    How the tests shall be prepared and performed, is to be defined in
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
        """Number of rows of the table."""
        return len(self.raw_first_col_strings)+1

    @property
    def nmb_cols(self):
        """Number of columns of the table."""
        nmb = 1
        for parseq in self.parseqs:
            nmb += max(len(parseq), 1)
        return nmb

    @property
    def raw_header_strings(self):
        """All raw strings for the tables header."""
        strings = [self.HEADER_OF_FIRST_COL]
        for parseq in self.parseqs:
            for dummy in range(len(parseq)-1):
                strings.append('')
            if ((parseq.name == 'sim') and
                    isinstance(parseq, sequencetools.Sequence)):
                strings.append(parseq.subseqs.node.name)
            else:
                strings.append(parseq.name)
        return strings

    @property
    def raw_body_strings(self):
        """All raw strings for the tables body."""
        strings = []
        for (idx, first_string) in enumerate(self.raw_first_col_strings):
            strings.append([first_string])
            for parseq in self.parseqs:
                array = self.get_output_array(parseq)
                if parseq.NDIM == 0:
                    strings[-1].append(objecttools.repr_(array[idx]))
                else:
                    strings[-1].extend(
                        objecttools.repr_(value) for value in array[idx])
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
    def col_seperators(self):
        """The seperators for adjacent columns."""
        seps = ['| ']
        for parseq in self.parseqs:
            seps.append(' | ')
            for dummy in range(len(parseq)-1):
                seps.append('  ')
        seps.append(' |')
        return seps

    @property
    def row_nmb_characters(self):
        """Number of characters of a single row of the table."""
        return (sum(self.col_widths) +
                sum((len(sep) for sep in self.col_seperators)))

    @staticmethod
    def _interleave(seperators, strings, widths):
        """Generate a table line from the given arguments."""
        lst = [value for (seperator, string, width)
               in zip(seperators, strings, widths)
               for value in (seperator, string.rjust(width))]
        lst.append(seperators[-1])
        return ''.join(lst)

    def print_table(self, idx1=None, idx2=None):
        """Print the result table between the given indices."""
        col_widths = self.col_widths
        col_seperators = self.col_seperators
        print(self._interleave(self.col_seperators,
                               self.raw_header_strings,
                               col_widths))
        print('-'*self.row_nmb_characters)
        for strings_in_line in self.raw_body_strings[idx1:idx2]:
            print(self._interleave(col_seperators,
                                   strings_in_line,
                                   col_widths))

    @staticmethod
    def extract_units(parseqs):
        """Return a set of units of the given parameters and sequences."""
        units = set()
        for parseq in parseqs:
            desc = objecttools.description(parseq)
            if '[' in desc:
                unit = desc.split('[')[-1].split(']')[0]
                units.add(unit)
        return units


class PlottingOptions:
    """Plotting options of class |IntegrationTest|."""

    def __init__(self):
        self.width = 600
        self.height = 300
        self.activated = None
        self.selected = None


class IntegrationTest(Test):
    """Defines model integration doctests.

    The functionality of |IntegrationTest| is easiest to understand by
    inspecting doctests like the ones of modules |llake_v1| or |arma_v1|.

    Note that all condition sequences (state and logging sequences) are
    initialised in accordance with the values are given in the `inits`
    values.  The values of the simulation sequences of outlet and
    sender nodes are always set to zero before each test run.  All other
    parameter and sequence values can be changed between different test
    runs.
    """

    HEADER_OF_FIRST_COL = 'date'
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
            selectiontools.Selection('test', self.nodes, self.elements))
        self._src = None
        self._width = None
        self._height = None

    def __call__(self, *args, update_parameters=True, **kwargs):
        """Prepare and perform an integration test and print and eventually
        plot its results.

        Plotting is only performed, when a filename is given as first
        argument.  Additionally, all other arguments of function
        |IntegrationTest.plot| are allowed to modify plot design.
        """
        self.prepare_model(update_parameters=update_parameters)
        self.hydpy.simulate()
        self.print_table()
        if args:
            self.plot(*args, **kwargs)

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

        You can query and change property |IntegrationTest.dateformat|.
        Passing ill-defined format strings results in the shown error:

        >>> from hydpy import Element, IntegrationTest, prepare_model, pub
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'
        >>> element = Element('element', outlets='node')
        >>> element.model = prepare_model('hland_v1')
        >>> __package__ = 'testpackage'
        >>> tester = IntegrationTest(element)
        >>> tester.dateformat
        '%Y-%m-%d %H:%M:%S'

        >>> tester.dateformat = '%'
        Traceback (most recent call last):
        ...
        ValueError: The given date format `%` is not a valid format \
string for `datetime` objects.  Please read the documentation on module \
datetime of the Python standard library for for further information.

        >>> tester.dateformat = '%x'
        >>> tester.dateformat
        '%x'
        """
        dateformat = vars(self).get('dateformat')
        if dateformat is None:
            return timetools.Date.formatstrings['iso2']
        return dateformat

    @dateformat.setter
    def dateformat(self, dateformat: str) -> None:
        try:
            datetime.datetime(2000, 1, 1).strftime(dateformat)
        except BaseException:
            raise ValueError(
                f'The given date format `{dateformat}` is not a valid '
                f'format string for `datetime` objects.  Please read '
                f'the documentation on module datetime of the Python '
                f'standard library for for further information.')
        vars(self)['dateformat'] = dateformat

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
                node.deploymode = 'oldsim'
            sim = node.sequences.sim
            sim.activate_ram()

    def prepare_input_model_sequences(self):
        """Configure the input sequences of the model in a manner that allows
        for applying their time series data in integration tests."""
        subseqs = getattr(self.element.model.sequences, 'inputs', ())
        for seq in subseqs:
            seq.activate_ram()

    def extract_print_sequences(self):
        """Return a list of all input, flux and state sequences of the model
        as well as the simulation sequences of all nodes."""
        seqs = []
        for name in ('inputs', 'fluxes', 'states'):
            subseqs = getattr(self.element.model.sequences, name, ())
            for seq in subseqs:
                seqs.append(seq)
        for node in self.nodes:
            seqs.append(node.sequences.sim)
        return seqs

    def prepare_model(self, update_parameters):
        """Derive the secondary parameter values, prepare all required time
        series and set the initial conditions.
        """
        if update_parameters:
            self.model.parameters.update()
        self.element.prepare_fluxseries()
        self.element.prepare_stateseries()
        self.reset_outputs()
        self.reset_inits()

    def reset_outputs(self):
        """Set the values of the simulation sequences of all outlet nodes to
        zero."""
        for node in self.nodes:
            if ((node in self.element.outlets) or
                    (node in self.element.senders)):
                node.sequences.sim[:] = 0.

    def reset_inits(self):
        """Set all initial conditions of all models."""
        for subname in ('states', 'logs'):
            for element in self.elements:
                for seq in getattr(element.model.sequences, subname, ()):
                    try:
                        seq(getattr(self.inits, seq.name))
                    except AttributeError:
                        pass

    def plot(self, filename, width=None, height=None,
             selected=None, activated=None):
        """Save a bokeh html file plotting the current test results.

        (Optional) arguments:
            * filename: Name of the file.  If necessary, the file ending
              `html` is added automatically.  The file is stored in the
              `html` folder of subpackage `docs`.
            * width: Width of the plot in screen units.  Defaults to 600.
            * height: Height of the plot in screen units.  Defaults to 300.
            * selected: List of the sequences to be plotted.
            * activated: List of the sequences to be shown initially.
        """
        if width is None:
            width = self.plotting_options.width
        if height is None:
            height = self.plotting_options.height
        if not filename.endswith('.html'):
            filename += '.html'
        if selected is None:
            selected = self.plotting_options.selected
            if selected is None:
                selected = self.parseqs
        if activated is None:
            activated = self.plotting_options.activated
            if activated is None:
                activated = self.parseqs
        activated = tuple(nm_.name if hasattr(nm_, 'name') else nm_.lower()
                          for nm_ in activated)
        path = os.path.join(docs.__path__[0], 'html', filename)
        plotting.output_file(path)
        plot = plotting.figure(x_axis_type="datetime",
                               tools=['pan', 'ywheel_zoom'],
                               toolbar_location=None)
        plot.toolbar.active_drag = plot.tools[0]
        plot.toolbar.active_scroll = plot.tools[1]
        plot.plot_width = width
        plot.plot_height = height
        legend_entries = []
        viridis = palettes.viridis
        headers = [header for header in self.raw_header_strings[1:]
                   if header]
        zipped = zip(selected,
                     viridis(len(selected)),
                     headers)
        for (seq, col, header) in zipped:
            series = seq.series.copy()
            if not seq.NDIM:
                listofseries = [series]
                listofsuffixes = ['']
            else:
                nmb = seq.shape[0]
                listofseries = [series[:, idx] for idx in range(nmb)]
                if nmb == 1:
                    listofsuffixes = ['']
                else:
                    listofsuffixes = ['-%d' % idx for idx in range(nmb)]
            for subseries, suffix in zip(listofseries, listofsuffixes):
                line = plot.line(self._datetimes, subseries,
                                 alpha=0.8, muted_alpha=0.0,
                                 line_width=2, color=col)
                line.muted = seq.name not in activated
                if header.strip() == seq.name:
                    title = objecttools.classname(seq)
                else:
                    title = header.capitalize()
                title += suffix
                legend_entries.append((title, [line]))
        legend = models.Legend(items=legend_entries,
                               click_policy='mute')
        legend.border_line_color = None
        plot.add_layout(legend, 'right')
        units = self.extract_units(selected)
        ylabel = objecttools.enumeration(units).replace('and', 'or')
        plot.yaxis.axis_label = ylabel
        plot.yaxis.axis_label_text_font_style = 'normal'
        plotting.save(plot)
        self._src = filename
        self._width = width
        self._height = height

    def print_iframe(self, tabs: int = 4) -> None:
        """Print a command for embeding the saved html file into the online
        documentation via an `iframe`.

        >>> from hydpy import Element, IntegrationTest, prepare_model, pub
        >>> pub.timegrids = '2000-01-01', '2001-01-01', '1d'
        >>> element = Element('element', outlets='node')
        >>> element.model = prepare_model('hland_v1')
        >>> __package__ = 'testpackage'
        >>> IntegrationTest(element).print_iframe()
            .. raw:: html
        <BLANKLINE>
                <iframe
                    src="None"
                    width="100"
                    height="330"
                    frameborder=0
                ></iframe>
        <BLANKLINE>
        """
        blanks = ' '*tabs
        height = self._height
        height = self.plotting_options.height if height is None else height
        lines = [f'.. raw:: html',
                 f'',
                 f'    <iframe',
                 f'        src="{self._src}"',
                 f'        width="100"',
                 f'        height="{height+30}"',
                 f'        frameborder=0',
                 f'    ></iframe>',
                 f'']
        print('\n'.join(blanks+line for line in lines))


class UnitTest(Test):
    """Defines unit doctests for a single model method."""

    HEADER_OF_FIRST_COL = 'ex.'
    """The header of the first column containing sequential numbers."""

    nexts = ArrayDescriptor()
    """Stores arrays for setting different values of parameters and/or
    sequences before each new experiment."""

    results = ArrayDescriptor()
    """Stores arrays with the resulting values of parameters and/or
    sequences of each new experiment."""

    def __init__(self, model, method, first_example=1, last_example=1,
                 parseqs=None):
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
        self.memorize_inits()
        self.prepare_output_arrays()

    @property
    def nmb_examples(self):
        """The number of examples to be calculated."""
        return self.last_example_calc-self.first_example_calc+1

    @property
    def idx0(self):
        """First index of the examples selected for printing."""
        return self.first_example_plot-self.first_example_calc

    @property
    def idx1(self):
        """Last index of the examples selected for printing."""
        return self.nmb_examples-(self.last_example_calc -
                                  self.last_example_plot)

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
        return [str(example) for example in
                range(self.first_example_plot, self.last_example_plot+1)]

    def memorize_inits(self):
        """Memorize all initial conditions."""
        for parseq in self.parseqs:
            setattr(self.inits, parseq.name, parseq.values)

    def prepare_output_arrays(self):
        """Prepare arrays for storing the calculated results for the
        respective parameters and/or sequences."""
        for parseq in self.parseqs:
            shape = [len(self.raw_first_col_strings)] + list(parseq.shape)
            type_ = getattr(parseq, 'TYPE', float)
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
        'Reading is not possible at the moment.  Please see the '
        'documentation on class `Open` of module `testtools` '
        'for further information.')

    def __init__(self, path, mode, *args, **kwargs):
        # pylint: disable=unused-argument
        # all further positional and keyword arguments are ignored.
        self.path = path.replace(os.sep, '/')
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
        """Replaces the `write` method of file objects."""
        self.texts.append(text)

    def writelines(self, lines):
        """Replaces the `writelines` method of file objects."""
        self.texts.extend(lines)

    def close(self):
        """Replaces the `close` method of file objects."""
        text = ''.join(self.texts)
        maxchars = len(self.path)
        lines = []
        for line in text.split('\n'):
            if not line:
                line = '<BLANKLINE>'
            lines.append(line)
            maxchars = max(maxchars, len(line))
        text = '\n'.join(lines)
        print('~'*maxchars)
        print(self.path)
        print('-'*maxchars)
        print(text)
        print('~'*maxchars)


class Open:
    """Replace |open| in doctests temporarily.

    Class |Open| to intended to make writing to files visible and testable
    in docstrings.  Therefore, Python's built in function |open| is
    temporarily replaced by another object, printing the filename and the
    file contend as shown in the following example:

    >>> import os
    >>> path = os.path.join('folder', 'test.py')
    >>> from hydpy import Open
    >>> with Open():
    ...     with open(path, 'w') as file_:
    ...         file_.write('first line\\n')
    ...         file_.writelines(['\\n', 'third line\\n'])
    ~~~~~~~~~~~~~~
    folder/test.py
    --------------
    first line
    <BLANKLINE>
    third line
    <BLANKLINE>
    ~~~~~~~~~~~~~~

    Note that, for simplicity, the UNIX style path seperator `/` is used
    to print the file path on all systems.

    Class |Open| is rather restricted at the moment.  Functionalities
    like reading are not supported so far:

    >>> with Open():
    ...     with open(path, 'r') as file_:
    ...         file_.read()
    Traceback (most recent call last):
    ...
    NotImplementedError: Reading is not possible at the moment.  \
Please see the documentation on class `Open` of module `testtools` \
for further information.

    >>> with Open():
    ...     with open(path, 'r') as file_:
    ...         file_.readline()
    Traceback (most recent call last):
    ...
    NotImplementedError: Reading is not possible at the moment.  \
Please see the documentation on class `Open` of module `testtools` \
for further information.

    >>> with Open():
    ...     with open(path, 'r') as file_:
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
    >>> os.path.exists('testfile.txt')
    False

    If some tests require writing such a file, this should be done
    within HydPy's `iotesting` folder in subpackage `tests`, which
    is achieved by appyling the `with` statement on |TestIO|:

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     open('testfile.txt', 'w').close()
    ...     print(os.path.exists('testfile.txt'))
    True

    After the `with` block, the working directory is reset automatically:

    >>> os.path.exists('testfile.txt')
    False

    Nevertheless, `testfile.txt` still exists in folder `iotesting`:

    >>> with TestIO():
    ...     print(os.path.exists('testfile.txt'))
    True

    Optionally, files and folders created within the current `with` block
    can be removed automatically by setting `clear_own` to |True|
    (modified files and folders are not affected):

    >>> with TestIO(clear_own=True):
    ...     open('testfile.txt', 'w').close()
    ...     os.makedirs('testfolder')
    ...     print(os.path.exists('testfile.txt'),
    ...           os.path.exists('testfolder'))
    True True
    >>> with TestIO(clear_own=True):
    ...     print(os.path.exists('testfile.txt'),
    ...           os.path.exists('testfolder'))
    True False

    Alternatively, all files and folders contained in folder `iotesting`
    can be removed after leaving the `with` block:

    >>> with TestIO(clear_all=True):
    ...     os.makedirs('testfolder')
    ...     print(os.path.exists('testfile.txt'),
    ...           os.path.exists('testfolder'))
    True True
    >>> with TestIO(clear_own=True):
    ...     print(os.path.exists('testfile.txt'),
    ...           os.path.exists('testfolder'))
    False False

    For just clearing the `iofolder`, one can call method |TestIO.clear|
    alternatively:

    >>> with TestIO():
    ...     open('testfile.txt', 'w').close()
    ...     print(os.path.exists('testfile.txt'))
    True
    >>> TestIO.clear()
    >>> with TestIO():
    ...     print(os.path.exists('testfile.txt'))
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
        os.chdir(os.path.join(iotesting.__path__[0]))
        if self._clear_own:
            self._olds = os.listdir('.')
        return self

    def __exit__(self, exception, message, traceback_):
        for file in os.listdir('.'):
            if file.startswith('.coverage'):
                shutil.move(file, os.path.join(self._path, file))
            if ((file != '__init__.py') and
                    (self._clear_all or
                     (self._clear_own and (file not in self._olds)))):
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
    its protection against initialization is disabled:

    >>> from hydpy import make_abc_testable, classname
    >>> ncvar = make_abc_testable(NetCDFVariableBase)(False, False, 1)

    To avoid confusion, |make_abc_testable| suffixes an underscore the
    original classname:

    >>> classname(ncvar)
    'NetCDFVariableBase_'
    """
    concrete = type(abstract.__name__ + '_', (abstract,), {})
    concrete.__abstractmethods__ = frozenset()
    return concrete


@contextlib.contextmanager
def mock_datetime_now(testdatetime):
    """Let class method |datetime.datetime.now| of class |datetime.datetime|
    of module |datetime| return the given date for testing purposes within
    a "with block".

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

    A test to see that mocking |datetime.datetime| does not interfere
    with initialising |Date| objects and that exceptions are property
    handled:

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
