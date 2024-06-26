.. _Python: http://www.python.org/
.. _Cython: http://www.cython.org/
.. _`Ruhr-University Bochum`: http://www.hydrology.ruhr-uni-bochum.de/index.html.en
.. _`German Federal Institute of Hydrology`: https://www.bafg.de/EN
.. _`Björnsen Consulting Engineers`: https://www.bjoernsen.de/en/bjoernsen-consulting-engineers
.. _`GitHub repository`: https://github.com/hydpy-dev/hydpy
.. _`GNU Lesser General Public License 3`: https://www.gnu.org/licenses/lgpl-3.0.en.html
.. _`documentation test`: https://docs.python.org/3.6/library/doctest.html
.. _`Travis CI`: https://travis-ci.com/hydpy-dev/hydpy/branches
.. _`AppVeyor`: https://ci.appveyor.com/project/tyralla/hydpy/history
.. _`example 13`: https://hydpy-dev.github.io/hydpy/master/dam_v001.html#dam-v001-ex13
.. _Plotly: https://plotly.com/python/
.. _`GitHub issue`: https://github.com/hydpy-dev/hydpy/issues
.. _`Pull Request`: https://github.com/pulls

.. _HydPy:

Introduction
============

*HydPy* is an interactive framework for developing and applying
different types of hydrological models, originally developed
at the `Ruhr-University Bochum`_ for specific research purposes.
Later it was extended on behalf of the `German Federal Institute of
Hydrology`_ to be applicable in practical applications like runoff
forecasting in large river basins.  Now it is being maintained by
`Björnsen Consulting Engineers`_.

*HydPy* is intended to be a modern open source software, based
on the programming language `Python`_, commonly used in many scientific
fields.  Through using different well-established `Python`_ libraries
and design principles, we target high quality and transparency standards.
To avoid writing model cores (like |lland_dd|) in a more native
programming language, *HydPy* includes a `Cython`_ based mechanism
to automatically translate Python code to C code and to compile it.

*HydPy* has no graphical user interface. Instead, it is thought to
be applied by executing Python scripts.  These scripts help to increase
the reproducibility of studies performed with *HydPy* because
they can be easily shared and repeatedly executed.  This approach facilitates
discussing possible weaknesses of *HydPy* and its implemented
models and comparing different methodical approaches (e. g. different
strategies to calibrate model parameters).  However, if you are not an
experienced hydrologist with basic programming skills, you may need
some help to become acquainted with *HydPy*.

We host *HydPy* in a `GitHub repository`_ and everyone
is allowed to download, modify, and use it.  However, when passing the
(possibly modified) code to third parties, one has to be aware that
the selected `GNU Lesser General Public License 3`_ cannot be changed
to a "less open source" license.  If you, for example, implement a new
model into *HydPy*, you can be sure that all possible further
developments of your model code are still open source and the mentioned
third parties are allowed to pass this modified source code to you.

*HydPy* offers many functionalities to make the implemented
models as transparent and reliable as possible.  For this reason,
the online documentation is automatically updated for each new
*HydPy* version and includes different `documentation test`_
mechanism ensuring that *HydPy* is working as expected and
that the documentation is up-to-date with it.

See for example the documentation of the (very simple) method
|lland_model.Calc_NKor_V1|.  The text describes what the method does
and what input data it requires.  It is comprehensive but, as in common
documentations, technical reports and scientific articles, could be
outdated or be wrong in other ways.  This is not the case for the
example calculation shown in the green box.  This example is actual
`Python`_ code that shows how method |lland_model.Calc_NKor_V1| can be
used and how different input values (for variables |lland_inputs.Nied|
and |lland_control.KG|) result in different output values (for variable
|lland_fluxes.NKor|).  Each time a new *HydPy* version is pushed
into the `GitHub repository`_, automatic test routines on `Travis CI`_ and
`AppVeyor`_  are trigged.  The new *HydPy* version is rejected, if the
actual |lland_model.Calc_NKor_V1| method does not result in the exact
same output values as given in the last line of the example.

Such basic "unit tests" should provide a good basis for discussing the
proper implementation of certain hydrological processes.  But they
are no proof a complete model is actually working well.  Therefore
*HydPy* also offers some "integration test" functionalities.

Each integration test should demonstrate how a certain model could be
set up meaningfully.  Ideally, the model configuration should be varied
to show different aspects of its functionality.  See e.g. `example 13`_
of the documentation on model |dam_v001|, which discusses the implemented
flood retention routine.  Here, example calculations are performed for a
period of 20 days, and for each day all input and output values, as well
as all internal states (e.g. the |dam_states.WaterVolume|), are tabulated.
Again, `Travis CI`_ checks that all of these values are exactly recalculated
by each new *HydPy* version.  Additionally, the tabulated values are
shown in a `Plotly`_ plot, which is also updated for each new *HydPy*
version automatically.  You can click on the variables and zoom into some
details you are actually interested in.

If there were some methodical or technical flaws in the retention routine
of |dam_v001|, you would have good chances to find them when reading the
documentation critically.  You could tell us about your finding via a
`GitHub issue`_, allowing us or others to read (and at best solve) the
problem.  Or you could try to solve it on your own and offer your solution
as a `Pull Request`_.  You could also add a new test to the documentation
files to prove that something goes wrong and offer it via a
`Pull Request`_, which would enable `Travis CI`_ to reject future
*HydPy* versions that still contain this flaw.

We hope to have made clear that the design of *HydPy* focusses
on open collaboration in order to improve existing and to develop
better models.  The :ref:`development` section offers more information
on how to actually participate in the further development of *HydPy*.
Section :ref:`model_families` lists all models implemented so far.
Sections :ref:`core` covers the basic functionalities of the
*HydPy* framework.

.. toctree::
   :hidden:

   installation
   example_projects
   quickstart
   user_guide
   development
   reference_manual
   Bibliography <zbibliography>


