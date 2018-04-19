# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class NKor(sequencetools.FluxSequence):
    """Korrigierter Niederschlag (corrected precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class TKor(sequencetools.FluxSequence):
    """Korrigierte Lufttemperatur (corrected air temperature) [°C]."""
    NDIM, NUMERIC = 1, False


class ET0(sequencetools.FluxSequence):
    """Grasreferenzverdunstung (reference evapotranspiration) [mm]."""
    NDIM, NUMERIC = 1, False


class EvPo(sequencetools.FluxSequence):
    """Potenzielle Evaporation/Evapotranspiration (potential
    evaporation/evapotranspiration) [mm]."""
    NDIM, NUMERIC = 1, False


class NBes(sequencetools.FluxSequence):
    """Gesamter Bestandsniederschlag (total stand precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class SBes(sequencetools.FluxSequence):
    """Schneeanteil Bestandsniederschlag (frozen stand precipitation) [mm]."""
    NDIM, NUMERIC = 1, False


class EvI(sequencetools.FluxSequence):
    """Tatsächliche Interzeptionsverdunstung (actual evaporation of
    intercepted water) [mm]."""
    NDIM, NUMERIC = 1, False


class EvB(sequencetools.FluxSequence):
    """Tatsächliche Bodenverdunstung (actual evaporation of
    soil water) [mm]."""
    NDIM, NUMERIC = 1, False


class WGTF(sequencetools.FluxSequence):
    """Potenzielle Schneeschmelze (maximum amount of frozen water that could
    be melted) [mm]."""
    NDIM, NUMERIC = 1, False


class Schm(sequencetools.FluxSequence):
    """Tatsächliche Schneeschmelze (actual amount of water melting within the
    snow cover) [mm]."""
    NDIM, NUMERIC = 1, False


class WaDa(sequencetools.FluxSequence):
    """Wasserdargebot (water reaching the soil routine) [mm]."""
    NDIM, NUMERIC = 1, False


class QDB(sequencetools.FluxSequence):
    """Direktabfluss-Abgabe aus dem Bodenspeicher (direct runoff release
    from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QIB1(sequencetools.FluxSequence):
    """Erste Komponente der Interflow-Abgabe aus dem Bodenspeicher (first
    component of the interflow release from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QIB2(sequencetools.FluxSequence):
    """Zweite Komponente der Interflow-Abgabe aus dem Bodenspeicher (second
    component of the interflow release from the soil storage) [mm]."""
    NDIM, NUMERIC = 1, False


class QBB(sequencetools.FluxSequence):
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
    _SEQCLASSES = (NKor,
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
