from hydpy.models.hland_96 import *
from hydpy.models import evap_aet_hbv96
from hydpy.models import evap_pet_hbv96
from hydpy.models import rconc_uh

simulationstep("1h")
parameterstep("1d")

area(692.3)
nmbzones(12)
zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD,
         FOREST, FIELD, FOREST)
zonearea(14.41, 7.06, 70.83, 84.36, 70.97, 198.0, 27.75, 130.0, 27.28,
         56.94, 1.09, 3.61)
psi(1.0)
zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0)
pcorr(auxfile="land")
pcalt(0.1)
rfcf(1.04283)
sfcf(1.1)
tcorr(0.0)
tcalt(0.6)
icmax(auxfile="land")
tt(0.55824)
ttint(2.0)
dttm(0.0)
gmelt(0.0)
gvar(0.0)
fc(278.0)
beta(2.54011)
percmax(1.39636)
cflux(0.0)
resparea(auxfile="land")
recstep(1200.0)
alpha(auxfile="land")
k(0.005617743528874685)
k4(0.05646)
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
    rainsnowthreshold(0.55824)
    rainsnowinterval(2.0)
    throughfalldistribution(1.0)
    degreedaythreshold(0.55824)
    degreedayfactor(field=4.55853, forest=2.735118)
    degreedayvariability(0.0)
    freezingfactor(0.05)
    watercapacity(0.1)
    snowpacklimit(inf)
    redistributionpaths(0.0)
with model.add_rconcmodel_v1(rconc_uh):
    uh("triangle", tb=0.36728)
