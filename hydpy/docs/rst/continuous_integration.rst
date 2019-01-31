.. _GitHub: https://github.com
.. _Travis CI: https://travis-ci.com/
.. _Travis CI project: https://travis-ci.org/hydpy-dev/hydpy
.. _GitHub repository: https://github.com/hydpy-dev/hydpy
.. _online documentation: https://hydpy-dev.github.io/hydpy/
.. _test future Python: https://snarky
.. _Sphinx: http://www.sphinx-doc.org/en/stable/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _travis-sphinx: https://github.com/Syntaf/travis-sphinx
.. _gh-pages branch: https://github.com/hydpy-dev/hydpy/tree/gh-pages
.. _master branch: https://github.com/hydpy-dev/hydpy/tree/master
.. _Coverage.py: https://coverage.readthedocs.io/en/coverage-4.3.4/

.. _continuous_integration:

Continuous Integration
______________________

To improve the code base of HydPy, you need your own working copy
(your own fork, see section :ref:`version_control`).  The existence
of multiple working copies inevitably leads to the danger of
integration problems, meaning that different changes in different
working copies lead to source code incompatibilities.  To reduce
this risk, the different working copies should be merged `continuously`.
This decreases the likelihood of simultaneous changes to the same
code sections and keeps the complexity of possible conflicts to
a minimum.

The current (online) development of HydPy relies, besides `GitHub`_,
on `Travis CI`_.  `Travis CI`_ is a hosted, distributed continuous
integration service.  This `Travis CI project`_ has been linked
to HydPy's `GitHub repository`_.  It is configured to accomplish
the following tasks for each new commit or pull request:

  * Install HydPy on the Debian based Linux operating system Ubuntu using
    different versions of CPython.
  * Cythonize all implemented models on the different Python versions.
  * Execute all `conventional` unit tests and all doctests on the
    different Python versions.
  * Prepare a `Test Coverage`_ report based on Python 2.7.
  * Update this `online documentation`_ based on Python 2.7.

Installation and testing are performed using Python 2.7, 3.4, 3.5 and 3.6.
2.7 still seems to be the Python version most frequently used by scientists.
Python versions 3.0 to 3.3 do not seem to be of great importance anymore.
Additionally, installation and testing are performed using the development
branches of version 3.5, 3.6 and (the still not released) version 3.7.
This offers the advantage of anticipating future problems and to
`test future Python`_ itself, possibly helping to avoid future bugs.

Whenever one single test fails under one single Python version, the total
process (build) is regarded as defective and will not be merged into
the master branch of the main fork.  The same is true, of course, when
one installation process itself fails.  So make sure all your changes
are compatible with each selected Python version.  But, in accordance with
one of Python's principle, it is easier to ask for forgiveness than
permission: let Travis evaluate your current working branch and see what
happens...

Not only the source code but also the contributed documentation
text is checked in two ways. Doctesting is discussed above and always
performed using each mentioned Python version.  Additionally, when
using  Python 2.7 the properness of the whole documentation text is
considered. `Sphinx`_ is applied to create the HTML pages of this
`online documentation`_ based on the given `reStructuredText`_ files.
In case problems occur, e.g. due to faulty inline markup, the
total build (including all Python versions) is regarded as defective.
This assures that each new HydPy version is accompanied by a
functioning online documentation.  If nothing goes wrong, the
`travis-sphinx`_ script is used to push the final HTML pages to the
`gh-pages branch`_ automatically, meaning, that this
`online documentation`_ is updated immediately.  This deploy process
is restricted to the `master branch`_ of the main development line
and has disabled pull request option for safety reasons.

Test Coverage
-------------

This is the :download:`latest coverage report <coverage.html>`.

One can never be sure, that all important aspects of a software
application are checked properly (instead, one can be quite certain,
one has always missed something...).  However, one can at least evaluate
the runtime behaviour of the tests themselves in order to find out
which code sections they do invoke and which not.  HydPy's
`Travis CI project`_ has been configured to perform such an evaluation
automatically for each build process based on `Coverage.py`_.  The
resulting HTML report is linked to this `online documentation`_
automatically.

The coverage report does only include modules with a percentage
coverage less than 100 %, as only those need further attention.
If a code section is covered one can at least be sure, that it does
not cause an unhandled exception or a total program crash on the
applied Python versions. But one cannot be sure, that the test(s)
actually covering the code section are meaningful.

Note that the coverage analysis is performed on Python 2.7 only.
Hence code sections only relevant for Python 3 might be reported
as uncovered erroneously.
