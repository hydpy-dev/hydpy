.. _The Python Standard Library: https://docs.python.org/2/library/
.. _Cython: http://www.cython.org/
.. _NumPy: http://www.numpy.org/
.. _matplotlib: http://matplotlib.org/

.. _hydpydependencies:

Dependencies
____________

Whenever reasonable, import only packages of
`The Python Standard Library`_ or at least restrict yourself
to mature and stable site-packages.  At the moment, HydPy relies
only on the highly accepted site-packages `Cython`_, `NumPy`_,
and `matplotlib`_.  Further developments of HydPy based on more
specialized site-packages (e.g. for plotting maps) might be
useful.  But the related import commands should be secured in
a way that allows for the application of HydPy without having
these specialized site-packages available.
