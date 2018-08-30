# -*- coding: utf-8 -*-
"""

>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

>>> from hydpy import HydPy, pub, Timegrid, Timegrids, TestIO
>>> hp = HydPy('LahnHBV')
>>> pub.timegrids = Timegrids(Timegrid('1996-01-01 00:00:00',
...                                    '1996-01-06 00:00:00',
...                                    '1d'))
>>> pub.sequencemanager.generalfiletype = 'nc'

>>> pub.options.printprogress = False   # ToDo
>>> import warnings   # ToDo
>>> warnings.filterwarnings('ignore', 'Note that,')   # ToDo

>>> with TestIO():
...     hp.prepare_network()
...     hp.init_models()
...     hp.load_conditions()
...     hp.prepare_inputseries()
...     pub.sequencemanager.open_netcdf_reader(isolate=True)
...     hp.load_inputseries()
...     pub.sequencemanager.close_netcdf_reader()
...     hp.prepare_simseries()
...     hp.prepare_stateseries()
...     hp.doit()
...     pub.sequencemanager.open_netcdf_writer(isolate=True, flatten=True)
...     hp.save_simseries()
...     hp.save_stateseries()
...     pub.sequencemanager.close_netcdf_writer()

>>> from hydpy.core.netcdftools import netcdf4, chars2str, query_variable
>>> with TestIO():
...     ncfile = netcdf4.Dataset('LahnHBV/sequences/node/node_sim_q.nc')
>>> chars2str(query_variable(ncfile, 'station_names'))
['dill', 'lahn_1', 'lahn_2', 'lahn_3']
>>> all(query_variable(ncfile, 'sim_q')[1] == hp.nodes.lahn_1.sequences.sim.series)
True

>>> with TestIO():
...     ncfile = netcdf4.Dataset('LahnHBV/sequences/output/hland_v1_state_sm.nc')
>>> chars2str(query_variable(ncfile, 'station_names'))[:3]
['land_dill_0', 'land_dill_1', 'land_dill_2']
>>> all(query_variable(ncfile, 'state_sm')[2] == hp.elements.land_dill.model.sequences.states.sm.series[:, 2])
True

"""
# import...
# ...from standard library
import xml.etree.ElementTree as elementtree
# ...from HydPy


