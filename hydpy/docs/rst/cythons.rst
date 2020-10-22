
.. _cythons:

Cython Tools
============

The modules of subpackage `cythons` should be of interest for framework
developers (and eventually some model developers) only.

The most important module (and so far the only one which is actually a
Python module) is |modelutils|, which implements the routines to translate
Python code into Cython code, to translate Cython code into C code, to
compile C code, and to embed the compilation into a "Python dll"
(a "pyd" file on Windows and a "so" file on Linux systems).

The other modules are Cython extension files.  Often they are named
similar to the Python modules of other packages (see for example |anntools|
and :ref:`annutils`).  The respective Cython extension file then implements
the performance critical part of the the required functionality.

The required dll files are automatically generated when *HydPy*
is installed and stored in the `cythons` subpackage `autogen`.  The
dll files of the different hydrological models are also stored in
`autogen`.  But they are automatically updated each time class
|Cythonizer| of module |modelutils| detects a change in the code base
of the model or of *HydPy* that could affect the models functionality.

Note that it is always harder to maintain Cython code than it is to
maintain Python code.  So please refrain from writing Cython code
when the expected computational time gain is small or when Python
offers other strategies to decrease computation times.


.. toctree::
   :hidden:

   annutils
   configutils
   modelutils
   pointerutils
   sequenceutils
   smoothutils
   rootutils
