# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.core import parametertools


class Nmb(parametertools.Parameter):
    """Number of response functions [-]."""
    NDIM, TYPE, TIME, SPAN = 0, int, None, (0, None)

    def update(self):
        """Determine the number of response functions.

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.nmb.update()
        >>> derived.nmb
        nmb(2)

        Note that updating parameter `nmb` sets the shape of the flux
        sequences |QPIn|, |QPOut|, |QMA|, and |QAR| automatically.

        >>> fluxes.qpin
        qpin(nan, nan)
        >>> fluxes.qpout
        qpout(nan, nan)
        >>> fluxes.qma
        qma(nan, nan)
        >>> fluxes.qar
        qar(nan, nan)
        """
        pars = self.subpars.pars
        responses = pars.control.responses
        fluxes = pars.model.sequences.fluxes
        self.value = len(responses)
        fluxes.qpin.shape = self.value
        fluxes.qpout.shape = self.value
        fluxes.qma.shape = self.value
        fluxes.qar.shape = self.value


class MaxQ(parametertools.Parameter):
    """Maximum discharge values of the respective ARMA models [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def update(self):
        """Determine the maximum discharge values.

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.maxq.update()
        >>> derived.maxq
        maxq(0.0, 3.0)
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)
        self.value = responses.thresholds


class DiffQ(parametertools.Parameter):
    """Differences between the values of |MaxQ| [m³/s]."""
    NDIM, TYPE, TIME, SPAN = 1, float, None, (0, None)

    def update(self):
        """Determine the "max Q deltas".

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.diffq.update()
        >>> derived.diffq
        diffq(3.0)
         >>> responses(((1., 2.), (1.,)))
        >>> derived.diffq.update()
        >>> derived.diffq
        diffq([])
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)-1
        self.value = numpy.diff(responses.thresholds)


class AR_Order(parametertools.Parameter):
    """Number of AR coefficients of the different responses [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, None)

    def update(self):
        """Determine the total number of AR coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ar_order.update()
        >>> derived.ar_order
        ar_order(2, 1)
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)
        self.value = responses.ar_orders


class MA_Order(parametertools.Parameter):
    """Number of MA coefficients of the different responses [-]."""
    NDIM, TYPE, TIME, SPAN = 1, int, None, (0, None)

    def update(self):
        """Determine the total number of MA coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ma_order.update()
        >>> derived.ma_order
        ma_order(1, 3)
        """
        responses = self.subpars.pars.control.responses
        self.shape = len(responses)
        self.value = responses.ma_orders


class AR_Coefs(parametertools.Parameter):
    """AR coefficients of the different responses [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)

    def update(self):
        """Determine all AR coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ar_coefs.update()
        >>> derived.ar_coefs
        ar_coefs([[1.0, 2.0],
                  [1.0, nan]])

        Note that updating parameter `ar_coefs` sets the shape of the log
        sequence |LogOut| automatically.

        >>> logs.logout
        logout([[nan, nan],
                [nan, nan]])
        """
        pars = self.subpars.pars
        coefs = pars.control.responses.ar_coefs
        self.shape = coefs.shape
        self.value = coefs
        pars.model.sequences.logs.logout.shape = self.shape


class MA_Coefs(parametertools.Parameter):
    """MA coefficients of the different responses [-]."""
    NDIM, TYPE, TIME, SPAN = 2, float, None, (None, None)

    def update(self):
        """Determine all MA coefficients.

        >>> from hydpy.models.arma import *
        >>> parameterstep('1d')
        >>> responses(((1., 2.), (1.,)), th_3=((1.,), (1., 2., 3.)))
        >>> derived.ma_coefs.update()
        >>> derived.ma_coefs
        ma_coefs([[1.0, nan, nan],
                  [1.0, 2.0, 3.0]])

        Note that updating parameter `ar_coefs` sets the shape of the log
        sequence |LogIn| automatically.

        >>> logs.login
        login([[nan, nan, nan],
               [nan, nan, nan]])
        """
        pars = self.subpars.pars
        coefs = pars.control.responses.ma_coefs
        self.shape = coefs.shape
        self.value = coefs
        pars.model.sequences.logs.login.shape = self.shape


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of arma, indirectly defined by the user."""
    CLASSES = (Nmb,
               MaxQ,
               DiffQ,
               AR_Order,
               MA_Order,
               AR_Coefs,
               MA_Coefs)
