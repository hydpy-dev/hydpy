
.. _Hutton et al.: https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2016WR019285
.. _docstrings: https://www.python.org/dev/peps/pep-0257
.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://www.sphinx-doc.org/en/master/
.. _doctests: https://docs.python.org/library/doctest.html
.. _unittest: https://docs.python.org/3/library/unittest.html
.. _run_doctests.py: https://github.com/hydpy-dev/hydpy/blob/master/hydpy/tests/run_doctests.py
.. _tests: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/tests
.. _coverage library: https://coverage.readthedocs.io
.. _Travis CI: https://travis-ci.com/
.. _Travis log-page: https://travis-ci.com/hydpy-dev/hydpy
.. _Pylint: https://www.pylint.org/

.. _tests_and_documentation:

Tests & documentation
_____________________

The scientific community broadly discusses the capabilities and shortcomings of
hydrological models from a theoretical point of view.  For example, many
sensitivity studies address the negative impacts of low data quality.  By
contrast, we unaware of any studies estimating the adverse effects of bugs and
misleading documentation of hydrological computer models.  With little
attention paid to these issues during evaluation processes (e.g. during
peer-review), there is a risk of publishing impaired model results, possibly
compromising the drawn conclusions.  See, for example, the commentary of
`Hutton et al.`_, addressing this topic from the scientific perspective.


This section describes strategies to limit the risk of serious errors and
outdated documentation.  We try to keep the code and the documentation in sync
by connecting them as strong as possible, using Python's "docstring" and
"doctest" features.

The first "connection" is writing each piece of the documentation close to the
related source code.  Therefore, we prefer to write all explanations addressing
specific HydPy features as `docstrings`_.  Docstrings are documentation strings
attached to the Python objects they explain.  When extending *HydPy*, it is a
strict requirement that each newly implemented public member (including the
sub-members, e.g. the user-available methods of a class) comes with its own
docstring.  Our `Travis CI`_ based continuous integration workflow recognises
any missing docstrings using `Pylint`_ and reports them as errors.

The second "connection" is to use and extend the functionalities of `Sphinx`_,
which collects the source code, the docstrings, and the usual documentation
files to generate the online documentation. `Sphinx`_ relies on the
`reStructuredText`_ format, hence follow this format when writing docstrings
and regular documentation files.  However, instead of using its regular
referencing style, make use of "substitutions" as defined by class |Substituter|
of module |autodoctools|.  Write, for example, the class name "Substituter"
within vertical bars to reference the corresponding class properly.  This short
syntax allows making frequent use of substitutions. A helpful side effect is
that, during the generation of the HTML pages, wrong substitutions result in
warnings, interpreted as errors by our `Travis CI`_ based continuous
integration workflow (see section :ref:`continuous_integration`).  This
mechanism  increases the chances that, when documentation adjustments do not
accompany future code changes, the `Travis CI`_ based workflow breaks, forcing
the responsible programmer to adapt the documentation.

The third "connection" is to define a sufficient number of `doctests`_.
Doctests are documentation sections containing valid Python code followed by
the expected results.  For developers, |doctest| is not always as convenient as
other unit testing frameworks (e.g. |unittest|), but it offers the great
advantage to defining tests that are understandable for non-programmers.  At
best, each (sub)member should specify its own doctests, in conjunction with
some "normal" explanations about its purpose and usage. Non-programmers should
be enabled to learn using *HydPy* by repeating the doctests.  Besides their
intuitiveness, doctests (like substitutions) offer the significant advantage of
keeping source code and documentation in sync.  For example, as long as the
following three-line doctest remains in the documentation, one can be sure that
the current core package contains a module named "objecttools":

    >>> from hydpy.core import objecttools
    >>> objecttools.classname(objecttools)
    'module'

The Python script `run_doctests.py`_ collects the doctests of all modules and
executes them.

We measure the "code coverage" (the number of executed code lines divided by
the total number of code lines), determined by the `coverage library`_.  The
current code coverage of *HydPy* is 100 %.  `Travis CI`_ reports all future
changes introducing uncovered lines as failures to make sure future changes do
not undo this favourable situation.
