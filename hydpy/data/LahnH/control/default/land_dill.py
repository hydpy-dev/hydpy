# -*- coding: utf-8 -*-

from hydpy.models.hland_v1 import *

simulationstep("1h")
parameterstep("1d")

area(692.3)
nmbzones(12)
sclass(1)
zonetype(
    FIELD,
    FOREST,
    FIELD,
    FOREST,
    FIELD,
    FOREST,
    FIELD,
    FOREST,
    FIELD,
    FOREST,
    FIELD,
    FOREST,
)
zonearea(
    14.41, 7.06, 70.83, 84.36, 70.97, 198.0, 27.75, 130.0, 27.28, 56.94, 1.09, 3.61
)
psi(1.0)
zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0)
zrelp(3.75)
zrelt(3.75)
zrele(3.665)
pcorr(auxfile="land")
pcalt(0.1)
rfcf(1.04283)
sfcf(1.1)
tcalt(0.6)
ecorr(1.0)
ecalt(0.0)
epf(0.02)
etf(0.1)
ered(0.0)
ttice(nan)
icmax(auxfile="land")
sfdist(1.0)
smax(inf)
sred(0.0)
tt(0.55824)
ttint(2.0)
dttm(0.0)
cfmax(field=4.55853, forest=2.735118)
cfvar(0.0)
gmelt(0.0)
gvar(0.0)
cfr(0.05)
whc(0.1)
fc(278.0)
lp(0.9)
beta(2.54011)
percmax(1.39636)
cflux(0.0)
resparea(auxfile="land")
recstep(1200.0)
alpha(auxfile="land")
k(0.005617743528874685)
k4(0.05646)
gamma(0.0)
maxbaz(0.36728)
