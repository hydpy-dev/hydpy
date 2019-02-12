.. _Python Standard Library: https://docs.python.org/library/
.. _setup.py: https://github.com/hydpy-dev/hydpy/blob/master/setup.py
.. _NumPy: http://www.numpy.org/
.. _SciPy: https://www.scipy.org/
.. _wrapt: https://wrapt.readthedocs.io/en/latest/
.. _netCDF4 module: http://unidata.github.io/netcdf4-python/
.. _NetCDF-CF: http://cfconventions.org/Data/cf-conventions/cf-conventions-1.7/cf-conventions.html
.. _hydpy __init__.py file: https://github.com/hydpy-dev/hydpy/blob/master/hydpy/__init__.py
.. _coverage library: https://coverage.readthedocs.io
.. _requirements.txt: https://github.com/hydpy-dev/hydpy/blob/master/requirements.txt
.. _Sphinx: http://www.sphinx-doc.org/en/master/
.. _conf.py: https://github.com/hydpy-dev/hydpy/blob/master/hydpy/docs/sphinx/conf.py

.. _hydpydependencies:

Dependencies
____________

As mentioned at the beginning of the :ref:`development` section, using
multiple Python libraries without questioning their maturity and
long-term stability can be a huge time-saver when compiling Python scripts
as ad-hoc solutions for complex problems.  However, we have to be more
cautious when including external libraries into our core code.  In general,
we should keep the number of imported libraries low and avoid libraries
with significant shortcomings or uncertain future support.  Otherwise,
we risk the long-term stability of *HydPy* itself.  Whenever reasonable,
import only packages of the `Python Standard Library`_, or at least
restrict yourself to reliable, mature and stable site-packages.

In the development of *HydPy*, we consider three groups of site-packages:
**required** dependencies, **optional** dependencies, and dependencies
only relevant for **development**.

"Required dependencies" are site-packages being imported within
each *HydPy* application by necessity.  See the "install_requires"
argument within the `setup.py`_ file for the current list of required
dependencies.  At the time of writing these are only the highly
accepted and easily installable site-packages `NumPy`_, `SciPy`_, and
`wrapt`_, providing essential features not available within the
`Python Standard Library`_.

"Optional dependencies" are site-packages needed for specific *HydPy*
features only.  One good example is the `netCDF4 module`_.  The first
reason for declaring this site-package optional is its limited scope for
reading and writing `NetCDF-CF`_ time series files.  Users can choose other
file formats as well.  The second reason is that its installation is not
always working smoothly.  See the documentation on class |OptionalImport|
on how to define optional imports.

"Development dependencies" are site-packages relevant for framework or
model developers only.  One example is the `coverage library`_, checking
whether the available tests execute certain source code lines or not.  The
`requirements.txt`_ file lists most development dependencies.  Additionally,
we rely on `Sphinx`_ in conjunction with its extensions listed in `conf.py`_
for generating the HTML documentation.
