.. _GitHub: https://github.com
.. _repository: https://github.com/tyralla/hydpy
.. _hydpy package: https://pypi.python.org/pypi
.. _Python Package Index: https://pypi.python.org/pypi
.. _Python tutorials: https://www.python.org/about/gettingstarted/
.. _book on object-oriented design: http://www.itmaybeahack.com/homepage/books/oodesign.html
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _The Python Standard Library: https://docs.python.org/2/library/
.. _Cython: http://www.cython.org/
.. _NumPy: http://www.numpy.org/
.. _matplotlib: http://matplotlib.org/
.. _End Of Life for Python 2.7: https://www.python.org/dev/peps/pep-0373/
.. _pandas: http://pandas-docs.github.io/pandas-docs-travis/contributing.html
.. _free GitHub account: https://github.com/signup/free
.. _source tree: https://www.sourcetreeapp.com/
.. _Pro Git: https://progit2.s3.amazonaws.com/en/2016-03-22-f3531/progit-en.1084.pdf
.. _Python 2-3 cheat sheet: http://python-future.org/compatible_idioms.html
.. _development:

Development
===========

You can install HydPy from the `hydpy package`_ available on the
`Python package index`_ or fork from this `repository`_ available
on `GitHub`_.  Afterwards, you can implement your own models or
change the frameworks structure in a manner that meets your personal
goals and preferences.  There are many other Python tools freely
available, which will be of great help while trying to achieve more
complex tasks like paramater calibration or regionalization.  Cherry
picking from many different Python packages can be a huge time-saving.
Very often it is not necessary to write a "real" Python program.
Instead, just writing a simple script calling different functionalities
of different packages in the correct order often gets the job done.

However, if you intend to contribute to the further development of HydPy
(hopefully you will!), you must abdicate some parts of the freedom and
ease of use Python offers.  The number of depencencies to other Python
packages, in particular those with some relevant shortcomings and those
which might not be further supported in the future, should be kept as
small as possible.  Otherwise it would be to hard to guarantee the
long-term applicability of HydPy.  Additionally, the Python code
contributed by different developers should be as consistent as possible.
Otherwise there would be a risk of the code base becoming opaque, making
future extensions of HydPy impossible.

The following sections try to define a strategy allowing HydPy to be
developed as an open source project while maintaining sufficiently
high quality standards for practical applications.  The hydrological
modelling community has not made that much progress in this field yet.
This is why the outlined strategy his highly influenced from other
non-hydrological open source projects like `pandas`_.  Discussions on
how to improve the outlined strategy are welcome!


How to contribute?
__________________

To work in collaboration on the same software code requires some kind
of version control.  It must be clear who is working on which part of
the code, when (and why) code changes were conducted, and which code
sections of one developer are compatible with some code sections of
another developer (or not).  Also, one always needs the possibility to
fall back on an older code version whenever some current changes turned
out to be a dead end.

For HydPy, we selected the version control software Git for these tasks.
The main Git `repository`_ is available on `GitHub`_.  So the first
step should be to sing up for a `free GitHub account`_.  After that,
you could contribute to HydPy online without to install anything on
your own computer.  If your only aim is to improve the documentation,
this could be reasonable.  But normally you need to handle Git
repositories on your own computer.  Git itself works via command lines.
Most likely, you would prefer to install Git together with a graphical
user interface like `source tree`_.

To contribute to HydPy requires essentially three or four steps, no matter
if working directy online on GitHub or with your local Git software.  For
simplicity and generality, these steps are explained using the example
of a single change to the documentation via GitHub:

  * Go to `repository`_ and click on "Fork".  On this way you create
    your own HydPy repository, allowing you to add, change, or delete
    any files without interfering in the original repository.
  * Click on "Branch: master", type a name that reflects what you want
    to accomplish and press enter. Now that you have created a new
    branch, you can experiment without affecting the orginal branch or your
    own  master branch. (This step is not really required; you could
    apply the following steps on your own master branch likewise.
    But to create branches for different tasks helps structuring your
    work and to cooperate with others.)
  * Change something.  For example
      * click on ".gitignore"
      * click on the marker symbol ("Edit this file")
      * change the order of two lines (e.g. "*c." and "*.h")
      * write something under "Commit changes" to explain your doing
        (e.g. "change order of lines in .gitignore")
      * click on the green "Commit changes" button

    Now you have changed the file .gitignore in your own branch
    specialized for this task.  Normally, you would commit multiple
    small changes to one branch.  Keeping single commits small allows
    for inspecting and reversing different changes.
  * At last, you can suggest your changes to be included in HydPy's
    main repository.  Click on "Compare" to visualize the relevant
    differences.  Click on "Create pull request" to ask others
    to diskuss your changes and to eventually merge them into their
    projects.  In other words: you request other people to pull (get)
    your own changes and to merge (incorporate) these changes into their
    repositories.

Note that everyone is responsible for his or her own repository, you
do not have to be afraid to break another persons repository accidentally.
But you are responsibility the make pull requests focussing on one issue
that is clearly explained.  Otherwise your contribution is likely to be
refused.

Of course, it is not always as easy as in the given example.  Not only
your branches, but also those of the forks you want to contribute to
evolve.  Often, you will have to retrieve changes from the main branch
and eventually resolve some conflicts before you can make "good" pull
request.  See much more thorough explanations as `Pro Git`_ on how to
improve your skills in using Git.

HydPy Style Guide
_________________

Python allows for writing concise and easily readable software code,
that can be maintained and further developed with relative ease.
However, code quality does also depend on the experience (and available
time) of the programmer writing it.  In hydrology, much model code is
written by PhD students and other young scientists, who --- besides
having participated in some more or less comprehensive introductory
courses --- have often little programming experience and who are under
the pressure not only to get their model running, but also to tackle
their scientific questions and to publish as many research articles
as possible within a limited period of time.  The source code
resulting from such a rush is understandably often a mess.  And even
the better software results often prove inadequate when it comes
to transfering the software into practical applications or sharing it
with other researchers.

This is why we defined the HydPy Style Guide, which is a refinement
of `PEP 8`_ --- the "official" Style Guide for Python Code.
`PEP 8`_ gives coding conventions that help to write clear code.
And it eases diving into already existing source code, as one has
less effort with unraveling the mysteries of overly creative
programming solutions.

In some regards the HydPy Style Guide deviates substantially from `PEP 8`_.
This is mostly due to following two aims.  First, that the HydPy framework
shall be applicable for hydrologists with little or even no programming
experience.  Ideally, such framework users should not even notice that they
are writing valid Python code while preparing their configuration files.
Secondly, that the common gap between model code, model documentation and
model testing should be closed as well as possible.  Understanding the
model documentation of a certain HydPy version should be identical with
understanding how the model actually works under the same HydPy version.
These two points are elucidated in the following subsections.


General framework features
--------------------------
When trying to contribute code to the core tools of HydPy (meaning
basically everything except the actual model implementations), on has
to be aware that even slight changes can have significant effects
on the applicability of HydPy, and that future HydPy developers must
cope with your contributions.   So, always make sure to check the effects
of your code changes properly (as described below).  And try to structure
your code in a readable, object-oriented design.  This section describes
some conventions for the development of HydPy, but is no guidance on how
to write good source code in general.  So, if you have little experience
in programming, first make sure to learn the basics of Python through some
`Python tutorials`_.  Afterwards, improve your  knowledge on code quality
through reading more advanced literature like this
`book on object-oriented design`_.

Python Version
..............
The `End Of Life for Python 2.7` is scheduled for 2020. Nevertheless,
still many scientists are using it.  This is why HydPy is continuously
tested both on Python 2 and Python 3. For the time beeing future HydPy
versions should be applicable on both Python versions.

Always insert

    >>> from __future__ import division, print_function

at the top of a new module.  This introduces the new (integer) division
and print statement of Python 3 into Python 2 (when using Python 3, this
import statement is automatically skipped).

Whenever there are two multiple options to achieve something, prefer
one that is fits best to Python 3.  For example, always use :func:`range`.
While under Python three often :func:`xrange` would be preferable
regarding time and memory efficiency, just using :func:`range` leads to
a clean syntax and is future-proof.  (Have a look at the
`Python 2-3 cheat sheet`_ whenever in compatibility trouble.)

Sometimes incompatibilities of Python 2 and Python 3 require that specific
HydPy functionalities must be coded twice.  Use `pyversion` in these cases:

    >>> from hydpy import pub
    >>> import sys
    >>> if pub.pyversion == 2:
    ...     traceback_ = sys.exc_info()[2]
    ...     exec("raise SystemError, 'just a test', traceback_")
    ... else:
    ...     SystemError('just a test').with_traceback()
    Traceback (most recent call last):
    ...
    SystemError: just a test

(The example above is already taken into account by function
:func:`~hydpy.objecttools.augmentexcmessage`.)


Site Packages
.............
Whenever reasonable, import only packages of the
`The Python Standard Library`_ or at least restrict yourself
to mature and stable site packages.  At the moment, HydPy relies
only on the highly accepted site packages `Cython`_, `NumPy`_,
and `matplotlib`_.  Further developments of HydPy based on more
specialized site packages (e.g. for plotting maps) might be
useful.  But the related import commands should be secured in
a way that allows for the application of HydPy without having
these specialized site packages available.

Imports
.......
As recommended in `PEP 8`_, clarify the sources of your imports.
Always use the following pattern at the top of a new module
(with some example packages):

    >>> # import from...
    >>> # ...the Python Standard Library
    >>> from __future__ import division, print_function
    >>> import os
    >>> import sys
    >>> # ...site-packages
    >>> import numpy
    >>> # ...from HydPy
    >>> from hydpy.core import sequencetools
    >>> from hydpy.cythons import pointer

Note that each import command has its own line.  Always import
complete modules from HydPy without changing their names. ---
No wildcard imports!

The wildcard ban is lifted when writing configuration files.
Using the parameter control files as an example, it wouldn't be nice to
always write something like:

    >>> from hydpy.models import hland
    >>> model = hland.Model()
    >>> model.parameters = hland.Parameters({'model':model})
    >>> model.parameters.control = hland.ControlParameters(model.parameters.control)
    >>> model.parameters.control.nmbzones = 2
    >>> model.parameters.control.nmbzones
    nmbzones(2)

Here a wildcard import (and some magic, see below), allows for a much
cleaner syntax:

    >>>  # First delete the model instance of the example above.
    >>> del model
    >>> # Now repeat the above example in a more intuitive manner.
    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(2)
    >>> nmbzones
    nmbzones(2)

Note that the wildcard import is acceptable here, as there is only one
import statement.  There is no danger of name conflicts.

Defensive Programming
.....................
HydPy is intended to be applicable by researchers and practitioners
who are no Python experts and may have little experience in programming
in general.  Hence it is desirable to anticipate errors due to misleading
input as good as possible and report them as soon as possible.
So, in contradiction to `PEP 8`_, it is recommended to not just expose
the names of simple public attributes.  Instead, use protected attributes
(usually properties) to assure that the internal states of objects remain
consistent, whenever this appears to be useful. One example is that it
is not allowed to assign an unknown string to the `outputfiletype` of a
:class:`~hydpy.core.filetools.SequenceManager`:

    >>> from hydpy import SequenceManager
    >>> sm = SequenceManager()
    >>> sm.outputfiletype = 'test'
    Traceback (most recent call last):
      ...
    NotImplementedError: The given output file type `test` is not implemented yet.  Please choose one of the following file types: ('npy', 'asc').

Of course, the extensive usage of protected attributes increases
the length of the source code and slows computation time.  But,
regarding the first point, writing a graphical user interface
would require much more source code.  And, regarding the second
point, the computation times of the general framework
functionalities discussed here should be negligible in comparison
with the computation times of the hydrological simulations,
which are discussed below, in the majority of cases.

Exceptions
..........
Unmodified error messages of Python (and of the imported
libraries) are often not helpful in the application of HydPy due
to two reasons: First, they are probably read by someone who has
no experience in understanding Pythons exception handling system.
And secondly, they do not tell in which context a problem occurs.
Here, "context" does not mean the relevant part of the source code,
which is of course referenced in the traceback; instead it means
things like the concerned geographical location.  It would, for example,
be of little help to only know that the required value of a certain
parameter is not available, when the same parameter is applied
thousands of times in different subcatchments.  Try to add as much
helpful information to error messages as possible, e.g.::

    raise RuntimeError('For parameter %s of element %s no value has been '
                       'defined so far.  Hence it is not possible to...'
                       % (parameter.name, objecttools.devicename(parameter)))

(The function :func:`~hydpy.core.objecttools.devicename` tries
to determine the name of the :class:`~hydpy.core.devicetools.Node`
or :class:`~hydpy.core.devicetools.Element` instance (indirectly)
containing the given object, which is in many cases the most relevant
information for identifying the error source.)

Whenever possible, us function :func:`~hydpy.objecttools.augmentexcmessage`
to augment standard Python error messages with `HydPy information`.


Naming Conventions
..................
The naming conventions of `PEP 8`_ apply.  Additionally, it is
encouraged to name classes and their instances as similar as
possible whenever reasonable, often simply switching from
**CamelCase** to **lowercase**. This can be illustrated based
on some classes for handling time series:

=============== ============== ===================================================================================
Class Name      Instance Name  Note
=============== ============== ===================================================================================
Sequences       sequences      each Model instance handles exactly one Sequence instance: `model.sequences`
InputSequences  inputs         "inputsequences" would be redundant for attribute access: `model.sequences.inputs`
=============== ============== ===================================================================================

If possible, each instance should define its own preferred name via
the property `name`:

    >>> from hydpy.models.hland import *
    >>> InputSequences(None).name
    'inputs'

For classes like :class:`~hydpy.core.devicetools.Element` or
:class:`~hydpy.core.devicetools.Node`, where names (and not
namespaces) are used to differentiate between instances, the
property `name` is also implemented, but --- of course --- not
related to the class name, e.g.:

    >>> from hydpy import Node
    >>> Node('gauge1').name
    'gauge1'

In HydPy, instances of the same or similar type should be grouped in
collection objects with a similar name, but with an attached letter "s".
Different :class:`~hydpy.core.devicetools.Element` instances are stored
in an instance of the class :class:`~hydpy.core.devicetools.Elements`,
different :class:`~hydpy.core.devicetools.Node` instances are stored in
an instance of the class :class:`~hydpy.core.devicetools.Nodes`...

Collection Classes
..................
The naming (of the instances) of collection classes is discussed just
above.  Additionally, try to follow the following recommendations.

Each collection object should be iterable.  Normally, both the names of
the handled objects (as known to the collection object) and the objects
themself should be returned, e.g.:

    >>> from hydpy import Nodes
    >>> nodes = Nodes()
    >>> nodes += 'gauge1'
    >>> nodes += 'gauge2'
    >>> for (name, node) in nodes:
    ...     name, node
    ('gauge1', Node("gauge1", variable="Q"))
    ('gauge2', Node("gauge2", variable="Q"))

To ease working in the interactive mode, objects handled by a
collection object should be accessible as attributes:

    >>> nodes.gauge1
    Node("gauge1", variable="Q")
    >>> nodes.gauge2
    Node("gauge2", variable="Q")

Whenever usefull, define convenience functions which simplify the
handling of collection objects, e.g.:

    >>> nodes += Node('gauge1')
    >>> nodes.gauge1 is nodes['gauge1']
    True
    >>> len(nodes)
    2
    >>> 'gauge1' in nodes
    True
    >>> nodes.gauge1 in nodes
    True
    >>> newnodes = nodes.copy()
    >>> nodes is newnodes
    False
    >>> nodes.gauge1 is newnodes.gauge1
    True
    >>> nodes -= 'gauge1'
    >>> 'gauge1' in nodes
    False


String Representations
......................
Be aware of the difference between :func:`str` and :func:`repr`.
A good string representation (return value of :func:`repr`) is one
that a Non-Python-Programmer does not identify to be a string.
The first ideal case is that copy-pasting the string representation
within a command line to evaluate it returns a reference to the same
object. A Python example:

    >>> repr(None)
    'None'
    >>> eval('None') is None
    True

A HydPy example:

    >>> from hydpy import Node
    >>> Node('gauge1')
    Node("gauge1", variable="Q")
    >>> eval('Node("gauge1", variable="Q")') is Node('gauge1')
    True

In the second ideal case is that evaluating the string representation
results in an equal object. A Python example:

    >>> 1.5
    1.5
    >>> eval('1.5') is 1.5
    False
    >>> eval('1.5') == 1.5
    True

A HydPy example:

    >>> from hydpy import Period
    >>> Period('1d')
    Period("1d")
    >>> eval('Period("1d")') is Period('1d')
    False
    >>> eval('Period("1d")') == Period('1d')
    True

For nested objects this might be more hard to accomplish, but sometimes it's
worth it.  A Python example:

    >>> [1., 'a']
    [1.0, 'a']
    >>> eval("[1.0, 'a']") == [1.0, 'a']
    True

A HydPy example:

    >>> from hydpy import Timegrid
    >>> Timegrid('01.11.1996', '1.11.2006', '1d')
    Timegrid("01.11.1996 00:00:00",
             "01.11.2006 00:00:00",
             "1d")
    >>> eval('Timegrid("01.11.1996 00:00:00", "01.11.2006 00:00:00", "1d")') == Timegrid('01.11.1996', '1.11.2006', '1d')
    True

ToDo: For deeply nested objects, this strategy becomes infeasible, of course.
SubParameters(None)...

Sometimes, additional information might increase the value of a
string representation.  Add comments in these cases, but only when
the :attr:`~hydpy.pub.options.reprcomments` flag is activated:

    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(2)
    >>> from hydpy.pub import options
    >>> options.reprcomments = True
    >>> nmbzones
    # Number of zones (hydrological response units) in a subbasin [-].
    nmbzones(2)
    >>> options.reprcomments = False
    >>> nmbzones
    nmbzones(2)

Such comments are of great importance, whenever the string representation
might be misleading:

    >>> simulationstep('12h', warn=False)
    >>> percmax(2)
    >>> options.reprcomments = True
    >>> percmax
    # Maximum percolation rate [mm/T].
    # The actual value representation depends on the actual parameter step size, which is `1d`.
    percmax(2.0)
    >>> options.reprcomments = False
    >>> percmax
    percmax(2.0)


Introspection
.............

Model specific features
-----------------------

Assuring code quality
_____________________

See the latest :download:`coverage report <coverage.html>`.
