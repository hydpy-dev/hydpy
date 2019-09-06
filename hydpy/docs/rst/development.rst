.. _hydpy package: https://pypi.org/project/HydPy
.. _Python Package Index: https://pypi.python.org/pypi
.. _hydpy repository: https://github.com/hydpy-dev/hydpy
.. _GitHub: https://github.com
.. _pandas: http://pandas-docs.github.io/pandas-docs-travis/contributing.html

.. _development:

Development
===========

When applying *HydPy*, you can download it from the `hydpy package`_
available on the `Python package index`_ and install it with little effort.
There is a considerable  amount of Python tools freely available, being
of great help when trying to achieve more complex tasks like parameter
calibration or regionalisation.  Cherry picking from different Python
packages can be a substantial  time-saving.  Very often it is not necessary
to write a "real" Python program for the task at hand.  Instead, writing a
simple script utilising functionalities of different packages in the correct
order often gets the job done.

There is also nothing stopping you from modifying the downloaded Python
files in your favour.  You are free to modify existing models, implement
new ones,or change the framework's structure in a manner that meets your
personal goals and preferences.

However, if you intend to contribute to the further development of *HydPy*,
you must abandon some parts of freedom and ease of use Python offers.
First, you must become acquainted with the collaborative development of the
`hydpy repository`_, primarily taking place on `GitHub`_.  Second, you
need to follow some guidelines on the development of *HydPy*.  The Python
code contributed by different developers should be as consistent as possible.
Otherwise, there would be a risk of the code base becoming opaque (or
even faulty), impeding future extensions of *HydPy*.


The following sections try to define a strategy allowing to develop *HydPy*
as an open source project while maintaining sufficiently high quality for
scientific and engineering applications.  The hydrological modelling
community has not made much progress in this field yet, which is why we
adopted many concepts from non-hydrological open source projects like
`pandas`_.  Ideas and discussions on improving the outlined strategy are
welcome!

.. toctree::

   required_tools
   version_control
   hydpydependencies
   continuous_integration
   tests_and_documentation
   programming_style
   additional_repositories
