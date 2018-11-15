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
>>> from hydpy import TestIO, print_latest_logfile
>>> TestIO.clear()
>>> with TestIO():
...     print_latest_logfile()    # doctest: +ELLIPSIS
Traceback (most recent call last):
...
FileNotFoundError: Cannot find a HydPy log file in directory ...iotesting.
>>> with TestIO():
...     _ = subprocess.run(
...         'hyd.py',
...         stdout=subprocess.PIPE,
...         stderr=subprocess.PIPE,
...         shell=True)
...     print_latest_logfile()    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
The first argument defining the function to be called is missing.
<BLANKLINE>
See the following stack traceback for debugging:
...

If this test example does not work on your machine, you should first make sure
there is a `hyd.py` file in the `Scripts` folder of your Python distribution,
and that the environment variable `Path` is pointing to this folder.
Windows users should also make sure to have the `Python Launcher for Windows`_
installed.  The Python standard distribution contains this launcher, but
other distributions like Anaconda do not.  You can find the suitable
installer `here`_.

For convenience, we wrap the three required code lines test function "execute":

>>> def execute(command):
...     with TestIO():
...         _ = subprocess.run(command, shell=True)
...         print_latest_logfile()

Without any further arguments, `hyd.py` does not know which function to call:

>>> execute("hyd.py")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
The first argument defining the function to be called is missing.
...

The first additional argument must be an available "script function":

>>> execute("hyd.py "
...         "wrong_argument")    # doctest: +ELLIPSIS
Invoking hyd.py with arguments `...hyd.py, wrong_argument` resulted in the \
following error:
There is no `wrong_argument` function callable by `hyd.py`.  \
Choose one of the following instead: exec_commands, exec_xml, start_server, \
and xml_replace.
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
...         f"z=x+y{esc};"
...         f"print{esc}(z{esc}) "
...         f"x={esc}'2{esc}' "
...         f"y={esc}'=1+1{esc}'")
Start to execute the commands ['z=x+y', 'print(z)'] for testing purposes.
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
<BLANKLINE>

Each "script function" is allowed to write additional information
into the logging file:

>>> execute(f"hyd.py "    # doctest: +ELLIPSIS
...         f"exec_commands "
...         f"logfile.write{esc}({esc}'it_works{esc}'{esc})")
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
import time
import traceback
# ...from hydpy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools


def exec_commands(commands, *, logfile: IO, **parameters) -> None:
    """Execute the given Python.

    Function |exec_commands| is thought for testing purposes only (see
    the main documentation on module |hyd|).  The given commands must
    be seperated by semicolons, underscores are replaced by whitespaces:

    >>> from hydpy.exe.hyd import exec_commands
    >>> import sys
    >>> exec_commands("x_=_1+1;print(x)", logfile=sys.stdout)
    Start to execute the commands ['x_=_1+1', 'print(x)'] for testing purposes.
    2

    Double underscores are interpreted as a single underscore:

    >>> exec_commands("x_=_1;print(x.____class____)", logfile=sys.stdout)
    Start to execute the commands ['x_=_1', 'print(x.____class____)'] \
for testing purposes.
    <class 'int'>

    Additional keyword arguments are evaluated before command execution:

    >>> exec_commands("e=x==y;print(e)", x=1, y=2, logfile=sys.stdout)
    Start to execute the commands ['e=x==y', 'print(e)'] for testing purposes.
    False
    """
    cmdlist = commands.split(';')
    logfile.write(
        f'Start to execute the commands {cmdlist} for testing purposes.\n')
    for par, value in parameters.items():
        exec(f'{par} = {value}')
    for command in cmdlist:
        command = command.replace('__', 'temptemptemp')
        command = command.replace('_', ' ')
        command = command.replace('temptemptemp', '_')
        exec(command)


pub.scriptfunctions['exec_commands'] = exec_commands


def print_latest_logfile(dirpath='.', wait=0.0) -> None:
    """Print the latest log file in the current or the given working directory.

    When processes are executed in parallel, |print_latest_logfile| may
    be called before any log file exists.  Then pass an appropriate
    number of seconds to the argument `wait`.  |print_latest_logfile| then
    prints the contents of the latest log file, as soon as it finds one.

    See the main documentation on module |hyd| for more information.
    """
    now = time.perf_counter()
    wait += now
    filenames = []
    while now <= wait:
        for filename in os.listdir(dirpath):
            if filename.startswith('hydpy_') and filename.endswith('.log'):
                filenames.append(filename)
        if filenames:
            break
        else:
            time.sleep(0.1)
            now = time.perf_counter()
    if not filenames:
        raise FileNotFoundError(
            f'Cannot find a HydPy log file in directory '
            f'{os.path.abspath(dirpath)}.')
    with open(sorted(filenames)[-1]) as logfile:
        print(logfile.read())


def prepare_logfile():
    """Prepare an empty log file and return its absolute path with a
    filename containing the actual date and time.


    >>> from hydpy.exe.hyd import prepare_logfile
    >>> from hydpy import TestIO
    >>> from hydpy.core.testtools import mock_datetime_now
    >>> from datetime import datetime
    >>> with TestIO():
    ...     with mock_datetime_now(datetime(2000, 1, 1, 12, 30, 0)):
    ...         filepath = prepare_logfile()
    >>> import os
    >>> os.path.exists(filepath)
    True
    >>> filepath    # doctest: +ELLIPSIS
    '...hydpy...tests...iotesting...hydpy_2000-01-01_12-30-00.log'
    """
    filename = datetime.datetime.now().strftime(
        'hydpy_%Y-%m-%d_%H-%M-%S.log')
    with open(filename, 'w'):
        pass
    return os.path.abspath(filename)


def execute_scriptfunction():
    """Execute a HydPy script function.

    Function |execute_scriptfunction| is indirectly applied in the
    examples of the main documentation on module |hyd|.  We repeat
    these examples here for measuring code coverage:


    >>> import sys
    >>> from hydpy import TestIO
    >>> from hydpy.exe.hyd import execute_scriptfunction
    >>> def execute(commands):
    ...     sys.argv = commands.split()
    ...     with TestIO():
    ...         execute_scriptfunction()
    ...         print_latest_logfile()

    >>> execute("hyd.py")    # doctest: +ELLIPSIS
    Invoking hyd.py with arguments `...hyd.py` resulted in the following error:
    The first argument defining the function to be called is missing.
    <BLANKLINE>
    See the following stack traceback for debugging:
    ...

    >>> execute("hyd.py "
    ...         "wrong_argument")    # doctest: +ELLIPSIS
    Invoking hyd.py with arguments `...hyd.py, wrong_argument` resulted \
in the following error:
    There is no `wrong_argument` function callable by `hyd.py`.  \
Choose one of the following instead: exec_commands, exec_xml, start_server, \
and xml_replace.
    ...

    >>> execute("hyd.py "
    ...         "exec_commands")    # doctest: +ELLIPSIS
    Invoking hyd.py with arguments `...hyd.py, exec_commands` resulted \
in the following error:
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
but `2` are given (first_name and second_name).
    ...

    >>> execute("hyd.py "
    ...         "exec_commands "
    ...         "z=x+y;"
    ...         "print(z) "
    ...         "x='2' "
    ...         "y='=1+1'")
    Start to execute the commands ['z=x+y', 'print(z)'] for testing purposes.
    2=1+1
    <BLANKLINE>

    >>> execute(f"hyd.py "
    ...         f"exec_commands "
    ...         f"raise_RuntimeError('it_fails')")    # doctest: +ELLIPSIS
    Start to execute the commands ["raise_RuntimeError('it_fails')"] for \
testing purposes.
    Invoking hyd.py with arguments `...hyd.py, exec_commands, \
raise_RuntimeError('it_fails')` resulted in the following error:
    it fails
    ...

    >>> import warnings
    >>> warnings.filterwarnings('always', 'it stumbles')
    >>> execute(f"hyd.py "
    ...         f"exec_commands "
    ...         f"import_warnings;"
    ...         f"warnings.warn('it_stumbles')")    # doctest: +ELLIPSIS
    Start to execute the commands ['import_warnings', \
"warnings.warn('it_stumbles')"] for testing purposes...
    ...UserWarning: it stumbles
      #...
    <BLANKLINE>

    >>> execute(f"hyd.py "
    ...         f"exec_commands "
    ...         f"logfile.write('it_works')")    # doctest: +ELLIPSIS
    Start to execute the commands ["logfile.write('it_works')"] \
for testing purposes.
    it works
    """
    logfilepath = prepare_logfile()
    try:
        try:
            funcname = sys.argv[1]
        except IndexError:
            raise ValueError(
                'The first argument defining the function '
                'to be called is missing.')
        try:
            func = pub.scriptfunctions[funcname]
        except KeyError:
            available_funcs = objecttools.enumeration(
                sorted(pub.scriptfunctions.keys()))
            raise ValueError(
                f'There is no `{funcname}` function callable by `hyd.py`.  '
                f'Choose one of the following instead: {available_funcs}.')
        args_required = inspect.getfullargspec(func).args
        nmb_args_required = len(args_required)
        args_given = []
        kwargs_given = {}
        for idx, arg in enumerate(sys.argv[2:]):
            if idx < nmb_args_required:
                args_given.append(arg)
            else:
                try:
                    key, value = parse_argument(arg)
                    kwargs_given[key] = value
                except ValueError:
                    args_given.append(arg)
        nmb_args_given = len(args_given)
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
                f'positional arguments{enum_args_required}, but '
                f'`{nmb_args_given:d}` are given{enum_args_given}.')
        stdout = sys.stdout
        try:
            with open(logfilepath, 'a') as logfile:
                sys.stdout = logfile
                func(*args_given, **kwargs_given, logfile=logfile)
        finally:
            sys.stdout = stdout
    except BaseException as exc:
        with open(logfilepath, 'a') as logfile:
            arguments = ', '.join(sys.argv)
            logfile.write(
                f'Invoking hyd.py with arguments `{arguments}` '
                f'resulted in the following error:\n{str(exc)}\n\n'
                f'See the following stack traceback for debugging:\n')
            traceback.print_tb(sys.exc_info()[2], file=logfile)


def parse_argument(string):
    """Return a single value for a string understood as a positional
    argument or a |tuple| containing a keyword and its value for a
    string understood as a keyword argument.

    |parse_argument| is intended to be used as a helper function for
    function |execute_scriptfunction| only.  See the following
    examples to see which types of keyword arguments |execute_scriptfunction|
    covers:

    >>> from hydpy.exe.hyd import parse_argument
    >>> parse_argument('x=3')
    ('x', '3')
    >>> parse_argument('"x=3"')
    '"x=3"'
    >>> parse_argument("'x=3'")
    "'x=3'"
    >>> parse_argument('x="3==3"')
    ('x', '"3==3"')
    >>> parse_argument("x='3==3'")
    ('x', "'3==3'")
    """
    idx_equal = string.find('=')
    if idx_equal == -1:
        return string
    idx_quote = idx_equal+1
    for quote in ('"', "'"):
        idx = string.find(quote)
        if -1 < idx < idx_quote:
            idx_quote = idx
    if idx_equal < idx_quote:
        return string[:idx_equal], string[idx_equal+1:]
    return string


if __name__ == '__main__':   # pragma: no cover
    execute_scriptfunction()


autodoctools.autodoc_module()
