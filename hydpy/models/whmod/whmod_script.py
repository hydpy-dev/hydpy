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

import numpy
import pandas

import hydpy
from hydpy.core import devicetools
from hydpy.core import logtools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.exe import commandtools
from hydpy.models import whmod_pet
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_model
from hydpy.core.typingtools import *

# from hydpy import inputs  # actual imports below
# from hydpy import outputs  # actual imports below


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
    """
    result: Dict[str, Dict[str, object]] = {}
    hrus = table[table["id"] == idx_]
    extended_hrus = pandas.DataFrame(columns=hrus.columns)
    n_hrus = 0
    for i, hru in hrus.iterrows():
        for landuse, area_perc in landuse_dict[hru["nutz_nr"]].items():
            extended_hrus.loc[n_hrus] = hrus.loc[i].copy()
            extended_hrus.loc[n_hrus, "nutz_nr"] = landuse.upper()
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


def run_whmod(basedir: str, write_output: str) -> None:
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
    Mean GWN [mm/a]: 38.974463878806326
    Mean verz. GWN [mm/a]: 36.916119888336866

    >>> run_whmod(basedir=projectpath, write_output=True) # doctest: +ELLIPSIS
    Start WHMOD calculations (...).
    Initialize WHMOD (...).
    method simulate started at ...
        |---------------------|
        ***********************
        seconds elapsed: ...
    Write Output in ...\WHMod\Results (...).
    Mean GWN [mm/a]: 38.974463878806326
    Mean verz. GWN [mm/a]: 36.916119888336866

    You can also run the script from the command prompt with hyd.py:

    >>> _ = run_subprocess(f"hyd.py run_whmod {projectpath} False")
    Mean GWN [mm/a]: 38.974463878806326
    Mean verz. GWN [mm/a]: 36.916119888336866

    >>> with open(os.path.join(projectpath, "Results",
    ... "Groundwater_Recharge_1990-1992.txt"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    # Max Mustermann, ...
    # Monthly WHMod-Groundwater Recharge in mm
    # Monthly values from 1990-01-01 to 1992-01-01
    ##########################################################
    1990-01	0.3123535222629805
    1990-02	11.26990972195137
    1990-03	1.202722479827292
    1990-04	1.6153368961041545
    1990-05	-1.966510855767592
    1990-06	-0.7622536716921774
    1990-07	-1.482467549347431
    1990-08	-2.7902887575098454
    1990-09	1.1584295976408858
    1990-10	1.8341058769334753
    1990-11	15.30160514900505
    1990-12	16.083881574719623
    1991-01	12.867846494514447
    1991-02	5.596682579465355
    1991-03	4.404740610210456
    1991-04	0.3109043749421045
    1991-05	-0.7420669814995602
    1991-06	0.5799537654768397
    1991-07	-1.707045080537081
    1991-08	-2.807612545031555
    1991-09	-2.0378062382157776
    1991-10	1.0124938321292507
    1991-11	7.57714758711962
    1991-12	11.065644964600226

    >>> with open(os.path.join(projectpath, "Results",
    ... "Groundwater_Recharge_Verz_1990-1992.txt"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    # Max Mustermann, ...
    # Monthly WHMod-Groundwater Recharge in mm
    # Monthly values from 1990-01-01 to 1992-01-01
    ##########################################################
    1990-01	0.5045038812540086
    1990-02	5.250603291729102
    1990-03	6.4497203320862395
    1990-04	1.7912861345033646
    1990-05	-0.6268182705790565
    1990-06	-1.2685268478426805
    1990-07	-0.6807497284977176
    1990-08	-2.782809513177545
    1990-09	0.00455351862727867
    1990-10	1.0133223565827008
    1990-11	10.543526380157056
    1990-12	12.408252255341312
    1991-01	17.41453327524282
    1991-02	5.238857183865606
    1991-03	6.298480526672588
    1991-04	1.705189692982093
    1991-05	0.5847423425736368
    1991-06	0.01631629765354097
    1991-07	-0.3823595659513151
    1991-08	-2.097171803288229
    1991-09	-2.5505616288699913
    1991-10	0.7403114329158353
    1991-11	5.877001644492123
    1991-12	8.331521262534562

    >>> with open(os.path.join(projectpath, "Results",
    ... "Sum_Verz_Groundwater_Recharge_1990-1992.txt"), 'r') as file:
    ...     print(file.read())  # doctest: +NORMALIZE_WHITESPACE
    ncols         3
    nrows         4
    xllcorner     3455523.97
    yllcorner     5567507.03
    cellsize      100
    nodata_value  -9999.0
    31.645292796869786 81.48036442990723 23.44272208840597
    40.700753395675605 49.292163415765636 -103.99671214064254
    28.282173000284654 19.35690518826799 66.62374633575931
    87.69237800071348 73.3194305226362 45.154221626399156
    """
    write_output_ = print_hydpy_progress(write_output=write_output)

    whmod_main = read_whmod_main(basedir)

    person_in_charge = whmod_main["PERSON_IN_CHARGE"][1].strip()
    hydpy_version = whmod_main["HYDPY_VERSION"][1].strip()

    check_hydpy_version(hydpy_version=hydpy_version)

    outputdir = os.path.join(basedir, whmod_main["OUTPUTDIR"][1].strip())
    outputmode = [mode.strip() for mode in whmod_main["OUTPUTMODE"][1].split(",")]
    filename_node_data = whmod_main["FILENAME_NODE_DATA"][1].strip()
    filename_timeseries = whmod_main["FILENAME_TIMESERIES"][1].strip()
    filename_station_data = whmod_main["FILENAME_STATION_DATA"][1].strip()
    filename_landuse = whmod_main["FILENAME_LANDUSE"][1].strip()
    with_capillary_rise = whmod_main["WITH_CAPPILARY_RISE"][1]
    day_degree_factor = whmod_main["DEGREE_DAY_FACTOR"][1]
    root_depth_option = whmod_main["ROOT_DEPTH_OPTION"][1].strip()
    simulation_start = whmod_main["SIMULATION_START"][1]
    simulation_end = whmod_main["SIMULATION_END"][1]
    frequence = whmod_main["FREQUENCE"][1]
    cellsize = whmod_main["CELLSIZE"][1]
    nodata_value = whmod_main["NODATA_VALUE"][1]

    hydpy.pub.timegrids = simulation_start, simulation_end, frequence
    hydpy.pub.options.parameterstep = frequence
    hydpy.pub.options.checkseries = False

    df_knoteneigenschaften = read_nodeproperties(
        basedir=basedir, filename_node_data=filename_node_data
    )
    filepath_landuse = os.path.join(basedir, filename_landuse)

    landuse_dict = read_landuse(filepath_landuse=filepath_landuse)

    df_stammdaten = pandas.read_csv(
        os.path.join(basedir, filename_station_data), comment="#", sep="\t"
    )
    df_stammdaten["Messungsart"] = df_stammdaten["Dateiname"].apply(
        lambda a: a.split("_")[1].split(".")[0]
    )
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

    # define two loggers, one for the actual groundwater recharge, one for the delayed
    # groundwater recharge (verz)
    hp.loggers["logger_akt"] = logtools.Logger(simulation_start, simulation_end)
    hp.loggers["logger_verz"] = logtools.Logger(simulation_start, simulation_end)

    # same for the month logger
    if "txt" in outputmode or "rch" in outputmode:
        hp.loggers["month_logger_akt"] = whmod_model.WHModMonthLogger()
        hp.loggers["month_logger_verz"] = whmod_model.WHModMonthLogger()

    # add the fluxes to the respective logger
    for element in hp.elements:
        if element.name.startswith("WHMod"):
            hp.loggers["logger_akt"].add_sequence(
                element.model.sequences.fluxes.aktgrundwasserneubildung
            )
            hp.loggers["month_logger_akt"].add_sequence(
                element.model.sequences.fluxes.aktgrundwasserneubildung
            )
            hp.loggers["logger_verz"].add_sequence(
                element.model.sequences.fluxes.verzgrundwasserneubildung
            )
            hp.loggers["month_logger_verz"].add_sequence(
                element.model.sequences.fluxes.verzgrundwasserneubildung
            )

    hp.simulate()

    hydpy.pub.sequencemanager.overwrite = True
    hydpy.pub.sequencemanager.currentdir = outputdir

    ncol = df_knoteneigenschaften["col"].max()
    nrow = df_knoteneigenschaften["row"].max()
    xllcorner = df_knoteneigenschaften["x"].min()
    yllcorner = df_knoteneigenschaften["y"].min()

    _save_results(
        write_output=write_output_,
        outputdir=outputdir,
        outputmode=outputmode,
        nrow=nrow,
        ncol=ncol,
        hp=hp,
        cellsize=cellsize,
        simulation_start=simulation_start,
        simulation_end=simulation_end,
        xllcorner=xllcorner,
        yllcorner=yllcorner,
        nodata_value=nodata_value,
        person_in_charge=person_in_charge,
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


def print_hydpy_progress(write_output: str) -> bool:
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
    """Read the whmod main file."""
    dtype_whmod_main = {
        "PERSON_IN_CHARGE": str,
        "HYDPY_VERSION": str,
        "OUTPUTDIR": str,
        "OUTPUTMODE": str,
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
        except FileNotFoundError:
            raise ValueError(
                f"Der Wert für ROOT_DEPTH_OPTION ({root_depth_option}) ist "
                f"ungültig er muss entweder auf eine Datei verweisen oder den "
                f"Wert 'BK', 'WABOA', 'TGU' oder 'DARMSTADT' enthalten."
            )
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

    for idx in range(len(df_knoteneigenschaften["id"].unique())):

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
            basedir,
            filename_timeseries,
            seq_sunshineduration,
        )
        inp_meteo.sunshineduration.load_series()
        del inp_meteo.sunshineduration.filepath

        inp_evap.airtemperature.filepath = os.path.join(
            basedir, filename_timeseries, seq_airtemperature
        )
        inp_evap.airtemperature.load_series()

        inp_evap.relativehumidity.filepath = os.path.join(
            basedir,
            filename_timeseries,
            seq_relativehumidity,
        )
        inp_evap.relativehumidity.load_series()
        del inp_evap.relativehumidity.filepath

        inp_evap.windspeed.filepath = os.path.join(
            basedir, filename_timeseries, seq_windspeed
        )
        inp_evap.windspeed.load_series()
        del inp_evap.windspeed.filepath

        inp_evap.atmosphericpressure.filepath = os.path.join(
            basedir,
            filename_timeseries,
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

        seq_precipitation = stations_daten["Dateiname"][
            stations_daten["Messungsart"] == "Niederschlag"
        ].values[0]

        p_node = hydpy.Node(f"P_{stat}", variable="P")
        p_node.deploymode = "obs"
        prec_selection_stat.nodes.add_device(p_node)
        node2xy[p_node] = _XY(
            rechts=df_stammdaten.loc[index, "X"], hoch=df_stammdaten.loc[index, "Y"]
        )
        p_node.prepare_obsseries()
        p_node.sequences.obs.filepath = os.path.join(
            basedir, filename_timeseries, seq_precipitation
        )
        p_node.sequences.obs.load_series()
        del p_node.sequences.obs.filepath


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


def _save_results(
    write_output: bool,
    outputdir: str,
    outputmode: List[Union[Literal["rch"], Literal["txt"], Literal["sum_txt"]]],
    nrow: int,
    ncol: int,
    hp: hydpy.HydPy,
    cellsize: int,
    simulation_start: str,
    simulation_end: str,
    xllcorner: float,
    yllcorner: float,
    nodata_value: float,
    person_in_charge: str,
) -> None:
    def convert_values2string(values_: Sequence[float]) -> str:
        return " ".join(str(-9999.0 if v == -9999.0 else v * 365.24) for v in values_)

    period = f"{simulation_start[0:4]}-{simulation_end[0:4]}"

    if write_output:
        commandtools.print_textandtime(f"Write Output in {outputdir}")

    logger_akt = hp.loggers["logger_akt"]
    assert isinstance(logger_akt, logtools.Logger)
    logger_verz = hp.loggers["logger_verz"]
    assert isinstance(logger_verz, logtools.Logger)

    if "sum_txt" in outputmode:
        grid_akt = numpy.full((nrow, ncol), -9999.0, dtype=float)

        for sequence, value in logger_akt.sequence2mean.items():
            assert isinstance(sequence.subseqs, sequencetools.ModelSequences)
            assert sequence.subseqs.seqs.model.element is not None
            _, row, col = sequence.subseqs.seqs.model.element.name.split("_")
            grid_akt[int(row) - 1, int(col) - 1] = value

        filepath = os.path.join(outputdir, f"Sum_Groundwater_Recharge_{period}.txt")
        with open(filepath, "w", encoding="utf-8") as gridfile:
            gridfile.write(
                f"ncols         {ncol}\n"
                f"nrows         {nrow}\n"
                f"xllcorner     {xllcorner}\n"
                f"yllcorner     {yllcorner}\n"
                f"cellsize      {cellsize}\n"
                f"nodata_value  {nodata_value}\n"
            )

            for values in grid_akt:
                gridfile.write(f"{convert_values2string(values)}\n")

        grid_verz = numpy.full((nrow, ncol), -9999.0, dtype=float)

        for sequence, value in logger_verz.sequence2mean.items():
            assert isinstance(sequence.subseqs, sequencetools.ModelSequences)
            assert sequence.subseqs.seqs.model.element is not None
            _, row, col = sequence.subseqs.seqs.model.element.name.split("_")
            grid_verz[int(row) - 1, int(col) - 1] = value

        filepath = os.path.join(
            outputdir, f"Sum_Verz_Groundwater_Recharge_{period}.txt"
        )
        with open(filepath, "w", encoding="utf-8") as gridfile:
            gridfile.write(
                f"ncols         {ncol}\n"
                f"nrows         {nrow}\n"
                f"xllcorner     {xllcorner}\n"
                f"yllcorner     {yllcorner}\n"
                f"cellsize      {cellsize}\n"
                f"nodata_value  {nodata_value}\n"
            )

            for values in grid_verz:
                gridfile.write(f"{convert_values2string(values)}\n")

    if "txt" in outputmode:
        filepath = os.path.join(outputdir, f"Groundwater_Recharge_{period}.txt")
        with open(filepath, "w", encoding="utf-8") as seriesfile:
            seriesfile.write(
                f"# {person_in_charge}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in mm\n"
                f"# Monthly values from {simulation_start} to {simulation_end}\n"
                f"##########################################################\n"
            )
            month_logger_akt = hp.loggers["month_logger_akt"]
            assert isinstance(month_logger_akt, whmod_model.WHModMonthLogger)
            month_logger_akt.write_seriesfile(
                seriesfile=seriesfile,
                month2sequence2value=month_logger_akt.month2sequence2sum,
            )

        filepath = os.path.join(outputdir, f"Groundwater_Recharge_Verz_{period}.txt")
        with open(filepath, "w", encoding="utf-8") as seriesfile:
            seriesfile.write(
                f"# {person_in_charge}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in mm\n"
                f"# Monthly values from {simulation_start} to {simulation_end}\n"
                f"##########################################################\n"
            )
            month_logger_verz = hp.loggers["month_logger_verz"]
            assert isinstance(month_logger_verz, whmod_model.WHModMonthLogger)
            month_logger_verz.write_seriesfile(
                seriesfile=seriesfile,
                month2sequence2value=month_logger_verz.month2sequence2sum,
            )

    if "rch" in outputmode:
        filepath = os.path.join(outputdir, f"Groundwater_Recharge_{period}.rch")
        with open(filepath, "w", encoding="utf-8") as rchfile:
            rchfile.write(
                f"# {person_in_charge}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in m/s\n"
                f"# Monthly values from {simulation_start} to {simulation_end}\n"
                f"##########################################################\n"
            )
            month_logger_akt = hp.loggers["month_logger_akt"]
            assert isinstance(month_logger_akt, whmod_model.WHModMonthLogger)
            month_logger_akt.write_rchfile(rchfile)

        period = os.path.join(outputdir, f"Groundwater_Recharge_Verz_{period}.rch")
        with open(period, "w", encoding="utf-8") as rchfile:
            rchfile.write(
                f"# {person_in_charge}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in m/s\n"
                f"# Monthly values from {simulation_start} to {simulation_end}\n"
                f"##########################################################\n"
            )
            month_logger_verz = hp.loggers["month_logger_verz"]
            assert isinstance(month_logger_verz, whmod_model.WHModMonthLogger)
            month_logger_verz.write_rchfile(rchfile)

    mean_gwn = (
        sum(logger_akt.sequence2mean.values()) / len(logger_akt.sequence2sum) * 365.24
    )
    mean_verzgwn = (
        sum(logger_verz.sequence2mean.values()) / len(logger_verz.sequence2sum) * 365.24
    )

    print(f"Mean GWN [mm/a]: {mean_gwn}")
    print(f"Mean verz. GWN [mm/a]: {mean_verzgwn}")
