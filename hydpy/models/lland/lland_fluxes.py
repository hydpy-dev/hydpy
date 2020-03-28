# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from HydPy
from hydpy.core import sequencetools
# ...from lland
from hydpy.models.lland import lland_sequences


class NKor(lland_sequences.Flux1DSequence):
    """Korrigierter Niederschlag (corrected precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class TKor(lland_sequences.Flux1DSequence):
    """Korrigierte Lufttemperatur (corrected air temperature) [°C]."""
    NDIM, NUMERIC = 1, False


class F2SIMax(lland_sequences.Flux1DSequence):
    """Faktor zur Berechnung der Schneeinterzeptionskapazität als Funktion der
    Lufttemperatur"""
    NDIM, NUMERIC = 1, False


class SInzpCap(lland_sequences.Flux1DSequence):
    """Schneeinterzeptionskapazität [mm]."""
    NDIM, NUMERIC = 1, False


class F2SIRate(lland_sequences.Flux1DSequence):
    """Faktor zur Berechnung der Schneeinterzeptionsratet als Funktion der
    Lufttemperatur"""
    NDIM, NUMERIC = 1, False


class SInzpRate(lland_sequences.Flux1DSequence):
    """Schneeinterzeptionsrate [mm/T]."""
    NDIM, NUMERIC = 1, False


class ET0(lland_sequences.Flux1DSequence):
    """Grasreferenzverdunstung (reference evapotranspiration) [mm]."""
    NDIM, NUMERIC = 1, False


class EvPo(lland_sequences.Flux1DSequence):
    """Evapotranspiration (evapotranspiration) [mm]."""
    NDIM, NUMERIC = 1, False


class WindSpeed2m(sequencetools.FluxSequence):
    """Adjusted wind speed [m/s]."""
    NDIM, NUMERIC = 0, False


class WindSpeed10m(sequencetools.FluxSequence):
    """Adjusted wind speed [m/s]."""
    NDIM, NUMERIC = 0, False


class SaturationVapourPressure(sequencetools.FluxSequence):
    """Saturation vapour pressure [kPa]."""
    NDIM, NUMERIC = 1, False


class SaturationVapourPressureSnow(sequencetools.FluxSequence):
    """Saturation vapour pressure snow [kPa]."""
    NDIM, NUMERIC = 1, False


class SaturationVapourPressureSlope(sequencetools.FluxSequence):
    """The slope of the saturation vapour pressure curve [kPa/°C]."""
    NDIM, NUMERIC = 1, False


class ActualVapourPressure(sequencetools.FluxSequence):
    """Actual vapour pressure [kPa]."""
    NDIM, NUMERIC = 1, False


class ActualVapourPressureSnow(sequencetools.FluxSequence):
    """Actual vapour pressure over Snow[kPa]."""
    NDIM, NUMERIC = 1, False


class DryAirPressure(sequencetools.FluxSequence):
    """Dry air pressure [kPa]."""
    NDIM, NUMERIC = 1, False


class DensityAir(sequencetools.FluxSequence):
    """Air density [kg/m³]"""
    NDIM, NUMERIC = 1, False


class EarthSunDistance(sequencetools.FluxSequence): #todo derived parameters?
    """The relative inverse distance between the earth and the sun [-]."""
    NDIM, NUMERIC = 0, False


class SolarDeclination(sequencetools.FluxSequence):
    """Solar declination [-]."""
    NDIM, NUMERIC = 0, False


class SunsetHourAngle(sequencetools.FluxSequence):
    """Sunset hour angle [rad]."""
    NDIM, NUMERIC = 0, False


class SolarTimeAngle(sequencetools.FluxSequence):
    """Solar time angle [rad]."""
    NDIM, NUMERIC = 0, False


class ExtraterrestrialRadiation(sequencetools.FluxSequence):
    """Extraterrestial radiation [MJ/m²/T]."""
    NDIM, NUMERIC = 0, False


class PossibleSunshineDuration(sequencetools.FluxSequence):
    """Possible astronomical sunshine duration [h]."""
    NDIM, NUMERIC = 0, False


class GlobalRadiation(sequencetools.FluxSequence):
    """Global Radiation [MJ/m²]."""
    NDIM, NUMERIC = 0, False


class AdjustedGlobalRadiation(sequencetools.FluxSequence):
    """ToDo Adjusted global Radiation [MJ/m²]."""
    NDIM, NUMERIC = 0, False


class WG(sequencetools.FluxSequence):
    """Bodenwärmestrom (soil heat flux) [MJ/m²]

    Der Wärmestrom ist positiv, wenn die Oberfläche fühlbare Wärme verliert
    (the heat flux is positive if the surface loses heat)."""
    NDIM, NUMERIC = 1, False


class TZ(sequencetools.FluxSequence):
    """Bodentemperatur in einer Tiefe von z (soil temperature at a depth of z)
    [°C]"""
    NDIM, NUMERIC = 1, False


class NetShortwaveRadiation(sequencetools.FluxSequence):
    """Netto kurzwellige Strahlungsbilanz (Net shortwave radiation [MJ/m²/T]).

    Die Strahlungsbilanz ist positiv, wenn die Oberfläche Wärme hinzu gewinnt
    (the net shortwave radiation is positive if the surface gains heat)."""
    NDIM, NUMERIC = 1, False


class NetLongwaveRadiation(sequencetools.FluxSequence):
    """Net longwave radiation [MJ/m²].

    Die Strahlungsbilanz ist positiv, wenn die Oberfläche Wärme verliert
    (the net longwave radiation is positive if the surface loses heat)."""
    NDIM, NUMERIC = 1, False


class NetRadiation(sequencetools.FluxSequence):
    """Total net radiation [MJ/m²].

    Die Strahlungsbilanz ist positiv, wenn die Oberfläche Wärme hinzu gewinnt
    (the net shortwave radiation is positive if the surface gains heat)."""
    NDIM, NUMERIC = 1, False


class PsychrometricConstant(sequencetools.FluxSequence):
    """Psychrometric constant [kPa/°C]."""
    NDIM, NUMERIC = 0, False


class AerodynamicResistance(sequencetools.FluxSequence):
    """Aerodynamischer Widerstand (aerodynamic resistance) [s/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class SoilSurfaceResistance(sequencetools.FluxSequence):
    """Oberflächenwiderstand (surface resistance) [s/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class LanduseSurfaceResistance(sequencetools.FluxSequence):
    """Oberflächenwiderstand (surface resistance) [s/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class ActualSurfaceResistance(sequencetools.FluxSequence):
    """Oberflächenwiderstand (surface resistance) [s/m]."""
    NDIM, NUMERIC, SPAN = 1, False, (0., None)


class NBes(lland_sequences.Flux1DSequence):
    """Gesamter Bestandsniederschlag (total stand precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class SKor(lland_sequences.Flux1DSequence):
    """Schneeanteil Gesamtniederschlag (frozen precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class SBes(lland_sequences.Flux1DSequence):
    """Schneeanteil Bestandsniederschlag (frozen stand precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class EvI(lland_sequences.Flux1DSequence):
    """Tatsächliche Interzeptionsverdunstung (actual evaporation of
    intercepted water) [mm]."""
    NDIM, NUMERIC = 1, False


class EvB(lland_sequences.Flux1DSequence):
    """Tatsächliche Bodenverdunstung (actual evaporation of
    soil water) [mm]."""
    NDIM, NUMERIC = 1, False


class EvS(lland_sequences.Flux1DSequence):
    """Potentielle Verdunstung bei Schneebedeckung (actual evaporation at
    wnow cover) [mm]."""
    NDIM, NUMERIC = 1, False


class WGTF(lland_sequences.Flux1DSequence):
    """Mit dem Grad-Tag-Verfahren berechneter Wärmeestrom in die Schneedecke
    (heat flux into the snow layer calculated with the degree-day method)
    [MJ/m²/T].

    Positive values indicate an energy gain of the snow layer.
    """
    NDIM, NUMERIC = 1, False


class WNied(lland_sequences.Flux1DSequence):
    """Niederschlagsbedingter Wärmestrom in die Schneedecke (heat flux
    into the snow layer due to precipitation) [MJ/m²/T].

    Positive values indicate an energy gain of the snow layer.
    """
    NDIM, NUMERIC = 1, False


class WSnow(lland_sequences.Flux1DSequence):
    """Netto-Energieänderung der Schneedecke (net energy intake of the
    snow layer) [MJ/m²/T]"""
    NDIM, NUMERIC = 1, False


class TempSSurface(lland_sequences.Flux1DSequence):
    """Schneetemperatur an der Schneeoberfläche (the snow temperature at the
    snow surface) [°C].

    Note that the value of sequence |TempSSurface| is |numpy.nan| for
    snow-free surfaces.
    """
    NDIM, NUMERIC = 1, False


class ActualAlbedo(lland_sequences.Flux1DSequence):
    """Aktuelle Albedo der relevanten Oberfläche (the current albedo of
    the relevant surface) [-]."""
    NDIM, NUMERIC = 1, False


class SchmPot(lland_sequences.Flux1DSequence):
    """Potentielle Schneeschmelze (potential amount of water melting within the
    snow cover) [mm]."""
    NDIM, NUMERIC = 1, False


class Schm(lland_sequences.Flux1DSequence):
    """Tatsächliche Schneeschmelze (actual amount of water melting within the
    snow cover) [mm]."""
    NDIM, NUMERIC = 1, False


class GefrPot(lland_sequences.Flux1DSequence):
    """Potentielle Menge an Wiedergefrorenen Schnee (potential amount of water
    refreezing within the snow cover) [mm]."""
    NDIM, NUMERIC = 1, False


class Gefr(lland_sequences.Flux1DSequence):
    """Tatsächliche Menge an wiedergefrorenem Wasser (actual amount of water
    refreezing within the snow cover) [mm]."""
    NDIM, NUMERIC = 1, False


class WLatSnow(lland_sequences.Flux1DSequence):
    """Latente Wärme (latent heat) [MJ/m²/T]

    Der Wärmestrom ist positiv, wenn die Oberfläche fühlbare Wärme verliert
    (the heat flux is positive if the surface loses heat).
    """
    NDIM, NUMERIC = 1, False


class WSensSnow(lland_sequences.Flux1DSequence):
    """Fühlbare Wärme (sensible heat) [MJ/m²/T].

    Der Wärmestrom ist positiv, wenn die Oberfläche fühlbare Wärme verliert
    (the heat flux is positive if the surface loses heat).
    """
    NDIM, NUMERIC = 1, False


class WSurf(lland_sequences.Flux1DSequence):
    """Wärmestrom von der Schneedecke zur Schneeoberfläche (heat flux from
    the snow layer to the snow surface) [MJ/m²/T].

    Der Wärmestrom ist positiv, wenn die Schneeoberfläche Wärme aus der
    Schneedecke hinzu gewinnt (the heat fluy is positive if the snow surface
    gains heat from the snow layer).
    """
    NDIM, NUMERIC = 1, False


class SFF(lland_sequences.Flux1DSequence):
    """Relativer Anteil des gefrorenen Bodenwassers bis zu einer Tiefe von
    2z (relative proportion of frozen soil water) []."""
    NDIM, NUMERIC = 1, False


class FVG(lland_sequences.Flux1DSequence):
    """Frostversiegelungsgrad (degree of frost sealing)[-]."""
    NDIM, NUMERIC = 1, False


class WaDa(lland_sequences.Flux1DSequence):
    """Wasserdargebot (water reaching the soil routine) [mm]."""
    NDIM, NUMERIC = 1, False


class QDB(lland_sequences.Flux1DSequence):
    """Direktabfluss-Abgabe aus dem Bodenspeicher (direct runoff release
    from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QIB1(lland_sequences.Flux1DSequence):
    """Erste Komponente der Interflow-Abgabe aus dem Bodenspeicher (first
    component of the interflow release from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QIB2(lland_sequences.Flux1DSequence):
    """Zweite Komponente der Interflow-Abgabe aus dem Bodenspeicher (second
    component of the interflow release from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QBB(lland_sequences.Flux1DSequence):
    """Basisabfluss-Abgabe aus dem Bodenspeicher (base flow release
    from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QKap(lland_sequences.Flux1DSequence):
    """Kapillarer Aufstieg in den Bodenspeicher (capillary rise to soil
    storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QDGZ(sequencetools.FluxSequence):
    """Gesamtzufluss in beide Direktabfluss-Gebietsspeicher (total inflow
    into both storage compartments for direct runoff) [mm]."""
    NDIM, NUMERIC = 0, False


class Q(sequencetools.FluxSequence):
    """Gesamtabfluss des Teilgebiets (runoff at the catchment outlet) [mm]."""
    NDIM, NUMERIC = 0, False
