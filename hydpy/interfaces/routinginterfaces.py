# pylint: disable=unused-argument
"""This module defines submodel interfaces for calculating 1-dimensional water flows."""
# import...
# ...from standard library
from __future__ import annotations

# ...from hydpy
from hydpy.core import modeltools
from hydpy.core.typingtools import *


class CrossSectionModel_V1(modeltools.SubmodelInterface):
    """Interface for calculating the discharge and related properties at a channel
    cross-section."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |CrossSectionModel_V1| submodels."""

    def prepare_bottomslope(self, bottomslope: int) -> None:
        """Set the bottom's slope (in the longitudinal direction) [-]."""

    @modeltools.abstractmodelmethod
    def use_waterdepth(self, waterdepth: float, /) -> None:
        """Set the water depth in m and use it to calculate all other properties."""

    @modeltools.abstractmodelmethod
    def use_waterlevel(self, waterlevel: float, /) -> None:
        """Set the water level in m and use it to calculate all other properties."""

    @modeltools.abstractmodelmethod
    def get_wettedarea(self) -> float:
        """Get the wetted area in m²."""

    @modeltools.abstractmodelmethod
    def get_surfacewidth(self) -> float:
        """Get the surface width in m."""

    @modeltools.abstractmodelmethod
    def get_discharge(self) -> float:
        """Get the discharge in m³/s."""

    @modeltools.abstractmodelmethod
    def get_celerity(self) -> float:
        """Get the wave celerity in m/s."""


class CrossSectionModel_V2(modeltools.SubmodelInterface):
    """Interface for calculating discharge-related properties at a channel
    cross-section."""

    typeid: ClassVar[Literal[2]] = 2
    """Type identifier for |CrossSectionModel_V2| submodels."""

    @modeltools.abstractmodelmethod
    def use_waterdepth(self, waterdepth: float, /) -> None:
        """Set the water depth in m and use it to calculate all other properties."""

    @modeltools.abstractmodelmethod
    def use_waterlevel(self, waterlevel: float, /) -> None:
        """Set the water level in m and use it to calculate all other properties."""

    @modeltools.abstractmodelmethod
    def use_wettedarea(self, wettedarea: float, /) -> None:
        """Set the wetted area in m² and use it to calculate all other properties."""

    @modeltools.abstractmodelmethod
    def get_waterdepth(self) -> float:
        """Get the water depth in m."""

    @modeltools.abstractmodelmethod
    def get_waterlevel(self) -> float:
        """Get the water level in m."""

    @modeltools.abstractmodelmethod
    def get_wettedarea(self) -> float:
        """Get the wetted area in m²."""

    @modeltools.abstractmodelmethod
    def get_wettedperimeter(self) -> float:
        """Get the wetted perimeter in m."""


class RoutingModelBase(modeltools.SubmodelInterface):
    """Base interface for routing models at inflow, central, and outflow locations.

    An essential note for model developers: All main models using submodels that follow
    the interface  |RoutingModel_V1|, |RoutingModel_V2|, or |RoutingModel_V3| must call
    |RoutingModelBase.determine_maxtimestep|, |RoutingModelBase.set_timestep|, and
    |RoutingModelBase.determine_discharge| in the mentioned order during each internal
    simulation step.  Before |RoutingModelBase.determine_discharge| is called, methods
    |RoutingModelBase.get_discharge|, |RoutingModel_V1.get_partialdischargeupstream|,
    and |RoutingModel_V3.get_partialdischargedownstream| (if implemented) must return
    the "old" discharge previously calculated or read from condition files.
    """

    typeid: ClassVar[int]
    """Type identifier for the respective routing submodels."""

    @modeltools.abstractmodelmethod
    def determine_maxtimestep(self) -> None:
        """Determine the highest possible computation time step."""
        assert False

    @modeltools.abstractmodelmethod
    def get_maxtimestep(self) -> float:
        """Get the highest possible computation time step in s."""
        assert False

    @modeltools.abstractmodelmethod
    def set_timestep(self, timestep: float) -> None:
        """Set the actual computation time step in s."""

    @modeltools.abstractmodelmethod
    def determine_discharge(self) -> None:
        """Determine the discharge."""
        assert False

    @modeltools.abstractmodelmethod
    def get_discharge(self) -> float:
        """Get the simulated total discharge in m³/s."""
        assert False

    @modeltools.abstractmodelmethod
    def get_dischargevolume(self) -> float:
        """Get the simulated total discharge in m."""
        assert False


class RoutingModel_V1(RoutingModelBase):
    """Interface for calculating the inflow into a channel."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |RoutingModel_V1| submodels."""

    routingmodelsdownstream: modeltools.SubmodelsProperty[
        RoutingModel_V2 | RoutingModel_V3
    ]
    """References to the neighbour routing models lying downstream."""

    storagemodeldownstream: modeltools.SubmodelProperty[StorageModel_V1]
    """Required reference to the neighbour storage model downstream."""

    @modeltools.abstractmodelmethod
    def get_partialdischargeupstream(self, clientdischarge: float) -> float:
        """Get the simulated partial discharge in m³/s.

        For multiple downstream models, |RoutingModel_V1.get_partialdischargeupstream|
        returns the discharge portion that it attributes to the client model.
        """
        assert False


class RoutingModel_V2(RoutingModelBase):
    """Interface for calculating the discharge between two channel segments."""

    typeid: ClassVar[Literal[2]] = 2
    """Type identifier for |RoutingModel_V2| submodels."""

    routingmodelsupstream: modeltools.SubmodelsProperty[
        RoutingModel_V1 | RoutingModel_V2
    ]
    """References to the neighbour routing models lying upstream."""

    routingmodelsdownstream: modeltools.SubmodelsProperty[
        RoutingModel_V2 | RoutingModel_V3
    ]
    """References to the neighbour routing models lying downstream."""

    storagemodelupstream: modeltools.SubmodelProperty[StorageModel_V1]
    """Required reference to the neighbour storage model upstream."""

    storagemodeldownstream: modeltools.SubmodelProperty[StorageModel_V1]
    """Required reference to the neighbour storage model downstream."""

    @modeltools.abstractmodelmethod
    def get_partialdischargeupstream(self, clientdischarge: float) -> float:
        """Get the simulated partial discharge in m³/s.

        For multiple downstream models, |RoutingModel_V1.get_partialdischargeupstream|
        returns the discharge portion that it attributes to the client model.
        """
        assert False

    @modeltools.abstractmodelmethod
    def get_partialdischargedownstream(self, clientdischarge: float) -> float:
        """Get the simulated partial discharge in m³/s.

        For multiple upstream models, |RoutingModel_V2.get_partialdischargedownstream|
        returns the discharge portion that it attributes to the client model.
        """
        assert False


class RoutingModel_V3(RoutingModelBase):
    """Interface for calculating the outflow of a channel."""

    typeid: ClassVar[Literal[3]] = 3
    """Type identifier for |RoutingModel_V3| submodels."""

    routingmodelsupstream: modeltools.SubmodelsProperty[
        RoutingModel_V1 | RoutingModel_V2
    ]
    """References to the neighbour routing models lying upstream."""

    storagemodelupstream: modeltools.SubmodelProperty[StorageModel_V1]
    """Required reference to the neighbour storage model upstream."""

    @modeltools.abstractmodelmethod
    def get_partialdischargedownstream(self, clientdischarge: float) -> float:
        """Get the simulated partial discharge in m³/s.

        For multiple upstream models, |RoutingModel_V3.get_partialdischargedownstream|
        returns the discharge portion that it attributes to the client model.
        """
        assert False


class StorageModel_V1(modeltools.SubmodelInterface):
    """Interface for calculating the water amount stored in a single channel segment."""

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |StorageModel_V1| submodels."""

    routingmodelsupstream: modeltools.SubmodelsProperty[
        RoutingModel_V1 | RoutingModel_V2 | RoutingModel_V3
    ]
    """Optional reference to the neighbour routing model upstream."""

    routingmodelsdownstream: modeltools.SubmodelsProperty[
        RoutingModel_V1 | RoutingModel_V2 | RoutingModel_V3
    ]
    """Optional reference to the neighbour routing model downstream."""

    @modeltools.abstractmodelmethod
    def set_timestep(self, timestep: float) -> None:
        """Set the actual computation time step in s."""
        assert False

    @modeltools.abstractmodelmethod
    def update_storage(self) -> None:
        """Update the stored water content."""
        assert False

    @modeltools.abstractmodelmethod
    def get_watervolume(self) -> float:
        """Get the current water volume in 1000 m³."""
        assert False

    @modeltools.abstractmodelmethod
    def get_waterlevel(self) -> float:
        """Get the current water level in m."""
        assert False


class ChannelModel_V1(modeltools.SubmodelInterface):
    """Interface for handling routing and storage submodels.

    The purpose of any model that follows the |ChannelModel_V1| interface is to collect
    and connect the routing and storage submodels required to simulate the water flow
    through a single channel (without confluences or branches).  It can but must not be
    able to perform the actual simulation itself.  See |sw1d_channel| as an example,
    which usually delegates simulations to |sw1d_network|.
    """

    typeid: ClassVar[Literal[1]] = 1
    """Type identifier for |ChannelModel_V1| submodels."""

    storagemodels: modeltools.SubmodelsProperty[StorageModel_V1]
    """References to the storage submodels.
    
    There must be one storage model for each channel segment.
    """

    routingmodels: modeltools.SubmodelsProperty[
        RoutingModel_V1 | RoutingModel_V2 | RoutingModel_V3
    ]
    """References to the routing submodels.

    There must be one routing model for each interface between two channel segments.
    Additionally, one routing model can be at the first position for simulating
    "longitudinal inflow" into the channel.  And there can be one routing model at the
    last position for calculating "longitudinal outflow".  
    
    Note that "inflow" and "outflow" here only refer to the location but not 
    necessarily to water increases or decreases in the channel's water amount, as both 
    might be positive or negative, depending on the selected submodel.
    
    If neither the upstream channel model defines a routing model for its last 
    position nor the corresponding downstream channel model for its first position, 
    both channels cannot become connected.  If both channel models define routing 
    models for the mentioned positions, it is unclear which is relevant.  We suggest 
    the following convention.  Of course, add routing submodels that handle "external 
    longitudinal inflow" (e.g. |sw1d_q_in|) at the first position and routing submodels 
    that handle "external longitudinal outflow" (e.g. |sw1d_weir_out|) at the last 
    position.  Add routing submodels that handle "internal longitudinal flow" (e.g. 
    |sw1d_lias|) at the last position for places with confluences or without 
    tributaries.  For branches, add them to the first position.
    """
