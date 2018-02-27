# -*- coding: utf-8 -*-
"""This module implements superordinate tools for handling a HydPy project.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import os
import warnings
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import filetools
from hydpy.core import magictools
from hydpy.core import objecttools
from hydpy.core import selectiontools


class HydPy(object):
    """Main class for managing HydPy projects."""

    # A counter for the number of HydPy instances.
    nmb_instances = 0

    def __init__(self, projectname=None):

        # Increment and check number of HydPy instances.
        HydPy.nmb_instances += 1
        if HydPy.nmb_instances > 1:
            warnings.warn('Currently %d instances of HydPy are initialized '
                          'within the same process.  It is strongly '
                          'recommended to initialize only one instance at a '
                          'time.  Consider deleting all instances and '
                          'initializing a new one, unless you are fully aware '
                          'in what manner HydPy is relying on some global '
                          'information stored in module `pub`.'
                          % HydPy.nmb_instances)

        # Store public information in a seperate module.
        if projectname is not None:
            pub.projectname = projectname
            pub.filemanager = filetools.MainManager()
            pub.networkmanager = filetools.NetworkManager()
            pub.controlmanager = filetools.ControlManager()
            pub.sequencemanager = filetools.SequenceManager()
            pub.conditionmanager = filetools.ConditionManager()

    @magictools.printprogress
    def prepare_network(self):
        pub.selections = selectiontools.Selections()
        pub.selections += pub.networkmanager.load()
        self.update_devices(pub.selections.complete)

    def init_models(self):
        self.elements.init_models()

    def save_controls(self, controldirectory=None, projectdirectory=None,
                      parameterstep=None, simulationstep=None,
                      auxfiler=None):
        self.elements.save_controls(controldirectory=controldirectory,
                                    projectdirectory=projectdirectory,
                                    parameterstep=parameterstep,
                                    simulationstep=simulationstep,
                                    auxfiler=auxfiler)

    def load_conditions(self, conditiondirectory=None, controldirectory=None,
                        projectdirectory=None):
        self.elements.load_conditions(conditiondirectory=conditiondirectory,
                                      controldirectory=controldirectory,
                                      projectdirectory=projectdirectory)

    def save_conditions(self, conditiondirectory=None, controldirectory=None,
                        projectdirectory=None):
        self.elements.save_conditions(conditiondirectory=conditiondirectory,
                                      controldirectory=controldirectory,
                                      projectdirectory=projectdirectory)

    def trim_conditions(self):
        self.elements.trim_conditions()

    def reset_conditions(self):
        self.elements.reset()

    def connect(self):
        self.elements.connect()

    @property
    def network_properties(self):
        print('Number of nodes: %d' % len(self.nodes))
        print('Number of elements: %d' % len(self.elements))
        print('Number of end nodes: %d' % len(self.endnodes))
        print('Number of distinct networks: %d' % len(self.distinct_networks))
        print('Applied node variables: %s' % ', '.join(self.variables))

    @property
    def distinct_networks(self):
        sels1 = selectiontools.Selections()
        sels2 = selectiontools.Selections()
        complete = selectiontools.Selection('complete',
                                            self.nodes, self.elements)
        for node in self.endnodes:
            sel = complete.copy(node.name).select_upstream(node)
            sels1 += sel
            sels2 += sel.copy(node.name)
        for sel1 in sels1:
            for sel2 in sels2:
                if sel1.name != sel2.name:
                    sel1 -= sel2
        for name in list(sels1.names):
            if not sels1[name].elements:
                del sels1[name]
        return sels1

    def _update_deviceorder(self):
        self.deviceorder = []
        for node in self.endnodes:
            self._nextnode(node)
        self.deviceorder = self.deviceorder[::-1]

    def _nextnode(self, node):
        for element in node.exits:
            if ((element in self.elements) and
                    (element not in self.deviceorder)):
                if node not in element.receivers:
                    self._nextelement(element)
        if (node in self.nodes) and (node not in self.deviceorder):
            self.deviceorder.append(node)
            for element in node.entries:
                self._nextelement(element)

    def _nextelement(self, element):
        for node in element.outlets:
            if ((node in self.nodes) and
                    (node not in self.deviceorder)):
                self._nextnode(node)
        if (element in self.elements) and (element not in self.deviceorder):
            self.deviceorder.append(element)
            for node in element.inlets:
                self._nextnode(node)

    @property
    def endnodes(self):
        endnodes = devicetools.Nodes()
        for node in self.nodes:
            for element in node.exits:
                if ((element in self.elements) and
                        (node not in element.receivers)):
                    break
            else:
                endnodes += node
        return endnodes

    @property
    def variables(self):
        variables = set([])
        for node in self.nodes:
            variables.add(node.variable)
        return sorted(variables)

    @property
    def simindices(self):
        return (pub.timegrids.init[pub.timegrids.sim.firstdate],
                pub.timegrids.init[pub.timegrids.sim.lastdate])

    def open_files(self, idx=0):
        self.elements.open_files(idx=idx)
        self.nodes.open_files(idx=idx)

    def close_files(self):
        self.elements.close_files()
        self.nodes.close_files()

    def update_devices(self, selection=None):
        if selection is not None:
            self.nodes = selection.nodes
            self.elements = selection.elements
        self._update_deviceorder()

    @property
    def funcorder(self):
        funcs = []
        for node in self.nodes:
            if node.deploymode == 'oldsim':
                funcs.append(node._loaddata_sim)
            elif node.sequences.obs.use_ext:
                funcs.append(node._loaddata_obs)
        for node in self.nodes:
            if node.deploymode != 'oldsim':
                funcs.append(node.reset)
        for device in self.deviceorder:
            if isinstance(device, abctools.ElementABC):
                funcs.append(device.model.doit)
        for element in self.elements:
            if element.senders:
                funcs.append(element.model.update_senders)
        for element in self.elements:
            if element.receivers:
                funcs.append(element.model.update_receivers)
        for element in self.elements:
            funcs.append(element.model.savedata)
        for node in self.nodes:
            if node.deploymode != 'oldsim':
                funcs.append(node._savedata_sim)
        return funcs

    @magictools.printprogress
    def doit(self):
        idx_start, idx_end = self.simindices
        self.open_files(idx_start)
        funcorder = self.funcorder
        for idx in magictools.progressbar(range(idx_start, idx_end)):
            for func in funcorder:
                func(idx)
        self.close_files()

    def prepare_modelseries(self, ramflag=True):
        self.elements.prepare_allseries(ramflag=ramflag)

    def prepare_inputseries(self, ramflag=True):
        self.elements.prepare_inputseries(ramflag=ramflag)

    def prepare_fluxseries(self, ramflag=True):
        self.elements.prepare_fluxseries(ramflag=ramflag)

    def prepare_stateseries(self, ramflag=True):
        self.elements.prepare_stateseries(ramflag=ramflag)

    def prepare_nodeseries(self, ramflag=True):
        self.nodes.prepare_allseries(ramflag=ramflag)

    def prepare_simseries(self, ramflag=True):
        self.nodes.prepare_simseries(ramflag=ramflag)

    def prepare_obsseries(self, ramflag=True):
        self.nodes.prepare_obsseries(ramflag=ramflag)

    def save_modelseries(self):
        self.elements.save_allseries()

    def save_inputseries(self):
        self.elements.save_inputseries()

    def save_fluxseries(self):
        self.elements.save_fluxseries()

    def save_stateseries(self):
        self.elements.save_stateseries()

    def save_nodeseries(self):
        self.nodes.save_allseries()

    def save_simseries(self, ramflag=True):
        self.nodes.save_simseries()

    def save_obsseries(self, ramflag=True):
        self.nodes.save_obsseries()


autodoctools.autodoc_module()
