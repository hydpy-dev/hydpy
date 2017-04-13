# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 11:54:28 2017

@author: Wuestenfeld
"""
from __future__ import division, print_function
from hydpy import pub
from hydpy.models.globwat import *
parameterstep()

""" Werte sind noch frei erfunden """
scmax.shape = (2,3)
scmax(3.)

""" Werte sind noch frei erfunden """
rtd.shape = (2,3)
rtd(.6)

""" Werte sind noch frei erfunden """
irra.shape = (1)
irra(4.)

""" Werte sind noch frei erfunden """
ta.shape = (1)
ta(5.)

kc.shape = 14, 12
kc(radrytrop=(90,90,90,90,90,90,90,90,90,90,90,90))
kc(rahumtrop=(100,100,100,100,100,100,100,100,100,100,100,100))
kc(rahighl=(90,90,90,90,90,90,90,90,90,90,90,90))
kc(rasubtrop=(100,100,100,100,100,100,100,100,100,100,100,100))
kc(ratemp=(100,100,100,100,100,100,100,100,100,100,100,100))
kc(rlsubtrop=(80,80,80,80,80,80,80,80,80,80,80,80))
kc(rltemp=(90,90,90,90,90,90,90,90,90,90,90,90))
kc(rlboreal=(80,80,80,80,80,80,80,80,80,80,80,80))
kc(forest=(110,110,110,110,110,110,110,110,110,110,110,110))
kc(desert=(70,70,70,70,70,70,70,70,70,70,70,70))
kc(water=(100,100,100,100,100,100,100,100,100,100,100,100))
kc(irrcpr=(100,100,100,100,100,100,100,100,100,100,100,100))
kc(irrcnpr=(100,100,100,100,100,100,100,100,100,100,100,100))
kc(other=(100,100,100,100,100,100,100,100,100,100,100,100))

pub.indexer.monthofyear = [1,2,3]

model.parameters.update()
""" mit diesem Befehl werden alle abgeleiteten Parameter berechnet, die in globwat-derived angelegt sind """


