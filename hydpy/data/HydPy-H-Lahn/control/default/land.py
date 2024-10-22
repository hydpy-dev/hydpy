from hydpy.models.hland_96 import *

simulationstep("1h")
parameterstep("1d")

pcorr(1.0)
icmax(field=1.0, forest=1.5)
resparea(True)
alpha(1.0)
