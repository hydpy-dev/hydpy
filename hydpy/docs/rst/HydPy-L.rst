
.. _`LARSIM`: http://www.larsim.de/en/the-model/
.. _`German Federal Institute of Hydrology (BfG)`: https://www.bafg.de/EN
.. _Bremicker: http://www.larsim.info/fileadmin/files/Dokumentation/FSH-Bd11-Bremicker.pdf
.. _LARSIM-Entwicklergemeinschaft: http://www.larsim.info/fileadmin/files/Dokumentation/LARSIM-Dokumentation.pdf
.. _LARSIM Online-Hilfe: http://www.larsim.info/larsim-hilfe/
.. _KLIWAS: http://www.kliwas.de/KLIWAS/DE/Service/Downloads/Publikationen/abschlussbericht.pdf;jsessionid=C89ED85DF782A3D5FE117808A6129002.live21303?__blob=publicationFile

.. _HydPy-L:

HydPy-L (LARSIM)
================

*HydPy* implements a close but not exact emulation of the central routines of the
`LARSIM`_ model, applied by many forecasting centres in Germany and some neighbouring
countries.  The version 1 application model of *HydPy-L* agrees very well with a LARSIM
configuration called LARSIM-ME ("ME" stands for Middle Europe), used by the `German
Federal Institute of Hydrology (BfG)`_ for calculating hydroclimatic scenarios for
large river basins (see e. g. the `KLIWAS`_ project).

*HydPy-L* is partly based on the original publication on LARSIM (`BREMICKER`_), the
summary of the theory and the range of applications of LARSIM, which is continuously
updated by the LARSIM development community (`LARSIM-Entwicklergemeinschaft`_), the
LARSIM online documentation (`LARSIM Online-Hilfe`_), and some helpful hints of the
colleagues of the LUBW (Landesanstalt für Umwelt, Messungen und Naturschutz
Baden-Württemberg) and the HYDRON GmbH.  Some other parts of *HydPy-L* have been
programmed more independently and were incorporated into the original LARSIM
implementation later.

Available models:

.. toctree::
   :maxdepth: 1

   lland
   lland_dd
   lland_knauf
   lland_knauf_ic

For reasons of consistency with the original LARSIM implementation, the names of all
parameter and sequence classes are German terms and abbreviations.  Additionally, the
documentation on each parameter or sequence contains an English translation.
