# -*- coding: utf-8 -*-
"""

Obviously, using the "smoothly applied" parameter `remotedischargesavety`
can be beneficial.  But the proper definition of the values of the
"smoothing parameters" of the dam model might require some experience.
It seems advisable to investigate the functioning of each new
model parameterization on a large number of synthetic and/or measured
drought events.


Integration examples:

    The following are performed over a period of 20 days:

    >>> from hydpy import pub, Timegrid, Timegrids
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000',
    ...                                    '21.01.2000',
    ...                                    '1d'))

    The first examples are supposed to demonstrate how drought events at a
    cross section far downstream are reduced by the corresponding methods of
    the dam model under different configurations.  To show this in a
    realistic manner, a relatively complex setting is required.  We will
    make use of the :mod:`~hydpy.models.arma_v1` application model.  This
    model will be used to route the outflow of the dam to the cross section
    under investigation and add some `natural` discharge of the subcatchment
    between the dam and the cross section (a picture would be helful).

    We define four nodes.  The `input` node is used to define the inflow into
    the dam and the `natural` node is used to define the additional discharge
    of the subcatchment.  The `output` node receives the (unmodified) outflow
    out of dam and the `remote` node receives both the routed outflow of the
    dam and the additional discharge of the subcatchment:

    >>> from hydpy import Node
    >>> input_ = Node('input')
    >>> output = Node('output')
    >>> natural = Node('natural')
    >>> remote = Node('remote')

    These nodes are used to connect the following three elements.  There is
    one element for handling the `dam` model and there are two elements for
    handling different `stream` models.  The model of element `stream1` is
    supposed to route the outflow of the dam model with significant delay
    and the model of element `stream2` is supposed to directly pass the
    discharge of the subcatchment:

    >>> from hydpy import Element
    >>> dam = Element('dam', inlets=input_, outlets=output, receivers=remote)
    >>> stream1 = Element('stream1', inlets=output, outlets=remote)
    >>> stream2 = Element('stream2', inlets=natural, outlets=remote)

    Now the models can be prepared.  We begin with the `stream2` model.
    By setting the `responses` parameter in the following manner we define
    a pure Moving Average model that neither results in translation nor
    retention processes:

    >>> from hydpy.core.magictools import prepare_model
    >>> from hydpy.models import arma_v1
    >>> arma_model = prepare_model(arma_v1)
    >>> stream2.connect(arma_model)
    >>> arma_model.parameters.control.responses(((), (1.0,)))
    >>> arma_model.parameters.update()

    The second stream model is also configured as pure Moving Average model
    but with a time delay of 1.8 days:

    >>> arma_model = prepare_model(arma_v1)
    >>> stream1.connect(arma_model)
    >>> arma_model.parameters.control.responses(((), (0.2, 0.4, 0.3, 0.1)))
    >>> arma_model.parameters.update()
    >>> arma_model.sequences.logs.login = 0.0

    Last but not least, the dam model is initialized and handed over to its
    the `dam` element (different sets of parameters will be defined in the
    examples below):

    >>> from hydpy.models.dam_v1 import *
    >>> parameterstep('1d')
    >>> dam.connect(model)

    To execute the following examples conveniently, a test function object
    is prepared:

    >>> from hydpy.core.testtools import IntegrationTest
    >>> test = IntegrationTest(dam,
    ...                        inits=((states.watervolume, 0.0),
    ...                               (logs.loggedtotalremotedischarge, 1.9),
    ...                               (logs.loggedoutflow, 0.0),
    ...                               (stream1.model.sequences.logs.login, 0.0)))
    >>> test.dateformat = '%d.%m.'

    Next the drought event needs to be defined.  The natural discharge of
    the subcatchment decreases constantly for 9 days, than stays at constant
    level of 1 m³/s for 4 days, and finally increases constantly again:

    >>> natural.sequences.sim.series = [
    ...         1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 1.0,
    ...         1.0, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]

    The inflow into the dam is assumened to remain constant for the whole
    simulation period:

    >>> input_.sequences.sim.series = 1.0

    Finally, we can set the parameter values of the dam model.  For the sake
    of simplicity, the relationship between water level and volume is assumed
    to be linear in the range relevant for the following examples (between
    0 to 25 m or 0 to 1e8 m³).  This is approximately true if with the
    following configuration of the `watervolume2waterlevel` parameter:

    >>> watervolume2waterlevel(
    ...         weights_input=1e-10, weights_output=1e4,
    ...         intercepts_hidden=0.0, intercepts_output=-1e4/2)

    The following plot confirms the linearity of the defined relationship:

    >>> watervolume2waterlevel.plot(0.0, 1e8)

    Either close the plot manually or write the following lines:

    >>> from matplotlib import pyplot
    >>> pyplot.close()

    To focus on the drought related algorithms solely we turn of the flood
    related processes.  This is accomplished by setting the weights and
    intercepts of the `waterlevel2flooddischarge` to zero:

    >>> waterlevel2flooddischarge(
    ...        weights_input=0.0, weights_output=0.0,
    ...        intercepts_hidden=0.0, intercepts_output=0.0)
    >>> waterlevel2flooddischarge.plot(0.0, 25.0)
    >>> pyplot.close()

    To confirm that the whole scenario is properly aranged, we also turn of
    of the drought related methods at first:

    >>> nmblogentries(1)
    >>> remotedischargeminimum(0.0)
    >>> remotedischargesavety(0.0)
    >>> neardischargeminimumthreshold(0.0)
    >>> neardischargeminimumtolerance(0.0)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)

    The following table confirms that the dam model does not release any
    discharge (row `output` contains zero values only).  Hence the
    discharge at the cross section downstream (row `remote`) is identical
    with the discharge of the subcatchment (row `natural`):

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge | outflow | watervolume | input | natural | output | remote |
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -1.9 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |     86400.0 |   1.0 |     1.8 |    0.0 |    1.8 |
    | 02.01. |    1.0 |                  1.8 |                    1.8 |          0.0 |          -1.8 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    172800.0 |   1.0 |     1.7 |    0.0 |    1.7 |
    | 03.01. |    1.0 |                  1.7 |                    1.7 |          0.0 |          -1.7 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    259200.0 |   1.0 |     1.6 |    0.0 |    1.6 |
    | 04.01. |    1.0 |                  1.6 |                    1.6 |          0.0 |          -1.6 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    345600.0 |   1.0 |     1.5 |    0.0 |    1.5 |
    | 05.01. |    1.0 |                  1.5 |                    1.5 |          0.0 |          -1.5 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    432000.0 |   1.0 |     1.4 |    0.0 |    1.4 |
    | 06.01. |    1.0 |                  1.4 |                    1.4 |          0.0 |          -1.4 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    518400.0 |   1.0 |     1.3 |    0.0 |    1.3 |
    | 07.01. |    1.0 |                  1.3 |                    1.3 |          0.0 |          -1.3 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    604800.0 |   1.0 |     1.2 |    0.0 |    1.2 |
    | 08.01. |    1.0 |                  1.2 |                    1.2 |          0.0 |          -1.2 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    691200.0 |   1.0 |     1.1 |    0.0 |    1.1 |
    | 09.01. |    1.0 |                  1.1 |                    1.1 |          0.0 |          -1.1 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    777600.0 |   1.0 |     1.0 |    0.0 |    1.0 |
    | 10.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    864000.0 |   1.0 |     1.0 |    0.0 |    1.0 |
    | 11.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |    950400.0 |   1.0 |     1.0 |    0.0 |    1.0 |
    | 12.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1036800.0 |   1.0 |     1.0 |    0.0 |    1.0 |
    | 13.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1123200.0 |   1.0 |     1.1 |    0.0 |    1.1 |
    | 14.01. |    1.0 |                  1.1 |                    1.1 |          0.0 |          -1.1 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1209600.0 |   1.0 |     1.2 |    0.0 |    1.2 |
    | 15.01. |    1.0 |                  1.2 |                    1.2 |          0.0 |          -1.2 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1296000.0 |   1.0 |     1.3 |    0.0 |    1.3 |
    | 16.01. |    1.0 |                  1.3 |                    1.3 |          0.0 |          -1.3 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1382400.0 |   1.0 |     1.4 |    0.0 |    1.4 |
    | 17.01. |    1.0 |                  1.4 |                    1.4 |          0.0 |          -1.4 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1468800.0 |   1.0 |     1.5 |    0.0 |    1.5 |
    | 18.01. |    1.0 |                  1.5 |                    1.5 |          0.0 |          -1.5 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1555200.0 |   1.0 |     1.6 |    0.0 |    1.6 |
    | 19.01. |    1.0 |                  1.6 |                    1.6 |          0.0 |          -1.6 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1641600.0 |   1.0 |     1.7 |    0.0 |    1.7 |
    | 20.01. |    1.0 |                  1.7 |                    1.7 |          0.0 |          -1.7 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |     0.0 |   1728000.0 |   1.0 |     1.8 |    0.0 |    1.8 |

    Next the discharge that should not be undercut at the cross section
    downstream is set to 1.4 m³/s:

    >>> remotedischargeminimum(1.4)

    The dam model decreases the drought but is not very successful in
    doing so.  The lowest discharge at the cross section is increased from
    1 m³/s to approximately 1.2 m³/s in the beginning of the event, which
    is still below the threshold value of 1.4 m³/s.  Furthermore, in the
    second half of the event too much discharge is released.  On January 12,
    the discharge at the cross section is increased from 1 m³/s to
    approximately 1.6 m³/s:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |        86400.0 |   1.0 |     1.8 |      0.0 |      1.8 |
    | 02.01. |    1.0 |                  1.8 |                    1.8 |          0.0 |          -0.4 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       172800.0 |   1.0 |     1.7 |      0.0 |      1.7 |
    | 03.01. |    1.0 |                  1.7 |                    1.7 |          0.0 |          -0.3 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       259200.0 |   1.0 |     1.6 |      0.0 |      1.6 |
    | 04.01. |    1.0 |                  1.6 |                    1.6 |          0.0 |          -0.2 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       345600.0 |   1.0 |     1.5 |      0.0 |      1.5 |
    | 05.01. |    1.0 |                  1.5 |                    1.5 |          0.0 |          -0.1 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       432000.0 |   1.0 |     1.4 |      0.0 |      1.4 |
    | 06.01. |    1.0 |                  1.4 |                    1.4 |          0.0 |           0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       518400.0 |   1.0 |     1.3 |      0.0 |      1.3 |
    | 07.01. |    1.0 |                  1.3 |                    1.3 |          0.1 |           0.1 |                   0.1 |             0.1 |             0.1 |           0.1 |            0.0 |      0.1 |       596160.0 |   1.0 |     1.2 |      0.1 |     1.22 |
    | 08.01. |    1.0 |                 1.22 |                   1.12 |         0.28 |          0.18 |                  0.28 |            0.28 |            0.28 |          0.28 |            0.0 |     0.28 |       658368.0 |   1.0 |     1.1 |     0.28 |    1.196 |
    | 09.01. |    1.0 |                1.196 |                  0.916 |        0.484 |         0.204 |                 0.484 |           0.484 |           0.484 |         0.484 |            0.0 |    0.484 |       702950.4 |   1.0 |     1.0 |    0.484 |   1.2388 |
    | 10.01. |    1.0 |               1.2388 |                 0.7548 |       0.6452 |        0.1612 |                0.6452 |          0.6452 |          0.6452 |        0.6452 |            0.0 |   0.6452 |      733605.12 |   1.0 |     1.0 |   0.6452 |  1.41664 |
    | 11.01. |    1.0 |              1.41664 |                0.77144 |      0.62856 |      -0.01664 |               0.62856 |         0.62856 |         0.62856 |       0.62856 |            0.0 |  0.62856 |     765697.536 |   1.0 |     1.0 |  0.62856 | 1.556992 |
    | 12.01. |    1.0 |             1.556992 |               0.928432 |     0.471568 |     -0.156992 |              0.471568 |        0.471568 |        0.471568 |      0.471568 |            0.0 | 0.471568 |    811354.0608 |   1.0 |     1.0 | 0.471568 | 1.587698 |
    | 13.01. |    1.0 |             1.587698 |                1.11613 |      0.28387 |     -0.187698 |               0.28387 |         0.28387 |         0.28387 |       0.28387 |            0.0 |  0.28387 |   873227.65824 |   1.0 |     1.1 |  0.28387 | 1.598489 |
    | 14.01. |    1.0 |             1.598489 |               1.314619 |     0.085381 |     -0.198489 |              0.085381 |        0.085381 |        0.085381 |      0.085381 |            0.0 | 0.085381 |  952250.729472 |   1.0 |     1.2 | 0.085381 | 1.534951 |
    | 15.01. |    1.0 |             1.534951 |                1.44957 |          0.0 |     -0.134951 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1038650.729472 |   1.0 |     1.3 |      0.0 |  1.46647 |
    | 16.01. |    1.0 |              1.46647 |                1.46647 |          0.0 |      -0.06647 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1125050.729472 |   1.0 |     1.4 |      0.0 | 1.454001 |
    | 17.01. |    1.0 |             1.454001 |               1.454001 |          0.0 |     -0.054001 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1211450.729472 |   1.0 |     1.5 |      0.0 | 1.508538 |
    | 18.01. |    1.0 |             1.508538 |               1.508538 |          0.0 |     -0.108538 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1297850.729472 |   1.0 |     1.6 |      0.0 |      1.6 |
    | 19.01. |    1.0 |                  1.6 |                    1.6 |          0.0 |          -0.2 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1384250.729472 |   1.0 |     1.7 |      0.0 |      1.7 |
    | 20.01. |    1.0 |                  1.7 |                    1.7 |          0.0 |          -0.3 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1470650.729472 |   1.0 |     1.8 |      0.0 |      1.8 |

    The qualified success in the example above is due to the time delay
    of the information flow from the cross section to the dam and, more
    importantly, due to the travel time of the discharge released.
    A simple strategy to increase reliability would be to set a higher
    value for parameter `remotedischargeminimum`, e.g.:

    >>> remotedischargeminimum(1.6)

    Now there is only a small violation of threshold value on January, 6:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.3 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |        86400.0 |   1.0 |     1.8 |      0.0 |      1.8 |
    | 02.01. |    1.0 |                  1.8 |                    1.8 |          0.0 |          -0.2 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       172800.0 |   1.0 |     1.7 |      0.0 |      1.7 |
    | 03.01. |    1.0 |                  1.7 |                    1.7 |          0.0 |          -0.1 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       259200.0 |   1.0 |     1.6 |      0.0 |      1.6 |
    | 04.01. |    1.0 |                  1.6 |                    1.6 |          0.0 |           0.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |       345600.0 |   1.0 |     1.5 |      0.0 |      1.5 |
    | 05.01. |    1.0 |                  1.5 |                    1.5 |          0.1 |           0.1 |                   0.1 |             0.1 |             0.1 |           0.1 |            0.0 |      0.1 |       423360.0 |   1.0 |     1.4 |      0.1 |     1.42 |
    | 06.01. |    1.0 |                 1.42 |                   1.32 |         0.28 |          0.18 |                  0.28 |            0.28 |            0.28 |          0.28 |            0.0 |     0.28 |       485568.0 |   1.0 |     1.3 |     0.28 |    1.396 |
    | 07.01. |    1.0 |                1.396 |                  1.116 |        0.484 |         0.204 |                 0.484 |           0.484 |           0.484 |         0.484 |            0.0 |    0.484 |       530150.4 |   1.0 |     1.2 |    0.484 |   1.4388 |
    | 08.01. |    1.0 |               1.4388 |                 0.9548 |       0.6452 |        0.1612 |                0.6452 |          0.6452 |          0.6452 |        0.6452 |            0.0 |   0.6452 |      560805.12 |   1.0 |     1.1 |   0.6452 |  1.51664 |
    | 09.01. |    1.0 |              1.51664 |                0.87144 |      0.72856 |       0.08336 |               0.72856 |         0.72856 |         0.72856 |       0.72856 |            0.0 |  0.72856 |     584257.536 |   1.0 |     1.0 |  0.72856 | 1.576992 |
    | 10.01. |    1.0 |             1.576992 |               0.848432 |     0.751568 |      0.023008 |              0.751568 |        0.751568 |        0.751568 |      0.751568 |            0.0 | 0.751568 |    605722.0608 |   1.0 |     1.0 | 0.751568 | 1.683698 |
    | 11.01. |    1.0 |             1.683698 |                0.93213 |      0.66787 |     -0.083698 |               0.66787 |         0.66787 |         0.66787 |       0.66787 |            0.0 |  0.66787 |   634418.05824 |   1.0 |     1.0 |  0.66787 | 1.717289 |
    | 12.01. |    1.0 |             1.717289 |               1.049419 |     0.550581 |     -0.117289 |              0.550581 |        0.550581 |        0.550581 |      0.550581 |            0.0 | 0.550581 |  673247.849472 |   1.0 |     1.0 | 0.550581 | 1.675591 |
    | 13.01. |    1.0 |             1.675591 |                1.12501 |      0.47499 |     -0.075591 |               0.47499 |         0.47499 |         0.47499 |       0.47499 |            0.0 |  0.47499 |  718608.684442 |   1.0 |     1.1 |  0.47499 | 1.690748 |
    | 14.01. |    1.0 |             1.690748 |               1.215758 |     0.384242 |     -0.090748 |              0.384242 |        0.384242 |        0.384242 |      0.384242 |            0.0 | 0.384242 |  771810.184212 |   1.0 |     1.2 | 0.384242 | 1.698806 |
    | 15.01. |    1.0 |             1.698806 |               1.314564 |     0.285436 |     -0.098806 |              0.285436 |        0.285436 |        0.285436 |      0.285436 |            0.0 | 0.285436 |  833548.512928 |   1.0 |     1.3 | 0.285436 | 1.708339 |
    | 16.01. |    1.0 |             1.708339 |               1.422903 |     0.177097 |     -0.108339 |              0.177097 |        0.177097 |        0.177097 |      0.177097 |            0.0 | 0.177097 |  904647.346378 |   1.0 |     1.4 | 0.177097 | 1.712365 |
    | 17.01. |    1.0 |             1.712365 |               1.535269 |     0.064731 |     -0.112365 |              0.064731 |        0.064731 |        0.064731 |      0.064731 |            0.0 | 0.064731 |  985454.548223 |   1.0 |     1.5 | 0.064731 |  1.70784 |
    | 18.01. |    1.0 |              1.70784 |               1.643109 |          0.0 |      -0.10784 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1071854.548223 |   1.0 |     1.6 |      0.0 | 1.707565 |
    | 19.01. |    1.0 |             1.707565 |               1.707565 |          0.0 |     -0.107565 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1158254.548223 |   1.0 |     1.7 |      0.0 | 1.737129 |
    | 20.01. |    1.0 |             1.737129 |               1.737129 |          0.0 |     -0.137129 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 | 1244654.548223 |   1.0 |     1.8 |      0.0 | 1.806473 |

    While is is possible to simply increase the value of parameter
    `remotedischargeminimum`, it is often advisable to use parameter
    'remotedischargesavety´ instead:

    >>> remotedischargeminimum(1.4)
    >>> remotedischargesavety(0.5)

    Under this configuration, the threshold value is exceeded at each
    simulation time step.  Additionally, the final storage content of
    the dam is about 4 % higher than in the last example, meaning the
    available water has been used more efficiently:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |           0.005 |           0.005 |       0.00375 |            0.0 |  0.00375 |        86076.0 |   1.0 |     1.8 |  0.00375 |  1.80075 |
    | 02.01. |    1.0 |              1.80075 |                  1.797 |          0.0 |      -0.40075 |              0.012265 |        0.012265 |        0.012265 |      0.012265 |            0.0 | 0.012265 |  171416.268866 |   1.0 |     1.7 | 0.012265 | 1.703953 |
    | 03.01. |    1.0 |             1.703953 |               1.691688 |          0.0 |     -0.303953 |              0.028841 |        0.028841 |        0.028841 |      0.028841 |            0.0 | 0.028841 |  255324.415962 |   1.0 |     1.6 | 0.028841 | 1.611799 |
    | 04.01. |    1.0 |             1.611799 |               1.582958 |          0.0 |     -0.211799 |              0.062468 |        0.062468 |        0.062468 |      0.062468 |            0.0 | 0.062468 |   336327.13962 |   1.0 |     1.5 | 0.062468 | 1.528085 |
    | 05.01. |    1.0 |             1.528085 |               1.465616 |          0.0 |     -0.128085 |              0.117784 |        0.117784 |        0.117784 |      0.117784 |            0.0 | 0.117784 |  412550.566188 |   1.0 |     1.4 | 0.117784 | 1.458423 |
    | 06.01. |    1.0 |             1.458423 |               1.340639 |     0.059361 |     -0.058423 |              0.243813 |        0.243813 |        0.243813 |      0.243813 |            0.0 | 0.243813 |  477885.099964 |   1.0 |     1.3 | 0.243813 | 1.417501 |
    | 07.01. |    1.0 |             1.417501 |               1.173688 |     0.226312 |     -0.017501 |              0.456251 |        0.456251 |        0.456251 |      0.456251 |            0.0 | 0.456251 |   524865.04915 |   1.0 |     1.2 | 0.456251 | 1.430358 |
    | 08.01. |    1.0 |             1.430358 |               0.974107 |     0.425893 |     -0.030358 |              0.641243 |        0.641243 |        0.641243 |      0.641243 |            0.0 | 0.641243 |  555861.631798 |   1.0 |     1.1 | 0.641243 | 1.495671 |
    | 09.01. |    1.0 |             1.495671 |               0.854428 |     0.545572 |     -0.095671 |              0.692239 |        0.692239 |        0.692239 |      0.692239 |            0.0 | 0.692239 |  582452.150909 |   1.0 |     1.0 | 0.692239 | 1.556202 |
    | 10.01. |    1.0 |             1.556202 |               0.863962 |     0.536038 |     -0.156202 |              0.632157 |        0.632157 |        0.632157 |      0.632157 |            0.0 | 0.632157 |  614233.797238 |   1.0 |     1.0 | 0.632157 | 1.641325 |
    | 11.01. |    1.0 |             1.641325 |               1.009168 |     0.390832 |     -0.241325 |              0.439912 |        0.439912 |        0.439912 |      0.439912 |            0.0 | 0.439912 |  662625.416141 |   1.0 |     1.0 | 0.439912 | 1.612641 |
    | 12.01. |    1.0 |             1.612641 |               1.172729 |     0.227271 |     -0.212641 |              0.289317 |        0.289317 |        0.289317 |      0.289317 |            0.0 | 0.289317 |  724028.399479 |   1.0 |     1.0 | 0.289317 | 1.492699 |
    | 13.01. |    1.0 |             1.492699 |               1.203382 |     0.196618 |     -0.092699 |              0.346132 |        0.346132 |        0.346132 |      0.346132 |            0.0 | 0.346132 |  780522.556389 |   1.0 |     1.1 | 0.346132 | 1.480143 |
    | 14.01. |    1.0 |             1.480143 |                1.13401 |      0.26599 |     -0.080143 |              0.427871 |        0.427871 |        0.427871 |      0.427871 |            0.0 | 0.427871 |  829954.460845 |   1.0 |     1.2 | 0.427871 | 1.554814 |
    | 15.01. |    1.0 |             1.554814 |               1.126942 |     0.273058 |     -0.154814 |              0.370171 |        0.370171 |        0.370171 |      0.370171 |            0.0 | 0.370171 |  884371.658863 |   1.0 |     1.3 | 0.370171 | 1.677954 |
    | 16.01. |    1.0 |             1.677954 |               1.307783 |     0.092217 |     -0.277954 |               0.12828 |         0.12828 |         0.12828 |       0.12828 |            0.0 |  0.12828 |  959688.224863 |   1.0 |     1.4 |  0.12828 | 1.736699 |
    | 17.01. |    1.0 |             1.736699 |               1.608419 |          0.0 |     -0.336699 |              0.021671 |        0.021671 |        0.021671 |      0.021671 |            0.0 | 0.021671 | 1044215.892674 |   1.0 |     1.5 | 0.021671 | 1.709485 |
    | 18.01. |    1.0 |             1.709485 |               1.687814 |          0.0 |     -0.309485 |               0.02749 |         0.02749 |         0.02749 |       0.02749 |            0.0 |  0.02749 | 1128240.763982 |   1.0 |     1.6 |  0.02749 | 1.689667 |
    | 19.01. |    1.0 |             1.689667 |               1.662178 |          0.0 |     -0.289667 |              0.032623 |        0.032623 |        0.032623 |      0.032623 |            0.0 | 0.032623 | 1211822.123053 |   1.0 |     1.7 | 0.032623 |  1.73685 |
    | 20.01. |    1.0 |              1.73685 |               1.704227 |          0.0 |      -0.33685 |              0.021642 |        0.021642 |        0.021642 |      0.021642 |            0.0 | 0.021642 | 1296352.266543 |   1.0 |     1.8 | 0.021642 | 1.827792 |

    Building upon the last example, we subsequently increase the complexity
    of the model parameterization.  Firstly, we introduce a required minimum
    water release of 0.2 m³/s:

    >>> neardischargeminimumthreshold(0.2)

    Now there is also a relevant water release before and after the drought
    event occurs:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.0 | 0.191667 |        69840.0 |   1.0 |     1.8 | 0.191667 | 1.838333 |
    | 02.01. |    1.0 |             1.838333 |               1.646667 |          0.0 |     -0.438333 |              0.008746 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |       138960.0 |   1.0 |     1.7 |      0.2 | 1.816667 |
    | 03.01. |    1.0 |             1.816667 |               1.616667 |          0.0 |     -0.416667 |              0.010632 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |       208080.0 |   1.0 |     1.6 |      0.2 |   1.7775 |
    | 04.01. |    1.0 |               1.7775 |                 1.5775 |          0.0 |       -0.3775 |              0.015099 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |       277200.0 |   1.0 |     1.5 |      0.2 | 1.699167 |
    | 05.01. |    1.0 |             1.699167 |               1.499167 |          0.0 |     -0.299167 |               0.03006 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |       346320.0 |   1.0 |     1.4 |      0.2 |      1.6 |
    | 06.01. |    1.0 |                  1.6 |                    1.4 |          0.0 |          -0.2 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |       415440.0 |   1.0 |     1.3 |      0.2 |      1.5 |
    | 07.01. |    1.0 |                  1.5 |                    1.3 |          0.1 |          -0.1 |              0.242578 |        0.242578 |        0.242578 |      0.242578 |            0.0 | 0.242578 |  480881.225857 |   1.0 |     1.2 | 0.242578 | 1.408516 |
    | 08.01. |    1.0 |             1.408516 |               1.165937 |     0.234063 |     -0.008516 |              0.474285 |        0.474285 |        0.474285 |      0.474285 |            0.0 | 0.474285 |   526302.99581 |   1.0 |     1.1 | 0.474285 | 1.371888 |
    | 09.01. |    1.0 |             1.371888 |               0.897603 |     0.502397 |      0.028112 |              0.784512 |        0.784512 |        0.784512 |      0.784512 |            0.0 | 0.784512 |  544921.130446 |   1.0 |     1.0 | 0.784512 |  1.43939 |
    | 10.01. |    1.0 |              1.43939 |               0.654878 |     0.745122 |      -0.03939 |               0.95036 |         0.95036 |         0.95036 |       0.95036 |            0.0 |  0.95036 |   549210.05895 |   1.0 |     1.0 |  0.95036 |  1.67042 |
    | 11.01. |    1.0 |              1.67042 |               0.720061 |     0.679939 |      -0.27042 |               0.71839 |         0.71839 |         0.71839 |       0.71839 |            0.0 |  0.71839 |  573541.198788 |   1.0 |     1.0 |  0.71839 | 1.806604 |
    | 12.01. |    1.0 |             1.806604 |               1.088214 |     0.311786 |     -0.406604 |              0.323424 |        0.323424 |        0.323424 |      0.323424 |            0.0 | 0.323424 |  631997.405196 |   1.0 |     1.0 | 0.323424 |   1.7156 |
    | 13.01. |    1.0 |               1.7156 |               1.392176 |     0.007824 |       -0.3156 |               0.03389 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |  701117.405196 |   1.0 |     1.1 |      0.2 | 1.579922 |
    | 14.01. |    1.0 |             1.579922 |               1.379922 |     0.020078 |     -0.179922 |              0.100394 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |  770237.405196 |   1.0 |     1.2 |      0.2 | 1.488866 |
    | 15.01. |    1.0 |             1.488866 |               1.288866 |     0.111134 |     -0.088866 |              0.264366 |        0.264366 |        0.264366 |      0.264366 |            0.0 | 0.264366 |  833796.158466 |   1.0 |     1.3 | 0.264366 | 1.525216 |
    | 16.01. |    1.0 |             1.525216 |               1.260849 |     0.139151 |     -0.125216 |              0.259326 |        0.259326 |        0.259326 |      0.259326 |            0.0 | 0.259326 |  897790.419365 |   1.0 |     1.4 | 0.259326 | 1.637612 |
    | 17.01. |    1.0 |             1.637612 |               1.378286 |     0.021714 |     -0.237612 |              0.072326 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |  966910.419365 |   1.0 |     1.5 |      0.2 |  1.74304 |
    | 18.01. |    1.0 |              1.74304 |                1.54304 |          0.0 |      -0.34304 |              0.020494 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 1036030.419365 |   1.0 |     1.6 |      0.2 | 1.824234 |
    | 19.01. |    1.0 |             1.824234 |               1.624234 |          0.0 |     -0.424234 |              0.009932 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 1105150.419365 |   1.0 |     1.7 |      0.2 | 1.905933 |
    | 20.01. |    1.0 |             1.905933 |               1.705933 |          0.0 |     -0.505933 |              0.004737 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 1174270.419365 |   1.0 |     1.8 |      0.2 |      2.0 |

    One may have noted that the water release is only 0.19 m³/s instead
    of 0.2 m³/s on January 1.  This is due to the low local truncation
    error of 1e-2 m³/s in combination with the fact that the simulation
    starts with an completely dry dam. To confirm this, the required
    numerical accuracy is increased temporarily:

    >>> pub.config.abs_error_max = 1e-6

    Now there is only a tiny deviation left in the last shown digit:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |   watervolume | input | natural |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |             0.2 |             0.2 |      0.199998 |            0.0 | 0.199998 |  69120.205714 |   1.0 |     1.8 | 0.199998 |     1.84 |
    | 02.01. |    1.0 |                 1.84 |               1.640002 |          0.0 |         -0.44 |              0.008615 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 138240.205714 |   1.0 |     1.7 |      0.2 | 1.819999 |
    | 03.01. |    1.0 |             1.819999 |               1.619999 |          0.0 |     -0.419999 |              0.010318 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 207360.205714 |   1.0 |     1.6 |      0.2 | 1.779999 |
    | 04.01. |    1.0 |             1.779999 |               1.579999 |          0.0 |     -0.379999 |              0.014766 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 276480.205714 |   1.0 |     1.5 |      0.2 |      1.7 |
    | 05.01. |    1.0 |                  1.7 |                    1.5 |          0.0 |          -0.3 |              0.029844 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 345600.205714 |   1.0 |     1.4 |      0.2 |      1.6 |
    | 06.01. |    1.0 |                  1.6 |                    1.4 |          0.0 |          -0.2 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 414720.205714 |   1.0 |     1.3 |      0.2 |      1.5 |
    | 07.01. |    1.0 |                  1.5 |                    1.3 |          0.1 |          -0.1 |              0.242578 |        0.242578 |        0.242578 |      0.242578 |            0.0 | 0.242578 | 480161.431571 |   1.0 |     1.2 | 0.242578 | 1.408516 |
    | 08.01. |    1.0 |             1.408516 |               1.165937 |     0.234063 |     -0.008516 |              0.474285 |        0.474285 |        0.474285 |      0.474285 |            0.0 | 0.474285 | 525583.201524 |   1.0 |     1.1 | 0.474285 | 1.371888 |
    | 09.01. |    1.0 |             1.371888 |               0.897603 |     0.502397 |      0.028112 |              0.784512 |        0.784512 |        0.784512 |      0.784512 |            0.0 | 0.784512 | 544201.336161 |   1.0 |     1.0 | 0.784512 |  1.43939 |
    | 10.01. |    1.0 |              1.43939 |               0.654878 |     0.745122 |      -0.03939 |               0.95036 |         0.95036 |         0.95036 |       0.95036 |            0.0 |  0.95036 | 548490.264664 |   1.0 |     1.0 |  0.95036 |  1.67042 |
    | 11.01. |    1.0 |              1.67042 |               0.720061 |     0.679939 |      -0.27042 |               0.71839 |         0.71839 |         0.71839 |       0.71839 |            0.0 |  0.71839 | 572821.404502 |   1.0 |     1.0 |  0.71839 | 1.806604 |
    | 12.01. |    1.0 |             1.806604 |               1.088214 |     0.311786 |     -0.406604 |              0.323424 |        0.323424 |        0.323424 |      0.323424 |            0.0 | 0.323424 |  631277.61091 |   1.0 |     1.0 | 0.323424 |   1.7156 |
    | 13.01. |    1.0 |               1.7156 |               1.392176 |     0.007824 |       -0.3156 |               0.03389 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |  700397.61091 |   1.0 |     1.1 |      0.2 | 1.579922 |
    | 14.01. |    1.0 |             1.579922 |               1.379922 |     0.020078 |     -0.179922 |              0.100394 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |  769517.61091 |   1.0 |     1.2 |      0.2 | 1.488866 |
    | 15.01. |    1.0 |             1.488866 |               1.288866 |     0.111134 |     -0.088866 |              0.264366 |        0.264366 |        0.264366 |      0.264366 |            0.0 | 0.264366 |  833076.36418 |   1.0 |     1.3 | 0.264366 | 1.525216 |
    | 16.01. |    1.0 |             1.525216 |               1.260849 |     0.139151 |     -0.125216 |              0.259326 |        0.259326 |        0.259326 |      0.259326 |            0.0 | 0.259326 |  897070.62508 |   1.0 |     1.4 | 0.259326 | 1.637612 |
    | 17.01. |    1.0 |             1.637612 |               1.378286 |     0.021714 |     -0.237612 |              0.072326 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |  966190.62508 |   1.0 |     1.5 |      0.2 |  1.74304 |
    | 18.01. |    1.0 |              1.74304 |                1.54304 |          0.0 |      -0.34304 |              0.020494 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 1035310.62508 |   1.0 |     1.6 |      0.2 | 1.824234 |
    | 19.01. |    1.0 |             1.824234 |               1.624234 |          0.0 |     -0.424234 |              0.009932 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 1104430.62508 |   1.0 |     1.7 |      0.2 | 1.905933 |
    | 20.01. |    1.0 |             1.905933 |               1.705933 |          0.0 |     -0.505933 |              0.004737 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 | 1173550.62508 |   1.0 |     1.8 |      0.2 |      2.0 |

    >>> pub.config.abs_error_max = 1e-2

    To allow for a smooth transition of the water release in periods where
    the highest demand switches from `remote` to `near` or the other way
    round, one can increase the value of the `neardischargeminimumtolerance`
    parameter:

    >>> neardischargeminimumtolerance(0.2)

    It is easiest to inspect the functioning the effect of this "smooth
    switch" by looking at the results of column `requiredrelease`:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |        0.210526 |        0.210526 |      0.201754 |            0.0 | 0.201754 |   68968.429374 |   1.0 |     1.8 | 0.201754 | 1.840351 |
    | 02.01. |    1.0 |             1.840351 |               1.638597 |          0.0 |     -0.440351 |              0.008588 |         0.21092 |         0.21092 |       0.21092 |            0.0 |  0.21092 |  137144.958057 |   1.0 |     1.7 |  0.21092 | 1.822886 |
    | 03.01. |    1.0 |             1.822886 |               1.611966 |          0.0 |     -0.422886 |              0.010053 |        0.211084 |        0.211084 |      0.211084 |            0.0 | 0.211084 |  205307.258171 |   1.0 |     1.6 | 0.211084 | 1.787111 |
    | 04.01. |    1.0 |             1.787111 |               1.576027 |          0.0 |     -0.387111 |              0.013858 |        0.211523 |        0.211523 |      0.211523 |            0.0 | 0.211523 |  273431.659673 |   1.0 |     1.5 | 0.211523 |  1.71019 |
    | 05.01. |    1.0 |              1.71019 |               1.498667 |          0.0 |      -0.31019 |              0.027322 |        0.213209 |        0.213209 |      0.213209 |            0.0 | 0.213209 |  341410.364069 |   1.0 |     1.4 | 0.213209 | 1.611668 |
    | 06.01. |    1.0 |             1.611668 |               1.398459 |     0.001541 |     -0.211668 |              0.064075 |        0.219043 |        0.219043 |      0.219043 |            0.0 | 0.219043 |  408885.032539 |   1.0 |     1.3 | 0.219043 | 1.513658 |
    | 07.01. |    1.0 |             1.513658 |               1.294615 |     0.105385 |     -0.113658 |              0.235523 |        0.283419 |        0.283419 |      0.283419 |            0.0 | 0.283419 |  470797.641859 |   1.0 |     1.2 | 0.283419 | 1.429416 |
    | 08.01. |    1.0 |             1.429416 |               1.145997 |     0.254003 |     -0.029416 |              0.470414 |        0.475212 |        0.475212 |      0.475212 |            0.0 | 0.475212 |  516139.366423 |   1.0 |     1.1 | 0.475212 | 1.395444 |
    | 09.01. |    1.0 |             1.395444 |               0.920232 |     0.479768 |      0.004556 |              0.735001 |        0.735281 |        0.735281 |      0.735281 |            0.0 | 0.735281 |    539011.1214 |   1.0 |     1.0 | 0.735281 | 1.444071 |
    | 10.01. |    1.0 |             1.444071 |                0.70879 |      0.69121 |     -0.044071 |              0.891263 |        0.891315 |        0.891315 |      0.891315 |            0.0 | 0.891315 |  548401.529276 |   1.0 |     1.0 | 0.891315 | 1.643281 |
    | 11.01. |    1.0 |             1.643281 |               0.751966 |     0.648034 |     -0.243281 |              0.696325 |        0.696749 |        0.696749 |      0.696749 |            0.0 | 0.696749 |   574602.39174 |   1.0 |     1.0 | 0.696749 | 1.763981 |
    | 12.01. |    1.0 |             1.763981 |               1.067232 |     0.332768 |     -0.363981 |              0.349797 |        0.366406 |        0.366406 |      0.366406 |            0.0 | 0.366406 |  629344.887653 |   1.0 |     1.0 | 0.366406 | 1.692903 |
    | 13.01. |    1.0 |             1.692903 |               1.326497 |     0.073503 |     -0.292903 |              0.105231 |        0.228241 |        0.228241 |      0.228241 |            0.0 | 0.228241 |  696024.889028 |   1.0 |     1.1 | 0.228241 | 1.590367 |
    | 14.01. |    1.0 |             1.590367 |               1.362126 |     0.037874 |     -0.190367 |              0.111928 |        0.230054 |        0.230054 |      0.230054 |            0.0 | 0.230054 |   762548.20931 |   1.0 |     1.2 | 0.230054 | 1.516904 |
    | 15.01. |    1.0 |             1.516904 |                1.28685 |      0.11315 |     -0.116904 |              0.240436 |        0.286374 |        0.286374 |      0.286374 |            0.0 | 0.286374 |  824205.477401 |   1.0 |     1.3 | 0.286374 | 1.554409 |
    | 16.01. |    1.0 |             1.554409 |               1.268035 |     0.131965 |     -0.154409 |              0.229369 |        0.279807 |        0.279807 |      0.279807 |            0.0 | 0.279807 |  886430.159961 |   1.0 |     1.4 | 0.279807 | 1.662351 |
    | 17.01. |    1.0 |             1.662351 |               1.382544 |     0.017456 |     -0.262351 |              0.058622 |         0.21805 |         0.21805 |       0.21805 |            0.0 |  0.21805 |  953990.607095 |   1.0 |     1.5 |  0.21805 | 1.764451 |
    | 18.01. |    1.0 |             1.764451 |                 1.5464 |          0.0 |     -0.364451 |              0.016958 |        0.211892 |        0.211892 |      0.211892 |            0.0 | 0.211892 | 1022083.097724 |   1.0 |     1.6 | 0.211892 | 1.842178 |
    | 19.01. |    1.0 |             1.842178 |               1.630286 |          0.0 |     -0.442178 |              0.008447 |        0.210904 |        0.210904 |      0.210904 |            0.0 | 0.210904 | 1090260.981267 |   1.0 |     1.7 | 0.210904 | 1.920334 |
    | 20.01. |    1.0 |             1.920334 |               1.709429 |          0.0 |     -0.520334 |              0.004155 |        0.210435 |        0.210435 |      0.210435 |            0.0 | 0.210435 | 1158479.356753 |   1.0 |     1.8 | 0.210435 | 2.011822 |

    Version 1 of the dam model that is forced to keep a certain degree
    of low flow variability.  It is not allowed to release an arbitrary
    amount of water when its inflow falls below the required minimum
    water release.  We show this by decreasing the inflow in the
    second half of the simulation period to 0.1 m³/s:

    >>> input_.sequences.sim.series[10:] = 0.1

    The value of parameter `neardischargeminimumthreshold` (0.2 m³/s) is
    maintained, but the value of `neardischargeminimumtolerance` is reset
    to 0 m³/s for improving comprehensibility:

    >>> neardischargeminimumtolerance(0.0)

    As to be expected, the actual release drops to 0.1 m³/s on January 11.
    But, due to the time delay of the discharge released earlier, the
    largest violation of the threshold value takes place on January, 13:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |   watervolume | input | natural |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |             0.2 |             0.2 |      0.191667 |            0.0 | 0.191667 |       69840.0 |   1.0 |     1.8 | 0.191667 | 1.838333 |
    | 02.01. |    1.0 |             1.838333 |               1.646667 |          0.0 |     -0.438333 |              0.008746 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      138960.0 |   1.0 |     1.7 |      0.2 | 1.816667 |
    | 03.01. |    1.0 |             1.816667 |               1.616667 |          0.0 |     -0.416667 |              0.010632 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      208080.0 |   1.0 |     1.6 |      0.2 |   1.7775 |
    | 04.01. |    1.0 |               1.7775 |                 1.5775 |          0.0 |       -0.3775 |              0.015099 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      277200.0 |   1.0 |     1.5 |      0.2 | 1.699167 |
    | 05.01. |    1.0 |             1.699167 |               1.499167 |          0.0 |     -0.299167 |               0.03006 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      346320.0 |   1.0 |     1.4 |      0.2 |      1.6 |
    | 06.01. |    1.0 |                  1.6 |                    1.4 |          0.0 |          -0.2 |              0.068641 |             0.2 |             0.2 |           0.2 |            0.0 |      0.2 |      415440.0 |   1.0 |     1.3 |      0.2 |      1.5 |
    | 07.01. |    1.0 |                  1.5 |                    1.3 |          0.1 |          -0.1 |              0.242578 |        0.242578 |        0.242578 |      0.242578 |            0.0 | 0.242578 | 480881.225857 |   1.0 |     1.2 | 0.242578 | 1.408516 |
    | 08.01. |    1.0 |             1.408516 |               1.165937 |     0.234063 |     -0.008516 |              0.474285 |        0.474285 |        0.474285 |      0.474285 |            0.0 | 0.474285 |  526302.99581 |   1.0 |     1.1 | 0.474285 | 1.371888 |
    | 09.01. |    1.0 |             1.371888 |               0.897603 |     0.502397 |      0.028112 |              0.784512 |        0.784512 |        0.784512 |      0.784512 |            0.0 | 0.784512 | 544921.130446 |   1.0 |     1.0 | 0.784512 |  1.43939 |
    | 10.01. |    1.0 |              1.43939 |               0.654878 |     0.745122 |      -0.03939 |               0.95036 |         0.95036 |         0.95036 |       0.95036 |            0.0 |  0.95036 |  549210.05895 |   1.0 |     1.0 |  0.95036 |  1.67042 |
    | 11.01. |    0.1 |              1.67042 |               0.720061 |     0.679939 |      -0.27042 |               0.71839 |         0.71839 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.0 |      0.1 | 1.682926 |
    | 12.01. |    0.1 |             1.682926 |               1.582926 |          0.0 |     -0.282926 |              0.034564 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.0 |      0.1 | 1.423559 |
    | 13.01. |    0.1 |             1.423559 |               1.323559 |     0.076441 |     -0.023559 |              0.299482 |        0.299482 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.1 |      0.1 | 1.285036 |
    | 14.01. |    0.1 |             1.285036 |               1.185036 |     0.214964 |      0.114964 |              0.585979 |        0.585979 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.2 |      0.1 |      1.3 |
    | 15.01. |    0.1 |                  1.3 |                    1.2 |          0.2 |           0.1 |              0.557422 |        0.557422 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.3 |      0.1 |      1.4 |
    | 16.01. |    0.1 |                  1.4 |                    1.3 |          0.1 |          -0.0 |                  0.35 |            0.35 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.4 |      0.1 |      1.5 |
    | 17.01. |    0.1 |                  1.5 |                    1.4 |          0.0 |          -0.1 |              0.142578 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.5 |      0.1 |      1.6 |
    | 18.01. |    0.1 |                  1.6 |                    1.5 |          0.0 |          -0.2 |              0.068641 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.6 |      0.1 |      1.7 |
    | 19.01. |    0.1 |                  1.7 |                    1.6 |          0.0 |          -0.3 |              0.029844 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.7 |      0.1 |      1.8 |
    | 20.01. |    0.1 |                  1.8 |                    1.7 |          0.0 |          -0.4 |              0.012348 |             0.2 |             0.1 |           0.1 |            0.0 |      0.1 |  549210.05895 |   0.1 |     1.8 |      0.1 |      1.9 |

    Another issue of the dam model relevant for the simulation of drought
    events to be discussed is the possible restriction of water release
    due to limited storage.  To focus on this, we reset the parameter
    `neardischargeminimumthreshold` to 0 m³/s and define smaller inflow
    values, which are constantly decreasing from 0.2 m³/s to 0.0 m³/s:

    >>> neardischargeminimumthreshold(0.0)
    >>> input_.sequences.sim.series = numpy.linspace(0.2, 0.0, 20)

    Now the storage content increases only until January, 5.  Afterwards
    the dam begins to run dry.  On January 11, the dam is actually empty.
    But there are some fluctuations of the water volume around 0 m³.
    The most severe deviation from the correct value of 0 m³ oocurs on
    January 11, where the final storage volume is -666 m³:

    >>> test()
    |   date |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |  watervolume |    input | natural |   output |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |      0.2 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |           0.005 |           0.005 |       0.00375 |            0.0 |  0.00375 |      16956.0 |      0.2 |     1.8 |  0.00375 |  1.80075 |
    | 02.01. | 0.189474 |              1.80075 |                  1.797 |          0.0 |      -0.40075 |              0.012265 |        0.012265 |        0.012265 |      0.012265 |            0.0 | 0.012265 | 32266.795182 | 0.189474 |     1.7 | 0.012265 | 1.703953 |
    | 03.01. | 0.178947 |             1.703953 |               1.691688 |          0.0 |     -0.303953 |              0.028841 |        0.028841 |        0.028841 |      0.028841 |            0.0 | 0.028841 |  45235.99491 | 0.178947 |     1.6 | 0.028841 | 1.611799 |
    | 04.01. | 0.168421 |             1.611799 |               1.582958 |          0.0 |     -0.211799 |              0.062468 |        0.062468 |        0.062468 |      0.062468 |            0.0 | 0.062468 | 54390.297515 | 0.168421 |     1.5 | 0.062468 | 1.528085 |
    | 05.01. | 0.157895 |             1.528085 |               1.465616 |          0.0 |     -0.128085 |              0.117784 |        0.117784 |        0.117784 |      0.117784 |            0.0 | 0.117784 | 57855.829346 | 0.157895 |     1.4 | 0.117784 | 1.458423 |
    | 06.01. | 0.147368 |             1.458423 |               1.340639 |     0.059361 |     -0.058423 |              0.243813 |        0.243813 |        0.243813 |      0.243813 |            0.0 | 0.243813 |   49522.9947 | 0.147368 |     1.3 | 0.243813 | 1.417501 |
    | 07.01. | 0.136842 |             1.417501 |               1.173688 |     0.226312 |     -0.017501 |              0.456251 |        0.456251 |        0.456251 |      0.456251 |            0.0 | 0.456251 | 21926.101782 | 0.136842 |     1.2 | 0.456251 | 1.430358 |
    | 08.01. | 0.126316 |             1.430358 |               0.974107 |     0.425893 |     -0.030358 |              0.641243 |        0.641243 |        0.641243 |      0.382861 |            0.0 | 0.382861 |  -239.431715 | 0.126316 |     1.1 | 0.382861 | 1.443995 |
    | 09.01. | 0.115789 |             1.443995 |               1.061134 |     0.338866 |     -0.043995 |              0.539003 |        0.539003 |        0.539003 |       0.11547 |            0.0 |  0.11547 |  -211.822396 | 0.115789 |     1.0 |  0.11547 | 1.337495 |
    | 10.01. | 0.105263 |             1.337495 |               1.222025 |     0.177975 |      0.062505 |              0.497868 |        0.497868 |        0.497868 |      0.108362 |            0.0 | 0.108362 |  -479.597978 | 0.105263 |     1.0 | 0.108362 | 1.228344 |
    | 11.01. | 0.094737 |             1.228344 |               1.119981 |     0.280019 |      0.171656 |              0.694448 |        0.694448 |        0.694448 |      0.089381 |            0.0 | 0.089381 |   -16.812151 | 0.094737 |     1.0 | 0.089381 | 1.134148 |
    | 12.01. | 0.084211 |             1.134148 |               1.044768 |     0.355232 |      0.265852 |              0.815265 |        0.815265 |        0.815265 |      0.091721 |            0.0 | 0.091721 |  -665.717182 | 0.084211 |     1.0 | 0.091721 | 1.098152 |
    | 13.01. | 0.073684 |             1.098152 |               1.006431 |     0.393569 |      0.301848 |              0.864198 |        0.864198 |        0.864198 |      0.067904 |            0.0 | 0.067904 |  -166.338008 | 0.073684 |     1.1 | 0.067904 |  1.18792 |
    | 14.01. | 0.063158 |              1.18792 |               1.120015 |     0.279985 |       0.21208 |              0.717657 |        0.717657 |        0.717657 |      0.067501 |            0.0 | 0.067501 |  -541.539987 | 0.063158 |     1.2 | 0.067501 | 1.277116 |
    | 15.01. | 0.052632 |             1.277116 |               1.209616 |     0.190384 |      0.122884 |              0.568242 |        0.568242 |        0.568242 |      0.046544 |            0.0 | 0.046544 |     -15.5575 | 0.052632 |     1.3 | 0.046544 | 1.365852 |
    | 16.01. | 0.042105 |             1.365852 |               1.319309 |     0.080691 |      0.034148 |              0.369601 |        0.369601 |        0.369601 |      0.048083 |            0.0 | 0.048083 |  -532.012332 | 0.042105 |     1.4 | 0.048083 | 1.455275 |
    | 17.01. | 0.031579 |             1.455275 |               1.407192 |          0.0 |     -0.055275 |              0.187833 |        0.187833 |        0.187833 |      0.027168 |            0.0 | 0.027168 |  -150.917224 | 0.031579 |     1.5 | 0.027168 |  1.54538 |
    | 18.01. | 0.021053 |              1.54538 |               1.518212 |          0.0 |      -0.14538 |              0.104078 |        0.104078 |        0.104078 |      0.021731 |            0.0 | 0.021731 |  -209.570696 | 0.021053 |     1.6 | 0.021731 | 1.634293 |
    | 19.01. | 0.010526 |             1.634293 |               1.612561 |          0.0 |     -0.234293 |              0.052016 |        0.052016 |        0.052016 |      0.013004 |            0.0 | 0.013004 |  -423.642187 | 0.010526 |     1.7 | 0.013004 | 1.724252 |
    | 20.01. |      0.0 |             1.724252 |               1.711248 |          0.0 |     -0.324252 |               0.02417 |         0.02417 |        0.012085 |           0.0 |            0.0 |      0.0 |  -423.642187 |      0.0 |     1.8 |      0.0 | 1.814438 |

    This behaviour of the dam model is due to method
    :func:`~hydpy.models.dam.dam_model.calc_actualrelease_v1` beeing
    involved in the set of differential equation that are solved
    approximately by a numerical integration algorithm.  Theoretically,
    we could decrease the local truncation error to decrease this
    problem significantly.  But this could result in quite huge
    computation times, as the underlying numerical algorithm is not
    really able to handle the discontinuous relationship between release
    and volume around `neardischargeminimumthreshold`.

    One solution would be to define another version of the dam model and
    simply implement an alternative balance equation for the calculation of
    the actual release (not done yet, but seems to be worth the effort).
    When using the version of the dam model discussed here, it is instead
    advised to smooth this problematic discontinuity by increasing the
    value of parameter `waterlevelminimumtolerance` (which could not be
    implemented properly if method
    :func:`~hydpy.models.dam.dam_model.calc_actualrelease_v1` would
    apply a simple balance equation):

    >>> waterlevelminimumtolerance(0.01)

    If one wants to avoid not only the fluctuation but also the negative
    values of the water volume, one should also sligthly increase the
    original threshold value, e.g.:

    >>> waterlevelminimumthreshold(0.005)

    Now water storage is decaying smoothly.  The lowest storage content
    of 541 m³ occurs on January 14.  After that date, the dam is refilled
    to a certain degree.  This is due the decreasing remote demand. Note
    that negative storage values are circumvented in this example, but this
    would have not been the case if the low flow period were prolonged:

    >>> test()
    |   date |   inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |  watervolume |    input | natural |   output |   remote |
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |      0.2 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |           0.005 |           0.005 |      0.001282 |            0.0 | 0.001282 | 17169.249844 |      0.2 |     1.8 | 0.001282 | 1.800256 |
    | 02.01. | 0.189474 |             1.800256 |               1.798975 |          0.0 |     -0.400256 |               0.01232 |         0.01232 |         0.01232 |      0.007624 |            0.0 | 0.007624 | 32881.105309 | 0.189474 |     1.7 | 0.007624 | 1.702037 |
    | 03.01. | 0.178947 |             1.702037 |               1.694414 |          0.0 |     -0.302037 |              0.029323 |        0.029323 |        0.029323 |      0.025921 |            0.0 | 0.025921 | 46102.589814 | 0.178947 |     1.6 | 0.025921 | 1.608618 |
    | 04.01. | 0.168421 |             1.608618 |               1.582697 |          0.0 |     -0.208618 |              0.064084 |        0.064084 |        0.064084 |      0.062022 |            0.0 | 0.062022 | 55295.500328 | 0.168421 |     1.5 | 0.062022 | 1.525188 |
    | 05.01. | 0.157895 |             1.525188 |               1.463166 |          0.0 |     -0.125188 |              0.120198 |        0.120198 |        0.120198 |      0.118479 |            0.0 | 0.118479 |  58700.97886 | 0.157895 |     1.4 | 0.118479 | 1.457043 |
    | 06.01. | 0.147368 |             1.457043 |               1.338564 |     0.061436 |     -0.057043 |              0.247367 |        0.247367 |        0.247367 |      0.242243 |            0.0 | 0.242243 | 50503.784839 | 0.147368 |     1.3 | 0.242243 | 1.417039 |
    | 07.01. | 0.136842 |             1.417039 |               1.174796 |     0.225204 |     -0.017039 |               0.45567 |         0.45567 |         0.45567 |      0.397328 |            0.0 | 0.397328 | 27997.821816 | 0.136842 |     1.2 | 0.397328 | 1.418109 |
    | 08.01. | 0.126316 |             1.418109 |               1.020781 |     0.379219 |     -0.018109 |              0.608464 |        0.608464 |        0.608464 |      0.290761 |            0.0 | 0.290761 | 13789.733847 | 0.126316 |     1.1 | 0.290761 | 1.401604 |
    | 09.01. | 0.115789 |             1.401604 |               1.110843 |     0.289157 |     -0.001604 |              0.537314 |        0.537314 |        0.537314 |      0.154283 |            0.0 | 0.154283 | 10463.886844 | 0.115789 |     1.0 | 0.154283 | 1.290584 |
    | 10.01. | 0.105263 |             1.290584 |               1.136301 |     0.263699 |      0.109416 |              0.629775 |        0.629775 |        0.629775 |      0.138519 |            0.0 | 0.138519 |  7590.544301 | 0.105263 |     1.0 | 0.138519 | 1.216378 |
    | 11.01. | 0.094737 |             1.216378 |               1.077859 |     0.322141 |      0.183622 |              0.744091 |        0.744091 |        0.744091 |      0.126207 |            0.0 | 0.126207 |  4871.489513 | 0.094737 |     1.0 | 0.126207 |  1.15601 |
    | 12.01. | 0.084211 |              1.15601 |               1.029803 |     0.370197 |       0.24399 |               0.82219 |         0.82219 |         0.82219 |      0.109723 |            0.0 | 0.109723 |  2667.198079 | 0.084211 |     1.0 | 0.109723 | 1.129412 |
    | 13.01. | 0.073684 |             1.129412 |               1.019689 |     0.380311 |      0.270588 |              0.841916 |        0.841916 |        0.841916 |      0.092645 |            0.0 | 0.092645 |  1028.989492 | 0.073684 |     1.1 | 0.092645 | 1.214132 |
    | 14.01. | 0.063158 |             1.214132 |               1.121487 |     0.278513 |      0.185868 |              0.701812 |        0.701812 |        0.701812 |      0.068806 |            0.0 | 0.068806 |   540.999824 | 0.063158 |     1.2 | 0.068806 | 1.296357 |
    | 15.01. | 0.052632 |             1.296357 |               1.227551 |     0.172449 |      0.103643 |              0.533258 |        0.533258 |        0.533258 |      0.051779 |            0.0 | 0.051779 |   614.695181 | 0.052632 |     1.3 | 0.051779 | 1.376644 |
    | 16.01. | 0.042105 |             1.376644 |               1.324865 |     0.075135 |      0.023356 |              0.351863 |        0.351863 |        0.351863 |      0.035499 |            0.0 | 0.035499 |  1185.469356 | 0.042105 |     1.4 | 0.035499 | 1.457718 |
    | 17.01. | 0.031579 |             1.457718 |               1.422218 |          0.0 |     -0.057718 |              0.185207 |        0.185207 |        0.185207 |       0.02024 |            0.0 |  0.02024 |  2165.156029 | 0.031579 |     1.5 |  0.02024 | 1.540662 |
    | 18.01. | 0.021053 |             1.540662 |               1.520422 |          0.0 |     -0.140662 |              0.107697 |        0.107697 |        0.107697 |      0.012785 |            0.0 | 0.012785 |  2879.458398 | 0.021053 |     1.6 | 0.012785 | 1.626481 |
    | 19.01. | 0.010526 |             1.626481 |               1.613695 |          0.0 |     -0.226481 |              0.055458 |        0.055458 |        0.055458 |      0.006918 |            0.0 | 0.006918 |   3191.17369 | 0.010526 |     1.7 | 0.006918 |  1.71612 |
    | 20.01. |      0.0 |              1.71612 |               1.709201 |          0.0 |      -0.31612 |              0.025948 |        0.025948 |        0.012974 |      0.001631 |            0.0 | 0.001631 |  3050.215722 |      0.0 |     1.8 | 0.001631 | 1.808953 |

    So the fluctuation seems to be gone, but there is still some
    inaccuracy in the results.  Note that the last outflow value is smaller
    than the local truncation error.  However, due to the smoothing of
    the discontinuous relationship it would now be possible to define
    a lower local truncation error without to increase computation times
    too much.

    The last "drought parameter" we did no not vary so far is
    `nmblogentries`.  In the examples above, this parameter was always
    set to 1, meaning that each estimate of the `natural` discharge of
    the subcatchment was based only on the latest observation.  Using
    only the latest observation offers the advantage of quick adjustments
    of the control of the dam.  But there is a risk of the estimates being
    too uncertain and of a bad timing of water releases during periods of
    fast fluctations.

    Let us define a series of extreme fluctuations by repeating the the
    natural discharge values of 1.5 m³/s and 0.5 m³/s ten times:

    >>> natural.sequences.sim.series = 10*[1.5, 0.5]

    Also increase the inflow to 1 m³/s again, to assure that the dam is
    actually able to release as much water as has been estimated to be
    required:

    >>> input_.sequences.sim.series = 1.0

    Furthermore, assume that there is no relevant routing time between
    the outlet of the dam and the cross section downstream:

    >>> stream1.model.parameters.control.responses(((), (1.0,)))
    >>> stream1.model.parameters.update()

    The exemple is a little artificial, but exemplifies a general problem
    that might occur in different forms.  Due to the time delay of the
    information flow from the cross section to the dam, much water is
    wasted to increase the peak flows, but the violations of the low flow
    threshold remain almost unchanged:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |   watervolume | input | natural |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |           0.005 |           0.005 |      0.002727 |            0.0 | 0.002727 |  86164.379296 |   1.0 |     1.5 | 0.002727 | 1.502727 |
    | 02.01. |    1.0 |             1.502727 |                    1.5 |          0.0 |     -0.102727 |              0.140038 |        0.140038 |        0.140038 |      0.140003 |            0.0 | 0.140003 | 160468.137095 |   1.0 |     0.5 | 0.140003 | 0.640003 |
    | 03.01. |    1.0 |             0.640003 |                    0.5 |          0.9 |      0.759997 |              1.399537 |        1.399537 |        1.399537 |      1.399534 |            0.0 | 1.399534 | 125948.425467 |   1.0 |     1.5 | 1.399534 | 2.899534 |
    | 04.01. |    1.0 |             2.899534 |                    1.5 |          0.0 |     -1.499534 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 212348.380753 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 05.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 |  177799.42825 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 06.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 264199.383675 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 07.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 229650.430347 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 08.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 316050.385773 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 09.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 281501.432443 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 10.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 367901.387868 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 11.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 333352.434538 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 12.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 419752.389964 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 13.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 385203.436634 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 14.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 471603.392059 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 15.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 437054.438729 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 16.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 523454.394155 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 17.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 488905.440825 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 18.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 |  575305.39625 |   1.0 |     0.5 | 0.000001 | 0.500001 |
    | 19.01. |    1.0 |             0.500001 |                    0.5 |          0.9 |      0.899999 |              1.399872 |        1.399872 |        1.399872 |      1.399872 |            0.0 | 1.399872 | 540756.442921 |   1.0 |     1.5 | 1.399872 | 2.899872 |
    | 20.01. |    1.0 |             2.899872 |                    1.5 |          0.0 |     -1.499872 |              0.000001 |        0.000001 |        0.000001 |      0.000001 |            0.0 | 0.000001 | 627156.398346 |   1.0 |     0.5 | 0.000001 | 0.500001 |

    It seems advisable to increase the number of observations taken into
    account to estimate the natural discharge at the cross section.
    For this purpuse, the value of parameter `nmblogentries` is set to
    two days:

    >>> nmblogentries(2)

    Now the water release is relatively constant.  This does not completely
    solve the problems of wasting water during peak flows and the repeated
    violation the low flow threshold, but reduces them significantly:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |   watervolume | input | natural |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    1.0 |                  1.9 |                    1.9 |          0.0 |          -0.5 |                 0.005 |           0.005 |           0.005 |      0.002727 |            0.0 | 0.002727 |  86164.379296 |   1.0 |     1.5 | 0.002727 | 1.502727 |
    | 02.01. |    1.0 |             1.502727 |                    1.7 |          0.0 |     -0.301364 |              0.029495 |        0.029495 |        0.029495 |      0.029487 |            0.0 | 0.029487 | 170016.689857 |   1.0 |     0.5 | 0.029487 | 0.529487 |
    | 03.01. |    1.0 |             0.529487 |                    1.0 |          0.4 |      0.383893 |              0.885738 |        0.885738 |        0.885738 |      0.885738 |            0.0 | 0.885738 |  179888.93206 |   1.0 |     1.5 | 0.885738 | 2.385738 |
    | 04.01. |    1.0 |             2.385738 |                    1.0 |          0.4 |     -0.057613 |               0.58532 |         0.58532 |         0.58532 |       0.58532 |            0.0 |  0.58532 | 215717.293205 |   1.0 |     0.5 |  0.58532 |  1.08532 |
    | 05.01. |    1.0 |              1.08532 |                    1.0 |          0.4 |     -0.335529 |              0.421895 |        0.421895 |        0.421895 |      0.421895 |            0.0 | 0.421895 | 265665.599739 |   1.0 |     1.5 | 0.421895 | 1.921895 |
    | 06.01. |    1.0 |             1.921895 |                    1.0 |          0.4 |     -0.103607 |              0.539224 |        0.539224 |        0.539224 |      0.539224 |            0.0 | 0.539224 | 305476.666244 |   1.0 |     0.5 | 0.539224 | 1.039224 |
    | 07.01. |    1.0 |             1.039224 |                    1.0 |          0.4 |     -0.080559 |              0.561463 |        0.561463 |        0.561463 |      0.561463 |            0.0 | 0.561463 | 343366.270896 |   1.0 |     1.5 | 0.561463 | 2.061463 |
    | 08.01. |    1.0 |             2.061463 |                    1.0 |          0.4 |     -0.150343 |              0.500369 |        0.500369 |        0.500369 |      0.500369 |            0.0 | 0.500369 | 386534.410705 |   1.0 |     0.5 | 0.500369 | 1.000369 |
    | 09.01. |    1.0 |             1.000369 |                    1.0 |          0.4 |     -0.130916 |              0.515458 |        0.515458 |        0.515458 |      0.515458 |            0.0 | 0.515458 | 428398.852364 |   1.0 |     1.5 | 0.515458 | 2.015458 |
    | 10.01. |    1.0 |             2.015458 |                    1.0 |          0.4 |     -0.107913 |              0.535283 |        0.535283 |        0.535283 |      0.535283 |            0.0 | 0.535283 | 468550.369444 |   1.0 |     0.5 | 0.535283 | 1.035283 |
    | 11.01. |    1.0 |             1.035283 |                    1.0 |          0.4 |     -0.125371 |              0.520045 |        0.520045 |        0.520045 |      0.520045 |            0.0 | 0.520045 | 510018.479846 |   1.0 |     1.5 | 0.520045 | 2.020045 |
    | 12.01. |    1.0 |             2.020045 |                    1.0 |          0.4 |     -0.127664 |              0.518133 |        0.518133 |        0.518133 |      0.518133 |            0.0 | 0.518133 | 551651.814067 |   1.0 |     0.5 | 0.518133 | 1.018133 |
    | 13.01. |    1.0 |             1.018133 |                    1.0 |          0.4 |     -0.119089 |               0.52539 |         0.52539 |         0.52539 |       0.52539 |            0.0 |  0.52539 | 592658.106574 |   1.0 |     1.5 |  0.52539 |  2.02539 |
    | 14.01. |    1.0 |              2.02539 |                    1.0 |          0.4 |     -0.121761 |              0.523097 |        0.523097 |        0.523097 |      0.523097 |            0.0 | 0.523097 | 633862.537263 |   1.0 |     0.5 | 0.523097 | 1.023097 |
    | 15.01. |    1.0 |             1.023097 |                    1.0 |          0.4 |     -0.124244 |              0.520992 |        0.520992 |        0.520992 |      0.520992 |            0.0 | 0.520992 | 675248.786157 |   1.0 |     1.5 | 0.520992 | 2.020992 |
    | 16.01. |    1.0 |             2.020992 |                    1.0 |          0.4 |     -0.122045 |              0.522855 |        0.522855 |        0.522855 |      0.522855 |            0.0 | 0.522855 | 716474.073463 |   1.0 |     0.5 | 0.522855 | 1.022855 |
    | 17.01. |    1.0 |             1.022855 |                    1.0 |          0.4 |     -0.121924 |              0.522958 |        0.522958 |        0.522958 |      0.522958 |            0.0 | 0.522958 | 757690.477036 |   1.0 |     1.5 | 0.522958 | 2.022958 |
    | 18.01. |    1.0 |             2.022958 |                    1.0 |          0.4 |     -0.122907 |              0.522123 |        0.522123 |        0.522123 |      0.522123 |            0.0 | 0.522123 | 798979.079256 |   1.0 |     0.5 | 0.522123 | 1.022123 |
    | 19.01. |    1.0 |             1.022123 |                    1.0 |          0.4 |      -0.12254 |              0.522434 |        0.522434 |        0.522434 |      0.522434 |            0.0 | 0.522434 |  840240.80615 |   1.0 |     1.5 | 0.522434 | 2.022434 |
    | 20.01. |    1.0 |             2.022434 |                    1.0 |          0.4 |     -0.122278 |              0.522657 |        0.522657 |        0.522657 |      0.522657 |            0.0 | 0.522657 | 881483.266237 |   1.0 |     0.5 | 0.522657 | 1.022657 |

    Such negative effects due to information delay cannot be circumvented
    easily, unless one would solve the differential equations of all models
    involved simultaneously.  However, at least for drougth events (with
    much slower dynamics than flood events) these delays should normally
    be not overly important.


    The next examples are supposed to demonstrate that the flood retention
    methods are implemented properly.  Hence, all parameters related to low
    water calculations are set in a deactivating manner:

    >>> nmblogentries(1)
    >>> remotedischargeminimum(0.0)
    >>> remotedischargesavety(0.0)
    >>> neardischargeminimumthreshold(0.0)
    >>> neardischargeminimumtolerance(0.0)
    >>> waterlevelminimumthreshold(0.0)
    >>> waterlevelminimumtolerance(0.0)

    To be able to compare the following numerical results of HydPy-Dam with
    an analytical solution, we approximate a linear storage retetenion
    process.  The relationship between water level and volume has already
    been defined to be (approximately) linear in the range of 0 to 1e8 m³
    or 0 to 25 m, respectively.  The relationship between flood discharge
    and the water level is also approximately linear in this range, with a
    discharge value of 62.5 m³/s for a water level 25 m:

    >>> waterlevel2flooddischarge(
    ...         weights_input=1e-6, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2)
    >>> waterlevel2flooddischarge.plot(0.0, 25.0)

    Close the drawn figure:

    >>> pyplot.close()

    Hence, for the given simulation step size, the linear storage
    coefficient is approximately 0.054 per day.

    (Please be careful when defining such extremely large and small parameter
    values for `watervolume2waterlevel` and 'waterlevel2flooddischarge'.
    Otherwise you might get into precision loss trouble, causing the
    numerical calculations of the dam model to become very slow or the
    results to be very inaccurate.  So either use `normal` parameter values
    or check the precision of the results of `watervolume2waterlevel` and
    'waterlevel2flooddischarge' manually before performing the actual
    simulation runs.)

    Now a flood event needs to be defined:

    >>> input_.sequences.sim.series = [ 0., 1., 5., 9., 8., 5., 3., 2., 1., 0.,
    ...                                 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]

    For the sake of simplicity, a constant discharge of 1 m³/s of the
    subcatchment is assumed:

    >>> test.inits.loggedtotalremotedischarge = 1.0
    >>> natural.sequences.sim.series = 1.0

    At first, a low numerical accuracy of 0.01 m³/s is defined, which should
    be sufficient for most flood simulations for large dams:

    >>> pub.config.abs_error_max = 1e-2

    When simulating flood events, numerical stability and accuracy and
    their relation to computation time should be examined more closely.
    We use the number of function calls of the set of differential
    equations as an indicator for computation time, and set the
    corresponding counter to zero:

    >>> model.numvars.nmb_calls = 0

    You can copy can plot this table to see that the dam actually responds
    (approximately) like a linear storage:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |            0.0 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 02.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.026514 | 0.026514 |   84109.190364 |   1.0 |     1.0 | 0.026514 | 1.026514 |
    | 03.01. |    5.0 |             1.026514 |                    1.0 |          0.0 |     -1.026514 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.183744 | 0.183744 |  500233.669862 |   5.0 |     1.0 | 0.183744 | 1.183744 |
    | 04.01. |    9.0 |             1.183744 |                    1.0 |          0.0 |     -1.183744 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.542983 | 0.542983 | 1230919.977915 |   9.0 |     1.0 | 0.542983 | 1.542983 |
    | 05.01. |    8.0 |             1.542983 |                    1.0 |          0.0 |     -1.542983 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.961039 | 0.961039 | 1839086.199421 |   8.0 |     1.0 | 0.961039 | 1.961039 |
    | 06.01. |    5.0 |             1.961039 |                    1.0 |          0.0 |     -1.961039 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.251523 | 1.251523 | 2162954.619688 |   5.0 |     1.0 | 1.251523 | 2.251523 |
    | 07.01. |    3.0 |             2.251523 |                    1.0 |          0.0 |     -2.251523 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.395546 | 1.395546 | 2301579.465191 |   3.0 |     1.0 | 1.395546 | 2.395546 |
    | 08.01. |    2.0 |             2.395546 |                    1.0 |          0.0 |     -2.395546 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.453375 | 1.453375 | 2348807.855625 |   2.0 |     1.0 | 1.453375 | 2.453375 |
    | 09.01. |    1.0 |             2.453375 |                    1.0 |          0.0 |     -2.453375 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.455596 | 1.455596 | 2309444.342159 |   1.0 |     1.0 | 1.455596 | 2.455596 |
    | 10.01. |    0.0 |             2.455596 |                    1.0 |          0.0 |     -2.455596 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.405132 | 1.405132 | 2188040.908965 |   0.0 |     1.0 | 1.405132 | 2.405132 |
    | 11.01. |    0.0 |             2.405132 |                    1.0 |          0.0 |     -2.405132 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.331267 | 1.331267 | 2073019.440982 |   0.0 |     1.0 | 1.331267 | 2.331267 |
    | 12.01. |    0.0 |             2.331267 |                    1.0 |          0.0 |     -2.331267 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.261285 | 1.261285 | 1964044.449569 |   0.0 |     1.0 | 1.261285 | 2.261285 |
    | 13.01. |    0.0 |             2.261285 |                    1.0 |          0.0 |     -2.261285 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.194981 | 1.194981 |  1860798.08203 |   0.0 |     1.0 | 1.194981 | 2.194981 |
    | 14.01. |    0.0 |             2.194981 |                    1.0 |          0.0 |     -2.194981 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.132163 | 1.132163 | 1762979.194687 |   0.0 |     1.0 | 1.132163 | 2.132163 |
    | 15.01. |    0.0 |             2.132163 |                    1.0 |          0.0 |     -2.132163 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.072647 | 1.072647 | 1670302.474397 |   0.0 |     1.0 | 1.072647 | 2.072647 |
    | 16.01. |    0.0 |             2.072647 |                    1.0 |          0.0 |     -2.072647 |                   0.0 |             0.0 |             0.0 |           0.0 |        1.01626 |  1.01626 | 1582497.606486 |   0.0 |     1.0 |  1.01626 |  2.01626 |
    | 17.01. |    0.0 |              2.01626 |                    1.0 |          0.0 |      -2.01626 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.962837 | 0.962837 | 1499308.486381 |   0.0 |     1.0 | 0.962837 | 1.962837 |
    | 18.01. |    0.0 |             1.962837 |                    1.0 |          0.0 |     -1.962837 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.912222 | 0.912222 | 1420492.472175 |   0.0 |     1.0 | 0.912222 | 1.912222 |
    | 19.01. |    0.0 |             1.912222 |                    1.0 |          0.0 |     -1.912222 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.864268 | 0.864268 | 1345819.677378 |   0.0 |     1.0 | 0.864268 | 1.864268 |
    | 20.01. |    0.0 |             1.864268 |                    1.0 |          0.0 |     -1.864268 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.818835 | 0.818835 | 1275072.300303 |   0.0 |     1.0 | 0.818835 | 1.818835 |

    For a more precise evaluation, you can compare the outflow of the dam
    with the following results of the linear storage cascade with only
    one storage:

    >>> from hydpy.auxs.iuhtools import LinearStorageCascade
    >>> lsc = LinearStorageCascade(n=1, k=1.0/0.054)
    >>> from hydpy.core.objecttools import round_
    >>> round_(numpy.convolve(lsc.ma.coefs, input_.sequences.sim.series)[:20])
    0.0, 0.02652, 0.183776, 0.543037, 0.961081, 1.251541, 1.395548, 1.453371, 1.455585, 1.405116, 1.331252, 1.261271, 1.194968, 1.132151, 1.072636, 1.01625, 0.962828, 0.912214, 0.864261, 0.818829

    The largest difference occurs on January, 1. But this difference of
    0.000054 m³/s is way below the required accuracy of 0.01 m³/s.  There
    is no guarantee that the actual numerical error will always fall below
    the defined tolerance value.  However, if everything works well, we
    should at least expect so for the individual simulation time step,
    as the actual error should be better as the error estimate by one order.
    On the other hand, the accumulation of errors of individual simulation
    time steps is not controlled and might sometimes result in an violation
    of the defined tolerance value.

    To achieve the results discussed above, about 4 calls of the methods
    of the dam model were required:

    >>> model.numvars.nmb_calls
    78
    >>> model.numvars.nmb_calls = 0

    If we set the tolerance value to 1e-6 m³/s, the printed table shows
    (six decimal places) no deviation from the analytical solution of the
    linear storage:

    >>> pub.config.abs_error_max = 1e-6
    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |    watervolume | input | natural |   output |   remote |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |            0.0 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 02.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |        0.02652 |  0.02652 |   84108.629678 |   1.0 |     1.0 |  0.02652 |  1.02652 |
    | 03.01. |    5.0 |              1.02652 |                    1.0 |          0.0 |      -1.02652 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.183776 | 0.183776 |   500230.36447 |   5.0 |     1.0 | 0.183776 | 1.183776 |
    | 04.01. |    9.0 |             1.183776 |                    1.0 |          0.0 |     -1.183776 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.543037 | 0.543037 | 1230911.974815 |   9.0 |     1.0 | 0.543037 | 1.543037 |
    | 05.01. |    8.0 |             1.543037 |                    1.0 |          0.0 |     -1.543037 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.961081 | 0.961081 | 1839074.562583 |   8.0 |     1.0 | 0.961081 | 1.961081 |
    | 06.01. |    5.0 |             1.961081 |                    1.0 |          0.0 |     -1.961081 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.251541 | 1.251541 | 2162941.435394 |   5.0 |     1.0 | 1.251541 | 2.251541 |
    | 07.01. |    3.0 |             2.251541 |                    1.0 |          0.0 |     -2.251541 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.395548 | 1.395548 | 2301566.049694 |   3.0 |     1.0 | 1.395548 | 2.395548 |
    | 08.01. |    2.0 |             2.395548 |                    1.0 |          0.0 |     -2.395548 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.453371 | 1.453371 | 2348794.830447 |   2.0 |     1.0 | 1.453371 | 2.453371 |
    | 09.01. |    1.0 |             2.453371 |                    1.0 |          0.0 |     -2.453371 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.455585 | 1.455585 | 2309432.264101 |   1.0 |     1.0 | 1.455585 | 2.455585 |
    | 10.01. |    0.0 |             2.455585 |                    1.0 |          0.0 |     -2.455585 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.405116 | 1.405116 | 2188030.275196 |   0.0 |     1.0 | 1.405116 | 2.405116 |
    | 11.01. |    0.0 |             2.405116 |                    1.0 |          0.0 |     -2.405116 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.331252 | 1.331252 |  2073010.13307 |   0.0 |     1.0 | 1.331252 | 2.331252 |
    | 12.01. |    0.0 |             2.331252 |                    1.0 |          0.0 |     -2.331252 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.261271 | 1.261271 | 1964036.357462 |   0.0 |     1.0 | 1.261271 | 2.261271 |
    | 13.01. |    0.0 |             2.261271 |                    1.0 |          0.0 |     -2.261271 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.194968 | 1.194968 | 1860791.103637 |   0.0 |     1.0 | 1.194968 | 2.194968 |
    | 14.01. |    0.0 |             2.194968 |                    1.0 |          0.0 |     -2.194968 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.132151 | 1.132151 | 1762973.235287 |   0.0 |     1.0 | 1.132151 | 2.132151 |
    | 15.01. |    0.0 |             2.132151 |                    1.0 |          0.0 |     -2.132151 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.072636 | 1.072636 | 1670297.446171 |   0.0 |     1.0 | 1.072636 | 2.072636 |
    | 16.01. |    0.0 |             2.072636 |                    1.0 |          0.0 |     -2.072636 |                   0.0 |             0.0 |             0.0 |           0.0 |        1.01625 |  1.01625 |  1582493.42799 |   0.0 |     1.0 |  1.01625 |  2.01625 |
    | 17.01. |    0.0 |              2.01625 |                    1.0 |          0.0 |      -2.01625 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.962828 | 0.962828 |   1499305.0821 |   0.0 |     1.0 | 0.962828 | 1.962828 |
    | 18.01. |    0.0 |             1.962828 |                    1.0 |          0.0 |     -1.962828 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.912214 | 0.912214 |  1420489.77232 |   0.0 |     1.0 | 0.912214 | 1.912214 |
    | 19.01. |    0.0 |             1.912214 |                    1.0 |          0.0 |     -1.912214 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.864261 | 0.864261 | 1345817.617371 |   0.0 |     1.0 | 0.864261 | 1.864261 |
    | 20.01. |    0.0 |             1.864261 |                    1.0 |          0.0 |     -1.864261 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.818829 | 0.818829 |  1275070.82022 |   0.0 |     1.0 | 0.818829 | 1.818829 |

    However, this improvement in accuracy increases the computation time
    significantly.  Now 10.5 calls were required on average:

    >>> model.numvars.nmb_calls
    211
    >>> model.numvars.nmb_calls = 0

    Now we reset the local error tolerance to the more realistic value.
    But we configure the `waterlevel2flooddischarge` parameter in a
    highly reactive manner:

    >>> pub.config.abs_error_max = 1e-2
    >>> waterlevel2flooddischarge(
    ...         weights_input=1e-4, weights_output=1e7,
    ...         intercepts_hidden=0.0, intercepts_output=-1e7/2)
    >>> waterlevel2flooddischarge.plot(0.0, 25.0)

   Close the drawn figure:

    >>> pyplot.close()

    With this new parameterization of the dam model, the linear storage
    coefficient is approximately 5.4 per day.  This is why the following
    test results show virtually no retention effects:

    >>> test()
    |   date | inflow | totalremotedischarge | naturalremotedischarge | remotedemand | remotefailure | requiredremoterelease | requiredrelease | targetedrelease | actualrelease | flooddischarge |  outflow |   watervolume | input | natural |   output |   remote |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |            0.0 |      0.0 |           0.0 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 02.01. |    1.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.818699 | 0.818699 |   15664.40313 |   1.0 |     1.0 | 0.818699 | 1.818699 |
    | 03.01. |    5.0 |             1.818699 |                    1.0 |          0.0 |     -1.818699 |                   0.0 |             0.0 |             0.0 |           0.0 |        4.25814 |  4.25814 |  79761.099558 |   5.0 |     1.0 |  4.25814 |  5.25814 |
    | 04.01. |    9.0 |              5.25814 |                    1.0 |          0.0 |      -5.25814 |                   0.0 |             0.0 |             0.0 |           0.0 |       8.259255 | 8.259255 | 143761.458619 |   9.0 |     1.0 | 8.259255 | 9.259255 |
    | 05.01. |    8.0 |             9.259255 |                    1.0 |          0.0 |     -9.259255 |                   0.0 |             0.0 |             0.0 |           0.0 |       8.178598 | 8.178598 | 128330.593527 |   8.0 |     1.0 | 8.178598 | 9.178598 |
    | 06.01. |    5.0 |             9.178598 |                    1.0 |          0.0 |     -9.178598 |                   0.0 |             0.0 |             0.0 |           0.0 |       5.555424 | 5.555424 |  80341.959294 |   5.0 |     1.0 | 5.555424 | 6.555424 |
    | 07.01. |    3.0 |             6.555424 |                    1.0 |          0.0 |     -6.555424 |                   0.0 |             0.0 |             0.0 |           0.0 |       3.371696 | 3.371696 |  48227.442567 |   3.0 |     1.0 | 3.371696 | 4.371696 |
    | 08.01. |    2.0 |             4.371696 |                    1.0 |          0.0 |     -4.371696 |                   0.0 |             0.0 |             0.0 |           0.0 |       2.183878 | 2.183878 |  32340.367437 |   2.0 |     1.0 | 2.183878 | 3.183878 |
    | 09.01. |    1.0 |             3.183878 |                    1.0 |          0.0 |     -3.183878 |                   0.0 |             0.0 |             0.0 |           0.0 |       1.185158 | 1.185158 |   16342.73601 |   1.0 |     1.0 | 1.185158 | 2.185158 |
    | 10.01. |    0.0 |             2.185158 |                    1.0 |          0.0 |     -2.185158 |                   0.0 |             0.0 |             0.0 |           0.0 |       0.187346 | 0.188656 |     42.819891 |   0.0 |     1.0 | 0.188656 | 1.188656 |
    | 11.01. |    0.0 |             1.188656 |                    1.0 |          0.0 |     -1.188656 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 | 0.001338 |    -72.793845 |   0.0 |     1.0 | 0.001338 | 1.001338 |
    | 12.01. |    0.0 |             1.001338 |                    1.0 |          0.0 |     -1.001338 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 13.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 14.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 15.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 16.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 17.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 18.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 19.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |
    | 20.01. |    0.0 |                  1.0 |                    1.0 |          0.0 |          -1.0 |                   0.0 |             0.0 |             0.0 |           0.0 |       -0.00455 |      0.0 |    -72.793845 |   0.0 |     1.0 |      0.0 |      1.0 |

    The following calculations show that the dam model reaches the required
    numerical for this extreme parameterizations:

    >>> lsc.k = 1.0/5.4
    >>> round_(numpy.convolve(lsc.ma.coefs, input_.sequences.sim.series)[:20])
    0.0, 0.815651, 4.261772, 8.259271, 8.181003, 5.553864, 3.371199, 2.186025, 1.185189, 0.185185, 0.000836, 0.000004, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    However, due to the potential stiffness of this parameterization, the
    division of the different simulation steps into some substeps were
    required.  This increased the average required number of model methods
    calls to 19 per simulation step:

    >>> model.numvars.nmb_calls
    358
    >>> model.numvars.nmb_calls = 0

    Also note that the final water volume is negative due the limited
    numerical accuracy of the results.

    For common (realistic) simulations of dam retention processes, the
    stability issue disussed here should not be of big relevance.
    But one should keep it in mind when playing around with parameters
    e.g. during model calibration.  Otherwise unexpectedly long simulation
    durations might occur.

"""
# import...
# ...from standard library
from __future__ import division, print_function
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.core.modelimports import *
# ...from dam
from hydpy.models.dam import dam_model
from hydpy.models.dam import dam_control
from hydpy.models.dam import dam_derived
from hydpy.models.dam import dam_fluxes
from hydpy.models.dam import dam_states
from hydpy.models.dam import dam_logs
from hydpy.models.dam import dam_aides
from hydpy.models.dam import dam_inlets
from hydpy.models.dam import dam_outlets
from hydpy.models.dam import dam_receivers


class Model(modeltools.ModelELS):
    """Version 1 of HydPy-Dam."""

    _INLET_METHODS = (dam_model.pic_inflow_v1,
                      dam_model.pic_totalremotedischarge_v1,
                      dam_model.calc_naturalremotedischarge_v1,
                      dam_model.calc_remotedemand_v1,
                      dam_model.calc_remotefailure_v1,
                      dam_model.calc_requiredremoterelease_v1,
                      dam_model.calc_requiredrelease_v1,
                      dam_model.calc_targetedrelease_v1)
    _RECEIVER_METHODS = (dam_model.update_loggedtotalremotedischarge_v1,)
    _PART_ODE_METHODS = (dam_model.pic_inflow_v1,
                         dam_model.calc_waterlevel_v1,
                         dam_model.calc_actualrelease_v1,
                         dam_model.calc_flooddischarge_v1,
                         dam_model.calc_outflow_v1)
    _FULL_ODE_METHODS = (dam_model.update_watervolume_v1,)
    _OUTLET_METHODS = (dam_model.pass_outflow_v1,
                       dam_model.update_loggedoutflow_v1)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of HydPy-Dam, Version 1."""
    _PARCLASSES = (dam_control.NmbLogEntries,
                   dam_control.RemoteDischargeMinimum,
                   dam_control.RemoteDischargeSavety,
                   dam_control.NearDischargeMinimumThreshold,
                   dam_control.NearDischargeMinimumTolerance,
                   dam_control.WaterLevelMinimumThreshold,
                   dam_control.WaterLevelMinimumTolerance,
                   dam_control.WaterVolume2WaterLevel,
                   dam_control.WaterLevel2FloodDischarge)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of HydPy-Dam, Version 1."""
    _PARCLASSES = (dam_derived.TOY,
                   dam_derived.Seconds,
                   dam_derived.RemoteDischargeSmoothPar,
                   dam_derived.NearDischargeMinimumSmoothPar1,
                   dam_derived.NearDischargeMinimumSmoothPar2,
                   dam_derived.WaterLevelMinimumSmoothPar)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_fluxes.Inflow,
                   dam_fluxes.TotalRemoteDischarge,
                   dam_fluxes.NaturalRemoteDischarge,
                   dam_fluxes.RemoteDemand,
                   dam_fluxes.RemoteFailure,
                   dam_fluxes.RequiredRemoteRelease,
                   dam_fluxes.RequiredRelease,
                   dam_fluxes.TargetedRelease,
                   dam_fluxes.ActualRelease,
                   dam_fluxes.FloodDischarge,
                   dam_fluxes.Outflow)


class StateSequences(sequencetools.StateSequences):
    """State sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_states.WaterVolume,)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_logs.LoggedTotalRemoteDischarge,
                   dam_logs.LoggedOutflow)


class AideSequences(sequencetools.AideSequences):
    """State sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_aides.WaterLevel,)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_outlets.Q,)


class ReceiverSequences(sequencetools.LinkSequences):
    """Information link sequences of HydPy-Dam, Version 1."""
    _SEQCLASSES = (dam_receivers.Q,)


tester = Tester()
#cythonizer = Cythonizer()
#cythonizer.complete()