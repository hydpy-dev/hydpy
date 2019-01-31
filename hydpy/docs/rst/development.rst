.. _hydpy package: https://pypi.org/project/HydPy
.. _Python Package Index: https://pypi.python.org/pypi
.. _GitHub repository: https://github.com/hydpy-dev/hydpy
.. _GitHub: https://github.com
.. _pandas: http://pandas-docs.github.io/pandas-docs-travis/contributing.html

.. _development:

Contributing to HydPy
=====================

You can install HydPy from the `hydpy package`_ available on the
`Python package index`_ or fork from this `GitHub repository`_ available
on `GitHub`_.  Afterwards, you can implement your own models or
change the framework's structure in a manner that meets your personal
goals and preferences.  There are many other Python tools freely
available, which will be of great help while trying to achieve more
complex tasks like parameter calibration or regionalization.  Cherry
picking from many different Python packages can be a huge time-saving.
Very often it is not necessary to write a "real" Python program.
Instead, just writing a simple script calling different functionalities
of different packages in the correct order often gets the job done.

However, if you intend to contribute to the further development of HydPy
(hopefully you will!), you must abdicate some parts of the freedom and
ease of use Python offers.  The number of dependencies to other Python
packages, in particular those with some relevant shortcomings and those
which might not be further supported in the future, should be kept as
small as possible.  Otherwise, it would be too hard to guarantee the
long-term applicability of HydPy.  Additionally, the Python code
contributed by different developers should be as consistent as possible.
Otherwise, there would be a risk of the code base becoming opaque, making
future extensions of HydPy impossible.

The following sections try to define a strategy allowing HydPy to be
developed as an open source project while maintaining sufficiently
high-quality standards for practical applications.  The hydrological
modelling community has not made that much progress in this field yet.
This is why the outlined strategy is highly influenced by other
non-hydrological open source projects like `pandas`_.  Discussions on
how to improve the outlined strategy are welcome!

.. toctree::
   :hidden:

   development_environment
   version_control
   hydpydependencies
   continuous_integration
   tests_and_documentation
   programming_style
   additional_repositories
