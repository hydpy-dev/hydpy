# -*- coding: utf-8 -*-
"""This module implements superordinate tools for handling a HydPy project.
"""
# import...
# ...from standard library
from typing import Dict, Union
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.core import abctools
from hydpy.core import autodoctools
from hydpy.core import devicetools
from hydpy.core import filetools
from hydpy.core import printtools
from hydpy.core import selectiontools


class HydPy(object):
    """Main class for managing HydPy projects."""

    def __init__(self, projectname=None):
        self._nodes = None
        self._elements = None
        self.deviceorder = None
        # Store public information in a separate module.
        if projectname is not None:
            pub.projectname = projectname
            pub.networkmanager = filetools.NetworkManager()
            pub.controlmanager = filetools.ControlManager()
            pub.sequencemanager = filetools.SequenceManager()
            pub.conditionmanager = filetools.ConditionManager()

    @property
    def nodes(self) -> devicetools.Nodes:
        nodes = self._nodes
        if nodes is None:
            raise RuntimeError(
                'The actual HydPy instance does not handle any '
                'nodes at the moment.')
        return self._nodes

    @nodes.setter
    def nodes(self, values):
        self._nodes = devicetools.Nodes(values)

    @nodes.deleter
    def nodes(self):
        self._nodes = None

    @property
    def elements(self) -> devicetools.Elements:
        elements = self._elements
        if elements is None:
            raise RuntimeError(
                'The actual HydPy instance does not handle any '
                'elements at the moment.')
        return self._elements

    @elements.setter
    def elements(self, values):
        self._elements = devicetools.Elements(values)

    @elements.deleter
    def elements(self):
        self._elements = None


    @printtools.print_progress
    def prepare_network(self):
        """Load all network files as |Selections| (stored in module |pub|)
        and assign the "complete" selection to the |HydPy| object."""
        pub.selections = selectiontools.Selections()
        pub.selections += pub.networkmanager.load_files()
        self.update_devices(pub.selections.complete)

    def init_models(self):
        """Call method |Element.init_model| of all |Element| objects
        currently handled by the |HydPy| object."""
        self.elements.init_models()

    def save_controls(self, controldir=None, projectdir=None,
                      parameterstep=None, simulationstep=None,
                      auxfiler=None):
        """Call method |Elements.save_controls| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_controls(controldir=controldir,
                                    projectdir=projectdir,
                                    parameterstep=parameterstep,
                                    simulationstep=simulationstep,
                                    auxfiler=auxfiler)

    def load_conditions(self, conditiondir=None, projectdir=None):
        """Call method |Elements.load_conditions| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.load_conditions(conditiondir=conditiondir,
                                      projectdir=projectdir)

    def save_conditions(self, conditiondir=None, projectdir=None,
                        controldir=None):
        """Call method |Elements.save_conditions| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_conditions(conditiondir=conditiondir,
                                      projectdir=projectdir,
                                      controldir=controldir)

    def trim_conditions(self):
        """Call method |Elements.trim_conditions| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.trim_conditions()

    def reset_conditions(self):
        """Call method |Elements.reset_conditions| of the |Elements| object
        currently handled by the |HydPy| object.

        Method |HydPy.reset_conditions| is the most convenient way to
        perform simulations repeatedly for the same period, each time
        starting from the same initial conditions, e.g. for parameter
        calibration. Each |StateSequence| and |LogSequence| object
        remembers the last assigned values and can reactivate them
        for the mentioned purpose.

        For demonstration, we perform a simulation for the `LahnH`
        example project spanning four days:

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO, print_values
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     hp.load_conditions()
        ...     hp.prepare_inputseries()
        ...     hp.prepare_simseries()
        ...     hp.load_inputseries()
        >>> hp.doit()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294

        Just repeating the simulation gives different results due to
        applying the final states of the first simulation run as the
        initial states of the second run:

        >>> hp.doit()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        26.21469, 25.063443, 24.238632, 23.317984

        Calling |HydPy.reset_conditions| first, allows repeating the
        first simulation run exactly multiple times:

        >>> hp.reset_conditions()
        >>> hp.doit()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294
        >>> hp.reset_conditions()
        >>> hp.doit()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294
        """
        self.elements.reset_conditions()

    @property
    def conditions(self) -> \
            Dict[str, Dict[str, Dict[str, Union[float, numpy.ndarray]]]]:
        """A nested dictionary containing the values of all condition
        sequences of all currently handled models.

        The primary  purpose of property |HydPy.conditions| is similar to
        the one of method |HydPy.reset_conditions|, to allow to perform
        repeated calculations starting from the same initial conditions.
        Nevertheless, |HydPy.conditions| is more flexible when it comes
        to handling multiple conditions, which can, for example, be useful
        for applying ensemble based assimilation algorithms.

        For demonstration, we perform simulations for the `LahnH` example
        project spanning the first three months of 1996.  We begin with a
        preparation run beginning on the first day of January and ending
        on the 20th day of February:

        >>> from hydpy.core.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO, print_values
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     pub.timegrids = '1996-01-01', '1996-04-01', '1d'
        ...     hp.prepare_network()
        ...     hp.init_models()
        ...     hp.load_conditions()
        ...     hp.prepare_modelseries()
        ...     hp.prepare_simseries()
        ...     hp.load_inputseries()
        >>> pub.timegrids.sim.lastdate = '1996-02-20'
        >>> hp.doit()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series[48:52])
        70.292046, 94.076568, 0.0, 0.0

        At the end of the preparation run, a snow layer is covering the
        Lahn catchment.  In the `lahn_1` subcatchment, this snow layer
        contains 19.5 mm of frozen water and 1.7 mm of liquid water:

        >>> lahn1_states = hp.elements.land_lahn_1.model.sequences.states
        >>> print_values([lahn1_states.sp.average_values()])
        19.543831
        >>> print_values([lahn1_states.wc.average_values()])
        1.745963

        Now we save the current conditions and perform the first simulation
        run from the 20th day of February until the end of March:

        >>> conditions = hp.conditions
        >>> hp.nodes.lahn_3.sequences.sim.series = 0.0
        >>> pub.timegrids.sim.firstdate = '1996-02-20'
        >>> pub.timegrids.sim.lastdate = '1996-04-01'
        >>> hp.doit()
        >>> first = hp.nodes.lahn_3.sequences.sim.series.copy()
        >>> print_values(first[48:52])
        0.0, 0.0, 84.986676, 63.834078

        To exactly repeat the last simulation run, we assign the
        memorised conditions to property |HydPy.conditions|:

        >>> hp.conditions = conditions
        >>> print_values([lahn1_states.sp.average_values()])
        19.543831
        >>> print_values([lahn1_states.wc.average_values()])
        1.745963

        All discharge values of the second simulation run are identical
        with the ones of the first simulation run:

        >>> hp.nodes.lahn_3.sequences.sim.series = 0.0
        >>> pub.timegrids.sim.firstdate = '1996-02-20'
        >>> pub.timegrids.sim.lastdate = '1996-04-01'
        >>> hp.doit()
        >>> second = hp.nodes.lahn_3.sequences.sim.series.copy()
        >>> print_values(second[48:52])
        0.0, 0.0, 84.986676, 63.834078
        >>> all(first == second)
        True

        We selected the snow period as an example due to potential
        problems with the limited water holding capacity of the
        snow layer, which depends on the ice content of the snow layer
        (|hland_states.SP|) and the relative water holding capacity
        (|hland_control.WHC|).  Due to this restriction, problems can
        occur.  To give an example, we set |hland_control.WHC| to zero
        temporarily, apply the memorised conditions, and finally reset
        the original values of |hland_control.WHC|:

        >>> for element in hp.elements.catchment:
        ...     element.whc = element.model.parameters.control.whc.values
        ...     element.model.parameters.control.whc = 0.0
        >>> with pub.options.warntrim(False):
        ...     hp.conditions = conditions
        >>> for element in hp.elements.catchment:
        ...     element.model.parameters.control.whc = element.whc

        Without any water holding capacity of the snow layer, its water
        content is zero despite the actual memorised value of 1.7 mm:

        >>> print_values([lahn1_states.sp.average_values()])
        19.543831
        >>> print_values([lahn1_states.wc.average_values()])
        0.0

        What is happening in the case of such conflicts partly depends
        on the implementation of the respective application model.
        For safety, we suggest setting option |Options.warntrim| to
        |True| before resetting conditions.
        """
        return self.elements.conditions

    @conditions.setter
    def conditions(self, conditions):
        self.elements.conditions = conditions

    def connect(self):
        """Call method |Elements.connect| of the |Elements| object currently
        handled by the |HydPy| object."""
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
        """Call method |Devices.open_files| of the |Nodes| and |Elements|
        objects currently handled by the |HydPy| object."""
        self.elements.open_files(idx=idx)
        self.nodes.open_files(idx=idx)

    def close_files(self):
        """Call method |Devices.close_files| of the |Nodes| and |Elements|
        objects currently handled by the |HydPy| object."""
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
            elif node.deploymode == 'obs':
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

    @printtools.print_progress
    def doit(self):
        """Perform a simulation run over the actual simulation time period
        defined by the |Timegrids| object stored in module |pub|."""
        idx_start, idx_end = self.simindices
        self.open_files(idx_start)
        methodorder = self.methodorder
        for idx in printtools.progressbar(range(idx_start, idx_end)):
            for func in methodorder:
                func(idx)
        self.close_files()

    def prepare_modelseries(self, ramflag=True):
        """Call method |Elements.prepare_allseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.prepare_allseries(ramflag=ramflag)

    def prepare_inputseries(self, ramflag=True):
        """Call method |Elements.prepare_inputseries| of the |Elements|
        object currently handled by the |HydPy| object."""
        self.elements.prepare_inputseries(ramflag=ramflag)

    def prepare_fluxseries(self, ramflag=True):
        """Call method |Elements.prepare_fluxseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.prepare_fluxseries(ramflag=ramflag)

    def prepare_stateseries(self, ramflag=True):
        """Call method |Elements.prepare_stateseries| of the |Elements|
        object currently handled by the |HydPy| object."""
        self.elements.prepare_stateseries(ramflag=ramflag)

    def prepare_nodeseries(self, ramflag=True):
        """Call method |Nodes.prepare_allseries| of the |Nodes| object
        currently handled by the |HydPy| object."""
        self.nodes.prepare_allseries(ramflag=ramflag)

    def prepare_simseries(self, ramflag=True):
        """Call method |Nodes.prepare_simseries| of the |Nodes| object
        currently handled by the |HydPy| object."""
        self.nodes.prepare_simseries(ramflag=ramflag)

    def prepare_obsseries(self, ramflag=True):
        """Call method |Nodes.prepare_obsseries| of the |Nodes| object
        currently handled by the |HydPy| object."""
        self.nodes.prepare_obsseries(ramflag=ramflag)

    def save_modelseries(self):
        """Call method |Elements.save_allseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_allseries()

    def save_inputseries(self):
        """Call method |Elements.save_inputseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_inputseries()

    def save_fluxseries(self):
        """Call method |Elements.save_fluxseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_fluxseries()

    def save_stateseries(self):
        """Call method |Elements.save_stateseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_stateseries()

    def save_nodeseries(self):
        """Call method |Nodes.save_allseries| of the |Nodes| object currently
        handled by the |HydPy| object."""
        self.nodes.save_allseries()

    def save_simseries(self):
        """Call method |Nodes.save_simseries| of the |Nodes| object currently
        handled by the |HydPy| object."""
        self.nodes.save_simseries()

    def save_obsseries(self):
        """Call method |Nodes.save_obsseries| of the |Nodes| object currently
        handled by the |HydPy| object."""
        self.nodes.save_obsseries()

    def load_modelseries(self):
        """Call method |Elements.load_allseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.load_allseries()

    def load_inputseries(self):
        """Call method |Elements.load_inputseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.load_inputseries()

    def load_fluxseries(self):
        """Call method |Elements.load_fluxseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.save_loadseries()

    def load_stateseries(self):
        """Call method |Elements.load_stateseries| of the |Elements| object
        currently handled by the |HydPy| object."""
        self.elements.load_stateseries()

    def load_nodeseries(self):
        """Call method |Nodes.load_allseries| of the |Nodes| object currently
        handled by the |HydPy| object."""
        self.nodes.load_allseries()

    def load_simseries(self):
        """Call method |Nodes.load_simseries| of the |Nodes| object currently
        handled by the |HydPy| object."""
        self.nodes.load_simseries()

    def load_obsseries(self):
        """Call method |Nodes.load_obsseries| of the |Nodes| object currently
        handled by the |HydPy| object."""
        self.nodes.load_obsseries()


autodoctools.autodoc_module()
