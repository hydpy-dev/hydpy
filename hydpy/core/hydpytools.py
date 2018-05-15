# -*- coding: utf-8 -*-
"""This module implements superordinate tools for handling a HydPy project.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import warnings
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import filetools
from hydpy.core import magictools
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
        self.nodes = None
        self.elements = None
        self.deviceorder = None
        # Store public information in a separate module.
        if projectname is not None:
            pub.projectname = projectname
            pub.networkmanager = filetools.NetworkManager()
            pub.controlmanager = filetools.ControlManager()
            pub.sequencemanager = filetools.SequenceManager()
            pub.conditionmanager = filetools.ConditionManager()

    @magictools.print_progress
    def prepare_network(self):
        """Load all network files as |Selections| (stored in module |pub|)
        and assign the "complete" selection to the |HydPy| object."""
        pub.selections = selectiontools.Selections()
        pub.selections += pub.networkmanager.load_files()
        self.update_devices(pub.selections.complete)

    def init_models(self):
        """Call method :func:`~hydpy.core.devicetools.Element.init_model` of
        all |Element| objects currently handled by the |HydPy| object."""
        self.elements.init_models()

    def save_controls(self, controldir=None, projectdir=None,
                      parameterstep=None, simulationstep=None,
                      auxfiler=None):
        """Call method :func:`~hydpy.core.devicetools.Element.save_controls`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.save_controls(controldir=controldir,
                                    projectdir=projectdir,
                                    parameterstep=parameterstep,
                                    simulationstep=simulationstep,
                                    auxfiler=auxfiler)

    def load_conditions(self, conditiondir=None, projectdir=None):
        """Call method :func:`~hydpy.core.devicetools.Element.load_conditions`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.load_conditions(conditiondir=conditiondir,
                                      projectdir=projectdir)

    def save_conditions(self, conditiondir=None, projectdir=None,
                        controldir=None):
        """Call method :func:`~hydpy.core.devicetools.Element.save_conditions`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.save_conditions(conditiondir=conditiondir,
                                      projectdir=projectdir,
                                      controldir=controldir)

    def trim_conditions(self):
        """Call method :func:`~hydpy.core.devicetools.Element.trim_conditions`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.trim_conditions()

    def reset_conditions(self):
        """Call method :func:`~hydpy.core.devicetools.Element.reset_conditions`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.reset_conditions()

    def connect(self):
        """Call method :func:`~hydpy.core.devicetools.Element.connect`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.connect()

    @property
    def networkproperties(self):
        """Print out some properties of the network defined by the |Node| and
        |Element| objects currently handled by the |HydPy| object."""
        print('Number of nodes: %d' % len(self.nodes))
        print('Number of elements: %d' % len(self.elements))
        print('Number of end nodes: %d' % len(self.endnodes))
        print('Number of distinct networks: %d' % len(self.numberofnetworks))
        print('Applied node variables: %s' % ', '.join(self.variables))

    @property
    def numberofnetworks(self):
        """The number of distinct networks defined by the|Node| and
        |Element| objects currently handled by the |HydPy| object."""
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
        """|Nodes| object containing all |Node| objects currently handled by
        the |HydPy| object which define a downstream end point of a network."""
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
        """Sorted list of strings summarizing all variables handled by the
        |Node| objects"""
        variables = set([])
        for node in self.nodes:
            variables.add(node.variable)
        return sorted(variables)

    @property
    def simindices(self):
        """Tuple containing the start and end index of the simulation period
        regarding the initialization period defined by the |Timegrids| object
        stored in module |pub|."""
        return (pub.timegrids.init[pub.timegrids.sim.firstdate],
                pub.timegrids.init[pub.timegrids.sim.lastdate])

    def open_files(self, idx=0):
        """Call method :func:`~hydpy.core.devicetools.Devcies.open_files`
        of the |Nodes| and |Elements| objects currently handled by the
        |HydPy| object."""
        self.elements.open_files(idx=idx)
        self.nodes.open_files(idx=idx)

    def close_files(self):
        """Call method :func:`~hydpy.core.devicetools.Devcies.close_files`
        of the |Nodes| and |Elements| objects currently handled by the
        |HydPy| object."""
        self.elements.close_files()
        self.nodes.close_files()

    def update_devices(self, selection=None):
        """Determines the order, in which the |Node| and |Element| objects
        currently handled by the |HydPy| objects need to be processed during
        a simulation time step.  Optionally, a |Selection| object for defining
        new |Node| and |Element| objects can be passed."""
        if selection is not None:
            self.nodes = selection.nodes
            self.elements = selection.elements
        self._update_deviceorder()

    @property
    def methodorder(self):
        """A list containing all methods of all |Node| and |Element| objects
        that need to be processed during a simulation time step in the
        order they must be called."""
        # Some private methods of other classes are called.  The wrong usage
        # of these method could cause segmentation faults in Cython mode.
        # Hence it seems to be a good idea to make them "invisible" for
        # novice users via declaring them as private:
        # pylint: disable=protected-access
        funcs = []
        for node in self.nodes:
            if node.deploymode == 'oldsim':
                funcs.append(node._load_data_sim)
            elif node.sequences.obs.use_ext:
                funcs.append(node._load_data_obs)
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
            funcs.append(element.model.save_data)
        for node in self.nodes:
            if node.deploymode != 'oldsim':
                funcs.append(node._save_data_sim)
        return funcs

    @magictools.print_progress
    def doit(self):
        """Perform a simulation run over the actual simulation time period
        defined by the |Timegrids| object stored in module |pub|."""
        idx_start, idx_end = self.simindices
        self.open_files(idx_start)
        methodorder = self.methodorder
        for idx in magictools.progressbar(range(idx_start, idx_end)):
            for func in methodorder:
                func(idx)
        self.close_files()

    def prepare_modelseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Element.prepare_allseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.prepare_allseries(ramflag=ramflag)

    def prepare_inputseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Element.prepare_inputseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.prepare_inputseries(ramflag=ramflag)

    def prepare_fluxseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Element.prepare_fluxseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.prepare_fluxseries(ramflag=ramflag)

    def prepare_stateseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Element.prepare_stateseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.prepare_stateseries(ramflag=ramflag)

    def prepare_nodeseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Node.prepare_allseries`
        of the |Nodes| object currently handled by the |HydPy| object."""
        self.nodes.prepare_allseries(ramflag=ramflag)

    def prepare_simseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Node.prepare_simseries`
        of the |Nodes| object currently handled by the |HydPy| object."""
        self.nodes.prepare_simseries(ramflag=ramflag)

    def prepare_obsseries(self, ramflag=True):
        """Call method
        :func:`~hydpy.core.devicetools.Node.prepare_obsseries`
        of the |Nodes| object currently handled by the |HydPy| object."""
        self.nodes.prepare_obsseries(ramflag=ramflag)

    def save_modelseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Element.save_allseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.save_allseries()

    def save_inputseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Element.save_inputseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.save_inputseries()

    def save_fluxseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Element.save_fluxseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.save_fluxseries()

    def save_stateseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Element.save_stateseries`
        of the |Elements| object currently handled by the |HydPy| object."""
        self.elements.save_stateseries()

    def save_nodeseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Node.save_allseries`
        of the |Nodes| object currently handled by the |HydPy| object."""
        self.nodes.save_allseries()

    def save_simseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Node.save_simseries`
        of the |Nodes| object currently handled by the |HydPy| object."""
        self.nodes.save_simseries()

    def save_obsseries(self):
        """Call method
        :func:`~hydpy.core.devicetools.Node.save_obsseries`
        of the |Nodes| object currently handled by the |HydPy| object."""
        self.nodes.save_obsseries()


autodoctools.autodoc_module()
