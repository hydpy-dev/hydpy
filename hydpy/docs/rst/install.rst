
.. _Python 3.6 or 3.7: https://www.python.org/downloads/
.. _numpy: http://www.numpy.org/
.. _netcdf4: http://unidata.github.io/netcdf4-python/
.. _Anaconda: https://www.anaconda.com/what-is-anaconda/
.. _Miniconda: https://conda.io/miniconda.html
.. _Spyder: https://www.spyder-ide.org/
.. _bokeh: https://bokeh.pydata.org/en/latest/
.. _conda: https://conda.io/docs/
.. _Python Package Index: https://pypi.org/project/HydPy/
.. _pip: https://pip.pypa.io/en/stable/
.. _releases: https://github.com/hydpy-dev/hydpy/releases
.. _issue: https://github.com/hydpy-dev/hydpy/issues
.. _GNU Compiler Collection: https://gcc.gnu.org/
.. _Windows Compilers page: https://wiki.python.org/moin/WindowsCompilers


.. _install:

Installation Instructions
=========================

Starting with version 3.0 *HydPy* is available on the
`Python Package Index`_.  That means, with `Python 3.6 or 3.7`_
on your computer and having access to the Internet, you only have
to type::

  pip install hydpy

into your command line tool to install the latest version of
*HydPy* on your computer.  `pip` then installs necessary
site-packages like `numpy`_ on-the-fly.  Optional site-packages
like `netcdf4`_ must be installed manually, as described below.

For 64 bit Windows, the `Python Package Index`_ provides so-called
"wheels", which include precompiled binaries and simplify
installing a lot. On Linux systems, you have to install "from
source" at the moment, as explained below.

Selecting a Python distribution
--------------------------------

Using *HydPy* requires installing `Python 3.6 or 3.7`_ first.  If you
are new to Python, we recommend installing a convenient Python distribution
like `Anaconda`_, already containing many scientific and mathematical tools
as well as the integrated development environment `Spyder`_.  A more
lightweight alternative would be to install `Miniconda`_ and use it
to install only the required libraries afterwards.  For example, if you want
to enable *HydPy* to read and write NetCDF files, you need to install
the `netcdf4`_ library::

   conda install netcdf4

Selecting a HydPy distribution
------------------------------

If you want to contribute to the development of  *HydPy* or implement
own models, please see the :ref:`development` section.  If you want to
apply *HydPy* only, you should start with a stable version available
under `releases`_.

Probably, you are interested in using the latest version of *HydPy*,
which is the one with the highest version number.  HydPy's version numbers
consist of three separate numbers. In "X.Y.Z.", "X" is the major number.
There can be important differences between *HydPy* versions with
different major numbers, possibly resulting in some incompatibility issues
with interfacing systems.  "Y" is the minor revision number, indicating
some improvements, but no potentially problematic changes, e.g. the
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
and uncompressed the `source code` archive in an arbitrary folder and open
the command line interface within the uncompressed `hydpy` folder.
Then write::

    python setup.py install

This command starts copying all available files to your site-packages folder
and generating the necessary system dependent binary files.  Additionally,
the testing system of *HydPy* is triggered. If everything works well,
you finally get the message::

    test_everything.py resulted in 0 failing unit test suites,
    0 failing doctest suites in Python mode and 0 failing doctest
    suites in Cython mode.

If a test suit fails, you get an additional warning message.  Then see
the more detailed test report above for additional information.
If there seems to be a severe problem, check if it is a known (and
possibly solved) `issue`_, already.  If not, please raise a new one.


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

















