# -*- coding: utf-8 -*-

from hydpy.models.hland_96 import *
from hydpy.models import evap_aet_hbv96
from hydpy.models import evap_pet_hbv96
from hydpy.models import rconc_uh

simulationstep("1h")
parameterstep("1d")

area(1733.0)
nmbzones(14)
sclass(1)
zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD,
         FOREST, FIELD, FOREST, FOREST, FOREST)
zonearea(213.62, 56.98, 308.62, 304.89, 163.41, 320.46, 105.06, 176.22,
         9.83, 57.47, 0.2, 11.75, 3.55, 0.94)
zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0, 8.0, 9.0)
psi(1.0)
pcorr(auxfile="land")
pcalt(0.1)
rfcf(0.8)
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
fc(219.0)
beta(1.51551)
percmax(1.25686)
cflux(0.0)
resparea(auxfile="land")
recstep(1200.0)
alpha(auxfile="land")
k(0.002571233607305936)
k4(0.04087)
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
    uh("triangle", tb=0.54769)
