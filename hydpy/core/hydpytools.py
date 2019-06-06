# -*- coding: utf-8 -*-
"""This module implements superordinate tools for handling a HydPy project.
"""
# import...
# ...from standard library
from typing import Dict, Union
# ...from site-packages
import numpy
# ...from HydPy
import hydpy
from hydpy.core import abctools
from hydpy.core import devicetools
from hydpy.core import filetools
from hydpy.core import printtools
from hydpy.core import selectiontools


conditionstype = Dict[str, Dict[str, Dict[str, Union[float, numpy.ndarray]]]]


class HydPy(object):
    """Main class for managing HydPy projects."""

    def __init__(self, projectname=None):
        self._nodes = None
        self._elements = None
        self.deviceorder = None
        # Store public information in a separate module.
        if projectname is not None:
            hydpy.pub.projectname = projectname
            hydpy.pub.networkmanager = filetools.NetworkManager()
            hydpy.pub.controlmanager = filetools.ControlManager()
            hydpy.pub.sequencemanager = filetools.SequenceManager()
            hydpy.pub.conditionmanager = filetools.ConditionManager()

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

    def prepare_everything(self):
        """Convenience method to make the actual |HydPy| instance runable."""
        self.prepare_network()
        self.init_models()
        self.load_conditions()
        with hydpy.pub.options.warnmissingobsfile(False):
            self.prepare_nodeseries()
        self.prepare_modelseries()
        self.load_inputseries()

    @printtools.print_progress
    def prepare_network(self):
        """Load all network files as |Selections| (stored in module |pub|)
        and assign the "complete" selection to the |HydPy| object."""
        hydpy.pub.selections = selectiontools.Selections()
        hydpy.pub.selections += hydpy.pub.networkmanager.load_files()
        self.update_devices(hydpy.pub.selections.complete)

    def init_models(self):
        """Call method |Element.init_model| of all |Element| objects
        currently handled by the |HydPy| object."""
        self.elements.init_models()

    def save_controls(self, parameterstep=None, simulationstep=None,
                      auxfiler=None):
        """Call method |Elements.save_controls| of the |Elements| object
        currently handled by the |HydPy| object.

        We use the `LahnH` example project to demonstrate how to write
        a complete set parameter control files.  For convenience, we let
        function |prepare_full_example_2| prepare a fully functional
        |HydPy| object, handling seven |Element| objects controlling
        four |hland_v1| and three |hstream_v1| application models:

        >>> from hydpy.core.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        At first, there is only one control subfolder named "default",
        containing the seven control files used in the step above:

        >>> import os
        >>> with TestIO():
        ...     os.listdir('LahnH/control')
        ['default']

        Next, we use the |ControlManager| to create a new directory
        and dump all control file into it:

        >>> with TestIO():
        ...     pub.controlmanager.currentdir = 'newdir'
        ...     hp.save_controls()
        ...     sorted(os.listdir('LahnH/control'))
        ['default', 'newdir']

        We focus our examples on the (smaller) control files of
        application model |hstream_v1|.  The values of parameter
        |hstream_control.Lag| and |hstream_control.Damp| for the
        river channel connecting the outlets of subcatchment `lahn_1`
        and `lahn_2` are 0.583 days and 0.0, respectively:

        >>> model = hp.elements.stream_lahn_1_lahn_2.model
        >>> model.parameters.control
        lag(0.583)
        damp(0.0)

        The corresponding written control file defines the same values:

        >>> dir_ = 'LahnH/control/newdir/'
        >>> with TestIO():
        ...     with open(dir_ + 'stream_lahn_1_lahn_2.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1d')
        parameterstep('1d')
        <BLANKLINE>
        lag(0.583)
        damp(0.0)
        <BLANKLINE>

        Its name equals the element name and the time step information
        is taken for the |Timegrid| object available via |pub|:

        >>> pub.timegrids.stepsize
        Period('1d')

        Use the |Auxfiler| class To avoid redefining the same parameter
        values in multiple control files.  Here, we prepare an |Auxfiler|
        object which handles the two parameters of the model discussed
        above:

        >>> from hydpy import Auxfiler
        >>> aux = Auxfiler()
        >>> aux += 'hstream_v1'
        >>> aux.hstream_v1.stream = model.parameters.control.damp
        >>> aux.hstream_v1.stream = model.parameters.control.lag

        When passing the |Auxfiler| object to |HydPy.save_controls|,
        both parameters the control file of element `stream_lahn_1_lahn_2`
        do not define their values on their own, but reference the
        auxiliary file `stream.py` instead:

        >>> with TestIO():
        ...     pub.controlmanager.currentdir = 'newdir'
        ...     hp.save_controls(auxfiler=aux)
        ...     with open(dir_ + 'stream_lahn_1_lahn_2.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1d')
        parameterstep('1d')
        <BLANKLINE>
        lag(auxfile='stream')
        damp(auxfile='stream')
        <BLANKLINE>

        `stream.py` contains the actual value definitions:

        >>> with TestIO():
        ...     with open(dir_ + 'stream.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1d')
        parameterstep('1d')
        <BLANKLINE>
        damp(0.0)
        lag(0.583)
        <BLANKLINE>

        The |hstream_v1| model of element `stream_lahn_2_lahn_3` defines
        the same value for parameter |hstream_control.Damp| but a different
        one for parameter |hstream_control.Lag|.  Hence, only
        |hstream_control.Damp| can reference control file `stream.py`
        without distorting data:

        >>> with TestIO():
        ...     with open(dir_ + 'stream_lahn_2_lahn_3.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1d')
        parameterstep('1d')
        <BLANKLINE>
        lag(0.417)
        damp(auxfile='stream')
        <BLANKLINE>

        Another option is to pass alternative step size information.
        The `simulationstep` information, which is not really required
        in control files but useful for testing them, has no impact
        on the written data.  However, passing an alternative
        `parameterstep` information changes the written values of
        time dependent parameters both in the primary and the auxiliary
        control files, as to be expected:

        >>> with TestIO():
        ...     pub.controlmanager.currentdir = 'newdir'
        ...     hp.save_controls(
        ...         auxfiler=aux, parameterstep='2d', simulationstep='1h')
        ...     with open(dir_ + 'stream_lahn_1_lahn_2.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1h')
        parameterstep('2d')
        <BLANKLINE>
        lag(auxfile='stream')
        damp(auxfile='stream')
        <BLANKLINE>

        >>> with TestIO():
        ...     with open(dir_ + 'stream.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1h')
        parameterstep('2d')
        <BLANKLINE>
        damp(0.0)
        lag(0.2915)
        <BLANKLINE>

        >>> with TestIO():
        ...     with open(dir_ + 'stream_lahn_2_lahn_3.py') as controlfile:
        ...         print(controlfile.read())
        # -*- coding: utf-8 -*-
        <BLANKLINE>
        from hydpy.models.hstream_v1 import *
        <BLANKLINE>
        simulationstep('1h')
        parameterstep('2d')
        <BLANKLINE>
        lag(0.2085)
        damp(auxfile='stream')
        <BLANKLINE>
        """
        self.elements.save_controls(parameterstep=parameterstep,
                                    simulationstep=simulationstep,
                                    auxfiler=auxfiler)

    def load_conditions(self):
        """Load all currently relevant initial conditions.

        The following examples demonstrate both the functionality of
        method |HydPy.load_conditions| and |HydPy.save_conditions| based
        on the `LahnH` project, which we prepare via function
        |prepare_full_example_2|:

        >>> from hydpy.core.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        Our |HydPy| instance `hp` is completely ready for the first
        simulation run, meaning the required initial conditions have
        been loaded already.  First, we start a simulation run covering
        the whole initialisation period and inspect the resulting soil
        moisture values of |Element| `land_dill`, handled by sequence
        |hland_states.SM|:

        >>> hp.doit()
        >>> sm = hp.elements.land_dill.model.sequences.states.sm
        >>> sm
        sm(184.098541, 180.176461, 198.689343, 195.462014, 210.856923,
           208.319571, 220.881637, 218.898327, 229.022364, 227.431521,
           235.597338, 234.329294)

        By default, method |HydPy.load_conditions| always (re)loads the
        initial conditions from the directory with a name matching the
        start date of the simulation period, which we proof by also
        showing the related content of the respective condition file
        `land_dill.py`:

        >>> with TestIO():
        ...     hp.load_conditions()
        >>> sm
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)

        >>> path = 'LahnH/conditions/init_1996_01_01_00_00_00/land_dill.py'
        >>> with TestIO():
        ...     with open(path, 'r') as file_:
        ...         lines = file_.read().split('\\n')
        ...         print(lines[10])
        ...         print(lines[11])
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)

        Now we perform two sequential runs, covering the first and the
        second half of the initialisation period, respectively, and
        write, in both cases, the resulting final conditions to disk:

        >>> pub.timegrids.sim.lastdate = '1996-01-03'
        >>> hp.doit()
        >>> sm
        sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
           208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
           236.244147, 234.972621)
        >>> with TestIO():
        ...     hp.save_conditions()

        >>> pub.timegrids.sim.firstdate = '1996-01-03'
        >>> pub.timegrids.sim.lastdate = '1996-01-05'
        >>> hp.doit()
        >>> with TestIO():
        ...     hp.save_conditions()
        >>> sm
        sm(184.098541, 180.176461, 198.689343, 195.462014, 210.856923,
           208.319571, 220.881637, 218.898327, 229.022364, 227.431521,
           235.597338, 234.329294)

        Analogous to method |HydPy.load_conditions|, method
        |HydPy.save_conditions| writes the resulting conditions to a
        directory with a name matching the end date of the simulation
        period, which we proof by reloading the conditions related
        to the middle of the initialisation period and showing the
        related file content:

        >>> with TestIO():
        ...     hp.load_conditions()
        >>> sm
        sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
           208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
           236.244147, 234.972621)

        >>> path = 'LahnH/conditions/init_1996_01_03_00_00_00/land_dill.py'
        >>> with TestIO():
        ...     with open(path, 'r') as file_:
        ...         lines = file_.read().split('\\n')
        ...         print(lines[10])
        ...         print(lines[11])
        ...         print(lines[12])
        sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
           208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
           236.244147, 234.972621)

        You can define another directory by assigning another directory
        name to property |FileManager.currentdir| of the actual
        |ConditionManager| instance:

        >>> with TestIO():
        ...     pub.conditionmanager.currentdir = 'test'
        ...     hp.save_conditions()

        >>> path = 'LahnH/conditions/test/land_dill.py'
        >>> with TestIO():
        ...     with open(path, 'r') as file_:
        ...         lines = file_.read().split('\\n')
        ...         print(lines[10])
        ...         print(lines[11])
        ...         print(lines[12])
        sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
           208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
           236.244147, 234.972621)

        This change remains permanent until you undo it manually:

        >>> sm(0.0)
        >>> pub.timegrids.sim.firstdate = '1996-01-01'
        >>> with TestIO():
        ...     hp.load_conditions()
        >>> sm
        sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
           208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
           236.244147, 234.972621)

        >>> with TestIO():
        ...     del pub.conditionmanager.currentdir
        ...     hp.load_conditions()
        >>> sm
        sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
           222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)
        """
        self.elements.load_conditions()

    def save_conditions(self):
        """Save all currently relevant final conditions.

        See the documentation on method |HydPy.load_conditions| for
        further information.
        """
        self.elements.save_conditions()

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

        >>> from hydpy.core.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> hp.doit()
        >>> from hydpy import print_values
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
    def conditions(self) -> conditionstype:
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
        ...     hp.prepare_everything()
        >>> pub.timegrids.sim.lastdate = '1996-02-20'
        >>> hp.doit()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series[48:52])
        70.292046, 94.076568, nan, nan

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
        endnodes = self.endnodes
        if endnodes:
            self.deviceorder = []
            for node in endnodes:
                self._nextnode(node)
            self.deviceorder = self.deviceorder[::-1]
        else:
            self.deviceorder = list(self.elements)

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
        return (hydpy.pub.timegrids.init[hydpy.pub.timegrids.sim.firstdate],
                hydpy.pub.timegrids.init[hydpy.pub.timegrids.sim.lastdate])

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
        funcs = []
        for node in self.nodes:
            if node.deploymode == 'oldsim':
                funcs.append(node.sequences.fastaccess.load_simdata)
            elif node.deploymode == 'obs':
                funcs.append(node.sequences.fastaccess.load_obsdata)
        for node in self.nodes:
            if node.deploymode != 'oldsim':
                funcs.append(node.reset)
        for device in self.deviceorder:
            if isinstance(device, devicetools.Element):
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
                funcs.append(node.sequences.fastaccess.save_simdata)
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
