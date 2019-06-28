# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Version 2 of HydPy-Dam.

Application model |dam_v002| is a simplification of |dam_v001|.
While most functionlities are identical, |dam_v002| does not calculate
|RequiredRemoteRelease| on its own, but picks this information from
the simulation results of another model.

The following explanations focus on this difference.  For further
information on the usage of |dam_v002| please read the documentation
on model |dam_v001|.

Integration examples:

    Each of the following examples is a repetition of an example performed
    to demonstrate the functionality of model |dam_v001|.  To achieve
    comparability, identical parameter values and initial conditions are set.
    Additionally, the values of sequence |RequiredRemoteRelease| calculated
    by |dam_v001| in the respective example are used as input data of
    |dam_v002| via the node object `remote`.  (Note that this nodes handles
    variable |dam_receivers.D|). Due to the limit precision of the
    copy-pasted |RequiredRemoteRelease| values, there are some tiny
    deviations between the results of both models.

    :ref:`Recalculation of example 7 <dam_v001_ex07>`

    The general time- and space-related set up is identical, except that
    no other models need to bee included to construct meaningful examples:

    >>> from hydpy import pub
    >>> pub.timegrids = '01.01.2000', '21.01.2000',  '1d'
    >>> from hydpy import Node
    >>> input_ = Node('input_')
    >>> output = Node('output')
    >>> remote = Node('remote', variable='D')
    >>> from hydpy import Element
    >>> dam = Element('dam', inlets=input_, outlets=output, receivers=remote)
    >>> from hydpy.models.dam_v002 import *
    >>> parameterstep('1d')
    >>> dam.model = model

    Next, all initial conditions and the external input time series data
    are defined.  Note that the first value of |RequiredRemoteRelease|
    calculated by model |dam_v001| is inserted as an initial condition
    via the `test` object and all other values are passed to the series
    object of node `remote`:

    >>> from hydpy import IntegrationTest
    >>> IntegrationTest.plotting_options.height = 200
    >>> IntegrationTest.plotting_options.activated=(
    ...     fluxes.inflow, fluxes.outflow)
    >>> test = IntegrationTest(
    ...     dam,
    ...     inits=((states.watervolume, 0.0),
    ...            (logs.loggedrequiredremoterelease, 0.005)))
    >>> test.dateformat = '%d.%m.'
    >>> input_.sequences.sim.series = 1.0
    >>> remote.sequences.sim.series = [
    ...     0.008588, 0.010053, 0.013858, 0.027322, 0.064075,
    ...     0.235523, 0.470414, 0.735001, 0.891263, 0.696325,
    ...     0.349797, 0.105231, 0.111928, 0.240436, 0.229369,
    ...     0.058622, 0.016958, 0.008447, 0.004155, 0.0]

    Except that |dam_v002| implements less parameters
    than |dam_v001|, all parameter settings are identical:

    >>> watervolume2waterlevel(
    ...         weights_input=1e-6, weights_output=1e6,
    ...         intercepts_hidden=0.0, intercepts_output=-1e6/2)
    >>> waterlevel2flooddischarge(ann(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0))
    >>> catchmentarea(86.4)
    >>> neardischargeminimumthreshold(0.2)
    >>> neardischargeminimumtolerance(0.2)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> restricttargetedrelease(True)
    >>> parameters.update()

    The following test results confirm that both models behave identical
    under low flow conditions both when there is a "near" and/or a "remote"
    need for water supply:

    >>> test('dam_v002_ex7')
    |   date | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                 0.005 |        0.210526 |        0.210526 |      0.201754 |            0.0 | 0.201754 |    0.068968 |    1.0 | 0.201754 | 0.008588 |
    | 02.01. |    1.0 |              0.008588 |         0.21092 |         0.21092 |       0.21092 |            0.0 |  0.21092 |    0.137145 |    1.0 |  0.21092 | 0.010053 |
    | 03.01. |    1.0 |              0.010053 |        0.211084 |        0.211084 |      0.211084 |            0.0 | 0.211084 |    0.205307 |    1.0 | 0.211084 | 0.013858 |
    | 04.01. |    1.0 |              0.013858 |        0.211523 |        0.211523 |      0.211523 |            0.0 | 0.211523 |    0.273432 |    1.0 | 0.211523 | 0.027322 |
    | 05.01. |    1.0 |              0.027322 |        0.213209 |        0.213209 |      0.213209 |            0.0 | 0.213209 |     0.34141 |    1.0 | 0.213209 | 0.064075 |
    | 06.01. |    1.0 |              0.064075 |        0.219043 |        0.219043 |      0.219043 |            0.0 | 0.219043 |    0.408885 |    1.0 | 0.219043 | 0.235523 |
    | 07.01. |    1.0 |              0.235523 |        0.283419 |        0.283419 |      0.283419 |            0.0 | 0.283419 |    0.470798 |    1.0 | 0.283419 | 0.470414 |
    | 08.01. |    1.0 |              0.470414 |        0.475211 |        0.475211 |      0.475211 |            0.0 | 0.475211 |    0.516139 |    1.0 | 0.475211 | 0.735001 |
    | 09.01. |    1.0 |              0.735001 |         0.73528 |         0.73528 |       0.73528 |            0.0 |  0.73528 |    0.539011 |    1.0 |  0.73528 | 0.891263 |
    | 10.01. |    1.0 |              0.891263 |        0.891314 |        0.891314 |      0.891314 |            0.0 | 0.891314 |    0.548402 |    1.0 | 0.891314 | 0.696325 |
    | 11.01. |    1.0 |              0.696325 |         0.69675 |         0.69675 |       0.69675 |            0.0 |  0.69675 |    0.574602 |    1.0 |  0.69675 | 0.349797 |
    | 12.01. |    1.0 |              0.349797 |        0.366407 |        0.366407 |      0.366407 |            0.0 | 0.366407 |    0.629345 |    1.0 | 0.366407 | 0.105231 |
    | 13.01. |    1.0 |              0.105231 |        0.228241 |        0.228241 |      0.228241 |            0.0 | 0.228241 |    0.696025 |    1.0 | 0.228241 | 0.111928 |
    | 14.01. |    1.0 |              0.111928 |        0.230054 |        0.230054 |      0.230054 |            0.0 | 0.230054 |    0.762548 |    1.0 | 0.230054 | 0.240436 |
    | 15.01. |    1.0 |              0.240436 |        0.286374 |        0.286374 |      0.286374 |            0.0 | 0.286374 |    0.824205 |    1.0 | 0.286374 | 0.229369 |
    | 16.01. |    1.0 |              0.229369 |        0.279807 |        0.279807 |      0.279807 |            0.0 | 0.279807 |     0.88643 |    1.0 | 0.279807 | 0.058622 |
    | 17.01. |    1.0 |              0.058622 |         0.21805 |         0.21805 |       0.21805 |            0.0 |  0.21805 |    0.953991 |    1.0 |  0.21805 | 0.016958 |
    | 18.01. |    1.0 |              0.016958 |        0.211893 |        0.211893 |      0.211893 |            0.0 | 0.211893 |    1.022083 |    1.0 | 0.211893 | 0.008447 |
    | 19.01. |    1.0 |              0.008447 |        0.210904 |        0.210904 |      0.210904 |            0.0 | 0.210904 |    1.090261 |    1.0 | 0.210904 | 0.004155 |
    | 20.01. |    1.0 |              0.004155 |        0.210435 |        0.210435 |      0.210435 |            0.0 | 0.210435 |    1.158479 |    1.0 | 0.210435 |      0.0 |

    .. raw:: html

        <iframe
            src="dam_v002_ex7.html"
            width="100%"
            height="230px"
            frameborder=0
        ></iframe>


    :ref:`Recalculation of example 8.1 <dam_v001_ex08_1>`

    The next recalculation confirms that the restriction on releasing
    water when there is little inflow works as explained for model
    |dam_v001|:

    >>> input_.sequences.sim.series[10:] = 0.1
    >>> remote.sequences.sim.series = [
    ...     0.008746, 0.010632, 0.015099, 0.03006, 0.068641,
    ...     0.242578, 0.474285, 0.784512, 0.95036, 0.35,
    ...     0.034564, 0.299482, 0.585979, 0.557422, 0.229369,
    ...     0.142578, 0.068641, 0.029844, 0.012348, 0.0]
    >>> neardischargeminimumtolerance(0.0)
    >>> test('dam_v002_ex8_1')
    |   date | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.0 | 0.191667 |     0.06984 |    1.0 | 0.191667 | 0.008746 |
    | 02.01. |    1.0 |              0.008746 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.13896 |    1.0 |      0.2 | 0.010632 |
    | 03.01. |    1.0 |              0.010632 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.20808 |    1.0 |      0.2 | 0.015099 |
    | 04.01. |    1.0 |              0.015099 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      0.2772 |    1.0 |      0.2 |  0.03006 |
    | 05.01. |    1.0 |               0.03006 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.34632 |    1.0 |      0.2 | 0.068641 |
    | 06.01. |    1.0 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |     0.41544 |    1.0 |      0.2 | 0.242578 |
    | 07.01. |    1.0 |              0.242578 |        0.242578 |        0.242578 |      0.242578 |            0.0 | 0.242578 |    0.480881 |    1.0 | 0.242578 | 0.474285 |
    | 08.01. |    1.0 |              0.474285 |        0.474285 |        0.474285 |      0.474285 |            0.0 | 0.474285 |    0.526303 |    1.0 | 0.474285 | 0.784512 |
    | 09.01. |    1.0 |              0.784512 |        0.784512 |        0.784512 |      0.784512 |            0.0 | 0.784512 |    0.544921 |    1.0 | 0.784512 |  0.95036 |
    | 10.01. |    1.0 |               0.95036 |         0.95036 |         0.95036 |       0.95036 |            0.0 |  0.95036 |     0.54921 |    1.0 |  0.95036 |     0.35 |
    | 11.01. |    0.1 |                  0.35 |            0.35 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.034564 |
    | 12.01. |    0.1 |              0.034564 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.299482 |
    | 13.01. |    0.1 |              0.299482 |        0.299482 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.585979 |
    | 14.01. |    0.1 |              0.585979 |        0.585979 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.557422 |
    | 15.01. |    0.1 |              0.557422 |        0.557422 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.229369 |
    | 16.01. |    0.1 |              0.229369 |        0.229369 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.142578 |
    | 17.01. |    0.1 |              0.142578 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.068641 |
    | 18.01. |    0.1 |              0.068641 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.029844 |
    | 19.01. |    0.1 |              0.029844 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 | 0.012348 |
    | 20.01. |    0.1 |              0.012348 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |     0.54921 |    0.1 |      0.1 |      0.0 |

    .. raw:: html

        <iframe
            src="dam_v002_ex8_1.html"
            width="100%"
            height="230px"
            frameborder=0
        ></iframe>

    :ref:`Recalculation of example 10 <dam_v001_ex10>`

    The last recalculation for low flow conditions deals with a case where
    the available water storage is too limited to supply enough discharge:

    >>> input_.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)
    >>> neardischargeminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.01)
    >>> waterlevelminimumthreshold(0.005)
    >>> remote.sequences.sim.series = [
    ...     0.01232, 0.029323, 0.064084, 0.120198, 0.247367,
    ...     0.45567, 0.608464, 0.537314, 0.629775, 0.744091,
    ...     0.82219, 0.841916, 0.701812, 0.533258, 0.351863,
    ...     0.185207, 0.107697, 0.055458, 0.025948, 0.0]
    >>> test('dam_v008_ex10')
    |   date |   inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume |   input_ |   output |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |      0.2 |                 0.005 |           0.005 |           0.005 |      0.001282 |            0.0 | 0.001282 |    0.017169 |      0.2 | 0.001282 |  0.01232 |
    | 02.01. | 0.189474 |               0.01232 |         0.01232 |         0.01232 |      0.007624 |            0.0 | 0.007624 |    0.032881 | 0.189474 | 0.007624 | 0.029323 |
    | 03.01. | 0.178947 |              0.029323 |        0.029323 |        0.029323 |      0.025921 |            0.0 | 0.025921 |    0.046103 | 0.178947 | 0.025921 | 0.064084 |
    | 04.01. | 0.168421 |              0.064084 |        0.064084 |        0.064084 |      0.062021 |            0.0 | 0.062021 |    0.055296 | 0.168421 | 0.062021 | 0.120198 |
    | 05.01. | 0.157895 |              0.120198 |        0.120198 |        0.120198 |      0.118479 |            0.0 | 0.118479 |    0.058701 | 0.157895 | 0.118479 | 0.247367 |
    | 06.01. | 0.147368 |              0.247367 |        0.247367 |        0.247367 |      0.242243 |            0.0 | 0.242243 |    0.050504 | 0.147368 | 0.242243 |  0.45567 |
    | 07.01. | 0.136842 |               0.45567 |         0.45567 |         0.45567 |      0.397328 |            0.0 | 0.397328 |    0.027998 | 0.136842 | 0.397328 | 0.608464 |
    | 08.01. | 0.126316 |              0.608464 |        0.608464 |        0.608464 |      0.290762 |            0.0 | 0.290762 |     0.01379 | 0.126316 | 0.290762 | 0.537314 |
    | 09.01. | 0.115789 |              0.537314 |        0.537314 |        0.537314 |      0.154283 |            0.0 | 0.154283 |    0.010464 | 0.115789 | 0.154283 | 0.629775 |
    | 10.01. | 0.105263 |              0.629775 |        0.629775 |        0.629775 |      0.138519 |            0.0 | 0.138519 |    0.007591 | 0.105263 | 0.138519 | 0.744091 |
    | 11.01. | 0.094737 |              0.744091 |        0.744091 |        0.744091 |      0.126207 |            0.0 | 0.126207 |    0.004871 | 0.094737 | 0.126207 |  0.82219 |
    | 12.01. | 0.084211 |               0.82219 |         0.82219 |         0.82219 |      0.109723 |            0.0 | 0.109723 |    0.002667 | 0.084211 | 0.109723 | 0.841916 |
    | 13.01. | 0.073684 |              0.841916 |        0.841916 |        0.841916 |      0.092645 |            0.0 | 0.092645 |    0.001029 | 0.073684 | 0.092645 | 0.701812 |
    | 14.01. | 0.063158 |              0.701812 |        0.701812 |        0.701812 |      0.068806 |            0.0 | 0.068806 |    0.000541 | 0.063158 | 0.068806 | 0.533258 |
    | 15.01. | 0.052632 |              0.533258 |        0.533258 |        0.533258 |      0.051779 |            0.0 | 0.051779 |    0.000615 | 0.052632 | 0.051779 | 0.351863 |
    | 16.01. | 0.042105 |              0.351863 |        0.351863 |        0.351863 |      0.035499 |            0.0 | 0.035499 |    0.001185 | 0.042105 | 0.035499 | 0.185207 |
    | 17.01. | 0.031579 |              0.185207 |        0.185207 |        0.185207 |       0.02024 |            0.0 |  0.02024 |    0.002165 | 0.031579 |  0.02024 | 0.107697 |
    | 18.01. | 0.021053 |              0.107697 |        0.107697 |        0.107697 |      0.012785 |            0.0 | 0.012785 |    0.002879 | 0.021053 | 0.012785 | 0.055458 |
    | 19.01. | 0.010526 |              0.055458 |        0.055458 |        0.055458 |      0.006918 |            0.0 | 0.006918 |    0.003191 | 0.010526 | 0.006918 | 0.025948 |
    | 20.01. |      0.0 |              0.025948 |        0.025948 |        0.012974 |      0.001631 |            0.0 | 0.001631 |     0.00305 |      0.0 | 0.001631 |      0.0 |


    :ref:`Recalculation of example 13 <dam_v001_ex13>`

    The final recalculation shows the equality of both models under
    high flow conditions:

    >>> neardischargeminimumthreshold(0.0)
    >>> neardischargeminimumtolerance(0.0)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> waterlevel2flooddischarge(ann(
    ...         weights_input=1e-6, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2))

    >>> neardischargeminimumthreshold(0.0)
    >>> input_.sequences.sim.series = [ 0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                                 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> remote.sequences.sim.series = 0.0
    >>> test.inits.loggedrequiredremoterelease = 0.0
    >>> test('dam_v002_ex13')
    |   date | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow | watervolume | input_ |   output | remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |         0.0 |    0.0 |      0.0 |    0.0 |
    | 02.01. |    1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.026514 | 0.026514 |    0.084109 |    1.0 | 0.026514 |    0.0 |
    | 03.01. |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.183744 | 0.183744 |    0.500234 |    5.0 | 0.183744 |    0.0 |
    | 04.01. |    9.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.542983 | 0.542983 |     1.23092 |    9.0 | 0.542983 |    0.0 |
    | 05.01. |    8.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.961039 | 0.961039 |    1.839086 |    8.0 | 0.961039 |    0.0 |
    | 06.01. |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.251523 | 1.251523 |    2.162955 |    5.0 | 1.251523 |    0.0 |
    | 07.01. |    3.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.395546 | 1.395546 |    2.301579 |    3.0 | 1.395546 |    0.0 |
    | 08.01. |    2.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.453375 | 1.453375 |    2.348808 |    2.0 | 1.453375 |    0.0 |
    | 09.01. |    1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.455596 | 1.455596 |    2.309444 |    1.0 | 1.455596 |    0.0 |
    | 10.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.405132 | 1.405132 |    2.188041 |    0.0 | 1.405132 |    0.0 |
    | 11.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.331267 | 1.331267 |    2.073019 |    0.0 | 1.331267 |    0.0 |
    | 12.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.261285 | 1.261285 |    1.964044 |    0.0 | 1.261285 |    0.0 |
    | 13.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.194981 | 1.194981 |    1.860798 |    0.0 | 1.194981 |    0.0 |
    | 14.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.132163 | 1.132163 |    1.762979 |    0.0 | 1.132163 |    0.0 |
    | 15.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.072647 | 1.072647 |    1.670302 |    0.0 | 1.072647 |    0.0 |
    | 16.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |        1.01626 |  1.01626 |    1.582498 |    0.0 |  1.01626 |    0.0 |
    | 17.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.962837 | 0.962837 |    1.499308 |    0.0 | 0.962837 |    0.0 |
    | 18.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.912222 | 0.912222 |    1.420492 |    0.0 | 0.912222 |    0.0 |
    | 19.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.864268 | 0.864268 |     1.34582 |    0.0 | 0.864268 |    0.0 |
    | 20.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.818835 | 0.818835 |    1.275072 |    0.0 | 0.818835 |    0.0 |

    .. raw:: html

        <iframe
            src="dam_v002_ex13.html"
            width="100%"
            height="230px"
            frameborder=0
        ></iframe>
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.auxs.anntools import ann   # pylint: disable=unused-import
# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_solver
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_logs
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_receivers


class Model(modeltools.ELSModel):
    """Version 2 of HydPy-Dam."""

    INLET_METHODS = (dam_model.pic_inflow_v1,
                     dam_model.calc_requiredremoterelease_v2,
                     dam_model.calc_requiredrelease_v1,
                     dam_model.calc_targetedrelease_v1)
    RECEIVER_METHODS = (dam_model.pic_loggedrequiredremoterelease_v1,)
    PART_ODE_METHODS = (dam_model.pic_inflow_v1,
                        dam_model.calc_waterlevel_v1,
                        dam_model.calc_actualrelease_v1,
                        dam_model.calc_flooddischarge_v1,
                        dam_model.calc_outflow_v1)
    FULL_ODE_METHODS = (dam_model.update_watervolume_v1,)
    OUTLET_METHODS = (dam_model.pass_outflow_v1,)
    SENDER_METHODS = ()


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-Dam, Version 2."""
    CLASSES = (dam_control.CatchmentArea,
               dam_control.NearDischargeMinimumThreshold,
               dam_control.NearDischargeMinimumTolerance,
               dam_control.RestrictTargetedRelease,
               dam_control.WaterLevelMinimumThreshold,
               dam_control.WaterLevelMinimumTolerance,
               dam_control.WaterVolume2WaterLevel,
               dam_control.WaterLevel2FloodDischarge)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-Dam, Version 2."""
    CLASSES = (dam_derived.TOY,
               dam_derived.Seconds,
               dam_derived.NearDischargeMinimumSmoothPar1,
               dam_derived.NearDischargeMinimumSmoothPar2,
               dam_derived.WaterLevelMinimumSmoothPar)


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of HydPy-Dam, Version 2."""
    CLASSES = (dam_solver.AbsErrorMax,
               dam_solver.RelDTMin)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_fluxes.Inflow,
               dam_fluxes.RequiredRemoteRelease,
               dam_fluxes.RequiredRelease,
               dam_fluxes.TargetedRelease,
               dam_fluxes.ActualRelease,
               dam_fluxes.FloodDischarge,
               dam_fluxes.Outflow)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_states.WaterVolume,)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_logs.LoggedRequiredRemoteRelease,)


class AideSequences(sequencetools.AideSequences):
    """State sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_aides.WaterLevel,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_outlets.Q,)


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 2."""
    CLASSES = (dam_receivers.D,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.finalise()
