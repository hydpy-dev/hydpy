# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import os
import sys
import shutil
import copy
import time
import psutil
import datetime
import warnings
import collections
# ...from HydPy
from . import pub
from . import timetools
from . import filetools
from . import devicetools
from . import selectiontools
from . import magictools

import cython 

warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

class HydPy(object):
    """HydPy for single processing."""
    
    # A counter for the number of HydPy instances.
    nmb_instances = 0

    def __init__(self, projectname):

        if pub.print_progress:
            print('HydPy initialization started at', time.strftime('%X'))

        # Increment and check number of HydPy instances.
        HydPy.nmb_instances += 1
        if HydPy.nmb_instances > 1:
            warnings.warn('Currently %d instances of HydPy are initialized '
                          'within the same process.  It is strongly '
                          'recommended to initialize only one instance at a '
                          'time.  Consider deleting all instances and '
                          'initializing a new one, unless you are fully aware '
                          'in what manner HydPy is relying on some global '
                          'information stored in modules.' 
                          %HydPy.nmb_instances)
            
        
        
        # Store public information in a seperate module.
        pub.allowcoldstart = False
        pub.projectname = projectname
        pub.filemanager = filetools.MainManager()   
        pub.networkmanager = filetools.NetworkManager()
        pub.controlmanager = filetools.ControlManager()
        pub.sequencemanager = filetools.SequenceManager()
        pub.conditionmanager = filetools.ConditionManager()
        
    def preparenetwork(self):
        pub.selections = selectiontools.Selections()
        pub.selections += pub.networkmanager.load()
        self.updatedevices(pub.selections.complete)

    def initmodels(self):
        warn = magictools.simulationstep.warn
        magictools.simulationstep.warn = False
        try:
            for (name, element) in self.elements:
                element.initmodel()
                element.model.parameters.update()
                element.model.connect()
        finally:
            magictools.simulationstep.warn = warn

    def loadconditions(self, conditiondirectory=None, controldirectory=None,
                       projectdirectory=None, ):
        self._ioconditions(conditiondirectory,  controldirectory, 
                           projectdirectory, True)
        
    def saveconditions(self, conditiondirectory=None, controldirectory=None,
                       projectdirectory=None):
        self._ioconditions(conditiondirectory,  controldirectory, 
                           projectdirectory, False)

    def _ioconditions(self, conditiondirectory, controldirectory, 
                      projectdirectory, loadflag):
        _conditiondirectory = pub.conditionmanager._conditiondirectory
        _controldirectory = pub.controlmanager._controldirectory
        _projectdirectory = pub.conditionmanager._projectdirectory
        try:
            if projectdirectory:
                pub.conditionmanager.projectdirectory = projectdirectory
            if conditiondirectory:
                pub.conditionmanager.conditiondirectory = conditiondirectory
            if controldirectory:
                pub.controlmanager.controldirectory = controldirectory
            for (name, element) in self.elements:
                if loadflag:
                    element.model.sequences.loadconditions()
                else:
                    element.model.sequences.saveconditions()
        finally:
            pub.conditionmanager._conditiondirectory = _conditiondirectory
            pub.controlmanager._controldirectory = _controldirectory
            pub.conditionmanager._projectdirectory = _projectdirectory
            
    def trimconditions(self):
        for (name, element) in self.elements:
            element.model.sequences.trimconditions()        

    def connect(self):
        for (name, element) in self.elements:
            element.connect()


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
        for name in sels1.names:
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
                self._nextelement(element)
        if node not in self.deviceorder:
            self.deviceorder.append(node)
            for (name, element) in node.entries:
                self._nextelement(element)

    def _nextelement(self, element):
        for (name, node) in element.outlets:
            if ((node in self.nodes) and 
                (node not in self.deviceorder)):
                self._nextnode(node)
        if element not in self.deviceorder:
            self.deviceorder.append(element)
            for (name, node) in element.inlets:
                self._nextnode(node)
        
    @property
    def endnodes(self):
        endnodes = devicetools.Nodes()
        for (name, node) in self.nodes:
            for (name, element) in node.exits:
                if element in self.elements:
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
        for (name, element) in self.elements:
            if element.receivers:
                funcs.append(funcs.updatereceiver)
        for (name, node) in self.nodes:
            if node.routingmode != 'oldsim':
                funcs.append(node.reset)
        for device in self.deviceorder:
            if isinstance(device, devicetools.Element):
                funcs.append(device.model.doit)
        for (name, element) in self.elements:
            if element.senders:
                funcs.append(funcs.updatesenders)
        for (name, node) in self.nodes:
            if node.routingmode != 'oldsim':
                funcs.append(node._savedata_sim)
        return funcs
                   
    def doit(self):
        idx_start,idx_end = self.simindices
        self.openfiles(idx_start)
        funcorder = self.funcorder
        if pub.options._printprogress:
            maxcounter = int(float(idx_end-idx_start)/20.)
            print('|'+18*'-'+'|')
        else:
            maxcounter = idx_end
        counter = 0
        for idx in xrange(idx_start, idx_end):
            counter += 1
            if counter > maxcounter:
                print('*', end='')
                counter = 0
            for func in funcorder:
                func(idx)
        print('*')
        self.closefiles()
        