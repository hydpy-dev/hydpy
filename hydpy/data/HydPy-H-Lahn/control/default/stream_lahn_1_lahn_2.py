# -*- coding: utf-8 -*-

from hydpy.models.musk_classic import *

simulationstep("1h")
parameterstep("1d")

nmbsegments(lag=0.583)
coefficients(damp=0.0)
