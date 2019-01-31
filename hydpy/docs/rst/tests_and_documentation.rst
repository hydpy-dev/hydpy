.. _mock object library: https://docs.python.org/3/library/unittest.mock.html
.. _reStructuredText: http://docutils.sourceforge.net/rst.html

.. _tests_and_documentation:

Tests & documentation
_____________________

From a theoretical or even a philosophical point of view, the
capabilities and shortcomings of hydrological modelling have been
discussed thoroughly.  The negative impacts of low data quality
are addressed by many sensitivity studies.  By contrast, we are not
aware of any study focussing on the compromising effects of bugs
and misleading code documentation of hydrological computer models.
(Of course, such a study would be hard to conduct due to several
reasons.) Given the little attention paid during the peer-review
process to the correctness of model code and its transparent
documentation, the danger of scientific results being corrupted
by such flaws can --- carefully worded --- at least not be ruled
out.

This sections describes strategies on how to keep the danger
of severe bugs and outdated documentation to a (hopefully)
reasonable degree.

Conventional Unit-Tests
-----------------------

After installing HydPy through executing the `setup.py` module with
the argument `install`, the script `test_everything` is executed as well.
The first task of the latter module is to perform all `conventional`
unit tests.  Therefore, all modules within the subpackage `tests` named
'unittests_*.py' are evaluated based on the unit testing framework
|unittest| of Pythons standard library.  Each new HydPy module should
be complemented by a corresponding unittest file, testing its functionality
thoroughly.  Just write test classes in each unittest file.  These are
evaluated automatically by the script `test_everything`.  Let each class
name  start with 'Test', a consecutive number, and a description of the
functionality to be testet.  Each test class must inherit from
|unittest.TestCase|, allowing for using its assert methods.  Last but not
least, add the different test methods.  Again, each name should start with
'test' and a consecutive number, but this time in lower case letters
separated by underscores. By way of example, consider a snipplet of the
test class for the initialization of |Date| objects:

    >>> import unittest
    >>> import datetime
    >>> from hydpy.core import timetools
    >>> class Test01DateInitialization(unittest.TestCase):
    ...     def setUp(self):
    ...         self.refdate_day = datetime.datetime(1996, 11, 1)
    ...         self.refdate_hour = datetime.datetime(1996, 11, 1, 12)
    ...     def test_01_os_style_day(self):
    ...         self.assertEqual(self.refdate_day,
    ...                          timetools.Date('1996_11_01').datetime)
    ...     def test_02_os_style_hour(self):
    ...         self.assertEqual(self.refdate_hour,
    ...                          timetools.Date('1997_11_01_12').datetime)

The |unittest.TestCase.setUp| method allows for some preparations that
have to beconducted before the test methods can be called.  The status
defined in the |unittest.TestCase.setUp| method is restored before each
test method call, hence --- normally --- the single test methods do not
affect each other (the consecutive numbers are only used for reporting
the test results in a sorted manner).  In case the test methods affect
some global variables, add a |unittest.TestCase.tearDown| method to your
test class, which will be executed after each test method call. See the
documentation on |unittest.TestCase| regarding the available assert methods.

To elaborate the example above, the two test methods are executed manually
(normally, this is done by the script `test_everything` automatically).
First prepare an object for the test results:

    >>> result = unittest.result.TestResult()

Then initialize a test object engaging the first test method and run
all assertions (in this case, there is only one assertion per method):

    >>> tester = Test01DateInitialization('test_01_os_style_day')
    >>> _ = tester.run(result)

Now do the same for the second test method:

    >>> tester = Test01DateInitialization('test_02_os_style_hour')
    >>> _ = tester.run(result)

The test result object tells us that two tests have been executed, that
no (unexpected) error occurred, and that one test failed:

    >>> result
    <unittest.result.TestResult run=2 errors=0 failures=1>

Here is the reason for the (intentional) failure in this example:

    >>> print(result.failures[0][-1].split('\n')[-2])
    AssertionError: datetime.datetime(1996, 11, 1, 12, 0) != datetime.datetime(1997, 11, 1, 12, 0)



Doctests
--------

When defining `conventional` unit tests, one tries to achieve a large
test coverage with few lines of code (don't repeat yourself!).
Therefore, sophisticated tools like the `mock object library`_ are
available.  Unit tests might also save the purpose to explain the
functioning of the main code, as they explicitly show how it can
be used.  However, the latter is pie in the sky when the unit tests
are interpreted by someone who has little experience in unit testing
and maybe little experience in programming at all.  This might not be
a relevant problem as long as we test such basic functionalities of
the HydPy framework, the user is not really interested in directly or
just expects to work.  However, at the latest when the implemented
hydrological models are involved, the clarity of the defined unit tests
is desirable even for non-programmers (and --- in our opinion ---
it is scientifically necessary).

Each model implemented in HydPy should be tested in a manner that is
as clear and comprehensible as possible.  To this end, the documentation
test principle defined by the module |doctest| should be applied
extensively.  At least, all code branches including (hydrological)
equations should be captured completely via doctests. (More technical
branches, e.g. those including the treatment of exceptions, can be
left to conventional unit tests.)  Often only one or two sentences
are required to explain a doctest in a way, allowing a non-programmer
to understand and repeat it.  And through repetition, he learns to
apply the model.

Besides their intuitiveness, doctests offer the big advantage of
keeping source code and documentation in sync.  Whenever either
a source line or its associated doctest contains errors, or
whenever the source code is updated but the associated doctests
not (or the other way round), it is reported.  Hence all examples
in the HydPy documentation should be written as doctests.  The more
doctests the documentation includes, the merrier the danger of
retaining outdated documentation sections.  In order to keep an
eye on a concrete example: as long as this three-line doctest...

    >>> from hydpy.core import objecttools
    >>> objecttools.classname(objecttools)
    'module'

...remains in the documentation, one can be sure that the current
core package contains a module named `objecttools`.

To support the frequent usage of doctests, one is allowed to use
them at any section of the documentation, accepting possible
redundancies with defined `conventional` unit tests.  The script
`test_everything` searches for doctests in all Python modules and
all `reStructuredText`_ files contained in the package hydpy and
executes them.
