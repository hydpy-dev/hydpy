
.. _LARSIM: http://www.larsim.info/1/the-model/

.. _modelcollection:

Model Collection
================

In :ref:`HydPy`, many models are devided into groups (e.g. :ref:`HydPy-L`)
and subgroups (e.g. :ref:`HydPy-L-Land`).

The existence of the groups is primarily due to historical reasons.
For example, all subgroups related to the orginal `LARSIM`_ model are
part of group :ref:`HydPy-L`, despite their different functionality
(:ref:`HydPy-L-Land` for modelling "land processes", :ref:`HydPy-L-Stream`
for modelling "stream processes", and :ref:`HydPy-L-Lake` for modelling
"lake processes").

The seperation into subgroups is of greater importance.  Each subgroup
(e.g. :ref:`HydPy-L-Land`) consists of one base model (e.g.
:mod:`~hydpy.models.lland`) and a number of application models
(e.g. :mod:`~hydpy.models.lland_v1`).  The base models offer basic
features like model parameter classes (e.g.
:class:`~hydpy.models.lland.lland_control.KG`), sequence classes (e.g.
:class:`~hydpy.models.lland.lland_fluxes.NKor`) and process
equation methods (e.g. :func:`~hydpy.models.lland.lland_model.calc_nkor_v1`),
but cannot perform an actual simulation run.  This is the task
of the application models, which select different parameters, sequences,
and process equations in a meaningful combination and order.

If not stated otherwise, all models can be freely combined and applied
on arbitrary simulation time steps.  It is, for example, possible to simulate
the "land processes" with :mod:`~hydpy.models.hland_v1`, the "stream
processes" with :mod:`~hydpy.models.arma_v1`, the "lake processes" with
":mod:`~hydpy.models.llake_v1` in either a daily or hourly time step.

Often base models offer different versions of a method to calculate the
value of the same variable.  For example, base model
:mod:`~hydpy.models.hland` offers two methods for calculating
:class:`~hydpy.models.lland.lland_fluxes.ET0`:
:func:`~hydpy.models.lland.lland_model.calc_et0_v1` and
:func:`~hydpy.models.lland.lland_model.calc_et0_v2`.  Each application
model has to select a specific version of the method.  For example,
application model :mod:`~hydpy.models.hland_v1` selects
:func:`~hydpy.models.lland.lland_model.calc_et0_v1`...

>>> from hydpy.models.lland_v1 import *
>>> parameterstep('1d')
>>> model.calc_et0_v1
<function Model.calc_et0_v1>

...but not :func:`~hydpy.models.lland.lland_model.calc_et0_v2`:

>>> model.calc_et0_v2
Traceback (most recent call last):
...
AttributeError: 'Model' object has no attribute 'calc_et0_v2'

For simplicity, you can skip the version number when trying to access
a certain method of an application model:

>>> model.calc_et0
<function Model.calc_et0>

Note that this way to construct different application models is very
different from the usual design of hydrological models, where only
one model exists.  Here it is the responsibility of the user to combine
different possible methods in a meaningful combination, usually via
setting some options in configuration files.

In the light of experience that model users are often overstrained with
such decisions when using complex models and that it is often very hard to
communicate (and remember) all selected settings, we favour the more
reliable "application model" approach.  This allows the model developer to
carefully check the combination of methods he selected by himself
in thorough integration tests.  And it allows him to document how he
thinks the application model should actually be used.  On the downside,
eventually many application models must be compiled in order to support
different combinations of methods.  To keep this problem small, newly
implemented models should be kept small.  But this also depends on
other design decisions (e.g. how process equations are numerically solved)
and will have to be discussed later.

.. toctree::
   :hidden:

   HydPy-A
   HydPy-D
   HydPy-H
   HydPy-L


