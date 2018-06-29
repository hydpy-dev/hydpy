# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring


# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools
from hydpy.models.lland import lland_sequences


class NKor(lland_sequences.Flux1DSequence):
    """Korrigierter Niederschlag (corrected precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class TKor(lland_sequences.Flux1DSequence):
    """Korrigierte Lufttemperatur (corrected air temperature) [°C]."""
    NDIM, NUMERIC = 1, False


class ET0(lland_sequences.Flux1DSequence):
    """Grasreferenzverdunstung (reference evapotranspiration) [mm]."""
    NDIM, NUMERIC = 1, False


class EvPo(lland_sequences.Flux1DSequence):
    """Potenzielle Evaporation/Evapotranspiration (potential
    evaporation/evapotranspiration) [mm]."""
    NDIM, NUMERIC = 1, False


class NBes(lland_sequences.Flux1DSequence):
    """Gesamter Bestandsniederschlag (total stand precipitation) [mm]."""
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


class WGTF(lland_sequences.Flux1DSequence):
    """Potenzielle Schneeschmelze (maximum amount of frozen water that could
    be melted) [mm]."""
    NDIM, NUMERIC = 1, False


class Schm(lland_sequences.Flux1DSequence):
    """Tatsächliche Schneeschmelze (actual amount of water melting within the
    snow cover) [mm]."""
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


class QDGZ(sequencetools.FluxSequence):
    """Gesamtzufluss in beide Direktabfluss-Gebietsspeicher (total inflow
    into both storage compartments for direct runoff) [mm]."""
    NDIM, NUMERIC = 0, False


class Q(sequencetools.FluxSequence):
    """Gesamtabfluss des Teilgebiets (runoff at the catchment outlet) [mm]."""
    NDIM, NUMERIC = 0, False


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of the HydPy-L-Land model."""
    CLASSES = (NKor,
               TKor,
               ET0,
               EvPo,
               SBes,
               NBes,
               EvI,
               EvB,
               WGTF,
               Schm,
               WaDa,
               QDB,
               QIB1,
               QIB2,
               QBB,
               QDGZ,
               Q)
