# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import masktools


class Complete(masktools.DefaultMask):
    """Mask including all channel segments."""


class Masks(masktools.Masks):
    """Masks of base model |musk|."""

    CLASSES = (Complete,)
