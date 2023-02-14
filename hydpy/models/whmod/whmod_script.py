# -*- coding: utf-8 -*-
"""
WHMod is a deterministic groundwater recharge model and accounts for all main water
fluxes in the water cycle. It is similar to the model GWN-BW, which is widely used in
Baden-Württemberg.

This module transforms regular WHMod Input data and implements and runs the
HydPy-Version of WHMod (whmod_pet).  The model is controlled by the WHMod_Main.txt in
which all variables and paths are defined. Furthermore timeseries data of the weather
stations has to be prepared, as well as the Node_Data.csv and the Station_Data.txt.
Node_Data.csv contains rasterized information about the location, land-use, field
capacity, depth to groundwater, baseflow-index and initial conditions of each cell.
Station_Data.txt links the timeseries data to the respective weather station, including
information about the location, precipitation correction and the name of the
timeseries.

The following example shows the structure of WHMod_Main.txt:

# WHMod Hydpy-Version
PERSON_IN_CHARGE	Max Mustermann
HYDPY_VERSION	5.0a0
OUTPUTDIR	Results
OUTPUTMODE	rch, txt, sum_txt # Mehrfachangabe möglich getrennt durch Komma; ...
# ...Alternativ aber noch nicht implementiert: netcdf, ganglinien
FILENAME_NODE_DATA	Node_Data.csv
FILENAME_TIMESERIES	Timeseries
FILENAME_STATION_DATA	Station_Data.txt
SIMULATION_START	1990-01-01
SIMULATION_END	1992-01-01
FREQUENCE	1d
WITH_CAPPILARY_RISE	True
DEGREE_DAY_FACTOR	4.5
PRECIP_RICHTER_CORRECTION	False # noch nicht implementiert
EVAPORATION_MODE	FAO # noch nicht implementiert
CELLSIZE	100
NODATA_VALUE	-9999.0

Paths are given relative to the base directory, which has to be defined when starting
the simulation.  The model can be run with the following command in the terminal:
{sys.executable} {hyd.__file__} run_whmod {path_to_whmod_base_directory} True
The last argument defines the output-mode. When True the progess of the simulation is
printed in the terminal.
"""

import csv
import datetime
import os
import warnings
from typing import *
from itertools import product
from dateutil.parser import parse  # type: ignore[import]
import numpy
import pandas  # type: ignore[import]
import xarray

import hydpy
from hydpy.core import devicetools
from hydpy.core import objecttools
from hydpy.exe import commandtools
from hydpy.models import whmod_pet
from hydpy.models.whmod import whmod_constants
from hydpy.core.typingtools import *

# from hydpy import inputs  # actual imports below
# from hydpy import outputs  # actual imports below


class Position(NamedTuple):
    """The row and column of a `WHMod` grid cell.

    Counting starts with 1.
    """

    row: int
    col: int

    @classmethod
    def from_elementname(cls, elementname: str) -> "Position":
        """Extract the grid cell position from the name of the |Element|
        object handling the given sequence."""
        _, row, col = elementname.split("_")
        return cls(row=int(row), col=int(col))


class Positionbounds(NamedTuple):
    """The smallest and heighest row and column values of multiple `WHMod`
    grid cells."""

    rowmin: int
    rowmax: int
    colmin: int
    colmax: int

    @classmethod
    def from_elementnames(cls, elementnames: Iterable[str]) -> "Positionbounds":
        """Extract the grid cell position from the names of the |Element|
        objects handling the given sequences."""
        rowmin = numpy.inf
        rowmax = -numpy.inf
        colmin = numpy.inf
        colmax = -numpy.inf
        for elementname in elementnames:
            row, col = Position.from_elementname(elementname)
            rowmin = min(rowmin, row)
            rowmax = max(rowmax, row)
            colmin = min(colmin, col)
            colmax = max(colmax, col)
        return Positionbounds(
            rowmin=rowmin,
            rowmax=rowmax,
            colmin=colmin,
            colmax=colmax,
        )


class _XY(NamedTuple):
    rechts: float
    hoch: float


def _collect_hrus(
    table: pandas.DataFrame, idx_: int, landuse_dict: Dict[str, Dict[str, int]]
) -> Dict[str, Dict[str, object]]:
    """Collect the hrus of the respective raster-cell. Returns Dictionary.

    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> df_knoteneigenschaften = read_nodeproperties(basedir, "Node_Data.csv")
    >>> landuse_dict = read_landuse(filepath_landuse=os.path.join(basedir,
    ... "nutzung.txt"))
    >>> _collect_hrus(table=df_knoteneigenschaften, idx_=11, landuse_dict=landuse_dict)
    {'nested_dict_nr-0': {'id': 11, 'f_id': 12, 'row': 4, 'col': 3, 'x': 3455723.97, \
'y': 5567507.03, 'area': 10000.0, 'f_area': 3500.0, 'nutz_nr': 'NADELWALD', \
'bodentyp': 'TON', 'nfk100_mittel': 90.6, 'nfk_faktor': 1.0, 'nfk_offset': 0.0, \
'flurab': 2.9, 'bfi': 0.2847355, 'verzoegerung': '10', 'init_boden': 50.0, \
'init_gwn': 40.0}, 'nested_dict_nr-1': {'id': 11, 'f_id': 12, 'row': 4, 'col': 3, \
'x': 3455723.97, 'y': 5567507.03, 'area': 10000.0, 'f_area': 3500.0, 'nutz_nr': \
'LAUBWALD', 'bodentyp': 'TON', 'nfk100_mittel': 90.6, 'nfk_faktor': 1.0, \
'nfk_offset': 0.0, 'flurab': 2.9, 'bfi': 0.2847355, 'verzoegerung': '10', \
'init_boden': 50.0, 'init_gwn': 40.0}, 'nested_dict_nr-2': {'id': 11, 'f_id': 13, \
'row': 4, 'col': 3, 'x': 3455723.97, 'y': 5567507.03, 'area': 10000.0, 'f_area': \
3000.0, 'nutz_nr': 'ZUCKERRUEBEN', 'bodentyp': 'SAND', 'nfk100_mittel': 90.6, \
'nfk_faktor': 1.0, 'nfk_offset': 0.0, 'flurab': 2.9, 'bfi': 0.2871167, \
'verzoegerung': '10', 'init_boden': 50.0, 'init_gwn': 40.0}}
    >>> df_knoteneigenschaften = read_nodeproperties(basedir, "Node_Data_wrong1.csv")
    >>> _collect_hrus(table=df_knoteneigenschaften, idx_=4, landuse_dict=landuse_dict)
    Traceback (most recent call last):
    ...
    KeyError: "Die Landnutzungsklasse 'NADELLWALD', die für die Rasterzelle mit der \
id 4 angesetzt wird ist nicht definiert"
    """
    result: Dict[str, Dict[str, object]] = {}
    hrus = table[table["id"] == idx_]
    extended_hrus = pandas.DataFrame(columns=hrus.columns)
    n_hrus = 0
    for i, hru in hrus.iterrows():
        try:
            landuse = landuse_dict[hru["nutz_nr"]]
        except KeyError as exc:
            raise KeyError(
                f"Die Landnutzungsklasse '{hru['nutz_nr']}', die für die "
                f"Rasterzelle mit der id {idx_} angesetzt wird ist nicht "
                f"definiert"
            ) from exc
        for luse, area_perc in landuse.items():
            extended_hrus.loc[n_hrus] = hrus.loc[i].copy()
            extended_hrus.loc[n_hrus, "nutz_nr"] = luse.upper()
            extended_hrus.loc[n_hrus, "f_area"] *= area_perc / 100
            n_hrus += 1

    # hru in nutzungstabelle prüfen, wenn ja: aufteilen ansonsten Fehler
    for i in range(len(extended_hrus)):
        result[f"nested_dict_nr-{i}"] = {}
        for key in table.columns:
            result[f"nested_dict_nr-{i}"][key] = extended_hrus.reset_index().loc[i, key]
    return result


def _return_con_hru(hrus: Dict[str, Dict[str, T]], con: str) -> List[T]:
    """Returns a list of the condition (con) of a hru."""
    temp_list = []
    for hru in hrus:
        temp_list.append(hrus[hru][con])
    return temp_list


def _init_gwn_to_zwischenspeicher(
    init_gwn: float, time_of_concentration: float
) -> float:
    """Calculate an estimate value for zwischenspeicher based on the expected initial
    groundwater recharge."""
    init_gwn = init_gwn / 365.25  # mm/a to mm/d
    init_storage = init_gwn * time_of_concentration
    return init_storage


def run_whmod(basedir: str, write_output: bool) -> None:
    """Run_whmod takes the WHMod input data and prepares an instance of the model.
    After the initialization the simulation can be run.  Apart from WHMod_Main.txt,
    Node_Data.csv, Station_Data.txt and a folder with the time series are required.

    How it works:
    In a first step, the rasterized whmod-elements are prepared based on the
    information provided in Node_Data.csv. After the initialization of the
    whmod-elements, the station data is provided to the meteorologic and
    evaporation-elements. All elements are conncected through respective nodes. The
    data from the weather station is interpolated to the raster cells by the
    conv-models and ultimately provided to the whmod-elements.

    The initialization of the whmod-elements (_initialize_whmod_models()), the weather
    station data (_initialize_weather_stations()) and the interpolation models
    (_initialize_conv_models()) are implemented in separate functions, which are called
    by the main function run_whmod(). The final step of the simulation is the saving of
    the results, which is implemented in the function _save_results(), which is also
    called by the main function run_whmod().

    >>> from hydpy import run_subprocess, TestIO
    >>> TestIO.clear()
    >>> projectpath = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> run_whmod(basedir=projectpath, write_output=False)
    Mean AktGrundwasserneubildung [mm/a]: 53.0961615003527
    Mean VerzGrundwasserneubildung [mm/a]: 50.27369399928801
    Mean NiederschlagRichter [mm/a]: 686.7624195313758
    Mean InterzeptionsVerdunstung [mm/a]: 127.57986770079988

    >>> run_whmod(basedir=projectpath, write_output=True) # doctest: +ELLIPSIS
    Start WHMOD calculations (...).
    Initialize WHMOD (...).
    method simulate started at ...
        |---------------------|
        ***********************
        seconds elapsed: ...
    Write Output in ...Results (...).
    Mean AktGrundwasserneubildung [mm/a]: 53.0961615003527
    Mean VerzGrundwasserneubildung [mm/a]: 50.27369399928801
    Mean NiederschlagRichter [mm/a]: 686.7624195313758
    Mean InterzeptionsVerdunstung [mm/a]: 127.57986770079988


    You can also run the script from the command prompt with hyd.py:

    >>> _ = run_subprocess(f"hyd.py run_whmod {projectpath} False")
    Mean AktGrundwasserneubildung [mm/a]: 53.0961615003527
    Mean VerzGrundwasserneubildung [mm/a]: 50.27369399928801
    Mean NiederschlagRichter [mm/a]: 686.7624195313758
    Mean InterzeptionsVerdunstung [mm/a]: 127.57986770079988

    >>> with open(os.path.join(projectpath, "Results",
    ... "monthly_timeseries_AktGrundwasserneubildung.txt"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    # Max Mustermann, ...
    # monthly WHMod-AktGrundwasserneubildung in mm
    # monthly values from 1990-01-01T00 to 1991-12-01T00
    ##########################################################
    1990-01-01 0.7028468260577259
    1990-02-01 13.957352151783375
    1990-03-01 1.654816419935198
    1990-04-01 2.443347283036093
    1990-05-01 -1.661790198704215
    1990-06-01 -0.25917369919965183
    1990-07-01 -1.1187220679497472
    1990-08-01 -2.6569262117737877
    1990-09-01 1.8769592964940027
    1990-10-01 2.6141286249982136
    1990-11-01 19.13499252643273
    1990-12-01 19.95844763416463
    1991-01-01 14.87164920372785
    1991-02-01 7.71029234354305
    1991-03-01 5.466120234439423
    1991-04-01 0.6625795438813451
    1991-05-01 -0.3612378678536788
    1991-06-01 1.4033637032773913
    1991-07-01 -1.4542704826475383
    1991-08-01 -2.7211217368665888
    1991-09-01 -1.8467053575494965
    1991-10-01 1.5482994669932146
    1991-11-01 9.942934126770014
    1991-12-01 14.254362030837713

    >>> with open(os.path.join(projectpath, "Results",
    ... "monthly_timeseries_VerzGrundwasserneubildung.txt"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    # Max Mustermann, ...
    # monthly WHMod-VerzGrundwasserneubildung in mm
    # monthly values from 1990-01-01T00 to 1991-12-01T00
    ##########################################################
    1990-01-01 0.7354062546860497
    1990-02-01 6.536275191558225
    1990-03-01 7.993232702855191
    1990-04-01 2.553324343490558
    1990-05-01 -0.07375077659961421
    1990-06-01 -0.8320219215894414
    1990-07-01 -0.144611371666009
    1990-08-01 -2.624242426838646
    1990-09-01 0.5426003650433756
    1990-10-01 1.6253440338171956
    1990-11-01 13.208931733858217
    1990-12-01 15.669861097926352
    1991-01-01 20.553139501800576
    1991-02-01 6.636077386899841
    1991-03-01 8.277475250923542
    1991-04-01 2.282198592422247
    1991-05-01 1.2149947349015224
    1991-06-01 0.6957100402292622
    1991-07-01 0.16127378204943124
    1991-08-01 -1.8628242647164013
    1991-09-01 -2.4254028076651135
    1991-10-01 1.3074037551443471
    1991-11-01 7.682496633141494
    1991-12-01 10.768426259118066

    >>> with open(os.path.join(projectpath, "Results",
    ... "monthly_mean_AktGrundwasserneubildung.txt"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE
        ncols         3
        nrows         4
        xllcorner     3455523.97
        yllcorner     5567507.03
        cellsize      100.0
        nodata_value  -9999.0
        1.214049718260273442e-01 2.756014615062301054e-01 1.019817010459422163e-01
        1.753518676336352222e-01 1.719348460699934300e-01 -2.089579331110139881e-01
        1.113094151188262632e-01 7.927670621589584521e-02 2.311449451727813076e-01
        2.937570084599854248e-01 2.506958064706713007e-01 1.635317903660306327e-01
    >>> with open(os.path.join(projectpath, "Results",
    ... "monthly_rch_AktGrundwasserneubildung.rch"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    # Max Mustermann, ...
    # monthly WHMod-AktGrundwasserneubildung in m/s
    # monthly values from 1990-01-01T00 to 1991-12-01T00
    ##########################################################
             1        51         1         1
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     4.0298e-011 2.7098e-009 3.5240e-012
     5.8612e-011 1.1418e-009-7.1452e-009
     2.9174e-011 2.1543e-012 1.3740e-009
     2.8379e-009 1.3883e-009 7.0852e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     3.5793e-009 1.0631e-008 1.5328e-009
     4.9996e-009 6.9113e-009 3.0186e-009
     2.9883e-009 8.1067e-010 9.0592e-009
     1.0953e-008 9.1995e-009 5.5499e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     4.3868e-010 7.4476e-010 1.7819e-010
     9.6702e-010 5.7982e-010 6.4246e-011
     2.4445e-010 1.1639e-010 1.1696e-009
     1.0417e-009 1.1982e-009 6.7102e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     3.8115e-010 1.6603e-009 1.2298e-010
     1.5621e-009 9.6095e-010-8.7607e-010
     1.7865e-010 8.6864e-011 2.0672e-009
     1.8604e-009 2.3682e-009 9.3908e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     9.9119e-012 3.2886e-010 1.2723e-012
     1.0133e-010 8.3732e-011-8.7863e-009
     2.0511e-012 1.3058e-012 1.4711e-010
     2.8037e-010 3.1370e-010 7.1312e-011
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     1.0174e-012 2.3132e-009 4.1851e-013
     6.1311e-011 4.8064e-010-7.6799e-009
     4.5234e-013 6.4443e-014 4.4086e-010
     1.8971e-009 9.3933e-010 3.4555e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     2.7332e-012 1.0936e-009 1.7335e-012
     8.8423e-011 2.9442e-010-8.7002e-009
     1.8439e-012 2.4722e-013 3.8015e-010
     9.7696e-010 6.4094e-010 2.0692e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     5.8607e-016 4.7051e-010 5.9146e-016
     3.3689e-013 1.0603e-010-1.3185e-008
     5.9018e-016 1.0682e-017 5.5257e-011
     4.6542e-010 1.1010e-010 7.3888e-011
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     4.1137e-012 3.0805e-009 3.4913e-012
     1.3916e-010 1.0678e-009-3.4625e-009
     3.5858e-012 2.4143e-013 1.4496e-009
     3.6183e-009 2.0194e-009 7.6587e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     5.0483e-011 2.7242e-009 3.6191e-011
     8.6146e-010 1.1609e-009-1.6718e-009
     3.7002e-011 5.1276e-012 2.0294e-009
     3.0615e-009 2.6150e-009 8.0268e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     5.1633e-009 1.0113e-008 4.4975e-009
     9.3461e-009 7.1751e-009 7.9829e-009
     4.6436e-009 2.0894e-009 9.6793e-009
     1.1195e-008 1.0134e-008 6.5700e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     7.5081e-009 7.6639e-009 7.1218e-009
     7.7078e-009 6.4708e-009 7.7489e-009
     7.3815e-009 6.5446e-009 7.8713e-009
     7.9088e-009 7.9026e-009 7.5894e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     5.5747e-009 5.7102e-009 5.3044e-009
     5.6065e-009 4.8025e-009 5.6623e-009
     5.5197e-009 5.4825e-009 5.7847e-009
     5.7531e-009 5.7908e-009 5.6379e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     2.9730e-009 3.4122e-009 2.7246e-009
     3.4194e-009 2.8365e-009 2.9373e-009
     2.8279e-009 2.8378e-009 3.7367e-009
     3.5825e-009 3.7467e-009 3.2110e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     1.7071e-009 2.3391e-009 1.3149e-009
     2.5750e-009 1.8054e-009 1.4170e-009
     1.3631e-009 1.3830e-009 2.8990e-009
     2.6787e-009 2.9285e-009 2.0788e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     8.4803e-011 7.4646e-010 4.7840e-011
     5.1980e-010 3.7496e-010-1.7700e-009
     4.9300e-011 7.1991e-011 8.2085e-010
     6.7948e-010 1.1037e-009 3.3827e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     2.8974e-011 3.9625e-010 1.2958e-011
     2.3531e-010 1.5352e-010-3.8097e-009
     1.3232e-011 1.6726e-011 3.1431e-010
     4.4449e-010 4.4129e-010 1.3414e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     4.1289e-011 3.3646e-009 1.6024e-011
     5.1787e-010 9.0439e-010-5.3030e-009
     1.6830e-011 1.2293e-011 1.1402e-009
     3.2260e-009 1.9154e-009 6.4514e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     1.0800e-013 6.9241e-010 3.9418e-014
     2.2268e-011 1.1881e-010-8.2911e-009
     3.9652e-014 1.6434e-014 9.3029e-011
     4.5710e-010 3.0687e-010 8.4912e-011
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     1.3550e-015 8.2011e-011 6.9764e-016
     2.0702e-012 1.6296e-011-1.2413e-008
     7.1351e-016 1.6307e-016 1.2850e-011
     4.8891e-011 4.7225e-011 1.2292e-011
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     1.4846e-013 8.9732e-010 1.3402e-013
     3.7507e-012 2.8780e-010-1.1864e-008
     1.3777e-013 4.2916e-015 2.4226e-010
     1.3558e-009 3.2430e-010 2.0275e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     6.8313e-012 1.9552e-009 5.1955e-012
     9.9705e-011 7.9047e-010-1.5831e-009
     5.3635e-012 3.4622e-013 1.1132e-009
     2.6695e-009 1.3246e-009 5.4963e-010
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     1.3597e-009 7.1142e-009 1.1252e-009
     3.6297e-009 4.2708e-009 3.8605e-009
     1.1713e-009 2.4787e-010 5.9657e-009
     7.9071e-009 6.4096e-009 2.9704e-009
             1         1         0         0
            18     1.000(20e12.4)                   -1     RECHARGE
     4.7678e-009 6.3129e-009 4.2770e-009
     6.1842e-009 4.9651e-009 5.8056e-009
     4.4418e-009 2.3116e-009 6.3612e-009
     6.7004e-009 6.4698e-009 5.2662e-009
    <BLANKLINE>
    """
    write_output_ = print_hydpy_progress(write_output=write_output)

    whmod_main = read_whmod_main(basedir)

    person_in_charge = whmod_main["PERSON_IN_CHARGE"][1].strip()
    hydpy_version = whmod_main["HYDPY_VERSION"][1].strip()

    check_hydpy_version(hydpy_version=hydpy_version)

    outputdir = os.path.join(basedir, whmod_main["OUTPUTDIR"][1].strip())
    filename_node_data = whmod_main["FILENAME_NODE_DATA"][1].strip()
    filename_timeseries = whmod_main["FILENAME_TIMESERIES"][1].strip()
    filename_station_data = whmod_main["FILENAME_STATION_DATA"][1].strip()
    filename_landuse = whmod_main["FILENAME_LANDUSE"][1].strip()
    with_capillary_rise = whmod_main["WITH_CAPPILARY_RISE"][1].strip()
    day_degree_factor = whmod_main["DEGREE_DAY_FACTOR"][1].strip()
    root_depth_option = whmod_main["ROOT_DEPTH_OPTION"][1].strip()
    simulation_start = whmod_main["SIMULATION_START"][1].strip()
    simulation_end = whmod_main["SIMULATION_END"][1].strip()
    frequence = whmod_main["FREQUENCE"][1].strip()
    richter = bool(
        whmod_main["PRECIP_RICHTER_CORRECTION"][1].strip() in ("True", "true", 1)
    )
    cellsize = float(whmod_main["CELLSIZE"][1].strip())
    nodata_value = whmod_main["NODATA_OUTPUT_VALUE"][1].strip()
    outputconfig = [
        stepsize.strip() for stepsize in whmod_main["OUTPUTCONFIG"][1].split(",")
    ]

    hydpy.pub.timegrids = simulation_start, simulation_end, frequence
    hydpy.pub.options.parameterstep = frequence
    hydpy.pub.options.checkseries = False

    df_knoteneigenschaften = read_nodeproperties(
        basedir=basedir, filename_node_data=filename_node_data
    )
    filepath_landuse = os.path.join(basedir, filename_landuse)

    landuse_dict = read_landuse(filepath_landuse=filepath_landuse)

    df_stammdaten = read_stationdata(os.path.join(basedir, filename_station_data),
                                     richter=richter)
    root_depth_dict = read_root_depth(
        root_depth_option=root_depth_option, basedir=basedir
    )

    # define Selections
    whmod_selection = hydpy.Selection("raster")
    evap_selection_stat = hydpy.Selection("evap_stat")
    evap_selection_raster = hydpy.Selection("evap_raster")
    meteo_selection_stat = hydpy.Selection("meteo_stat")
    cssr_selection_stat = hydpy.Selection("CSSR_stat")
    gsr_selection_stat = hydpy.Selection("GSR_stat")
    temp_selection_stat = hydpy.Selection("temp_stat")
    temp_selection_raster = hydpy.Selection("temp_raster")
    prec_selection_stat = hydpy.Selection("prec_stat")
    prec_selection_raster = hydpy.Selection("prec_raster")

    hp = hydpy.HydPy("run_WHMod")
    hydpy.pub.sequencemanager.filetype = "asc"

    node2xy: Dict[hydpy.Node, _XY] = {}

    _initialize_whmod_models(
        write_output=write_output_,
        df_knoteneigenschaften=df_knoteneigenschaften,
        prec_selection_raster=prec_selection_raster,
        temp_selection_raster=temp_selection_raster,
        evap_selection_raster=evap_selection_raster,
        whmod_selection=whmod_selection,
        with_capillary_rise=with_capillary_rise,
        day_degree_factor=day_degree_factor,
        root_depth=root_depth_dict,
        node2xy=node2xy,
        landuse_dict=landuse_dict,
    )

    _initialize_weather_stations(
        df_stammdaten=df_stammdaten,
        richter=richter,
        cssr_selection_stat=cssr_selection_stat,
        gsr_selection_stat=gsr_selection_stat,
        meteo_selection_stat=meteo_selection_stat,
        evap_selection_stat=evap_selection_stat,
        temp_selection_stat=temp_selection_stat,
        prec_selection_stat=prec_selection_stat,
        filename_timeseries=filename_timeseries,
        basedir=basedir,
        node2xy=node2xy,
    )

    _initialize_conv_models(
        evap_selection_stat=evap_selection_stat,
        evap_selection_raster=evap_selection_raster,
        temp_selection_stat=temp_selection_stat,
        temp_selection_raster=temp_selection_raster,
        prec_selection_stat=prec_selection_stat,
        prec_selection_raster=prec_selection_raster,
        node2xy=node2xy,
    )

    # Merge Selections
    hydpy.pub.selections = hydpy.Selections(
        whmod_selection,
        cssr_selection_stat,
        gsr_selection_stat,
        meteo_selection_stat,
        evap_selection_stat,
        evap_selection_raster,
        temp_selection_stat,
        temp_selection_raster,
        prec_selection_stat,
        prec_selection_raster,
    )

    complete_network = hydpy.Selection("complete_network")

    for selection in hydpy.pub.selections:
        complete_network += selection

    hp.update_devices(selection=complete_network)

    hydpy.pub.selections.add_selections(complete_network)

    # Update elements
    for element in hp.elements:
        element.model.parameters.update()

    # Define Loggers according to OUTPUTCONFIG
    loggers = []
    for file in outputconfig:
        loggers.append(read_outputconfig(basedir=basedir, outputconfigfile=file))
    hydpy.pub.selections += hydpy.Selection(
        name="complete", nodes=hp.nodes, elements=hp.elements
    )
    whm_elements = (
        hydpy.pub.selections["complete"].search_modeltypes("whmod_pet").elements
    )

    seriesdir = os.path.join(outputdir, "series")
    hydpy.pub.sequencemanager.currentdir = seriesdir
    hydpy.pub.sequencemanager.filetype = "nc"

    for element in whm_elements:
        for logger in loggers:
            for seq in logger["sequence"]:
                sequence = getattr(element.model.sequences.fluxes, seq.lower())
                if not sequence.diskflag_writing:
                    sequence.prepare_series(allocate_ram=False, write_jit=True)

    hp.simulate()

    hydpy.pub.sequencemanager.overwrite = True
    hydpy.pub.sequencemanager.currentdir = outputdir

    if write_output:
        commandtools.print_textandtime(f"Write Output in {outputdir}")

    aggregated_series = aggregate_whmod_series(loggers=loggers, seriesdir=seriesdir)

    save_results(
        aggregated_series=aggregated_series,
        loggers=loggers,
        outputdir=outputdir,
        cellsize=cellsize,
        df_knoteneigenschaften=df_knoteneigenschaften,
        person_in_charge=person_in_charge,
        nodata_value=nodata_value,
    )


def check_hydpy_version(hydpy_version: str) -> None:
    """Check Hydpy-Version

    >>> import hydpy
    >>> check_hydpy_version(hydpy_version=hydpy.__version__)

    >>> check_hydpy_version(hydpy_version="5.0")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    UserWarning: The currently used Hydpy-Version (...) differs from the \
Hydpy-Version (5.0) defined in WHMod_Main.txt.
    """
    if hydpy_version != hydpy.__version__:
        warnings.warn(
            f"The currently used Hydpy-Version ({hydpy.__version__}) differs from the "
            f"Hydpy-Version ({hydpy_version}) defined in WHMod_Main.txt."
        )


def print_hydpy_progress(write_output: bool) -> bool:
    """Activate hydpy printprogress and return wirte_output handle.

    >>> print_hydpy_progress(write_output="True")  # doctest: +ELLIPSIS
    Start WHMOD calculations (...).
    True
    >>> print_hydpy_progress(write_output="False")
    False
    """
    write_output_ = objecttools.value2bool("x", write_output)
    if write_output_:
        commandtools.print_textandtime("Start WHMOD calculations")
        hydpy.pub.options.printprogress = True
    else:
        hydpy.pub.options.printprogress = False
    return write_output_


def read_stationdata(path_station_data: str, richter: bool = False) -> pandas.DataFrame:
    """
    Lese die Stationsdaten ein.

    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> station_path = os.path.join(basedir, "Station_Data.txt")
    >>> pandas.set_option('display.expand_frame_repr', False)

    # pylint: disable=line-too-long
    >>> read_stationdata(path_station_data=station_path, richter=False)  # doctest:+NORMALIZE_WHITESPACE
       Messnetz  StationsNr          X          Y      Lat    Long  HNN       Richterklasse                  Dateiname          Messungsart
    0       DWD           1  3465773.0  5543398.0  50.0259  8.5213 -999                -999       1_Lufttemperatur.asc       Lufttemperatur
    1       DWD           1  3465773.0  5543398.0  50.0259  8.5213 -999                -999     1_Relative-Feuchte.asc     Relative-Feuchte
    2       DWD           1  3465773.0  5543398.0  50.0259  8.5213 -999                -999  1_Windgeschwindigkeit.asc  Windgeschwindigkeit
    3       DWD           1  3465773.0  5543398.0  50.0259  8.5213 -999                -999    1_Sonnenscheindauer.asc    Sonnenscheindauer
    4       DWD           1  3465773.0  5543398.0  50.0259  8.5213 -999                -999            1_Luftdruck.asc            Luftdruck
    5       DWD           1  3465773.0  5543398.0  50.0259  8.5213 -999   leicht_geschuetzt         1_Niederschlag.asc         Niederschlag
    6       DWD           2  3476845.0  5556809.0  50.1470  8.6750 -999                -999       2_Lufttemperatur.asc       Lufttemperatur
    7       DWD           2  3476845.0  5556809.0  50.1470  8.6750 -999                -999     2_Relative-Feuchte.asc     Relative-Feuchte
    8       DWD           2  3476845.0  5556809.0  50.1470  8.6750 -999                -999  2_Windgeschwindigkeit.asc  Windgeschwindigkeit
    9       DWD           2  3476845.0  5556809.0  50.1470  8.6750 -999                -999    2_Sonnenscheindauer.asc    Sonnenscheindauer
    10      DWD           2  3476845.0  5556809.0  50.1470  8.6750 -999                -999            2_Luftdruck.asc            Luftdruck
    11      DWD           2  3476845.0  5556809.0  50.1470  8.6750 -999  maessig_geschuetzt         2_Niederschlag.asc         Niederschlag
    12      DWD           3  3476407.0  5554586.0  50.1270  8.6690 -999                -999       3_Lufttemperatur.asc       Lufttemperatur
    13      DWD           3  3476407.0  5554586.0  50.1270  8.6690 -999                -999     3_Relative-Feuchte.asc     Relative-Feuchte
    14      DWD           3  3476407.0  5554586.0  50.1270  8.6690 -999                -999  3_Windgeschwindigkeit.asc  Windgeschwindigkeit
    15      DWD           3  3476407.0  5554586.0  50.1270  8.6690 -999                -999    3_Sonnenscheindauer.asc    Sonnenscheindauer
    16      DWD           3  3476407.0  5554586.0  50.1270  8.6690 -999                -999            3_Luftdruck.asc            Luftdruck
    17      DWD           3  3476407.0  5554586.0  50.1270  8.6690 -999    stark_geschuetzt         3_Niederschlag.asc         Niederschlag
    18      DWD           4  3475760.0  5553921.0  50.1210  8.6600 -999                -999       4_Lufttemperatur.asc       Lufttemperatur
    19      DWD           4  3475760.0  5553921.0  50.1210  8.6600 -999                -999     4_Relative-Feuchte.asc     Relative-Feuchte
    20      DWD           4  3475760.0  5553921.0  50.1210  8.6600 -999                -999  4_Windgeschwindigkeit.asc  Windgeschwindigkeit
    21      DWD           4  3475760.0  5553921.0  50.1210  8.6600 -999                -999    4_Sonnenscheindauer.asc    Sonnenscheindauer
    22      DWD           4  3475760.0  5553921.0  50.1210  8.6600 -999                -999            4_Luftdruck.asc            Luftdruck
    23      DWD           4  3475760.0  5553921.0  50.1210  8.6600 -999                frei         4_Niederschlag.asc         Niederschlag
    24      DWD           5  3438168.0  5543991.0      NaN     NaN -999   leicht_geschuetzt         5_Niederschlag.asc         Niederschlag
    25      DWD           6  3457044.0  5556598.0      NaN     NaN -999  maessig_geschuetzt         6_Niederschlag.asc         Niederschlag
    26      DWD           7  3484302.0  5540430.0      NaN     NaN -999    stark_geschuetzt         7_Niederschlag.asc         Niederschlag
    27      DWD           8  3445255.0  5536238.0      NaN     NaN -999                frei         8_Niederschlag.asc         Niederschlag
    28      DWD           9  3435601.0  5521105.0      NaN     NaN -999                frei         9_Niederschlag.asc         Niederschlag

    # pylint: enable=line-too-long
    >>> station_path = os.path.join(basedir, "Station_Data_wrong1.txt")
    >>> read_stationdata(path_station_data=station_path)
    Traceback (most recent call last):
    ...
    ValueError: Die Dateinamen müssen den Parameternamen: ('Lufttemperatur', \
'Relative-Feuchte', 'Windgeschwindigkeit', 'Sonnenscheindauer', 'Luftdruck', \
'Niederschlag') entsprechen. Die Messsungsart ist jedoch RelativeFeuchte
    >>> station_path = os.path.join(basedir, "Station_Data_wrong2.txt")
    >>> read_stationdata(path_station_data=station_path, richter=False)
    Traceback (most recent call last):
    ...
    ValueError: Notwendiger Spaltenname 'StationsNr' ist nicht in der \
Stationsdaten-Datei vorhanden.
    >>> station_path = os.path.join(basedir, "Station_Data_wrong3.txt")
    >>> read_stationdata(path_station_data=station_path, richter=True)
    Traceback (most recent call last):
    ...
    ValueError: Die Dateinamen müssen den Parameternamen: ('frei', \
'leicht_geschuetzt', 'maessig_geschuetzt', 'stark_geschuetzt') entsprechen. Die \
Richterklasse ist jedoch wald
    """
    df_stammdaten = pandas.read_csv(path_station_data, comment="#", sep="\t")
    df_stammdaten["Messungsart"] = df_stammdaten["Dateiname"].apply(
        lambda a: a.split("_")[1].split(".")[0]
    )
    possible_variables = (
        "Lufttemperatur",
        "Relative-Feuchte",
        "Windgeschwindigkeit",
        "Sonnenscheindauer",
        "Luftdruck",
        "Niederschlag",
    )
    valid_messart = df_stammdaten["Messungsart"].isin(possible_variables)
    if not all(valid_messart):
        raise ValueError(
            f"Die Dateinamen müssen den Parameternamen: "
            f"{possible_variables} entsprechen. Die Messsungsart ist "
            f"jedoch "
            f"{', '.join(df_stammdaten['Messungsart'][~valid_messart].values)}"
        )
    valid_columns = ["StationsNr", "Messungsart", "Dateiname", "Lat", "Long", "X", "Y"]
    if richter:
        valid_columns.append("Richterklasse")

    for column in valid_columns:
        if column not in df_stammdaten.columns:
            raise ValueError(
                f"Notwendiger Spaltenname '{column}' ist nicht in der "
                f"Stationsdaten-Datei vorhanden."
            )
    if richter:
        df_stammdaten["Richterklasse"] = df_stammdaten["Richterklasse"].astype(str)
        possible_richterklasse = ("frei", "leicht_geschuetzt", "maessig_geschuetzt",
                               "stark_geschuetzt")
        niederschlag = df_stammdaten[df_stammdaten['Messungsart'] == "Niederschlag"]
        valid_richterklasse = niederschlag["Richterklasse"].isin(
            possible_richterklasse)
        if not all(valid_richterklasse):
            actual_richter = niederschlag['Richterklasse'][~valid_richterklasse].values
            raise ValueError(
                f"Die Dateinamen müssen den Parameternamen: {possible_richterklasse} "
                f"entsprechen. Die Richterklasse ist jedoch "
                f"{', '.join(actual_richter)}"
            )
    return df_stammdaten


def read_nodeproperties(basedir: str, filename_node_data: str) -> pandas.DataFrame:
    """Read the node property file"""
    # Read Node Data
    dtype_knoteneigenschaften = {
        "id": int,
        "f_id": int,
        "row": int,
        "col": int,
        "x": float,
        "y": float,
        "area": float,
        "f_area": float,
        "nutz_nr": str,
        "bodentyp": str,
        "nfk100_mittel": float,
        "nfk_faktor": float,
        "nfk_offset": float,
        "flurab": float,
        "bfi": float,
        "verzoegerung": str,
        "init_boden": float,
        "init_gwn": float,
    }
    df_knoteneigenschaften = pandas.read_csv(
        os.path.join(basedir, filename_node_data),
        skiprows=[1],
        sep=";",
        comment="#",
        decimal=".",
        dtype=dtype_knoteneigenschaften,
    )
    return df_knoteneigenschaften


def read_whmod_main(basedir: str) -> pandas.DataFrame:
    """
    Read the whmod main file.
    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> pandas.set_option('display.expand_frame_repr', False)

    # pylint: disable=line-too-long
    >>> read_whmod_main(basedir=basedir)
    0 PERSON_IN_CHARGE HYDPY_VERSION OUTPUTDIR FILENAME_NODE_DATA FILENAME_TIMESERIES FILENAME_STATION_DATA FILENAME_LANDUSE   ROOT_DEPTH_OPTION SIMULATION_START SIMULATION_END FREQUENCE WITH_CAPPILARY_RISE DEGREE_DAY_FACTOR PRECIP_RICHTER_CORRECTION EVAPORATION_MODE CELLSIZE NODATA_OUTPUT_VALUE                                       OUTPUTCONFIG
    1   Max Mustermann         6.0a0   Results      Node_Data.csv          Timeseries      Station_Data.txt      nutzung.txt  max_root_depth.txt       1990-01-01     1992-01-01        1d                True               4.5                     True              FAO       100             -9999.0  Tageswerte.txt, Monatswerte.txt, Variablewerte...

    # pylint: enable=line-too-long
    """
    dtype_whmod_main = {
        "PERSON_IN_CHARGE": str,
        "HYDPY_VERSION": str,
        "OUTPUTDIR": str,
        "ROOT_DEPTH_OPTION": str,
        "FILENAME_NODE_DATA": str,
        "FILENAME_TIMESERIES": str,
        "FILENAME_STATION_DATA": str,
        "SIMULATION_START": str,
        "SIMULATION_END": str,
        "FREQUENCE": str,
        "WITH_CAPPILARY_RISE": bool,
        "DEGREE_DAY_FACTOR": float,
        "PRECIP_RICHTER_CORRECTION": bool,
        "EVAPORATION_MODE": str,
        "CELLSIZE": int,
        "NODATA_VALUE": float,
        "OUTPUTCONFIG": str,
    }
    whmod_main = pandas.read_csv(
        os.path.join(basedir, "WHMod_Main.txt"),
        sep="\t",
        comment="#",
        header=None,
        index_col=0,
        dtype=dtype_whmod_main,
    ).T
    return whmod_main


def read_landuse(filepath_landuse: str) -> Dict[str, Dict[str, int]]:
    """Read the landuse file.

    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> df_knoteneigenschaften = read_nodeproperties(basedir, "Node_Data.csv")
    >>> landuse_dict = read_landuse(filepath_landuse=os.path.join(basedir,
    ... "nutzung_wrong.txt"))
    Traceback (most recent call last):
    ...
    ValueError: Landnutzungsklasse 1 fehlerhaft. Summe muss 100 ergeben
    """
    landuse_dict = {}
    with open(filepath_landuse, mode="r", encoding="utf-8") as infile:
        reader = csv.reader(infile, delimiter=":")
        for row in reader:
            if row[0].strip().startswith("#"):
                continue
            landuse_dict[row[0].strip()] = {
                u[0].strip(): int(u[1])
                for u in [s.split("=") for s in row[1].split(",")]
            }
    # check dictionary
    for lnk, landuse_orig_dict in landuse_dict.items():
        rel_area_sum = 0
        for vals in landuse_orig_dict.values():
            rel_area_sum += vals
        if rel_area_sum != 100:
            raise ValueError(
                f"Landnutzungsklasse {lnk} fehlerhaft. Summe muss 100 ergeben"
            )
    return landuse_dict


def read_root_depth(root_depth_option: str, basedir: str) -> Dict[str, float]:
    """Reads maximum root_depth from file or takes predefined values according to the
    chosen option.

    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> read_root_depth(root_depth_option="WABOA", basedir=basedir)
    {'gras': 0.6, 'laubwald': 1.5, 'nadelwald': 1.9, 'mais': 1.0, 'sommerweizen': 1.0, \
'winterweizen': 1.0, 'zuckerrueben': 1.0}

    >>> read_root_depth(root_depth_option="max_root_depth.txt", basedir=basedir)
    {'gras': 0.6, 'laubwald': 1.5, 'nadelwald': 1.5, 'mais': 1.0, 'sommerweizen': 1.0, \
'winterweizen': 1.0, 'zuckerrueben': 0.8}

    >>> read_root_depth(root_depth_option="max_root_depth_wrong1.txt", basedir=basedir)
    Traceback (most recent call last):
    ...
    ValueError: Unable to parse string "WABOA" at position 6

    >>> read_root_depth(root_depth_option="max_root_depth_wrong2.txt",
    ...                 basedir=basedir)  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError:
    In der Datei zur Wurzeltiefe wurde ein Wert für 'mischwald' definiert, der nicht \
zu den Basislandnutzungsklassen gehört
    In der Datei zur Wurzeltiefe wurde kein Wert für 'mais' definiert

    >>> read_root_depth(root_depth_option="test.txt", basedir=basedir)
    Traceback (most recent call last):
    ...
    ValueError: Der Wert für ROOT_DEPTH_OPTION (test.txt) ist ungültig er muss \
entweder auf eine Datei verweisen oder den Wert 'BK', 'WABOA', 'TGU' oder 'DARMSTADT' \
enthalten.
    """
    predefined_root_depth = pandas.DataFrame(
        index=[
            "gras",
            "laubwald",
            "nadelwald",
            "mais",
            "sommerweizen",
            "winterweizen",
            "zuckerrueben",
        ],
        columns=["BK", "WABOA", "TGU", "DARMSTADT"],
        data=[
            [0.3, 0.6, 0.5, 1.0],
            [1.2, 1.5, 1.5, 2.5],
            [0.8, 1.9, 1.9, 2.5],
            [0.6, 1.0, 0.5, 1.0],
            [0.6, 1.0, 0.5, 1.0],
            [0.6, 1.0, 0.5, 1.0],
            [0.6, 1.0, 0.4, 1.0],
        ],
    )
    if root_depth_option in ("BK", "WABOA", "TGU", "DARMSTADT"):
        root_depth = dict(predefined_root_depth[root_depth_option])
    else:
        try:
            root_depth_table = pandas.read_csv(
                os.path.join(basedir, root_depth_option),
                sep="=",
                comment="#",
                index_col=0,
                header=None,
                names=["BENUTZERDEFINIERT"],
            )
        except FileNotFoundError as exc:
            raise ValueError(
                f"Der Wert für ROOT_DEPTH_OPTION ({root_depth_option}) ist "
                f"ungültig er muss entweder auf eine Datei verweisen oder den "
                f"Wert 'BK', 'WABOA', 'TGU' oder 'DARMSTADT' enthalten."
            ) from exc
        root_depth_table.index = [i.lower() for i in root_depth_table.index]
        error = []
        for entry in root_depth_table.index:
            if entry not in predefined_root_depth.index:
                error.append(
                    f"In der Datei zur Wurzeltiefe wurde ein Wert für "
                    f"'{entry}' definiert, der nicht zu den "
                    f"Basislandnutzungsklassen gehört"
                )
        for entry in predefined_root_depth.index:
            if entry not in root_depth_table.index:
                error.append(
                    f"In der Datei zur Wurzeltiefe wurde kein Wert für "
                    f"'{entry}' definiert"
                )
        if error:
            raise ValueError("\n" + "\n".join(error))

        root_depth = dict(pandas.to_numeric(root_depth_table["BENUTZERDEFINIERT"]))
    return root_depth


def read_outputconfig(
    outputconfigfile: str, basedir: str
) -> Dict[str, List[Union[str, pandas.DatetimeIndex]]]:
    """
    Read text files which define the stepsize of the outputfiles.
    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> hydpy.pub.timegrids = "1990-01-01", "1992-01-01", "1d"
    >>> read_outputconfig(outputconfigfile="Tageswerte.txt", basedir=basedir)
    {'sequence': ['AktGrundwasserneubildung', 'VerzGrundwasserneubildung', \
'NiederschlagRichter', 'InterzeptionsVerdunstung'], 'steps': ['daily'], \
'name_rch_file': ['daily_rch'], 'name_mean_file': ['daily_mean'], \
'name_time_series': ['daily_timeseries']}
    >>> read_outputconfig(outputconfigfile="Variablewerte.txt", basedir=basedir)
    {'sequence': ['AktGrundwasserneubildung', 'VerzGrundwasserneubildung', \
'NiederschlagRichter'], 'steps': [DatetimeIndex(['1990-01-01', '1990-02-01', \
'1991-01-01', '1992-01-01'], dtype='datetime64[ns]', freq=None)], 'name_rch_file': \
['user_rch'], 'name_mean_file': ['user_mean'], 'name_time_series': ['user_timeseries']}

    >>> read_outputconfig(outputconfigfile="Variablewerte_wrong1.txt", basedir=basedir)
    Traceback (most recent call last):
    ...
    ValueError: Chose either one or multiple of the aggregation methods ('daily', \
'monthly', 'yearly') OR define your own aggregation timegrid
    >>> read_outputconfig(outputconfigfile="Variablewerte_wrong2.txt", basedir=basedir)
    Traceback (most recent call last):
    ...
    AssertionError: Output timesteps of user defined output have to be sorted
    >>> read_outputconfig(outputconfigfile="Variablewerte_wrong3.txt", basedir=basedir)
    Traceback (most recent call last):
    ...
    ValueError: Aggregation timegrid DatetimeIndex(['2000-01-01', '2000-02-01', \
'2002-01-01'], dtype='datetime64[ns]', freq=None) outside simulation timegrid.
    """
    filepath = os.path.join(basedir, outputconfigfile)
    outputconfig_dict = {}
    with open(filepath, mode="r", encoding="utf-8") as infile:
        lines = infile.readlines()
        for line in lines:
            if line.strip().startswith("#"):
                continue
            if ":" in line:
                split_line = line.split(":")
                entryname = split_line[0].strip()
                entries = split_line[1].strip()
            else:
                entries += ", " + line.strip()

            entries_list = [entry.strip() for entry in entries.split(",")]

            outputconfig_dict[entryname] = entries_list
    check_date = [is_date(da) for da in outputconfig_dict["steps"]]
    allowed_steps = ("daily", "monthly", "yearly")
    if all(step in allowed_steps for step in outputconfig_dict["steps"]):
        pass
    elif all(check_date):
        aggregation_timegrid = pandas.to_datetime(
            [parse(string, fuzzy=False) for string in outputconfig_dict["steps"]]
        )
        outputconfig_dict["steps"] = [
            aggregation_timegrid,
        ]
        if any(sorted(aggregation_timegrid) != aggregation_timegrid):
            raise AssertionError(
                "Output timesteps of user defined output have to be sorted"
            )
        if (
            aggregation_timegrid[0] < hydpy.pub.timegrids.eval_.firstdate
            or aggregation_timegrid[0] > hydpy.pub.timegrids.eval_.lastdate
        ):
            raise ValueError(
                f"Aggregation timegrid {aggregation_timegrid} outside simulation "
                f"timegrid."
            )
    elif any(check_date):
        raise ValueError(
            f"Chose either one or multiple of the aggregation methods "
            f"{allowed_steps} OR define your own aggregation timegrid"
        )
    return outputconfig_dict


def _initialize_whmod_models(
    write_output: bool,
    df_knoteneigenschaften: pandas.DataFrame,
    prec_selection_raster: hydpy.Selection,
    temp_selection_raster: hydpy.Selection,
    evap_selection_raster: hydpy.Selection,
    whmod_selection: hydpy.Selection,
    with_capillary_rise: bool,
    day_degree_factor: float,
    landuse_dict: Dict[str, Dict[str, int]],
    root_depth: Dict[str, float],
    node2xy: Dict[hydpy.Node, _XY],
) -> None:
    """In this function, the whmod-elements are initialized based on the data provided
    in Node_Data.csv.  The arguments of this function are HydPy-selections, which
    contain the respective nodes and elements. Furthermore information about cappilary
    rise (with_capillary_rise) and the degree day factor (day_degree_factor) have to be
    provided.
    """
    from hydpy import inputs  # pylint: disable=import-outside-toplevel

    # Initialize WHMod-Models
    if write_output:
        commandtools.print_textandtime("Initialize WHMOD")

    for idx in sorted(df_knoteneigenschaften["id"].unique()):

        row = getattr(
            df_knoteneigenschaften[df_knoteneigenschaften["id"] == idx], "row"
        ).values[0]
        col = getattr(
            df_knoteneigenschaften[df_knoteneigenschaften["id"] == idx], "col"
        ).values[0]

        name = f"{str(row).zfill(3)}_{str(col).zfill(3)}"

        # Initialize Precipitation Nodes
        precnode = hydpy.Node(f"P_{name}", variable=inputs.whmod_Niederschlag)
        prec_selection_raster.nodes.add_device(precnode)

        # Initialize Temperature Nodes
        tempnode = hydpy.Node(f"T_{name}", variable=inputs.whmod_Temp_TM)
        temp_selection_raster.nodes.add_device(tempnode)

        # Initialize Evap Nodes
        evapnode = hydpy.Node(f"E_{name}", variable=inputs.whmod_ET0)
        evap_selection_raster.nodes.add_device(evapnode)

        # Initialize WHMod-Elements
        raster = hydpy.Element(f"WHMod_{name}", inputs=(precnode, tempnode, evapnode))

        # Hinzufügen zu WHMod-Selection
        whmod_selection.elements.add_device(raster)

        # find number of hrus in element
        hrus = _collect_hrus(
            table=df_knoteneigenschaften, idx_=idx, landuse_dict=landuse_dict
        )

        # Coordinates
        rechts = _return_con_hru(hrus, "x")[0]
        assert isinstance(rechts, float)
        hoch = _return_con_hru(hrus, "y")[0]
        assert isinstance(hoch, float)
        xy = _XY(rechts=rechts, hoch=hoch)

        # Coordinate for Nodes
        for node in (precnode, tempnode, evapnode):
            node2xy[node] = xy

        # temporary WHMod-Model
        whmod = hydpy.prepare_model(whmod_pet, "1d")
        raster.model = whmod

        # add Parameters to model (control)
        con = whmod.parameters.control

        con.area(sum(_return_con_hru(hrus, "f_area")))
        con.nmb_cells(len(hrus))
        con.mitfunktion_kapillareraufstieg(with_capillary_rise)

        # iterate over all hrus and create a list with the land use
        temp_list = []
        for i in range(len(_return_con_hru(hrus, "nutz_nr"))):
            nutz_nr = _return_con_hru(hrus, "nutz_nr")[i]
            assert isinstance(nutz_nr, str)
            temp_list.append(whmod_constants.LANDUSE_CONSTANTS[nutz_nr])
        con.nutz_nr(temp_list)

        # fmt: off
        con.maxinterz(
            gras=[0.4, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6, 0.5, 0.4],
            laubwald=[0.1, 0.1, 0.3, 0.8, 1.4, 2.2, 2.4, 2.4, 2.2, 1.6, 0.3, 0.1],
            mais=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04, 0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
            nadelwald=[2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
            sommerweizen=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04, 0.92, 0.62, 0.26, 0.04, 0.0, 0.0],  # pylint: disable=line-too-long
            winterweizen=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04, 0.92, 0.62, 0.26, 0.04, 0.0, 0.0],  # pylint: disable=line-too-long
            zuckerrueben=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04, 0.92, 0.62, 0.26, 0.04, 0.0, 0.0],  # pylint: disable=line-too-long
            versiegelt=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            wasser=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        )
        # fmt: on

        # iterate over all hrus and create a list with the soil type
        temp_list = []
        for i in range(len(_return_con_hru(hrus, "bodentyp"))):
            bodentyp = _return_con_hru(hrus, "bodentyp")[i]
            assert isinstance(bodentyp, str)
            temp_list.append(whmod_constants.SOIL_CONSTANTS[bodentyp.upper()])
        con.bodentyp(temp_list)

        # fmt: off
        # DWA-M 504:
        ackerland = [0.733, 0.733, 0.774, 0.947, 1.188, 1.181, 1.185, 1.151, 0.974, 0.853, 0.775, 0.733]  # pylint: disable=line-too-long
        con.fln(
            gras=1.0,  # DWA-M 504
            laubwald=[1.003, 1.003, 1.053, 1.179, 1.114, 1.227, 1.241, 1.241, 1.241, 1.139, 1.082, 1.003],  # DWA-M 504  # pylint: disable=line-too-long
            mais=ackerland,
            nadelwald=1.335,  # DWA-M 504
            sommerweizen=ackerland,
            winterweizen=ackerland,
            zuckerrueben=ackerland,
            versiegelt=0.0,
            wasser=[1.165, 1.217, 1.256, 1.283, 1.283, 1.296, 1.283, 1.283, 1.270, 1.230, 1.165, 1.139],  # pylint: disable=line-too-long
        )  # DWA-M 504
        # fmt: on

        con.f_area(_return_con_hru(hrus, "f_area"))
        con.gradfaktor(float(day_degree_factor))
        nfk100_mittel = _return_con_hru(hrus, "nfk100_mittel")[0]
        assert isinstance(nfk100_mittel, float)
        nfk_faktor = _return_con_hru(hrus, "nfk_faktor")[0]
        assert isinstance(nfk_faktor, float)
        nfk_offset = _return_con_hru(hrus, "nfk_offset")[0]
        assert isinstance(nfk_offset, float)
        nfk = (nfk100_mittel * nfk_faktor) + nfk_offset
        con.nfk100_mittel(nfk)

        con.flurab(_return_con_hru(hrus, "flurab"))
        con.maxwurzeltiefe(**root_depth)
        con.minhasr(
            gras=4.0,
            laubwald=6.0,
            mais=3.0,
            nadelwald=6.0,
            sommerweizen=6.0,
            winterweizen=6.0,
            zuckerrueben=6.0,
        )
        con.kapilschwellwert(
            sand=0.8, sand_bindig=1.4, lehm=1.4, ton=1.35, schluff=1.75, torf=0.85
        )
        con.kapilgrenzwert(
            sand=0.4, sand_bindig=0.85, lehm=0.45, ton=0.25, schluff=0.75, torf=0.55
        )
        con.bfi(_return_con_hru(hrus, "bfi")[0])

        verzoegerung = str(_return_con_hru(hrus, "verzoegerung")[0])
        if verzoegerung == "flurab_probst":
            flurab = _return_con_hru(hrus, "flurab")[0]
            assert isinstance(flurab, float)
            con.schwerpunktlaufzeit(flurab_probst=flurab)
        else:
            try:
                verzoegerung_flt = float(verzoegerung.replace(",", "."))
            except ValueError:
                raise ValueError(
                    "'verzoegerung' muss den Datentyp float enthalten "
                    "oder die Option 'flurab_probst"
                ) from None
            con.schwerpunktlaufzeit(verzoegerung_flt)

        whmod.sequences.states.interzeptionsspeicher(0.0)
        whmod.sequences.states.schneespeicher(0.0)
        whmod.sequences.states.aktbodenwassergehalt(
            _return_con_hru(hrus, "init_boden")[0]
        )
        init_gwn = _return_con_hru(hrus, "init_gwn")[0]
        assert isinstance(init_gwn, float)
        init_zwischenspeicher = _init_gwn_to_zwischenspeicher(
            init_gwn=init_gwn, time_of_concentration=con.schwerpunktlaufzeit.value
        )
        whmod.sequences.states.zwischenspeicher(init_zwischenspeicher)


def _initialize_weather_stations(
    df_stammdaten: pandas.DataFrame,
    richter: bool,
    cssr_selection_stat: hydpy.Selection,
    gsr_selection_stat: hydpy.Selection,
    meteo_selection_stat: hydpy.Selection,
    evap_selection_stat: hydpy.Selection,
    temp_selection_stat: hydpy.Selection,
    prec_selection_stat: hydpy.Selection,
    filename_timeseries: str,
    basedir: str,
    node2xy: Dict[hydpy.Node, _XY],
) -> None:
    """In this function, the data from the weather stations is integrated in the
    temperature- and precipitation-nodes, as well as the meteo- and evap-elements.  The
    arguments of this function are HydPy-selections, which contain the respective nodes
     and elements, and the Node_Data.csv (as a Pandas DataFrame "df_stammdaten").
    Furthermore, the locations of the basedircetory (basedir) and the folder with the
    timeseries (filename_timeseries) are required.
    """
    from hydpy import inputs, outputs  # pylint: disable=import-outside-toplevel

    # Initialization Meteo-Elements, Evap-Elements, Temp-Nodes
    # Fused Variables
    cssr = devicetools.FusedVariable(
        "CSSR", outputs.meteo_ClearSkySolarRadiation, inputs.evap_ClearSkySolarRadiation
    )
    gsr = devicetools.FusedVariable(
        "GSR", outputs.meteo_GlobalRadiation, inputs.evap_GlobalRadiation
    )

    timeseries_path = os.path.join(
        basedir,
        filename_timeseries,
    )
    if richter:
        # Interpolate temperature for richter correction:
        niederschlag_temperature_nodes = _conv_models_temperature(
            stammdaten_in=df_stammdaten, timeseries_path=timeseries_path
        )

    # Iteration over Weather Stations
    for stat in df_stammdaten["StationsNr"].unique():
        # Stationsdaten einladen
        stations_daten = df_stammdaten[df_stammdaten["StationsNr"] == stat]

        index = stations_daten.index[0]

        xy = _XY(
            rechts=float(df_stammdaten.loc[index, "X"]),
            hoch=float(df_stammdaten.loc[index, "Y"]),
        )
        lat = df_stammdaten.loc[index, "Lat"]
        long = df_stammdaten.loc[index, "Long"]

        # Load weather data if all data is available
        if len(stations_daten) == 6:
            seq_airtemperature = stations_daten["Dateiname"][
                stations_daten["Messungsart"] == "Lufttemperatur"
            ].values[0]
            seq_windspeed = stations_daten["Dateiname"][
                stations_daten["Messungsart"] == "Windgeschwindigkeit"
            ].values[0]
            seq_sunshineduration = stations_daten["Dateiname"][
                stations_daten["Messungsart"] == "Sonnenscheindauer"
            ].values[0]
            seq_atmosphericpressure = stations_daten["Dateiname"][
                stations_daten["Messungsart"] == "Luftdruck"
            ].values[0]
            seq_relativehumidity = stations_daten["Dateiname"][
                stations_daten["Messungsart"] == "Relative-Feuchte"
            ].values[0]
        else:
            # there is only precipitation data
            continue

        cssr_node = hydpy.Node(f"CSSR_{stat}", variable=cssr)
        gsr_node = hydpy.Node(f"GSR_{stat}", variable=gsr)
        cssr_selection_stat.nodes.add_device(cssr_node)
        gsr_selection_stat.nodes.add_device(gsr_node)

        evap_node = hydpy.Node(
            f"E_{stat}", variable=outputs.evap_MeanReferenceEvapotranspiration
        )
        node2xy[evap_node] = xy

        # Meteo-Elemente
        meteo_element = hydpy.Element(f"Meteo_{stat}", outputs=(cssr_node, gsr_node))
        meteo = hydpy.prepare_model("meteo_v001", "1d")
        meteo_element.model = meteo

        # Evap-Element
        evap_element = hydpy.Element(
            f"Evap_{stat}", inputs=(cssr_node, gsr_node), outputs=(evap_node)
        )
        evap = hydpy.prepare_model("evap_fao56", "1d")
        evap_element.model = evap

        con_evap = evap.parameters.control
        con_meteo = meteo.parameters.control

        # Control Meteo-Element
        con_meteo.latitude(lat)
        con_meteo.longitude(long)
        con_meteo.angstromconstant(0.25)
        con_meteo.angstromfactor(0.5)
        meteo.parameters.update()

        # Control Evap-Element
        con_evap.nmbhru(1)
        con_evap.hruarea(1.0)  # tatsächliche Fläche hier irrelevant
        con_evap.measuringheightwindspeed(10.0)
        con_evap.airtemperatureaddend(0.0)
        con_evap.evapotranspirationfactor(1.0)
        evap.parameters.update()

        evap_element.model.sequences.logs.loggedglobalradiation(0.0)
        evap_element.model.sequences.logs.loggedclearskysolarradiation(0.0)

        inp_meteo = meteo.sequences.inputs
        inp_evap = evap.sequences.inputs

        inp_meteo.prepare_series()
        inp_evap.prepare_series()

        inp_meteo.sunshineduration.filepath = os.path.join(
            timeseries_path,
            seq_sunshineduration,
        )
        inp_meteo.sunshineduration.load_series()
        del inp_meteo.sunshineduration.filepath

        inp_evap.airtemperature.filepath = os.path.join(
            timeseries_path, seq_airtemperature
        )
        inp_evap.airtemperature.load_series()

        inp_evap.relativehumidity.filepath = os.path.join(
            timeseries_path,
            seq_relativehumidity,
        )
        inp_evap.relativehumidity.load_series()
        del inp_evap.relativehumidity.filepath

        inp_evap.windspeed.filepath = os.path.join(timeseries_path, seq_windspeed)
        inp_evap.windspeed.load_series()
        del inp_evap.windspeed.filepath

        inp_evap.atmosphericpressure.filepath = os.path.join(
            timeseries_path,
            seq_atmosphericpressure,
        )
        inp_evap.atmosphericpressure.load_series()
        del inp_evap.atmosphericpressure.filepath

        # Initialization of Temperature-Nodes
        t_node = hydpy.Node(f"T_{stat}", variable="T")
        t_node.deploymode = "obs"
        t_node.prepare_obsseries()
        t_node.sequences.obs.series = inp_evap.airtemperature.series
        node2xy[t_node] = xy

        # add meteo-elements, evap-elements, evap-nodes to selections
        meteo_selection_stat.elements.add_device(meteo_element)
        evap_selection_stat.nodes.add_device(evap_node)
        evap_selection_stat.elements.add_device(evap_element)
        temp_selection_stat.nodes.add_device(t_node)

    # Initialization Precipitation-Nodes
    for stat in df_stammdaten["StationsNr"].unique():
        # Load weather station data
        stations_daten = df_stammdaten[df_stammdaten["StationsNr"] == stat]

        index = stations_daten.index[0]

        niederschlag_station = stations_daten[
            stations_daten["Messungsart"] == "Niederschlag"
        ].squeeze()

        seq_precipitation = niederschlag_station["Dateiname"]

        p_node = hydpy.Node(f"P_{stat}", variable="P")
        p_node.deploymode = "obs"
        prec_selection_stat.nodes.add_device(p_node)
        node2xy[p_node] = _XY(
            rechts=df_stammdaten.loc[index, "X"], hoch=df_stammdaten.loc[index, "Y"]
        )
        p_node.prepare_obsseries()
        p_node.sequences.obs.filepath = os.path.join(timeseries_path, seq_precipitation)
        p_node.sequences.obs.load_series()
        if richter:
            temperature_node = niederschlag_temperature_nodes[f"Tinterp_{stat}"]
            apply_richter(
                richterklasse=niederschlag_station["Richterklasse"],
                temperature_node=temperature_node,
                precipitation_node=p_node,
            )

        del p_node.sequences.obs.filepath


def apply_richter(
    richterklasse: Literal[
        "frei", "leicht_geschuetzt", "maessig_geschuetzt", "stark_geschuetzt"
    ],
    temperature_node: hydpy.Node,
    precipitation_node: hydpy.Node,
) -> None:
    """
    Führe die Richterkorrektur durch
    >>> hydpy.pub.timegrids = "2000-09-25", "2000-10-05", "1d"
    >>> p = hydpy.Node("p")
    >>> p.prepare_obsseries()
    >>> p.sequences.obs.series = [0., 2., 1., 5., 1., 1., 1., 3., 1., 0.5]
    >>> t = hydpy.Node("t")
    >>> t.prepare_simseries()
    >>> t.sequences.sim.series = [-1., -2., 3., 0., 5., 5., 5., -3., 5., 0.5]
    >>> apply_richter(temperature_node=t, precipitation_node=p, richterklasse="frei")
    >>> p.sequences.sim.series
    InfoArray([0.        , 3.27109231, 1.345     , 6.29654407, 1.345     ,
               1.345     , 1.34      , 4.77244156, 1.34      , 0.86541577])
    >>> apply_richter(temperature_node=t, precipitation_node=p,
    ...     richterklasse="maessig_geschuetzt")
    >>> p.sequences.sim.series
    InfoArray([0.        , 2.58258398, 1.28      , 5.73915129, 1.28      ,
               1.28      , 1.24      , 3.81236905, 1.24      , 0.70832114])
    >>> apply_richter(temperature_node=t, precipitation_node=p,
    ...     richterklasse="maessig_geschuetzt")
    >>> p.sequences.sim.series
    InfoArray([0.        , 2.58258398, 1.28      , 5.73915129, 1.28      ,
               1.28      , 1.24      , 3.81236905, 1.24      , 0.70832114])
    >>> apply_richter(temperature_node=t, precipitation_node=p,
    ...     richterklasse="stark_geschuetzt")
    >>> p.sequences.sim.series
    InfoArray([0.        , 2.37073526, 1.245     , 5.44833767, 1.245     ,
               1.245     , 1.19      , 3.51696212, 1.19      , 0.62635872])
    >>> apply_richter(temperature_node=t, precipitation_node=p,
    ...     richterklasse="wald")
    Traceback (most recent call last):
    ...
    KeyError: 'wald'
    """

    precipitation_node.prepare_simseries()
    precipitation_node.deploymode = "oldsim"
    ns_art = get_ns_art(temperature_node=temperature_node)
    precipitation_node.sequences.sim.series = calc_richter(
        ns_art=ns_art,
        precipitation=precipitation_node.sequences.obs.series,
        richterklasse=richterklasse,
    )


def get_ns_art(temperature_node: hydpy.Node) -> numpy.typing.NDArray[numpy.character]:
    """
    Bestimme ob Niederschlag als Sommerregen, Winterregen, Mischniederschlag oder
    Schnee fällt
    >>> hydpy.pub.timegrids = "2000-09-25", "2000-10-05", "1d"
    >>> t = hydpy.Node("t")
    >>> t.prepare_simseries()
    >>> t.sequences.sim.series = [-1., -2., 3., 0., 5., 5., 5., -3., 5., 0.5]
    >>> get_ns_art(temperature_node=t)
    array(['Schnee', 'Schnee', 'Sommerregen', 'Mischniederschlag',
           'Sommerregen', 'Sommerregen', 'Winterregen', 'Schnee',
           'Winterregen', 'Mischniederschlag'], dtype='<U20')
    """
    t_node_ser = temperature_node.sequences.sim.series
    winter = numpy.array(
        [i.month > 9 or i.month < 5 for i in
         hydpy.pub.timegrids.init]
    )
    ns_art = numpy.empty(shape=t_node_ser.shape, dtype="<U20")
    ns_art[numpy.logical_and(t_node_ser >= 3, winter)] = "Winterregen"
    ns_art[numpy.logical_and(t_node_ser >= 3, ~winter)] = "Sommerregen"
    ns_art[(-0.7 < t_node_ser) & (t_node_ser < 3)] = "Mischniederschlag"
    ns_art[t_node_ser <= -0.7] = "Schnee"
    return ns_art


def _conv_models_temperature(
    stammdaten_in: pandas.DataFrame, timeseries_path: str
) -> hydpy.Nodes:
    """
    Interpolate temperature data for Richter-correction.
    """
    temperature_in = stammdaten_in[stammdaten_in["Messungsart"] == "Lufttemperatur"]
    temperature_out = stammdaten_in[stammdaten_in["Messungsart"] == "Niederschlag"]

    hp_temperature = hydpy.HydPy("temperature")
    in_coords_dict: Dict[str, Tuple[float, float]] = {}
    out_coords_dict: Dict[str, Tuple[float, float]] = {}
    e = hydpy.Element("conv_temperature_richter")

    inlet_nodes = hydpy.Nodes()
    outlet_nodes = hydpy.Nodes()
    for _, input_station in temperature_in.iterrows():
        name = "Tin_" + str(input_station["StationsNr"])
        n = hydpy.Node(name)
        n.deploymode = "obs"
        n.sequences.obs.prepare_series()
        n.sequences.obs.filepath = os.path.join(
            timeseries_path, input_station["Dateiname"]
        )
        n.sequences.obs.load_series()
        inlet_nodes.add_device(n)
        # Coordinates
        in_coords_dict[n.name] = _XY(rechts=input_station["X"], hoch=input_station["Y"])
    for _, output_station in temperature_out.iterrows():
        n = hydpy.Node("Tinterp_" + str(output_station["StationsNr"]))
        n.deploymode = "newsim"
        n.sequences.sim.prepare_series()
        outlet_nodes.add_device(n)
        # Coordinates
        out_coords_dict[n.name] = _XY(
            rechts=output_station["X"], hoch=output_station["Y"]
        )

    e.inlets = inlet_nodes
    e.outlets = outlet_nodes
    model_t = hydpy.prepare_model("conv_v002")
    model_t.parameters.control.inputcoordinates(**in_coords_dict)
    model_t.parameters.control.outputcoordinates(**out_coords_dict)
    model_t.parameters.control.maxnmbinputs()
    model_t.parameters.control.power(2.0)
    e.model = model_t
    e.model.parameters.update()

    hp_temperature.update_devices(nodes=outlet_nodes + inlet_nodes, elements=e)
    hp_temperature.simulate()

    return outlet_nodes


def _initialize_conv_models(
    evap_selection_stat: hydpy.Selection,
    evap_selection_raster: hydpy.Selection,
    temp_selection_stat: hydpy.Selection,
    temp_selection_raster: hydpy.Selection,
    prec_selection_stat: hydpy.Selection,
    prec_selection_raster: hydpy.Selection,
    node2xy: Dict[hydpy.Node, _XY],
) -> None:
    """The conv models are based on the selections of the input data of the weather
    stations (evapselection_stat, tempselection_stat, precselection_stat) and their
    rasterized counterpart (evapselection_raster, tempselection_raster,
    precselection_raster).
    """
    # Initialization Conv-Modelle
    def _get_coordinatedict(nodes: hydpy.Nodes) -> Dict[str, _XY]:
        """Returns a Dictionary with x and y values. Used for Conv-models."""
        return {n.name: node2xy[n] for n in nodes}

    # Conv-Modell PET
    conv_pet = hydpy.prepare_model("conv_v002")
    conv_pet.parameters.control.inputcoordinates(
        **_get_coordinatedict(evap_selection_stat.nodes)
    )
    conv_pet.parameters.control.outputcoordinates(
        **_get_coordinatedict(evap_selection_raster.nodes)
    )
    conv_pet.parameters.control.maxnmbinputs()
    conv_pet.parameters.control.power(2.0)
    element = hydpy.Element(
        "ConvPET", inlets=evap_selection_stat.nodes, outlets=evap_selection_raster.nodes
    )
    element.model = conv_pet
    evap_selection_stat.elements.add_device(element)

    # Conv-Modell Temperature
    conv_temp = hydpy.prepare_model("conv_v002")
    conv_temp.parameters.control.inputcoordinates(
        **_get_coordinatedict(temp_selection_stat.nodes)
    )
    conv_temp.parameters.control.outputcoordinates(
        **_get_coordinatedict(temp_selection_raster.nodes)
    )
    conv_temp.parameters.control.maxnmbinputs()
    conv_temp.parameters.control.power(2.0)

    element = hydpy.Element(
        "ConvTemp",
        inlets=temp_selection_stat.nodes,
        outlets=temp_selection_raster.nodes,
    )
    element.model = conv_temp
    temp_selection_stat.elements.add_device(element)

    conv_prec = hydpy.prepare_model("conv_v002")
    conv_prec.parameters.control.inputcoordinates(
        **_get_coordinatedict(prec_selection_stat.nodes)
    )
    conv_prec.parameters.control.outputcoordinates(
        **_get_coordinatedict(prec_selection_raster.nodes)
    )
    conv_prec.parameters.control.maxnmbinputs()
    conv_prec.parameters.control.power(2.0)
    element = hydpy.Element(
        "ConvPrec",
        inlets=prec_selection_stat.nodes,
        outlets=prec_selection_raster.nodes,
    )
    element.model = conv_prec
    prec_selection_stat.elements.add_device(element)


def write_rch_file(
    filepath: str,
    data: xarray.DataArray,
    step: str,
    person_in_charge: str,
    precision: int = 4,
    layer: int = 1,
    balancefile: int = 51,
    values_per_line: int = 20,
    exp_digits: int = 3,
) -> None:
    """
    Writes rch file
    """
    nchars = precision + exp_digits + 5
    formatstring = f"({values_per_line}e{nchars}.{precision})".ljust(20)
    ncols = len(data.col)
    sections = numpy.arange(values_per_line, ncols, values_per_line)
    nchars = precision + exp_digits + 5
    name, unit = str(data.name).split("_")
    with open(filepath, "w", encoding="utf-8") as rchfile:
        rchfile.write(
            f"# {person_in_charge}, {datetime.datetime.now()}\n"
            f"# {step} WHMod-{name} in {unit}\n"
            f"# {step} values from "
            f"{numpy.datetime_as_string(data.time[0].values)[:13]} to "
            f"{numpy.datetime_as_string(data.time[-1].values)[:13]}\n"
            f"##########################################################\n"
        )
        rchfile.write(
            f"{str(layer).rjust(10)}"
            f"{str(balancefile).rjust(10)}"
            f"         1         1\n"
        )
        for time_i in data.time:
            rchfile.write(
                f"         1         1         0         0\n"
                f"        18     1.000{formatstring}        -1     RECHARGE\n"
            )
            for row in data.row:
                row_timestep = data.sel(time=time_i, row=row)
                for subarray in numpy.array_split(row_timestep, sections):
                    rchfile.write(
                        "".join(
                            numpy.format_float_scientific(
                                value,
                                unique=False,
                                precision=precision,
                                exp_digits=exp_digits,
                            ).rjust(nchars)
                            for value in subarray
                        )
                    )
                    rchfile.write("\n")


def write_mean_file(
    filepath: str,
    data: xarray.DataArray,
    df_knoteneigenschaften: pandas.DataFrame,
    nodata_value: str,
    cellsize: float,
) -> None:
    """
    Writes file with means
    """
    with open(filepath, "w", encoding="utf-8") as gridfile:
        gridfile.write(
            f"ncols         {data.shape[1]}\n"
            f"nrows         {data.shape[0]}\n"
            f"xllcorner     {df_knoteneigenschaften['x'].min()}\n"
            f"yllcorner     {df_knoteneigenschaften['y'].min()}\n"
            f"cellsize      {cellsize}\n"
            f"nodata_value  {nodata_value}\n"
        )
        meandata = data.mean(dim="time").values

        numpy.savetxt(gridfile, meandata, delimiter=" ")


def write_time_series(
    filepath: str, data: xarray.DataArray, person_in_charge: str, step: str
) -> None:
    """
    Writes spatially aggregated timeseries
    """
    spatial_sum = data.mean(dim=("row", "col")).to_dataframe()
    # todo: Länge Start und Enddatum
    name, unit = str(data.name).split("_")
    with open(filepath, "w", encoding="utf-8", newline="\n") as seriesfile:
        seriesfile.write(
            f"# {person_in_charge}, {datetime.datetime.now()}\n"
            f"# {step} WHMod-{name} in {unit}\n"
            f"# {step} values from "
            f"{numpy.datetime_as_string(data.time[0].values)[:13]} to "
            f"{numpy.datetime_as_string(data.time[-1].values)[:13]}\n"
            f"##########################################################\n"
        )
        spatial_sum.to_csv(path_or_buf=seriesfile, sep=" ", header=False)


def inplace_change(filename: str, old_string: str, new_string: str) -> None:
    """
    Replaces strings inplace in a file
    """
    # Safely read the input filename using 'with'
    with open(filename, encoding="utf-8") as f:
        s = f.read()

    # Safely write the changed content, if found in the file
    with open(filename, "w", encoding="utf-8") as f:
        s = s.replace(old_string, new_string)
        f.write(s)


def save_results(
    aggregated_series: Dict[str, Dict[Literal["mean", "sum"], xarray.DataArray]],
    loggers: List[Dict[str, List[Union[str, pandas.DatetimeIndex]]]],
    outputdir: str,
    df_knoteneigenschaften: pandas.DataFrame,
    cellsize: float,
    person_in_charge: str,
    nodata_value: str,
) -> None:
    """
    Save results to specified format
    """
    for logger in loggers:
        for i, (step, seq) in enumerate(product(logger["steps"], logger["sequence"])):
            if isinstance(step, pandas.DatetimeIndex):
                name = str(i) + "_" + "userdefined" + "_" + seq
            else:
                name = str(i) + "_" + step + "_" + seq
            grid = aggregated_series[name]
            output = False
            if "name_rch_file" in logger.keys():
                for filename in logger["name_rch_file"]:
                    filepath = os.path.join(outputdir, filename + "_" + seq + ".rch")
                    data = prepare_rch(grid=grid, seq=seq)
                    write_rch_file(
                        filepath=filepath,
                        data=data,
                        step=step,
                        person_in_charge=person_in_charge,
                    )
                    inplace_change(
                        filename=filepath, old_string="nan", new_string=nodata_value
                    )
                    output = True

            if "name_time_series" in logger.keys():
                for filename in logger["name_time_series"]:
                    filepath = os.path.join(outputdir, filename + "_" + seq + ".txt")
                    if str(grid["mean"].name).split("_")[1] == "mm":
                        data = grid["sum"]
                    else:
                        data = grid["mean"]
                    write_time_series(
                        filepath=filepath,
                        data=data,
                        step=step,
                        person_in_charge=person_in_charge,
                    )
                    inplace_change(
                        filename=filepath, old_string="nan", new_string=nodata_value
                    )
                    output = True
            if "name_mean_file" in logger.keys():
                for filename in logger["name_mean_file"]:
                    filepath = os.path.join(outputdir, filename + "_" + seq + ".txt")
                    write_mean_file(
                        filepath=filepath,
                        data=grid["mean"],
                        cellsize=cellsize,
                        nodata_value=nodata_value,
                        df_knoteneigenschaften=df_knoteneigenschaften,
                    )
                    inplace_change(
                        filename=filepath, old_string="nan", new_string=nodata_value
                    )
                    output = True
            if not output:
                raise ValueError("The outputfiles have to be ...")


def prepare_rch(
    grid: Dict[Union[Literal["mean"], Literal["sum"]], xarray.DataArray], seq: str
) -> xarray.DataArray:
    """
    Konvertiere Einheiten entsprechend Anforderungen.
    """
    if seq in ("AktGrundwasserneubildung", "VerzGrundwasserneubildung"):
        # factor to convert from mm to m/s
        data = grid["mean"].copy()
        assert "_mm" in str(data.name)
        factor = 1.0 / (1000.0 * hydpy.pub.timegrids.stepsize.seconds)
        data.name = str(data.name).replace("_mm", "_m/s")
    else:
        data = grid["sum"].copy()
        factor = 1.0
    data *= factor
    return data


def aggregate_whmod_series(
    loggers: List[Dict[str, List[Union[str, pandas.DatetimeIndex]]]], seriesdir: str
) -> Dict[str, Dict[Literal["sum", "mean"], xarray.DataArray]]:
    """
    >>> from hydpy import TestIO
    >>> TestIO.clear()
    >>> basedir = TestIO.copy_dir_from_data_to_iotesting("WHMod")
    >>> logger = read_outputconfig(outputconfigfile="Tageswerte.txt", basedir=basedir)
    """
    hydpy.pub.sequencemanager.currentdir = seriesdir
    whm_elements = (
        hydpy.pub.selections["complete"].search_modeltypes("whmod_pet").elements
    )
    all_series: List[str] = []
    elementnames = (e.name for e in whm_elements)
    pb = Positionbounds.from_elementnames(elementnames=elementnames)
    raster_shape = (pb.rowmax - pb.rowmin + 1, pb.colmax - pb.colmin + 1)
    aggregated_series: Dict[str, Dict[Literal["sum", "mean"], xarray.DataArray]] = {}
    for logger in loggers:
        for i, (step, seq) in enumerate(product(logger["steps"], logger["sequence"])):
            unit = getattr(hydpy.models.whmod.whmod_fluxes, seq).unit
            if isinstance(step, pandas.DatetimeIndex):
                name = str(i) + "_" + "userdefined" + "_" + seq
                timeseries_index = step[:-1]
            else:
                name = str(i) + "_" + step + "_" + seq
                timeseries_index = hydpy.aggregate_series(
                    series=numpy.ones(len(hydpy.pub.timegrids.init)), stepsize=step
                ).index
            aggregated_series[name] = {}
            agg_grid_shape = raster_shape + (len(timeseries_index),)
            grid = numpy.full(agg_grid_shape, numpy.nan, dtype=float)
            xarr_mean = xarray.DataArray(
                name=seq + "_" + unit,
                data=grid,
                dims=["row", "col", "time"],
                coords={"time": timeseries_index},
            )
            xarr_sum = xarr_mean.copy()
            with hydpy.pub.sequencemanager.netcdfreading():
                for element in whm_elements:
                    sequence = getattr(element.model.sequences.fluxes, seq.lower())
                    if not sequence.ramflag:
                        sequence.prepare_series(allocate_ram=True)
                        sequence.load_series()
            sum_agg_ser = 0
            for element in whm_elements:
                sequence = getattr(element.model.sequences.fluxes, seq.lower())
                sim_series = sequence.average_series()
                row, col = Position.from_elementname(element.name)
                if isinstance(step, pandas.DatetimeIndex):
                    agg_ser_mean = aggregate_flexible_series(
                        series=sim_series,
                        aggregation_timegrid=step,
                        aggregator="mean",
                    ).values
                    agg_ser_sum = aggregate_flexible_series(
                        series=sim_series,
                        aggregation_timegrid=step,
                        aggregator="sum",
                    ).values
                else:
                    agg_ser_sum = hydpy.aggregate_series(
                        series=sim_series, stepsize=step, aggregator="sum"
                    ).values
                    agg_ser_mean = hydpy.aggregate_series(
                        series=sim_series, stepsize=step, aggregator="mean"
                    ).values
                sum_agg_ser += numpy.mean(sim_series)
                xarr_sum.loc[{"row": row - 1, "col": col - 1}] = agg_ser_sum
                xarr_mean.loc[{"row": row - 1, "col": col - 1}] = agg_ser_mean
                sequence.prepare_series(allocate_ram=False)
            if seq not in all_series:
                print(
                    f"Mean {seq} [{unit}/a]: "
                    f"{sum_agg_ser / len(whm_elements) * 365.24}"
                )
                all_series.append(seq)
            aggregated_series[name] = {}
            aggregated_series[name]["sum"] = xarr_sum
            aggregated_series[name]["mean"] = xarr_mean
    return aggregated_series


def is_date(string: str) -> bool:
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    """
    try:
        parse(string, fuzzy=False)
        return True

    except ValueError:
        return False


def aggregate_flexible_series(
    series: numpy.typing.NDArray[numpy.float_],
    aggregation_timegrid: pandas.DatetimeIndex,
    aggregator: Union[Literal["mean"], Literal["sum"]] = "mean",
) -> pandas.Series:
    """
    Aggregiere Zeitreihen auf vordefineirtes Grid:
    >>> from hydpy import pub, Node
    >>> import pandas
    >>> import numpy
    >>> pub.timegrids = '2011-01-01', '2011-01-10', '1d'
    >>> node = Node("test")
    >>> node.prepare_simseries()
    >>> sim = node.sequences.sim
    >>> sim.series = numpy.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
    >>> agg_timegrid = pandas.DatetimeIndex(['2011-01-01', "2011-01-02", "2011-01-08"])
    >>> aggregate_flexible_series(series=sim.series, aggregation_timegrid=agg_timegrid)
    2011-01-01    1.0
    2011-01-02    4.5
    Name: series, dtype: float64
    >>> aggregate_flexible_series(series=sim.series, aggregation_timegrid=agg_timegrid,
    ...     aggregator="sum")
    2011-01-01     1.0
    2011-01-02    27.0
    Name: series, dtype: float64
    >>> aggregate_flexible_series(series=sim.series, aggregation_timegrid=agg_timegrid,
    ...     aggregator="std")
    Traceback (most recent call last):
    ...
    ValueError: Aggregator `std` not defined

    >>> agg_timegrid = pandas.DatetimeIndex(['2001-01-01', "2011-01-02", "2011-01-08"])
    >>> aggregate_flexible_series(series=sim.series, aggregation_timegrid=agg_timegrid,
    ...     aggregator="mean")
    Traceback (most recent call last):
    ...
    ValueError: Aggregation timegrid DatetimeIndex(['2001-01-01', '2011-01-02', \
'2011-01-08'], dtype='datetime64[ns]', freq=None) outside data timegrid.
    >>> agg_timegrid = pandas.DatetimeIndex(['2001-01-02', "2011-01-01", "2011-01-08"])
    >>> aggregate_flexible_series(series=sim.series, aggregation_timegrid=agg_timegrid,
    ...     aggregator="mean")
    Traceback (most recent call last):
    ...
    ValueError: Aggregation timegrid DatetimeIndex(['2001-01-02', '2011-01-01', \
'2011-01-08'], dtype='datetime64[ns]', freq=None) outside data timegrid.
    """
    if any(sorted(aggregation_timegrid) != aggregation_timegrid):
        raise AssertionError(
            "Output timesteps of user defined output have to be sorted"
        )
    if (
        aggregation_timegrid[0] < hydpy.pub.timegrids.eval_.firstdate
        or aggregation_timegrid[0] > hydpy.pub.timegrids.eval_.lastdate
    ):
        raise ValueError(
            f"Aggregation timegrid {aggregation_timegrid} outside data " f"timegrid."
        )

    ps = pandas.Series(name="series", index=aggregation_timegrid[:-1], dtype=float)
    for i, time in enumerate(aggregation_timegrid):
        if i > 0:
            start: datetime.datetime = hydpy.pub.timegrids.eval_[start_time]
            end = hydpy.pub.timegrids.eval_[time]
            if aggregator == "sum":
                ps.loc[start_time] = series[start:end].sum()
            elif aggregator == "mean":
                ps.loc[start_time] = series[start:end].mean()
            else:
                raise ValueError(f"Aggregator `{aggregator}` not defined")
        start_time = time
    return ps


richter_factor_b = pandas.DataFrame(
    index=["Sommerregen", "Winterregen", "Mischniederschlag", "Schnee"],
    columns=["frei", "leicht_geschuetzt", "maessig_geschuetzt", "stark_geschuetzt"],
    data=[
        [0.345, 0.310, 0.280, 0.245],
        [0.340, 0.280, 0.240, 0.190],
        [0.535, 0.390, 0.305, 0.185],
        [0.720, 0.510, 0.330, 0.210],
    ],
)
richter_factor_epsilon = pandas.Series(
    index=["Sommerregen", "Winterregen", "Mischniederschlag", "Schnee"],
    data=[0.38, 0.46, 0.55, 0.82],
)


def get_richter_factors(
    richterklasse: Literal[
        "frei", "leicht_geschuetzt", "maessig_geschuetzt", "stark_geschuetzt"
    ],
    ns_art: Literal["Sommerregen", "Winterregen", "Mischniederschlag", "Schnee"],
) -> Tuple[float, float]:
    """
    Gibt den Richterkorrekturwert zurück

    >>> get_richter_factors(richterklasse="frei", ns_art="Sommerregen")
    (0.345, 0.38)
    >>> get_richter_factors(richterklasse="test", ns_art="Sommerregen")
    Traceback (most recent call last):
    ...
    KeyError: 'test'
    """
    b = richter_factor_b.loc[ns_art, richterklasse]
    epsilon = richter_factor_epsilon.loc[ns_art]
    return b, epsilon


def calc_richter(
    ns_art: numpy.typing.NDArray[numpy.character],
    richterklasse: Literal[
        "frei", "leicht_geschuetzt", "maessig_geschuetzt", "stark_geschuetzt"
    ],
    precipitation: numpy.typing.NDArray[numpy.float64],
) -> List[float]:
    """
    Gibt nach Richter korrigiergte Zeitreihe zurück

    >>> ns_art = numpy.array(["Sommerregen", "Winterregen", "Mischniederschlag",
    ...                       "Schnee"])
    >>> precipitation = numpy.array([0., 2., 1., 3.])
    >>> calc_richter(ns_art=ns_art, precipitation=precipitation, richterklasse="frei")
    [0.0, 2.4676842181675127, 1.5350000000000001, 4.772441562190775]
    """
    corr_precipitation = []
    for art, p in zip(ns_art, precipitation):
        b, epsilon = get_richter_factors(ns_art=art, richterklasse=richterklasse)
        p_corr = p + b * p**epsilon
        corr_precipitation.append(p_corr)
    return corr_precipitation
