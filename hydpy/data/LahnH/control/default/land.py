# -*- coding: utf-8 -*-

from hydpy.models.hland_v1 import *

simulationstep("1h")
parameterstep("1d")

pcorr(1.0)
icmax(field=1.0, forest=1.5)
resparea(True)
alpha(1.0)
