.. _Git: https://git-scm.com/
.. _hydpy repository: https://github.com/hydpy-dev/hydpy
.. _GitHub: https://github.com
.. _GitHub account: https://github.com/signup/free
.. _Sourcetree: https://www.sourcetreeapp.com/
.. _Pro Git: https://progit2.s3.amazonaws.com/en/2016-03-22-f3531/progit-en.1084.pdf
.. _How to Rebase a Pull Request: https://github.com/edx/edx-platform/wiki/How-to-Rebase-a-Pull-Request
.. _gitignore: https://github.com/hydpy-dev/hydpy/blob/master/.gitignore

.. _version_control:

Version control
_______________

To work collaboratively on the same software code requires version control.
It must be clear who is working on which part of the code, when (and why)
someone conducted code changes, and which code sections of one developer
are compatible with code sections of another developer (or not).  Also,
one might need to fall back on an older code version when some current
changes turned out to be a dead end.

For *HydPy*, we choose `Git`_ for these tasks.  `Git`_ is a distributed
version control software, allowing for handling multiple repositories
of the same project at different places by different people. Each
repository contains all projects files including their change histories.
We host the main `hydpy repository`_ on `GitHub`_.  So you first should
sing up for a free `GitHub account`_.  After that, you can contribute to
*HydPy* online without installing any software or downloading the repository.
If you are only aiming to improve the documentation, this could be
reasonable.  However, for more substantial contributions you need to
handle a separate *HydPy* repository on your local computer with a local
installation of `Git`_. `Git`_ itself works via command lines, but in
the majority of cases using graphical user interface as `Sourcetree`_
is much more comfortable.

Contributing to *HydPy* essentially requires three or four steps, no matter
if working on `GitHub`_ directly or with your local `Git`_ software. For
simplicity and generality, we explain these steps using the example of a
single file change via `GitHub`_:

  * Go to the main `hydpy repository`_ and click on "Fork", creating a
    new *HydPy* repository under your own `GitHub`_ account, allowing to
    add, change, or delete any files without intervening in the
    development the original `hydpy repository`_.
  * Click on "Branch: master", type a name reflecting your goal (e.g.
    "improve_gitignore" and click on "Create branch: improve_gitignore
    from `master`".  Now that you have created a new branch, you can
    experiment without affecting the master branch of your forked
    repository. (This step is not required, but creating branches for
    different tasks helps to structure your work, to cooperate with others,
    and to keep the "official" history free from unsuccessful experiments.)
  * Change the content of a file.  For example:
      * Click on `gitignore`_.
      * Click on the pen symbol ("Edit this file").
      * change the order of two lines (e.g. "*c." and "*.h")
      * Write something under "Commit changes" to explain your purpose
        (e.g. "change the order of two lines in `.gitignore` to practise it").
      * Click on the green "Commit changes" button.

    Now you have changed the `gitignore`_ file of your specialised branch.
    Typically, you would commit multiple small changes to one branch.
    Keeping the single commits small allows for inspecting and reversing
    different changes.
  * At last, you can suggest incorporating your changes in the original
    `hydpy repository`_.  Click on "Compare & pull request" to visualise
    the relevant differences and add some explanations.  Click on
    "Create pull request" to ask others to discuss your changes and to
    ask the maintainer of the original `hydpy repository`_  to pull and
    merge them into the main development line.

You are responsible for your forked repository only and do not have to
be afraid to break the original `hydpy repository`_ accidentally.
However, you should give your best to focus your pull requests on single
issues and explain them clearly.  Otherwise, the package maintainer
might refuse your contributions in the sake of safeguarding *HydPy's*
code integrity.

Of course, things are not always as easy as in the example above.  Not only
your code changes, but the main line of development evolves as well.
Then you first have to merge the latest changes of the master branch of the
original `hydpy repository`_ into your current working branch, to resolve
some conflicts if necessary, and to "rebase" everything to provide a granular
and understandable pull request.  See the much more thorough explanations
`How to Rebase a Pull Request`_ and `Pro Git`_ to improve your `Git`_ skills.
