# -*- coding: utf-8 -*-
"""This module implements the main features for managing *HydPy* projects."""
# import...
# ...from standard library
import itertools
import warnings
from typing import *
# ...from site-packages
import numpy
import networkx
# ...from HydPy
import hydpy
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import objecttools
from hydpy.core import printtools
from hydpy.core import selectiontools
from hydpy.core import timetools
from hydpy.core import typingtools
if TYPE_CHECKING:
    from hydpy.core import auxfiletools
    from hydpy.core.logtools import Logger
    from hydpy.core.sequencetools import Sequence


ConditionsType = Dict[str, Dict[str, Dict[str, Union[float, numpy.ndarray]]]]


class HydPy:
    """The main class for managing *HydPy* projects.

    In typical *HydPy* projects, one prepares a single instance of class
    |HydPy|.  This instance, which we name "hp" throughout this
    documentation instead of "hydpy" to avoid a naming collision with
    the `hydpy` site-package, provides many convenience methods to perform
    task like reading time series data or starting simulation runs.
    Additionally, it serves as a root to access most of the details of
    a *HydPy* project, allowing for more granular control over the
    framework features.

    We elaborate these short explanations by using the `LahnH` example
    project.  Calling function |prepare_full_example_1| copies the
    complete example project `LahnH` into the `iotesting` directory of
    the *HydPy* site-package (alternatively, you can copy the `LahnH`
    example project, which can be found in subpackage `data`,  into a
    working directory of your choice):

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    At first, the |HydPy| instance needs to know the name of the relevant
    project, which is identical with the name of the project's root
    directory.  Pass `LahnH` to the constructor of class |HydPy|:

    >>> from hydpy import HydPy
    >>> hp = HydPy('LahnH')

    So far, our |HydPy| instance does not know any project configurations
    except its name.  Most of this information would be available via
    properties |HydPy.nodes| and |HydPy.elements|, but if we try to
    access them, we get the following error responses:

    >>> hp.nodes
    Traceback (most recent call last):
    ...
    AttributeError: The actual HydPy instance does not handle any nodes \
at the moment.

    >>> hp.elements
    Traceback (most recent call last):
    ...
    AttributeError: The actual HydPy instance does not handle any elements \
at the moment.

    One now could continue rather quickly by calling method
    |HydPy.prepare_everything|, which would make our |HydPy| instance
    ready for its first simulation run in one go.  However, we prefer
    to continue step by step by calling the more specific preparation
    methods, which offers more flexibility.

    First, the |HydPy| instance needs to know the relevant |Node| and
    |Element| objects.  Method |HydPy.prepare_network| reads this
    information from so-called "network files".  The |Node| and |Element|
    objects connect automatically and thereby define the topology or
    the network structure of the project (see the documentation on class
    |NetworkManager| and module |devicetools| for more detailed  explanations):

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     hp.prepare_network()

    (Using the "with" statement in combination with class |TestIO|
    makes sure we are reading the network files from a subdirectory
    of the `iotesting` directory.  Here and in the following, you
    must omit such "with blocks" in case you copied the `LahnH` example
    project into your current working directory.)

    Now, our |HydPy| instance offers access to all |Node| objects
    defined within the `LahnH` example project, which are grouped
    by a |Nodes| object:

    >>> hp.nodes
    Nodes("dill", "lahn_1", "lahn_2", "lahn_3")

    Taking the node `dill` as an example, we can dive into the details
    and, for example, search for those elements which node `dill` is
    connected to (it receives water from element `land_dill` and passes
    it to element `stream_dill_lahn_2`), or inspect its simulated
    discharge value handled by a |Sim| sequence object (so far, zero):

    >>> hp.nodes.dill.entries
    Elements("land_dill")

    >>> hp.nodes.dill.exits
    Elements("stream_dill_lahn_2")

    >>> hp.nodes.dill.sequences.sim
    sim(0.0)

    All |Node| objects are ready to be used.  The same is only partly
    true for the |Element| objects, which are also accessible (via a
    |Elements| instance) and properly connected to the |Node| objects
    but do not handle workable |Model| objects, which is required to
    perform any simulation run:

    >>> hp.elements
    Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3",
             "stream_dill_lahn_2", "stream_lahn_1_lahn_2",
             "stream_lahn_2_lahn_3")

    >>> hp.elements.stream_dill_lahn_2
    Element("stream_dill_lahn_2",
            inlets="dill",
            outlets="lahn_2",
            keywords="river")

    >>> hp.elements.land_dill.model
    Traceback (most recent call last):
    ...
    AttributeError: The model object of element `land_dill` has been \
requested but not been prepared so far.

    Hence, we need to call method |HydPy.prepare_models|, which
    instructs all |Element| objects to read the relevant parameter
    control files and prepare their |Model| objects.  Note that
    the individual |Element| object does not know the relevant model
    type beforehand; both the information on the model type and
    the parameter settings is encoded in individual control files,
    making it easy to exchange individual models later (the
    documentation on method |Elements.prepare_models| of class
    |Elements| is a good starting point for a deeper understanding
    on configuring *HydPy* projects via control files):

    >>> with TestIO():
    ...     hp.prepare_models()
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to initialise the model object of element \
`land_dill`, the following error occurred: The initialisation period has \
not been defined via attribute `timegrids` of module `pub` yet but might \
be required to prepare the model properly.

    Oops, something went wrong.  We forgot to define the simulation
    period, which might be relevant for some time-dependent
    configurations.  We discuss some examples of such configurations
    below but now use this little accident to discuss the typical pattern
    of *HydPy* error messages.  First, we usually try to add some
    additional "spatial" information (in this case: the name of the related
    |Element| object).  Second, we try to explain in which program context
    an error occurs.  This context is already available in much
    more detail in the so-called "stack trace" (the middle part of the
    printed error response we do not show).  Stack trace descriptions
    are great for programmers but hard to read for others, which
    is why we often add "While trying to..." explanations to our error
    messages.  In our example, one can see that the error occurred
    while trying to initialise the |Model| object of element `land_dill`,
    which is quite evident in our example but could be less evident
    in more complex *HydPy* applications.

    The last sentence of the error message tells us that we need
    to define the attribute `timegrids` of module `pub`.  `pub`
    stands for "public", meaning module `pub` handles all (or at
    least most of) the globally available configuration data.
    One example is that module `pub` handles a |Timegrids| instance
    defining both the initialisation and the simulation period,
    which can be done by the following assignment (see the
    documentation on class |Timegrid| and on class |Timegrids| for
    further information):

    >>> from hydpy import pub
    >>> pub.timegrids = '1996-01-01', '1996-01-05', '1d'

    Now method |HydPy.prepare_models| does not complain anymore and
    adds an instance of the |hland_v1| application model to element
    `land_dill`, to which we set an additional reference to shorten
    the following examples:

    >>> with TestIO():
    ...     hp.prepare_models()

    >>> model = hp.elements.land_dill.model
    >>> model.name
    'hland_v1'

    All control parameter values, defined in the corresponding control
    file, are correctly set.  As an example, we show the values of
    control parameter |hland_control.IcMax|, which in this case
    defines different values for hydrological response units of
    type |hland_constants.FIELD| (1.0 mm) and of type
    |hland_constants.FOREST| (1.5 mm):

    >>> model.parameters.control.icmax
    icmax(field=1.0, forest=1.5)

    The values of the derived parameters, which need to be calculated
    before starting a simulation run based on the control parameters
    and eventually based on some other settings (e.g. the initialisation
    period) are also ready.  Here we show the value of the derived
    parameter  |hland_derived.RelLandArea|, representing the relative
    area of "land" units (1.0 means there is no "water" unit at all):

    >>> model.parameters.derived.rellandarea
    rellandarea(1.0)

    Note that we define all class names in "CamelCase" letters
    (which is a Python convention) and, whenever useful, name
    the related objects identically but in lower case letters.
    We hope that eases finding the relevant parts of the online
    documentation when in trouble with a particular object.  Three
    examples we already encountered are the |Timegrids| instance
    `timegrids` of module `pub`, the |Nodes| instance `nodes` of
    class `HydPy`, and the |hland_derived.RelLandArea| instance
    `rellandarea` of application model |hland_v1|:

    >>> from hydpy import classname
    >>> classname(pub.timegrids)
    'Timegrids'

    >>> classname(hp.nodes)
    'Nodes'

    >>> classname(model.parameters.derived.rellandarea)
    'RelLandArea'

    As shown above, all |Parameter| objects of the model of element
    `land_dill` are ready to be used. However, all sequences (which
    handle the time variable properties) contain |numpy| |numpy.nan|
    values, which we use to indicate missing data.  We show this
    for the 0-dimensional input temperature sequence |hland_inputs.T|,
    for the 1-dimensional soil moisture state sequence |hland_states.SM|,
    and for the 0-dimensional discharge flux sequence |hland_fluxes.QT|:

    >>> model.sequences.inputs.t
    t(nan)

    >>> model.sequences.states.sm
    sm(nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan, nan)

    >>> model.sequences.fluxes.qt
    qt(nan)

    There are some other sequence types (see the documentation on
    module |sequencetools| for more details) but |InputSequence|,
    |FluxSequence|, and |StateSequence| are the most common ones
    (besides the |NodeSequence| subtypes  |Obs| and especially |Sim|).

    |StateSequence| objects describe many aspects of the current state
    of a model (or, e.g., of a catchment).  Each simulation run requires
    proper initial states, which we call initial conditions in the
    following (also covering memory aspects represented by |LogSequence|
    objects).  We load all necessary initial conditions by calling the
    method |HydPy.load_conditions| (see the documentation on method
    |HydPy.load_conditions| for further details):

    >>> with TestIO():
    ...     hp.load_conditions()

    Now, the states of our model are also ready to be used.  However,
    one should note that state sequence |hland_states.SM| knows only
    the current soil moisture states for the twelve hydrological
    response units of element `land_dill` (more specifically, we
    loaded the soil moisture values related to the start date of the
    initialisation period, which is the first of January at zero
    o'clock).  By default and for reasons of memory storage efficiency,
    sequences generally handle the currently relevant values only
    instead of complete time series:

    >>> model.sequences.inputs.t
    t(nan)

    >>> model.sequences.states.sm
    sm(185.13164, 181.18755, 199.80432, 196.55888, 212.04018, 209.48859,
       222.12115, 220.12671, 230.30756, 228.70779, 236.91943, 235.64427)

    >>> model.sequences.fluxes.qt
    qt(nan)

    For states like |hland_states.SM|, we need to know the values at
    the beginning of the simulation period only.  All following values
    are calculated subsequentially during the simulation run.  However,
    this is different for input sequences like |hland_inputs.T|.
    Time variable properties like the air temperature are external
    forcings. Hence they must be available over the whole simulation
    period apriori.  Such complete time series can be made available
    via property |IOSequence.series| of class |IOSequence|, which
    has not happened for any sequence so far:

    >>> model.sequences.inputs.t.series
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `t` of element `land_dill` is not \
requested to make any internal data available.

    Before loading time series data, we need to reserve the required
    memory storage.  We do this for all sequences at ones (not only
    the |ModelSequence| objects but also the |NodeSequence| objects
    as the |Sim| instance handled by node `dill`) through calling
    method |HydPy.prepare_allseries|:

    >>> hp.prepare_allseries()

    Now property |IOSequence.series| returns an |InfoArray| object,
    which is a slight modification of the widely applied |numpy|
    |numpy.ndarray|.  The first axis (or the only axis) corresponds
    to the number of days of the initialisation period (a *HydPy*
    convention).  For the 1-dimensional soil moisture state sequence
    |hland_states.SM|, the second axis corresponds to the number of
    hydrological response units (a |hland| convention):

    >>> model.sequences.inputs.t.series
    InfoArray([ nan,  nan,  nan,  nan])

    >>> model.sequences.states.sm.series
    InfoArray([[ nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,
                 nan,  nan],
               [ nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,
                 nan,  nan],
               [ nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,
                 nan,  nan],
               [ nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,  nan,
                 nan,  nan]])

    >>> model.sequences.fluxes.qt.series
    InfoArray([ nan,  nan,  nan,  nan])

    >>> hp.nodes.dill.sequences.sim.series
    InfoArray([ nan,  nan,  nan,  nan])

    So far, each time series array is empty.  The `LahnH` example
    project provides time series files for the input sequences only,
    which is the minimum requirement for starting a simulation run.
    We use method |HydPy.load_inputseries| to load this data:

    >>> with TestIO():
    ...     hp.load_inputseries()

    >>> from hydpy import round_
    >>> round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    Finally, we can perform the simulation run by calling the method
    |HydPy.simulate|:

    >>> hp.simulate()

    The time series arrays of all sequences now contain calculated
    values --- except those of input sequence |hland_inputs.T|, of course
    (for state sequence |hland_states.SM|, we show the time series
    of the first hydrological response unit only):

    >>> round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> round_(model.sequences.fluxes.qt.series)
    1.454998, 1.103529, 0.886541, 0.749761

    >>> round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 7.103614, 6.00763

    By comparison, you see that the lastly calculated (or read) time
    series value is the actual one for each |Sequence| object.  This
    mechanism allows, for example, to write the final states of soil
    moisture sequence |hland_states.SM| and use them as initial
    conditions later, even if its complete time series were not available:

    >>> model.sequences.inputs.t
    t(-5.968849)

    >>> model.sequences.states.sm
    sm(184.098541, 180.176461, 198.689343, 195.462014, 210.856923,
       208.319571, 220.881637, 218.898327, 229.022364, 227.431521,
       235.597338, 234.329294)

    >>> model.sequences.fluxes.qt
    qt(0.749761)

    >>> hp.nodes.dill.sequences.sim
    sim(6.00763)

    In many applications, the simulated time series is the result
    we are interested in.  Hence we close our explanations with some
    detailed examples on this topic that also cover the potential
    problem of limited rapid access storage availability.

    By default, the *HydPy* framework does not overwrite already
    existing time series files.  You can change such settings via
    the |SequenceManager| object available in module |pub| (module
    |pub| also handles |ControlManager| and |ConditionManager| objects
    for settings related to reading and writing control files and
    condition files).  We change the default behaviour by setting
    the `generaloverwrite` attribute to |True| and write all the time
    series (not only those of the flux and states sequences but
    also those of the input sequences) by calling method
    |HydPy.save_allseries|:

    >>> pub.sequencemanager.generaloverwrite = True
    >>> with TestIO():
    ...     hp.save_allseries()

    Next, we show how the reading of time series works.  We first set the
    time series values of all considered sequences to zero for this purpose:

    >>> model.sequences.inputs.t.series = 0.0
    >>> model.sequences.states.sm.series = 0.0
    >>> model.sequences.inputs.t.series = 0.0
    >>> hp.nodes.dill.sequences.sim.series = 0.

    Now we can reload the time series of all relevant sequences.
    However, doing so would result in a warning due to incomplete
    data (for example, of the observation data handled by the
    |Obs| sequence objects, which is not available in the `LahnH`
    example project).  To circumvent this problem, we disable
    the |Options.checkseries| option, which is one of the
    public options handled by the instance of class |Options|
    available as another attribute of module |pub|.  We again
    use a "with block", making sure the option is changed only
    temporarily while loading the time series (this time not by
    executing method |HydPy.load_allseries| but by the more
    specific methods |HydPy.load_inputseries|, |HydPy.load_fluxseries|,
    |HydPy.load_stateseries|, and |HydPy.load_simseries|):

    >>> with TestIO(), pub.options.checkseries(False):
    ...     hp.load_inputseries()
    ...     hp.load_fluxseries()
    ...     hp.load_stateseries()
    ...     hp.load_simseries()

    The read time series data equals the previously written one:

    >>> round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> round_(model.sequences.fluxes.qt.series)
    1.454998, 1.103529, 0.886541, 0.749761

    >>> round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 7.103614, 6.00763

    We mentioned the possibility for more granular control of
    *HydPy* by using the different objects handled by the |HydPy|
    object instead of using its convenience methods.
    Here is an elaborate example showing how to (re)load the states
    of an arbitrary simulation time step, which might be relevant
    for more complex workflows implementing data assimilation techniques:

    >>> model.sequences.states.load_data(1)
    >>> model.sequences.states.sm
    sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
       208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
       236.244147, 234.972621)

    Using the node sequence |Sim| as an example, we also show the
    inverse functionality of changing time series values:

    >>> hp.nodes.dill.sequences.sim = 0.0
    >>> hp.nodes.dill.sequences.save_data(2)
    >>> round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 0.0, 6.00763

    >>> hp.nodes.dill.sequences.load_data(1)
    >>> hp.nodes.dill.sequences.sim
    sim(8.842278)

    In the examples above, we keep all data in rapid access memory,
    which can be problematic when handling long time series in huge
    *HydPy* projects.  When in trouble, first try to prepare only those
    time series which are strictly required (very often, it is
    sufficient to call |HydPy.prepare_inputseries|,
    |HydPy.load_inputseries|, and |HydPy.prepare_simseries| only).
    If this does not work in your project, you can choose to handle
    some time series on disk instead, which unavoidably increases
    computation times immensely.  To prepare the necessary space on
    disk, assign |False| to the `ramflag` argument of method
    |HydPy.prepare_allseries| or its more specific counterparts:

    >>> with TestIO():
    ...     hp.prepare_inputseries(ramflag=False)
    ...     hp.prepare_stateseries(ramflag=False)
    ...     hp.prepare_fluxseries(ramflag=False)
    ...     hp.prepare_simseries(ramflag=False)
    ...     hp.prepare_obsseries(ramflag=False)

    By doing so, you lose the previously available time series information:

    >>> with TestIO():
    ...     round_(model.sequences.inputs.t.series)
    nan, nan, nan, nan

    >>> with TestIO():
    ...     round_(model.sequences.states.sm.series[:, 0])
    nan, nan, nan, nan

    >>> with TestIO():
    ...     round_(model.sequences.fluxes.qt.series)
    nan, nan, nan, nan

    >>> with TestIO():
    ...     round_(hp.nodes.dill.sequences.sim.series)
    nan, nan, nan, nan

    (Re)Loading the initial conditions and the input time series
    and (re)performing the simulation run results, as to be expected,
    in the same simulation results:

    >>> with TestIO():
    ...     hp.load_conditions()
    ...     hp.load_inputseries()
    ...     hp.simulate()

    >>> with TestIO():
    ...     round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> with TestIO():
    ...     round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> with TestIO():
    ...     round_(model.sequences.fluxes.qt.series)
    1.454998, 1.103529, 0.886541, 0.749761

    >>> with TestIO():
    ...     round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 7.103614, 6.00763

    Writing and reading from external time series files also works
    in combination with handling internal time series data on disk:

    >>> with TestIO():
    ...     hp.save_inputseries()
    ...     hp.save_stateseries()
    ...     hp.save_fluxseries()
    ...     hp.save_simseries()
    ...     hp.save_obsseries()

    >>> with TestIO():
    ...     model.sequences.inputs.t.series = 0.0
    ...     model.sequences.states.sm.series = 0.0
    ...     model.sequences.fluxes.qt.series = 0.0
    ...     hp.nodes.dill.sequences.sim.series = 0.0

    >>> with TestIO():
    ...     with pub.options.checkseries(False):
    ...         hp.load_allseries()

    >>> with TestIO():
    ...     round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> with TestIO():
    ...     round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> with TestIO():
    ...     round_(model.sequences.fluxes.qt.series)
    1.454998, 1.103529, 0.886541, 0.749761

    >>> with TestIO():
    ...     round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 7.103614, 6.00763

    Besides computation times, it usually makes no difference whether
    one handles internal time series data in RAM or on disk.  However,
    there are some subtle differences when one dives into the details.
    Above, we have shown the possibility to (re)load the states of
    arbitrary simulation time steps when working in RAM.  The same is
    possible when working on the hard disk, but one has to call
    |IOSequences.open_files| first to prepare the necessary file
    object and pass the relevant time step index to this
    method instead to method |ModelIOSequences.load_data|:

    >>> with TestIO():
    ...     model.sequences.states.open_files(1)
    ...     model.sequences.states.load_data(-999)
    ...     model.sequences.states.close_files()
    >>> model.sequences.states.sm
    sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
       208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
       236.244147, 234.972621)

    For the sake of completeness, we also repeat the |Sim| based example:

    >>> hp.nodes.dill.sequences.sim = 0.0
    >>> with TestIO():
    ...     hp.nodes.dill.sequences.open_files(2)
    ...     hp.nodes.dill.sequences.save_data(-999)
    ...     hp.nodes.dill.sequences.close_files()
    ...     round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 0.0, 6.00763

    >>> with TestIO():
    ...     hp.nodes.dill.sequences.open_files(1)
    ...     hp.nodes.dill.sequences.load_data(-999)
    ...     hp.nodes.dill.sequences.close_files()
    >>> hp.nodes.dill.sequences.sim
    sim(8.842278)
    """

    _nodes: Optional[devicetools.Nodes]
    _elements: Optional[devicetools.Elements]
    deviceorder: List[devicetools.Device]
    loggers: Dict[str, 'Logger']

    def __init__(self, projectname: Optional[str] = None):
        self._nodes = None
        self._elements = None
        self.loggers = {}
        self.deviceorder = []
        if projectname is not None:
            hydpy.pub.projectname = projectname
            hydpy.pub.networkmanager = filetools.NetworkManager()
            hydpy.pub.controlmanager = filetools.ControlManager()
            hydpy.pub.sequencemanager = filetools.SequenceManager()
            hydpy.pub.conditionmanager = filetools.ConditionManager()

    @property
    def nodes(self) -> devicetools.Nodes:
        """The currently handled |Node| objects.

        You are allowed to get, set and delete the currently handled nodes:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> hp.nodes
        Nodes("dill", "lahn_1", "lahn_2", "lahn_3")

        >>> del hp.nodes
        >>> hp.nodes
        Traceback (most recent call last):
        ...
        AttributeError: The actual HydPy instance does not handle any nodes \
at the moment.

        >>> hp.nodes = 'dill', 'lahn_1'
        >>> hp.nodes
        Nodes("dill", "lahn_1")

        However, note that doing so might result in erroneous networks
        and that you, even in case of correctness, must most likely call
        method |HydPy.update_devices| before performing the next
        simulation run.
        """
        nodes = self._nodes
        if nodes is None:
            raise AttributeError(
                'The actual HydPy instance does not handle any '
                'nodes at the moment.')
        return nodes

    @nodes.setter
    def nodes(self, values):
        self._nodes = devicetools.Nodes(values).copy()

    @nodes.deleter
    def nodes(self):
        self._nodes = None

    @property
    def elements(self) -> devicetools.Elements:
        """The currently handled |Element| objects.

        You are allowed to get, set and delete the currently handled elements:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> hp.elements
        Elements("land_dill", "land_lahn_1", "land_lahn_2", "land_lahn_3",
                 "stream_dill_lahn_2", "stream_lahn_1_lahn_2",
                 "stream_lahn_2_lahn_3")

        >>> del hp.elements
        >>> hp.elements
        Traceback (most recent call last):
        ...
        AttributeError: The actual HydPy instance does not handle any elements \
at the moment.

        >>> hp.elements = 'land_dill', 'land_lahn_1'
        >>> hp.elements
        Elements("land_dill", "land_lahn_1")

        However, note that doing so might result in erroneous networks
        and that you, even in case of correctness, must most likely call
        method |HydPy.update_devices| before performing the next
        simulation run.
        """
        elements = self._elements
        if elements is None:
            raise AttributeError(
                'The actual HydPy instance does not handle any '
                'elements at the moment.')
        return elements

    @elements.setter
    def elements(self, values):
        self._elements = devicetools.Elements(values).copy()

    @elements.deleter
    def elements(self):
        self._elements = None

    def prepare_everything(self) -> None:
        """Convenience method to make the actual |HydPy| instance runnable.

        Method |HydPy.prepare_everything| is the fastest approach to get a
        runnable |HydPy| object.  You only need to import class |Hydpy|,
        initialise it with the project name, define the simulation period
        via the |Timegrids| object of module |pub|, and call method
        |HydPy.prepare_everything| (in this documentation, we first need
        to prepare the example project via function |prepare_full_example_1|
        and change the current working directory via class |TestIO|):

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, round_, TestIO
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
        ...     hp.prepare_everything()

        Now you can start a simulation run and inspect the calculated
        time series of all relevant sequences.  We take the discharge
        values of the flux sequence |hland_fluxes.QT| of |Element| object
        `land_dill` and of the node sequence |Sim| of |Node| object `dill`
        as examples, which provide the same information in different
        units (mm/d and m³/s, respectively):

        >>> hp.simulate()
        >>> round_(hp.elements.land_dill.model.sequences.fluxes.qt.series)
        1.454998, 1.103529, 0.886541, 0.749761
        >>> round_(hp.nodes.dill.sequences.sim.series)
        11.658511, 8.842278, 7.103614, 6.00763
        """
        self.prepare_network()
        self.prepare_models()
        self.load_conditions()
        with hydpy.pub.options.warnmissingobsfile(False):
            self.prepare_nodeseries()
        self.prepare_modelseries()
        self.load_inputseries()

    @printtools.print_progress
    def prepare_network(self) -> None:
        """Load all network files as |Selections| (stored in module |pub|)
        and assign the "complete" selection to the |HydPy| object.

        .. testsetup::

            >>> from hydpy import pub
            >>> del pub.selections

        First, we call function |prepare_full_example_1| to prepare
        the `LahnH` example project, including its network files
        `headwaters.py`, `nonheadwaters.py`, and `streams.py`:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        Directly after initialising class |HydPy|, neither the
        resulting object nor module |pub| contain any information
        stemming from the network files:

        >>> from hydpy import HydPy, pub, TestIO
        >>> hp = HydPy('LahnH')
        >>> pub.selections
        Traceback (most recent call last):
        ...
        RuntimeError: Attribute selections of module `pub` is not \
defined at the moment.

        By calling the method |HydPy.prepare_network|, one loads all three
        network files into separate |Selection| objects, all handled
        by the |Selections| object of module |pub|.  Additionally,
        there is a |Selection| object named `complete`, covering all
        |Node| and |Element| objects of the other |Selection| objects:

        >>> with TestIO():
        ...     hp.prepare_network()
        >>> pub.selections
        Selections("complete", "headwaters", "nonheadwaters", "streams")

        >>> pub.selections.headwaters <= pub.selections.complete
        True
        >>> pub.selections.nonheadwaters <= pub.selections.complete
        True
        >>> pub.selections.streams <= pub.selections.complete
        True

        Initially, the |HydPy| object is aware of the complete set
        of |Node| and |Element| objects:

        >>> hp.nodes == pub.selections.complete.nodes
        True
        >>> hp.elements == pub.selections.complete.elements
        True

        See the documentation on method |HydPy.update_devices| on
        how to "activate| another selection in the safest manner.
        """
        hydpy.pub.selections = selectiontools.Selections()
        hydpy.pub.selections += hydpy.pub.networkmanager.load_files()
        self.update_devices(hydpy.pub.selections.complete)

    def prepare_models(self) -> None:
        """Read all control files related to the current |Element| objects,
        initialise the defined models, and prepare their parameter values.

        First, we call function |prepare_full_example_1| to prepare the
        `LahnH` example project:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        Now we can initialise a |HydPy| instance accordingly and call
        its methods |HydPy.prepare_network| and |HydPy.prepare_models|:

        >>> from hydpy import HydPy, pub, round_, TestIO
        >>> with TestIO():
        ...     pub.timegrids = '1996-01-01', '1996-01-05', '1d'
        ...     hp = HydPy('LahnH')
        ...     hp.prepare_network()
        ...     hp.prepare_models()

        As a result, each |Element| object handles a model of the type and
        with the parameter values defined in the relevant control file:

        >>> hp.elements.land_dill.model.name
        'hland_v1'
        >>> hp.elements.land_dill.model.parameters.control.area
        area(692.3)
        >>> hp.elements.stream_lahn_1_lahn_2.model.name
        'hstream_v1'
        >>> hp.elements.stream_lahn_1_lahn_2.model.parameters.control.lag
        lag(0.583)

        The `LahnH` example project comes with one auxiliary file, named
        `land.py`.  This file defines general parameter values, valid
        for all single parameter objects of the different model instances
        which are referencing this file via the `auxfile` keyword argument.
        The following examples use the `land_dill` element to show that
        the affected parameters are also correctly prepared:

        >>> control = hp.elements.land_dill.model.parameters.control
        >>> control.alpha
        alpha(1.0)
        >>> control.pcorr
        pcorr(1.0)
        >>> control.resparea
        resparea(True)
        >>> control.icmax
        icmax(field=1.0, forest=1.5)

        We show that the individual |hland_control.IcMax| values for two
        different elements are different, to demonstrate that parameter
        values defined within a master control file (|hland_control.ZoneType|)
        can affect the actual values of parameters defined in auxiliary
        control files:

        >>> from hydpy import round_
        >>> round_(control.icmax.values)
        1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5
        >>> round_(
        ...     hp.elements.land_lahn_2.model.parameters.control.icmax.values)
        1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5

        Missing parameter information in auxiliary files results in errors
        like the following:

        >>> filepath = 'LahnH/control/default/land.py'
        >>> with TestIO():
        ...     with open(filepath) as infile:
        ...         text = infile.read().replace('alpha(1.0)', '')
        ...     with open(filepath, 'w') as outfile:
        ...         outfile.write(text)
        ...     hp.prepare_models()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to initialise the model object of \
element `land_dill`, the following error occurred: While trying to load \
the control file `...land_dill.py`, the following error occurred: \
While trying to extract information for parameter `alpha` from file \
`land`, the following error occurred: The selected auxiliary file \
does not define value(s) for parameter `alpha`.

        Completely wrong control files result in the following error:

        >>> with TestIO():
        ...     with open('LahnH/control/default/land_dill.py', 'w'):
        ...         pass
        ...     hp.prepare_models()   # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to initialise the model object of \
element `land_dill`, the following error occurred: Model parameters \
cannot be loaded from control file `...land_dill.py`.  Please refer \
to the HydPy documentation on how to prepare control files properly.
        """
        self.elements.prepare_models()

    def init_models(self):
        """Deprecated! Use method |HydPy.prepare_models| instead.

        >>> from hydpy import HydPy
        >>> from unittest import mock
        >>> with mock.patch.object(HydPy, 'prepare_models') as mocked:
        ...     hp = HydPy('test')
        ...     hp.init_models()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.HydPyDeprecationWarning: \
Method `init_models` of class `HydPy` is deprecated.  \
Use method `prepare_models` instead.
        >>> mocked.call_args_list
        [call()]
        """
        self.prepare_models()
        warnings.warn(
            'Method `init_models` of class `HydPy` is deprecated.  '
            'Use method `prepare_models` instead.',
            exceptiontools.HydPyDeprecationWarning)

    def save_controls(
            self,
            parameterstep: Optional[timetools.PeriodConstrArg] = None,
            simulationstep: Optional[timetools.PeriodConstrArg] = None,
            auxfiler: Optional['auxfiletools.Auxfiler'] = None) -> None:
        """Write the control files of all current |Element| objects.

        We use the `LahnH` example project to demonstrate how to write
        a complete set of parameter control files.  For convenience, we
        let function |prepare_full_example_2| prepare a fully functional
        |HydPy| object, handling seven |Element| objects controlling
        four |hland_v1| and three |hstream_v1| application models:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        At first, there is only one control subfolder named "default",
        containing the seven master control files used in the step above:

        >>> import os
        >>> with TestIO():
        ...     os.listdir('LahnH/control')
        ['default']

        Next, we use the |ControlManager| to create a new directory
        and write analogue control files into it:

        >>> with TestIO():
        ...     pub.controlmanager.currentdir = 'newdir'
        ...     hp.save_controls()
        ...     sorted(os.listdir('LahnH/control'))
        ['default', 'newdir']

        We focus our examples on the (shorter) control files of
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

        Its name equals the element name.  The time step information
        stems from the |Timegrid| object available via |pub|:

        >>> pub.timegrids.stepsize
        Period('1d')

        Use the |Auxfiler| class to avoid redefining the same parameter
        values in multiple control files.  Here, we prepare an |Auxfiler|
        object which handles the two parameters of the model discussed
        above:

        >>> from hydpy import Auxfiler
        >>> aux = Auxfiler()
        >>> aux += 'hstream_v1'
        >>> aux.hstream_v1.stream = model.parameters.control.damp
        >>> aux.hstream_v1.stream = model.parameters.control.lag

        When passing the |Auxfiler| object to the method |HydPy.save_controls|,
        the control file of element `stream_lahn_1_lahn_2` does not
        define the values of both parameters on its own, but references
        the auxiliary file `stream.py` instead:

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
        |hstream_control.Damp| can reference control file `stream.py`:

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
        The `simulationstep` information, which is no integral part of
        control files but useful for testing them, has no impact on the
        written data.  However, passing an alternative `parameterstep`
        information changes the written values of time-dependent
        parameters both in the primary and the auxiliary control files,
        as to be expected:

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

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        Our |HydPy| instance `hp` is ready for the first simulation run,
        meaning the required initial conditions are available already.
        First, we start a simulation run covering the whole initialisation
        period and inspect the resulting soil moisture values of |Element|
        `land_dill`, handled by a sequence object of type |hland_states.SM|:

        >>> hp.simulate()
        >>> sm = hp.elements.land_dill.model.sequences.states.sm
        >>> sm
        sm(184.098541, 180.176461, 198.689343, 195.462014, 210.856923,
           208.319571, 220.881637, 218.898327, 229.022364, 227.431521,
           235.597338, 234.329294)

        By default, method |HydPy.load_conditions| always (re)loads the
        initial conditions from the directory with its name matching the
        start date of the simulation period, which we prove by also
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

        Now we perform two consecutive runs, covering the first and the
        second half of the initialisation period, respectively, and
        write, in both cases, the resulting final conditions to disk:

        >>> pub.timegrids.sim.lastdate = '1996-01-03'
        >>> hp.simulate()
        >>> sm
        sm(184.603966, 180.671117, 199.234825, 195.998635, 211.435809,
           208.891492, 221.488046, 219.49929, 229.651122, 228.055912,
           236.244147, 234.972621)
        >>> with TestIO():
        ...     hp.save_conditions()

        >>> pub.timegrids.sim.firstdate = '1996-01-03'
        >>> pub.timegrids.sim.lastdate = '1996-01-05'
        >>> hp.simulate()
        >>> with TestIO():
        ...     hp.save_conditions()
        >>> sm
        sm(184.098541, 180.176461, 198.689343, 195.462014, 210.856923,
           208.319571, 220.881637, 218.898327, 229.022364, 227.431521,
           235.597338, 234.329294)

        Analogous to method |HydPy.load_conditions|, method
        |HydPy.save_conditions| writes the resulting conditions to a
        directory with its name matching the end date of the simulation
        period, which we prove by reloading the conditions related
        to the middle of the initialisation period and showing the
        relevant file content:

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

        You can define another directory by assigning a different
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
        """Check all values of the condition sequences (|StateSequence|
        and |LogSequence| objects) for boundary violations and fix them
        if necessary.

        We use the `LahnH` example project to explain the functionality
        of method |HydPy.trim_conditions|, that gives no response at
        all when all conditions are correctly set:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> with pub.options.warntrim(True):
        ...     hp.trim_conditions()

        If you try, for example, to set interception capacities
        (|hland_states.Ic|) that violate the maximum capacity
        (|hland_control.IcMax|), you get a direct response based
        on function |trim|:

        >>> with pub.options.warntrim(True):
        ...     hp.elements.land_dill.model.sequences.states.ic(1.2)
        Traceback (most recent call last):
        ...
        UserWarning: For variable `ic` of element `land_dill` at least \
one value needed to be trimmed.  The old and the new value(s) are \
`1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.2` and \
`1.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.0, 1.2`, respectively.

        However, changing the boundaries themselves without adjusting
        the conditions cannot be detected automatically.  Whenever in
        doubt, call method |HydPy.trim_conditions| explicitly:

        >>> hp.elements.land_dill.model.parameters.control.icmax(1.1)
        >>> with pub.options.warntrim(True):
        ...     hp.trim_conditions()
        Traceback (most recent call last):
        ...
        UserWarning: For variable `ic` of element `land_dill` at least \
one value needed to be trimmed.  The old and the new value(s) are \
`1.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.0, 1.2, 1.0, 1.2` and \
`1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0, 1.1, 1.0, 1.1`, respectively.
        """
        self.elements.trim_conditions()

    def reset_conditions(self):
        """Reset all currently relevant condition sequences.

        Method |HydPy.reset_conditions| is the most convenient way to
        perform simulations repeatedly for the same period, each time
        starting from the same initial conditions, e.g. for parameter
        calibration. Each |StateSequence| and |LogSequence| object
        remembers the last assigned values and can reactivate them
        for the mentioned purpose.

        For demonstration, we perform a simulation for the `LahnH`
        example project spanning four days:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> hp.simulate()
        >>> from hydpy import print_values
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294

        Just repeating the simulation gives different results due to
        applying the final states of the first simulation run as the
        initial states of the second run:

        >>> hp.simulate()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        26.21469, 25.063443, 24.238632, 23.317984

        Calling |HydPy.reset_conditions| first allows repeating the
        first simulation run exactly multiple times:

        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294
        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> print_values(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294
        """
        self.elements.reset_conditions()

    @property
    def conditions(self) -> ConditionsType:
        """A nested dictionary, containing the values of all condition
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

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, pub, TestIO, print_values
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     pub.timegrids = '1996-01-01', '1996-04-01', '1d'
        ...     hp.prepare_everything()
        >>> pub.timegrids.sim.lastdate = '1996-02-20'
        >>> hp.simulate()
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
        >>> hp.simulate()
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
        >>> hp.simulate()
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
        For safety, we suggest setting the option |Options.warntrim| to
        |True| before resetting conditions.
        """
        return self.elements.conditions

    @conditions.setter
    def conditions(self, conditions):
        self.elements.conditions = conditions

    @property
    def networkproperties(self) -> Dict[str, Any]:
        """Some properties of the network defined by the currently relevant
        |Node| and |Element| objects.

        See the documentation on method |HydPy.print_networkproperties|
        for further information.
        """
        return {
            f'Number of nodes': len(self.nodes),
            f'Number of elements': len(self.elements),
            f'Number of end nodes': len(self.endnodes),
            f'Number of distinct networks': len(self.segregatednetworks),
            f'Applied node variables': self.variables
        }

    def print_networkproperties(self) -> None:
        """Print some properties of the network defined by the currently
        relevant |Node| and |Element| objects.

        |HydPy.print_networkproperties| is for convenience to summarise
        specific network measures like |HydPy.segregatednetworks|.

        The `LahnH` example project defines a small, single network,
        with all catchments ultimately discharging to node `lahn_3`:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, TestIO
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     hp.prepare_network()
        >>> hp.print_networkproperties()
        Number of nodes: 4
        Number of elements: 7
        Number of end nodes: 1
        Number of distinct networks: 1
        Applied node variables: Q
        """
        for key, value in self.networkproperties.items():
            if isinstance(value, typingtools.IterableNonString):
                value = objecttools.enumeration(value)
            print(f'{key}: {value}')

    @property
    def endnodes(self):
        """All currently relevant |Node| objects which define a downstream
        endpoint of the network.

        The `LahnH` example project defines a small, single network,
        with all catchments ultimately discharging to node `lahn_3`:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, TestIO
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     hp.prepare_network()
        >>> hp.endnodes
        Nodes("lahn_3")

        After breaking the connection between node `lahn_1` and its
        downstream river channel element `stream_lahn_1_lahn2`,
        `lahn_1` also becomes an end node:

        >>> hp.nodes.lahn_1.exits.mutable = True
        >>> hp.elements.stream_lahn_1_lahn_2.inlets.mutable = True
        >>> del hp.nodes.lahn_1.exits.stream_lahn_1_lahn_2
        >>> del hp.elements.stream_lahn_1_lahn_2.inlets.lahn_1
        >>> hp.endnodes
        Nodes("lahn_1", "lahn_3")

        Even with a proper connection to a downstream element, a node
        counts as an end node as long as these elements are not part
        of the currently relevant network (meaning, currently handled
        by the |HydPy| object):

        >>> del hp.elements.stream_dill_lahn_2
        >>> hp.nodes.dill.exits
        Elements("stream_dill_lahn_2")
        >>> hp.endnodes
        Nodes("dill", "lahn_1", "lahn_3")

        Connections with "remote" elements are considered irrelevant:

        >>> stream = hp.elements.stream_lahn_2_lahn_3
        >>> stream.inlets.mutable = True
        >>> stream.receivers.mutable = True
        >>> stream.receivers += stream.inlets.lahn_2
        >>> del stream.inlets.lahn_2
        >>> hp.endnodes
        Nodes("dill", "lahn_1", "lahn_2", "lahn_3")
        """
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
    def segregatednetworks(self) -> 'selectiontools.Selections':
        """The number of segregated networks defined by the currently
        relevant |Node| and |Element| objects.

        Each end node (as defined by property |HydPy.endnodes|) eventually
        defines a single network, segregated from the networks of other
        end nodes.  Due to the `LahnH` example project defining only a
        single end node, there can be only one segregate network,
        accordingly:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, TestIO
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     hp.prepare_network()
        >>> hp.segregatednetworks
        Selections("lahn_3")
        >>> hp.segregatednetworks.lahn_3
        Selection("lahn_3",
                  nodes=("dill", "lahn_1", "lahn_2", "lahn_3"),
                  elements=("land_dill", "land_lahn_1", "land_lahn_2",
                            "land_lahn_3", "stream_dill_lahn_2",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

        Revisiting the examples of the documentation on property
        |HydPy.endnodes|, we get the similar results.  Note that
        the segregated networks are always |Selection| objects, that
        do not overlap each other (meaning, no |Node| or |Element| object
        occurs more than one time):

        >>> hp.nodes.lahn_1.exits.mutable = True
        >>> hp.elements.stream_lahn_1_lahn_2.inlets.mutable = True
        >>> del hp.nodes.lahn_1.exits.stream_lahn_1_lahn_2
        >>> del hp.elements.stream_lahn_1_lahn_2.inlets.lahn_1
        >>> hp.segregatednetworks
        Selections("lahn_1", "lahn_3")
        >>> hp.segregatednetworks.lahn_1
        Selection("lahn_1",
                  nodes="lahn_1",
                  elements="land_lahn_1")
        >>> hp.segregatednetworks.lahn_3
        Selection("lahn_3",
                  nodes=("dill", "lahn_2", "lahn_3"),
                  elements=("land_dill", "land_lahn_2", "land_lahn_3",
                            "stream_dill_lahn_2", "stream_lahn_1_lahn_2",
                            "stream_lahn_2_lahn_3"))

        >>> del hp.elements.stream_dill_lahn_2
        >>> hp.nodes.dill.exits
        Elements("stream_dill_lahn_2")
        >>> hp.segregatednetworks
        Selections("dill", "lahn_1", "lahn_3")
        >>> hp.segregatednetworks.dill
        Selection("dill",
                  nodes="dill",
                  elements="land_dill")
        >>> hp.segregatednetworks.lahn_1
        Selection("lahn_1",
                  nodes="lahn_1",
                  elements="land_lahn_1")
        >>> hp.segregatednetworks.lahn_3
        Selection("lahn_3",
                  nodes=("lahn_2", "lahn_3"),
                  elements=("land_lahn_2", "land_lahn_3",
                            "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))


        >>> stream = hp.elements.stream_lahn_2_lahn_3
        >>> stream.inlets.mutable = True
        >>> stream.receivers.mutable = True
        >>> stream.receivers += stream.inlets.lahn_2
        >>> del stream.inlets.lahn_2
        >>> hp.segregatednetworks
        Selections("dill", "lahn_1", "lahn_2", "lahn_3")
        >>> hp.segregatednetworks.dill
        Selection("dill",
                  nodes="dill",
                  elements="land_dill")
        >>> hp.segregatednetworks.lahn_1
        Selection("lahn_1",
                  nodes="lahn_1",
                  elements="land_lahn_1")
        >>> hp.segregatednetworks.lahn_2
        Selection("lahn_2",
                  nodes="lahn_2",
                  elements=("land_lahn_2", "stream_lahn_1_lahn_2"))
        >>> hp.segregatednetworks.lahn_3
        Selection("lahn_3",
                  nodes="lahn_3",
                  elements=("land_lahn_3", "stream_lahn_2_lahn_3"))

        In all examples above, the number of the end nodes and the number
        of the segregated networks are identical, which is not the case
        when two or more networks share the same network.  We restore
        our original network and add two additional end nodes, `nowhere`
        and `somewhere`,  linking the first one with element
        `stream_lahn_2_lahn_3` and the second one with the additional
        element `stream_lahn_1_nowhere`, which we connect to node `lahn_1`:

        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     hp.prepare_network()
        >>> from hydpy import Element
        >>> _ = Element('stream_lahn_2_lahn_3', outlets='nowhere')
        >>> hp.nodes += 'nowhere'
        >>> hp.elements += Element('stream_lahn_1_nowhere',
        ...                        inlets='lahn_1',
        ...                        outlets='somewhere')
        >>> hp.nodes += 'somewhere'

        Now there are three end nodes but only two segregated networks,
        as node `nowhere` does not reference any upstream devices not
        also referenced by node `lahn_3`.  The unique feature of element
        `lahn_3` and `stream_lahn_1_nowhere` is that they drain to
        either node `lahn_3` or `somewhere` but not both, which is why
        they are the only members of selection `lahn_3` and `somewhere`,
        respectively:

        >>> hp.endnodes
        Nodes("lahn_3", "nowhere", "somewhere")
        >>> hp.segregatednetworks
        Selections("lahn_3", "somewhere")
        >>> hp.segregatednetworks.lahn_3
        Selection("lahn_3",
                  nodes="lahn_3",
                  elements="land_lahn_3")
        >>> hp.segregatednetworks.somewhere
        Selection("somewhere",
                  nodes="somewhere",
                  elements="stream_lahn_1_nowhere")
        """
        sels1 = selectiontools.Selections()
        sels2 = selectiontools.Selections()
        complete = selectiontools.Selection(
            'complete', self.nodes, self.elements)
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

    @property
    def _directedgraph(self) -> networkx.DiGraph:
        digraph = networkx.DiGraph()
        digraph.add_nodes_from(self.elements)
        digraph.add_nodes_from(self.nodes)
        for element in self.elements:
            for node in itertools.chain(element.inlets, element.inputs):
                digraph.add_edge(node, element)
            for node in element.outlets:
                digraph.add_edge(element, node)
        return digraph

    @property
    def variables(self) -> List[str]:
        """Summary of all |Node.variable| properties of the currently
        relevant |Node| objects.

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import HydPy, TestIO
        >>> with TestIO():
        ...     hp = HydPy('LahnH')
        ...     hp.prepare_network()
        >>> hp.variables
        ['Q']

        >>> from hydpy import Node
        >>> hp.nodes += Node('test', variable='T')
        >>> hp.variables
        ['Q', 'T']
        """
        variables = set([])
        for node in self.nodes:
            variables.add(node.variable)
        return sorted(variables)

    def open_files(self, idx: int = 0) -> None:
        """Open all required internal time series files.

        This method is only required when storing internal time series
        data on disk.  See the main documentation on class |HydPy| for
        further information.
        """
        self.elements.open_files(idx=idx)
        self.nodes.open_files(idx=idx)

    def close_files(self) -> None:
        """Close all previously opened internal time series files.

        This method is only required when storing internal time series
        data on disk.  See the main documentation on class |HydPy| for
        further information.
        """
        self.elements.close_files()
        self.nodes.close_files()

    def update_devices(
            self,
            selection: Optional[typingtools.DevicesHandlerProtocol] = None
    ) -> None:
        """Determine the order, in which method |HydPy.simulate| processes
        the currently relevant |Node| and |Element| objects.

        Eventually passed |Node| and |Element| objects (for example,
        contained within a |Selection| object) replace existing ones.

        As described in the documentation on the method
        |HydPy.prepare_network|, a |HydPy| object usually starts with
        the "complete" network of the considered project:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        The safest approach to "activate" another selection is to use
        the method |HydPy.update_devices|:

        >>> pub.selections.headwaters
        Selection("headwaters",
                  nodes=("dill", "lahn_1"),
                  elements=("land_dill", "land_lahn_1"))

        >>> hp.update_devices(pub.selections.headwaters)
        >>> hp.nodes
        Nodes("dill", "lahn_1")
        >>> hp.elements
        Elements("land_dill", "land_lahn_1")

        Method |HydPy.update_devices| automatically updates the `deviceorder`,
        assuring method |HydPy.simulate| processes "upstream" model
        instances before it processes their "downstream" neighbours:

        >>> for device in hp.deviceorder:
        ...     print(device)
        land_lahn_1
        lahn_1
        land_dill
        dill

        *HydPy* projects supposed for calculating groundwater recharge
        or for testing may not define any |Node| objects:

        >>> del hp.nodes.dill
        >>> hp.elements.land_dill.outlets.mutable = True
        >>> del hp.elements.land_dill.outlets.dill
        >>> del hp.nodes.lahn_1
        >>> hp.elements.land_lahn_1.outlets.mutable = True
        >>> del hp.elements.land_lahn_1.outlets.lahn_1
        >>> hp.update_devices()
        >>> for device in hp.deviceorder:
        ...     print(device)
        land_lahn_1
        land_dill
        """
        if selection is not None:
            self.nodes = selection.nodes
            self.elements = selection.elements
        self.deviceorder = list(networkx.topological_sort(self._directedgraph))

    @property
    def methodorder(self) -> List[Callable]:
        """All methods of the currently relevant |Node| and |Element|
        objects to be processed by method |HydPy.simulate| during a
        simulation time step, ordered in a correct execution sequence.

        Property |HydPy.methodorder| should be of interest for framework
        developers only..
        """
        funcs = []
        for node in self.nodes:
            if node.deploymode == 'oldsim':
                funcs.append(node.sequences.fastaccess.load_simdata)
            elif node.deploymode == 'obs':
                funcs.append(node.sequences.fastaccess.load_obsdata)
        for node in self.nodes:
            if node.deploymode != 'oldsim':
                funcs.append(node.sequences.fastaccess.reset)
        for device in self.deviceorder:
            if isinstance(device, devicetools.Element):
                funcs.append(device.model.simulate)
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
        for logger in self.loggers.values():
            funcs.append(logger.update)
        return funcs

    @printtools.print_progress
    def simulate(self) -> None:
        """Perform a simulation run over the actual simulation period
        defined by the |Timegrids| object stored in module |pub|.

        We let function |prepare_full_example_2| prepare a runnable
        |HydPy| object related to the `LahnH` example project:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()

        First, we execute a default simulation run covering the whole
        simulation period and inspect the discharge series simulated
        at the outlet of the river basin, represented by node `lahn_3`:

        >>> hp.simulate()
        >>> from hydpy import round_
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294

        After resetting the initial conditions via method
        |HydPy.reset_conditions|, we repeat the simulation run and get
        the same results (usually, one would change, for example,
        some parameter values to calculate different results, of course):

        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294

        Simulation runs do not need to cover the whole initialisation
        period at once.  After setting the |Timegrid.lastdate| property
        of the `sim` |Timegrid| of the |Timegrids| objects stored within
        module |pub| to the middle of the initialisation period, method
        |HydPy.simulate| calculates the first two discharge values only:

        >>> hp.reset_conditions()
        >>> hp.nodes.lahn_3.sequences.sim.series = 0.0
        >>> pub.timegrids.sim.lastdate = '1996-01-03'
        >>> hp.simulate()
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 0.0, 0.0

        After justing the both |Timegrid.firstdate| and |Timegrid.lastdate|
        of the `sim` |Timegrid| to the second half of the initialisation
        period, |HydPy.simulate| completes the time series:

        >>> pub.timegrids.sim.firstdate = '1996-01-03'
        >>> pub.timegrids.sim.lastdate = '1996-01-05'
        >>> hp.simulate()
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294

        In the above examples, each |Model| object (handled by an |Element|
        object) passes its simulated values via a |Node| object to its
        downstream |Model| object.  There are two options to deviate from
        this default behaviour, that can be changed for each node
        individually via the property |Node.deploymode|.  We focus on node
        `lahn_2` in the following, being the upstream neighbour of node
        `lahn_3`.  So far, its deploy mode is `newsim`, meaning that the
        node passes newly calculated simulation values to the downstream
        element `stream_lahn_2_lahn_3`:

        >>> hp.nodes.lahn_2.deploymode
        'newsim'

        Under the second option `oldsim`, node `lahn_2` does not pass
        the discharge values simulated in the next simulation run but
        the "old" discharge values already available by the
        |IOSequence.series| array of the |Sim| sequence.  This behaviour
        can, for example, be useful when calibrating subsequent subareas
        of a river basin sequentially, beginning with the headwaters
        and continuing with their downstream neighbours.  For the
        clarity of this example, we decrease all values of the "old"
        simulated series of node `lahn_2` by 10 m³/s:

        >>> round_(hp.nodes.lahn_2.sequences.sim.series)
        42.19966, 27.098027, 22.873371, 20.178247
        >>> hp.nodes.lahn_2.deploymode = 'oldsim'
        >>> hp.nodes.lahn_2.sequences.sim.series -= 10.0

        After performing another simulation run (over the whole
        initialisation period, again), the modified discharge values of
        node `lahn_2` are unchanged.  The simulated values of node `
        lahn_3` are, compared to the `newsim` runs, decreased by 10 m³/s
        (there is no time delay or dampening of the discharge values
        between both nodes due to the |hstream_control.Lag| time of
        application model |hstream_v1| being smaller than the simulation
        time step):

        >>> hp.reset_conditions()
        >>> pub.timegrids.sim.firstdate = '1996-01-01'
        >>> pub.timegrids.sim.lastdate = '1996-01-05'
        >>> hp.simulate()
        >>> round_(hp.nodes.lahn_2.sequences.sim.series)
        32.19966, 17.098027, 12.873371, 10.178247
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        43.793428, 27.157714, 21.835184, 18.375294

        The third option is `obs`, where node `lahn_2` receives
        and stores the values from its upstream models but passes
        other, observed values, handled by sequence |Obs|, which
        we, for simplicity, set to zero for the complete initialisation
        and simulation period (more often, one would read measured
        data from files via methods as |HydPy.load_obsseries|):

        >>> hp.nodes.lahn_2.deploymode = 'obs'
        >>> hp.nodes.lahn_2.sequences.obs.series = 0.0

        Now the simulated values of node `lahn_2` are identical with
        the ones of the `newsim` example, but the simulated values
        of node `lahn_3` are lower due to receiving the observed
        instead of the simulated values from upstream:

        >>> hp.reset_conditions()
        >>> hp.nodes.lahn_3.sequences.sim.series = 0.0
        >>> hp.simulate()
        >>> round_(hp.nodes.lahn_2.sequences.obs.series)
        0.0, 0.0, 0.0, 0.0
        >>> round_(hp.nodes.lahn_2.sequences.sim.series)
        42.19966, 27.098027, 22.873371, 20.178247
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        11.593767, 10.059687, 8.961813, 8.197047

        The last example shows that resetting option
        |Node.deploymode| to `newsim` results in the default
        behaviour of the method |HydPy.simulate|, again:

        >>> hp.nodes.lahn_2.deploymode = 'newsim'
        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> round_(hp.nodes.lahn_2.sequences.sim.series)
        42.19966, 27.098027, 22.873371, 20.178247
        >>> round_(hp.nodes.lahn_3.sequences.sim.series)
        53.793428, 37.157714, 31.835184, 28.375294
        """
        idx_start, idx_end = hydpy.pub.timegrids.simindices
        self.open_files(idx_start)
        methodorder = self.methodorder
        for idx in printtools.progressbar(range(idx_start, idx_end)):
            for func in methodorder:
                func(idx)
        self.close_files()

    def doit(self) -> None:
        """Deprecated! Use method |HydPy.simulate| instead.

        >>> from hydpy import HydPy
        >>> from unittest import mock
        >>> with mock.patch.object(HydPy, 'simulate') as mocked:
        ...     hp = HydPy('test')
        ...     hp.doit()
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.HydPyDeprecationWarning: \
Method `doit` of class `HydPy` is deprecated.  \
Use method `simulate` instead.
        >>> mocked.call_args_list
        [call()]
        """
        self.simulate()
        warnings.warn(
            'Method `doit` of class `HydPy` is deprecated.  '
            'Use method `simulate` instead.',
            exceptiontools.HydPyDeprecationWarning)

    def prepare_allseries(self, ramflag: bool = True) -> None:
        """Allow all current |IOSequence| objects to handle time series
        data via property |IOSequence.series|, depending on argument
        `ramflag` either in RAM (|True|) on disk (|False|).

        See the main documentation on class |HydPy| for further information.
        """
        self.prepare_modelseries(ramflag)
        self.prepare_nodeseries(ramflag)

    def prepare_modelseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for model sequences."""
        self.elements.prepare_allseries(ramflag=ramflag)

    def prepare_inputseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for model input sequences."""
        self.elements.prepare_inputseries(ramflag=ramflag)

    def prepare_fluxseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for model flux sequences."""
        self.elements.prepare_fluxseries(ramflag=ramflag)

    def prepare_stateseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for model state sequences."""
        self.elements.prepare_stateseries(ramflag=ramflag)

    def prepare_nodeseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for node sequences."""
        self.nodes.prepare_allseries(ramflag=ramflag)

    def prepare_simseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for simulation sequences of nodes."""
        self.nodes.prepare_simseries(ramflag=ramflag)

    def prepare_obsseries(self, ramflag: bool = True) -> None:
        """An alternative method for |HydPy.prepare_allseries| specialised
        for observation sequences of nodes."""
        self.nodes.prepare_obsseries(ramflag=ramflag)

    def save_allseries(self) -> None:
        """Write the time series data of all current |IOSequence| objects
        at once to the external data file(s).

        See the main documentation on class |HydPy| for further information.
        """
        self.save_modelseries()
        self.save_nodeseries()

    def save_modelseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for model sequences."""
        self.elements.save_allseries()

    def save_inputseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for model input sequences."""
        self.elements.save_inputseries()

    def save_fluxseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for model flux sequences."""
        self.elements.save_fluxseries()

    def save_stateseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for model state sequences."""
        self.elements.save_stateseries()

    def save_nodeseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for node sequences."""
        self.nodes.save_allseries()

    def save_simseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for simulation sequences of nodes."""
        self.nodes.save_simseries()

    def save_obsseries(self) -> None:
        """An alternative method for |HydPy.save_modelseries| specialised
        for observation sequences of nodes."""
        self.nodes.save_obsseries()

    def load_allseries(self) -> None:
        """Read the time series data of all current |IOSequence| objects
        at once from the external data file(s).

        See the main documentation on class |HydPy| for further information.
        """
        self.load_modelseries()
        self.load_nodeseries()

    def load_modelseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for model sequences."""
        self.elements.load_allseries()

    def load_inputseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for model input sequences."""
        self.elements.load_inputseries()

    def load_fluxseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for model flux sequences."""
        self.elements.save_fluxseries()

    def load_stateseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for model state sequences."""
        self.elements.load_stateseries()

    def load_nodeseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for node sequences."""
        self.nodes.load_allseries()

    def load_simseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for simulation sequences of nodes."""
        self.nodes.load_simseries()

    def load_obsseries(self) -> None:
        """An alternative method for |HydPy.load_modelseries| specialised
        for observation sequences of nodes."""
        self.nodes.load_obsseries()
