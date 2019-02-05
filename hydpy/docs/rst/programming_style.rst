.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _Python tutorials: https://www.python.org/about/gettingstarted/
.. _book on object-oriented design: http://www.itmaybeahack.com/homepage/books/oodesign.html
.. _PyPy: https://pypy.org/


.. _programming_style:

Programming style
_________________

Python allows for writing concise and easily readable software code,
that can be maintained and further developed with acceptable effort.
However, code quality does also depend on the experience and available
time of the programmer writing it.  In hydrology, much model code is
written by PhD students, who often have little programming experience
and are under pressure not only to get their model running but also to
tackle their scientific questions and to publish their results.  The
source code resulting from such a rush is understandably often a mess.
Even the better software results often prove inadequate when it comes
to transferring the software into practical applications or sharing it
with other researchers.


In the long development process of *HydPy*, which also started as a
quick side-project when writing a PhD thesis, we made many misleading
design decisions ourselves.   However, through much effort spent in
periods of refactoring and consolidation, we came to a software
architecture that, in our opinion, should be easily extensible and
applicable in many contexts.

This section defines the steadily growing "HydPy Style Guide", being
an attempt to explain the principles in the development of *HydPy*,
to make sure contributions by different developers are as consistent
as possible.  Please understand the "HydPy Style Guide" as a refinement
of `PEP 8`_ — the “official” Style Guide for Python Code. `PEP 8`_ gives
coding conventions that help to write clear code.  If everyone follows
these conventions, diving into already existing source code becomes much
more straightforward, as one has less effort unravelling the mysteries
of overly creative programming solutions.

In some regards, the HydPy Style Guide deviates from `PEP 8`_, mostly
due to the following two aims.  First, we design the *HydPy* framework
as a Python library applicable for hydrologists with little or even no
programming experience.  Ideally, such framework users should not even
notice that they are writing valid Python code while preparing their
configuration files.  Second, we try to close the gap between the model
code, model documentation and model tests as well as possible.
Through reading (and testing) for example the documentation of a specific
model, one should exactly understand how this model works within the
corresponding version of the *HydPy* framework.


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
`Python tutorials`_.  Afterwards, improve your knowledge of code quality
through reading more advanced literature like this
`book on object-oriented design`_.


Imports
-------

As recommended in `PEP 8`_, clarify the sources of your imports.
Always use the following pattern at the top of a new module and
list the imports of a section in alphabetical order:

    >>> # import...
    >>> # ...from standard library
    >>> import os
    >>> import sys
    >>> # ...from site-packages
    >>> import numpy
    >>> # ...from HydPy
    >>> from hydpy.core import sequencetools
    >>> from hydpy.cythons import pointerutils

Note that each import command stands in a separate line.  Always import
complete modules from HydPy without changing their names. ---
No wildcard imports!

We lift the wildcard ban for  writing configuration files. Using the
example of parameter control files, it would not be convenient always
to write something like:

    >>> from hydpy.models import hland
    >>> model = hland.Model()
    >>> from hydpy.core import parametertools
    >>> model.parameters = parametertools.Parameters({'model':model})
    >>> model.parameters.control = hland.ControlParameters(model.parameters.control)
    >>> model.parameters.control.nmbzones = 2
    >>> model.parameters.control.nmbzones
    nmbzones(2)

Here a wildcard import (and the "magic" of function |parameterstep|),
allows for a much cleaner syntax:

    >>> del model
    >>> from hydpy.models.hland import *
    >>> parameterstep('1d')
    >>> nmbzones(2)
    >>> nmbzones
    nmbzones(2)

Note that the wildcard import is acceptable here, as there is only one
import statement.  There is no danger of name conflicts.

Besides the wildcard exeption explained above, there is another one
related to |modelimports| (see section :ref:`implementing_models`).


Defensive Programming
---------------------

HydPy should be applicable by researchers and practitioners who are no
Python experts and may have little experience in programming in general.
Hence, it is desirable to anticipate errors due to misleading input as
good as possible and report them as soon as possible.  So, in contradiction
to `PEP 8`_, it is often preferable to not just expose the names of
simple public attributes.  Whenever sensible, use protected attributes
(usually the basic |property| objects or the more specific properties
provided by module |propertytools|) to assure that the internal states
of objects remain consistent. One example is that it is not allowed to
assign an unknown string to the `outputfiletype` of an instance of
class |SequenceManager| :

>>> from hydpy.core.filetools import SequenceManager
>>> sm = SequenceManager()
>>> sm.fluxfiletype = 'test'
Traceback (most recent call last):
  ...
ValueError: The given sequence file type `test` is not implemented.  Please choose one of the following file types: npy, asc, and nc.


Of course, the extensive usage of protected attributes increases the
length of the source code and slows computation time.  However, regarding
the first point, writing a graphical user interface would require much
more source code (and still decrease flexibility).  Regarding the second
point, one should take into account that the computation times of the
general framework functionalities discussed here should be negligible
in comparison with the computation times of hydrological simulations
in the majority of cases.


Exceptions
----------

Unmodified Python error messages are often not sufficiently informative
for *HydPy* applications due to two reasons. First, they are probably
read by someone who has no experience in understanding Python's exception
handling system.  Second, they do not tell in which hydrological context
a problem occurs.  It would be of little help to only know that the value
of a parameter object of a particular type has been misspecified, but not
to know in which sub-catchment.  Hence, try to add as much helpful
information to error messages as possible.  One useful helper function
for doing so is |elementphrase|, trying to determine the name of the
relevant |Element| object and add it to the error message:


>>> from hydpy.models.hland import *
>>> parameterstep('1d')
>>> from hydpy import Element
>>> e1 = Element('e1')
>>> e1.connect(model)
>>> k(hq=10.0)
Traceback (most recent call last):
...
ValueError: For the alternative calculation of parameter `k` of element `e1`, at least the keywords arguments `khq` and `hq` must be given.

Another recommended approach is exception chaining, for which we
recommend using function |augment_excmessage|:

>>> e1.keywords = 'correct', 'w r o n g'
Traceback (most recent call last):
...
ValueError: While trying to add the keyword `w r o n g` to device e1, the following error occurred: The given name string `w r o n g` does not define a valid variable identifier.  Valid identifiers do not contain characters like `-` or empty spaces, do not start with numbers, cannot be mistaken with Python built-ins like `for`...)


Naming Conventions
------------------

The naming conventions of `PEP 8`_ apply.  Additionally, we
encouraged to name classes and their instances as similar as
possible whenever reasonable, often simply switching from
**CamelCase** to **lowercase**, as shown in the following
examples:

=============== ============== ===================================================================================
Class Name      Instance Name  Note
=============== ============== ===================================================================================
Sequences       sequences      each Model instance handles exactly one Sequence instance: `model.sequences`
InputSequences  inputs         "inputsequences" would be redundant for attribute access: `model.sequences.inputs`
=============== ============== ===================================================================================

If reasonable, each instance should define its preferred name via *name*
attribute:

>>> from hydpy.models.hland import *
 >>> InputSequences(None).name
'inputs'

Classes like |Element| or |Node|, where names (and not namespaces) are
used to differentiate between instances, should implement instance name
attributes, when reasonable:

>>> from hydpy import Node
>>> Node('gauge1').name
'gauge1'

Group instances of the same type in collection objects with the same name,
except an attached letter "s". For example, we store different |Element|
objects are in an instance of class |Elements|, and different |Node|
objects in an instance of the class |Nodes|.


Collection Classes
------------------

The naming (of the instances) of collection classes is discussed just
above.  Additionally, try to follow the following recommendations.

Each collection object should be iterable, e.g.:

    >>> from hydpy import Nodes
    >>> nodes = Nodes('gauge1', 'gauge2')
    >>> for node in nodes:
    ...     node
    Node("gauge1", variable="Q")
    Node("gauge2", variable="Q")

To ease working in the interactive mode, objects handled by a
collection object should be accessible as attributes:

    >>> nodes.gauge1
    Node("gauge1", variable="Q")
    >>> nodes.gauge2
    Node("gauge2", variable="Q")

Whenever usefull, define convenience functions which simplify the
handling of collection objects, e.g.:

    >>> nodes += Node('gauge1')
    >>> nodes.gauge1 is Node('gauge1')
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
----------------------

Be aware of the difference between |str| and |repr|.  A good string
representation (return value of |repr|) is one
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
    Period('1d')
    >>> eval("Period('1d')") is Period('1d')
    False
    >>> eval("Period('1d')") == Period('1d')
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
    Timegrid('01.11.1996 00:00:00',
             '01.11.2006 00:00:00',
             '1d')
    >>> eval("Timegrid('01.11.1996 00:00:00', '01.11.2006 00:00:00', '1d')") == Timegrid('01.11.1996', '1.11.2006', '1d')
    True

ToDo: For deeply nested objects, this strategy becomes infeasible, of course.
SubParameters(None)...

Sometimes, additional information might increase the value of a
string representation.  Add comments in these cases, but only when
the |Options.reprcomments| flag handled in module |pub| is activated:

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

    >>> simulationstep('12h')
    >>> percmax(2)
    >>> options.reprcomments = True
    >>> percmax
    # Maximum percolation rate [mm/T].
    # The actual value representation depends on the actual parameter step size,
    # which is `1d`.
    percmax(2.0)
    >>> options.reprcomments = False
    >>> percmax
    percmax(2.0)


Introspection
-------------

One of Pythons major strengths is `introspection`, allowing you to analyze
(and modify) objects fundamentally at runtime.  One simple example would
be to access and change the documentation of a single HBV `number of zones`
parameter initialized at runtime.  Here, the given string representation
comment is simply the first line of the documentation string of class
|hland_control.NmbZones|:

    >>> from hydpy.models.hland.hland_control import NmbZones
    >>> NmbZones.__doc__.split('\n')[0]
    'Number of zones (hydrological response units) in a subbasin [-].'

However, we could define a unique documentation string for the specific
|hland_control.NmbZones| instance defined above:

    >>> nmbzones.__doc__ = NmbZones.__doc__.replace('a subbasin',
    ...                                             'the amazonas basin')

Now the representation string (only) of this instance is changed:

    >>> options.reprcomments = True
    >>> nmbzones
    # Number of zones (hydrological response units) in the amazonas basin [-].
    nmbzones(2)

As you can see, it is easy to retrieve information from living objects
and to adjust them to specific situations.  With little effort, one
can do much more tricky things. But when writing production code, one
has to be cautious.  First, do not all Python implementations support
each introspection feature of CPython.  Secondly is introspection often
a possible source of confusion.  For HydPy, only the second issue is of
importance, as the use of Cython rules out its application on alternative
Python implementations as `PyPy`_.  But the second issue needs to be
taken into account more strongly.

HydPy makes extensive use of Pythons introspection features, whenever it
serves the purpose of relieving non-programmers from writing code lines
that do not deal with hydrological modelling directly.  Section `Imports`_
discusses the usage of wildcard imports in parameter control files.
However, the real comfort comes primarily from the `magic` implemented
in the function |parameterstep|.  Through calling this function one does
not only define a relevant time interval length for the following parameter
values.  One also initializes a new model instance (if such an instance
does not already exist) and makes its control parameter objects available
in the local namespace.  Hence, for the sake of the user's comfort, each
parameter control file purports being a simple configuration file that
somehow checks its own validity.  On the downside, to modify the operating
principle of HydPy's parameter control files requires more thought than if
everything would have been accomplished in a more direct manner.

It is encouraged to implement additional introspection features into
HydPy, as long as they improve the intuitive usability for non-programmers.
But one should be particularly cautious when doing so and document the
why and how thoroughly.  To ensure traceability, one should usually add
such code to the modules like |modelutils| and |autodoctools|.  Module
|modelutils| deals with all introspection needed to `cythonize` Python models
automatically.  Module |autodoctools| serves for improving HydPy's online
documentation automatically.
