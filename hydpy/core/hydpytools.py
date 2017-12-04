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
from hydpy.core import objecttools
from hydpy.core import filetools
from hydpy.core import devicetools
from hydpy.core import selectiontools
from hydpy.core import autodoctools
from hydpy.core import magictools


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
    def preparenetwork(self):
        pub.selections = selectiontools.Selections()
        pub.selections += pub.networkmanager.load()
        self.updatedevices(pub.selections.complete)

    @magictools.printprogress
    def initmodels(self):
        warn = pub.options.warnsimulationstep
        pub.options.warnsimulationstep = False
        try:
            for (name, element) in magictools.progressbar(self.elements):
                try:
                    element.initmodel()
                except IOError as exc:
                    temp = 'While trying to load the control file'
                    if ((temp in str(exc)) and
                            pub.options.warnmissingcontrolfile):
                        warnings.warn('No model could be initialized for '
                                      'element `%s`' % name)
                        self.model = None
                    else:
                        objecttools.augmentexcmessage(
                            'While trying to initialize the model of '
                            'element `%s`' % name)
                else:
                    element.model.parameters.update()
        finally:
            pub.options.warnsimulationstep = warn

    @magictools.printprogress
    def savecontrols(self, controldirectory=None, projectdirectory=None,
                     parameterstep=None, simulationstep=None):
        _controldirectory = pub.controlmanager._controldirectory
        _projectdirectory = pub.controlmanager._projectdirectory
        try:
            if controldirectory:
                pub.controlmanager.controldirectory = controldirectory
            if projectdirectory:
                pub.controlmanager.projectdirectory = projectdirectory
            for (name, element) in magictools.progressbar(self.elements):
                element.model.parameters.savecontrols(parameterstep,
                                                      simulationstep)
        finally:
            pub.controlmanager._controldirectory = _controldirectory
            pub.controlmanager._projectdirectory = _projectdirectory

    @magictools.printprogress
    def loadconditions(self, conditiondirectory=None, controldirectory=None,
                       projectdirectory=None):
        self._ioconditions(conditiondirectory,  controldirectory,
                           projectdirectory, True)

    @magictools.printprogress
    def saveconditions(self, conditiondirectory=None, controldirectory=None,
                       projectdirectory=None):
        self._ioconditions(conditiondirectory,  controldirectory,
                           projectdirectory, False)

    def _ioconditions(self, conditiondirectory, controldirectory,
                      projectdirectory, loadflag):
        if loadflag:
            _conditiondirectory = pub.conditionmanager._loaddirectory
        else:
            _conditiondirectory = pub.conditionmanager._savedirectory
        _controldirectory = pub.controlmanager._controldirectory
        _projectdirectory = pub.conditionmanager._projectdirectory
        try:
            if projectdirectory:
                pub.conditionmanager.projectdirectory = projectdirectory
            if conditiondirectory:
                if loadflag:
                    pub.conditionmanager.loaddirectory = conditiondirectory
                else:
                    pub.conditionmanager.savedirectory = conditiondirectory
            if controldirectory:
                pub.controlmanager.controldirectory = controldirectory
            for (name, element) in magictools.progressbar(self.elements):
                if loadflag:
                    element.model.sequences.loadconditions()
                else:
                    element.model.sequences.saveconditions()
        finally:
            if loadflag:
                pub.conditionmanager._loaddirectory = _conditiondirectory
            else:
                pub.conditionmanager._savedirectory = _conditiondirectory
            pub.controlmanager._controldirectory = _controldirectory
            pub.conditionmanager._projectdirectory = _projectdirectory

    def trimconditions(self):
        for (name, element) in self.elements:
            element.model.sequences.trimconditions()

    def resetconditions(self):
        for (name, element) in self.elements:
            element.model.sequences.reset()

    def connect(self):
        for (name, element) in self.elements:
            element.connect()
            element.model.parameters.update()

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
        for (name, node) in self.endnodes:
            sel = complete.copy(name).select_upstream(node)
            sels1 += sel
            sels2 += sel.copy(name)
        for (name1, sel1) in sels1:
            for (name2, sel2) in sels2:
                if name1 != name2:
                    sel1 -= sel2
        for name in list(sels1.names):
            if not sels1[name].elements:
                del sels1[name]
        return sels1

    def _updatedeviceorder(self):
        self.deviceorder = []
        for (name, node) in self.endnodes:
            self._nextnode(node)
        self.deviceorder = self.deviceorder[::-1]

    def _nextnode(self, node):
        for (name, element) in node.exits:
            if ((element in self.elements) and
                    (element not in self.deviceorder)):
                if node not in element.receivers:
                    self._nextelement(element)
        if (node in self.nodes) and (node not in self.deviceorder):
            self.deviceorder.append(node)
            for (name, element) in node.entries:
                self._nextelement(element)

    def _nextelement(self, element):
        for (name, node) in element.outlets:
            if ((node in self.nodes) and
                    (node not in self.deviceorder)):
                self._nextnode(node)
        if (element in self.elements) and (element not in self.deviceorder):
            self.deviceorder.append(element)
            for (name, node) in element.inlets:
                self._nextnode(node)

    @property
    def endnodes(self):
        endnodes = devicetools.Nodes()
        for (name, node) in self.nodes:
            for (name, element) in node.exits:
                if ((element in self.elements) and
                        (node not in element.receivers)):
                    break
            else:
                endnodes += node
        return endnodes

    @property
    def variables(self):
        variables = set([])
        for (name, node) in self.nodes:
            variables.add(node.variable)
        return sorted(variables)

    @property
    def simindices(self):
        return (pub.timegrids.init[pub.timegrids.sim.firstdate],
                pub.timegrids.init[pub.timegrids.sim.lastdate])

    def openfiles(self, idx=0):
        for (name, element) in self.elements:
            element.model.sequences.openfiles(idx)
        for (name, node) in self.nodes:
            node.sequences.openfiles(idx)

    def closefiles(self):
        for (name, element) in self.elements:
            element.model.sequences.closefiles()
        for (name, node) in self.nodes:
            node.sequences.closefiles()

    def updatedevices(self, selection=None):
        if selection is not None:
            self.nodes = selection.nodes
            self.elements = selection.elements
        self._updatedeviceorder()

    @property
    def funcorder(self):
        funcs = []
        for (name, node) in self.nodes:
            if node.routingmode == 'oldsim':
                funcs.append(node._loaddata_sim)
            elif node.sequences.obs.use_ext:
                funcs.append(node._loaddata_obs)
        for (name, node) in self.nodes:
            if node.routingmode != 'oldsim':
                funcs.append(node.reset)
        for device in self.deviceorder:
            if isinstance(device, devicetools.Element):
                funcs.append(device.model.doit)
        for (name, element) in self.elements:
            if element.senders:
                funcs.append(element.model.update_senders)
        for (name, element) in self.elements:
            if element.receivers:
                funcs.append(element.model.update_receivers)
        for (name, node) in self.nodes:
            if node.routingmode != 'oldsim':
                funcs.append(node._savedata_sim)
        return funcs

    @magictools.printprogress
    def doit(self):
        idx_start, idx_end = self.simindices
        self.openfiles(idx_start)
        funcorder = self.funcorder
        for idx in magictools.progressbar(range(idx_start, idx_end)):
            for func in funcorder:
                func(idx)
        self.closefiles()

    @magictools.printprogress
    def prepare_modelseries(self, ramflag=True):
        for (name, element) in magictools.progressbar(self.elements):
            element.prepare_allseries(ramflag)

    @magictools.printprogress
    def prepare_inputseries(self, ramflag=True):
        for (name, element) in magictools.progressbar(self.elements):
            element.prepare_inputseries(ramflag)

    @magictools.printprogress
    def prepare_fluxseries(self, ramflag=True):
        for (name, element) in magictools.progressbar(self.elements):
            element.prepare_fluxseries(ramflag)

    @magictools.printprogress
    def prepare_stateseries(self, ramflag=True):
        for (name, element) in magictools.progressbar(self.elements):
            element.prepare_stateseries(ramflag)

    @magictools.printprogress
    def prepare_nodeseries(self, ramflag=True):
        self.prepare_simseries(ramflag)
        self.prepare_obsseries(ramflag)

    @magictools.printprogress
    def prepare_simseries(self, ramflag=True):
        for (name, node) in magictools.progressbar(self.nodes):
            node.prepare_simseries(ramflag)

    @magictools.printprogress
    def prepare_obsseries(self, ramflag=True):
        for (name, node) in magictools.progressbar(self.nodes):
            node.prepare_obsseries(ramflag)

    @magictools.printprogress
    def save_modelseries(self):
        self.save_inputseries()
        self.save_fluxseries()
        self.save_stateseries()

    @magictools.printprogress
    def save_inputseries(self):
        self._save_modelseries('inputs', pub.sequencemanager.inputoverwrite)

    @magictools.printprogress
    def save_fluxseries(self):
        self._save_modelseries('fluxes', pub.sequencemanager.outputoverwrite)

    @magictools.printprogress
    def save_stateseries(self):
        self._save_modelseries('states', pub.sequencemanager.outputoverwrite)

    def _save_modelseries(self, name_subseqs, overwrite):
        for (name1, element) in magictools.progressbar(self.elements):
            sequences = element.model.sequences
            subseqs = getattr(sequences, name_subseqs, ())
            for (name2, seq) in subseqs:
                if seq.memoryflag:
                    if overwrite or not os.path.exists(seq.filepath_ext):
                        seq.save_ext()
                    else:
                        warnings.warn('Due to the argument `overwrite` beeing '
                                      '`False` it is not allowed to overwrite '
                                      'the already existing file `%s`.'
                                      % seq.filepath_ext)

    @magictools.printprogress
    def save_nodeseries(self):
        self.save_simseries()
        self.save_obsseries()

    @magictools.printprogress
    def save_simseries(self, ramflag=True):
        self._save_nodeseries('sim', pub.sequencemanager.simoverwrite)

    @magictools.printprogress
    def save_obsseries(self, ramflag=True):
        self._save_nodeseries('obs', pub.sequencemanager.obsoverwrite)

    def _save_nodeseries(self, seqname, overwrite):
        for (name, node) in magictools.progressbar(self.nodes):
            seq = getattr(node.sequences, seqname)
            if seq.memoryflag:
                if overwrite or not os.path.exists(seq.filepath_ext):
                    seq.save_ext()
                else:
                    warnings.warn('Due to the argument `overwrite` beeing '
                                  '`False` it is not allowed to overwrite '
                                  'the already existing file `%s`.'
                                  % seq.filepath_ext)


autodoctools.autodoc_module()
