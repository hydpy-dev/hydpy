# pylint: disable=missing-module-docstring

from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.evap import evap_masks

if TYPE_CHECKING:
    from hydpy.core import variabletools


class LandMonthParameter(parametertools.KeywordParameter2D):
    """Base class for parameters whose values depend on the actual month and land cover
    type.

    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
    >>> from hydpy.models.wland_wag import *
    >>> parameterstep()
    >>> nu(2)
    >>> at(10.0)
    >>> aur(0.2, 0.8)
    >>> lt(FIELD, WATER)
    >>> with model.add_petmodel_v1("evap_pet_mlc"):
    ...     pass
    >>> model.petmodel.parameters.control.landmonthfactor  # doctest: +ELLIPSIS
    landmonthfactor(sealed=[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                    ...
                    water=[nan, nan, nan, nan, nan, nan, nan, nan, nan, nan,
                           nan, nan])
    """

    TYPE: Final = float

    columnnames = (
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    )
    rownames: tuple[str, ...] = ("ANY",)


class BaseZipParameter1D(parametertools.ZipParameter):
    """Base class for 1-dimensional parameters that provide additional keyword-based
    zipping functionalities."""

    constants = {}


class CompleteZipParameter1D(BaseZipParameter1D):
    """Base class for unrestricted 1-dimensional parameters.

    >>> from hydpy.models.hland_96 import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> area(10.0)
    >>> zonearea(0.5, 1.5, 2.5, 1.0, 4.5)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonez(2.0)
    >>> fc(200.0)
    >>> psi(1.0)
    >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
    ...     soil
    soil(field=True, forest=True, glacier=False, ilake=False, sealed=False)
    >>> model.aetmodel.parameters.control.water
    water(field=False, forest=False, glacier=False, ilake=True,
          sealed=False)
    >>> water = model.aetmodel.parameters.control.water
    >>> water.average_values()
    0.1
    >>> water.average_values(water.availablemasks.water)
    1.0
    """

    mask = evap_masks.Complete()


class SoilParameter1D(BaseZipParameter1D):
    """Base class for soil-related 1-dimensional parameters.

    >>> from hydpy.models.hland_96 import *
    >>> parameterstep()
    >>> nmbzones(6)
    >>> area(9.0)
    >>> zonearea(2.0, 3.0, 1.0, 1.0, 1.0, 1.0)
    >>> zonetype(FIELD, FOREST, GLACIER, ILAKE, SEALED, FIELD)
    >>> zonez(2.0)
    >>> fc(200.0)
    >>> psi(1.0)
    >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
    ...     excessreduction(field=1.0, forest=0.5)
    >>> model.aetmodel.parameters.control.excessreduction
    excessreduction(field=1.0, forest=0.5)
    >>> from hydpy import round_
    >>> excessreduction = model.aetmodel.parameters.control.excessreduction
    >>> round_(excessreduction.average_values())
    0.75
    >>> round_(excessreduction.average_values(excessreduction.availablemasks.soil))
    0.75
    """

    mask = evap_masks.Soil()


class PlantParameter1D(BaseZipParameter1D):
    """Base class for plant-related 1-dimensional parameters.

    >>> from hydpy.models.lland_dd import *
    >>> parameterstep()
    >>> nhru(6)
    >>> lnk(WASSER, GLETS, BODEN, ACKER, BAUMB, MISCHW)
    >>> ft(10.0)
    >>> fhru(0.1, 0.1, 0.2, 0.1, 0.3, 0.2)
    >>> gh(100.0)
    >>> wmax(200.0)
    >>> from hydpy import pub
    >>> pub.timegrids = "2000-01-01", "2000-01-02", "1d"
    >>> with model.add_aetmodel_v1("evap_aet_minhas"):
    ...     with model.add_petmodel_v2("evap_pet_ambav1"):
    ...         leafresistance(acker=30.0, baumb=40.0, mischw=50.0)
    >>> leafresistance = model.aetmodel.petmodel.parameters.control.leafresistance
    >>> leafresistance
    leafresistance(acker=30.0, baumb=40.0, mischw=50.0)
    >>> from hydpy import round_
    >>> round_(leafresistance.average_values())
    41.666667
    >>> round_(leafresistance.average_values(leafresistance.availablemasks.plant))
    41.666667

    .. testsetup::

        >>> del pub.timegrids
    """

    mask = evap_masks.Plant()


class WaterParameter1D(BaseZipParameter1D):
    """Base class for water area-related 1-dimensional parameters.

    >>> from hydpy.models.hland_96 import *
    >>> parameterstep()
    >>> nmbzones(5)
    >>> area(6.0)
    >>> zonearea(2.0, 1.0, 1.0, 1.0, 1.0)
    >>> zonetype(ILAKE, FOREST, GLACIER, ILAKE, SEALED)
    >>> zonez(2.0)
    >>> fc(200.0)
    >>> psi(1.0)
    >>> with model.add_aetmodel_v1("evap_aet_hbv96"):
    ...     temperaturethresholdice(ilake=1.0)
    >>> t = model.aetmodel.parameters.control.temperaturethresholdice
    >>> t
    temperaturethresholdice(1.0)
    >>> t.average_values()
    1.0
    >>> t.average_values(t.availablemasks.water)
    1.0
    """

    mask = evap_masks.Water()
