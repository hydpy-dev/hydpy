#!python3
"""The script for executing HydPy workflows.

.. _`Python Launcher for Windows`: \
https://docs.python.org/3/using/windows.html#launcher

.. _`here`: https://bitbucket.org/vinay.sajip/pylauncher/downloads//

This script is thought to be called from a command line.  After
successful installation of HydPy, you should be able to invoke it from
anywhere on your computer.  You can test this by just typing `hyd.py` into
your command line.  Then you should find a HydPy log file within
your current working directory, containing the current date in its name.
The following example shows this by using class |TestIO|, to write the
log file into the "iotesting" folder:

>>> import subprocess
>>> from hydpy import TestIO, print_latest_logfile
>>> TestIO.clear()
>>> with TestIO():
...     print_latest_logfile()
Traceback (most recent call last):
...
FileNotFoundError: Cannot find a HydPy log file in directory ...iotesting.
>>> with TestIO():
...     _ = subprocess.call('hyd.py', shell=True)
...     print_latest_logfile()
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
The first argument defining the function to be called is missing.
<BLANKLINE>

If this test example does not work on your machine, you should first make
sure there is a `hyd.py` file in the `Scripts` folder of your Python
distribution, and that a system variable is pointing to this folder.
Windows users should also make sure to have the `Python Launcher for Windows`_
installed.  The Python standard distribution contains this launcher, but
other distributions like Anaconda do not.  You can find the suitable
installer `here`_.

For convenience, we wrap the three required code lines test function "execute":

>>> def execute(command):
...     with TestIO():
...         _ = subprocess.call(command, shell=True)
...         print_latest_logfile()

Without any further arguments, `hyd.py` does not know which function to call:

>>> execute("hyd.py")
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
The first argument defining the function to be called is missing.
<BLANKLINE>

The first additional argument must be an available "script function":

>>> execute("hyd.py "
...         "wrong_argument")
Invoking hyd.py with arguments `...hyd.py, wrong_argument` resulted in the \
following error:
There is no `wrong_argument` function callable by `hyd.py`.  \
Choose one of the following instead: exec_xml and exec_commands
<BLANKLINE>

Further argument requirements depend on the selected "script function":

>>> execute("hyd.py "
...         "exec_commands")
Invoking hyd.py with arguments `...hyd.py, exec_commands` resulted in the \
following error:
Function `exec_commands` requires `1` arguments (commands), but `0` are given.
<BLANKLINE>
>>> execute("hyd.py "
...         "exec_commands "
...         "first_name "
...         "second_name")
Invoking hyd.py with arguments ...hyd.py, exec_commands, first_name, \
second_name` resulted in the following error:
Function `exec_commands` requires `1` arguments (commands), but `2` are given \
(first_name and second_name).
<BLANKLINE>

Error messages raised by the "script function" itself also find their
way into the log file:

>>> execute("hyd.py "
...         "exec_commands "
...         "raise_RuntimeError('it_fails')")
Start to execute the commands ["raise_RuntimeError('it_fails')"] for \
testing purposes.
Invoking hyd.py with arguments `...hyd.py, exec_commands, \
raise_RuntimeError('it_fails')` resulted in the following error:
it fails
<BLANKLINE>

The same is true for warning messages:

>>> execute("hyd.py "
...         "exec_commands "
...         "import_warnings;"
...         "warnings.warn('it_stumbles')")
Start to execute the commands ['import_warnings', \
"warnings.warn('it_stumbles')"] for testing purposes...
...UserWarning: it stumbles
  #!python3
<BLANKLINE>

Each "script function" is allowed to write additional information
into the logging file:

>>> execute("hyd.py "
...         "exec_commands "
...         "logfile.write('it_works')")
Start to execute the commands ["logfile.write('it_works')"] \
for testing purposes.
it works

See the documentation on module |xmltools| for an actually successful
example using the "script function" |exec_xml|.
"""
# import...
# ...from standard library
from typing import IO
import datetime
import inspect
import os
import sys
# ...from hydpy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools


def exec_commands(commands, *, logfile: IO) -> None:
    """Execute the given Python.

    Function |exec_commands| is thought for testing purposes only (see
    the main documentation on module |hyd|).  The given commands must
    be seperated by semicolons, underscores are replaced by whitespaces:

    >>> from hydpy.exe.hyd import exec_commands
    >>> import sys
    >>> exec_commands("x_=_1+1;print(x)", logfile=sys.stdout)
    Start to execute the commands ['x_=_1+1', 'print(x)'] for testing purposes.
    2
    """
    cmdlist = commands.split(';')
    logfile.write(
        f'Start to execute the commands {cmdlist} for testing purposes.\n')
    for command in cmdlist:
        exec(command.replace('_', ' '))


pub.scriptfunctions['exec_commands'] = exec_commands


def print_latest_logfile(dirpath='.'):
    """Print the latest log file in the current or the given working directory.

    See the main documentation on module |hyd| for more information.
    """
    filenames = []
    for filename in os.listdir(dirpath):
        if filename.startswith('hydpy_') and filename.endswith('.log'):
            filenames.append(filename)
    if not filenames:
        raise FileNotFoundError(
            f'Cannot find a HydPy log file in directory '
            f'{os.path.abspath(dirpath)}.')
    with open(sorted(filenames)[-1]) as logfile:
        print(logfile.read())


def execute_scriptfunction():
    """Execute a HydPy script function.

    Function |execute_scriptfunction| is indirectly applied in the
    examples of the main documentation on module |hyd|.
    """
    logfilename = datetime.datetime.now().strftime(
        'hydpy_%Y-%m-%d_%H-%M-%S.%f.log')
    with open(logfilename, 'w'):
        pass

    try:
        try:
            funcname = sys.argv[1]
        except IndexError:
            raise ValueError(
                'The first argument defining the function '
                'to be called is missing.'
            )
        try:
            func = pub.scriptfunctions[funcname]
        except KeyError:
            raise ValueError(
                f'There is no `{funcname}` function callable by `hyd.py`.  '
                f'Choose one of the following instead: '
                f'{objecttools.enumeration(pub.scriptfunctions.keys())}')
        args_given = sys.argv[2:]
        nmb_args_given = len(args_given)
        args_required = inspect.getfullargspec(func).args
        nmb_args_required = len(args_required)
        if nmb_args_given != nmb_args_required:
            enum_args_given = ''
            if nmb_args_given:
                enum_args_given = (
                    f' ({objecttools.enumeration(args_given)})')
            enum_args_required = ''
            if nmb_args_required:
                enum_args_required = (
                    f' ({objecttools.enumeration(args_required)})')
            raise ValueError(
                f'Function `{funcname}` requires `{nmb_args_required:d}` '
                f'arguments{enum_args_required}, but `{nmb_args_given:d}` '
                f'are given{enum_args_given}.')
        stdout = sys.stdout
        try:
            with open(logfilename, 'a') as logfile:
                sys.stdout = logfile
                func(*sys.argv[2:], logfile=logfile)
        finally:
            sys.stdout = stdout
    except BaseException as exc:
        with open(logfilename, 'a') as logfile:
            arguments = ', '.join(sys.argv)
            logfile.write(
                f'Invoking hyd.py with arguments `{arguments}` '
                f'resulted in the following error:\n{str(exc)}\n')


if __name__ == '__main__':   # pragma: no cover
    execute_scriptfunction()


autodoctools.autodoc_module()
