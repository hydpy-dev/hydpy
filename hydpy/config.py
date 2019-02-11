# -*- coding: utf-8 -*-
"""Module |config| allows the user to configure `HydPy`.

The available options should not be changed during runtime.
"""
use_autodoc = True    # pylint: disable=invalid-name
"""Flag that indicates whether HydPy's automatic documentation manipulation
features should be applyied or not.  It is imperative to set it to `True`
before one uses `Sphinx` to generate the online documentation.  However,
one can set it to `False` for regular applications, which reduces HydPy's
initialisation time."""
