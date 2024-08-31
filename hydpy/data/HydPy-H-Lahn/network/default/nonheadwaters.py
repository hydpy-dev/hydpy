# -*- coding: utf-8 -*-

from hydpy import Node, Element


Node("lahn_leun", variable="Q", keywords=["gauge"])

Node("lahn_kalk", variable="Q", keywords=["gauge"])


Element("land_lahn_leun", outlets="lahn_leun", keywords=["catchment"])

Element("land_lahn_kalk", outlets="lahn_kalk", keywords=["catchment"])
