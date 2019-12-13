
from hydpy.cythons import pointerutils

class FastAccessNodeSequence:

    sim: pointerutils.Double
    obs: pointerutils.Double
    _sim_array: numpy.ndarray
    _obs_array: numpy.ndarray
    _sim_ramflag: bool
    _obs_ramflag: bool
    _sim_diskflag: bool
    _sim_ramflag: bool

    def open_files(self, idx: int) -> None:
        ...

    def close_files(self) -> None:
        ...

    def load_simdata(self, idx: int) -> None:
        ...

    def save_simdata(self, idx: int) -> None:
        ...

    def load_obsdata(self, idx: int) -> None:
        ...

    def reset(self, idx: int) -> None:
        ...
