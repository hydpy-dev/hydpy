.. _GitHub repository: https://github.com/hydpy-dev/hydpy
.. _GitHub: https://github.com
.. _free GitHub account: https://github.com/signup/free
.. _source tree: https://www.sourcetreeapp.com/
.. _Pro Git: https://progit2.s3.amazonaws.com/en/2016-03-22-f3531/progit-en.1084.pdf
.. _How to Rebase a Pull Request: https://github.com/edx/edx-platform/wiki/How-to-Rebase-a-Pull-Request

.. _version_control:

Version control
_______________

To work in collaboration on the same software code requires some kind
of version control.  It must be clear who is working on which part of
the code, when (and why) code changes were conducted, and which code
sections of one developer are compatible with some code sections of
another developer (or not).  Also, one always needs the possibility to
fall back on an older code version whenever some current changes turned
out to be a dead end.

For HydPy, we selected the version control software Git for these tasks.
The main `GitHub repository`_ is available on `GitHub`_.  So the first
step should be to sing up for a `free GitHub account`_.  After that,
you could contribute to HydPy online without to install anything on
your own computer.  If your only aim is to improve the documentation,
this could be reasonable.  But normally you need to handle Git
repositories on your own computer.  Git itself works via command lines.
Most likely, you would prefer to install Git together with a graphical
user interface like `source tree`_.

To contribute to HydPy requires essentially three or four steps, no matter
if working directly online on GitHub or with your local Git software.  For
simplicity and generality, these steps are explained using the example
of a single change to the documentation via GitHub:

  * Go to this `GitHub repository`_ and click on "Fork".  This is how you
    create your own working copy of HydPy, allowing you to add, change,
    or delete any files without interfering with the original repository.
  * Click on "Branch: master", type a name that reflects what you want
    to accomplish and press enter. Now that you have created a new
    branch, you can experiment without affecting the original branch or your
    own  master branch. (This step is not really required; you could
    apply the following steps on your own master branch likewise.
    But to create branches for different tasks helps to structure your
    work and to cooperate with others.)
  * Change something.  For example
      * click on ".gitignore"
      * click on the marker symbol ("Edit this file")
      * change the order of two lines (e.g. "*c." and "*.h")
      * write something under "Commit changes" to explain your doing
        (e.g. "change the order of lines in .gitignore")
      * click on the green "Commit changes" button

    Now you have changed the file .gitignore in your own branch
    specialized for this task.  Normally, you would commit multiple
    small changes to one branch.  Keeping single commits small allows
    for inspecting and reversing different changes.
  * At last, you can suggest your changes to be included in HydPy's
    main repository.  Click on "Compare" to visualize the relevant
    differences.  Click on "Create pull request" to ask others
    to discuss your changes and to eventually merge them into their
    projects.  In other words: you request other people to pull (get)
    your own changes and to merge (incorporate) these changes into their
    repositories.

Note that everyone is responsible for his or her own repository, you
do not have to be afraid to break another person's repository accidentally.
But you are responsible the make pull requests focussing on one issue
that is clearly explained.  Otherwise, your contribution is likely to be
refused.

Of course, it is not always as easy as in the given example.  Not only
your branches but also the main line of development evolves.  Often,
you will have to retrieve changes from the main branch and eventually
resolve some conflicts before you can make "good" pull request.  See
much more thorough explanations as `Pro Git`_ on how to improve your
skills in using Git.  Here is a very nice description on
`How to Rebase a Pull Request`_ (this could be a good starting point for
explaining how to add newly developed models into the main line in
this documentation).
