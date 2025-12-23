"""This module defines generic submodel interfaces for exchanging freely selectable
data."""

# import...
# ...from standard library
from __future__ import annotations

# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class ExchangeModel_V1(modeltools.SubmodelInterface):
    """Interface for exchanging modified, scalar data of arbitrary type."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |ExchangeModel_V1| submodels."""

    @modeltools.abstractmodelmethod
    def determine_y(self) -> None:
        """Determine the modified data."""
        assert False

    @modeltools.abstractmodelmethod
    def get_y(self) -> float:
        """Get the modified data."""
        assert False
