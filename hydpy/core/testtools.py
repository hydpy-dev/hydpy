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


class Test(object):
    """Defines model integration doctests.

    The functionality of :class:`Test` is easiest to understand by inspecting
    doctests like the one of module :mod:`~hydpy.models.llake_v1`.

    Note that all condition sequences (state and logging sequences) are
    initialized in accordance with the values are given in the `inits`
    dictionary.  The values of the simulation sequences of outlet and
    sender nodes are always set to zero before each test run.  All other
    parameter and sequence values can be changed between different test
    runs.
    """
    _dateformat = None

    def __init__(self, element, seqs=None, inits=None):
        nodes = devicetools.Nodes()
        for connection in (element.inlets, element.outlets,
                           element.receivers, element.senders):
            nodes += connection.slaves
        for (name, node) in nodes:
            if (node in element.inlets) or (node in element.receivers):
                node.routingmode = 'oldsim'
            sim = node.sequences.sim
            sim.ramflag = True
            sim._setarray(numpy.zeros(len(pub.timegrids.init), dtype=float))
        for (name, seq) in getattr(element.model.sequences, 'inputs', ()):
            seq.ramflag = True
            seq._setarray(numpy.zeros(len(pub.timegrids.init), dtype=float))
        if seqs is None:
            seqs = []
            for subseqs in ('inputs', 'fluxes', 'states'):
                for (name, seq) in getattr(element.model.sequences,
                                           subseqs, ()):
                    seqs.append(seq)
            for (name, node) in nodes:
                seqs.append(node.sequences.sim)
        element.prepare_fluxseries()
        element.prepare_stateseries()
        self.element = element
        self.nodes = nodes
        self.seqs = seqs
        self.inits = {} if inits is None else inits
        self.model = element.model
        hydpytools.HydPy.nmb_instances = 0
        self.hp = hydpytools.HydPy()
        self.hp.updatedevices(selectiontools.Selection('test', nodes, element))

    def __call__(self):
        self._prepare_model()
        self.hp.doit()
        self._print_results()

    def _prepare_model(self):
        self.model.parameters.update()
        for (name, node) in self.nodes:
            if ((node in self.element.outlets) or
                    (node in self.element.senders)):
                node.sequences.sim[:] = 0.
        for (name, seq) in getattr(self.model.sequences, 'states', ()):
            seq(self.inits[name])
        for (name, seq) in getattr(self.model.sequences, 'logs', ()):
            seq(self.inits[name])

    def _print_results(self):
        strings = [['date'] + [seq.subseqs.node.name if
                               seq.name == 'sim' else seq.name
                               for seq in self.seqs]]
        lengths = numpy.zeros((len(pub.timegrids.sim)+1, len(self.seqs)+1),
                              dtype=int)
        lengths[0, :] = [len(string) for string in strings[0]]
        for (idx, date) in enumerate(pub.timegrids.sim):
            strings.append([date.datetime.strftime(self.dateformat)])
            for seq in self.seqs:
                if seq.NDIM == 0:
                    strings[-1].append(objecttools.repr_(seq.series[idx]))
                elif seq.NDIM == 1 and seq.shape == (1,):
                    strings[-1].append(objecttools.repr_(seq.series[idx, 0]))
                else:
                    raise RuntimeError(
                        'An instance of class `Test` of module `testtools` '
                        'is requested to print the results of sequence `%s`. '
                        'Unfortunately, for %d-dimensional sequences with '
                        'shape `%s` this feature is not supported yet.'
                        % (seq.name, seq.NDIM, seq.shape))
            lengths[idx+1, :] = [len(string) for string in strings[-1]]
        maxlengths = numpy.max(lengths, axis=0)
        for (idx, linestrings) in enumerate(strings):
            print('|',
                  ' | '.join(string.rjust(maxlengths[jdx]) for (jdx, string)
                             in enumerate(linestrings)),
                  '|')
            if idx == 0:
                print('-'*(numpy.sum(maxlengths)+3*(len(self.seqs))+4))

    def _getdateformat(self):
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
