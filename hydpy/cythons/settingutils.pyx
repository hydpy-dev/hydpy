"""This Cython module implements global settings that must be available during
simulation runs, both in pure Python mode and at Cython speed.

Module |settingutils| is the counterpart of module |optiontools|.  Users configure
settings via the corresponding options, while models read them via attribute
|Model.runsettings| of class |Model|.  Module |pub| and all models share the same
|RunSettings| and are thus always in sync.

So far, |RunSettings| handles only the integer representation of the option
|Options.simulationmode|, for which |settingutils| defines the constants
|settingutils.HISTORICAL| and |settingutils.FORECAST|:

>>> from hydpy.cythons.settingutils import FORECAST, HISTORICAL, RunSettings
>>> HISTORICAL, FORECAST
(0, 1)

The default mode is |settingutils.HISTORICAL|:

>>> settings = RunSettings()
>>> assert settings.simulationmode == HISTORICAL

Direct value assignments are forbidden (use option |Options.simulationmode| instead):

>>> settings.simulationmode = FORECAST
Traceback (most recent call last):
...
AttributeError: attribute 'simulationmode' of 'hydpy.cythons.autogen.settingutils.RunSettings' objects is not writable

"""

import cython

@cython.final
cdef class RunSettings:
    """The global settings that must be available during simulation runs."""

    def __init__(self) -> None:
        self.simulationmode = HISTORICAL

    def __hydpy__set_simulationmode__(self, value: int) -> None:
        self.simulationmode = value
