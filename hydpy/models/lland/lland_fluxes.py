# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools

# ...from lland
from hydpy.models.lland import lland_masks
from hydpy.models.lland import lland_sequences


# inflow


class QZ(sequencetools.FluxSequence):
    """Zufluss in das Teilgebiet (inflow into the subcatchment) [m³/s]."""

    NDIM, NUMERIC = 0, False


class QZH(sequencetools.FluxSequence):
    """Abflussspende in das Teilgebiet (inflow into the subcatchment) [mm/T]."""

    NDIM, NUMERIC = 0, False


# meteorological input


class TemLTag(sequencetools.FluxSequence):
    """Tageswert der Lufttemperatur (daily air temperature) [°C]."""

    NDIM, NUMERIC = 0, False


class DailyRelativeHumidity(sequencetools.FluxSequence):
    """Daily relative humidity [%]."""

    NDIM, NUMERIC = 0, False


class DailySunshineDuration(sequencetools.FluxSequence):
    """Daily sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class DailyPossibleSunshineDuration(sequencetools.FluxSequence):
    """Astronomically possible daily sunshine duration [h]."""

    NDIM, NUMERIC = 0, False


class DailyGlobalRadiation(sequencetools.FluxSequence):
    """Daily global radiation [h]."""

    NDIM, NUMERIC = 0, False


class NKor(lland_sequences.Flux1DSequence):
    """Korrigierter Niederschlag (corrected precipitation) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class TKor(lland_sequences.Flux1DSequence):
    """Korrigierte Lufttemperatur (corrected air temperature) [°C]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class TKorTag(lland_sequences.Flux1DSequence):
    """Tageswert der korrigierten Lufttemperatur (corrected daily air
    temperature) [°C]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class WindSpeed2m(sequencetools.FluxSequence):
    """Wind speed at a height of 2 m above the ground for grass [m/s]."""

    NDIM, NUMERIC = 0, False


class DailyWindSpeed2m(sequencetools.FluxSequence):
    """Daily wind speed 2 meters above ground  [m/s]."""

    NDIM, NUMERIC = 0, False


class ReducedWindSpeed2m(lland_sequences.Flux1DSequence):
    """Land-use-specific wind speed at a height of 2 m above the ground [m/s]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class WindSpeed10m(sequencetools.FluxSequence):
    """Wind speed at a height of 10 m above the ground for grass [m/s]."""

    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(lland_sequences.Flux1DSequence):
    """Saturation vapour pressure [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class DailySaturationVapourPressure(lland_sequences.Flux1DSequence):
    """Daily satuarion vapour pressure [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class SaturationVapourPressureInz(lland_sequences.Flux1DSequence):
    """Sättigungsdampdruck unmittelbar oberhalb der Oberfläche des interzepierten
    Schnees (saturation vapour pressure directly above the surface of the intercepted
    snow) [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class SaturationVapourPressureSnow(lland_sequences.Flux1DSequence):
    """Saturation vapour pressure snow [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class SaturationVapourPressureSlope(lland_sequences.Flux1DSequence):
    """The slope of the saturation vapour pressure curve [hPa/K]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class DailySaturationVapourPressureSlope(lland_sequences.Flux1DSequence):
    """Daily satuarion vapour pressure [hPa/K]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class ActualVapourPressure(lland_sequences.Flux1DSequence):
    """Actual vapour pressure [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class DailyActualVapourPressure(lland_sequences.Flux1DSequence):
    """Daily actual vapour pressure [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class DryAirPressure(lland_sequences.Flux1DSequence):
    """Dry air pressure [hPa]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class DensityAir(lland_sequences.Flux1DSequence):
    """Air density [kg/m³]"""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class G(lland_sequences.Flux1DSequence):
    """ "MORECS" Bodenwärmestrom ("MORECS" soil heat flux) [W/m²].

    With positive values, the soil looses heat to the atmosphere or the
    snow-layer.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class TZ(lland_sequences.Flux1DSequence):
    """Bodentemperatur in der Tiefe z (soil temperature at depth z) [°C]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class WG(lland_sequences.Flux1DSequence):
    """ "Dynamischer" Bodenwärmestrom ("dynamic" soil heat flux) [W/m²].

    With positive values, the soil looses heat to the atmosphere or the
    snow-layer.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class NetShortwaveRadiation(lland_sequences.Flux1DSequence):
    """Netto kurzwellige Strahlungsbilanz (net shortwave radiation) [W/m²].

    With positive values, the soil gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class NetShortwaveRadiationInz(lland_sequences.Flux1DSequence):
    """Kurzwellige Netto-Strahlungsbilanz für den interzipierten Schnee (net shortwave
    radiation for intercepted snow) [W/m²].

    With positive values, the soil gains heat from radiation.  Without intercepted
    snow, |NetShortwaveRadiationInz| is |numpy.nan|.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class NetShortwaveRadiationSnow(lland_sequences.Flux1DSequence):
    """Kurzwellige Netto-Strahlungsbilanz für Schneeoberflächen (net shortwave
    radiation for snow surfaces) [W/m²].

    With positive values, the soil gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class DailyNetShortwaveRadiation(lland_sequences.Flux1DSequence):
    """Daily not shortwave radiation [W/m²].

    With positive values, the soil gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class DailyNetLongwaveRadiation(lland_sequences.Flux1DSequence):
    """Daily net longwave radiation [W/m²].

    With positive values, the soil looses heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class NetLongwaveRadiationInz(lland_sequences.Flux1DSequence):
    """Langwellige Nettostrahlung des interzepierten Schnees (net longwave radiation
    of the intercepted snow [W/m²].

    With positive values, the snow-layer gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class NetLongwaveRadiationSnow(lland_sequences.Flux1DSequence):
    """Net longwave radiation for snow-surfaces [W/m²].

    With positive values, the snow-layer gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class NetRadiation(lland_sequences.Flux1DSequence):
    """Total net radiation [W/m²].

    With positive values, the soil gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class NetRadiationInz(lland_sequences.Flux1DSequence):
    """Nettostrahlung des interzepierten Schnees (total net radiation of the
    intercepted snow [W/m²].

    With positive values, the soil gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class NetRadiationSnow(lland_sequences.Flux1DSequence):
    """Total net radiation for snow-surfaces [W/m²].

    With positive values, the snow-layer gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class DailyNetRadiation(lland_sequences.Flux1DSequence):
    """Daily net radiation [W/m²].

    With positive values, the soil gains heat from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class AerodynamicResistance(lland_sequences.Flux1DSequence):
    """Aerodynamischer Widerstand (aerodynamic resistance) [s/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class SoilSurfaceResistance(lland_sequences.Flux1DSequence):
    """Oberflächenwiderstand (surface resistance) [s/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class LanduseSurfaceResistance(lland_sequences.Flux1DSequence):
    """Oberflächenwiderstand (surface resistance) [s/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class ActualSurfaceResistance(lland_sequences.Flux1DSequence):
    """Oberflächenwiderstand (surface resistance) [s/m]."""

    NDIM, NUMERIC, SPAN = 1, False, (0.0, None)
    mask = lland_masks.Land()


class NBes(lland_sequences.Flux1DSequence):
    """Gesamter Bestandsniederschlag (total stand precipitation) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class SBes(lland_sequences.Flux1DSequence):
    """Schneeanteil Bestandsniederschlag (frozen stand precipitation) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class SnowIntMax(lland_sequences.Flux1DSequence):
    """Schneeinterzeptionsspeicherkapazität (capacity of the snow interception
    storage) [mm]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class SnowIntRate(lland_sequences.Flux1DSequence):
    """Anteil des im Schneeinterzeptionsspeicher zurückgehaltenen Niederschlags
    (ratio between the snow interception rate and precipitation) [-]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class NBesInz(lland_sequences.Flux1DSequence):
    """Gesamter Bestandsniederschlag, der den Schneeinterzeptionsspeicher erreicht
    (total stand precipitation reaching the snow interception storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class SBesInz(lland_sequences.Flux1DSequence):
    """Gefrorener Bestandsniederschlag, der den Schneeinterzeptionsspeicher erreicht
    (frozen amount of stand precipitation reaching the snow interception storage)
    [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class WNiedInz(lland_sequences.Flux1DSequence):
    """Niederschlagsbedingter Wärmestrom in den Schneeinterzeptionsspeicher (heat flux
    into the snow interception storage due to precipitation) [W/m²].

    With positive values, the snow layer gains heat from precipitation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class ActualAlbedoInz(lland_sequences.Flux1DSequence):
    """Aktuelle Albedo der Oberfläche des interzeptierten Schnees (the current albedo
    of the surface of the intercepted snow) [-].

    If there is no intercepted snow, the value of |ActualAlbedoInz| is |numpy.nan|.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class WaDaInz(lland_sequences.Flux1DSequence):
    """Wasserdargebot des Schneeinterzeptionsspeichers (water leaving the snow
    interception storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class SchmPotInz(lland_sequences.Flux1DSequence):
    """Potentielle Schmelze des interzepierten Schnees (potential amount of snow
    melting within the snow interception storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class SchmInz(lland_sequences.Flux1DSequence):
    """Tatsächliche Schmelze des interzepierten Schnees (actual amount of snow
    melting within the snow cover) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class GefrPotInz(lland_sequences.Flux1DSequence):
    """Potentielles Wiedergefrieren des interzipierten Schnees (potential amount
    of water refreezing within the snow interception storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class GefrInz(lland_sequences.Flux1DSequence):
    """Tatsächliche Wiedergefrieren des interzipierten Schnees (actual amount of
    water refreezing within the snow interception storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class EvSInz(lland_sequences.Flux1DSequence):
    """Tatsächliche Verdunstung des interzepierten Schnees (actual evaporation of
    the intercepted snow) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class EvPo(lland_sequences.Flux1DSequence):
    """Potenzielle Evapotranspiration (potential evapotranspiration) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class EvI(lland_sequences.Flux1DSequence):
    """Tatsächliche Interzeptionsverdunstung (actual evaporation of
    intercepted water) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class EvB(lland_sequences.Flux1DSequence):
    """Tatsächliche Verdunstung von Bodenwasser (actual evaporation of soil
    water) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class EvS(lland_sequences.Flux1DSequence):
    """Tatsächliche Schneeverdunstung (actual evaporation of snow-water) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class WGTF(lland_sequences.Flux1DSequence):
    """Mit dem Grad-Tag-Verfahren berechneter Wärmeestrom in die Schneedecke
    (heat flux into the snow layer calculated with the degree-day method)
    [W/m²].

    With positive values, the snow layer gains heat from the atmosphere and
    from radiation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class WNied(lland_sequences.Flux1DSequence):
    """Niederschlagsbedingter Wärmestrom in die Schneedecke (heat flux
    into the snow layer due to precipitation) [W/m²].

    With positive values, the snow layer gains heat from precipitation.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class TempSSurface(lland_sequences.Flux1DSequence):
    """Schneetemperatur an der Schneeoberfläche (the snow temperature at the
    snow surface) [°C].

    Note that the value of sequence |TempSSurface| is |numpy.nan| for
    snow-free surfaces.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class ActualAlbedo(lland_sequences.Flux1DSequence):
    """Aktuelle Albedo der relevanten Oberfläche (the current albedo of
    the relevant surface) [-]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class SchmPot(lland_sequences.Flux1DSequence):
    """Potentielle Schneeschmelze (potential amount of water melting within the
    snow cover) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class Schm(lland_sequences.Flux1DSequence):
    """Tatsächliche Schneeschmelze (actual amount of water melting within the
    snow cover) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class GefrPot(lland_sequences.Flux1DSequence):
    """Potentielles Schnee-Wiedergefrieren (potential amount of water
    refreezing within the snow cover) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class Gefr(lland_sequences.Flux1DSequence):
    """Tatsächliche Schnee-Wiedergefrieren (actual amount of water
    refreezing within the snow cover) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class WLatInz(lland_sequences.Flux1DSequence):
    """Latente Wärmestrom interzepierter Schnee/Atmosphäre (latent heat flux between
    the intercepted snow and the atmosphere) [W/m²].

    With positive values, the snow-layer looses heat to the atmosphere.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class WLatSnow(lland_sequences.Flux1DSequence):
    """Latente Wärmestrom Schnee/Atmosphäre (latent heat flux between
    the snow-layer and the atmosphere) [W/m²].

    With positive values, the snow-layer looses heat to the atmosphere.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class WSensInz(lland_sequences.Flux1DSequence):
    """Fühlbare Wärmestrom interzipierter Schnee/Atmosphäre (sensible heat flux
    between the intercepted snow and the atmosphere) [W/m²].

    With positive values, the snow-layer looses heat to the atmosphere.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class WSensSnow(lland_sequences.Flux1DSequence):
    """Fühlbare Wärmestrom Schnee/Atmosphäre (sensible heat flux between
    the snow-layer and the atmosphere) [W/m²].

    With positive values, the snow-layer looses heat to the atmosphere.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class WSurfInz(lland_sequences.Flux1DSequence):
    """Wärmestrom vom Körper des interzepierten Schnees bis zu dessen Schneeoberfläche
    (heat flux from the body of the intercepted snow to its surface) [W/m²].

    With positive values, the snow-layer looses heat to the atmosphere.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Forest()


class WSurf(lland_sequences.Flux1DSequence):
    """Wärmestrom von der Schneedecke zur Schneeoberfläche (heat flux from
    the snow layer to the snow surface) [W/m²].

    With positive values, the snow-layer looses heat to the atmosphere.
    """

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class SFF(lland_sequences.Flux1DSequence):
    """Relativer Anteil des gefrorenen Bodenwassers bis zu einer Tiefe von
    2z (relative proportion of frozen soil water) [-]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Soil()


class FVG(lland_sequences.Flux1DSequence):
    """Frostversiegelungsgrad (degree of frost sealing) [-]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Soil()


class WaDa(lland_sequences.Flux1DSequence):
    """Wasserdargebot (water reaching the soil routine) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Land()


class QDB(lland_sequences.Flux1DSequence):
    """Direktabfluss-Abgabe aus dem Bodenspeicher (direct runoff release
    from the soil storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class QIB1(lland_sequences.Flux1DSequence):
    """Erste Komponente der Interflow-Abgabe aus dem Bodenspeicher (first
    component of the interflow release from the soil storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class QIB2(lland_sequences.Flux1DSequence):
    """Zweite Komponente der Interflow-Abgabe aus dem Bodenspeicher (second
    component of the interflow release from the soil storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class QBB(lland_sequences.Flux1DSequence):
    """Basisabfluss-Abgabe aus dem Bodenspeicher (base flow release
    from the soil storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class QKap(lland_sequences.Flux1DSequence):
    """Kapillarer Aufstieg in den Bodenspeicher (capillary rise to soil
    storage) [mm/T]."""

    NDIM, NUMERIC = 1, False
    mask = lland_masks.Complete()


class QDGZ(sequencetools.FluxSequence):
    """Gesamtzufluss in beide Direktabfluss-Gebietsspeicher (total inflow to both
    direct runoff storages) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QDGZ1(sequencetools.FluxSequence):
    """Zufluss in den trägeren Direktabfluss-Gebietsspeicher (inflow to the slow direct
    runoff storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QDGZ2(sequencetools.FluxSequence):
    """Zufluss in den dynamischeren Direktabfluss-Gebietsspeicher (inflow to the fast
    direct runoff storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QIGZ1(sequencetools.FluxSequence):
    """ "Zufluss in den ersten Zwischenabfluss-Gebietsspeicher (inflow to the first
    interflow storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QIGZ2(sequencetools.FluxSequence):
    """Zufluss in den zweiten Zwischenabfluss-Gebietsspeicher (inflow to the second
    interflow storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QBGZ(sequencetools.FluxSequence):
    """Zufluss in den Basisabfluss-Gebietsspeicher (inflow to the base flow storage)
    [mm/T]."""

    NDIM, NUMERIC = 0, False


class QDGA1(sequencetools.FluxSequence):
    """Abfluss aus dem trägeren Direktabfluss-Gebietsspeicher (outflow from the slow
    direct runoff storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QDGA2(sequencetools.FluxSequence):
    """Abfluss aus dem dynamischeren Direktabfluss-Gebietsspeicher (outflow from the
    fast direct runoff storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QIGA1(sequencetools.FluxSequence):
    """Abfluss aus dem "unteren" Zwischenabfluss-Gebietsspeicher (outflow from the
    first interflow storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QIGA2(sequencetools.FluxSequence):
    """Abfluss aus dem "oberen" Zwischenabfluss-Gebietsspeicher (outflow from the
    second interflow storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QBGA(sequencetools.FluxSequence):
    """Abfluss aus dem Basisabfluss-Gebietsspeicher (outflow from the base flow
    storage) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QAH(sequencetools.FluxSequence):
    """Abflussspende des Teilgebiets (runoff at the catchment outlet) [mm/T]."""

    NDIM, NUMERIC = 0, False


class QA(sequencetools.FluxSequence):
    """Abfluss des Teilgebiets (runoff at the catchment outlet) [m³/s]."""

    NDIM, NUMERIC = 0, False
