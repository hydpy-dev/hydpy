# -*- coding: utf-8 -*-
"""This module implements tools for making doctests more legible."""
# import...
# ...from standard library
from __future__ import division, print_function
import datetime
import itertools
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import hydpytools
from hydpy.core import devicetools
from hydpy.core import selectiontools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import sequencetools
from hydpy.core import autodoctools


class Array(object):
    """Assures that attributes are :class:`~numpy.ndarray` objects."""

    def __setattr__(self, name, value):
        object.__setattr__(self, name,  numpy.array(value))


class ArrayDescriptor(object):
    """Descriptor for handling values of :class:`Array` objects."""

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
    """Base class for :class:`IntegrationTest` and :class:`UnitTest`.

    This base class defines the printing of the test results primarily.
    How the tests shall be prepared and performed, is to be defined in
    its subclasses.
    """

    inits = ArrayDescriptor()
    """Stores arrays for setting the same values of parameters and/or
    sequences before each new experiment."""

    @property
    def nmb_rows(self):
        """Number of rows of the table."""
        return len(self.raw_first_col_strings)+1

    @property
    def nmb_cols(self):
        """Number of columns of the table."""
        nmb = 1
        for parseq in self.parseqs:
            nmb += max(parseq.length, 1)
        return nmb

    @property
    def raw_header_strings(self):
        """All raw strings for the tables header."""
        strings = [self.HEADER_OF_FIRST_COL]
        for parseq in self.parseqs:
            for idx in range(parseq.length-1):
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
                elif parseq.NDIM == 1:
                    if parseq.shape[0] > 0:
                        strings[-1].extend(objecttools.repr_(value)
                                           for value in array[idx])
                    else:
                        strings[-1].append('empty')
                else:
                    thing = ('sequence'
                             if isinstance(parseq, sequencetools.Sequence)
                             else 'parameter')
                    raise RuntimeError(
                        'An instance of class `Test` of module `testtools` '
                        'is requested to print the results of %s `%s`. '
                        'Unfortunately, for %d-dimensional sequences this '
                        'feature is not supported yet.'
                        % (thing, parseq.name, parseq.NDIM, parseq.shape))
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
            for idx in range(parseq.length-1):
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
        print(self._interleave(self.col_seperators,
                               self.raw_header_strings,
                               self.col_widths))
        print('-'*self.row_nmb_characters)
        for strings_in_line in self.raw_body_strings[idx1:idx2]:
            print(self._interleave(self.col_seperators,
                                   strings_in_line,
                                   self.col_widths))


class IntegrationTest(Test):
    """Defines model integration doctests.

    The functionality of :class:`Test` is easiest to understand by inspecting
    doctests like the ones of modules :mod:`~hydpy.models.llake_v1` or
    :mod:`~hydpy.models.arma_v1`.

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

    def __init__(self, element, seqs=None, inits=None):
        """Prepare the element and its nodes and put them into a HydPy object
        and make their sequences ready for use for integration testing."""
        del self.inits
        self.element = element
        self.elements = devicetools.Element.registeredelements()
        self.nodes = devicetools.Node.registerednodes()
        self.prepare_node_sequences()
        self.prepare_input_model_sequences()
        self.parseqs = seqs if seqs else self.extract_print_sequences()
        self.inits = inits
        self.model = element.model
        hydpytools.HydPy.nmb_instances = 0
        self.hp = hydpytools.HydPy()
        self.hp.updatedevices(selectiontools.Selection(
                                        'test', self.nodes, self.elements))

    def __call__(self):
        """Prepare and perform an integration test and print its results."""
        self.prepare_model()
        self.hp.doit()
        self.print_table()

    @property
    def raw_first_col_strings(self):
        """The raw date strings of the first column, except the header."""
        return [date.datetime.strftime(self.dateformat)
                for date in pub.timegrids.sim]

    def _getdateformat(self):
        """Format string for printing dates in the first column of the table.

        See :mod:`datetime` for the format strings allowed.
        """
        if self._dateformat is None:
            return timetools.Date._formatstrings['iso']
        else:
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
        for (name, node) in self.nodes:
            if not node.entries:
                node.routingmode = 'oldsim'
            sim = node.sequences.sim
            sim.ramflag = True
            sim._setarray(numpy.zeros(len(pub.timegrids.init), dtype=float))

    def prepare_input_model_sequences(self):
        """Configure the input sequences of the model in a manner that allows
        for applying their time series data in integration tests."""
        for (name, seq) in getattr(self.element.model.sequences, 'inputs', ()):
            seq.ramflag = True
            seq._setarray(numpy.zeros(len(pub.timegrids.init), dtype=float))

    def extract_print_sequences(self):
        """Return a list of all input, flux and state sequences of the model
        as well as the simulation sequences of all nodes."""
        seqs = []
        for subseqs in ('inputs', 'fluxes', 'states'):
            for (name, seq) in getattr(
                                    self.element.model.sequences, subseqs, ()):
                seqs.append(seq)
        for (name, node) in self.nodes:
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
        for (name, node) in self.nodes:
            if ((node in self.element.outlets) or
                    (node in self.element.senders)):
                node.sequences.sim[:] = 0.

    def reset_inits(self):
        """Set all initial conditions of all models."""
        for subname in ('states', 'logs'):
            for (name, element) in self.elements:
                for (name, seq) in getattr(element.model.sequences,
                                           subname, ()):
                    try:
                        seq(getattr(self.inits, name))
                    except AttributeError:
                        pass


class UnitTest(Test):

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
        self.reset_inits()
        for idx in range(self.nmb_examples):
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
        for parseq in self.parseqs:
            shape = [len(self.raw_first_col_strings)] + list(parseq.shape)
            type_ = getattr(parseq, 'TYPE', float)
            array = numpy.full(shape, numpy.nan, type_)
            setattr(self.results, parseq.name, array)

    def reset_inits(self):
        """Set all initial conditions."""
        for parseq in self.parseqs:
            parseq(getattr(self.inits, parseq.name))

    def extract_method_doc(self):
        """Return the documentation string of the method to be tested."""
        if getattr(self.method, '__doc__', None):
            return self.method.__doc__
        else:
            Model = type(self.model)
            for group_name in Model._METHOD_GROUPS:
                for function in getattr(Model, group_name, ()):
                    if function.__name__ == self.method.__name__:
                        return function.__doc__

    def extract_print_parameters_and_sequences(self):
        """Return a list of all input, flux and state sequences of the model
        as well as the simulation sequences of all nodes."""
        parseqs = []
        for (_, subparseqs) in itertools.chain(self.model.parameters,
                                               self.model.sequences):
            for (_, parseq) in subparseqs:
                if str(type(parseq)).split("'")[1] in self.doc:
                    parseqs.append(parseq)
        return tuple(parseqs)

    def _update_inputs(self, idx):
        """Update the actual values with the :attr:`~UnitTest.nexts` data of
        the given index."""
        for parseq in self.parseqs:
            if hasattr(self.nexts, parseq.name):
                parseq(getattr(self.nexts, parseq.name)[idx])

    def _update_outputs(self, idx):
        """Update the :attr:`~UnitTest.results` data with the actual values of
        the given index."""
        for parseq in self.parseqs:
            if hasattr(self.results, parseq.name):
                getattr(self.results, parseq.name)[idx] = parseq.values


autodoctools.autodoc_module()
