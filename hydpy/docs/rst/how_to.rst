
.. _`GitHub issue page`: https://github.com/hydpy-dev/hydpy/issues

.. _how_to:

How to...
=========

When developing *HydPy*, we tend to prefer flexibility over simplicity.
And when writing this documentation, we tend to prefer transparency over
graphicness.  Additionally, we follow some software standards not regularly
used within the hydrological community.  Therefore, it may take some time
before you profit from the strengths of *HydPy*.  As a little guidance,
our :ref:`how_to` help page tries to answer the most common questions of
new *HydPy* users.  We are going to extend it on demand, so please tell
us if a proper answer to your questions is missing (possibly on our
`GitHub issue page`_).

.. _understand_integration_tests:

...understand integration tests?
________________________________

Nowdadays, most software developers test their basic source code via other
source code.  Writing and maintaining this additional code is much work,
but one can easily automatise its execution.  Hence, one profits from
this strategy at the latest when a software project becomes too large for
repeated manual testing.

However, for reliable automatic testing, one needs to be sure that the
test code covers the different vital aspects of the code base thoroughly
enough.  One common strategy is to build two test suites, one including the
so-called unit tests and the other one the so-called integration tests.
Unit tests focus on specific software functionalities and often try to
cover all possible cases.  They lay the ground for software products that
yield correct results even under rare circumstances.  Integration tests, on the
other hand, evaluate the interplay of different functionalities.  Due to
increased complexity, they do not cover all possible cases but strive
to show that we get correct results for some relevant anticipated situations.
These "situations" are often workflows describing how we are expecting
users to work with the software.  Therefore, well-written integration tests
do not serve for testing only, but can be instructive for new developers
and sometimes even for users.

The documentation of *HydPy* follows the approach to embed all performed
unit and integration tests.  This very transparent approach allows the user
to read and quickly repeat the tests, and thereby to learn to use *HydPy*
correctly.

When speaking of integration tests, we often mean tests showing that the
individual components of a hydrological model are combined correctly, so
that the model can perform rational calculations.  Like *HydPy* standardises
model implementation, it suggests a certain structure for such tests.

We use the integration test on the application model |lland_dd| as an
example.  After some "usual" introductory remarks, we start with the
:ref:`lland_dd_integration_tests` section and prepare some general settings.
As we want our model to perform "real" simulations, we first define a
simulation period and step size via the |Timegrids| object available in
module |pub|.

Next, we prepare an object of the respective |Model| subclass (here,
|lland_dd.Model| of |lland_dd|) as well as an |Element| and a |Node|
object.  Through connecting these objects like in "real" projects, we check
that |lland_dd| does not only calculate the correct outflow but passes it
correctly to the downstream node (und thus potentially to other models
downstream).  For routing models as |lstream_v001|, we need to define
additional upstream nodes, to make sure the model also receives its inflow
correctly.

Eventually, we define some control parameters relevant for all integration
test examples.  For |lland_dd|, we decide to set parameter
|lland_control.NHRU| to one to focus only on one land-use type at a time.

The last general step is to initialise an |IntegrationTest| object,
which we use later for executing the individual integration test runs.
Behind the scenes, our test object prepares an |HydPy| object and uses
it very similar like we would do in a "real" *HydPy* project.

In the first example (:ref:`lland_dd_acker_summer`), we decide to test
|lland_dd| for the land-use type |lland_constants.ACKER| and set the
land use parameter |lland_control.Lnk| accordingly.  After that, we
prepare all remaining control parameters.  We can define the parameter
values as we would do within the control files of "real" *HydPy* projects.

Next, we define the initial conditions.  Principally, we could pass them
to the relevant state sequences directly, as we would do within the
condition files of a "real" *HydPy* project.  But then we need to reset
them after each integration test example (each simulation run changes the
model states, and each subsequent run starts with the lastly calculated
states by default).  To avoid additional resetting work, class
|IntegrationTest| offers the |Test.inits| property.  We pass pairs of
|StateSequence| objects and initial values, which our test object memorises.
Now it will reset each given state to the corresponding initial value
before each test run.  Note that |Test.inits| also accepts |LogSequence|
objects (see for example the documentation on application model |hland_v1|,
in which we define a single value for the unit hydrograph memory sequence
|rconc_logs.QUH|).

Finally, we define all model input series.  |lland_dd| receives external
meteorological input only, which we make available via the |IOSequence.series|
property of the relevant |InputSequence| objects (here we pass hard-coded
values to, for example, the precipitation sequence |lland_inputs.Nied|).
Routing models as |lstream_v001| usually do not receive external input
but inflow from upstream models.  More concretely, they pick data from the
|Sim| sequence(s) of their inlet |Node| object(s) (in the documentation on
|lstream_v001|, we calculate a design flood-wave on-the-fly and assign it
the simulation sequences of two inlet nodes).  In a "real" *HydPy* project,
we usually would not provide any time-series data via Python source code
but use more conventional file formats like NetCDF-CF (see |netcdftools|).

After all these preparations, we let our |IntegrationTest| object execute
the first test example.  It (re)sets the initial conditions, calls the
|HydPy.simulate| method and tabulates the original data of all |InputSequence|
and upstream |Sim| objects as well the result data of all |FluxSequence|,
|StateSequence|, and downstream |Sim| objects for each simulation time step.
This huge table is hard to read but should suffice to follow each relevant
aspect of the internal model behaviour.

Note that the tabulated date also exists hard-coded in the related source
file for regression testing.  Each time when we or, for example, Travis CI
(see section :ref:`tests_and_documentation`) execute our test suite,
Python's |doctest| features compare the freshly calculated table with the
hard-coded old table and report if they are not identical.  This sort of
testing helps users to check if their *HydPy* installation works as
documented and prevent developers from accidentally changing model features.

The tabulated data is comprehensive and partly even redundant.  We only
neglect the results of |AideSequence| objects (that usually handle temporary
information not relevant for the user) and |LogSequence| objects (that
typically provide access to data previously handled by other sequences).
Redundancy is often due to testing both the "internal" and the "external"
simulation results.  See for example the tabulated data of the integration
tests of |lstream_v001|, where the values of flux sequence
|lstream_fluxes.QA| and the outlet node sequence `output` are
identical. |lstream_v001| first calculates the outflow values and then
passes them to the downstream node.  Due to no other models being involved,
the identity of both series gives us confidence  |lstream_v001| integrates
correctly with all relevant *HydPy* functionalities.

When passing a filename to our test object (in example
:ref:`lland_dd_acker_summer`: "lland_dd_acker_summer") it also creates an
interactive HTML plot, stores it in the `html_` subpackage, and embeds it
into the documentation.  This mechanism ensures that each graph is always
in-sync with the considered *HydPy* version.  The additional arguments
`axis1` and `axis2` allow modifying the initial plot configuration.

We then continue the :ref:`lland_dd_integration_tests` section with example
:ref:`lland_dd_wasser`, dealing with one of the water types of |lland_dd|.
We only need to assign the constant |lland_constants.WASSER| to parameter
|lland_control.Lnk| and call our test object again to get the next results.

As mentioned initially, we try to cover the fundamental aspects of each
model but cannot expect to check everything.  So reading all of its
integration tests is a good starting point to understand a model.  After
that, you can perform alternative experiments yourself.  If you find your
analysis adds add valuable information to the existing test suite or even
reveals a shortcoming of the model, please do not hesitate to provide it
to us (see section :ref:`version_control`).
