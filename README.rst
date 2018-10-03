.. _online documentation: https://tyralla.github.io/hydpy/
.. _Python: http://www.python.org/
.. _Cython: http://www.cython.org/
.. _`Ruhr-University Bochum`: http://www.hydrology.ruhr-uni-bochum.de/index.html.en
.. _`German Federal Institute of Hydrology`: http://www.bafg.de/EN/Home/homepage_en_node.html;jsessionid=E48E3BA5184A678BB2D23AD16AD5FC09.live21304
.. _`Björnsen Consulting Engineers`: https://www.bjoernsen.de/index.php?id=bjoernsen&L=2
.. _`GitHub repository`: https://github.com/tyralla/hydpy
.. _`GNU Lesser General Public License 3`: https://www.gnu.org/licenses/lgpl-3.0.en.html
.. _`documentation tests`: https://docs.python.org/3.6/library/doctest.html

A Python framework for the development and application of hydrological models

*HydPy* is an interactive framework for developing and applying
different types of hydrological models.  It was originally developed
at the `Ruhr-University Bochum`_ for specific research purposes.
Later it was extended on behalf of the `German Federal Institute of
Hydrology`_ in order to be applicable in practical applications like
runoff forecasting in large river basins.  Now it is being maintained
by `Björnsen Consulting Engineers`_.


*HydPy* is intended to be a modern open source software, based
on the programming language `Python`_, commonly used in
many scientific fields.  Through using different well-established
`Python`_ libraries and design principles, we target high quality and
transparency standards.  In order to avoid writing model cores (like
|lland_v1|) in a more native programming language, *HydPy* includes
a `Cython`_ based mechanism to automatically translate Python code to C
code and to compile it.

*HydPy* has no graphical user interface (so far). Instead, it is thought
to be applied by executing Python scripts. These scripts help to increase
the reproducibility of studies performed with :ref:`HydPy` because
they can be easily shared and repeatedly executed.  This approach facilitates
discussing possible weaknesses of :ref:`HydPy` and its implemented
models and comparing different methodical approaches (e. g. different
strategies to calibrate model parameters).  However, if you are not an
experienced hydrologist with basic programming skills, you may need
some help to become acquainted with :ref:`HydPy`.

We host *HydPy* in a `GitHub repository`_ and everyone
is allowed to download, modify, and use it.  However, when passing the
(possibly modified) code to third parties, you have to be aware you
cannot change the selected `GNU Lesser General Public License 3`_
to a "less open source" license.  This means that if you, for example,
implement your own model in *HydPy*, you can be sure that all
possible further developments of your model code are still open
source and the mentioned third parties are allowed to pass this
modified source code to you.

*HydPy* offers many functionalities to make the implemented
models as transparent and reliable as possible.  For this reason,
the online documentation is automatically updated for each new
*HydPy* version and includes  a `documentation tests` mechanism
ensuring that *HydPy* is working properly and that the
documentation is actually up-to-date.

Please see the `online documentation`_ for in-depth information.
