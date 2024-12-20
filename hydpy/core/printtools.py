"""This module implements features for printing additional information and for
modifying how information is printed."""

# import...
# ...from standard library
from __future__ import annotations
import os
import sys
import tempfile
import time
import types

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import objecttools
from hydpy.core.typingtools import *


_printprogress_indentation = -4


@objecttools.decorator
def print_progress(
    wrapped: types.MethodType,
    _: object,
    args: Iterable[object],
    kwargs: Mapping[str, object],
) -> None:
    """Add print commands time to the given function informing about execution time.

    To show how the |print_progress| decorator works, we need to modify the functions
    used by |print_progress| to gain system time information available in module |time|.

    First, we mock the functions |time.strftime| and |time.perf_counter|:

    >>> import time
    >>> from unittest import mock
    >>> strftime = time.strftime
    >>> perf_counter = time.perf_counter
    >>> strftime_mock = mock.MagicMock()
    >>> time.strftime = strftime_mock
    >>> time.perf_counter = mock.MagicMock()

    The mock of |time.strftime| shall respond to two calls, as if the first call to a
    decorated function occurs at quarter past eight, and the second one two seconds
    later:

    >>> time.strftime.side_effect = "20:15:00", "20:15:02"

    The mock of |time.perf_counter| shall respond to four calls, as if the subsequent
    calls by decorated functions occur at second 1, 3, 4, and 7:

    >>> time.perf_counter.side_effect = 1, 3, 4, 7

    Now we decorate two test methods.  The first one does nothing; the second one
    only calls the first one:

    >>> from hydpy.core.printtools import print_progress
    >>> class Test:
    ...     @print_progress
    ...     def test1(self):
    ...         pass
    ...     @print_progress
    ...     def test2(self):
    ...         self.test1()

    The first example shows that the output is appropriately indented, that the
    returned times are at the right place, that the calculated execution the is
    correct, and that the mock of |time.strftime| received a valid format string:

    >>> from hydpy import pub
    >>> pub.options.printprogress = True
    >>> Test().test2()
    method Test.test2 started at 20:15:00
        method Test.test1 started at 20:15:02
            seconds elapsed: 1
        seconds elapsed: 6
    >>> strftime_mock.call_args
    call('%H:%M:%S')

    The second example verifies that resetting the indentation works:

    >>> time.strftime.side_effect = "20:15:00", "20:15:02"
    >>> time.perf_counter.side_effect = 1, 3, 4, 7
    >>> Test().test2()
    method Test.test2 started at 20:15:00
        method Test.test1 started at 20:15:02
            seconds elapsed: 1
        seconds elapsed: 6

    The last example shows that disabling the |Options.printprogress| option works as
    expected:

    >>> pub.options.printprogress = False
    >>> Test().test2()

    >>> time.strftime = strftime
    >>> time.perf_counter = perf_counter
    """
    global _printprogress_indentation
    _printprogress_indentation += 4
    try:
        if hydpy.pub.options.printprogress:
            blanks = " " * _printprogress_indentation
            name = f"{type(wrapped.__self__).__name__}.{wrapped.__name__}"
            time_ = time.strftime("%H:%M:%S")
            print(f"{blanks}method {name} started at {time_}")
            seconds = time.perf_counter()
            sys.stdout.flush()
            wrapped(*args, **kwargs)
            blanks = " " * (_printprogress_indentation + 4)
            seconds = time.perf_counter() - seconds
            print(f"{blanks}seconds elapsed: {seconds}")
            sys.stdout.flush()
        else:
            wrapped(*args, **kwargs)
    finally:
        _printprogress_indentation -= 4


def progressbar(iterable: Iterable[T], length: int = 23) -> Iterator[T]:
    """Print a simple progress bar while processing the given iterable.

    Function |progressbar| does print the progress bar when option `printprogress` is
    activted:

    >>> from hydpy import pub
    >>> pub.options.printprogress = True

    You can pass an iterable object.  Say you want to calculate the the sum of all
    integer values from 1 to 100 and print the progress of the calculation.  Using
    function |range|, one just has to interpose function |progressbar|:

    >>> from hydpy.core.printtools import progressbar
    >>> x_sum = 0
    >>> for x in progressbar(range(1, 101)):
    ...     x_sum += x
        |---------------------|
        ***********************
    >>> x_sum
    5050

    To prevent possible interim print commands from dismembering the status bar, they
    are delayed until the status bar is complete.  For intermediate print outs of each
    fiftieth calculation, the result looks as follows:

    >>> x_sum = 0
    >>> for x in progressbar(range(1, 101)):
    ...     x_sum += x
    ...     if not x % 50:
    ...         print(x, x_sum)
        |---------------------|
        ***********************
    50 1275
    100 5050


    The number of characters of the progress bar can be changed:

    >>> for i in progressbar(range(100), length=50):
    ...     continue
        |------------------------------------------------|
        **************************************************

    But its maximum number of characters is restricted by the length of the given
    iterable:

    >>> for i in progressbar(range(10), length=50):
    ...     continue
        |--------|
        **********

    The smallest possible progress bar has two characters:

    >>> for i in progressbar(range(2)):
    ...     continue
        ||
        **

    For iterables of length one or zero, no progress bar is plottet:

    >>> for i in progressbar(range(1)):
    ...     continue

    The same is True when the |Options.printprogress| option is inactivated:

    >>> pub.options.printprogress = False
    >>> for i in progressbar(range(100)):
    ...     continue
    """
    nmbitems = len(tuple(iterable))
    if hydpy.pub.options.printprogress and (nmbitems > 1):
        temp_name = os.path.join(tempfile.gettempdir(), "HydPy_progressbar_stdout")
        temp_stdout = open(temp_name, "w", encoding=config.ENCODING)
        real_stdout = sys.stdout
        try:
            sys.stdout = temp_stdout
            nmbstars = min(nmbitems, length)
            nmbcounts = nmbitems / nmbstars
            indentation = " " * max(_printprogress_indentation, 0)
            print(
                f"    {indentation}|{'-' * (nmbstars - 2)}|\n{indentation}    ",
                end="",
                file=real_stdout,
            )
            counts = 1.0
            for next_ in iterable:
                counts += 1.0
                if counts >= nmbcounts:
                    print(end="*", file=real_stdout)
                    counts -= nmbcounts
                yield next_
        finally:
            temp_stdout.close()
            sys.stdout = real_stdout
            print()
            with open(temp_name, encoding=config.ENCODING) as temp_stdout:
                sys.stdout.write(temp_stdout.read())
            sys.stdout.flush()
    else:
        yield from iterable
