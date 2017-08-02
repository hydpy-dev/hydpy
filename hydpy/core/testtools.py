# -*- coding: utf-8 -*-
"""This module implements tools for making doctests more legible.

At the moment only class :class:`Test` is implemented.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import datetime
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import hydpytools
from hydpy.core import devicetools
from hydpy.core import selectiontools
from hydpy.core import objecttools
from hydpy.core import timetools


class _Inits(object):
    """Descriptor for handling initial values of :class:`Test` objects."""

    def __init__(self):
        self.inits = type('Inits', (), {})()

    def __set__(self, obj, values):
        self.__delete__(obj)
        if values is not None:
            for (key, value) in values:
                setattr(self.inits, key.name, value)

    def __get__(self, obj, type_=None):
        return self.inits

    def __delete__(self, obj):
        for name in list(vars(self.inits).keys()):
            delattr(self.inits, name)


class Test(object):
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

    _dateformat = None
    inits = _Inits()

    def __init__(self, element, seqs=None, inits=None):
        """Prepare the element and its nodes and put them into a HydPy object
        and make their sequences ready for use for integration testing."""
        self.element = element
        self.nodes = self.retrieve_nodes()
        self.prepare_input_node_sequences()
        self.prepare_input_model_sequences()
        if seqs is None:
            self.seqs = self.retrieve_print_sequences()
        else:
            self.seqs = seqs
        self.inits = inits
        self.model = element.model
        hydpytools.HydPy.nmb_instances = 0
        self.hp = hydpytools.HydPy()
        self.hp.updatedevices(selectiontools.Selection(
                                                'test', self.nodes, element))

    def retrieve_nodes(self):
        """Return all nodes connected to the actual element."""
        nodes = devicetools.Nodes()
        for connection in (self.element.inlets, self.element.outlets,
                           self.element.receivers, self.element.senders):
            nodes += connection.slaves
        return nodes

    def prepare_input_node_sequences(self):
        """Configure the simulations sequences of the input nodes in
        a manner that allows for applying their time series data in
        integration tests.
        """
        for (name, node) in self.nodes:
            if ((node in self.element.inlets) or
                    (node in self.element.receivers)):
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

    def retrieve_print_sequences(self):
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

    def __call__(self):
        """Prepare and perform an integration test and print its results."""
        self.prepare_model()
        self.hp.doit()
        self.table

    def prepare_model(self):
        """Derive the secondary parameter values, prepare all required time
        series and set the initial conditions.
        """
        self.model.parameters.update()
        self.element.prepare_fluxseries()
        self.element.prepare_stateseries()
        for (name, node) in self.nodes:
            if ((node in self.element.outlets) or
                    (node in self.element.senders)):
                node.sequences.sim[:] = 0.
        for subname in ('states', 'logs'):
            for (name, seq) in getattr(self.model.sequences, subname, ()):
                try:
                    seq(getattr(self.inits, name))
                except AttributeError:
                    raise AttributeError(
                        'For %s sequence `%s`, no initial values have been '
                        'defined for integration testing.'
                        % (subname[:-1], seq.name))

    @property
    def nmb_rows(self):
        """Number of rows of the table."""
        return len(pub.timegrids.sim)+1

    @property
    def nmb_cols(self):
        """Number of columns of the table."""
        nmb = 1
        for seq in self.seqs:
            nmb += seq.length
        return nmb

    @property
    def raw_header_strings(self):
        """All raw strings for the tables header."""
        strings = ['date']
        for seq in self.seqs:
            for idx in range(seq.length-1):
                strings.append('')
            if seq.name == 'sim':
                strings.append(seq.subseqs.node.name)
            else:
                strings.append(seq.name)
        return strings

    @property
    def raw_body_strings(self):
        """All raw strings for the tables body."""
        strings = []
        for (idx, date) in enumerate(pub.timegrids.sim):
            strings.append([date.datetime.strftime(self.dateformat)])
            for seq in self.seqs:
                if seq.NDIM == 0:
                    strings[-1].append(objecttools.repr_(seq.series[idx]))
                elif seq.NDIM == 1:
                    strings[-1].extend(objecttools.repr_(value)
                                       for value in seq.series[idx])
                else:
                    raise RuntimeError(
                        'An instance of class `Test` of module `testtools` '
                        'is requested to print the results of sequence `%s`. '
                        'Unfortunately, for %d-dimensional sequences this '
                        'feature is not supported yet.'
                        % (seq.name, seq.NDIM, seq.shape))
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
        for seq in self.seqs:
            seps.append(' | ')
            for idx in range(seq.length-1):
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

    @property
    def table(self):
        """Print out of the complete table."""
        print(self._interleave(self.col_seperators,
                               self.raw_header_strings,
                               self.col_widths))
        print('-'*self.row_nmb_characters)
        for strings_in_line in self.raw_body_strings:
            print(self._interleave(self.col_seperators,
                                   strings_in_line,
                                   self.col_widths))

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
