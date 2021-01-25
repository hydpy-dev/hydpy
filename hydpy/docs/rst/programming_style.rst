.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _Pylint: https://www.pylint.org/
.. _Black: https://github.com/psf/black
.. _Travis CI: https://travis-ci.com/
.. _pylintrc: https://github.com/hydpy-dev/hydpy/blob/master/pylintrc
.. _Python tutorials: https://www.python.org/about/gettingstarted/
.. _book on object-oriented design: http://www.itmaybeahack.com/homepage/books/oodesign.html
.. _core: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/core
.. _auxs: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/auxs
.. _models: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/models
.. _exe: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/exe
.. _cythons: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/cythons
.. _Cython: https://cython.org/
.. _autogen: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/cythons/autogen
.. _conf: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/conf
.. _data: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/data
.. _LahnH example project: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/data/LahnH
.. _docs: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/docs
.. _reStructuredText: _http://docutils.sourceforge.net/rst.html
.. _sphinx: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/docs/sphinx
.. _rst: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/docs/rst
.. _figs: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/docs/figs
.. _html: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/docs/html
.. _bokeh: https://bokeh.pydata.org/en/latest/
.. _tests: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/tests
.. _iotesting: https://github.com/hydpy-dev/hydpy/tree/master/hydpy/tests/iotesting
.. _LaTeX: https://www.sphinx-doc.org/en/master/latex.html

.. _programming_style:

Programming style
_________________

Python allows for writing concise and easily readable software code
that can be maintained and further developed with acceptable effort.
However, code quality does also depend on the experience and available
time of the programmer writing it.  In hydrology, much model code is
written by PhD students, who often have little programming experience
and are under pressure not only to get their model running but also to
tackle their scientific questions and to publish their results.  The
source code resulting from such a rush is understandably often a mess.
Even the relatively goodsoftware results often prove inadequate when it
comes to transferring the software into practical applications or
sharing it with other researchers.

In the long development process of *HydPy*, which also started as a
quick side-project when writing a PhD thesis, we made many misleading
design decisions ourselves.   However, through much effort spent in
periods of refactoring and consolidation, we came to a software
architecture that, in our opinion, should be easily extensible and
applicable in many contexts.

This section defines the steadily growing "HydPy Style Guide", being
an attempt to explain the principles in the development of *HydPy* and
to make sure the contributions of different developers are as consistent
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
configuration files or working interactively in the Python shell.
Second, we try to close the gap between the model code, model
documentation and model tests as well as possible.  Through reading
(and testing) for example the documentation of a specific model, one
should exactly understand how this model works within the corresponding
version of the *HydPy* framework.  Third, we want the source code style
of *HydPy* to be as consistent as possible.  Therefore, we further
concretise many suggestions of `PEP 8`_ by applying (the standards of)
`Black`_.

When contributing to the code basis, be aware that even slight changes
can have significant effects on the  applicability of *HydPy*, and future
developers must cope with your work.  So, always make sure to check for
possible side-effects of your code changes.  Structure your code in a
clear (mainly object-oriented) design and use `Black`_ for automatically
formatting your code.  Refactor thoroughly enough to avoid code duplicates.
Last but not least, create smartly thought-through APIs for your objects,
allowing to use them smoothly both within doctests and within the Python shell.

Be aware of the usage of `Black`_ and `Pylint`_ in our `Travis CI`_ continuous
integration workflow.  `Black`_ checks that all committed files follow its
standards.  `Pylint`_ is an additional style checker that recognises missing
documentation sections, repeated or inconsistent method definitions, and much
more.  The `pylintrc`_ file configures the general behaviour and strictness of
`Pylint`_.  You are allowed to disable some checks locally in case you provide
a good explanation.  At best, simply at a link to a related issue explaining why
`Pylint`_ is wrong in your particular code section, using the following pattern:

>>> # pylint: disable=abstract-method
>>> # due to pylint issue https://github.com/PyCQA/pylint/issues/179

This section describes some specific conventions for the development
of *HydPy* but is no guidance on how to write good source code in general.
If you have little experience in programming, first make sure to learn
the basics of Python through some `Python tutorials`_.  Afterwards,
improve your knowledge of code quality through reading more advanced
literature like this `book on object-oriented design`_.


Project structure
-----------------

For *HydPy*, we prefer a flat folder structure  with at most two
subpackage levels.  The individual modules can be of arbitrary length
to cover particular topics completely.  For example, module
|parametertools| defines all base classes for creating model-specific
parameter classes as well as their collection classes.

Subpackage `core`_ provides the essential features of *HydPy*, used for
implementing hydrological models and workflows as well.  One example
is the mentioned |parametertools| module.  Modules defined in subpackage
`core`_ should never import features provided by modules of other
subpackages, excepts those of subpackage `cythons`_.

Subpackage `auxs`_ provides auxiliary features, only necessary for
selected *HydPy* models and applications.  One example is module
|anntools| defining artificial neural network classes usable as
complex model parameters, currently relevant for the |dam| model only.
Modules defined in subpackage `auxs` are allowed to import features
from subpackages `core`_ and `cythons`_.

Subpackage `models`_ contains the implemented hydrological models.
Base models as |dam| are additional subpackages, providing, for example,
different kinds of sequence classes in separate submodules. Application
models as |dam_v001|, selecting useful combinations of base model
features, are defined within single modules.  Please follow the naming
patterns of the modules of the already available models carefully, when
implementing new ones.

Subpackage `exe`_ provides features easing the execution of *HydPy*.
Module |commandtools| (in combination with script |hyd|), for example,
allows controlling *HydPy* from the command line.

Subpackage `cythons`_ is related to all `Cython`_ features of *HydPy*.
First, it contains functionalities for "cythonizing" the Python models
defined in subpackage `models`_.  Second, it contains `Cython`_ extension
files, which mostly correspond to Python modules of other subpackages.
For example, the extension file |annutils| provides time-critical
implementation details to module |anntools|.  Third, it contains the
additional subpackage `autogen`_, including all automatically generated
extension files and Dynamic Link Library files (*pyd* files on Windows
and *so* files on Linux). Extension files should not import any features
from other subpackages.  Python files controlling the automatic generation
of extension files are allowed to import from subpackage `core`_.

Note that the names of the modules of subpackages `core`_, `auxs`_, and
`exe`_ end in almost all cases with "tools" and those of the modules and
extension files of subpackage `cythons`_ with "utils", which helps to
identify the different module types immediately and to circumvent name
conflicts between and within modules.

Subpackage `conf`_ contains configuration files (currently XML schema
files and coefficients for numerical integration algorithms), which
might be generated automatically during *HydPy's* build process.

Subpackage `data`_ provides example data usable within doctests,
currently only the `LahnH example project`_.

Subpackage `docs`_ contains different subpackages itself.  `sphinx`_
controls the automatic generation of the HTML documentation. `rst`_
contains all `reStructuredText`_ files written manually. `figs`_ contains
all manually generated figures in the *png* format.  After the build
process, `html`_ contains the `bokeh`_ plots automatically generated
during testing.  Note that the actual HTML generation takes place in
a folder *auto*, automatically created and filled with information
during the process.

Subpackage `tests`_ deals with testing.  As explained in section
:ref:`tests_and_documentation`, the contained unit test modules are
deprecated.  Its subpackage `iotesting`_ is the place designated to
store data during testing temporarily.


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
complete modules from *HydPy* without changing their names. ---
No wildcard imports!

We lift the wildcard ban for  writing configuration files. Using the
example of parameter control files, it would not be convenient always
to write something like:

>>> from hydpy.models import hland
>>> model = hland.Model()
>>> from hydpy.core import parametertools
>>> model.parameters = parametertools.Parameters({"model": model})
>>> model.parameters.control = hland.ControlParameters(model.parameters.control)
>>> model.parameters.control.nmbzones = 2
>>> model.parameters.control.nmbzones
nmbzones(2)

Here a wildcard import (and the "magic" of function |parameterstep|),
allows for a much cleaner syntax:

>>> del model
>>> from hydpy.models.hland import *
>>> parameterstep("1d")
>>> nmbzones(2)
>>> nmbzones
nmbzones(2)

Note that the wildcard import is acceptable here, as there is only one
import statement.  There is no danger of name conflicts.

Besides the wildcard exeption explained above, there is another one
related to |modelimports|.


Defensive programming
---------------------

*HydPy* is intended to be applicable by researchers and practitioners who are
no Python experts and may have little experience in programming in general.
Hence, it is desirable to anticipate errors due to misleading input as thorough
as possible and report them as soon as possible.  So, in contradiction
to `PEP 8`_, it is often preferable to not just expose the names of
simple public attributes.  Whenever sensible, use protected attributes
(defined by |property| or the more specific property features provided by
module  |propertytools|) to assure that the internal states of objects
remain consistent. One example is that it is not allowed to assign an unknown
string to the `outputfiletype` of an instance ofclass |SequenceManager| :

>>> from hydpy.core.filetools import SequenceManager
>>> sm = SequenceManager()
>>> sm.fluxfiletype = "test"
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
>>> parameterstep("1d")
>>> from hydpy import Element
>>> e1 = Element("e1", outlets="n1")
>>> e1.model = model
>>> k(hq=10.0)
Traceback (most recent call last):
...
ValueError: For the alternative calculation of parameter `k` of element `e1`, at least the keywords arguments `khq` and `hq` must be given.

Another recommended approach is exception chaining, for which we
recommend using the function |augment_excmessage|:

>>> e1.keywords = "correct", "w r o n g"
Traceback (most recent call last):
...
ValueError: While trying to add the keyword `w r o n g` to device e1, the following error occurred: The given name string `w r o n g` does not define a valid variable identifier.  Valid identifiers do not contain characters like `-` or empty spaces, do not start with numbers, cannot be mistaken with Python built-ins like `for`...)


Naming conventions
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
>>> Node("gauge1").name
'gauge1'

Group instances of the same type in collection objects with the same name,
except an attached letter "s". For example, we store different |Element|
objects in an instance of class |Elements|, and different |Node| objects
in an instance of the class |Nodes|.


Collection classes
------------------

The subsection above deals with the naming (of the instances) of
collection classes.  Additionally, consider the following
recommendations when implementing new collection classes.

Each collection object must be iterable:

>>> from hydpy import Nodes
>>> nodes = Nodes("gauge1", "gauge2")
>>> for node in nodes:
...     print(repr(node))
Node("gauge1", variable="Q")
Node("gauge2", variable="Q")

For assisting the user when working interactively in the Python shell,
collection objects should expose their handled objects as attributes
and let function "dir" return the attribute names, being identical
with the *name* attributes of the handled objects:

>>> nodes.gauge1
Node("gauge1", variable="Q")
>>> nodes.gauge2
Node("gauge2", variable="Q")
>>> "gauge1" in dir(nodes)
True

Additionally, provide item access as a more type-safe and eventually
more efficient alternative for writing complex scripts:

>>> nodes["gauge1"]
Node("gauge1", variable="Q")

Whenever useful, define convenience functions to simplify the
handling of collection objects:

>>> nodes += Node("gauge1")
>>> nodes.gauge1 is Node("gauge1")
True
>>> len(nodes)
2
>>> "gauge1" in nodes
True
>>> nodes.gauge1 in nodes
True
>>> newnodes = nodes.copy()
>>> nodes is newnodes
False
>>> nodes.gauge1 is newnodes.gauge1
True
>>> nodes -= "gauge1"
>>> 'gauge1' in nodes
False


String representations
----------------------

Be aware of the difference between |str| and |repr|.  Often, |str| is
supposed to return strings describing objects in a condensed form for
end-users when executing a program, while |repr| is supposed to return
strings containing all details of an object for developers when debugging
a program.  Some argue, due to its limited usage, giving |repr| much
attention is a waste of time in many cases.  For *HydPy*, we think different.
Defining comprehensive  |repr| return values simplifies reading the
doctests of the online documentation and working interactively within
the Python shell, thus being of high relevance for end-users, too.  On
the other hand, |str| is a little less relevant due to mainly being an
alternative for the generation of exception messages.  Hence, focus
primarily on |repr| and concentrate on |str| when the return value of
|repr| is too complicated for exception messages.

A good return value of |repr| is one that a non-Python-programmer does
not identify as a string. The first ideal case is that copy-pasting
the string representation and evaluating it within the Python shell
returns a reference to the same object.

A Python example:

>>> repr(None)
'None'
>>> eval("None") is None
True

A *HydPy* example:

>>> from hydpy import Node
>>> Node("gauge1")
Node("gauge1", variable="Q")
>>> eval('Node("gauge1", variable="Q")') is Node("gauge1")
True

In the second ideal case, evaluating the string representation results
in an equal object.

A Python example:

>>> 1.5
1.5
>>> eval("1.5") is 1.5
False
>>> eval("1.5") == 1.5
True

A *HydPy* example:

>>> from hydpy import Period
>>> Period("1d")
Period("1d")
>>> eval('Period("1d")') is Period("1d")
False
>>> eval('Period("1d")') == Period("1d")
True

For nested objects, the above goals may be hard to accomplish, but
sometimes it's worth it.

A Python example:

>>> [1., "a"]
[1.0, 'a']
>>> eval("[1.0, 'a']") == [1.0, "a"]
True

A *HydPy* example:

>>> from hydpy import Timegrid
>>> Timegrid("01.11.1996", "1.11.2006", "1d")
Timegrid("01.11.1996 00:00:00",
         "01.11.2006 00:00:00",
         "1d")
>>> eval('Timegrid("01.11.1996 00:00:00", "01.11.2006 00:00:00", "1d")') == Timegrid("01.11.1996", "1.11.2006", "1d")
True

For deeply nested objects, this strategy becomes infeasible, of course.
Then try to find a way to "flatten" the string representation without
losing too much information:

>>> from hydpy import Element, Elements
>>> Elements(Element("e_1", outlets="n_1"), Element("e_2", outlets="n_2"))
Elements("e_1", "e_2")

Finally, always consider using functions provided by module |objecttools|
for simplifying the definition of |repr| and |str| return values,
to keep the string representations of different *HydPy* objects, at least
to a certain degree, consistent.  For example, use function |repr_| to
let the user control the maximum number of decimal places of scalar
floating-point values:

>>> from hydpy import pub, repr_
>>> class Number(float):
...     def __repr__(self):
...         return repr_(self)
>>> pub.options.reprdigits = 3
>>> Number(1./3.)
0.333


Introspection
-------------

One nice feature of Python is its "introspection" capability, allowing to
analyse (and, when necessary, modify) objects at runtime with little effort.

*HydPy* makes extensive use of these introspection features, whenever it
serves the purpose of relieving non-programmers from writing code lines
that do not deal with hydrological modelling directly.  Section `Imports`_
discusses the usage of wildcard imports in parameter control files,
where the real comfort comes from the "magic" implemented in function
|parameterstep|.  Invoking this function does not only define the time
interval length for the following parameter values.  It also initialises
a new model instance (if such an instance does not already exist) and
directly exposes its control parameter objects in the local namespace.
For the sake of the user's comfort, each parameter control file purports
to be a simple configuration file that somehow checks its own validity.
On the downside, modifying the operating principle of *HydPy's* parameter
control files requires more thought than a more simple direct approach would.

We encourage to implement additional introspection features, as long as
they improve the intuitive usability for non-programmers and do not harm
HydPy's reliability.  However, please be particularly cautious when doing
so and document why and how thoroughly.  To ensure traceability, one
should usually add such code to modules like |modelutils|, |importtools|,
and |autodoctools|.  Module |modelutils| deals with all introspection
needed to "cythonize" Python models automatically.  Module |importtools|
contains the function |parameterstep| and related features.  Module
|autodoctools| serves the purpose to improve the automatic generation of
the online documentation.


Typing
------

Python is a strongly but dynamically typed programming language, allowing
to write very condensed, readable, and flexible (scripting) code.  However,
missing type information has also its drawbacks.  With the *HydPy* sources
reaching a certain size, we began to introduce static typing annotations
based on module |typing|.  In our experience, the additional information
helps a lot, allowing code inspection and refactoring tools to analyse
and modify the code more efficiently. We are going to increase our efforts
in this direction, but do not have a "HydPy Typing Style Guide" at hand,
so far.  So please add the typing annotations you find useful.  The minimum
requirement for Python core modules is to declare the return type (or, when
necessary, to declare the |typing.Union| of possible return types) of
each new function or method:

>>> from typing import List
>>> def test(nmb) -> List[int]:
...     return list(range(nmb))

For `Cython`_ extension files, adding type information understandable
to Python tools is of even greater importance. Hence, accompany each
`Cython`_ extension file with a stub file, annotating all public
(sub)members.


Implementing models
-------------------

Please inspect the source files of the already available hydrological
models in detail to understand how to implement new ones correctly.
*HydPy* provides many standard features, allowing you to write straightforward
model source code in many cases.  However, you are free to implement any
functionalities you find missing (see for example the complex "connect"
method defined by the |hbranch| model). If those functionalities might
be of importance to other models as well, consider to generalise them
and to add them to the suitable subpackage.

The main effort of creating new models is not to write the source code,
but to document it thoroughly and to prove it is working correctly.
Each docstring of a calculation method must contain at least a short
description, lists of the required, calculated, and updated variables
(linked via substitutions), the basic equation in `LaTeX`_ style,
and doctests covering all anticipated usages of the method, even the
unlikely ones.  The docstrings of all |Parameter| or |Sequence_|
subclasses containing "special" source code (for example modifications
of |trim|) must contain doctests addressing these code sections.
Finally, write integration tests for each application model based on
class |IntegrationTest|, explaining all model functionalities in detail
both with text and `bokeh`_ plots, and preventing future regression by
sufficiently complete tabulated calculation results.

