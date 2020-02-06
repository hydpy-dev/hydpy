
import collections
import os
import sys
from typing import *
import numpy
import pandas
from matplotlib import pyplot
import hydpy
from hydpy.models import whmod_v3
from hydpy.models.whmod import whmod_inputs

os.chdir('C:/Temp/whmod/dritte_Analyse')

folder_whmodinput = '../erste_Analyse/WHMod/input'
filename_knoteneigenschaften = 'Knoteneigenschaften_Modellvergleich_v01d.daten'
filename_nutzungen = 'Nutzungen_Modellvergleich_v01f.n'

filepath_bfiraster = r'GIS/bfi_extracted.txt'

folder_metinput = r'Klimadaten_RmF_1960-2015'
filename_metstationinfo = 'RmF Klimadaten Stammdaten.dat'
filename_precstationinfo = 'RmF Niederschlag Stammdaten.dat'
filename_dwdliste = 'Stationsliste_DWD_2019-11-27.txt'
filename_airtemperature = 'Rmf Temperatur 1960-2015.dat'
filename_relativehumidity = 'RmF Luftfeuchte 1960-2015.dat'
filename_windspeed_original = 'RmF Windgeschwindigkeit 1960-2015 (Werte).dat'
filename_windspeed_modified = '_RmF Windgeschwindigkeit 1960-2015 (Werte).dat'
filename_sunshineduration = 'RmF Sonnenschein 1960-2015.dat'
filename_precipitation = 'RmF Niederschlag 1960-2015 (Roh).dat'

hydpy.pub.options.checkseries = False


# Stationsbenennung in Winddatei vereinheitlichen

inpath = os.path.join(folder_metinput, filename_windspeed_original)
with open(inpath) as infile:
    text = infile.read()
text = text.replace('DWD-ID 917', 'DWD-Bft 2592')
text = text.replace('DWD-ID 1420', 'DWD-Bft 2640')
text = text.replace('DWD-ID 2601', 'DWD-Bft 2648')
text = text.replace('DWD-ID 2843', 'DWD-Bft 2594')
text = text.replace('DWD-ID 7341', 'DWD-Bft 2551')
outpath = os.path.join(folder_metinput, filename_windspeed_modified)
with open(outpath, 'w') as outfile:
    outfile.write(text)


# Initialisierung WHMod-Modelle

def get_nutznr2subnutz(filepath: str) -> Dict[int, List[Tuple[str, float]]]:
    result = {}
    with open(filepath) as file_:
        for line in file_:
            if line.startswith('Alias'):
                pairs = [entry.split('=') for entry in line.split()]
                result[int(pairs[0][1])] = [
                    (name, float(value)/100.) for (name, value) in pairs[1:]]
    return result


def collect_hrus(table, idx_):
    result = collections.defaultdict(lambda: 0.)
    nutz_nr = getattr(table, 'Nutz_NR')[idx_]
    for subnutz, fraction in nutznr2subnutz[nutz_nr]:
        subkeys = [f'SubNutz:{subnutz}']
        for name in ('Flurab', 'nfk100_mittel', 'Bodentyp'):
            subkeys.append(f'{name}:{getattr(table, name)[idx_]}')
        key = '_'.join(subkeys)
        result[key] += fraction * table.F_AREA[idx_]
    return result


table_knoteneigenschaften = pandas.read_csv(
    f'{folder_whmodinput}/{filename_knoteneigenschaften}', sep='\t')

nutznr2subnutz = get_nutznr2subnutz(
    f'{folder_whmodinput}/{filename_nutzungen}')

whmodselection = hydpy.Selection('raster')
petselection_stat = hydpy.Selection('pet_stat')
petselection_raster = hydpy.Selection('pet_raster')
tempselection_stat = hydpy.Selection('temp_stat')
tempselection_raster = hydpy.Selection('temp_raster')
precselection_stat = hydpy.Selection('prec_stat')
precselection_raster = hydpy.Selection('prec_raster')


def calculate_coordinates(row_: int, col_: int) -> Tuple[float, float]:
    rechts_ = 3445873.97+((col_-1)*100.)+50.
    hoch_ = 5527357.03+((405-row_)*100.)+50.
    return rechts_, hoch_


def read_bfiraster(filepath: str) -> numpy.ndarray:
    with open(filepath) as file_:
        lines = file_.readlines()
    ncols = int(lines[0].split()[-1])
    nrows = int(lines[1].split()[-1])
    nodata = float(lines[5].split()[-1])
    bfiraster_ = numpy.full((nrows, ncols), numpy.nan, dtype=float)
    for i, line in enumerate(lines[6:]):
        for j, value in enumerate(line.split()):
            bfiraster_[i, j] = float(value)
    bfiraster_[bfiraster_ == nodata] = numpy.nan
    return bfiraster_


bfiraster = read_bfiraster(filepath_bfiraster)

hydpy.pub.timegrids = '1959-12-31', '1960-01-01', '1d'
for idx in range(len(table_knoteneigenschaften)):

    row = getattr(table_knoteneigenschaften, '/row')[idx]
    col = getattr(table_knoteneigenschaften, 'column')[idx]
    name = f'{str(row).zfill(3)}_{str(col).zfill(3)}'
    precnode = hydpy.Node(f'P_{name}', variable=whmod_inputs.Niederschlag)
    precselection_raster.nodes.add_device(precnode)
    tempnode = hydpy.Node(f'T_{name}', variable=whmod_inputs.Temp_TM)
    tempselection_raster.nodes.add_device(tempnode)
    evapnode = hydpy.Node(f'E_{name}', variable=whmod_inputs.ET0)
    petselection_raster.nodes.add_device(evapnode)
    raster = hydpy.Element(
        f'WHMod_{name}',
        inputs=(precnode, tempnode, evapnode),
    )
    whmodselection.elements.add_device(raster)
    rechts, hoch = calculate_coordinates(row_=row, col_=col)
    for node in (precnode, tempnode, evapnode):
        node.rechts = rechts
        node.hoch = hoch

    whmod = hydpy.prepare_model(whmod_v3, '1d')
    raster.model = whmod
    con = whmod.parameters.control
    hrus = collect_hrus(table_knoteneigenschaften, idx)
    con.area(sum(value for value in hrus.values()))
    con.nmb_cells(len(hrus))
    con.mitfunktion_kapillareraufstieg(True)
    con.nutz_nr(
        [whmod_v3.CONSTANTS[key.split('_')[0].split(':')[1].upper()]
         for key in hrus.keys()])
    con.maxinterz(gras=[0.4, 0.4, 0.6, 0.8, 1.0, 1.0,
                        1.0, 1.0, 1.0, 0.6, 0.5, 0.4],
                  laubwald=[0.1, 0.1, 0.3, 0.8, 1.4, 2.2,
                            2.4, 2.4, 2.2, 1.6, 0.3, 0.1],
                  mais=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
                        0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
                  nadelwald=[2.2, 2.2, 2.2, 2.2, 2.2, 2.2,
                             2.2, 2.2, 2.2, 2.2, 2.2, 2.2],
                  sommerweizen=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
                                0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
                  winterweizen=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
                                0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
                  zuckerrueben=[0.08, 0.08, 0.06, 0.14, 0.6, 1.04,
                                0.92, 0.62, 0.26, 0.04, 0.0, 0.0],
                  versiegelt=[2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
                              2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                  wasser=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    con.bodentyp(whmod_v3.SAND_BINDIG)
    ackerland = [0.733, 0.733, 0.774, 0.947, 1.188, 1.181,
                 # DWA-M 504: Ackerland
                 1.185, 1.151, 0.974, 0.853, 0.775, 0.733]
    con.fln(
        gras=1.0,  # DWA-M 504
        laubwald=[1.003, 1.003, 1.053, 1.179, 1.114, 1.227,
                  1.241, 1.241, 1.241, 1.139, 1.082, 1.003],  # DWA-M 504
        mais=ackerland,
        nadelwald=1.335,  # DWA-M 504
        sommerweizen=ackerland,
        winterweizen=ackerland,
        zuckerrueben=ackerland,
        versiegelt=0.0,
        wasser=[1.165, 1.217, 1.256, 1.283, 1.283, 1.296,
                1.283, 1.283, 1.270, 1.230, 1.165, 1.139])  # DWA-M 504
    con.f_area(list(hrus.values()))
    con.gradfaktor(4.5)
    con.nfk100_mittel(
        [float(key.split('_')[3].split(':')[1]) for key in hrus.keys()])
    con.flurab([float(key.split('_')[1].split(':')[1]) for key in hrus.keys()])
    con.maxwurzeltiefe(
        gras=0.6, laubwald=1.5, nadelwald=1.5, mais=1.0, sommerweizen=1.0,
        winterweizen=1.0, zuckerrueben=0.8, versiegelt=0.0, wasser=0.0)
    con.minhasr(
        gras=4.0, laubwald=6.0, mais=3.0, nadelwald=6.0, sommerweizen=6.0,
        winterweizen=6.0, zuckerrueben=6.0, versiegelt=1.0, wasser=1.0)
    con.kapilschwellwert(
        sand=0.8, sand_bindig=1.4, lehm=1.4, ton=1.35, schluff=1.75, torf=0.85)
    con.kapilgrenzwert(
        sand=0.4, sand_bindig=0.85, lehm=0.45, ton=0.25, schluff=0.75,
        torf=0.55)
    con.bfi(bfiraster[row-1, col-1])

    whmod.sequences.states.interzeptionsspeicher(0.0)
    whmod.sequences.states.schneespeicher(0.0)
    whmod.sequences.states.aktbodenwassergehalt(
        0.5*whmod.parameters.control.nfk100_mittel.values)


# Evap-Modelle initialisieren

path_dwdliste = os.path.join(folder_metinput, filename_dwdliste)
path_metstationinfo = os.path.join(folder_metinput, filename_metstationinfo)
path_precstationinfo = os.path.join(folder_metinput, filename_precstationinfo)

hydpy.pub.timegrids = '1960-01-01', '2016-01-01', '1d'


def read_series(filename, stat_):
    filepath = os.path.join(folder_metinput, filename)
    date2value = {}
    with open(filepath) as file_:
        for line_ in file_:
            _, stat__, date, value = line_.split()
            if stat_ == stat__:
                date2value[date] = float(value)
    values = []
    for date in hydpy.pub.timegrids.init:
        datestring = date.to_string(style='din1')[:10]
        value = date2value.get(datestring, numpy.nan)
        values.append(value)
    return values


stat2latlong: Dict[str, Tuple[float, float]] = {}
with open(path_dwdliste) as dwdfile:
    for line in dwdfile.readlines()[2:]:
        line = line.strip()
        if not line:
            continue
        stat = line[55:62].strip()
        kenn = line[53:56]
        lat = float(line[62:70])
        long = float(line[71:80])
        if kenn.strip() not in ('KL', 'RR'):
            continue
        if not ((49.5 < lat < 50.5) and (8.0 < long < 9.0)):
            continue
        if stat in stat2latlong and stat2latlong[stat] != (lat, long):
            raise RuntimeError(f'wrong duplicate {stat}, see line {line}')
        stat2latlong[stat] = lat, long

with open(path_metstationinfo) as metstationinfofile:
    for line in metstationinfofile.readlines()[1:]:
        line = line.strip()
        if not line:
            continue
        stat, rechts, hoch = line.split()[1:4]
        node = hydpy.Node(f'E_{stat}', variable='E')
        element = hydpy.Element(f'Evap_{stat}', outlets=node)
        evap = hydpy.prepare_model('evap_v001', '1d')
        element.model = evap
        petselection_stat.nodes.add_device(node)
        petselection_stat.elements.add_device(element)

        con = evap.parameters.control
        try:
            lat, long = stat2latlong[stat]
        except KeyError:
            lat, long = stat2latlong[f'0{stat}']
        node.lat = lat
        node.long = long
        node.rechts = float(rechts)
        node.hoch = float(hoch)
        con.latitude(lat)
        con.longitude(long)
        con.measuringheightwindspeed(10.0)
        con.angstromconstant(0.25)
        con.angstromfactor(0.5)
        evap.parameters.update()

        evap.sequences.logs.loggedglobalradiation(0.0)
        evap.sequences.logs.loggedclearskysolarradiation(0.0)

        inp = evap.sequences.inputs
        inp.activate_ram()
        inp.airtemperature.series = read_series(
            filename_airtemperature, stat)
        inp.airtemperature.series /= 10
        inp.relativehumidity.series = read_series(
            filename_relativehumidity, stat)
        inp.windspeed.series = read_series(
            filename_windspeed_modified, stat)
        inp.windspeed.series /= 10
        inp.sunshineduration.series = read_series(
            filename_sunshineduration, stat)
        inp.sunshineduration.series /= 10
        inp.atmosphericpressure.series = 100.1

        node = hydpy.Node(f'T_{stat}', variable='T')
        tempselection_stat.nodes.add_device(node)
        node.lat = lat
        node.long = long
        node.rechts = float(rechts)
        node.hoch = float(hoch)
        node.prepare_simseries()
        node.sequences.sim.series = inp.airtemperature.series


with open(path_precstationinfo) as precstationinfofile:
    for line in precstationinfofile.readlines()[1:]:
        line = line.strip()
        if not line:
            continue
        stat, rechts, hoch = line.split()[1:4]
        node = hydpy.Node(f'P_{stat}', variable='P')
        precselection_stat.nodes.add_device(node)
        node.rechts = float(rechts)
        node.hoch = float(hoch)
        node.prepare_simseries()
        node.sequences.sim.series = read_series(
            filename_precipitation, stat)
        node.sequences.sim.series /= 10


# Conv-Modelle für Interpolationen initialisieren

def get_coordinatedict(nodes):
    return {n.name: (n.rechts, n.hoch) for n in nodes}


conv_pet = hydpy.prepare_model('conv_v002')
conv_pet.parameters.control.inputcoordinates(
    **get_coordinatedict(petselection_stat.nodes)
)
conv_pet.parameters.control.outputcoordinates(
    **get_coordinatedict(petselection_raster.nodes)
)
conv_pet.parameters.control.maxnmbinputs()
conv_pet.parameters.control.power(2.0)
element = hydpy.Element(
    'ConvPET',
    inlets=petselection_stat.nodes,
    outlets=petselection_raster.nodes,
)
element.model = conv_pet
petselection_stat.elements.add_device(element)

conv_temp = hydpy.prepare_model('conv_v002')
conv_temp.parameters.control.inputcoordinates(
    **get_coordinatedict(tempselection_stat.nodes)
)
conv_temp.parameters.control.outputcoordinates(
    **get_coordinatedict(tempselection_raster.nodes)
)
conv_temp.parameters.control.maxnmbinputs()
conv_temp.parameters.control.power(2.0)

element = hydpy.Element(
    'ConvTemp',
    inlets=tempselection_stat.nodes,
    outlets=tempselection_raster.nodes,
)
element.model = conv_temp
tempselection_stat.elements.add_device(element)

conv_prec = hydpy.prepare_model('conv_v002')
conv_prec.parameters.control.inputcoordinates(
    **get_coordinatedict(precselection_stat.nodes)
)
conv_prec.parameters.control.outputcoordinates(
    **get_coordinatedict(precselection_raster.nodes)
)
conv_prec.parameters.control.maxnmbinputs()
conv_prec.parameters.control.power(2.0)
element = hydpy.Element(
    'ConvPrec',
    inlets=precselection_stat.nodes,
    outlets=precselection_raster.nodes,
)
element.model = conv_prec
precselection_stat.elements.add_device(element)

# Alles abspeichern

hp = hydpy.HydPy('AnalyseWHMod')

hydpy.pub.selections = hydpy.Selections(
    whmodselection,
    petselection_stat, petselection_raster,
    tempselection_stat, tempselection_raster,
    precselection_stat, precselection_raster,
)
complete = hydpy.Selection('nördliches_hessisches_Ried')
for selection in hydpy.pub.selections:
    complete += selection
hydpy.pub.networkmanager.save_files(hydpy.Selections(complete))
hp.update_devices(complete)
hp.save_controls()
hp.save_conditions()
hydpy.pub.sequencemanager.generalfiletype = 'asc'
#hydpy.pub.sequencemanager.generalfiletype = 'nc'
#hydpy.pub.sequencemanager.open_netcdfwriter()
hp.save_inputseries()
hp.save_simseries()
#hydpy.pub.sequencemanager.close_netcdfwriter()
os.rename(r'AnalyseWHMod\conditions\init_2016_01_01_00_00_00',
          r'AnalyseWHMod\conditions\init_1960_01_01_00_00_00')
