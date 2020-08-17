#!/usr/bin/env python
"""The script for executing HydPy workflows.

.. _`Python Launcher for Windows`: \
https://docs.python.org/3/using/windows.html#launcher

.. _`here`: https://bitbucket.org/vinay.sajip/pylauncher/downloads

This script is thought to be called from a command line.  After
successful installation of HydPy, you should be able to invoke it from
anywhere on your computer.  You can test this by just typing `hyd.py` into
your command line:

>>> import subprocess
>>> from hydpy import run_subprocess
>>> result = run_subprocess("hyd.py")    # doctest: +ELLIPSIS
Invoking hyd.py without arguments resulted in the following error:
The first positional argument defining the function to be called is missing.
<BLANKLINE>
See the following stack traceback for debugging:
...

If this test example does not work on your machine, you should first make sure
there is a `hyd.py` file in the `Scripts` folder of your Python distribution,
and that the environment variable `Path` is pointing to this folder.
Windows users should also make sure to have the `Python Launcher for Windows`_
installed.  The Python standard distribution contains this launcher, but
other distributions like Anaconda do not.  You can find the suitable
installer `here`_.  As a stopgap, you could directly call Python and pass
the complete path of the `hyd.py` file available in your *HydPy* site-packages
folder as an argument:

>>> import sys
>>> from hydpy.exe import hyd
>>> command = f"{sys.executable} {hyd.__file__}"
>>> from hydpy import repr_
>>> repr_(command)    # doctest: +ELLIPSIS
'...python... .../hydpy/exe/hyd.py'
>>> result = run_subprocess(command)    # doctest: +ELLIPSIS
Invoking hyd.py without arguments resulted in the following error:
The first positional argument defining the function to be called is missing.
...

You are free to redirect output to a log file:

>>> from hydpy import TestIO
>>> TestIO.clear()
>>> with TestIO():
...     result = run_subprocess("hyd.py logfile=my_log_file.txt")
>>> with TestIO():
...     with open('my_log_file.txt') as logfile:
...         print(logfile.read())    # doctest: +ELLIPSIS
Invoking hyd.py with argument `logfile=my_log_file.txt` resulted in the \
following error:
The first positional argument defining the function to be called is missing.
...

When passing `default` as keyword argument `logfile`, function
|prepare_logfile| generates a default name containing the current
date and time:

>>> import os
>>> with TestIO():
...     result = run_subprocess("hyd.py logfile=default")
>>> with TestIO():
...     for filename in os.listdir('.'):
...         if filename.endswith('.log'):
...             print(filename)    # doctest: +ELLIPSIS
hydpy_...log


Without any further arguments, `hyd.py` does not know which function to call:

>>> result = run_subprocess("hyd.py")    # doctest: +ELLIPSIS
Invoking hyd.py without arguments resulted in the following error:
The first positional argument defining the function to be called is missing.
...

The first additional argument must be an available "script function":

>>> result = run_subprocess("hyd.py "
...                         "wrong_argument")    # doctest: +ELLIPSIS
Invoking hyd.py with argument `wrong_argument` resulted in the \
following error:
There is no `wrong_argument` function callable by `hyd.py`.  Choose one of \
the following instead: await_server, exec_commands, exec_script, \
run_simulation, start_server, start_shell, test_everything, and xml_replace.
...

Further argument requirements depend on the selected "script function":

>>> result = run_subprocess("hyd.py "
...                         "exec_commands")    # doctest: +ELLIPSIS
Invoking hyd.py with argument `exec_commands` resulted in the \
following error:
Function `exec_commands` requires `1` positional arguments (commands), \
but `0` are given.
...
>>> result = run_subprocess("hyd.py "
...                         "exec_commands "
...                         "first_name "
...                         "second_name")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `exec_commands, first_name, second_name` \
resulted in the following error:
Function `exec_commands` allows `1` positional arguments (commands), \
but `2` are given \
(first_name and second_name).
...

Optional keyword arguments are supported: (on Linux, we have to escape
the characters "(", ")", ";", and "'" in the following)

>>> import platform
>>> esc = '' if 'windows' in platform.platform().lower() else '\\\\'
>>> result = run_subprocess(f"hyd.py "
...                         f"exec_commands "
...                         f"print{esc}(x+y{esc}) "
...                         f"x={esc}'2{esc}' "
...                         f"y={esc}'=1+1{esc}'")
Start to execute the commands ['print(x+y)'] for testing purposes.
2=1+1

Error messages raised by the "script function" itself also find their
way into the console or log file:

>>> result = run_subprocess(    # doctest: +ELLIPSIS
...    f"hyd.py exec_commands "
...    f"raise_RuntimeError{esc}({esc}'it_fails{esc}'{esc})")
Start to execute the commands ["raise_RuntimeError('it_fails')"] for \
testing purposes.
Invoking hyd.py with arguments `exec_commands, raise_RuntimeError('it_fails')` \
resulted in the following error:
it fails
...

The same is true for warning messages:

>>> result = run_subprocess(f"hyd.py "    # doctest: +ELLIPSIS
...                         f"exec_commands "
...                         f"import_warnings{esc};"
...                         f"warnings.warn{esc}({esc}'it_stumbles{esc}'{esc})")
Start to execute the commands ['import_warnings', \
"warnings.warn('it_stumbles')"] for testing purposes...
...UserWarning: it stumbles

And the same is true for printed messages:

>>> result = run_subprocess(f"hyd.py "
...                         f"exec_commands "
...                         f"print{esc}({esc}'it_works{esc}'{esc})")
Start to execute the commands ["print('it_works')"] \
for testing purposes.
it works

To report the importance level of individual log messages, use the
optional `logstyle` keyword argument:

>>> result = run_subprocess(     # doctest: +ELLIPSIS
...     f"hyd.py exec_commands "
...     f"print{esc}({esc}'it_works{esc}'{esc}){esc};"
...     f"import_warnings{esc};"
...     f"warnings.warn{esc}({esc}'it_stumbles{esc}'{esc}){esc};"
...     f"raise_RuntimeError{esc}({esc}'it_fails{esc}'{esc}) "
...     f"logstyle=prefixed")
info: Start to execute the commands ["print('it_works')", 'import_warnings', \
"warnings.warn('it_stumbles')", "raise_RuntimeError('it_fails')"] for \
testing purposes.
info: it works
warning: ...UserWarning: it stumbles
error: Invoking hyd.py with arguments `exec_commands, \
print('it_works');import_warnings;warnings.warn('it_stumbles');\
raise_RuntimeError('it_fails'), logstyle=prefixed` resulted in \
the following error:
error: it fails
...

So far, only `prefixed` and the default style `plain` are implemented:

>>> result = run_subprocess(f"hyd.py "    # doctest: +ELLIPSIS
...                         f"exec_commands "
...                         f"None "
...                         f"logstyle=missing")
Invoking hyd.py with arguments `exec_commands, None, logstyle=missing` \
resulted in the following error:
The given log file style missing is not available.  Please choose one \
of the following: plain and prefixed.
...

See the documentation on module |xmltools| for an actually successful
example using the "script function" |run_simulation|.
"""
# import...
# ...from standard-library
import sys
# ...from hydpy
from hydpy.exe import commandtools


def execute() -> None:
    """Call |execute_scriptfunction| of module |commandtools| in case |hyd|
    is the main script.

    >>> from hydpy.exe import hyd
    >>> from unittest import mock
    >>> with mock.patch('hydpy.exe.commandtools.execute_scriptfunction') as fun:
    ...     with mock.patch('sys.exit') as exit_:
    ...         with mock.patch.object(hyd, '__name__', '__not_main__'):
    ...             hyd.execute()
    ...             exit_.called
    False
    >>> for return_value in (None, 0, 2):
    ...     with mock.patch(
    ...             'hydpy.exe.commandtools.execute_scriptfunction',
    ...             return_value=return_value) as fun:
    ...         with mock.patch('sys.exit') as exit_:
    ...             with mock.patch.object(hyd, '__name__', '__main__'):
    ...                 hyd.execute()
    ...                 exit_.call_args
    call(False)
    call(False)
    call(True)
    """
    if __name__ == '__main__':
        sys.exit(bool(commandtools.execute_scriptfunction()))


execute()
