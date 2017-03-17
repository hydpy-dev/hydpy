.. _Python: http://www.python.org/
.. _Cython: http://www.cython.org/

.. _HydPy:

HydPy
=====

An interactive framework for developing and applying hydrological models
------------------------------------------------------------------------

**This page is currently under construction and will be continuously updated
over the coming weeks.**

:ref:`HydPy` is an interactive framework for developing and applying different
types of hydrological models.  It is completely written in the easy to learn
programming language `Python`_.  Scientists and engineers not already familiar
with `Python`_ will be surprised to discover the degree of flexibility
:ref:`HydPy` allows for in defining highly specific und complex workflows.
Furthermore, the transparent documentation of all model equations and the
opportunity to change them with little effort makes it easy to truly understand
and evaluate the underlying model concepts.  For those who are already familiar
with `Python`_ and are aware of its low efficiency when it comes to pure
mathematical calculations: :ref:`HydPy` includes an automated compiling
mechanism based on the `Python`_ superset `Cython`_.  You can code all model
equations in pure `Python`_ and --- after successful testing --- let
:ref:`HydPy` do the compiling for you.

If you are interested in the philosophy and primary goals of the
developement if :ref:`HydPy`, you are referred to the :ref:`introduction`
section.  If you want to dive into model application or development directly,
have a look at the  :ref:`tutorials` section.  Thorough descriptions the
features of the framework components and it models implemented so far are given
in the sections :ref:`framework` and :ref:`modelcollection`. The section
:ref:`projectstructure` explaines, how :ref:`HydPy` projects can be set up for
different tasks.  And last but not least: :ref:`HydPy` is intended as an open
source project --- any help is greatly appreciated. If you want to contribute
with bug reports, the extension of model collection, or the improvement of the
framework itself, see the :ref:`development` section:

.. toctree::
   :maxdepth: 2

   introduction
   tutorials
   framework
   cythons
   modelcollection
   projectstructure
   development


