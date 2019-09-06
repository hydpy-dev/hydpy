# -*- coding: utf-8 -*-

from hydpy import Node, Element


Element("stream_dill_lahn_2",
        inlets="dill",
        outlets="lahn_2",
        keywords=['river'])

Element("stream_lahn_1_lahn_2",
        inlets="lahn_1",
        outlets="lahn_2",
        keywords=['river'])

Element("stream_lahn_2_lahn_3",
        inlets="lahn_2",
        outlets="lahn_3",
        keywords=['river'])