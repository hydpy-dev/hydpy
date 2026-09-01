from hydpy.models.hland_96 import *
from hydpy.models import evap_aet_hbv96
from hydpy.models import evap_pet_hbv96
from hydpy.models import rconc_uh

simulationstep("1h")
parameterstep("1d")

area(1660.2)
nmbzones(13)
zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD,
         FOREST, FIELD, FOREST, FOREST)
zonearea(25.61, 1.9, 467.41, 183.0, 297.12, 280.53, 81.8, 169.66, 36.0,
         100.83, 2.94, 11.92, 1.48)
psi(1.0)
zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0, 8.0)
pcorr(auxfile="land")
pcalt(0.1)
rfcf(0.885)
sfcf(1.3203)
tcorr(0.0)
tcalt(0.6)
icmax(auxfile="land")
tt(0.59365)
ttint(2.0)
dttm(0.0)
gmelt(0.0)
gvar(0.0)
fc(206.0)
beta(1.45001)
percmax(1.02978)
cflux(0.0)
resparea(auxfile="land")
recstep(1200.0)
alpha(auxfile="land")
k(0.0053246701322556935)
k4(0.0413)
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
with model.add_snowmodel_v1("snow_dd"):
    numberdivisions(1)
    temperatureaddend(0.0)
    lapserate(0.6)
    rainsnowthreshold(0.59365)
    rainsnowinterval(2.0)
    throughfalldistribution(1.0)
    degreedaythreshold(0.59365)
    degreedayfactor(field=5.0, forest=3.0)
    degreedayvariability(0.0)
    freezingfactor(0.05)
    watercapacity(0.1)
    snowpacklimit(inf)
    redistributionpaths(0.0)
with model.add_rconcmodel_v1(rconc_uh):
    uh("triangle", tb=0.80521)
