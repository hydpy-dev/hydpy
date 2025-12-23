.. _GitHub: https://github.com
.. _hydpy repository: https://github.com/hydpy-dev/hydpy
.. _CPython: https://www.python.org/
.. _requirements.txt: https://github.com/hydpy-dev/hydpy/blob/master/requirements.txt
.. _Cython: http://www.cython.org/
.. _Sphinx: http://www.sphinx-doc.org/en/master/
.. _conf.py: https://github.com/hydpy-dev/hydpy/blob/master/hydpy/docs/sphinx/conf.py
.. _Spyder: https://www.spyder-ide.org/
.. _Anaconda distribution: https://www.anaconda.com/distribution/
.. _PyCharm: https://www.jetbrains.com/pycharm/
.. _type hints: https://docs.python.org/3/library/typing.html
.. _mypy: http://mypy-lang.org/
.. _Git: https://git-scm.com/

.. _required_tools:

Required tools
______________

For simple tasks like fixing typos, a web browser suffices to propose
file changes directly via `GitHub`_ (see section :ref:`version_control`).
Your "pull request" triggers a server-based process, employing all tools
required to test, build, release, and document a new *HydPy* version (see
section :ref:`continuous_integration`).  For an actual release, the
maintainer of the `hydpy repository`_ only needs to accept your request
and "tag" it. However, reaching for more complex goals requires to have
these development tools runnable on your machine.

First, you need the Python interpreter itself. We do our best to keep
*HydPy* up-to-date with the development of Python, so please select the
most recent stable `CPython`_ version.

Second, install all required site-packages listed in `requirements.txt`_.
These include tools like `Cython`_ for translating Python based model
source code into computationally more efficient C code.  Additionally,
you need `Sphinx`_ and its extensions listed in `conf.py`_ for generating
the HTML documentation.

Third, please use a modern Integrated Development Environment (IDE).
Principally, you are free to select any IDE you like (one reasonable
choice for beginners were `Spyder`_, already contained in the
`Anaconda distribution`_), but at least for developers planning more
substantial code contributions, we strongly recommend `PyCharm`_.
We gradually introduce `type hints`_ into *HydPy's* source code and,
so far, prefer `PyCharm`_'s internal type checker over `mypy`_, which
is still not part of the standard library.  One must use `PyCharm`_
specific comments to disable misleading type warnings (and other
misleading warnings as well).

Fourth, you need `Git`_ for version control, as described in the next section.
