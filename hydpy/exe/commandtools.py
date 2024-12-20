"""This module implements some main features for using *HydPy* from your command line
tools via script |hyd|."""

# import...
# ...from standard library
from __future__ import annotations
import contextlib
import datetime
import inspect
import os
import runpy
import subprocess
import sys
import time
import traceback

# ...from hydpy
import hydpy
import hydpy.tests.run_doctests
from hydpy import config
from hydpy.core import objecttools
from hydpy.core.typingtools import *


@overload
def run_subprocess(
    command: str, *, verbose: bool = True, blocking: Literal[True] = ...
) -> subprocess.CompletedProcess[str]:
    """non-blocking"""


@overload
def run_subprocess(
    command: str, *, verbose: bool = True, blocking: Literal[False]
) -> subprocess.Popen[str]:
    """blocking"""


def run_subprocess(
    command: str, *, verbose: bool = True, blocking: bool = True
) -> subprocess.CompletedProcess[str] | subprocess.Popen[str]:
    """Execute the given command in a new process.

    Only when both `verbose` and `blocking` are |True|, |run_subprocess| prints all
    responses to the current value of `sys.stdout`:

    >>> from hydpy import run_subprocess
    >>> import platform
    >>> esc = "" if "windows" in platform.platform().lower() else "\\\\"
    >>> result = run_subprocess(f"python -c print{esc}(1+1{esc})")
    2

    With verbose being |False|, |run_subprocess| never prints anything:

    >>> result = run_subprocess(f"python -c print{esc}(1+1{esc})", verbose=False)

    >>> process = run_subprocess("python", blocking=False, verbose=False)
    >>> process.kill()
    >>> _ = process.communicate()

    When `verbose` is |True| and `blocking` is |False|, |run_subprocess| prints all
    responses to the console ("invisible" for doctests):

    >>> process = run_subprocess("python", blocking=False)
    >>> process.kill()
    >>> _ = process.communicate()
    """
    command = command.strip()
    if command.startswith("python"):
        command = f"{sys.executable}{command[6:]}"
    if blocking:
        result1 = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            shell=True,
            check=False,
            env=dict(os.environ),
        )
        if verbose:  # due to doctest replacing sys.stdout
            for output in (result1.stdout, result1.stderr):
                output = output.strip()
                if output:
                    print(output)
        return result1
    stdouterr = None if verbose else subprocess.DEVNULL
    result2 = subprocess.Popen(  # pylint: disable=consider-using-with
        command,
        stdout=stdouterr,
        stderr=stdouterr,
        encoding="utf-8",
        shell=True,
        env=dict(os.environ),
    )
    return result2


def exec_commands(commands: str, **parameters: Any) -> None:
    """Execute the given Python commands.

    Function |exec_commands| is thought for testing purposes only (see the main
    documentation on module |hyd|).  Separate individual commands by semicolons and
    replaced whitespaces with underscores:

    >>> from hydpy.exe.commandtools import exec_commands
    >>> import sys
    >>> exec_commands("x_=_1+1;print(x)")
    Start to execute the commands ['x_=_1+1', 'print(x)'] for testing purposes.
    2

    |exec_commands| interprets double underscores as a single underscores:

    >>> exec_commands("x_=_1;print(x.____class____)")
    Start to execute the commands ['x_=_1', 'print(x.____class____)'] \
for testing purposes.
    <class 'int'>

    |exec_commands| evaluates additional keyword arguments before it executes the given
    commands:

    >>> exec_commands("e=x==y;print(e)", x=1, y=2)
    Start to execute the commands ['e=x==y', 'print(e)'] for testing purposes.
    False
    """
    cmdlist = commands.split(";")
    print(f"Start to execute the commands {cmdlist} for testing purposes.")
    for par, value in parameters.items():
        exec(f"{par} = {value}")
    for command in cmdlist:
        command = command.replace("__", "temptemptemp")
        command = command.replace("_", " ")
        command = command.replace("temptemptemp", "_")
        exec(command)


def run_doctests() -> int:  # pylint: disable=inconsistent-return-statements
    """Execute the main function of script `run_doctests.py` from remote.

    Whenever in doubt about the functioning of your *HydPy* installation, call the
    script function |run_doctests|.  It executes all tests employed before your actual
    *HydPy* version was released, which allows you to check for possible
    incompatibilities with the site-packages or the configuration of your specific
    system.

    |run_doctests| calls the mentioned function with default arguments and returns its
    exit code:

    >>> from hydpy import run_doctests
    >>> from unittest import mock
    >>> with mock.patch("hydpy.tests.run_doctests.main.callback",
    ...                 side_effect=SystemExit(1)) as main:
    ...     run_doctests()
    1
    >>> assert "hydpy_path=None" in str(main.mock_calls)
    >>> assert "file_doctests=[]" in str(main.mock_calls)
    >>> assert "python_mode=True" in str(main.mock_calls)
    >>> assert "cython_mode=True" in str(main.mock_calls)
    """
    try:
        callback = cast(Callable[..., NoReturn], hydpy.tests.run_doctests.main.callback)
        callback(hydpy_path=None, file_doctests=[], python_mode=True, cython_mode=True)
    except SystemExit as exc:
        return code if isinstance(code := exc.code, int) else 999


def exec_script(filepath: str) -> None:
    """Execute an arbitrary Python script.

    Function |run_simulation| allows you to execute a predefined *HydPy* workflow.  You
    can configure many details of this workflow but not change its general structure.
    Use function |exec_script| execute *HydPy* remotely but strive for more flexibility.
    As its name suggests, function |exec_script| executes any valid Python code relying
    on the standard library and the available site-packages.

    Function |exec_script| requires the name of the script to be executed as a single
    argument:

    >>> from hydpy import print_latest_logfile, Node, TestIO, run_subprocess
    >>> TestIO.clear()
    >>> with TestIO():
    ...     result = run_subprocess('hyd.py logfile="default" exec_script temp.py')
    ...     print_latest_logfile()    # doctest: +ELLIPSIS
    Invoking hyd.py with arguments `logfile=default, exec_script, temp.py` \
resulted in the following error:
    File `...temp.py` does not exist.
    ...

    Function |exec_script| can use all *HydPy* features.  As a simple example, we write
    a Python script that initialises a |Node| object and prints its string
    representation (into the log file):

    >>> with TestIO():
    ...     with open("temp.py", "w") as file_:
    ...         _ = file_.write("from hydpy import Node\\n")
    ...         _ = file_.write('print(repr(Node("valid_name")))\\n')
    ...     result = run_subprocess('hyd.py logfile="default" exec_script temp.py')
    ...     print_latest_logfile()
    Node("valid_name", variable="Q")
    <BLANKLINE>

    Errors are reported as usual:

    >>> with TestIO():
    ...     with open("temp.py", "w") as file_:
    ...         _ = file_.write("from hydpy import Node\\n")
    ...         _ = file_.write('print(repr(Node("invalid name")))\\n')
    ...     result = run_subprocess('hyd.py logfile="default" exec_script temp.py')
    ...     print_latest_logfile()    # doctest: +ELLIPSIS
    Invoking hyd.py with arguments `logfile=default, exec_script, temp.py` resulted \
in the following error:
    While trying to initialize a `Node` object with value `invalid name` of type \
`str`, the following error occurred: The given name string `invalid name` does not \
define a valid variable identifier.  Valid identifiers do not contain characters like \
`-` or empty spaces, do not start with numbers, cannot be mistaken with Python \
built-ins like `for`...)
    ...
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File `{os.path.abspath(filepath)}` does not exist.")
    runpy.run_path(filepath)


def start_shell(filepath: str = "") -> None:
    """Open an interactive Python shell.

    Writing "hyd.py start_shell" into your command line tool opens an interactive
    Python console with the most relevant *HydPy* features being imported already.  In
    our first example, we directly prepare an |Element| object (without needing to
    import class |Element| first) and print its string representation:

    >>> import subprocess
    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> with TestIO():
    ...     with subprocess.Popen(
    ...             "hyd.py start_shell",
    ...             stdin=subprocess.PIPE,
    ...             stdout=subprocess.PIPE,
    ...             stderr=subprocess.PIPE,
    ...             encoding="utf-8",
    ...             shell=True) as process:
    ...         response = process.communicate(
    ...             'print(repr(Element("e1", outlets="n1")))')
    ...         print(response[0])
    Element("e1",
            outlets="n1")
    <BLANKLINE>

    You can pass the name of a Python file as an additional argument, which enables
    interaction with the file results.  We create the example file `test.py` for
    demonstration purposes, simply defining a |Nodes| object handling two individual
    nodes:

    >>> with TestIO():
    ...     with open("test.py", "w") as file_:
    ...         _ = file_.write("from hydpy import Nodes\\n")
    ...         _ = file_.write('nodes = Nodes("n1", "n2")\\n')

    Now we can, execute this file and, for example, query the names of
    the defined nodes interactively:

    >>> with TestIO():
    ...     with subprocess.Popen(
    ...             "hyd.py start_shell test.py",
    ...             stdin=subprocess.PIPE,
    ...             stdout=subprocess.PIPE,
    ...             stderr=subprocess.PIPE,
    ...             encoding="utf-8",
    ...             shell=True) as process:
    ...         response = process.communicate(
    ...             "print(nodes.names)")
    ...         print(response[0])
    ('n1', 'n2')
    <BLANKLINE>
    """
    if filepath:
        filepath_ = filepath
    else:
        filepath_ = "__hydpy_temp__"
        with open("__hydpy_temp__", "w", encoding=config.ENCODING) as file_:
            file_.write("from hydpy import *")
    subprocess.run([sys.executable, "-i", filepath_], check=True)
    if not filepath:
        os.remove(filepath_)

    # First steps to use IPython instead:
    # import IPython
    # IPython.start_ipython()
    # console = IPython.get_ipython()
    # console.run_code(compile("print(1+1", "_", "exec"))
    # console.run_code(compile("from hydpy import *", "_", "exec"))


def print_latest_logfile(dirpath: str = ".", wait: float = 0.0) -> None:
    """Print the latest log file in the current or the given working directory.

    When executing processes in parallel, |print_latest_logfile| may be called before
    any log file exists.  Then pass an appropriate number of seconds to the argument
    `wait`.  |print_latest_logfile| prints the contents of the latest log file as soon
    as it finds one. Function |print_latest_logfile| works only for "default" logfile
    names, as described in the documentation on function |prepare_logfile|.

    >>> from hydpy import TestIO, print_latest_logfile, run_subprocess
    >>> TestIO.clear()
    >>> with TestIO():
    ...     result = run_subprocess("hyd.py")
    ...     print_latest_logfile(wait=0.5)    # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: Cannot find a default HydPy log file in directory ...iotesting.

    >>> with TestIO():
    ...     result1 = run_subprocess('hyd.py logfile="default" test=1')
    ...     result2 = run_subprocess('hyd.py logfile="default" test=2')
    ...     print_latest_logfile(wait=0.5)    # doctest: +ELLIPSIS
    Invoking hyd.py with arguments `logfile=default, test=2` resulted in the \
following error:
    ...
    """
    now = time.perf_counter()
    wait += now
    filenames = []
    while now <= wait:
        for filename in sorted(os.listdir(dirpath)):
            if filename.startswith("hydpy_") and filename.endswith(".log"):
                filenames.append(filename)
        if filenames:
            break
        time.sleep(0.1)
        now = time.perf_counter()
    if not filenames:
        raise FileNotFoundError(
            f"Cannot find a default HydPy log file in directory "
            f"{os.path.abspath(dirpath)}."
        )
    with open(sorted(filenames)[-1], encoding=config.ENCODING) as logfile:
        print(logfile.read())


def prepare_logfile(filename: str) -> str:
    """Prepare an empty log file eventually and return its absolute path.

    When passing the "filename" `stdout`, |prepare_logfile| does not prepare any file
    and just returns `stdout`:

    >>> from hydpy.exe.commandtools import prepare_logfile
    >>> prepare_logfile("stdout")
    'stdout'

    When passing the "filename" `default`, |prepare_logfile| generates a filename
    containing the actual date and time, prepares an empty file on disk, and returns
    its path:

    >>> from hydpy import repr_, TestIO
    >>> from hydpy.core.testtools import mock_datetime_now
    >>> from datetime import datetime
    >>> with TestIO():
    ...     with mock_datetime_now(datetime(2000, 1, 1, 12, 30, 0)):
    ...         filepath = prepare_logfile("default")
    >>> import os
    >>> os.path.exists(filepath)
    True
    >>> repr_(filepath)    # doctest: +ELLIPSIS
    '...hydpy/tests/iotesting/hydpy_2000-01-01_12-30-00.log'

    For all other strings, |prepare_logfile| does not add any date or time information
    to the filename:

    >>> with TestIO():
    ...     with mock_datetime_now(datetime(2000, 1, 1, 12, 30, 0)):
    ...         filepath = prepare_logfile("my_log_file.txt")
    >>> os.path.exists(filepath)
    True
    >>> repr_(filepath)    # doctest: +ELLIPSIS
    '...hydpy/tests/iotesting/my_log_file.txt'
    """
    if filename == "stdout":
        return filename
    if filename == "default":
        filename = datetime.datetime.now().strftime("hydpy_%Y-%m-%d_%H-%M-%S.log")
    with open(filename, "w", encoding=config.ENCODING):
        pass
    return os.path.abspath(filename)


@contextlib.contextmanager
def _activate_logfile(
    filepath: str,
    logstyle: str,
    level_stdout: Literal["info", "warning", "exception"],
    level_stderr: Literal["warning", "exception"],
) -> Generator[None, None, None]:
    try:
        if filepath == "stdout":
            sys.stdout = cast(
                TextIO, LogFileInterface(sys.stdout, logstyle, level_stdout)
            )
            sys.stderr = cast(
                TextIO, LogFileInterface(sys.stderr, logstyle, level_stderr)
            )
            yield
        else:
            with open(filepath, "a", encoding=config.ENCODING) as logfile:
                sys.stdout = cast(
                    TextIO, LogFileInterface(logfile, logstyle, level_stdout)
                )
                sys.stderr = cast(
                    TextIO, LogFileInterface(logfile, logstyle, level_stderr)
                )
                yield
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


def execute_scriptfunction() -> int | None:
    """Execute a HydPy script function.

    Function |execute_scriptfunction| is indirectly applied and explained in the
    documentation on module |hyd|.
    """
    logstyle = "plain"
    logfilepath = prepare_logfile("stdout")
    errorstyle = "multiline"
    try:
        args_given = []
        kwargs_given = {}
        for arg in sys.argv[1:]:
            if len(arg) < 3:
                args_given.append(arg)
            else:
                result = parse_argument(arg)
                if isinstance(result, str):
                    args_given.append(arg)
                else:
                    kwargs_given[result[0]] = result[1]
        logfilepath = prepare_logfile(kwargs_given.pop("logfile", "stdout"))
        logstyle = kwargs_given.pop("logstyle", "plain")
        errorstyle = kwargs_given.pop("errorstyle", "multiline")
        if errorstyle not in ("multiline", "single_line", "splittable"):
            errorstyle, errorstyle_ = "multiline", errorstyle
            raise ValueError(
                f"The given error message style `{errorstyle_}` is not available.  "
                f"Please choose one of the following: `multiline`, `single_line`, "
                f"and `splittable`."
            ) from None
        try:
            funcname = str(args_given.pop(0))
        except IndexError:
            raise ValueError(
                "The first positional argument defining the function to be called is "
                "missing."
            ) from None
        try:
            func = hydpy.pub.scriptfunctions[funcname]
        except KeyError:
            available_funcs = objecttools.enumeration(
                sorted(hydpy.pub.scriptfunctions.keys())
            )
            raise ValueError(
                f"There is no `{funcname}` function callable by `hyd.py`.  Choose one "
                f"of the following instead: {available_funcs}."
            ) from None
        argspec = inspect.getfullargspec(func)
        args_possible = argspec.args
        if argspec.defaults:
            args_required = args_possible[: -len(argspec.defaults)]
        else:
            args_required = args_possible
        nmb_args_possible = len(args_possible)
        nmb_args_required = len(args_required)
        nmb_args_given = len(args_given)
        if nmb_args_given < nmb_args_required or nmb_args_given > nmb_args_possible:
            enum_args_given = ""
            if nmb_args_given:
                enum_args_given = f" ({objecttools.enumeration(args_given)})"
            if nmb_args_given < nmb_args_required:
                args = args_required
                nmb_args = nmb_args_required
                condition = "requires"
            else:
                args = args_possible
                nmb_args = nmb_args_possible
                condition = "allows"
            enum_args = ""
            if nmb_args:
                enum_args = f" ({objecttools.enumeration(args)})"
            raise ValueError(
                f"Function `{funcname}` {condition} `{nmb_args:d}` "
                f"positional arguments{enum_args}, but "
                f"`{nmb_args_given:d}` are given{enum_args_given}."
            )
        with _activate_logfile(logfilepath, logstyle, "info", "warning"):
            return func(*args_given, **kwargs_given)
    except BaseException as exc:
        _print_error(
            exc=exc, logfilepath=logfilepath, logstyle=logstyle, errorstyle=errorstyle
        )
        return 1


def _print_error(
    *, exc: BaseException, logfilepath: str, logstyle: str, errorstyle: str
) -> None:

    if logstyle not in LogFileInterface.style2infotype2string:
        logstyle = "plain"

    with _activate_logfile(logfilepath, logstyle, "exception", "exception"):

        args = sys.argv[1:]
        if (nmb := len(args)) > 1:
            argphrase = f"with arguments `{', '.join(args)}`"
        elif nmb == 1:
            argphrase = f"with argument `{args[0]}`"
        else:
            argphrase = "without arguments"

        sep = "\n" if errorstyle == "multiline" else "__hydpy_newline__"
        message = (
            f"Invoking hyd.py {argphrase} resulted in the following error:"
            f"{' ' if errorstyle == 'single_line' else sep}"
            f"{str(exc)}"
        )
        if errorstyle != "single_line":
            traceback_ = "".join(traceback.format_tb(sys.exc_info()[2]))
            if errorstyle == "splittable":
                traceback_ = traceback_.replace("\n", sep)
            message = (
                f"{message}{sep}{sep}"
                f"See the following stack traceback for debugging:{sep}"
                f"{traceback_}"
            )
        if errorstyle == "splittable":
            message = message.replace("\n", "__hydpy_newline__")

        print(message, file=sys.stderr)


class LogFileInterface:
    """Wraps a usual file object, exposing all its methods while modifying only the
    `write` method.

    At the moment, class |LogFileInterface| supports only two log styles, as explained
    in the documentation on module |hyd|.  The following example shows its basic
    usage:

    >>> from hydpy import TestIO
    >>> from hydpy.exe.commandtools import LogFileInterface
    >>> with TestIO():
    ...     logfile = open("test.log", "w")
    >>> lfi = LogFileInterface(
    ...     logfile, logstyle="prefixed", infotype="exception")
    >>> lfi.write("a message\\n")
    >>> lfi.write("another message\\n")
    >>> lfi.close()
    >>> with TestIO():
    ...     with open("test.log", "r") as logfile:
    ...         print(logfile.read())
    error: a message
    error: another message
    <BLANKLINE>

    The class member `style2infotype2string` defines the currently available log styles.
    """

    style2infotype2string = {
        "plain": {"info": "", "warning": "", "exception": ""},
        "prefixed": {"info": "info: ", "warning": "warning: ", "exception": "error: "},
    }

    logfile: TextIO
    infotype: Literal["info", "warning", "exception"]

    def __init__(
        self,
        logfile: TextIO,
        logstyle: str,
        infotype: Literal["info", "warning", "exception"],
    ) -> None:
        self.logfile = logfile
        self._infotype = infotype
        try:
            stdtype2string = self.style2infotype2string[logstyle]
        except KeyError:
            styles = objecttools.enumeration(sorted(self.style2infotype2string.keys()))
            raise ValueError(
                f"The given log file style {logstyle} is not available.  "
                f"Please choose one of the following: {styles}."
            ) from None
        self._string = stdtype2string[infotype]

    def write(self, string: str) -> None:
        """Write the given string as explained in the main documentation on class
        |LogFileInterface|."""
        substrings = (f"{self._string}{s}" if s else "" for s in string.split("\n"))
        self.logfile.write("\n".join(substrings))

    def __getattr__(self, name: str) -> Any:
        return getattr(self.logfile, name)


def parse_argument(string: str) -> str | tuple[str, str]:
    """Return a single value for a string understood as a positional argument or a
    |tuple| containing a keyword and its value for a string understood as a keyword
    argument.

    |parse_argument| is intended to be used as a helper function for function
    |execute_scriptfunction| only.  See the following examples to see which types of
    keyword arguments |execute_scriptfunction| covers:

    >>> from hydpy.exe.commandtools import parse_argument
    >>> parse_argument("x=3")
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
    idx_equal = string.find("=")
    if idx_equal == -1:
        return string
    idx_quote = idx_equal + 1
    for quote in ('"', "'"):
        idx = string.find(quote)
        if -1 < idx < idx_quote:
            idx_quote = idx
    if idx_equal < idx_quote:
        return string[:idx_equal], string[idx_equal + 1 :]
    return string


def print_textandtime(text: str) -> None:
    """Print the given string and the current date and time with high precision for
    logging purposes.

    >>> from hydpy.exe.commandtools import print_textandtime
    >>> from hydpy.core.testtools import mock_datetime_now
    >>> from datetime import datetime
    >>> with mock_datetime_now(datetime(2000, 1, 1, 12, 30, 0, 123456)):
    ...     print_textandtime("something happens")
    something happens (2000-01-01 12:30:00.123456).
    """
    timestring = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"{text} ({timestring}).")
