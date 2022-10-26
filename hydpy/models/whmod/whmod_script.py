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
from hydpy import inputs, outputs
from hydpy.models.whmod import whmod_constants
from hydpy.models.whmod import whmod_model
from hydpy.core.typingtools import *

write = commandtools.print_textandtime


class Position(NamedTuple):
    """The row and column of a `WHMod` grid cell.

    Counting starts with 1.
    """

    row: int
    col: int


class XY(NamedTuple):
    rechts: float
    hoch: float


def _collect_hrus(table: pandas.DataFrame, idx_: int) -> Dict[str, Dict[str, object]]:
    """Collect the hrus of the respective raster-cell. Returns Dictionary."""
    result: Dict[str, Dict[str, object]] = {}
    hrus = table[table["id"] == idx_]
    for i in range(len(hrus)):
        result[f"nested_dict_nr-{i}"] = {}
        for key in table.columns:
            result[f"nested_dict_nr-{i}"][key] = hrus.reset_index().loc[i, key]
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
    >>> _ = run_subprocess(f"hyd.py run_whmod {projectpath} False")
    Mean GWN [mm/a]: 39.05889624326555
    Mean verz. GWN [mm/a]: 37.17119700488022
    """
    write_output_ = objecttools.value2bool("x", write_output)
    if write_output_:
        write("Start WHMOD calculations")
        hydpy.pub.options.printprogress = True
    else:
        hydpy.pub.options.printprogress = False

    BASEDIR = basedir

    dtype_whmod_main = {
        "PERSON_IN_CHARGE": str,
        "HYDPY_VERSION": str,
        "OUTPUTDIR": str,
        "OUTPUTMODE": str,
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

    WHMod_Main = pandas.read_csv(
        os.path.join(BASEDIR, "WHMod_Main.txt"),
        sep="\t",
        comment="#",
        header=None,
        index_col=0,
    ).T
    WHMod_Main = WHMod_Main.astype(dtype_whmod_main)

    PERSON_IN_CHARGE = WHMod_Main["PERSON_IN_CHARGE"][1].strip()
    HYDPY_VERSION = WHMod_Main["HYDPY_VERSION"][1].strip()

    # check Hydpy-Version
    if HYDPY_VERSION != hydpy.__version__:
        warnings.warn(
            f"The currently used Hydpy-Version ({hydpy.__version__}) differs from the "
            f"Hydpy-Version ({HYDPY_VERSION}) defined in WHMod_Main.txt"
        )

    OUTPUTDIR = os.path.join(BASEDIR, WHMod_Main["OUTPUTDIR"][1].strip())
    OUTPUTMODE = WHMod_Main["OUTPUTMODE"][1].split(",")
    for i, mode in enumerate(OUTPUTMODE):
        OUTPUTMODE[i] = OUTPUTMODE[i].strip()
    FILENAME_NODE_DATA = WHMod_Main["FILENAME_NODE_DATA"][1].strip()
    FILENAME_TIMESERIES = WHMod_Main["FILENAME_TIMESERIES"][1].strip()
    FILENAME_STATION_DATA = WHMod_Main["FILENAME_STATION_DATA"][1].strip()
    WITH_CAPPILARY_RISE = WHMod_Main["WITH_CAPPILARY_RISE"][1]
    DEGREE_DAY_FACTOR = WHMod_Main["DEGREE_DAY_FACTOR"][1]
    SIMULATION_START = WHMod_Main["SIMULATION_START"][1]
    SIMULATION_END = WHMod_Main["SIMULATION_END"][1]
    FREQUENCE = WHMod_Main["FREQUENCE"][1]
    CELLSIZE = WHMod_Main["CELLSIZE"][1]
    NODATA_VALUE = WHMod_Main["NODATA_VALUE"][1]

    hydpy.pub.timegrids = SIMULATION_START, SIMULATION_END, FREQUENCE
    hydpy.pub.options.parameterstep = FREQUENCE
    hydpy.pub.options.checkseries = False
    hydpy.pub.options.usecython = True

    # Read Node Data
    dtype_knoteneigenschaften = {
        "id": int,
        "f_id": int,
        "row": int,
        "col": int,
        "x": float,
        "y": float,
        "area": int,
        "f_area": int,
        "nutz_nr": str,
        "bodentyp": str,
        "nfk100_mittel": float,
        "nfk_faktor": float,
        "nfk_offset": float,
        "flurab": float,
        "bfi": float,
        "verzoegerung": float,
        "init_boden": float,
        "init_gwn": float,
    }

    df_knoteneigenschaften = pandas.read_csv(
        os.path.join(BASEDIR, FILENAME_NODE_DATA),
        skiprows=[1],
        sep=";",
        decimal=",",
    )
    df_knoteneigenschaften = df_knoteneigenschaften.astype(dtype_knoteneigenschaften)

    df_stammdaten = pandas.read_csv(
        os.path.join(BASEDIR, FILENAME_STATION_DATA), sep="\t"
    )
    df_stammdaten["Messungsart"] = df_stammdaten["Dateiname"].apply(
        lambda a: a.split("_")[1].split(".")[0]
    )

    # define Selections
    whmodselection = hydpy.Selection("raster")
    evapselection_stat = hydpy.Selection("evap_stat")
    evapselection_raster = hydpy.Selection("evap_raster")
    meteoselection_stat = hydpy.Selection("meteo_stat")
    CSSRselection_stat = hydpy.Selection("CSSR_stat")
    GSRselection_stat = hydpy.Selection("GSR_stat")
    tempselection_stat = hydpy.Selection("temp_stat")
    tempselection_raster = hydpy.Selection("temp_raster")
    precselection_stat = hydpy.Selection("prec_stat")
    precselection_raster = hydpy.Selection("prec_raster")

    hp = hydpy.HydPy("run_WHMod")
    hydpy.pub.sequencemanager.filetype = "asc"

    node2xy: Dict[hydpy.Node, XY] = {}

    _initialize_whmod_models(
        write_output=write_output_,
        df_knoteneigenschaften=df_knoteneigenschaften,
        precselection_raster=precselection_raster,
        tempselection_raster=tempselection_raster,
        evapselection_raster=evapselection_raster,
        whmodselection=whmodselection,
        WITH_CAPPILARY_RISE=WITH_CAPPILARY_RISE,
        DEGREE_DAY_FACTOR=DEGREE_DAY_FACTOR,
        node2xy=node2xy,
    )

    _initialize_weather_stations(
        df_stammdaten=df_stammdaten,
        CSSRselection_stat=CSSRselection_stat,
        GSRselection_stat=GSRselection_stat,
        meteoselection_stat=meteoselection_stat,
        evapselection_stat=evapselection_stat,
        tempselection_stat=tempselection_stat,
        precselection_stat=precselection_stat,
        FILENAME_TIMESERIES=FILENAME_TIMESERIES,
        BASEDIR=BASEDIR,
        node2xy=node2xy,
    )

    _initialize_conv_models(
        evapselection_stat=evapselection_stat,
        evapselection_raster=evapselection_raster,
        tempselection_stat=tempselection_stat,
        tempselection_raster=tempselection_raster,
        precselection_stat=precselection_stat,
        precselection_raster=precselection_raster,
        node2xy=node2xy,
    )

    # Merge Selections
    hydpy.pub.selections = hydpy.Selections(
        whmodselection,
        CSSRselection_stat,
        GSRselection_stat,
        meteoselection_stat,
        evapselection_stat,
        evapselection_raster,
        tempselection_stat,
        tempselection_raster,
        precselection_stat,
        precselection_raster,
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
    hp.loggers["logger_akt"] = logtools.Logger(SIMULATION_START, SIMULATION_END)
    hp.loggers["logger_verz"] = logtools.Logger(SIMULATION_START, SIMULATION_END)

    # same for the month logger
    if "txt" in OUTPUTMODE or "rch" in OUTPUTMODE:
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
    hydpy.pub.sequencemanager.currentdir = f"{OUTPUTDIR}"

    ncol = df_knoteneigenschaften["col"].max()
    nrow = df_knoteneigenschaften["row"].max()
    xllcorner = df_knoteneigenschaften["x"].min()
    yllcorner = df_knoteneigenschaften["y"].min()

    _save_results(
        write_output=write_output_,
        OUTPUTDIR=OUTPUTDIR,
        OUTPUTMODE=OUTPUTMODE,
        nrow=nrow,
        ncol=ncol,
        hp=hp,
        CELLSIZE=CELLSIZE,
        SIMULATION_START=SIMULATION_START,
        SIMULATION_END=SIMULATION_END,
        xllcorner=xllcorner,
        yllcorner=yllcorner,
        NODATA_VALUE=NODATA_VALUE,
        PERSON_IN_CHARGE=PERSON_IN_CHARGE,
    )


def _initialize_whmod_models(
    write_output: bool,
    df_knoteneigenschaften: pandas.DataFrame,
    precselection_raster: hydpy.Selection,
    tempselection_raster: hydpy.Selection,
    evapselection_raster: hydpy.Selection,
    whmodselection: hydpy.Selection,
    WITH_CAPPILARY_RISE: bool,
    DEGREE_DAY_FACTOR: float,
    node2xy: Dict[hydpy.Node, XY],
) -> None:
    """In this function, the whmod-elements are initialized based on the data provided
    in Node_Data.csv.  The arguments of this function are HydPy-selections, which
    contain the respective nodes and elements. Furthermore information about cappilary
    rise (WITH_CAPPILARY_RISE) and the degree day factor (DEGREE_DAY_FACTOR) have to be
    provided.
    """
    # Initialize WHMod-Models
    if write_output:
        write("Initialize WHMOD")

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
        precselection_raster.nodes.add_device(precnode)

        # Initialize Temperature Nodes
        tempnode = hydpy.Node(f"T_{name}", variable=inputs.whmod_Temp_TM)
        tempselection_raster.nodes.add_device(tempnode)

        # Initialize Evap Nodes
        evapnode = hydpy.Node(f"E_{name}", variable=inputs.whmod_ET0)
        evapselection_raster.nodes.add_device(evapnode)

        # Initialize WHMod-Elements
        raster = hydpy.Element(f"WHMod_{name}", inputs=(precnode, tempnode, evapnode))

        # Hinzufügen zu WHMod-Selection
        whmodselection.elements.add_device(raster)

        # find number of hrus in element
        hrus = _collect_hrus(df_knoteneigenschaften, idx)

        # Coordinates
        rechts = _return_con_hru(hrus, "x")[0]
        assert isinstance(rechts, float)
        hoch = _return_con_hru(hrus, "y")[0]
        assert isinstance(hoch, float)
        xy = XY(rechts=rechts, hoch=hoch)

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
        con.mitfunktion_kapillareraufstieg(WITH_CAPPILARY_RISE)

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
            temp_list.append(whmod_constants.SOIL_CONSTANTS[bodentyp])
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
        con.gradfaktor(float(DEGREE_DAY_FACTOR))
        nfk100_mittel = _return_con_hru(hrus, "nfk100_mittel")[0]
        assert isinstance(nfk100_mittel, float)
        nfk_faktor = _return_con_hru(hrus, "nfk_faktor")[0]
        assert isinstance(nfk_faktor, float)
        nfk_offset = _return_con_hru(hrus, "nfk_offset")[0]
        assert isinstance(nfk_offset, float)
        nfk = (nfk100_mittel * nfk_faktor) + nfk_offset
        con.nfk100_mittel(nfk)

        con.flurab(_return_con_hru(hrus, "flurab"))
        con.maxwurzeltiefe(
            gras=0.6,
            laubwald=1.5,
            nadelwald=1.5,
            mais=1.0,
            sommerweizen=1.0,
            winterweizen=1.0,
            zuckerrueben=0.8,
        )
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

        verzoegerung = _return_con_hru(hrus, "verzoegerung")[0]
        assert isinstance(verzoegerung, float)
        if verzoegerung > 0:
            con.schwerpunktlaufzeit(verzoegerung)
        else:
            flurab = _return_con_hru(hrus, "flurab")[0]
            assert isinstance(flurab, float)
            con.schwerpunktlaufzeit(flurab_probst=flurab)

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
    CSSRselection_stat: hydpy.Selection,
    GSRselection_stat: hydpy.Selection,
    meteoselection_stat: hydpy.Selection,
    evapselection_stat: hydpy.Selection,
    tempselection_stat: hydpy.Selection,
    precselection_stat: hydpy.Selection,
    FILENAME_TIMESERIES: str,
    BASEDIR: str,
    node2xy: Dict[hydpy.Node, XY],
) -> None:
    """In this function, the data from the weather stations is integrated in the
    temperature- and precipitation-nodes, as well as the meteo- and evap-elements.  The
    arguments of this function are HydPy-selections, which contain the respective nodes
     and elements, and the Node_Data.csv (as a Pandas DataFrame "df_stammdaten").
    Furthermore, the locations of the basedircetory (BASEDIR) and the folder with the
    timeseries (FILENAME_TIMESERIES) are required.
    """
    # Initialization Meteo-Elements, Evap-Elements, Temp-Nodes
    # Fused Variables
    CSSR = devicetools.FusedVariable(
        "CSSR", outputs.meteo_ClearSkySolarRadiation, inputs.evap_ClearSkySolarRadiation
    )
    GSR = devicetools.FusedVariable(
        "GSR", outputs.meteo_GlobalRadiation, inputs.evap_GlobalRadiation
    )
    # Iteration over Weather Stations
    for stat in df_stammdaten["StationsNr"].unique():
        # Stationsdaten einladen
        stations_daten = df_stammdaten[df_stammdaten["StationsNr"] == stat]

        index = stations_daten.index[0]

        xy = XY(
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

        CSSR_Node = hydpy.Node(f"CSSR_{stat}", variable=CSSR)
        GSR_Node = hydpy.Node(f"GSR_{stat}", variable=GSR)
        CSSRselection_stat.nodes.add_device(CSSR_Node)
        GSRselection_stat.nodes.add_device(GSR_Node)

        evap_node = hydpy.Node(
            f"E_{stat}", variable=outputs.evap_ReferenceEvapotranspiration
        )
        node2xy[evap_node] = xy

        # Meteo-Elemente
        meteo_element = hydpy.Element(f"Meteo_{stat}", outputs=(CSSR_Node, GSR_Node))
        meteo = hydpy.prepare_model("meteo_v001", "1d")
        meteo_element.model = meteo

        # Evap-Element
        evap_element = hydpy.Element(
            f"Evap_{stat}", inputs=(CSSR_Node, GSR_Node), outputs=(evap_node)
        )
        evap = hydpy.prepare_model("evap_v001", "1d")
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
        con_evap.measuringheightwindspeed(10.0)
        evap.parameters.update()

        evap_element.model.sequences.logs.loggedglobalradiation(0.0)
        evap_element.model.sequences.logs.loggedclearskysolarradiation(0.0)

        inp_meteo = meteo.sequences.inputs
        inp_evap = evap.sequences.inputs

        inp_meteo.prepare_series()
        inp_evap.prepare_series()

        inp_meteo.sunshineduration.filepath = os.path.join(
            BASEDIR,
            FILENAME_TIMESERIES,
            seq_sunshineduration,
        )
        inp_meteo.sunshineduration.load_series()
        del inp_meteo.sunshineduration.filepath

        inp_evap.airtemperature.filepath = os.path.join(
            BASEDIR, FILENAME_TIMESERIES, seq_airtemperature
        )
        inp_evap.airtemperature.load_series()

        inp_evap.relativehumidity.filepath = os.path.join(
            BASEDIR,
            FILENAME_TIMESERIES,
            seq_relativehumidity,
        )
        inp_evap.relativehumidity.load_series()
        del inp_evap.relativehumidity.filepath

        inp_evap.windspeed.filepath = os.path.join(
            BASEDIR, FILENAME_TIMESERIES, seq_windspeed
        )
        inp_evap.windspeed.load_series()
        del inp_evap.windspeed.filepath

        inp_evap.atmosphericpressure.filepath = os.path.join(
            BASEDIR,
            FILENAME_TIMESERIES,
            seq_atmosphericpressure,
        )
        inp_evap.atmosphericpressure.load_series()
        del inp_evap.atmosphericpressure.filepath

        # Initialization of Temperature-Nodes
        T_node = hydpy.Node(f"T_{stat}", variable="T")
        T_node.deploymode = "obs"
        T_node.prepare_obsseries()
        T_node.sequences.obs.series = inp_evap.airtemperature.series
        node2xy[T_node] = xy

        # add meteo-elements, evap-elements, evap-nodes to selections
        meteoselection_stat.elements.add_device(meteo_element)
        evapselection_stat.nodes.add_device(evap_node)
        evapselection_stat.elements.add_device(evap_element)
        tempselection_stat.nodes.add_device(T_node)

    # Initialization Precipitation-Nodes
    for stat in df_stammdaten["StationsNr"].unique():
        # Load weather station data
        stations_daten = df_stammdaten[df_stammdaten["StationsNr"] == stat]

        index = stations_daten.index[0]

        seq_precipitation = stations_daten["Dateiname"][
            stations_daten["Messungsart"] == "Niederschlag"
        ].values[0]

        P_node = hydpy.Node(f"P_{stat}", variable="P")
        P_node.deploymode = "obs"
        precselection_stat.nodes.add_device(P_node)
        node2xy[P_node] = XY(
            rechts=df_stammdaten.loc[index, "X"], hoch=df_stammdaten.loc[index, "Y"]
        )
        P_node.prepare_obsseries()
        P_node.sequences.obs.filepath = os.path.join(
            BASEDIR, FILENAME_TIMESERIES, seq_precipitation
        )
        P_node.sequences.obs.load_series()
        del P_node.sequences.obs.filepath


def _initialize_conv_models(
    evapselection_stat: hydpy.Selection,
    evapselection_raster: hydpy.Selection,
    tempselection_stat: hydpy.Selection,
    tempselection_raster: hydpy.Selection,
    precselection_stat: hydpy.Selection,
    precselection_raster: hydpy.Selection,
    node2xy: Dict[hydpy.Node, XY],
) -> None:
    """The conv models are based on the selections of the input data of the weather
    stations (evapselection_stat, tempselection_stat, precselection_stat) and their
    rasterized counterpart (evapselection_raster, tempselection_raster,
    precselection_raster).
    """
    # Initialization Conv-Modelle
    def _get_coordinatedict(nodes: hydpy.Nodes) -> Dict[str, XY]:
        """Returns a Dictionary with x and y values. Used for Conv-models."""
        return {n.name: node2xy[n] for n in nodes}

    # Conv-Modell PET
    conv_pet = hydpy.prepare_model("conv_v002")
    conv_pet.parameters.control.inputcoordinates(
        **_get_coordinatedict(evapselection_stat.nodes)
    )
    conv_pet.parameters.control.outputcoordinates(
        **_get_coordinatedict(evapselection_raster.nodes)
    )
    conv_pet.parameters.control.maxnmbinputs()
    conv_pet.parameters.control.power(2.0)
    element = hydpy.Element(
        "ConvPET", inlets=evapselection_stat.nodes, outlets=evapselection_raster.nodes
    )
    element.model = conv_pet
    evapselection_stat.elements.add_device(element)

    # Conv-Modell Temperature
    conv_temp = hydpy.prepare_model("conv_v002")
    conv_temp.parameters.control.inputcoordinates(
        **_get_coordinatedict(tempselection_stat.nodes)
    )
    conv_temp.parameters.control.outputcoordinates(
        **_get_coordinatedict(tempselection_raster.nodes)
    )
    conv_temp.parameters.control.maxnmbinputs()
    conv_temp.parameters.control.power(2.0)

    element = hydpy.Element(
        "ConvTemp", inlets=tempselection_stat.nodes, outlets=tempselection_raster.nodes
    )
    element.model = conv_temp
    tempselection_stat.elements.add_device(element)

    conv_prec = hydpy.prepare_model("conv_v002")
    conv_prec.parameters.control.inputcoordinates(
        **_get_coordinatedict(precselection_stat.nodes)
    )
    conv_prec.parameters.control.outputcoordinates(
        **_get_coordinatedict(precselection_raster.nodes)
    )
    conv_prec.parameters.control.maxnmbinputs()
    conv_prec.parameters.control.power(2.0)
    element = hydpy.Element(
        "ConvPrec", inlets=precselection_stat.nodes, outlets=precselection_raster.nodes
    )
    element.model = conv_prec
    precselection_stat.elements.add_device(element)


def _save_results(
    write_output: bool,
    OUTPUTDIR: str,
    OUTPUTMODE: str,
    nrow: int,
    ncol: int,
    hp: hydpy.HydPy,
    CELLSIZE: int,
    SIMULATION_START: str,
    SIMULATION_END: str,
    xllcorner: float,
    yllcorner: float,
    NODATA_VALUE: float,
    PERSON_IN_CHARGE: str,
) -> None:
    def convert_values2string(values_: Sequence[float]) -> str:
        return " ".join(str(-9999.0 if v == -9999.0 else v * 365.24) for v in values_)

    period = f"{SIMULATION_START[0:4]}-{SIMULATION_END[0:4]}"

    # write = commandtools.print_textandtime
    if write_output == True:
        write(f"Write Output in {OUTPUTDIR}")

    logger_akt = hp.loggers["logger_akt"]
    assert isinstance(logger_akt, logtools.Logger)
    logger_verz = hp.loggers["logger_verz"]
    assert isinstance(logger_verz, logtools.Logger)

    if "sum_txt" in OUTPUTMODE:
        grid_akt = numpy.full((nrow, ncol), -9999.0, dtype=float)

        for sequence, value in logger_akt.sequence2mean.items():
            assert isinstance(sequence.subseqs, sequencetools.ModelSequences)
            assert sequence.subseqs.seqs.model.element is not None
            _, row, col = sequence.subseqs.seqs.model.element.name.split("_")
            grid_akt[int(row) - 1, int(col) - 1] = value

        filepath = os.path.join(OUTPUTDIR, f"Sum_Groundwater_Recharge_{period}.txt")
        with open(filepath, "w", encoding="utf-8") as gridfile:
            gridfile.write(
                f"ncols         {ncol}\n"
                f"nrows         {nrow}\n"
                f"xllcorner     {xllcorner}\n"
                f"yllcorner     {yllcorner}\n"
                f"cellsize      {CELLSIZE}\n"
                f"nodata_value  {NODATA_VALUE}\n"
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
            OUTPUTDIR, f"Sum_Verz_Groundwater_Recharge_{period}.txt"
        )
        with open(filepath, "w", encoding="utf-8") as gridfile:
            gridfile.write(
                f"ncols         {ncol}\n"
                f"nrows         {nrow}\n"
                f"xllcorner     {xllcorner}\n"
                f"yllcorner     {yllcorner}\n"
                f"cellsize      {CELLSIZE}\n"
                f"nodata_value  {NODATA_VALUE}\n"
            )

            for values in grid_verz:
                gridfile.write(f"{convert_values2string(values)}\n")

    if "txt" in OUTPUTMODE:
        filepath = os.path.join(OUTPUTDIR, f"Groundwater_Recharge_{period}.txt")
        with open(filepath, "w", encoding="utf-8") as seriesfile:
            seriesfile.write(
                f"# {PERSON_IN_CHARGE}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in mm\n"
                f"# Monthly values from {SIMULATION_START} to {SIMULATION_END}\n"
                f"##########################################################\n"
            )
            month_logger_akt = hp.loggers["month_logger_akt"]
            assert isinstance(month_logger_akt, whmod_model.WHModMonthLogger)
            month_logger_akt.write_seriesfile(
                seriesfile=seriesfile,
                month2sequence2value=month_logger_akt.month2sequence2sum,
            )

        filepath = os.path.join(OUTPUTDIR, f"Groundwater_Recharge_Verz_{period}.txt")
        with open(filepath, "w", encoding="utf-8") as seriesfile:
            seriesfile.write(
                f"# {PERSON_IN_CHARGE}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in mm\n"
                f"# Monthly values from {SIMULATION_START} to {SIMULATION_END}\n"
                f"##########################################################\n"
            )
            month_logger_verz = hp.loggers["month_logger_verz"]
            assert isinstance(month_logger_verz, whmod_model.WHModMonthLogger)
            month_logger_verz.write_seriesfile(
                seriesfile=seriesfile,
                month2sequence2value=month_logger_verz.month2sequence2sum,
            )

    if "rch" in OUTPUTMODE:
        filepath = os.path.join(OUTPUTDIR, f"Groundwater_Recharge_{period}.rch")
        with open(filepath, "w", encoding="utf-8") as rchfile:
            rchfile.write(
                f"# {PERSON_IN_CHARGE}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in m/s\n"
                f"# Monthly values from {SIMULATION_START} to {SIMULATION_END}\n"
                f"##########################################################\n"
            )
            month_logger_akt = hp.loggers["month_logger_akt"]
            assert isinstance(month_logger_akt, whmod_model.WHModMonthLogger)
            month_logger_akt.write_rchfile(rchfile)

        period = os.path.join(OUTPUTDIR, f"Groundwater_Recharge_Verz_{period}.rch")
        with open(period, "w", encoding="utf-8") as rchfile:
            rchfile.write(
                f"# {PERSON_IN_CHARGE}, {datetime.datetime.now()}\n"
                f"# Monthly WHMod-Groundwater Recharge in m/s\n"
                f"# Monthly values from {SIMULATION_START} to {SIMULATION_END}\n"
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
