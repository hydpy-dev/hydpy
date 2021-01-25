# -*- coding: utf-8 -*-
"""This subpackage contains the example project data provided by the standard
distribution of *HydPy*."""
# import...
# ...from standard library
import os


def make_filepath(*names: str) -> str:
    """Create and return an absolute path based on the current location of
    subpackage `data` and the given folder of file names.

    >>> from hydpy.data import make_filepath
    >>> from hydpy import repr_
    >>> repr_(make_filepath('subfolder', 'file.txt'))   # doctest: +ELLIPSIS
    '.../hydpy/data/subfolder/file.txt'
    """
    return os.path.join(__path__[0], *names)  # type: ignore[attr-defined, name-defined]
