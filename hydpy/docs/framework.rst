
.. _framework:

Framework Tools
===============

The :ref:`HydPy` framework provides many functionalities for programming,
documenting, and using different hydrological models.  This section tries
to give a short overview and focusses on the on those aspects, you will
be most interested in when getting used to :ref:`HydPy`.

The most basic features are explained in some detail in subsection
:ref:`core`.  Subsection :ref:`cythons` deals mainly with programming
details related to computational efficiency and should be of importance
for framework developers (and eventually some model developers) only.
Subsection :ref:`cythons` covers some additional features, which are
not required when using :ref:`HydPy` in general but can be helpful
for programming new models or for writing new workflow scripts.

The mentioned subsections are related to different `subpackages` of
:ref:`HydPy`.  But users do not need to know exactly what kind of feature
is implemented where and why.  All features that are intended to be
actually applied by users are directly accessible via imports from
the :ref:`HydPy` package itself.  It is no good programming practice,
but in small scripts perfectly ok to make a "wildcard import" to load
all relevant features:

>>> from hydpy import *

After such an import, features like the |Date| class can be used and
learned interactively:

>>> date = Date('01.01.2000')
>>> date
Date('01.01.2000 00:00:00')
>>> date += '1d'
>>> date
Date('02.01.2000 00:00:00')

The cleaner approach would be to import the required features explicitly,
e.g. class |Period|:

>>> from hydpy import Period
>>> date += 2*Period('1d')
>>> date
Date('04.01.2000 00:00:00')

The above examples try to give a first impression on that, albeit
one has the use the programming language Python to control :ref:`HydPy`,
one can often write simple commands that are even understandable for
people not familiar with Python at all.

To learn what can be done else with classes |Date| and |Period|, see the
detailed examples of the documentation on module |timetools|.

.. toctree::
   :hidden:

   core
   cythons
   auxiliaries
