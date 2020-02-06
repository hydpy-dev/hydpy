# --------------------------------------------------------------------------
# -*- coding: utf-8 -*-
#
# Author : Holger Albert
# Created: 29.01.2020
#
# Description:
# TODO
# --------------------------------------------------------------------------
import hydpy
import numpy
import os
import pytz
import re
import sys
import traceback
from datetime import timedelta, datetime
from typing import *
from hydpy import pub
from hydpy.core.sequencetools import IOSequence

# Use flags.
UPDATE_CLIMATE = True
UPDATE_PRECIPITATION = False

# Paths to the input data.
CLIMATE_INPUT_PATH = 'C:/Temp/whmod/dritte_Analyse/Klimadaten_2016-2019/Klimadaten'
PRECIPITATION_INPUT_DATA = 'C:/Temp/whmod/dritte_Analyse/Klimadaten_2016-2019/Niederschlagsdaten'

# Paths to the output data.
SERIES_NODE = 'C:/Temp/whmod/dritte_Analyse/AnalyseWHMod/series/node'
SERIES_INPUT = 'C:/Temp/whmod/dritte_Analyse/AnalyseWHMod/series/input'

# Existing time range.
DATE_START_OLD = '1960-01-01 00:00:00+01:00'
DATE_END_OLD = '2016-01-01 00:00:00+01:00'

# Time range to add.
DATE_START_NEW = '2016-01-01 00:00:00+01:00'
DATE_END_NEW = '2020-01-20 00:00:00+01:00'


# --------------------------------------------------------------------------
# Classes.
# --------------------------------------------------------------------------

class DwdFileLine:
    """This class represents one line of the DWD file."""

    def __init__(self, tokens: List[str]) -> None:
        self.m_values = []

        for token in tokens:
            self.m_values.append(token.strip())

    def get_values_size(self) -> int:
        return len(self.m_values)

    def get_station(self, station_index: int) -> str:
        return self.m_values[station_index]

    def get_date(self, date_index: int) -> datetime:
        # REMARK: Parses the date string (only day, month and year) without time and without timezone.
        date_str = self.m_values[date_index]
        date_time = datetime.strptime(date_str, '%Y%m%d')
        return date_time

    def get_value(self, data_type_index) -> float:
        value_str = self.m_values[data_type_index]
        return float(value_str)


class DwdFile:
    """This class represents the whole DWD file."""

    def __init__(self, tokens: List[str]) -> None:
        self.m_titles = []
        self.m_lines = {}
        self.m_first_date = None

        for token in tokens:
            self.m_titles.append(token.strip())

    def get_titles_size(self) -> int:
        return len(self.m_titles)

    def add_line(self, line: DwdFileLine) -> None:
        if self.get_titles_size() != line.get_values_size():
            raise Exception('Die Wert-Zeile muss die selbe Anzahl Spalten besitzen, wie die Titel-Zeile.')

        if len(self.m_lines) == 0:
            date_index = self.m_titles.index('MESS_DATUM')
            date_time = line.get_date(date_index)
            self.m_lines[date_time] = line
            self.m_first_date = date_time
            return

        station_index = self.m_titles.index('STATIONS_ID')
        if self.m_lines[self.m_first_date].get_station(station_index) != line.get_station(station_index):
            raise Exception(
                'Die Station der hinzugefügten Wert-Zeile muss die Selbe Station enthalten, wie die erste Wert-Zeile.')

        date_index = self.m_titles.index('MESS_DATUM')
        date_time = line.get_date(date_index)
        self.m_lines[date_time] = line

    def get_station(self) -> str:
        station_index = self.m_titles.index('STATIONS_ID')
        if len(self.m_lines) == 0:
            raise Exception('Keine Wert-Zeilen vorhanden.')

        return self.m_lines[self.m_first_date].get_station(station_index)

    # TODO Unit conversion
    def get_value(self, date_time: datetime, data_type: str) -> float:
        # REMARK: Remove timezone as the keys do not have a time and timezone (time is already zeroed).
        key = date_time.replace(tzinfo=None)
        if not self.m_lines.keys().__contains__(key):
            return None

        line = self.m_lines[key]
        data_type_index = self.m_titles.index(data_type)

        value = line.get_value(data_type_index)
        if value == -999.0:
            return numpy.nan

        return value


# --------------------------------------------------------------------------
# Functions.
# --------------------------------------------------------------------------

def date_range(start_date, end_date) -> datetime:
    """This is a generator function that generates all dates in the date range with the timestep one day."""
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def create_or_update_data_file(dwd_file: DwdFile, key: str) -> None:
    # Read the existing data.
    station = dwd_file.get_station()

    # Build the hydpy filename.
    switcher = {
        'airtemperature': os.path.join(SERIES_INPUT, f'Evap_{station}_input_{key}.asc'),
        'atmosphericpressure': os.path.join(SERIES_INPUT, f'Evap_{station}_input_{key}.asc'),
        'relativehumidity': os.path.join(SERIES_INPUT, f'Evap_{station}_input_{key}.asc'),
        'sunshineduration': os.path.join(SERIES_INPUT, f'Evap_{station}_input_{key}.asc'),
        'windspeed': os.path.join(SERIES_INPUT, f'Evap_{station}_input_{key}.asc'),
        't': os.path.join(SERIES_NODE, f'T_{station}_sim_{key}.asc'),
        'p': os.path.join(SERIES_NODE, f'P_{station}_sim_{key}.asc'),
    }

    hydpy_filename = switcher[key]

    # Build the data type.
    switcher = {
        'airtemperature': 'TMK',  # TM = Mittel der Temperatur in 2 m über dem Erdboden / Grad Celsius
        'atmosphericpressure': 'PM',  # PM = Mittel des Luftdruckes in Stationshöhe / hpa
        'relativehumidity': 'UPM',  # RFM = Mittel der relativen Feuchte / %
        'sunshineduration': 'SDK',  # SO = Summe der Sonnenscheindauer / h
        'windspeed': 'FM',  # FM = Mittel der Windstärke / m/sec
        't': 'TMK',  # TM = Mittel der Temperatur in 2 m über dem Erdboden / Grad Celsius
        'p': 'RSK',  # RR/RSK = Niederschlagshöhe / mm
    }

    data_type = switcher[key]

    # Specifiy the new complete date range.
    start_date_str = min(DATE_START_OLD, DATE_START_NEW)
    end_date_str = max(DATE_END_OLD, DATE_END_NEW)
    pub.timegrids = start_date_str, end_date_str, '1d'
    pub.options.checkseries = False
    pub.sequencemanager = hydpy.core.filetools.SequenceManager()

    # Create the io sequence and load the file.
    IOSequence.NDIM = 0
    iosequence = IOSequence(None)
    iosequence.aggregation_ext = 'none'
    iosequence.overwrite_ext = True
    iosequence.filetype_ext = 'asc'
    iosequence.filepath_ext = hydpy_filename
    iosequence.fastaccess._iosequence_diskflag = False
    iosequence.activate_ram()
    iosequence.load_ext()

    # Iterate over the complete date range (format: 1960-01-01 00:00:00+01:00).
    for date_time in date_range(datetime.fromisoformat(start_date_str), datetime.fromisoformat(end_date_str)):
        date_time_str = date_time.isoformat(' ')

        # Is there a value in the new data?
        value = dwd_file.get_value(date_time, data_type)
        if value is not None:
            # Yes, there is a value in the new data.

            # Update/Add the value in/to the existing data.
            index = pub.timegrids.init[date_time_str]

            # If new value is not nan, always set it.
            if value is not numpy.nan:
                iosequence.series[index] = value
            else:
                if iosequence.series[index] is None:
                    iosequence.series[index] = value
        else:
            # No, there is no value in the new data.

            # Set NaN as value to the existing data, if there is no other value.
            index = pub.timegrids.init[date_time_str]
            if iosequence.series[index] is None:
                iosequence.series[index] = numpy.nan

    # Save the file.
    iosequence.save_ext()


def create_or_update_data(input_file: str) -> None:
    # Read the input file.
    print(f'Processing file {input_file}...')
    dwd_file = None

    first_line = True
    input_file_handle = open(input_file, 'r')
    for line in input_file_handle:
        tokens = line.split(';')

        if first_line is True:
            dwd_file = DwdFile(tokens)
            first_line = False
            continue

        dwd_file_line = DwdFileLine(tokens)
        dwd_file.add_line(dwd_file_line)

    input_file_handle.close()

    # Create/Update the data.

    # Evap_2543_input_airtemperature
    create_or_update_data_file(dwd_file, 'airtemperature')

    # Evap_2543_input_atmosphericpressure
    create_or_update_data_file(dwd_file, 'atmosphericpressure')

    # Evap_2543_input_relativehumidity
    create_or_update_data_file(dwd_file, 'relativehumidity')

    # Evap_2543_input_sunshineduration
    create_or_update_data_file(dwd_file, 'sunshineduration')

    # Evap_2543_input_windspeed
    create_or_update_data_file(dwd_file, 'windspeed')

    # T_2594_sim_t
    create_or_update_data_file(dwd_file, 't')

    # P_2594_sim_p
    create_or_update_data_file(dwd_file, 'p')


def get_input_files(input_directory: str) -> List[str]:
    """This function scans the input directory and returns the input files."""

    # Memory for the input files.
    input_files = []

    # Provide the file pattern and create a regular expression object.
    file_pattern = re.compile('produkt_[a-zA-Z]+_tag_([0-9]{8})_([0-9]{8})_([0-9]{5})\\.txt', re.IGNORECASE)

    # Provide the path to the input files and search for matches.
    with os.scandir(input_directory) as entries:
        for entry in entries:
            match = file_pattern.fullmatch(entry.name)
            if match is None:
                continue

            input_files.append(os.path.join(input_directory, entry.name))

    return input_files


def main() -> None:
    """
    The main function.
    It is executed, if this script is indented to be run as main script.
    """
    try:
        # Climate data.
        if UPDATE_CLIMATE:
            input_files = get_input_files(CLIMATE_INPUT_PATH)
            for input_file in input_files:
                create_or_update_data(input_file)

        # Precipitation data.
        if UPDATE_PRECIPITATION:
            input_files = get_input_files(PRECIPITATION_INPUT_DATA)
            for input_file in input_files:
                create_or_update_data(input_file)

    except:
        # Get the error information.
        sys_info = sys.exc_info()
        msg = traceback.format_tb(sys_info[2])[0] + str(sys_info[0]) + ": " + str(sys_info[1]) + "\n"

        # Print error messages.
        print(msg)


# Only execute, if this script is running as main script.
if __name__ == '__main__':
    # Execute the script.
    main()
