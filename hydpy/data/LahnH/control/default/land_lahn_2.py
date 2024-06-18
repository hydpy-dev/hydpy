# -*- coding: utf-8 -*-

from hydpy.models.hland_96 import *
from hydpy.models import evap_aet_hbv96
from hydpy.models import evap_pet_hbv96
from hydpy.models import rconc_uh

simulationstep("1h")
parameterstep("1d")

area(1212.5)
nmbzones(10)
sclass(1)
zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD,
         FOREST)
zonearea(188.3, 29.92, 396.94, 297.94, 82.69, 180.62, 3.91, 28.8, 0.61, 2.77)
zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0)
psi(1.0)
pcorr(auxfile="land")
pcalt(0.1)
rfcf(1.21132)
sfcf(1.1)
tcorr(0.0)
tcalt(0.6)
icmax(auxfile="land")
sfdist(1.0)
smax(inf)
sred(0.0)
tt(0.0)
ttint(2.0)
dttm(0.0)
cfmax(field=3.5, forest=2.1)
cfvar(0.0)
gmelt(0.0)
gvar(0.0)
cfr(0.05)
whc(0.1)
fc(197.0)
beta(2.5118)
percmax(1.17386)
cflux(0.0)
resparea(auxfile="land")
recstep(1200.0)
alpha(auxfile="land")
k(0.0059480964539007095)
k4(0.03402)
gamma(0.0)
with model.add_aetmodel_v1(evap_aet_hbv96):
    temperaturethresholdice(nan)
    soilmoisturelimit(0.9)
    excessreduction(0.0)
    with model.add_petmodel_v1(evap_pet_hbv96):
        airtemperaturefactor(0.1)
        altitudefactor(0.0)
        precipitationfactor(0.02)
        evapotranspirationfactor(1.0)
with model.add_rconcmodel_v1(rconc_uh):
    uh("triangle", tb=1.02427)
