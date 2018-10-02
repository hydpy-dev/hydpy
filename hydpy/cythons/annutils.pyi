
from typing import Sequence
import numpy

class ANN:

    nmb_inputs: int
    nmb_outputs: int
    nmb_layers: int
    nmb_neurons: numpy.ndarray
    weights_input: numpy.ndarray
    weights_output: numpy.ndarray
    weights_hidden: numpy.ndarray
    intercepts_hidden: numpy.ndarray
    intercepts_output: numpy.ndarray
    inputs: numpy.ndarray
    outputs: numpy.ndarray
    neurons: numpy.ndarray

    def process_actual_input(self) -> None:
        ...


class SeasonalANN:

    nmb_anns: int
    nmb_inputs: int
    nmb_outputs: int
    ratios: numpy.ndarray
    inputs: numpy.ndarray
    outputs: numpy.ndarray

    def __init__(self, ann:Sequence[ANN]):
        ...

    def process_actual_input(self, idx_season:int) -> None:
        ...
