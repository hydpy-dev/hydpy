
.. _Bremicker (2000): http://www.larsim.info/fileadmin/files/Dokumentation/FSH-Bd11-Bremicker.pdf
.. _LARSIM-Entwicklergemeinschaft: http://www.larsim.info/fileadmin/files/Dokumentation/LARSIM-Dokumentation.pdf
.. _LARSIM Online-Hilfe: http://www.larsim.info/larsim-hilfe/
.. _KLIWAS: http://www.kliwas.de/KLIWAS/DE/Service/Downloads/Publikationen/abschlussbericht.pdf;jsessionid=C89ED85DF782A3D5FE117808A6129002.live21303?__blob=publicationFile

.. _HydPy-L:

HydPy-L (LARSIM)
================

HydPy implements a close emulation of the central routines of the LARSIM
model, which is applied by many forecasting centres in Germany and
some neighbouring countries.  The version 1 application models of HydPy-L
agree very well with a LARSIM configuration called LARSIM-ME (Middle Europe),
being used by the German Federal Institute of Germany (BfG) for calculating
hydroclimatic scenarios for large river basins (see e.g. the `KLIWAS`_
project).  HydPy-L is partly based on the original publication on
LARSIM (`BREMICKER (2000)`_), the summary of the theory and the range of
applications of LARSIM, which is continuously updated by the LARSIM
development community (`LARSIM-Entwicklergemeinschaft`_), the LARSIM online
documentation (`LARSIM Online-Hilfe`_), and some useful hints of the
colleagues of the LUBW (Landesanstalt für Umwelt, Messungen und Naturschutz
Baden-Württemberg) and the HYDRON GmbH.  Some other parts of HydPy-L
have been programmed more independently and were incorporated into the
original LARSIM implementation later.


HydPy-L is divided into three base models, which can be used to compile
different application models:

.. toctree::
   :maxdepth: 1

   HydPy-L-Land
   HydPy-L-Stream
   HydPy-L-Lake


So far the following application models are compiled:

.. toctree::

   lland_v1 (LARSIM-Xinanjiang-Turc-Wendling version of HydPy-L-Land) <lland_v1>
   lland_v2 (External potential evaporation version of lland_v1) <lland_v2>
   lstream_v1 (LARSIM-Manning version of HydPy-L-Stream) <lstream_v1>
   llake_v1 (LARSIM-Lake version of HydPy-L-Branch) <llake_v1>

All these application models are stand-alone models, which can be
combined freely with other models implemented in HydPy.

For reason of consistency with the original LARSIM implementation, the
names of all parameter and sequence classes are German terms and abbreviations.
However, the documentation on each parameter or sequence contains an English
translation.