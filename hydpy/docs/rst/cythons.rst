
.. _cythons:

Cython Tools
============

The modules of the `cythons` subpackage should only be of interest to framework
developers (and eventually some model developers).

The most crucial module (and so far the only one which is a Python module) is
|modelutils|, which implements the routines to translate Python code into Cython code,
to translate Cython code into C code, to compile C code, and to embed the compilation
into a "Python dll" (a "pyd" file on Windows and a "so" file on Linux systems).

The other modules are Cython extension modules.  Often, they are named similar to the
Python modules of other packages (for example, |anntools| and :ref:`annutils`).  The
respective Cython extension module then implements the performance-critical part of the
required functionality.

The required dll files are shipped with the available HydPy wheels or automatically
generated when building HydPy locally.  You can find them in the `cythons` subpackage
`autogen`.  The same holds for the dll files of the "cythonized"  hydrological models.

If you want to change a model in Python (for example, for testing) and also want to
update its cythonized counterpart, use the responsible |Cythonizer| instance, which is
a member of the subpackage (in case of a base model) or module (in case of an
application model).

Note that it is more effort to maintain Cython code than to maintain Python code.  So
please refrain from writing Cython code when the expected computational time gain is
small or when Python offers other strategies to decrease computation times.


.. toctree::
   :hidden:

   annutils
   configutils
   interfaceutils
   interputils
   modelutils
   pointerutils
   ppolyutils
   quadutils
   rootutils
   sequenceutils
   smoothutils
