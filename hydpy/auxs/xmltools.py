# -*- coding: utf-8 -*-
"""

>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

>>> from hydpy import HydPy, pub, TestIO, XMLInterface
>>> hp = HydPy('LahnHBV')
>>> with TestIO():
...     xml = XMLInterface()
>>> pub.timegrids = xml.timegrids
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

>>> xml.prepare_series()

>>> hp.doit()

>>> with TestIO():
...     xml.save_series()

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
import os
from xml.etree import ElementTree
# ...from HydPy
from hydpy import pub
from hydpy.core import timetools

namespace = \
    '{https://github.com/tyralla/hydpy/tree/master/hydpy/conf/HydPy2FEWS.xsd}'

class XMLInterface(object):

    def __init__(self, filepath=None):
        if filepath is None:
            filepath = os.path.join(pub.projectname, 'config.xml')
        self.root = ElementTree.parse(filepath).getroot()

    def find(self, name):
        return self.root.find(f'{namespace}{name}')

    @property
    def timegrids(self):
        """The |Timegrids| object defined in the actual xml file.

        >>> from hydpy.auxs.xmltools import XMLInterface
        >>> from hydpy import data
        >>> xml = XMLInterface(data.get_path('LahnHBV', 'config.xml'))
        >>> xml.timegrids
        Timegrids(Timegrid('1996-01-01T00:00:00',
                           '1996-01-06T00:00:00',
                           '1d'))
        """
        timegrid_xml = (self.find('timegrid'))
        timegrid = timetools.Timegrid(
            *(timegrid_xml[idx].text for idx in range(3)))
        return timetools.Timegrids(timegrid)


