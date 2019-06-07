# -*- coding: utf-8 -*-
"""This module implements superordinate tools for handling a HydPy project."""
# import...
# ...from standard library
import warnings
from typing import *
# ...from site-packages
import numpy
# ...from HydPy
import hydpy
from hydpy.core import abctools
from hydpy.core import devicetools
from hydpy.core import exceptiontools
from hydpy.core import filetools
from hydpy.core import printtools
from hydpy.core import selectiontools


conditionstype = Dict[str, Dict[str, Dict[str, Union[float, numpy.ndarray]]]]


class HydPy:
    """The main class for managing *HydPy* projects.

    In common *HydPy* projects, one prepares a single instance of class
    |HydPy|.  This instance, which we call "hp" throughout this
    documentation instead of "hydpy" to avoid a naming collisions with
    the *HydPy* package, provides many convenience methods to perform
    task like reading time series data or starting simulation runs.
    Additionally, it serves as a "root point" to access most of the
    details of a *HydPy* project, which allows a more granular control
    over the framework features.

    We elaborate these short explanations by using the `LahnH` example
    project.  Calling function |prepare_full_example_1| copies the
    complete example project `LahnH` into the `iotesting` directory of
    the *HydPy* site-package (alternatively, you can just copy the
    `LahnH` example project, which can be found in subpackage `data`,
    into a working directory of your choice):

    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    At first, the |HydPy| instance only needs to know the name of
    the relevant project, which is identical with the name of its
    root directory and is normally passed to the constructor of
    class |HydPy|:

    >>> hp = HydPy('LahnH')

    So far, our |HydPy| instance does not know anything about the
    project configurations except its name.  Most of this information
    would be available via properties |HydPy.nodes| and |HydPy.elements|
    but if we try to access them, we get the following error responses:

    >>> hp.nodes
    Traceback (most recent call last):
    ...
    RuntimeError: The actual HydPy instance does not handle any nodes \
at the moment.

    >>> hp.elements
    Traceback (most recent call last):
    ...
    RuntimeError: The actual HydPy instance does not handle any elements \
at the moment.

    One now could continue rather quickly by calling method
    |HydPy.prepare_everything|, which would make our |HydPy| instance
    ready for its first simulation run in one go.  However, we prefer
    to continue step by step by calling the individual preparation
    methods, which offers more flexibility.

    First, the |HydPy| instance needs to know the relevant |Node|
    and |Element| objects.  Method |HydPy.prepare_network| reads this
    information from so-called "network files".  The |Node| and |Element|
    objects connect with each other "automatically" and thereby
    define the topology or the network structure of the project (see
    the documentation on class |NetworkManager| and on module
    |devicetools| for more detailed  explanations):

    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     hp.prepare_network()

    (Using the "with" statement in combination with class |TestIO|
    makes sure that we are reading the network files from a subdirectory
    with the `iotesting` directory.  Here and in the following, you
    must omit such "with blocks" in case you copied the `LahnH` example
    project into your current working directory.)

    Now, our |HydPy| instance offers access to all |Node| objects
    defined within the `LahnH` example project, which are grouped
    together by a |Nodes| object:

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

    All |Node| objects are ready to be used.  The same is only parlty
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
    forces all |Element| objects to read the relevant parameter
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

    OOps, something went wrong.  We forgot to define the simulation
    period, which might be relevant for some time dependent
    configurations.  We discuss some examples of such configurations
    below but now use this little accident to discuss the typical pattern
    of *HydPy* error messages.  First, we usually try to add some
    additial "spatial" information (in this case: the name of the related
    |Element| object).  Second, we try to explain in which program context
    an error occurs.  This context is already available in much
    more detail in the so-called "stack trace" (the middle part of the
    printed error response which we do not show).  Stack trace descriptions
    are great for programmers but hard to read for others, which
    is why we often add "While trying to..." explanations to our error
    messages.  In our example, one can see that the error was raised
    while trying to initialise the |Model| object of element `land_dill`,
    which is clear in our example but could be less clear in more
    complex *HydPy* applications.

    The last sentence of the error message tells us that we need
    to define the attribute `timegrids` of module `pub`.  `pub`
    stands for "public", meaning module `pub` handles all (or at
    least most of) the globally available configuration data.
    One example is that module `pub` handles a |Timegrids| instance
    defining both the initialisation and the simulation period,
    which can be done by the following assignement (see the
    documentation in class |Timegrid| and on class |Timegrids| for
    further information):

    >>> from hydpy import pub
    >>> pub.timegrids = '1996-01-01', '1996-01-05', '1d'

    Now method |HydPy.prepare_models| does not complain anymore and
    adds an instance of the |hland_v1| application model to element
    `land_dill`, to which we set an additional reference in order
    to shorten the following examples:

    >>> with TestIO():
    ...     hp.prepare_models()

    >>> model = hp.elements.land_dill.model
    >>> model.name
    'hland_v1'

    All control parameters, being defined in the corresponding
    control file, are properly set.  As an example, we show the
    values of control parameter |hland_control.IcMax|, which
    in this case defines different values for hydrological
    response units of type |hland_constants.FIELD| (1.0 mm) and
    of type |hland_constants.FOREST| (1.5 mm):

    >>> model.parameters.control.icmax
    icmax(field=1.0, forest=1.5)

    The values of the derived parameters, which need to be
    calculated before starting a simulation run based on the
    control parameters and eventually based on some other settings
    (e.g. the initialisation time period) are also ready.  Here we
    show the value of the derived parameter  |hland_derived.RelLandArea|,
    representing the relative area of "land" units (1.0 means there
    is no "water" unit at all):

    >>> model.parameters.derived.rellandarea
    rellandarea(1.0)

    Note that we define all class names in "CamelCase" letters
    (which is a Python convention) and, whenever usefull, name
    the related objects identically but in lower case letters.
    We hope that eases finding the relevant parts of the online
    documentation when in trouble with a certain object.  Three
    examples we already encountered are the |Timegrids| instance
    `timegrids` of module `pub`, the |Nodes| instance `nodes` of
    class `HydPy`, and the |hland_derived.RelLandArea| instance
    of application model |hland_v1|:

    >>> from hydpy import classname
    >>> classname(pub.timegrids)
    'Timegrids'

    >>> classname(hp.nodes)
    'Nodes'

    >>> classname(model.parameters.derived.rellandarea)
    'RelLandArea'

    As show above, all |Parameter| objects of the model of element
    `land_dill` are ready to be used. However, all sequences (which
    handle the time variable properties) contain |numpy| |numpy.nan|
    values, which we use do indicate missing data.  We show this
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
    |FluxSequence|, and |StateSequence| are the most frequent ones
    (besides the |NodeSequence| subtypes  |Obs| and especially |Sim|).

    |StateSequence| objects describe many aspects of the current
    state of a model (or, e.g., of a catchment).  Each simulation
    run requires proper initial states, which we call initial
    conditions in the following (covering also memory aspects
    represented by |LogSequence| objects.  We load all required initial
    conditions by calling method |HydPy.load_conditions| (see the
    documentation on method |HydPy.load_conditions| for futher details):

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

    For states like |hland_states.SM|, we need to know only the values
    at the beginning of the simulation period.  All later values are
    calculated subsequentially during the simulation run.  However,
    this is different for input sequences like |hland_inputs.T|.
    Time variable properties like the air temperature are external
    forcings, hence they must be available over the complete simulation
    period a-priori.  Such complete time series can be made available
    via property |IOSequence.series| of class |IOSequence|, which
    has not happened for any sequence so far:

    >>> model.sequences.inputs.t.series
    Traceback (most recent call last):
    ...
    AttributeError: Sequence `t` of element `land_dill` is not \
requested to make any internal data available.

    Before loading time series data, we need to make sure to reserve
    the required memory storage.  We do this for all sequences at ones
    (not only the |ModelSequence| objects but also the |NodeSequence|
    objects as the |Sim| instance handled by node `dill`) though
    calling method |HydPy.prepare_allseries|:

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

    So far, all time series arrays are empty.  The `LahnH` example
    project provides time series files for the input sequences only,
    which is the minimum requirement for starting a simulation run.
    We use method |HydPy.load_inputseries| to load this datas:

    >>> with TestIO():
    ...     hp.load_inputseries()

    >>> from hydpy import round_
    >>> round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    Finally, we can perform the simulation run by calling method
    |HydPy.doit|:

    >>> hp.doit()

    The time series arrays of all sequences are now filled with
    values, which have been calculated during the simulation run ---
    except those of input sequence |hland_inputs.T|, of course
    (for the state sequence |hland_states.SM| only the time series
    of the first hydrological response unit is shown):

    >>> round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> round_(model.sequences.fluxes.qt.series)
    1.454998, 1.103529, 0.886541, 0.749761

    >>> round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 7.103614, 6.00763

    By comparison you can see that the lastly calculated (or read)
    time series value is the actual one for each |Sequence| object.
    This allows for example to write the final states of soil
    moisture sequence |hland_states.SM| and use them as initial
    conditions later, even if its complete time series where not
    available:

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

    In many applications, the simulated time series are the result
    we are really interested in.  Hence we close our explanations
    with some related examples that also cover the potential problem
    of to limited rapid access storage availability.

    By default, the *HydPy* framework does not overwrite already
    existing time series files.  Such settings can be changed via
    the |SequenceManager| object available in module |pub| (module
    |pub| also handles |ControlManager| and |ConditionManager| objects
    for settings related to reading and writing control files and
    condition files).  We change the default behaviour by setting
    the `generaloverwrite` attribute to |True| and write all time
    series (not only those of the flux and states sequences but
    also those of the input sequences) by calling method
    |HydPy.save_allseries|:

    >>> pub.sequencemanager.generaloverwrite = True
    >>> with TestIO():
    ...     hp.save_allseries()

    Next, we want to show how (and that) the reading of time series
    works.  We first set the time series values of all considered
    sequences to zero for this purpose:

    >>> model.sequences.inputs.t.series = 0.0
    >>> model.sequences.states.sm.series = 0.0
    >>> model.sequences.inputs.t.series = 0.0
    >>> hp.nodes.dill.sequences.sim.series = 0.

    Now we can reload the time series of all relevant sequences.
    However, doing so would result in a warning due to incomplete
    data (for example, of the observation data handled by the
    |Obs| sequence objects, which is not available in the `LahnH`
    example project).  To circumvent this problem, we disable
    the |Options.checkseries| option.  This is one of the
    general options handles by the instance of class |Options|
    available as another attribute of module |pub|.  We again
    use a "with block", making sure the option is changed only
    temporarily while executing method |HydPy.load_allseries|:

    >>> with TestIO(), pub.options.checkseries(False):
    ...     hp.load_allseries()

    The read time series data equals the previously written one:

    >>> round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> round_(model.sequences.fluxes.qt.series)
    1.454998, 1.103529, 0.886541, 0.749761

    >>> round_(hp.nodes.dill.sequences.sim.series)
    11.658511, 8.842278, 7.103614, 6.00763

    We mentioned the possibility for a more granular control of
    *HydPy* by using the different objects handled by the |HydPy|
    object instead of using its different convenience methods.
    Here is an elaborate example showing how to (re)load the states
    of an arbitrary simulation time step, which might be relevant
    for more complex workflows implementing data assimilation techniques
    and is more efficient than working with property |IOSequence.series|
    on individual |IOSequence| objects:

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

    In the examples above, all data has been handled in rapid access
    memory, which can be problematic when handling long time series
    in huge *HydPy* projects.  It is then suggested to only prepare
    time series which are really required (very often, it is
    sufficient to call |HydPy.prepare_inputseries|,
    |HydPy.load_inputseries|, and |HydPy.prepare_simseries| only).
    If this is not possible in your project, you can choose to handle
    the time series on disk instead, which unavoidably increases
    computation times extremely (there are some relevant means to
    lessen this problem a little, which we did not consider so far
    due to seldom usage of this option).  To prepare the necessary
    space on disk, assign |False| to the `ramflag` argument of
    method |HydPy.prepare_allseries| (or the related methods):

    >>> with TestIO():
    ...     hp.prepare_allseries(ramflag=False)

    By doing so, all previously available time series information
    is lost:

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
    ...     hp.doit()

    >>> with TestIO():
    ...     round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    >>> with TestIO():
    ...     round_(model.sequences.states.sm.series[:, 0])
    184.926173, 184.603966, 184.386666, 184.098541

    >>> with TestIO():
    ...     round_(model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849

    We mentioned the possibility for a more granular control of
    *HydPy* by using the different objects handled by the |HydPy|
    object instead of using its different convenience methods.
    Here is an elaborate example showing how to (re)load the states
    of an arbitrary simulation time step, which might be relevant
    for more complex workflows implementing data assimilation techniques:

    Besides computation times, it usually should make no difference
    wether one handles internal time series data in RAM or on disk.
    However, there are some subtle differences when one dives into
    the details.  Above, we have shown the possibility to (re)load the
    states of arbitrary simulation time steps when working in RAM.
    The same is possible when working on disk but has to call
    |IOSequences.open_files| first to prepare the necessary file
    object first and pass the relevant time step index to this
    method instead to method |ModelIOSequences.load_data| (again, this
    behaviour could be improved but has not due to limited usage
    of the `diskflag` option):

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

    def __init__(self, projectname: Optional[str] = None):
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
        self.prepare_models()
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

    def prepare_models(self):
        """Call method |Element.prepare_model| of all |Element| objects
        currently handled by the |HydPy| object."""
        self.elements.prepare_models()

    def init_models(self):
        """Deprecated: use method |HydPy.prepare_models| instead.

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

    def prepare_allseries(self, ramflag=True):
        """Allow all current |IOSequence| objects to handle time series
        data via property |IOSequence.series|, depending on argument
        `ramflag` either in RAM (|True|) of on disk (|False|).

        See the main documentation on class |HydPy| for further information.
        """
        self.prepare_modelseries(ramflag)
        self.prepare_nodeseries(ramflag)

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

    def save_allseries(self):
        """Write the time series data of all current |IOSequence| objects
        at once to external data file(s).

        See the main documentation on class |HydPy| for further information.
        """
        self.save_modelseries()
        self.save_nodeseries()

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

    def load_allseries(self):
        """Read the time series data of all current |IOSequence| objects
        at once from external data file(s).

        See the main documentation on class |HydPy| for further information.
        """
        self.load_modelseries()
        self.load_nodeseries()

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
