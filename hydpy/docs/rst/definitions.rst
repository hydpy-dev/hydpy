
.. _definitions:

Definitions
===========

HydPy is a Python library that follows the principles of object-oriented programming,
so its key concepts are usually implemented via classes.  The :ref:`reference_manual`
describes these classes and all their functionalities in detail, which is too much
information for HydPy beginners.  This section offers easier access to HydPy's key
concepts by listing the central terms and briefly explaining how we understand them.
If you want to know more, follow the links to the :ref:`reference_manual`.

.. _module:

module
______

`Module` is the Python term for a single source code file.  HydPy's documentation is
highly in sync with its source code.  Hence, we often mention that a particular module
provides certain features.   If you are interested, click on the link to the module or
search for it in the quick search bar to be directed to a documentation page explaining
this specific module and all its features.

.. _subpackage:

subpackage
__________

Python libraries like HydPy are often called "packages".  `subpackage` is a
subdirectory of the complete HydPy package that combines multiple related :ref:`modules
<module>`.  The "model" subpackage, for example, contains all :ref:`base models
<base_model>` (defined in nested `subpackages` and :ref:`application models
<application_model>` (defined in single modules).

.. _class:

class
_____

`Class` (or "type") is a core term in object-oriented programming. In this
documentation, `class` usually refers to a Python class, with which we often represent
a hydrological "thing" in general.  A general example is the type |float|, which
defines the general properties of floating-point numbers in Python.  A HydPy-specific
example is the class |hland_control.Area|, used by the model family :ref:`HydPy-H` to
represent a subbasin's area.

.. _subclass:

subclass
________

In object-oriented programming, a subclass (or child class) inherits the properties of
its base classes.  One can understand this concept intuitively by considering
`Furniture` as a base class and `Chair` and `Table` as its subclasses.  `Chair` and
`Table` could share common properties such as `colour` defined by their common base
class.  However, only class `Chair` would need a property like `backrest`.

From the development perspective, the concept of subclassing prevents code
duplications.  In the given example, one must add the property `colour` only to the
single base class `Furniture`, not its two subclasses `Chair` and `Table`.  But
remembering that HydPy relies heavily on subclassing also eases its understanding a
lot.  For example, the mentioned class |hland_control.Area| is a subclass of the base
class |Parameter| (noted in the first documentation line).  Hence, you can expect
|hland_control.Area| to work like all other |Parameter| subclasses, but it might
provide additional features.  One example of a shared property is the general class
attribute |Variable.TYPE|, which tells if a parameter handles, for example, integer or
floating-point values.  As you can see in the documentation on |hland_control.Area|,
:ref:`HydPy-H` (unsurprisingly) expects the subbasin area to be defined by
floating-point values.

instance
________

An `instance` (or "object") is a concrete realisation of a :ref:`class`.  `1.5`, for
example, is an instance of |float| with concrete data that makes it usable.  You can
add two |float| instances with the value `1.5` to get the new float instance `3.0`.  In
contrast, adding two classes does not make sense.  To give a HydPy example, class
|hland_control.Area| defines how we define the area of a subcatchment and how we can
use it when working with members of the :ref:`HydPy-H` model family. But when dealing
with the concrete area of a specific subbasin, we work with a single instance of
|hland_control.Area|.

.. _model:

model
_____

In hydrology, the meaning of the term `model` is highly context-dependent.  Technically
speaking, this documentation typically uses it to refer to a user-relevant subclass of
the base class |Model|.  Many such classes provide the features to represent the water
cycle within a subcatchment (e.g. |hland_96|).  Others deal with related processes like
flood routing (e.g. |musk_classic|) or serve more technical purposes like interpolation
of meteorological input data (e.g. |conv_idw|).  The following subsections describe the
most relevant model-related terms used throughout this documentation.

.. _project:

project
_______

The term `model` in hydrology often refers to the complete input and configuration data
necessary to simulate a catchment's water cycle.  As explained in the :ref:`Model`
section, we prefer to use it in the sense of "model type".  Hence, when discussing
"readily set-up models", we use the term `project` instead.  See the
:ref:`HydPy-H-Lahn` project for an example.

.. _model_family:

model family
____________

Each `model family` targets certain hydrologcial processes or more technical purposes
and consists of one :ref:`base_model` and several :ref:`application models
<application_model>`.  Some model families are the only ones that fulfil a specific
task, while others share their tasks but accomplish it with different means.  For
example, :ref:`HydPy-Evap` is the only model family with :ref:`submodels <submodel>`
suitable for calculating evapotranspiration.  In contrast, :ref:`HydPy-Musk` and
:ref:`HydPy-SW1D` share the same target (flood routing) but achieve it with very
different approaches ("hydrological" Muskingum routing vs "hydrodynamical"
Saint-Vernaint routing).

.. _base_model:

base model
__________

A `base model` provides all :ref:`methods <method>` to be used by the :ref:`application
models <application_model>` of the same :ref:`model_family`.  In practice, base models
are merely important for model developers.  However, we use base modelsto explain and
test individual methods, so one frequently encounters them when reading the
documentation.  See, for example, the documentation on method |hland_model.Calc_TC_V1|,
which uses the base model |hland| of the model family :ref:`HydPy-H` to explain the
adjustment of subbasin-wide average air temperature to hydrological response units with
different elevations.  The explanations and tests apply to all submodels selecting this
method (in this case, all application models of :ref:`HydPy-H`).

A base model's name equals the name of the :ref:`subpackage` containing
all :ref:`modules <module>` defining it.

.. _application_model:

application model
_________________

`Application models` are user-relevant model types.  They select suitable combinations
of the :ref:`methods <method>` provided by the :ref:`base_model` of the same
:ref:`model_family`.  (Hence, technically speaking, an `application model` is a
composition of components provided by a base model, not its subclass.)  Two examples of
the :ref:`HydPy-Evap` model family are |evap_ret_fao56| and |evap_ret_tw2002|, which
calculate the reference evapotranspiration according :t:`ref-Allen1998` and
:cite:t:`ref-DVWK`, respectively.

An application model's name equals the name of the :ref:`module` defining it.

.. _main_model:

main model
__________

Essentially, HydPy :ref:`projects <project>` are structured via :ref:`elements
<element>` and :ref:`nodes <node>`.  Each element instance directly handles one `main
model` instance (and indirectly, eventually, some :ref:`submodel` instances).  The
`main model` defines the general considered processes and executes them or delegates
this task to its submodels.  For example, by selecting |hland_96| as the `main model`,
one determines that a subbasin's runoff generation and concentration processes are
represented in the style of HBV96 :cite:p:`ref-Lindstrom1997HBV96`.

.. _submodel:

submodel
________

`Submodels` are selectable (and sometimes optional) members of :ref:`main models
<main_model>` that serve more specific tasks.  For example, |evap_pet_hbv96| and
|evap_aet_hbv96| calculate potential and actual evapotranspiration following HBV96
:cite:p:`ref-Lindstrom1997HBV96`.  One can "plug them" to |hland_96| to get a
consistent HBV96 model but also to other application models of :ref:`HydPy-H` and
different model families.

Note that we sometimes use the term `sub-submodel` when submodels can themselves use
submodels. For example, |evap_aet_hbv96| can use |evap_pet_hbv96| or a similar submodel
to gain potential evapotranspiration estimates.

.. _submodel_interface:

submodel interface
__________________

In object-oriented programming, an `interface` is an abstract description of concrete
:ref:`classes <class>`.  If, for example, a function is "programmed against" an
`interface`, it can use all concrete classes that "implement" it (synonyms of
"implement" are "follow" and "comply with").

HydPy's design of the :ref:`submodel` concept relies on this programming technique.
The :ref:`subpackage` `interfaces` provides multiple abstract descriptions for
submodels.  Users do not need to be aware of all details but should understand that if
an :ref:`application_model` like |hland_96| claims it can consider additional runoff
concentration processes by using a submodel that follows the |RConcModel_V1| interface,
they can use, for example, |rconc_uh| for this purpose, as it one of the submodels
following the |RConcModel_V1| interface.

.. _stand_alone_model:

stand-alone model
_________________

Most :ref:`submodels <submodel>` work only as members of a :ref:`main_model` instance.
However, there are some exceptions like |evap_ret_fao56|, which also work as
`stand-alone models`.  Suppose you are, for example, just interested in calculating
reference evapotranspiration for a subbasin.  In that case, do not need to set up a
complete "land model" but can assign an |evap_ret_fao56| instance directly to an
:ref:`element` (or even use it without any "network overhead").

.. _method:

method
______

This documentation uses the term `method` in two ways.  First, following
object-oriented programming terminology, it stands for (Python) functions directly
related to a :ref:`classes <class>`.  Second, it stands for the "granular units" (often
single equations) of (more or less) hydrological approaches implemented via subclasses
of class |Method|.  One example is |hland_model.Calc_TC_V1|, which adjusts the
subbasin-wide average air temperature to hydrological response units with different
elevations following HBV96 :cite:p:`ref-Lindstrom1997HBV96`.  The :ref:`base_model`
|hland| defines this method, and :ref:`application models <application_model>` like
|hland_96| use it.

.. _network:

network
_______

The term `network` addresses the (spatial) connections necessary to model a catchment
consisting of more than one subbasin.  A `network` combines consistently coupled
:ref:`element` and :ref:`node` instances.

.. _element:

element
_______

`Element` instances are the central components of each HydPy :ref:`project's <project>`
:ref:`network`.  They usually represent places where something needs to be calculated,
for example, the subbasin of a catchment (where we want to calculate runoff generation
and concentration) or a river crossing a subbasin (where we want to calculate flood
routing).

Within a :ref:`project`, each `element` instance has a unique, user-defined name that
serves to identify it.

`Elements` cannot perform calculations by themselves but require :ref:`application
models <application_model>`.  Each `element` instance handles a single
:ref:`main_model` (which might have several :ref:`submodels <submodel>`).  The
`element's` task is mainly to connect its model to the network and enable data exchange
with other models via :ref:`nodes <node>`.  A routing model, for example, receives its
inflow through its `element's` "inlet nodes" and passes it through its `element's`
"outlet nodes" to the next `element` downstream, which might handle another routing
model of the same or a different type or, for example, a lake model.  Pure information
like the current water level within river reach required to control an upstream dam's
water release is sent and received via "sender nodes" and "receiver nodes".

HydPy only provides a single `element` type (defined by class |Element|), which can
handle all different model types.

.. _node:

node
____

`Node` instances are the second essential component of all :ref:`networks <network>`.
They allow specifying which :ref:`model` instance passes which type of information in
which direction.  The "direction" follows from the given connections to :ref:`element`
instances (which handle the model instances).  The "type" can be set by the `node's`
"variable" (see attribute |Node.variable| of class |Node|).  Typical "places" for
`nodes` are basin outlets, river mouths or streamflow gauges.

Within a :ref:`project`, each `node` instance has a unique, user-defined name that
serves to identify it.

In contrast to elements, `nodes` do not differentiate between "local material transfer"
and "remote information transfer".  They generally get it from their "entry elements"
and pass all data to their "exit elements".

Besides passing data from one model to the other, `nodes` support provide features like
injecting externally prepared time series or comparing simulated with observed
data, which are especially important when a node represents a streamflow gauge.

.. _device:

device
______

We use `device` as the umbrella term for :ref:`element` and :ref:`node`.  (This is due
to the technical fact that the classes |Element| and |Node| are subclasses of the base
class |Device|.)

.. _selection:

selection
_________

A `selection` combines multiple :ref:`node` and :ref:`element` instances.  Each HydPy
:ref:`project` automatically contains one named "complete" that covers the entire
:ref:`network`.  You can freely define additional `selections` and store them in
individual network files (see the documentation on module |selectiontools| on how to do
this).

Often, `selections` represent subareas of large river basins modelled by multiple
"land" and "routing" models.  Still, you can choose any other criteria; the
:ref:`HydPy-H-Lahn` project, for example, uses selections to distinguish headwater from
non-headwater catchments.

Overlapping is allowed, meaning the same node or element instance can be a member of
multiple `selections`.

.. _keyword:

keyword
_______

Throughout this documentation, the term `keyword` often means "short text attached to
:ref:`element` or :ref:`node` instances".  These `keywords` serve as simple metadata
and help to query certain instances.  For example, one can add the string "gauge" to
all node instances representing locations with runoff measurements, making it easy to
calculate Nash-Sutcliffe coefficients wherever possible.

Each element and node instance can hold multiple `keywords`.

.. _parameter:

parameter
_________

The programming and hydrological communities use the term `parameter` differently.  In
Python, `parameter` means a variable of a function that receives its data when the
function is called (in `def f(x):`, `x` is the variable).  To avoid confusion, we try
to avoid the term `parameter` in this context and instead speak of (function)
arguments.

In hydrological modelling, `parameters` represent properties (described by numbers)
that often depend on the spatial characteristics of a catchment but are not changed by
the model equations.  In most cases, `parameter` values do not change at all during a
simulation run (for example, a soil's field capacity).  In other cases, the `parameter`
values vary in a predefined, often daily or annual pattern (for example, a deciduous
tree's leaf area index).

All implemented `parameter` types are subclasses of the base class |Parameter|.  We
differentiate them into the following groups.

From the user's perspective, the `control parameters` are most important.  One must set
the values of these `parameters`, which is typically done within "control files", to
adjust the selected model to the processes of the considered catchment. One example is
|hland_control.FC|, the field capacity parameter of the :ref:`HydPy-H` model family.
Note that many `control parameters` offer individual functionalities that often serve
to reduce configuration efforts.

One often encounters `derived parameters` when reading the basic equations and
explanations of individual :ref:`methods <method>`, but users must seldom configure
them directly.  In applications, `derived parameters` usually query information from
`control parameters` to calculate their values automatically.  If ever, users should
modify these values for testing purposes.  One example is |hland_derived.QFactor|,
which uses the user-defined subcatchment area (defined by `control parameter`
|hland_control.Area|) to determine the factor for converting the units of fluxes from
mm/T to m³/s (with `T` being the simulation step size).

`Fixed parameters` represent mathematical or physical properties with unambiguous
values.  Principally, users can modify them, but this is more a feature for testing
than for practical applications.  One example (for a `parameter` with a definitely
fixed value) is |hland_fixed.Pi|.

`Solver parameters` determine the numerical accuracy of :ref:`application models
<application_model>` that rely on numerical integration methods.  All `solver
parameters` come with default values.  These should be sensible in most cases, but
experienced users always have the option to modify them for potential benefits in
accuracy or simulation speed.  One example is |wland_solver.AbsErrorMax|, which defines
the local truncation error when working with the models of the :ref:`HydPy-W` family.

.. _sequence:

sequence
________

In HydPy, the term `sequence's` meaning differs from the Python terminology, and
one should be aware of a class conflict.

In Python, `sequence` refers to any indexable, ordered data collection.  A `string`
(|str|), for example, is a fixed collection of Unicode characters and a `list` (|list|)
is an adjustable collection of arbitrary objects.  We avoid using the term `sequence`
this way in the documentation texts.  Still, many type hints (which define, for
example, which type of data a function accepts) rely on Python's corresponding abstract
collection type `Sequence`.  (To a function argument annotated with `Sequence[str]`,
you can pass a string, a list of strings, or any other indexable, ordered collection
that only contains strings.)

In HydPy, we understand the term `sequence` similar to the term :ref:`parameter`, with
the difference that `sequence` addresses properties that change during a simulation
run.   These properties can be external forcings like precipitation or calculation
results like discharge.  To limit confusion and prevent class name clashes, we added an
underscore to the general `sequence` base class |Sequence_|.

The terms `sequence` and "time series" are closely related but not interchangable.  By
default, `sequence` instances only handle the current value (or, in some cases, the
recent values) of the properties they represent.  Yet, most `sequences` have the
|IOSequence.series| attribute, allowing them to keep the time series of a complete
simulation period.

We differentiate all implemented `sequence` types into different groups.  All
`sequences` of a group share a common base class that offers special functionalities.

`Input sequences` (derived from |InputSequence|) provide the (mostly meteorological)
input forcings required for hydrological simulations, usually by reading their data
from time series files.

`State and log sequences` serve as a :ref:`model's <model>` memory. We often subsume
them as "condition sequences" or simply "conditions".  `State sequences` (derived from
|StateSequence|) represent current states like soil moisture.  `Log sequences` (derived
from |LogSequence|) log previous input data or calculation results required by
approaches like the Unit Hydrograph method.  `State and log sequences` usually read
their initial conditions from "condition files" and and become stepwise updated during
simulation runs.

`Factor and flux sequences` contain pure simulation results.  They are technically
identical but target different properties. `Factor sequences` (derived from
|FactorSequence|) deal with factors like air temperature or water level, while flux
sequences (derived from |FluxSequence|) deal with fluxes like global radiation or
discharge.

`Inlet, outlet, receiver, and sender sequences` usually serve to exchange data with
other models.  We often subsume them as "link sequences".  See the :ref:`element`
subsection for more information.

`Aide sequences` (derived from |AideSequence|) only store temporary information and are
of little importance to users.

Note that `state, factor, and flux sequences` are sometimes called` output sequences`
for two reasons.  First, they support writing simulation results to time series files.
Second, HydPy allows connecting an `output sequence` of one model instance to an
`input sequence` of another model instance.  (This feature is unhandy, so we added the
submodel concept to HydPy 6.0.  Only a few cases are left where the input-output
sequence mechanism is still required.)
