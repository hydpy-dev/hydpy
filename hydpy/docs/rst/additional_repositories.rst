
.. _HydPy project page: https://github.com/hydpy-dev
.. _hydpy repository: https://github.com/hydpy-dev/hydpy
.. _Delft-FEWS-demos repository: https://github.com/hydpy-dev/Delft-FEWS-demos
.. _Delft-FEWS: https://oss.deltares.nl/web/delft-fews
.. _OpenDA repository: https://github.com/hydpy-dev/OpenDA
.. _OpenDA: http://openda.org/
.. _Dud: https://github.com/hydpy-dev/OpenDA/blob/master/demos/openda_projects/DUD/README.rst
.. _Travis CI: https://travis-ci.com/
.. _AppVeyor: https://www.appveyor.com/

.. _additional_repositories:

Additional repositories
_______________________

The `HydPy project page`_ does not only contain the `hydpy repository`_
itself, but also repositories for *HydPy* extensions.  At the time of
writing, there is the `Delft-FEWS-demos repository`_, providing
configuration files for using *HydPy* within `Delft-FEWS`_, and the
`OpenDA repository`_, providing a based wrapper wrapper for optimising
*HydPy* simulations with `OpenDA`_.  Additional repositories should be
created for all new *HydPy* functionalities not integrating naturally
into its source files.  The `OpenDA`_ wrapper, for example, must respect
both the logic of `OpenDA`_ and *HydPy*.  Programming such a wrapper
within the main `hydpy repository`_ would impair the consistency and
thus the maintainability of *HydPy*.

We cannot give clear recommendations on the design of additional
repositories, due to their potentially very diverse nature (for example,
the `Delft-FEWS-demos repository`_ is primarily XML based, and the
`OpenDA repository`_ is primarily Java based).  At least, try to
compile online documentation pages comparable to the ones of *HydPy*.
For example, we added linked *README* files to the subfolders of the
`OpenDA repository`_, which seems to be an acceptable lightweight alternative.
When following the *rst* file format instead of the commonly used *md*
file format, one can even include doctests into such *README* files,
as we did for explaining the `Dud`_ algorithm.  Ideally, one would also
test the code and build the sources on `Travis CI`_ or `AppVeyor`_, but t
here might be software or license restrictions preventing this.
