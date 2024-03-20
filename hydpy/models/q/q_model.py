# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.cythons import smoothutils
from hydpy.interfaces import dischargeinterfaces

# ...from q
from hydpy.models.q import q_control
from hydpy.models.q import q_derived


class Calculate_Discharge_V1(modeltools.Method):
    r"""Calculate the discharge based on the water depth given in m according to
    :cite:t:`ref-Brauer2014` and return it in mm/T.

    Basic equation (discontinuous):
      .. math::
        q = q_{max} \cdot \left( \frac{max(h-h_{max}, \ 0)}{h_{max}-h_{min}} \right)^x
        \\ \\
        q = Discharge \\
        q_{max} = BankfullDischarge \\
        h = waterdepth \\
        h_{max} = ChannelDepth \\
        h_{min} = CrestHeight \\
        x = DischargeExponent

    Examples:

        >>> from hydpy.models.q_walrus import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> channeldepth(5.0)
        >>> crestheight(2.0)
        >>> bankfulldischarge(2.0)
        >>> dischargeexponent(2.0)
        >>> from hydpy import round_
        >>> hs = 1.0, 1.9, 2.0, 2.1, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0

        Without smoothing:

        >>> crestheighttolerance(0.0)
        >>> derived.crestheightregularisation.update()
        >>> for h in hs:
        ...     round_([h, model.calculate_discharge_v1(h)])
        1.0, 0.0
        1.9, 0.0
        2.0, 0.0
        2.1, 0.001111
        3.0, 0.111111
        4.0, 0.444444
        5.0, 1.0
        6.0, 1.777778
        7.0, 2.777778
        8.0, 4.0

        Without smooting:

        >>> crestheighttolerance(0.1)
        >>> derived.crestheightregularisation.update()
        >>> for h in hs:
        ...     round_([h, model.calculate_discharge_v1(h)])
        1.0, 0.0
        1.9, 0.0
        2.0, 0.00001
        2.1, 0.001111
        3.0, 0.111111
        4.0, 0.444444
        5.0, 1.0
        6.0, 1.777778
        7.0, 2.777778
        8.0, 4.0
    """

    CONTROLPARAMETERS = (
        q_control.ChannelDepth,
        q_control.CrestHeight,
        q_control.BankfullDischarge,
        q_control.DischargeExponent,
    )
    DERIVEDPARAMETERS = (q_derived.CrestHeightRegularisation,)

    @staticmethod
    def __call__(model: modeltools.Model, waterdepth: float) -> float:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess

        h: float = smoothutils.smooth_logistic2(
            waterdepth - con.crestheight, der.crestheightregularisation
        )
        f: float = (h / (con.channeldepth - con.crestheight)) ** con.dischargeexponent
        return con.bankfulldischarge * f


class Model(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """The HydPy-Q base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = ()
    INTERFACE_METHODS = (Calculate_Discharge_V1,)
    ADD_METHODS = ()
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


class Base_DischargeModel_V2(dischargeinterfaces.DischargeModel_V2):
    """Base class for HydPy-Q models that comply with the |DischargeModel_V2| submodel
    interface."""

    @importtools.define_targetparameter(q_control.ChannelDepth)
    def prepare_channeldepth(self, channeldepth: float) -> None:
        """Set the channel depth in m.

        >>> from hydpy.models.q_walrus import *
        >>> parameterstep()
        >>> model.prepare_channeldepth(2.0)
        >>> channeldepth
        channeldepth(2.0)
        """
        self.parameters.control.channeldepth(channeldepth)

    @importtools.define_targetparameter(q_control.CrestHeightTolerance)
    def prepare_tolerance(self, tolerance: float) -> None:
        """Set the depth-related smoothing parameter in m.

        >>> from hydpy.models.q_walrus import *
        >>> parameterstep()
        >>> model.prepare_tolerance(2.0)
        >>> crestheighttolerance
        crestheighttolerance(2.0)
        """
        self.parameters.control.crestheighttolerance(tolerance)
