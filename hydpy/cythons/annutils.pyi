
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
    activation: numpy.ndarray
    inputs: numpy.ndarray
    outputs: numpy.ndarray
    neurons: numpy.ndarray

    def calculate_values(self) -> None:
        ...

    def calculate_derivatives(self, idx_input: int) -> None:
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

    def calculate_values(self, idx_season:int) -> None:
        ...
