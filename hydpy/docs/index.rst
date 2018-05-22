.. _Python: http://www.python.org/
.. _Cython: http://www.cython.org/
.. _`Ruhr-University Bochum`: http://www.hydrology.ruhr-uni-bochum.de/index.html.en
.. _`German Federal Institute of Hydrology`: http://www.bafg.de/EN/Home/homepage_en_node.html;jsessionid=E48E3BA5184A678BB2D23AD16AD5FC09.live21304
.. _`Björnsen Consulting Engineers`: https://www.bjoernsen.de/index.php?id=bjoernsen&L=2
.. _`GitHub repository`: https://github.com/tyralla/hydpy
.. _`GNU Lesser General Public License 3`: https://www.gnu.org/licenses/lgpl-3.0.en.html
.. _`documentation tests`: https://docs.python.org/3.6/library/doctest.html
.. _`Travis CI`: https://travis-ci.org/tyralla/hydpy/branches
.. _`example 13`: https://tyralla.github.io/hydpy/dam_v001.html#dam-v001-ex13
.. _Bokeh: https://bokeh.pydata.org/en/latest/
.. _`GitHub issue`: https://github.com/tyralla/hydpy/issues
.. _`Pull Request`: https://github.com/pulls

.. _HydPy:

HydPy
=====

:ref:`HydPy` is an interactive framework for developing and applying
different types of hydrological models.  It was originally developed
at the `Ruhr-University Bochum`_ for specific research purposes.
Later it was extended on behalf of the `German Federal Institute of
Hydrology`_ in order to be applicable in practical applications like
runoff forecasting in large river basins.  Now it is being maintained
by `Björnsen Consulting Engineers`_.

:ref:`HydPy` is intended to be a modern open source software.  It is based
on the programming language `Python`_, which is commonly used in
many scientific fields.  Through using different well-established
`Python`_ libraries and design principles, high quality and transparency
standards are targeted.  In order to avoid writing model cores (like
|lland_v1|) in a more native programming language, :ref:`HydPy` includes
a `Cython`_ based mechanism to automatically translate Python code to C
code and to compile it.

:ref:`HydPy` has no graphical user interface. Instead, :ref:`HydPy`
is controlled by  `Python`_ scripts.  These scripts help to increase
the reproducibility of studies performed with :ref:`HydPy`, because
they can be easily shared and repeatedly executed.  This facilitates
discussing possible weaknesses of :ref:`HydPy` and its implemented
models and comparing different methodical approaches (e.g. different
strategies to calibrate model parameters).  However, if you are not an
experienced hydrologist with basic programming skills, you may need
some help to become acquainted with :ref:`HydPy`.

:ref:`HydPy` is hosted in a `GitHub repository`_ and everyone
is allowed to download, modify, and use it.  But when passing the
(possibly modified) code to third parties, one has to be aware that
the selected `GNU Lesser General Public License 3`_ cannot be changed
to a "less open source" license.  This means that if you e.g.
implement your own model in :ref:`HydPy`, you can be sure that all
possible further developments of your model code are still open
source and the mentioned third parties are allowed to pass this
modified source code to you.

:ref:`HydPy` offers many functionalities to make the implemented
models as transparent and reliable as possible.  For this reason,
the online documentation is automatically updated for each new
:ref:`HydPy` version and includes  a `documentation tests` mechanism
thas ensures that :ref:`HydPy` is working properly and that the
documentation is actually up-to-date.

See for example the documentation of the (very simple) method
|lland_model.calc_nkor_v1|.  The text describes what the method does
and what input data it requires.  It is comprehensive but, as in common
documentations, technical reports and scientific articles, could be
outdated or be wrong in other ways.  This is not the case for the
example calculation shown in the green box.  This example is actual
`Python`_ code that shows how method |lland_model.calc_nkor_v1| can be
used and how different input values (for variables |lland_inputs.Nied|
and |lland_control.KG|) result in different output values (for variable
|lland_fluxes.NKor|).  Each time a new :ref:`HydPy` version is pushed
into the `GitHub repository`_, automatic test routines on `Travis CI`_
are trigged.  The new :ref:`HydPy` version is rejected, if the
actual |lland_model.calc_nkor_v1| method does not result in the exact
same output values as given in the last line of the example.

Such basic "unit tests" should provide a good basis for discussing the
proper implementation of certain hydrological processes.  But they
are no proof a complete model is actually working well.  Therefore
:ref:`HydPy` also offers some "integration test" functionalities.

Each integration test should demonstrate how a certain model could be
set up meaningfully.  Ideally, the model configuration should be varied
to show different aspects of its functionality.  See e.g. `example 13`_
of the documentation on model |dam_v001|, which discusses the implemented
flood retention routine.  Here, example calculations are performed for a
period of 20 days, and for each day all input and output values, as well
as all internal states (e.g. the |dam_states.WaterVolume|), are tabulated.
Again, `Travis CI`_ checks that all of these values are exactly recalculated
by each new :ref:`HydPy` version.  Additionally, the tabulated values are
shown in a `Bokeh`_ plot, which is also updated for each new :ref:`HydPy`
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
:ref:`HydPy` versions that still contain this flaw.

We hope to have made clear that the design of :ref:`HydPy` focusses
on open collaboration in order to improve existing and to develop
better models.  The :ref:`development` section offers more information
on how to actually participate in the further development of :ref:`HydPy`.
Section :ref:`modelcollection` lists all models implemented so far.
Sections :ref:`core` covers the basic functionalities of the
:ref:`HydPy` framework.  We hope to be able to offer some beginner
:ref:`tutorials` based on real data soon.

.. toctree::
   :hidden:

   framework
   modelcollection
   tutorials
   development


