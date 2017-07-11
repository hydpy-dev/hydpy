# -*- coding: utf-8 -*-
"""This module implements tools for making doctests more legible.

At the moment only class :class:`Test` is implemented.
"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import hydpytools
from hydpy.core import devicetools
from hydpy.core import selectiontools
from hydpy.core import objecttools


class Test(object):
    """Defines model integration doctests.

    The functionality of :class:`Test` is easiest to understand by inspecting
    doctests like the one of module :mod:`~hydpy.models.llake_v1`.

    Note that all condition sequences (state and logging sequences) are
    initialized with zero values before each test run, if no alternative
    values are given in the `inits` dictionary.  The values of the
    simulation sequences of outlet and sender nodes are always set to
    zero before each test run.  All other parameter and sequence values
    can be changed between different test runs.
    """
    def __init__(self, element, seqs, inits=None):
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
        element.prepare_allseries()
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
            seq.old = self.inits.get(name, 0.)
        for (name, seq) in getattr(self.model.sequences, 'logs', ()):
            seq.value = self.inits.get(name, 0.)

    def _print_results(self):
        strings = [[seq.subseqs.node.name if seq.name == 'sim' else seq.name
                    for seq in self.seqs]]
        lengths = numpy.zeros((len(pub.timegrids.sim)+1, len(self.seqs)),
                              dtype=int)
        lengths[0, :] = [len(string) for string in strings[0]]
        for (idx, date) in enumerate(pub.timegrids.sim):
            strings.append([objecttools.repr_(seq.series[idx])
                            for seq in self.seqs])
            lengths[idx+1, :] = [len(string) for string in strings[-1]]
        maxlengths = numpy.max(lengths, axis=0)
        for (idx, linestrings) in enumerate(strings):
            print('|',
                  ' | '.join(string.rjust(maxlengths[jdx]) for (jdx, string)
                             in enumerate(linestrings)),
                  '|')
            if idx == 0:
                print('-'*(numpy.sum(maxlengths)+3*(len(self.seqs)-1)+4))
