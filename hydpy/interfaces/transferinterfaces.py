"""This module defines submodel interfaces for calculating water transfers into or out
of main models like those of the :ref:`HydPy-Dam` model family."""

from __future__ import annotations

import abc

from hydpy.core import modeltools
from hydpy.core.typingtools import *


class TransferModel_V1(modeltools.SubmodelInterface, abc.ABC):
    """Interface for calculating water transfers based on the main model's current
    water volume and allowed discharge.

    |TransferModel_V1| separates determining, querying, and setting the water transfer.
    This allows coupling with numerically solved main models like |dam_llake|, which
    let the submodel determine the transfer for multiple intermediate states within one
    simulation step (via |TransferModel_V1.determine_transfer|) and query the results
    (via |TransferModel_V1.get_transfer|).  At the end of the simulation step, the main
    model passes the step-averaged transfer back (via |TransferModel_V1.set_transfer|),
    so the submodel can process the final value further, for example, by passing it to
    an outlet node.
    """

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |TransferModel_V1| submodels."""

    @modeltools.abstractmodelmethod
    def determine_transfer(self, watervolume: float, alloweddischarge: float) -> None:
        """Determine the water transfer based on the water volume (million m³) and the
        highest discharge (m³/s) the main model can currently lose."""

    @modeltools.abstractmodelmethod
    def get_transfer(self) -> float:
        """Return the water transfer in m³/s determined by the last call of
        |TransferModel_V1.determine_transfer|.

        Positive values indicate withdrawals; negative values indicate supplies.
        """

    @modeltools.abstractmodelmethod
    def set_transfer(self, transfer: float) -> None:
        """Set the final water transfer in m³/s averaged over the current simulation
        step.

        Positive values indicate withdrawals; negative values indicate supplies.
        """
