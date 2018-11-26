#!python3
"""The script for executing HydPy workflows.

.. _`Python Launcher for Windows`: \
https://docs.python.org/3/using/windows.html#launcher

.. _`here`: https://bitbucket.org/vinay.sajip/pylauncher/downloads

This script is thought to be called from a command line.  After
successful installation of HydPy, you should be able to invoke it from
anywhere on your computer.  You can test this by just typing `hyd.py` into
your command line.  Then you should find a HydPy log file within
your current working directory, containing the current date in its name.
The following example shows this by using class |TestIO|, to write the
log file into the "iotesting" folder:

>>> import subprocess
>>> from hydpy import repr_, TestIO, print_latest_logfile
>>> TestIO.clear()
>>> with TestIO():
...     print_latest_logfile()    # doctest: +ELLIPSIS
Traceback (most recent call last):
...
FileNotFoundError: Cannot find a HydPy log file in directory ...iotesting.
>>> with TestIO():
...     _ = subprocess.run("hyd.py", shell=True)
...     print_latest_logfile()    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
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

>>> from hydpy.exe import hyd
>>> command = f"python {hyd.__file__}"
>>> repr_(command)    # doctest: +ELLIPSIS
'python .../hydpy/exe/hyd.py'
>>> TestIO.clear()
>>> with TestIO():
...     _ = subprocess.run(command, shell=True)
...     print_latest_logfile()    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
The first positional argument defining the function to be called is missing.
...

You are free to choose different log file names:

>>> with TestIO():
...     _ = subprocess.run("hyd.py logfile=my_log_file.txt", shell=True)
...     with open('my_log_file.txt') as logfile:
...         print(logfile.read())    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py, logfile=my_log_file.txt` resulted \
in the following error:
The first positional argument defining the function to be called is missing.
...

For convenience, we define the function `execute` to shorten the following
examples:

>>> def execute(command):
...     with TestIO():
...         _ = subprocess.run(command, shell=True)
...         print_latest_logfile()

Without any further arguments, `hyd.py` does not know which function to call:

>>> execute("hyd.py")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
The first positional argument defining the function to be called is missing.
...

The first additional argument must be an available "script function":

>>> execute("hyd.py "
...         "wrong_argument")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py, wrong_argument` resulted in the \
following error:
There is no `wrong_argument` function callable by `hyd.py`.  Choose one of \
the following instead: exec_commands, run_simulation, start_server, \
and xml_replace
...

Further argument requirements depend on the selected "script function":

>>> execute("hyd.py "
...         "exec_commands")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py, exec_commands` resulted in the \
following error:
Function `exec_commands` requires `1` positional arguments (commands), \
but `0` are given.
...
>>> execute("hyd.py "
...         "exec_commands "
...         "first_name "
...         "second_name")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py, exec_commands, first_name, \
second_name` resulted in the following error:
Function `exec_commands` requires `1` positional arguments (commands), \
but `2` are given \
(first_name and second_name).
...

Optional keyword arguments are supported: (on Linux, we have to escape
the characters "(", ")", ";", and "'" in the following)

>>> import platform
>>> esc = '' if 'windows' in platform.platform().lower() else '\\\\'
>>> execute(f"hyd.py "
...         f"exec_commands "
...         f"print{esc}(x+y{esc}) "
...         f"x={esc}'2{esc}' "
...         f"y={esc}'=1+1{esc}'")
Start to execute the commands ['print(x+y)'] for testing purposes.
2=1+1
<BLANKLINE>

Error messages raised by the "script function" itself also find their
way into the log file:

>>> execute(f"hyd.py "    # doctest: +ELLIPSIS
...         f"exec_commands "
...         f"raise_RuntimeError{esc}({esc}'it_fails{esc}'{esc})")
Start to execute the commands ["raise_RuntimeError('it_fails')"] for \
testing purposes.
Invoking hyd.py with arguments `...hyd.py, exec_commands, \
raise_RuntimeError('it_fails')` resulted in the following error:
it fails
...

The same is true for warning messages:

>>> execute(f"hyd.py "    # doctest: +ELLIPSIS
...         f"exec_commands "
...         f"import_warnings{esc};"
...         f"warnings.warn{esc}({esc}'it_stumbles{esc}'{esc})")
Start to execute the commands ['import_warnings', \
"warnings.warn('it_stumbles')"] for testing purposes...
...UserWarning: it stumbles
  #...
...

Each "script function" is allowed to write additional information
into the logging file:

>>> execute(f"hyd.py "    # doctest: +ELLIPSIS
...         f"exec_commands "
...         f"logfile.write{esc}({esc}'it_works{esc}'{esc})")
Start to execute the commands ["logfile.write('it_works')"] \
for testing purposes.
it works

To report the importance level of individual log messages, use the
optional `logstyle` keyword argument:

>>> execute(f"hyd.py "    # doctest: +ELLIPSIS
...         f"exec_commands "
...         f"print{esc}({esc}'it_works{esc}'{esc}){esc};"
...         f"import_warnings{esc};"
...         f"warnings.warn{esc}({esc}'it_stumbles{esc}'{esc}){esc};"
...         f"raise_RuntimeError{esc}({esc}'it_fails{esc}'{esc}) "
...         f"logstyle=prefixed")
info: Start to execute the commands ["print('it_works')", 'import_warnings', \
"warnings.warn('it_stumbles')", "raise_RuntimeError('it_fails')"] for \
testing purposes.
info: it works
warning: ...UserWarning: it stumbles
warning:   # -*- coding: utf-8 -*-
error: Invoking hyd.py with arguments ...hyd.py, exec_commands, \
print('it_works');import_warnings;warnings.warn('it_stumbles');\
raise_RuntimeError('it_fails'), logstyle=prefixed` resulted in \
the following error:
error: it fails
...

So far, only `prefixed` and the default style `plain` are implemented:

>>> execute(f"hyd.py "    # doctest: +ELLIPSIS
...         f"exec_commands "
...         f"None "
...         f"logstyle=missing")
Invoking hyd.py with arguments `...hyd.py, exec_commands, None, \
logstyle=missing` resulted in the following error:
The given log file style missing is not available.  Please choose one \
of the following: plain and prefixed.
...

See the documentation on module |xmltools| for an actually successful
example using the "script function" |run_simulation|.
"""
# import...
# ...from hydpy
from hydpy.core import autodoctools
from hydpy.exe import commandtools


if __name__ == '__main__':
    commandtools.execute_scriptfunction()


autodoctools.autodoc_module()
