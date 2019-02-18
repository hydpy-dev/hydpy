# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, wildcard-import, unused-wildcard-import
"""Version 3 of HydPy-Dam

Application |dam_v003| is quite similar to model |dam_v002|.  Both
possess the same flood retentions functionalities.  Also, both models
try to meet a remote water demand.  The only difference is that model
|dam_v002| assumes the demand to occur in the channel downstream
(usually to increase low discharge values), whereas model |dam_v003|
is supposed to supply water to different locations (e.g. to a drinking
water treatment plant).  Hence |dam_v002| releases its output only via
one path and |dam_v003| splits its output into two separate paths.

Integration examples:

    To test the functionalities of |dam_v002|, four integration examples
    of |dam_v001| are recalculated.  We again make use of these examples
    and focus our explanations on the differences only.  So please follow
    the links for further information.

    .. _dam_v003_ex07:

    :ref:`Recalculation of example 7 <dam_v001_ex07>`

    While the time-related set up is identical, the spatial set up needs
    to be changed.  Instead of one output node, there a now two nodes,
    called `release` (into the stream bed) and `supply` (e.g. for a
    drinking water supply treatment plant).  The node `demand` defines
    the amount of water required by the plant:

    >>> from hydpy import pub, Node, Element
    >>> pub.timegrids = '01.01.2000', '21.01.2000', '1d'
    >>> inflow = Node('inflow', variable='Q')
    >>> release = Node('release', variable='Q')
    >>> supply = Node('supply', variable='S')
    >>> demand = Node('demand', variable='S')
    >>> dam = Element('dam',
    ...               inlets=inflow,
    ...               outlets=(release, supply),
    ...               receivers=demand)
    >>> from hydpy.models.dam_v003 import *
    >>> parameterstep('1d')
    >>> dam.connect(model)

    Method |Model.connect| recognizes the different purposes of both
    output nodes through the given `variable` keyword.  Each |dam_v003|
    model must be connecte  to exactly two nodes.  The `Q`-node
    (discharge) handles the release into the stream bed downstream and
    the `S`-node (supply) passes the water flow to another (arbitrary) model.

    As explained for model |dam_v002|, the following initial conditions,
    external time series data, and parameter values are set in favour of
    making the simulation results as comparable as possible:

    >>> from hydpy import IntegrationTest
    >>> IntegrationTest.plotting_options.height = 250
    >>> IntegrationTest.plotting_options.activated=(
    ...     fluxes.inflow, fluxes.outflow)
    >>> test = IntegrationTest(
    ...     dam,
    ...     inits=((states.watervolume, 0.0),
    ...            (logs.loggedrequiredremoterelease, 0.005)))
    >>> test.dateformat = '%d.%m.'
    >>> inflow.sequences.sim.series = 1.0
    >>> demand.sequences.sim.series = [
    ...     0.008588, 0.010053, 0.013858, 0.027322, 0.064075,
    ...     0.235523, 0.470414, 0.735001, 0.891263, 0.696325,
    ...     0.349797, 0.105231, 0.111928, 0.240436, 0.229369,
    ...     0.058622, 0.016958, 0.008447, 0.004155, 0.0]
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
    >>> waterlevelminimumremotethreshold(0.0)
    >>> waterlevelminimumremotetolerance(0.0)
    >>> restricttargetedrelease(True)
    >>> parameters.update()

    Despite trying to make this example comparable with
    :ref:`example 7 <dam_v001_ex07>` of model |dam_v001| (and the
    corresponding recalculation of model |dam_v002|), there are relevant
    differences in the results.  These are due to the separate output
    paths of model |dam_v003|.  Models |dam_v001| and |dam_v002| use the
    same water to both meet the near and the remote demand.  This is not
    possible for model |dam_v003|,  which is why it has to release a larger
    total amount of water:

    >>> test('dam_v003_ex7')
    |   date | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume |   demand | inflow |  release |   supply |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 | 0.008588 |    1.0 | 0.191667 | 0.004792 |
    | 02.01. |    1.0 |              0.008588 |             0.2 |             0.2 |           0.2 |            0.008588 |            0.0 |      0.2 |    0.137804 | 0.010053 |    1.0 |      0.2 | 0.008588 |
    | 03.01. |    1.0 |              0.010053 |             0.2 |             0.2 |           0.2 |            0.010053 |            0.0 |      0.2 |    0.206055 | 0.013858 |    1.0 |      0.2 | 0.010053 |
    | 04.01. |    1.0 |              0.013858 |             0.2 |             0.2 |           0.2 |            0.013858 |            0.0 |      0.2 |    0.273978 | 0.027322 |    1.0 |      0.2 | 0.013858 |
    | 05.01. |    1.0 |              0.027322 |             0.2 |             0.2 |           0.2 |            0.027322 |            0.0 |      0.2 |    0.340737 | 0.064075 |    1.0 |      0.2 | 0.027322 |
    | 06.01. |    1.0 |              0.064075 |             0.2 |             0.2 |           0.2 |            0.064075 |            0.0 |      0.2 |    0.404321 | 0.235523 |    1.0 |      0.2 | 0.064075 |
    | 07.01. |    1.0 |              0.235523 |             0.2 |             0.2 |           0.2 |            0.235523 |            0.0 |      0.2 |    0.453092 | 0.470414 |    1.0 |      0.2 | 0.235523 |
    | 08.01. |    1.0 |              0.470414 |             0.2 |             0.2 |           0.2 |            0.470414 |            0.0 |      0.2 |    0.481568 | 0.735001 |    1.0 |      0.2 | 0.470414 |
    | 09.01. |    1.0 |              0.735001 |             0.2 |             0.2 |           0.2 |            0.735001 |            0.0 |      0.2 |    0.487184 | 0.891263 |    1.0 |      0.2 | 0.735001 |
    | 10.01. |    1.0 |              0.891263 |             0.2 |             0.2 |           0.2 |            0.891263 |            0.0 |      0.2 |    0.479299 | 0.696325 |    1.0 |      0.2 | 0.891263 |
    | 11.01. |    1.0 |              0.696325 |             0.2 |             0.2 |           0.2 |            0.696325 |            0.0 |      0.2 |    0.488257 | 0.349797 |    1.0 |      0.2 | 0.696325 |
    | 12.01. |    1.0 |              0.349797 |             0.2 |             0.2 |           0.2 |            0.349797 |            0.0 |      0.2 |    0.527154 | 0.105231 |    1.0 |      0.2 | 0.349797 |
    | 13.01. |    1.0 |              0.105231 |             0.2 |             0.2 |           0.2 |            0.105231 |            0.0 |      0.2 |    0.587182 | 0.111928 |    1.0 |      0.2 | 0.105231 |
    | 14.01. |    1.0 |              0.111928 |             0.2 |             0.2 |           0.2 |            0.111928 |            0.0 |      0.2 |    0.646632 | 0.240436 |    1.0 |      0.2 | 0.111928 |
    | 15.01. |    1.0 |              0.240436 |             0.2 |             0.2 |           0.2 |            0.240436 |            0.0 |      0.2 |    0.694978 | 0.229369 |    1.0 |      0.2 | 0.240436 |
    | 16.01. |    1.0 |              0.229369 |             0.2 |             0.2 |           0.2 |            0.229369 |            0.0 |      0.2 |    0.744281 | 0.058622 |    1.0 |      0.2 | 0.229369 |
    | 17.01. |    1.0 |              0.058622 |             0.2 |             0.2 |           0.2 |            0.058622 |            0.0 |      0.2 |    0.808336 | 0.016958 |    1.0 |      0.2 | 0.058622 |
    | 18.01. |    1.0 |              0.016958 |             0.2 |             0.2 |           0.2 |            0.016958 |            0.0 |      0.2 |     0.87599 | 0.008447 |    1.0 |      0.2 | 0.016958 |
    | 19.01. |    1.0 |              0.008447 |             0.2 |             0.2 |           0.2 |            0.008447 |            0.0 |      0.2 |    0.944381 | 0.004155 |    1.0 |      0.2 | 0.008447 |
    | 20.01. |    1.0 |              0.004155 |             0.2 |             0.2 |           0.2 |            0.004155 |            0.0 |      0.2 |    1.013142 |      0.0 |    1.0 |      0.2 | 0.004155 |

    .. raw:: html

        <iframe
            src="dam_v003_ex7.html"
            width="100%"
            height="280px"
            frameborder=0
        ></iframe>

    .. _dam_v003_ex08:

    :ref:`Recalculation of example 8.1 <dam_v001_ex08_1>`

    The next recalculation shows that the restriction on releasing
    water during low inflow conditions concerns the release into
    the stream bed only:

    >>> inflow.sequences.sim.series[10:] = 0.1
    >>> demand.sequences.sim.series = [
    ...     0.008746, 0.010632, 0.015099, 0.03006, 0.068641,
    ...     0.242578, 0.474285, 0.784512, 0.95036, 0.35,
    ...     0.034564, 0.299482, 0.585979, 0.557422, 0.229369,
    ...     0.142578, 0.068641, 0.029844, 0.012348, 0.0]
    >>> neardischargeminimumtolerance(0.0)
    >>> test('dam_v003_ex8_1')
    |   date | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume |   demand | inflow |  release |   supply |
    ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.004792 |            0.0 | 0.191667 |    0.069426 | 0.008746 |    1.0 | 0.191667 | 0.004792 |
    | 02.01. |    1.0 |              0.008746 |             0.2 |             0.2 |           0.2 |            0.008746 |            0.0 |      0.2 |     0.13779 | 0.010632 |    1.0 |      0.2 | 0.008746 |
    | 03.01. |    1.0 |              0.010632 |             0.2 |             0.2 |           0.2 |            0.010632 |            0.0 |      0.2 |    0.205992 | 0.015099 |    1.0 |      0.2 | 0.010632 |
    | 04.01. |    1.0 |              0.015099 |             0.2 |             0.2 |           0.2 |            0.015099 |            0.0 |      0.2 |    0.273807 |  0.03006 |    1.0 |      0.2 | 0.015099 |
    | 05.01. |    1.0 |               0.03006 |             0.2 |             0.2 |           0.2 |             0.03006 |            0.0 |      0.2 |     0.34033 | 0.068641 |    1.0 |      0.2 |  0.03006 |
    | 06.01. |    1.0 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.068641 |            0.0 |      0.2 |    0.403519 | 0.242578 |    1.0 |      0.2 | 0.068641 |
    | 07.01. |    1.0 |              0.242578 |             0.2 |             0.2 |           0.2 |            0.242578 |            0.0 |      0.2 |    0.451681 | 0.474285 |    1.0 |      0.2 | 0.242578 |
    | 08.01. |    1.0 |              0.474285 |             0.2 |             0.2 |           0.2 |            0.474285 |            0.0 |      0.2 |    0.479822 | 0.784512 |    1.0 |      0.2 | 0.474285 |
    | 09.01. |    1.0 |              0.784512 |             0.2 |             0.2 |           0.2 |            0.784512 |            0.0 |      0.2 |    0.481161 |  0.95036 |    1.0 |      0.2 | 0.784512 |
    | 10.01. |    1.0 |               0.95036 |             0.2 |             0.2 |           0.2 |             0.95036 |            0.0 |      0.2 |     0.46817 |     0.35 |    1.0 |      0.2 |  0.95036 |
    | 11.01. |    0.1 |                  0.35 |             0.2 |             0.1 |           0.1 |                0.35 |            0.0 |      0.1 |     0.43793 | 0.034564 |    0.1 |      0.1 |     0.35 |
    | 12.01. |    0.1 |              0.034564 |             0.2 |             0.1 |           0.1 |            0.034564 |            0.0 |      0.1 |    0.434943 | 0.299482 |    0.1 |      0.1 | 0.034564 |
    | 13.01. |    0.1 |              0.299482 |             0.2 |             0.1 |           0.1 |            0.299482 |            0.0 |      0.1 |    0.409068 | 0.585979 |    0.1 |      0.1 | 0.299482 |
    | 14.01. |    0.1 |              0.585979 |             0.2 |             0.1 |           0.1 |            0.585979 |            0.0 |      0.1 |    0.358439 | 0.557422 |    0.1 |      0.1 | 0.585979 |
    | 15.01. |    0.1 |              0.557422 |             0.2 |             0.1 |           0.1 |            0.557422 |            0.0 |      0.1 |    0.310278 | 0.229369 |    0.1 |      0.1 | 0.557422 |
    | 16.01. |    0.1 |              0.229369 |             0.2 |             0.1 |           0.1 |            0.229369 |            0.0 |      0.1 |    0.290461 | 0.142578 |    0.1 |      0.1 | 0.229369 |
    | 17.01. |    0.1 |              0.142578 |             0.2 |             0.1 |           0.1 |            0.142578 |            0.0 |      0.1 |    0.278142 | 0.068641 |    0.1 |      0.1 | 0.142578 |
    | 18.01. |    0.1 |              0.068641 |             0.2 |             0.1 |           0.1 |            0.068641 |            0.0 |      0.1 |    0.272211 | 0.029844 |    0.1 |      0.1 | 0.068641 |
    | 19.01. |    0.1 |              0.029844 |             0.2 |             0.1 |           0.1 |            0.029844 |            0.0 |      0.1 |    0.269633 | 0.012348 |    0.1 |      0.1 | 0.029844 |
    | 20.01. |    0.1 |              0.012348 |             0.2 |             0.1 |           0.1 |            0.012348 |            0.0 |      0.1 |    0.268566 |      0.0 |    0.1 |      0.1 | 0.012348 |

    .. raw:: html

        <iframe
            src="dam_v003_ex8_1.html"
            width="100%"
            height="280px"
            frameborder=0
        ></iframe>

    .. _dam_v003_ex10:

    :ref:`Recalculation of example 10 <dam_v001_ex10>`

    This example makes use of two control parameters which are unknown to
    models |dam_v001| and |dam_v002|.  |WaterLevelMinimumRemoteThreshold|
    and |WaterLevelMinimumRemoteTolerance| are introduced to allow for a
    distinct control of both dam output paths for situations when the
    available storage becomes limited.  Here, parameter
    |WaterLevelMinimumRemoteThreshold| is set to a higher value than
    parameter |WaterLevelMinimumThreshold|, meaning the release into the
    stream bed has a higher priority than the supply to the drinking water
    treatment plant:

    >>> inflow.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)
    >>> waterlevelminimumtolerance(0.01)
    >>> waterlevelminimumthreshold(0.005)
    >>> waterlevelminimumremotetolerance(0.01)
    >>> waterlevelminimumremotethreshold(0.01)
    >>> demand.sequences.sim.series = [
    ...     0.01232, 0.029323, 0.064084, 0.120198, 0.247367,
    ...     0.45567, 0.608464, 0.537314, 0.629775, 0.744091,
    ...     0.82219, 0.841916, 0.701812, 0.533258, 0.351863,
    ...     0.185207, 0.107697, 0.055458, 0.025948, 0.0]
    >>> test('dam_v003_ex10')
    |   date |   inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume |   demand |   inflow |  release |   supply |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |      0.2 |                 0.005 |             0.2 |             0.2 |      0.038491 |             0.00012 |            0.0 | 0.038491 |    0.013944 |  0.01232 |      0.2 | 0.038491 |  0.00012 |
    | 02.01. | 0.189474 |               0.01232 |             0.2 |        0.189474 |      0.086988 |            0.000993 |            0.0 | 0.086988 |    0.022713 | 0.029323 | 0.189474 | 0.086988 | 0.000993 |
    | 03.01. | 0.178947 |              0.029323 |             0.2 |        0.178947 |      0.116103 |            0.004642 |            0.0 | 0.116103 |    0.027742 | 0.064084 | 0.178947 | 0.116103 | 0.004642 |
    | 04.01. | 0.168421 |              0.064084 |             0.2 |        0.168421 |      0.125159 |            0.014625 |            0.0 | 0.125159 |    0.030216 | 0.120198 | 0.168421 | 0.125159 | 0.014625 |
    | 05.01. | 0.157895 |              0.120198 |             0.2 |        0.157895 |      0.121681 |            0.030361 |            0.0 | 0.121681 |    0.030722 | 0.247367 | 0.157895 | 0.121681 | 0.030361 |
    | 06.01. | 0.147368 |              0.247367 |             0.2 |        0.147368 |      0.109923 |            0.056857 |            0.0 | 0.109923 |    0.029044 |  0.45567 | 0.147368 | 0.109923 | 0.056857 |
    | 07.01. | 0.136842 |               0.45567 |             0.2 |        0.136842 |      0.094858 |            0.084715 |            0.0 | 0.094858 |    0.025352 | 0.608464 | 0.136842 | 0.094858 | 0.084715 |
    | 08.01. | 0.126316 |              0.608464 |             0.2 |        0.126316 |      0.076914 |            0.082553 |            0.0 | 0.076914 |    0.022488 | 0.537314 | 0.126316 | 0.076914 | 0.082553 |
    | 09.01. | 0.115789 |              0.537314 |             0.2 |        0.115789 |      0.064167 |            0.059779 |            0.0 | 0.064167 |    0.021783 | 0.629775 | 0.115789 | 0.064167 | 0.059779 |
    | 10.01. | 0.105263 |              0.629775 |             0.2 |        0.105263 |      0.055154 |            0.063011 |            0.0 | 0.055154 |    0.020669 | 0.744091 | 0.105263 | 0.055154 | 0.063011 |
    | 11.01. | 0.094737 |              0.744091 |             0.2 |        0.094737 |      0.045986 |            0.064865 |            0.0 | 0.045986 |    0.019277 |  0.82219 | 0.094737 | 0.045986 | 0.064865 |
    | 12.01. | 0.084211 |               0.82219 |             0.2 |        0.084211 |      0.037699 |             0.06228 |            0.0 | 0.037699 |    0.017914 | 0.841916 | 0.084211 | 0.037699 |  0.06228 |
    | 13.01. | 0.073684 |              0.841916 |             0.2 |        0.073684 |      0.030632 |            0.056377 |            0.0 | 0.030632 |    0.016763 | 0.701812 | 0.073684 | 0.030632 | 0.056377 |
    | 14.01. | 0.063158 |              0.701812 |             0.2 |        0.063158 |      0.025166 |            0.043828 |            0.0 | 0.025166 |    0.016259 | 0.533258 | 0.063158 | 0.025166 | 0.043828 |
    | 15.01. | 0.052632 |              0.533258 |             0.2 |        0.052632 |      0.020693 |            0.032602 |            0.0 | 0.020693 |    0.016201 | 0.351863 | 0.052632 | 0.020693 | 0.032602 |
    | 16.01. | 0.042105 |              0.351863 |             0.2 |        0.042105 |      0.016736 |            0.021882 |            0.0 | 0.016736 |    0.016502 | 0.185207 | 0.042105 | 0.016736 | 0.021882 |
    | 17.01. | 0.031579 |              0.185207 |             0.2 |        0.031579 |      0.012934 |            0.012076 |            0.0 | 0.012934 |     0.01707 | 0.107697 | 0.031579 | 0.012934 | 0.012076 |
    | 18.01. | 0.021053 |              0.107697 |             0.2 |        0.021053 |      0.008901 |            0.007386 |            0.0 | 0.008901 |    0.017482 | 0.055458 | 0.021053 | 0.008901 | 0.007386 |
    | 19.01. | 0.010526 |              0.055458 |             0.2 |        0.010526 |      0.004535 |             0.00392 |            0.0 | 0.004535 |    0.017661 | 0.025948 | 0.010526 | 0.004535 |  0.00392 |
    | 20.01. |      0.0 |              0.025948 |             0.2 |             0.0 |           0.0 |            0.001835 |            0.0 |      0.0 |    0.017502 |      0.0 |      0.0 |      0.0 | 0.001835 |

    .. raw:: html

        <iframe
            src="dam_v003_ex10.html"
            width="100%"
            height="280px"
            frameborder=0
        ></iframe>


    .. _dam_v003_ex13:

    :ref:`Recalculation of example 13 <dam_v001_ex13>`

    The final example deals with high flow conditions.  It demonstrates
    that model |dam_v003| calculates the same outflow values as model
    |dam_v001| and model |dam_v002| if there is neither a relevant near
    nor a relevant remote demand:

    >>> neardischargeminimumthreshold(0.0)
    >>> neardischargeminimumtolerance(0.0)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)
    >>> waterlevelminimumremotethreshold(0.0)
    >>> waterlevelminimumremotetolerance(0.0)
    >>> waterlevel2flooddischarge(ann(
    ...         weights_input=1e-6, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2))
    >>> neardischargeminimumthreshold(0.0)
    >>> inflow.sequences.sim.series = [ 0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                                 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
    >>> demand.sequences.sim.series = 0.0
    >>> test.inits.loggedrequiredremoterelease = 0.0
    >>> test('dam_v003_ex13')
    |   date | inflow | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | actualremoterelease | flooddischarge |  outflow | watervolume | demand | inflow |  release | supply |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |            0.0 |      0.0 |         0.0 |    0.0 |    0.0 |      0.0 |    0.0 |
    | 02.01. |    1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.026514 | 0.026514 |    0.084109 |    0.0 |    1.0 | 0.026514 |    0.0 |
    | 03.01. |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.183744 | 0.183744 |    0.500234 |    0.0 |    5.0 | 0.183744 |    0.0 |
    | 04.01. |    9.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.542983 | 0.542983 |     1.23092 |    0.0 |    9.0 | 0.542983 |    0.0 |
    | 05.01. |    8.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.961039 | 0.961039 |    1.839086 |    0.0 |    8.0 | 0.961039 |    0.0 |
    | 06.01. |    5.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.251523 | 1.251523 |    2.162955 |    0.0 |    5.0 | 1.251523 |    0.0 |
    | 07.01. |    3.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.395546 | 1.395546 |    2.301579 |    0.0 |    3.0 | 1.395546 |    0.0 |
    | 08.01. |    2.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.453375 | 1.453375 |    2.348808 |    0.0 |    2.0 | 1.453375 |    0.0 |
    | 09.01. |    1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.455596 | 1.455596 |    2.309444 |    0.0 |    1.0 | 1.455596 |    0.0 |
    | 10.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.405132 | 1.405132 |    2.188041 |    0.0 |    0.0 | 1.405132 |    0.0 |
    | 11.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.331267 | 1.331267 |    2.073019 |    0.0 |    0.0 | 1.331267 |    0.0 |
    | 12.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.261285 | 1.261285 |    1.964044 |    0.0 |    0.0 | 1.261285 |    0.0 |
    | 13.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.194981 | 1.194981 |    1.860798 |    0.0 |    0.0 | 1.194981 |    0.0 |
    | 14.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.132163 | 1.132163 |    1.762979 |    0.0 |    0.0 | 1.132163 |    0.0 |
    | 15.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       1.072647 | 1.072647 |    1.670302 |    0.0 |    0.0 | 1.072647 |    0.0 |
    | 16.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |        1.01626 |  1.01626 |    1.582498 |    0.0 |    0.0 |  1.01626 |    0.0 |
    | 17.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.962837 | 0.962837 |    1.499308 |    0.0 |    0.0 | 0.962837 |    0.0 |
    | 18.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.912222 | 0.912222 |    1.420492 |    0.0 |    0.0 | 0.912222 |    0.0 |
    | 19.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.864268 | 0.864268 |     1.34582 |    0.0 |    0.0 | 0.864268 |    0.0 |
    | 20.01. |    0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |                 0.0 |       0.818835 | 0.818835 |    1.275072 |    0.0 |    0.0 | 0.818835 |    0.0 |

    .. raw:: html

        <iframe
            src="dam_v003_ex13.html"
            width="100%"
            height="280px"
            frameborder=0
        ></iframe>
"""

# import...
# ...from standard library
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.auxs.anntools import ann   # pylint: disable=unused-import
from hydpy.exe.modelimports import *
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


class Model(modeltools.ModelELS):
    """Version 3 of HydPy-Dam."""

    INLET_METHODS = (dam_model.pic_inflow_v1,
                     dam_model.calc_requiredremoterelease_v2,
                     dam_model.calc_requiredrelease_v2,
                     dam_model.calc_targetedrelease_v1)
    RECEIVER_METHODS = (dam_model.pic_loggedrequiredremoterelease_v2,)
    PART_ODE_METHODS = (dam_model.pic_inflow_v1,
                        dam_model.calc_waterlevel_v1,
                        dam_model.calc_actualrelease_v1,
                        dam_model.calc_actualremoterelease_v1,
                        dam_model.calc_flooddischarge_v1,
                        dam_model.calc_outflow_v1)
    FULL_ODE_METHODS = (dam_model.update_watervolume_v2,)
    OUTLET_METHODS = (dam_model.pass_outflow_v1,
                      dam_model.pass_actualremoterelease_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-Dam, Version 3."""
    CLASSES = (dam_control.CatchmentArea,
               dam_control.NearDischargeMinimumThreshold,
               dam_control.NearDischargeMinimumTolerance,
               dam_control.RestrictTargetedRelease,
               dam_control.WaterLevelMinimumThreshold,
               dam_control.WaterLevelMinimumTolerance,
               dam_control.WaterLevelMinimumRemoteThreshold,
               dam_control.WaterLevelMinimumRemoteTolerance,
               dam_control.WaterVolume2WaterLevel,
               dam_control.WaterLevel2FloodDischarge)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-Dam, Version 3."""
    CLASSES = (dam_derived.TOY,
               dam_derived.Seconds,
               dam_derived.NearDischargeMinimumSmoothPar1,
               dam_derived.WaterLevelMinimumSmoothPar,
               dam_derived.WaterLevelMinimumRemoteSmoothPar)


class SolverParameters(parametertools.SubParameters):
    """Solver parameters of HydPy-Dam, Version 3."""
    CLASSES = (dam_solver.AbsErrorMax,
               dam_solver.RelDTMin)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_fluxes.Inflow,
               dam_fluxes.RequiredRemoteRelease,
               dam_fluxes.RequiredRelease,
               dam_fluxes.TargetedRelease,
               dam_fluxes.ActualRelease,
               dam_fluxes.ActualRemoteRelease,
               dam_fluxes.FloodDischarge,
               dam_fluxes.Outflow)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_states.WaterVolume,)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_logs.LoggedRequiredRemoteRelease,)


class AideSequences(sequencetools.AideSequences):
    """State sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_aides.WaterLevel,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_outlets.Q,
               dam_outlets.S)


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 3."""
    CLASSES = (dam_receivers.S,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
