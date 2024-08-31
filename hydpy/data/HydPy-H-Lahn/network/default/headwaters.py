# -*- coding: utf-8 -*-

from hydpy import Node, Element


Node("dill_assl", variable="Q", keywords=["gauge"])

Node("lahn_marb", variable="Q", keywords=["gauge"])


Element("land_dill_assl", outlets="dill_assl", keywords=["catchment"])

Element("land_lahn_marb", outlets="lahn_marb", keywords=["catchment"])
