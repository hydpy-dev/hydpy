# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from typing import *
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools
from hydpy.models.conv import conv_control


class NmbInputs(parametertools.Parameter):
    """The number of inlet nodes [-]"""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    CONTROLPARAMETERS = (
        conv_control.InputCoordinates,
    )

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.sequences.fluxes.inputs.shape = self

    def update(self) -> None:
        """Determine the number of inlet nodes via inspecting control
        parameter |InputCoordinates|.

        Note that invoking method |NmbInputs.update| as well as calling
        the parameter directly also sets the shape of flux sequence
        |conv_fluxes.Inputs|:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> inputcoordinates(
        ...     in1=(0.0, 3.0),
        ...     in2=(2.0, -1.0))
        >>> derived.nmbinputs.update()
        >>> derived.nmbinputs
        nmbinputs(2)
        >>> fluxes.inputs.shape
        (2,)

        >>> derived.nmbinputs(3)
        >>> derived.nmbinputs
        nmbinputs(3)
        >>> fluxes.inputs.shape
        (3,)
        """
        self(self.subpars.pars.control.inputcoordinates.shape[0])


class NmbOutputs(parametertools.Parameter):
    """The number of outlet nodes [-]"""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (1, None)

    CONTROLPARAMETERS = (
        conv_control.OutputCoordinates,
    )

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.subpars.pars.model.sequences.fluxes.outputs.shape = self

    def update(self) -> None:
        """Determine the number of inlet nodes via inspecting control
        parameter |OutputCoordinates|.

        Note that invoking method |NmbOutputs.update| as well as calling
        the parameter directly also sets the shape of flux sequence
        |conv_fluxes.Outputs|:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> outputcoordinates(
        ...     out1=(0.0, 3.0),
        ...     out2=(2.0, -1.0))
        >>> derived.nmboutputs.update()
        >>> derived.nmboutputs
        nmboutputs(2)
        >>> fluxes.outputs.shape
        (2,)

        >>> derived.nmboutputs(3)
        >>> derived.nmboutputs
        nmboutputs(3)
        >>> fluxes.outputs.shape
        (3,)
        """
        self(self.subpars.pars.control.outputcoordinates.shape[0])


class ProximityOrder(parametertools.Parameter):
    """Indices of the inlet nodes in the order of their proximity to each
    outlet node [-]"""
    NDIM, TYPE, TIME, SPAN = 2, int, None, (None, None)

    CONTROLPARAMETERS = (
        conv_control.MaxNmbInputs,
        conv_control.InputCoordinates,
        conv_control.OutputCoordinates,
    )

    def update(self) -> None:
        """Determine the proximity-order of the inlet and outlet nodes.

        The individual rows of parameter |ProximityOrder| correspond to the
        outlet nodes; the rows contain the proximity-sorted indices of the
        inlet nodes:

        >>> from hydpy.models.conv import *
        >>> parameterstep()
        >>> inputcoordinates(
        ...     in1=(0.0, 3.0),
        ...     in2=(2.0, -1.0))
        >>> outputcoordinates(
        ...     out1=(0.0, 3.0),
        ...     out2=(3.0, -2.0),
        ...     out3=(1.0, 2.0))
        >>> maxnmbinputs()
        >>> derived.proximityorder.update()
        >>> derived.proximityorder
        proximityorder([[0, 1],
                        [1, 0],
                        [0, 1]])

        Set the value of parameter |MaxNmbInputs| to one,if you want to
        consider the respective nearest input node only:

        >>> maxnmbinputs(1)
        >>> derived.proximityorder.update()
        >>> derived.proximityorder
        proximityorder([[0],
                        [1],
                        [0]])
        """
        control = self.subpars.pars.control
        incoords = control.inputcoordinates.__hydpy__get_value__()
        outcoords = control.outputcoordinates.__hydpy__get_value__()
        nmbinputs = control.maxnmbinputs.__hydpy__get_value__()
        idxs = numpy.empty((len(outcoords), nmbinputs), dtype=int)
        for idx, outcoord in enumerate(outcoords):
            distance = numpy.sqrt(numpy.sum((outcoord-incoords)**2, axis=1))
            idxs[idx, :] = numpy.argsort(distance)[:nmbinputs]
        self.__hydpy__set_shape__(idxs.shape)
        self.__hydpy__set_value__(idxs)
