
.. _Python Package Index: https://pypi.org/project/HydPy/
.. _Python 3.7, 3.8, or 3.9: https://www.python.org/downloads/
.. _numpy: http://www.numpy.org/
.. _Kalypso: https://kalypso.bjoernsen.de/index.php?id=382&L=1
.. _Delft-FEWS: https://oss.deltares.nl/web/delft-fews
.. _releases: https://github.com/hydpy-dev/hydpy/releases
.. _PyCharm: https://www.jetbrains.com/pycharm/download/#section=windows
.. _Anaconda: https://www.anaconda.com/what-is-anaconda/
.. _IDLE: https://docs.python.org/3/library/idle.html
.. _Spyder: https://www.spyder-ide.org/
.. _pip: https://pip.pypa.io/en/stable/
.. _releases: https://github.com/hydpy-dev/hydpy/releases
.. _issue: https://github.com/hydpy-dev/hydpy/issues
.. _GNU Compiler Collection: https://gcc.gnu.org/
.. _Windows Compilers page: https://wiki.python.org/moin/WindowsCompilers


.. _install:

Installation Instructions
=========================

Starting with version 3.0 *HydPy* is available on the `Python Package Index`_.
That means, with `Python 3.7, 3.8, or 3.9`_ on your computer and having access
to the internet you only have to type::

  pip install hydpy

into your command-line tool to install the latest version of *HydPy* on your
computer.  `pip` then installs necessary site-packages like `numpy`_ on-the-fly.

For 64 bit Windows, the `Python Package Index`_ provides so-called "wheels",
which include pre-compiled binaries and simplify installing a lot.  On Linux
systems, you have to install "from source" at the moment, as explained below.

Starting with version 4.0 *HydPy* also comes as an installer for Windows,
including Python itself and all required and optional dependencies.
You may find it useful if new to Python and want to check out *HydPy*
before installing a complete Python distribution, or if you are afraid to
mess up your current Python installation (but then you should probably
prefer to work in a virtual environment).  Additionally, the closedness
of the installer might be preferable when coupling *HydPy* to other
software systems such as `Kalypso`_ or `Delft-FEWS`_.  See `releases`_
for the latest version of the *HydPy* installer.


Selecting a Python distribution
--------------------------------

Using *HydPy* requires installing `Python 3.7, 3.8, or 3.9`_ first.  You should
favour the latest Python version unless you plan to use other libraries still
only available for earlier versions.  Alternatively, consider installing a more
comprehensive Python distribution like `Anaconda`_, already containing many
scientific and mathematical tools.

Note that these Python distributions do not include the most powerful
integrated development environments.  For simple tasks, the lightweight IDE
`IDLE`_ of the original Python distribution might be sufficient.  `Anaconda`_
also comes with `Spyder`_, which helps to structure medium-sized projects.
External IDEs like `PyCharm`_, on the other hand, offer significantly more
comfort, so that the initial installation and configuration effort required
should quickly pay for itself.


Selecting a HydPy distribution
------------------------------

If you want to contribute to the development of  *HydPy* or implement
new models, please see the :ref:`development` section.  If you want to
apply *HydPy* only, you should start with a stable version available
under `releases`_.

You are probably interested in using the latest version of *HydPy*,
which is the one with the highest version number.  HydPy's version numbers
consist of three separate numbers. In "X.Y.Z.", "X" is the major number.
There can be substantial differences between *HydPy* versions with
different major numbers, possibly resulting in incompatibility issues
with interfacing systems.  "Y" is the minor revision number, indicating
some improvements, but no potentially problematic changes, e. g. the
implementation of additional models.  "Z" is the revision number,
indicating some necessary corrections of the framework or its implemented
models.  In any case, you should make sure to select the highest revision
number available, meaning you should prefer using "X.Y.1" over "X.Y.0".

Each release is available in different compressed archives,
corresponding to different environments.  Currently, we distribute
pre-compiled binaries for 64-bit Windows only (see above).
For all other operating systems and Python versions, you have to build
binaries yourself.  Principally, this should be simple, but Windows users
might need to install the suitable compiler first (see below).  Download
and uncompress the `source code` archive in an arbitrary folder and open
the command line interface within the uncompressed `hydpy` folder.
Then write::

    python setup.py install

This command starts copying all available files to your site-packages folder
and generating the necessary system-dependent binary files.  Additionally,
the testing system of *HydPy* is triggered. If everything works well,
you finally get the message::

    test_everything.py resulted in 0 failing unit test suites,
    0 failing doctest suites in Python mode and 0 failing doctest
    suites in Cython mode.

If a test suit fails, you get an additional warning message.  Then see the
more detailed test report above for further information.  If there seems to
be a severe problem, check if it is already a known (and possibly solved)
`issue`_.  If not, please raise a new one.


Selecting a C Compiler
----------------------

You only need to care about selecting a C compiler, if no pre-compiled
binaries are available for your system or if you want to implement
new models into the *HydPy* framework.  Also, Linux users should
have no trouble, as the `GNU Compiler Collection`_ is ready for
use on standard Linux distributions.  Unfortunately, Windows does not
include compilers by default.  Search `Windows Compilers page`_ on how
to select and install the correct compiler.

After installing the required compiler successfully on Windows, you
might eventually have to deal with the **unable to find vcvarsall.bat**
problem.  `vcvarsall` is a batch file Python needs to control the installed
Visual Studio compiler.  Find this file on your system and set a new
system variable pointing to its path.  A quick search on the internet
should provide you with the required information.

















