# --------------------------------------------------------------------------
#
# Author : Holger Albert
# Created: 29.01.2020
#
# Description:
# TODO
# --------------------------------------------------------------------------
import os
import re
import sys
import traceback

STATIONS_MAP_FILE = 'P:/whm1500340/realisierung/07_Analyse/dritte_Analyse/Klimadaten_RmF_1960-2015/Stationsliste_DWD_2019-11-27.txt'
INPUT_DIRECTORYS = [
    'P:/whm1500340/realisierung/07_Analyse/dritte_Analyse/AnalyseWHMod/series/input',
    'P:/whm1500340/realisierung/07_Analyse/dritte_Analyse/AnalyseWHMod/series/node',
]


# Umwandlung: STAT in STAT_ID
class StationsMap:
    def __init__(self) -> None:
        self.m_rr = {}
        self.m_kl = {}

    def add_to_rr(self, stat: str, stat_id: str) -> None:
        if self.m_rr.keys().__contains__(stat):
            raise Exception(f'Duplicate key in RR map {stat}')

        self.m_rr[stat] = stat_id

    def add_to_kl(self, stat: str, stat_id: str) -> None:
        if self.m_kl.keys().__contains__(stat):
            raise Exception(f'Duplicate key in KL map {stat}')

        self.m_kl[stat] = stat_id

    def contains_old_rr_station(self, stat: str) -> bool:
        return self.m_rr.keys().__contains__(stat)

    def contains_old_kl_station(self, stat: str) -> bool:
        return self.m_kl.keys().__contains__(stat)

    def get_new_rr_station(self, stat: str) -> str:
        stat_id = self.m_rr[stat]
        return stat_id

    def get_new_kl_station(self, stat: str) -> str:
        stat_id = self.m_kl[stat]
        return stat_id


def read_station_map(stations_file: str) -> StationsMap:
    # Read the stations file.
    stations_map = StationsMap()

    cnt = 0
    stations_file_handle = open(stations_file, 'r')
    for line in stations_file_handle:
        # Skip the first two lines.
        if cnt < 2:
            cnt = cnt + 1
            continue

        if line.startswith('#'):
            continue

        stat_id = line[45:52].strip().lstrip('0')
        ke = line[53:55]
        stat = line[56:61].strip().lstrip('0')

        if ke == 'RR':
            stations_map.add_to_rr(stat, stat_id)

        if ke == 'KL':
            stations_map.add_to_kl(stat, stat_id)

    return stations_map


def find_new_station(stations_map: StationsMap, kl_stations: bool, old_station: str) -> str:
    if kl_stations:
        # input -> KL stations
        if not stations_map.contains_old_kl_station(old_station):
            return None

        return stations_map.get_new_kl_station(old_station)

    # node -> RR stations
    if not stations_map.contains_old_rr_station(old_station):
        return None

    return stations_map.get_new_rr_station(old_station)


def main() -> None:
    """
    The main function.
    It is executed, if this script is indented to be run as main script.
    """
    try:
        # Read the stations map.
        stations_map = read_station_map(STATIONS_MAP_FILE)

        # Provide the file pattern and create a regular expression object.
        file_pattern = re.compile('[a-zA-Z]+_([0-9]+)_.+\\.asc', re.IGNORECASE)

        for input_directory in INPUT_DIRECTORYS:
            # Provide the path to the input files and search for matches.
            entry_filenames = []
            with os.scandir(input_directory) as entries:
                for entry in entries:
                    entry_filename = entry.name
                    entry_filenames.append(entry_filename)

            for entry_filename in entry_filenames:
                match = file_pattern.fullmatch(entry_filename)
                if match is None:
                    continue

                kl_stations = not entry_filename.startswith('P')
                entry_station = match.group(1).strip().lstrip('0')

                # Entry station 2594 is not among the RR stations.
                # We assume it to be renamed to new station 2843
                # (new station from the entry station in the KL stations).
                # Rename manually after execution of the script.
                new_station = find_new_station(stations_map, kl_stations, entry_station)
                if new_station is None:
                    print(f'Skipping file {entry_filename} with station {entry_station}...')
                    continue

                new_filename = entry_filename.replace(entry_station, new_station)

                print(f'Renaming file {entry_filename} to {new_filename}...')
                os.rename(os.path.join(input_directory, entry_filename), os.path.join(input_directory, new_filename))

        # SPECIAL CASE.
        print('SPECIAL CASE: Renaming file P_2594_sim_p.asc to P_2843_sim_p.asc...')
        os.rename(os.path.join(INPUT_DIRECTORYS[1], 'P_2594_sim_p.asc'),
                  os.path.join(INPUT_DIRECTORYS[1], 'P_2843_sim_p.asc'))
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
