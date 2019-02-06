# -*- coding: utf-8 -*-
"""This module implements tools for making doctests more legible."""
# import...
# ...from standard library
import abc
import builtins
import contextlib
import datetime
import doctest
import importlib
import inspect
import itertools
import os
import shutil
import sys
import warnings
# ...from site-packages
# the following import are actually performed below due to performance issues:
# import bokeh.models
# import bokeh.palettes
# import bokeh.plotting
import numpy
# ...from HydPy
import hydpy
from hydpy import pub
from hydpy import docs
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import hydpytools
from hydpy.core import metatools
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import printtools
from hydpy.core import selectiontools
from hydpy.core import timetools
from hydpy.tests import iotesting


class StdOutErr(object):

    def __init__(self, indent=0):
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
        if exception:
            objecttools.augment_excmessage()

    def write(self, text):
        self.texts.extend(text.split('\n'))

    def print_(self, text):
        if text.strip():
            self.stdout.write(self.indent*' ' + text + '\n')

    def flush(self):
        pass


class Tester(object):
    """Tests either a base or an application model.

    Usually, a |Tester| object is initialized at the end of the `__init__`
    file of its base model or at the end of the module of an application
    modele.
    """

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.filepath = frame.f_code.co_filename
        self.package = frame.f_locals['__package__']
        if not self.package:
            self.package = 'hydpy.models'
        self.ispackage = os.path.split(self.filepath)[-1] == '__init__.py'

    @property
    def filenames(self):
        """|list| of all filenames to be taken into account for testing."""
        if self.ispackage:
            return os.listdir(os.path.dirname(self.filepath))
        return [self.filepath]

    @property
    def modulenames(self):
        """|list| of all module names to be taken into account for testing."""
        return [os.path.split(fn)[-1].split('.')[0] for fn in self.filenames
                if (fn.endswith('.py') and not fn.startswith('_'))]

    def doit(self):
        """Perform all doctests either in Python or in Cython mode depending
        on the state of |Options.usecython| set in module |pub|.

        Usually, |Tester.doit| is triggered automatically by a |Cythonizer|
        object assigned to the same base or application model as a
        |Tester| object.
        """
        opt = pub.options
        par = parametertools.Parameter
        color = 34 if pub.options.usecython else 36
        with printtools.PrintStyle(color=color, font=4):
            print(
                'Test %s %s in %sython mode.'
                % ('package' if self.ispackage else 'module',
                   self.package if self.ispackage else
                   self.modulenames[0],
                   'C' if pub.options.usecython else 'P'))
        with printtools.PrintStyle(color=color, font=2):
            for name in self.modulenames:
                print('    * %s:' % name, )
                with StdOutErr(indent=8), \
                        opt.usedefaultvalues(False), \
                        opt.usedefaultvalues(False), \
                        opt.printprogress(False), \
                        opt.printincolor(False), \
                        opt.warnsimulationstep(False), \
                        opt.reprcomments(False), \
                        opt.ellipsis(0), \
                        opt.reprdigits(6), \
                        opt.warntrim(False), \
                        par.parameterstep.delete(), \
                        par.simulationstep.delete():
                    projectname = pub.get('projectname')
                    del pub.projectname
                    timegrids = pub.get('timegrids')
                    del pub.timegrids
                    nodes = devicetools.Node._registry.copy()
                    elements = devicetools.Element._registry.copy()
                    devicetools.Node.clear_registry()
                    devicetools.Element.clear_registry()
                    plotting_options = IntegrationTest.plotting_options
                    IntegrationTest.plotting_options = PlottingOptions()
                    try:
                        modulename = '.'.join((self.package, name))
                        module = importlib.import_module(modulename)
                        solve_exception_doctest_issue(module)
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
                        pub.projectname = projectname
                        if timegrids is not None:
                            pub.timegrids = timegrids
                        devicetools.Node.clear_registry()
                        devicetools.Element.clear_registry()
                        devicetools.Node._registry = nodes
                        devicetools.Element._registry = elements
                        IntegrationTest.plotting_options = plotting_options
                        hydpy.dummies.clear()


class Array(object):
    """Assures that attributes are |numpy.ndarray| objects."""

    def __setattr__(self, name, value):
        object.__setattr__(self, name, numpy.array(value))


class ArrayDescriptor(object):
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


class Test(object):
    """Base class for |IntegrationTest| and |UnitTest|.

    This base class defines the printing of the test results primarily.
    How the tests shall be prepared and performed, is to be defined in
    its subclasses.
    """

    inits = ArrayDescriptor()
    """Stores arrays for setting the same values of parameters and/or
    sequences before each new experiment."""

    @property
    @abc.abstractmethod
    def raw_first_col_strings(self):
        """To be implemented by the subclasses of |Test|."""
        return NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def get_output_array(parseq):
        # pylint: disable=unused-argument
        """To be implemented by the subclasses of |Test|."""
        return NotImplementedError

    parseqs = NotImplemented

    HEADER_OF_FIRST_COL = NotImplemented

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
                    isinstance(parseq, abctools.SequenceABC)):
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
                elif parseq.NDIM == 1:
                    if parseq.shape[0] > 0:
                        strings[-1].extend(
                            objecttools.repr_(value) for value in array[idx])
                    else:
                        strings[-1].append('empty')
                else:
                    thing = ('sequence'
                             if isinstance(parseq, abctools.SequenceABC)
                             else 'parameter')
                    raise RuntimeError(
                        'An instance of class `Test` of module `testtools` '
                        'is requested to print the results of %s `%s`. '
                        'Unfortunately, for %d-dimensional sequences this '
                        'feature is not supported yet.'
                        % (thing, parseq.name, parseq.NDIM))
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

    def extract_units(self, parseqs=None):
        """Return a set of units of the given or the handled parameters
        and sequences."""
        if parseqs is None:
            parseqs = self.parseqs
        units = set()
        for parseq in parseqs:
            desc = metatools.description(parseq)
            if '[' in desc:
                unit = desc.split('[')[-1].split(']')[0]
                units.add(unit)
        return units


class PlottingOptions(object):
    """Plotting options of class |IntegrationTest|."""

    def __init__(self):
        self.width = 600
        self.height = 300
        self.activated = None
        self.selected = None
        self.skip_nodes = True


class IntegrationTest(Test):
    """Defines model integration doctests.

    The functionality of |IntegrationTest| is easiest to understand by
    inspecting doctests like the ones of modules |llake_v1| or |arma_v1|.

    Note that all condition sequences (state and logging sequences) are
    initialized in accordance with the values are given in the `inits`
    values.  The values of the simulation sequences of outlet and
    sender nodes are always set to zero before each test run.  All other
    parameter and sequence values can be changed between different test
    runs.
    """

    HEADER_OF_FIRST_COL = 'date'
    """The header of the first column containing dates."""

    _dateformat = None

    plotting_options = PlottingOptions()

    def __init__(self, element, seqs=None, inits=None):
        """Prepare the element and its nodes and put them into a HydPy object
        and make their sequences ready for use for integration testing."""
        del self.inits
        self.element = element
        self.elements = devicetools.Element.registered_elements()
        self.nodes = devicetools.Node.registered_nodes()
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

    def __call__(self, *args, **kwargs):
        """Prepare and perform an integration test and print and eventually
        plot its results.

        Plotting is only performed, when a filename is given as first
        argument.  Additionally, all other arguments of function
        |IntegrationTest.plot| are allowed to modify plot design.
        """
        self.prepare_model()
        self.hydpy.doit()
        self.print_table()
        if args:
            self.plot(*args, **kwargs)

    @property
    def _datetimes(self):
        return tuple(date.datetime for date in pub.timegrids.sim)

    @property
    def raw_first_col_strings(self):
        """The raw date strings of the first column, except the header."""
        return tuple(_.strftime(self.dateformat) for _ in self._datetimes)

    def _getdateformat(self):
        """Format string for printing dates in the first column of the table.

        See |datetime| for the format strings allowed.
        """
        if self._dateformat is None:
            return timetools.Date._formatstrings['iso']
        return self._dateformat

    def _setdateformat(self, dateformat):
        try:
            dateformat = str(dateformat)
        except BaseException:
            raise TypeError(
                'The given `dateformat` of type `%s` could not be converted '
                'to a `str` instance.' % objecttools.classname(dateformat))
        try:
            datetime.datetime(2000, 1, 1).strftime(dateformat)
        except BaseException:
            raise ValueError(
                "The given `dateformat` `%s` is not a valid format string "
                "for `datetime` objects.  Please read the documentation "
                "on module `datetime` of Python's the standard library "
                "for further information." % dateformat)
        self._dateformat = dateformat

    dateformat = property(_getdateformat, _setdateformat)

    @staticmethod
    def get_output_array(seq):
        """Return the array containing the output results of the given
        sequence."""
        return seq.series

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

    def prepare_model(self):
        """Derive the secondary parameter values, prepare all required time
        series and set the initial conditions.
        """
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
             selected=None, activated=None, skip_nodes=None):
        """Save a bokeh html file plotting the current test results.

        (Optional) arguments:
            * filename: Name of the file.  If necessary, the file ending
              `html` is added automatically.  The file is stored in the
              `html` folder of subpackage `docs`.
            * width: Width of the plot in screen units.  Defaults to 600.
            * height: Height of the plot in screen units.  Defaults to 300.
            * selected: List of the sequences to be plotted.
            * activated: List of the sequences to be shown initially.
            * skip_nodes: Boolean flag that indicates whether series of
              node objects shall be plotted or not. Defaults to `False`.
        """
        import bokeh.models
        import bokeh.palettes
        import bokeh.plotting
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
        if skip_nodes is None:
            skip_nodes = self.plotting_options.skip_nodes
        if skip_nodes:
            selected = [seq for seq in selected
                        if not isinstance(seq, abctools.NodeSequenceABC)]
        if activated is None:
            activated = self.plotting_options.activated
            if activated is None:
                activated = self.parseqs
        activated = tuple(nm_.name if hasattr(nm_, 'name') else nm_.lower()
                          for nm_ in activated)
        path = os.path.join(docs.__path__[0], 'html', filename)
        bokeh.plotting.output_file(path)
        plot = bokeh.plotting.figure(x_axis_type="datetime",
                                     tools=['pan', 'ywheel_zoom'],
                                     toolbar_location=None)
        plot.toolbar.active_drag = plot.tools[0]
        plot.toolbar.active_scroll = plot.tools[1]
        plot.plot_width = width
        plot.plot_height = height
        legend_entries = []
        viridis = bokeh.palettes.viridis   # pylint: disable=no-member
        headers = [header for header in self.raw_header_strings[1:]
                   if header]
        zipped = zip(selected,
                     viridis(len(selected)),
                     headers)
        for (seq, col, header) in zipped:
            series = seq.series.copy()
            if seq.NDIM == 0:
                listofseries = [series]
                listofsuffixes = ['']
            elif seq.NDIM == 1:
                nmb = seq.shape[0]
                listofseries = [series[:, idx] for idx in range(nmb)]
                if nmb == 1:
                    listofsuffixes = ['']
                else:
                    listofsuffixes = ['-%d' % idx for idx in range(nmb)]
            else:
                raise RuntimeError(
                    'IntegrationTest does not support plotting values of '
                    'sequences with more than 1 dimension so far, but '
                    'sequence `%s` is %d-dimensional.'
                    % (seq.name, seq.NDIM))
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
        legend = bokeh.models.Legend(items=legend_entries,
                                     click_policy='mute')
        legend.border_line_color = None
        plot.add_layout(legend, 'right')
        units = self.extract_units(selected)
        ylabel = objecttools.enumeration(units).replace('and', 'or')
        plot.yaxis.axis_label = ylabel
        plot.yaxis.axis_label_text_font_style = 'normal'
        bokeh.plotting.save(plot)
        self._src = filename
        self._width = width
        self._height = height

    def iframe(self, tabs=4):
        """Print a command for embeding the saved html file into the online
        documentation via an `iframe`."""
        blanks = ' '*tabs
        lines = ['.. raw:: html',
                 '',
                 '    <iframe',
                 '        src="%s"' % self._src,
                 '        width="100%"',
                 '        height="%dpx"' % (self._height+30),
                 '        frameborder=0',
                 '    ></iframe>',
                 '']
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
        self.doc = self.extract_method_doc()
        self.first_example_calc = first_example
        self.last_example_calc = last_example
        self.first_example_plot = first_example
        self.last_example_plot = last_example
        if parseqs:
            self.parseqs = parseqs
        else:
            self.parseqs = self.extract_print_parameters_and_sequences()
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

    def get_output_array(self, parseq):
        """Return the array containing the output results of the given
        parameter or sequence."""
        return getattr(self.results, parseq.name)

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

    def extract_method_doc(self):
        """Return the documentation string of the method to be tested."""
        if getattr(self.method, '__doc__', None):
            return self.method.__doc__
        else:
            model = type(self.model)
            for group_name in model._METHOD_GROUPS:
                for function_ in getattr(model, group_name, ()):
                    if function_.__name__ == self.method.__name__:
                        return function_.__doc__

    def extract_print_parameters_and_sequences(self):
        """Return a list of all parameter and sequences of the model.

        Note that all parameters and sequences without the common `values`
        attribute are omitted.
        """
        parseqs = []
        for subparseqs in itertools.chain(self.model.parameters,
                                          self.model.sequences):
            for parseq in subparseqs:
                if str(type(parseq)).split("'")[1] in self.doc:
                    if hasattr(parseq, 'values'):
                        parseqs.append(parseq)
        return tuple(parseqs)

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


class _Open(object):

    def __init__(self, path, mode, *args, **kwargs):
        # all positional and keyword arguments are ignored.
        self.path = path.replace(os.sep, '/')
        self.mode = mode
        self.texts = []
        self.entered = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exception, message, traceback_):
        self.close()

    def write(self, text):
        """Replaces the `write` method of file objects."""
        self.texts.append(text)

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


class Open(object):
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
    ...         file_.write('\\n')
    ...         file_.write('third line\\n')
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

    Class |Open| is rather restricted at the moment.  More functionalities
    will be added later...
    """
    def __init__(self):
        self.open = builtins.open

    def __enter__(self):
        builtins.open = _Open
        return self

    def __exit__(self, exception, message, traceback_):
        builtins.open = self.open


def solve_exception_doctest_issue(module):
    """Insert the string `hydpy.core.exceptiontools.` into the
    docstrings of the given module related to exceptions defined
    in module |exceptiontools|."""
    _replace(module)
    try:
        for member in vars(module).values():
            _replace(member)
            try:
                for submember in vars(member).values():
                    submember = getattr(submember, '__func__', submember)
                    _replace(submember)
            except (TypeError, KeyError):
                pass
    except TypeError:
        pass


def _replace(obj):
    try:
        doc = obj.__doc__
        for key, value in vars(exceptiontools).items():
            if inspect.isclass(value) and issubclass(value, BaseException):
                doc = doc.replace(
                    '    ' + key,
                    '    hydpy.core.exceptiontools.' + key)
                doc = doc.replace(
                    '\n' + key,
                    '\nhydpy.core.exceptiontools.' + key)
        obj.__doc__ = doc
    except BaseException:
        pass


class TestIO(object):
    """Prepare an environment for testing IO functionalities.

    ToDo: explain the handling of .coverage files

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
            try:
                if file.startswith('.coverage'):
                    shutil.move(file, os.path.join(self._path, file))
            except BaseException:
                pass
            try:
                if ((file != '__init__.py') and
                        (self._clear_all or
                         (self._clear_own and (file not in self._olds)))):
                    if os.path.exists(file):
                        if os.path.isfile(file):
                            os.remove(file)
                        else:
                            shutil.rmtree(file)
            except BaseException:
                pass
        os.chdir(self._path)

    @classmethod
    def clear(cls):
        """Remove all files from the `iotesting` folder."""
        with cls(clear_all=True):
            pass


def make_abc_testable(abstract: type) -> type:
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
    ...     Date(testdate)
    Traceback (most recent call last):
    ...
    ValueError: For `Date` instances, the microsecond must be `0`.  \
For the given `datetime` object, it is `999` instead.
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


autodoctools.autodoc_module()
