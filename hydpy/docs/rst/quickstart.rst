
.. _doctest: https://docs.python.org/library/doctest.html
.. _Interactive Python Interpreter: https://docs.python.org/tutorial/interpreter.html
.. _IPython: https://ipython.org/
.. _Spyder: https://www.spyder-ide.org/


.. _quickstart:

Quick Start
===========

This documentation includes a considerable number of `doctest`_ examples,
which you can easily repeat via copy-paste, and thus serves you as a very
comprehensive tutorial.  At first, it might be a little overwhelming,
so you might need to spend some time to get adjusted and to find the
relevant starting points, matching your skills and aims.  If you are
already familiar with Python, we recommend to start with reading and
repeating the examples of the documentation on the central |HydPy| class,
and then to follow the links mentioned therein pointing to more detailed
explanations.  Without Python knowledge, you should work through the
following paragraphs beforehand. If you are primarily interested in
executing standard workflows, for example in the context of flood
forecasting, you might prefer reading the documentation on modules
|hyd|, |commandtools|, and |xmltools| first.


Starting Python
_______________

Best first experience comes with using *HydPy* interactively.  Therefore,
we first need to start the `Interactive Python Interpreter`_ or similar
tools like `IPython`_.  Such tools come with complete integrated
development environments like `Spyder`_.  Additionally, any *HydPy*
installation allows you to start an interactive shell by typing the
following line in your command-line prompt::

  hyd.py start_shell


Using Python
____________

The `>>>` symbol tells you that Python is expecting your first statement.
First, try to do some math and see if you get the correct result:

>>> 1+2
3

Understanding the functioning of *HydPy* requires only basic Python
knowledge.  For example, you should be able to use functions like
|print| both with positional and keyword arguments:

>>> print(1, "<", 2)
1 < 2

>>> print(1, "<", 2, end=" is True")
1 < 2 is True

Realise that Python uses colons and indentations instead of brackets for
defining control flow structures like if-else clauses and loops:

>>> if 1 < 2:
...     print("yes")
... else:
...     print("no")
yes

>>> for i in [1, 2, 3]:
...     j = i**2
...     print(j)
1
4
9

In Python, everything is an object, and every object allows you to inspect
it interactively to find out about its features:

>>> obj = "test"

>>> type(obj) is str
True

>>> dir(obj)  # doctest: +ELLIPSIS
[..., 'title', 'translate', 'upper', 'zfill']
>>> print(obj.upper())
TEST
>>> print(obj.title())
Test

Using HydPy
___________

Now that you are familiar with nearly all details of Python (just kidding),
we introduce you to *HydPy*.  *HydPy* is a so-called "site-package",
supplementing the standard Python features.  Make these objects available
by importing them.  For example, write:

>>> from hydpy.examples import prepare_full_example_2

Now the additional function |prepare_full_example_2| lives in your shell.
Executing this function prepares the `LahnH` example project and returns
three further *HydPy* objects:

>>> hp, pub, TestIO = prepare_full_example_2()

Module |pub|, for example, keeps among other things the information about
the simulation period defined by function |prepare_full_example_2|.
The start and end date and the simulation step size are:

>>> print(pub.timegrids.sim.firstdate)
1996-01-01 00:00:00
>>> print(pub.timegrids.sim.lastdate)
1996-01-05 00:00:00
>>> print(pub.timegrids.sim.stepsize)
1d


The catchment outlet of the `LahnH` example project is named "lahn_3".
The following example demonstrates how to query the discharge values
simulated for this outlet:

>>> from hydpy import round_
>>> round_(hp.nodes.lahn_3.sequences.sim.series)
nan, nan, nan, nan

|numpy.nan| stands for "not a number", which we use to indicate missing
values.  Here, the |numpy.nan| values tell us we did not perform a simulation
run so far.  We catch up on this by calling the method |HydPy.simulate|:

>>> hp.simulate()

Now, we can inspect the freshly calculated discharge values:

>>> round_(hp.nodes.lahn_3.sequences.sim.series)
54.046428, 37.32527, 31.925872, 28.416456

You could now write the results to file, print them into a figure,
evaluate them statistically, or -- if you don't like them -- change
some configurations and calculate different ones.

As you can see, a few lines of code are often enough to let *HydPy* execute
complex tasks in a standard-manner.  However, *HydPy* offers a fine level
of control, allowing you to define specific workflows solving individual
problems.  Take your time to understand these first examples fully and
then follow the more detailed explanations in the documentation on the
|HydPy| class.
