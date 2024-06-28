# -*- coding: utf-8 -*-

from hydpy import Node, Element


Node("dill", variable="Q", keywords=["gauge"])

Node("lahn_1", variable="Q", keywords=["gauge"])


Element("land_dill", outlets="dill", keywords=["catchment"])

Element("land_lahn_1", outlets="lahn_1", keywords=["catchment"])
