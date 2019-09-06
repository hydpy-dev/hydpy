.. _GitHub: https://github.com
.. _Travis CI: https://travis-ci.com/
.. _AppVeyor: https://www.appveyor.com/
.. _hydpy repository: https://github.com/hydpy-dev/hydpy
.. _Travis log-page: https://travis-ci.org/hydpy-dev/hydpy
.. _AppVeyor log-page: https://ci.appveyor.com/project/tyralla/hydpy/history
.. _travis.yml: https://github.com/hydpy-dev/hydpy/blob/master/.travis.yml
.. _setup.py: https://github.com/hydpy-dev/hydpy/blob/master/setup.py
.. _GitHub pages: https://pages.github.com/
.. _appveyor.yml: https://github.com/hydpy-dev/hydpy/blob/master/appveyor.yml
.. _Python Package Index: https://pypi.org/project/HydPy/

.. _continuous_integration:

Continuous Integration
______________________

To contribute to the code base of *HydPy*, you need a copy of its sources
(a separate fork, see section :ref:`version_control`).  The existence
of multiple copies of the same code bears the danger of integration problems
due to incompatible changes.  An obvious problem is when two developers
introduce different changes to the same code lines. However, even untuned
changes in separate code sections can break functionalities.  As a means to
reduce such risks, different working copies should be synchronised
"continuously".  Taking the code changes of colleagues into account as often
as possible decreases the likelihood of simultaneous changes to the same code
sections and keeps the complexity of possible conflicts to a minimum.

The online development of *HydPy* relies, besides `GitHub`_, on `Travis CI`_
and `AppVeyor`_.  Both are a hosted, distributed continuous integration
services.  They are configured to check and eventually release new *HydPy*
versions in different ways.  Each time someone suggests changes to the
`hydpy repository`_, either via a direct commit or a pull request (see
section :ref:`version_control`), `GitHub`_ sends a message to the servers of
`Travis CI`_ and `AppVeyor`_.  They then download the new source code,
examine it, and log their results to the `Travis log-page`_ and the
`AppVeyor log-page`_, respectively.

`travis.yml`_ defines the following `Travis CI`_ workflow:

  * Download and install all *HydPy* dependencies on the Debian based
    Linux operating system Ubuntu separately for each currently
    supported CPython version.
  * Call `setup.py`_ to copy *HydPy* to the site-packages folder and
    build some additional files (e.g. Dynamic Link Library files).
    For reasons of measuring code coverage, `setup.py`_ also triggers
    all "conventional" unit tests and doctests.
  * Prepare a test coverage report (see section :ref:`tests_and_documentation`).
  * Generate the online documentation (for the latest stable Python version).
  * Publish the online documentation on `GitHub pages`_ in case the
    build process succeeded, all tests passed, and no formatting errors
    or wrong links corrupted the documentation. Additionally, the evaluated
    branch must be the master branch.

The workflow defined by `appveyour.yml` is as follows:

  * As on `Travis CI`_, download and install all *HydPy* dependencies for
    each supported CPython version, but on Windows Server instead of Linux.
  * As on `Travis CI`_, call `setup.py`_ to install *HydPy*, but do not
    measure code coverage.
  * Create binary distributions for the respective Python versions based
    on the extension files generated in the last step.
  * Remove the already installed files, reinstall *HydPy* based on the
    new binary distributions, and apply all tests.
  * Make all artefacts available (currently, besides the binary distributions,
    the automatically generated XML schema files).
  * Upload the binary distributions to the `Python Package Index`_  for
    tagged commits in case all tests passed.

Together, both continuous integration services capture a wide range
of possible problems, not only addressing the implemented hydrological
models, but also the release and documentation cycles.  If applied
regularly, chances are good to trace unexpected errors to specific code
changes.  Additionally, `Travis CI`_ and `AppVeyor`_ help you to decide
if contributions by colleagues are mature enough to be merged in your code.
