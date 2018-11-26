# -*- coding: utf-8 -*-

from hydpy import Node, Element


Node("lahn_2", variable="Q",
     keywords=['gauge'])

Node("lahn_3", variable="Q",
     keywords=['gauge'])


Element("land_lahn_2",
        outlets="lahn_2",
        keywords=['catchment'])

Element("land_lahn_3",
        outlets="lahn_3",
        keywords=['catchment'])