# -*- coding: utf-8 -*-

from hydpy import Node, Element


Node("dill", variable="Q")

Node("lahn_1", variable="Q")

Node("lahn_2", variable="Q")

Node("lahn_3", variable="Q")


Element("land_dill",
        outlets="dill")

Element("land_lahn_1",
        outlets="lahn_1")

Element("land_lahn_2",
        outlets="lahn_2")

Element("land_lahn_3",
        outlets="lahn_3")

Element("stream_dill_lahn_2",
        inlets="dill",
        outlets="lahn_2")

Element("stream_lahn_1_lahn_2",
        inlets="lahn_1",
        outlets="lahn_2")

Element("stream_lahn_2_lahn_3",
        inlets="lahn_2",
        outlets="lahn_3")
