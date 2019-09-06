# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import masktools


class Complete(masktools.DefaultMask):
    """Mask including a stream segments."""


class Masks(masktools.Masks):
    """Masks of base model |hstream|."""

    CLASSES = (Complete,)
