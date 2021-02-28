# -*- coding: utf-8 -*-
"""This module provides the aliases of the output variables of all available models."""
# import...
# ...from standard library
import importlib
import pkgutil

# ...from HydPy
import hydpy
from hydpy import models
from hydpy.core import sequencetools

groups = ("fluxes", "states")
_select = (sequencetools.FluxSequence, sequencetools.StateSequence)
modelpath: str = models.__path__[0]  # type: ignore[attr-defined, name-defined]
for moduleinfo in pkgutil.walk_packages([modelpath]):
    if moduleinfo.ispkg:
        for group in groups:
            modulepath = f"hydpy.models.{moduleinfo.name}.{moduleinfo.name}_{group}"
            try:
                module = importlib.import_module(modulepath)
            except ModuleNotFoundError:
                continue
            for member in vars(module).values():
                if (
                    (getattr(member, "__module__", None) == modulepath)
                    and issubclass(member, _select)
                    and member.NDIM == 0
                ):
                    alias = f"{moduleinfo.name}_{member.__name__}"
                    hydpy.sequence2alias[member] = alias
                    locals()[alias] = member
