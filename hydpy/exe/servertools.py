# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
"""This module implements features for using *HydPy* as an HTTP server
application.

.. _`OpenDA`: https://www.openda.org/
.. _`curl`: https://curl.haxx.se/
.. _`HydPy-OpenDA-Black-Box-Model-Wrapper`: \
https://github.com/hydpy-dev/OpenDA/tree/master/extensions/\
HydPyOpenDABBModelWrapper
.. _`issue`: https://github.com/hydpy-dev/OpenDA/issues

*HydPy* is designed to be used interactively.  Consider the typical steps of
calibrating model parameters.  Usually, one first prepares an instance of
class |HydPy|, then changes some parameter values and performs a simulation,
and finally inspects whether the new simulation results are better than the
ones of the original parameterisation or not.  One can perform these steps
manually (in a Python console) or apply optimisation tools like those
provided by |scipy| (usually in a Python script).

Performing or implementing such procedures is relatively simple, as long as
all tools are written in Python or come with a Python interface, which is
not the case for some relevant optimisation tools.  One example is
`OpenDA`_, being written in Java, which was the original reason for
adding module |servertools| to the *HydPy* framework.

Module |servertools| solves such integration problems by allowing to run
*HydPy* within an HTTP server.  After starting such a server, one can use
any HTTP client (e.g. `curl`_) to perform the steps described above.

The API of the |HydPy| server is relatively simple, allowing to perform a
"normal" calibration using a few server methods only.  However, it is
also more restrictive than controlling *HydPy* within a Python process.
Within a Python process, you are free to do anything, when using the
*HydPy* server you can, more or less, control *HydPy* in a manner that has
been anticipated by the framework developers only.

Commonly but not mandatory, one configures the initial state of a *HydPy*
server with an XML file.  As an example, we prepare the `LahnH` project
by calling function |prepare_full_example_1|, which contains the XML
configuration file `multiple_runs_alpha.xml`:

>>> from hydpy.examples import prepare_full_example_1
>>> prepare_full_example_1()

To start the server in a new process, open a command-line tool and
insert the following command (see module |hyd| for general information
on how to use *HydPy* via command line):

>>> command = "hyd.py start_server 8080 LahnH multiple_runs_alpha.xml"
>>> from hydpy import run_subprocess, TestIO
>>> with TestIO():
...     process = run_subprocess(command, blocking=False, verbose=False)
...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

The *HydPy* server should now be running on port 8080.  You can use any
HTTP client to check it is working.  For example, you can print the
following URL in your web browser to get information on the types of
exchange items defined in `multiple_runs_alpha.xml` (the
`HydPy-OpenDA-Black-Box-Model-Wrapper`_ does it similarly):

>>> url = "http://localhost:8080/itemtypes"
>>> from urllib import request
>>> print(str(request.urlopen(url).read(), encoding="utf-8"))
alpha = Double0D
dill_nodes_sim_series = TimeSeries0D

In general, it is possible to control the *HydPy* server via invoking
each method with a separate HTTP request.  However, one can use methods
|HydPyServer.GET_execute| and |HydPyServer.POST_execute| alternatively
to execute a larger number of methods with only one HTTP request.
We now define three such metafunctions that change the value of parameter
|hland_control.Alpha|, perform a simulation run, and print the newly
calculated discharge at the outlet of the headwater catchment `Dill`,
respectively, very similar as the
`HydPy-OpenDA-Black-Box-Model-Wrapper`_ does.

Function `set_itemvalues` wraps the POST methods |HydPyServer.POST_timegrid|,
|HydPyServer.POST_parameteritemvalues|, and
|HydPyServer.POST_conditionitemvalues|, and also the GET method
|HydPyServer.GET_load_conditionvalues|.  These methods are executed
in the given order.  Arguments `firstdate`, `lastdate`, and `alpha` allow
changing the start and end point of the simulation period and the value
of parameter |hland_control.alpha|, respectively:

>>> def set_itemvalues(id_, firstdate, lastdate, alpha):
...     content = (f"firstdate = {firstdate}\\n"
...                f"lastdate = {lastdate}\\n"
...                f"alpha = {alpha}").encode("utf-8")
...     methods = ",".join(("POST_timegrid",
...                         "POST_parameteritemvalues",
...                         "GET_load_conditionvalues",
...                         "POST_conditionitemvalues"))
...     url = f"http://localhost:8080/execute?id={id_}&methods={methods}"
...     request.urlopen(url, data=content)

Function `simulate` wraps only GET methods and triggers the next simulation
run.  As for all GET and POST methods, one should pass the query parameter
`id`, used by the *HydPy* server for internal bookmarking:

>>> def simulate(id_):
...     methods = ",".join(("GET_simulate",
...                         "GET_save_timegrid",
...                         "GET_save_parameteritemvalues",
...                         "GET_save_conditionvalues",
...                         "GET_save_modifiedconditionitemvalues",
...                         "GET_save_getitemvalues"))
...     url = f"http://localhost:8080/execute?id={id_}&methods={methods}"
...     request.urlopen(url)

Function `print_itemvalues` also wraps only GET methods and prints the current
value of parameter |hland_control.Alpha| as well as the lastly simulated
discharge values corresponding to the given `id` value:

>>> from hydpy import print_values
>>> def print_itemvalues(id_):
...     methods = ",".join(("GET_savedtimegrid",
...                         "GET_savedparameteritemvalues",
...                         "GET_savedmodifiedconditionitemvalues",
...                         "GET_savedgetitemvalues"))
...     url = f"http://localhost:8080/execute?id={id_}&methods={methods}"
...     data = str(request.urlopen(url).read(), encoding="utf-8")
...     for line in data.split("\\n"):
...         if line.startswith("alpha"):
...             alpha = line.split("=")[1].strip()
...         if line.startswith("dill"):
...             discharge = eval(line.split("=")[1])
...     print(f"{alpha}: ", end="")
...     print_values(discharge)

For the sake of brevity, we also define `do_everything` just calling
the other functions:

>>> def do_everything(id_, firstdate, lastdate, alpha):
...     set_itemvalues(id_, firstdate, lastdate, alpha)
...     simulate(id_)
...     print_itemvalues(id_)

In the first and simplest example, we perform a simulation throughout
five days for an |hland_control.Alpha| value of 2:

>>> do_everything("1a", "1996-01-01", "1996-01-06", 2.0)
2.0: 35.537828, 7.741064, 5.018981, 4.501784, 4.238874

The second example shows interlocked simulation runs.  The first call
only triggers a simulation run for the first initialised day:

>>> do_everything("1b", "1996-01-01", "1996-01-02", 2.0)
2.0: 35.537828

The second call repeats the first one with a different `id` value:

>>> do_everything("2", "1996-01-01", "1996-01-02", 2.0)
2.0: 35.537828

The third call covers the first three initialisation days:

>>> do_everything("3", "1996-01-01", "1996-01-04", 2.0)
2.0: 35.537828, 7.741064, 5.018981

The fourth call continues the simulation of the first call, covering
the last four initialised days:

>>> do_everything("1b", "1996-01-02", "1996-01-06", 2.0)
2.0: 7.741064, 5.018981, 4.501784, 4.238874

The results of the very first call of function `do_everything` (with
`id=1`) are identical with the pulled-together discharge values of the
calls with `id=1b`, made possible by the internal bookmarking feature of
the *HydPy* server.  Here we use numbers, but any other strings are
valid `id` values.

The third example extends the second one on applying different parameter
values:

>>> do_everything("4", "1996-01-01", "1996-01-04", 2.0)
2.0: 35.537828, 7.741064, 5.018981
>>> do_everything("5", "1996-01-01", "1996-01-04", 1.0)
1.0: 11.78038, 8.901179, 7.131072
>>> do_everything("4", "1996-01-04", "1996-01-06", 2.0)
2.0: 4.501784, 4.238874
>>> do_everything("5", "1996-01-04", "1996-01-06", 1.0)
1.0: 6.017787, 5.313211
>>> do_everything("5", "1996-01-01", "1996-01-06", 1.0)
1.0: 11.78038, 8.901179, 7.131072, 6.017787, 5.313211

The order in which function `do_everything` calls its subfunctions seems quite
natural, but some tools might require do deviate from it.  For example,
`OpenDA`_ offers ensemble-based algorithms triggering the simulation
of all memberse before starting to query any simulation results.  The
fourth example shows that the underlying atomic methods do support
such an order of execution:

>>> set_itemvalues("6", "1996-01-01", "1996-01-03", 2.0)
>>> simulate("6")
>>> set_itemvalues("7", "1996-01-01", "1996-01-03", 1.0)
>>> simulate("7")
>>> print_itemvalues("6")
2.0: 35.537828, 7.741064
>>> print_itemvalues("7")
1.0: 11.78038, 8.901179
>>> set_itemvalues("6", "1996-01-03", "1996-01-06", 2.0)
>>> simulate("6")
>>> set_itemvalues("7", "1996-01-03", "1996-01-06", 1.0)
>>> simulate("7")
>>> print_itemvalues("6")
2.0: 5.018981, 4.501784, 4.238874
>>> print_itemvalues("7")
1.0: 7.131072, 6.017787, 5.313211

.. note::

   The functions `set_itemvalues` and `simulate` still need to be executed
   directly one after another.  We are not aware of an `OpenDA`_ algorithm
   deviating from this pattern.  If you know one that might be suitable
   for *HydPy* applications, please open an `issue`_.

Finally, we close the server and kill its process (just closing your
command-line tool works as well):

>>> _ = request.urlopen("http://localhost:8080/close_server")
>>> process.kill()
>>> _ = process.communicate()

The above description focussed on coupling *HydPy* to `OpenDA`_.  However,
the applied atomic submethods of class |HydPyServer| are thought to couple
*HydPy*  with other software products, as well. See the documentation on
class |HydPyServer| for further information.
"""
# import...
# ...from standard library
import collections
import copy
import mimetypes
import os

# import http.server   #  moved below for efficiency reasons
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import types
from typing import *

# ...from HydPy
import hydpy
from hydpy import conf
from hydpy.auxs import xmltools
from hydpy.core import hydpytools
from hydpy.core import itemtools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.exe import commandtools


# pylint: disable=wrong-import-position, wrong-import-order
# see the documentation on method `start_server` for explanations
mimetypes.inited = True
import http.server

mimetypes.inited = False
# pylint: enable=wrong-import-position, wrong-import-order


class ServerState:
    """Singleton class handling states like the current |HydPy| instance
    and the current exchange items.

    The instance of class |ServerState| is available the member `state` of
    module |servertools|. You could create other instances, but most
    likely, you shouldn't.  The primary purpose of this instance is to store
    information between successive initialisations of class
    |HydPyServer|.

    >>> from hydpy.exe import servertools
    >>> isinstance(servertools.state, servertools.ServerState)
    True
    """

    def __init__(self) -> None:
        self.hp: hydpytools.HydPy = None
        self.parameteritems: List[itemtools.ChangeItem] = None
        self.conditionitems: List[itemtools.ChangeItem] = None
        self.getitems: List[itemtools.GetItem] = None
        self.conditions: Dict[str, Dict[int, hydpytools.ConditionsType]] = None
        self.parameteritemvalues: Dict[str, Dict[str, Any]] = None
        self.modifiedconditionitemvalues: Dict[str, Dict[str, Any]] = None
        self.getitemvalues: Dict[str, Dict[str, str]] = None
        self.timegrids: Dict[str, timetools.Timegrid] = None
        self.init_conditions: hydpytools.ConditionsType = None
        self.idx1: int = None
        self.idx2: int = None

    def initialise(self, projectname: str, xmlfile: str) -> None:
        """Initialise a *HydPy* project based on the given XML configuration
        file agreeing with `HydPyConfigMultipleRuns.xsd`.

        We use the `LahnH` project and its (complicated) XML configuration
        file `multiple_runs.xml` as an example (module |xmltools| provides
        information on interpreting this file):

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import print_values, TestIO
        >>> from hydpy.exe.servertools import ServerState
        >>> state = ServerState()
        >>> with TestIO():    # doctest: +ELLIPSIS
        ...     state.initialise("LahnH", "multiple_runs.xml")
        Start HydPy project `LahnH` (...).
        Read configuration file `multiple_runs.xml` (...).
        Interpret the defined options (...).
        Interpret the defined period (...).
        Read all network files (...).
        Activate the selected network (...).
        Read the required control files (...).
        Read the required condition files (...).
        Read the required time series files (...).

        After initialisation, all defined exchange items are available:

        >>> for item in state.parameteritems:
        ...     print(item)
        SetItem("alpha", "hland_v1", "control.alpha", 0)
        SetItem("beta", "hland_v1", "control.beta", 0)
        SetItem("lag", "hstream_v1", "control.lag", 0)
        SetItem("damp", "hstream_v1", "control.damp", 0)
        AddItem("sfcf_1", "hland_v1", "control.sfcf", "control.rfcf", 0)
        AddItem("sfcf_2", "hland_v1", "control.sfcf", "control.rfcf", 0)
        AddItem("sfcf_3", "hland_v1", "control.sfcf", "control.rfcf", 1)
        >>> for item in state.conditionitems:
        ...     print(item)
        SetItem("sm_lahn_2", "hland_v1", "states.sm", 0)
        SetItem("sm_lahn_1", "hland_v1", "states.sm", 1)
        SetItem("quh", "hland_v1", "logs.quh", 0)
        >>> for item in state.getitems:
        ...     print(item)
        GetItem("hland_v1", "fluxes.qt")
        GetItem("hland_v1", "fluxes.qt.series")
        GetItem("hland_v1", "states.sm")
        GetItem("hland_v1", "states.sm.series")
        GetItem("nodes", "nodes.sim.series")

        The initialisation also memorises the initial conditions of
        all elements:

        >>> for element in state.init_conditions:
        ...     print(element)
        land_dill
        land_lahn_1
        land_lahn_2
        land_lahn_3
        stream_dill_lahn_2
        stream_lahn_1_lahn_2
        stream_lahn_2_lahn_3

        The initialisation also prepares all selected series arrays and
        reads the required input data:

        >>> print_values(
        ...     state.hp.elements.land_dill.model.sequences.inputs.t.series)
        -0.298846, -0.811539, -2.493848, -5.968849, -6.999618
        >>> state.hp.nodes.dill.sequences.sim.series
        InfoArray([ nan,  nan,  nan,  nan,  nan])
        """
        write = commandtools.print_textandtime
        write(f"Start HydPy project `{projectname}`")
        hp = hydpytools.HydPy(projectname)
        write(f"Read configuration file `{xmlfile}`")
        interface = xmltools.XMLInterface(xmlfile)
        write("Interpret the defined options")
        interface.update_options()
        write("Interpret the defined period")
        interface.update_timegrids()
        write("Read all network files")
        hp.prepare_network()
        write("Activate the selected network")
        hp.update_devices(
            selection=interface.fullselection,
        )
        write("Read the required control files")
        hp.prepare_models()
        write("Read the required condition files")
        interface.conditions_io.load_conditions()
        write("Read the required time series files")
        interface.series_io.prepare_series()
        interface.exchange.prepare_series()
        interface.series_io.load_series()
        self.hp = hp
        self.parameteritems = interface.exchange.parameteritems
        self.conditionitems = interface.exchange.conditionitems
        self.getitems = interface.exchange.getitems
        self.conditions = {}
        self.parameteritemvalues = collections.defaultdict(lambda: {})
        self.modifiedconditionitemvalues = collections.defaultdict(lambda: {})
        self.getitemvalues = collections.defaultdict(lambda: {})
        self.init_conditions = hp.conditions
        self.timegrids = {}


state = ServerState()


class HydPyServer(http.server.BaseHTTPRequestHandler):
    # noinspection PyUnresolvedReferences
    """The API of the *HydPy* server.

    Note that, technically, |HydPyServer| is, strictly speaking, only the HTTP
    request handler for the real HTTP server class (from the standard library).

    After initialising the *HydPy* server, each communication via a GET
    or POST request is handled by a new instance of |HydPyServer|.
    All requests are handled in a unified way through using either method
    |HydPyServer.do_GET| or [HydPyServer.do_POST|, which select and apply
    the actual GET or POST method.  All methods provided by class
    |HydPyServer| starting with "GET" or "POST"  are accessible via HTTP.

    As in the main documentation on module |servertools|, we use the
    `multiple_runs_alpha.xml` file of the `LahnH` project as an example.
    However, this time we select the more complex XML configuration file
    `multiple_runs.xml`, covering a higher number of cases:

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():
    ...     process = run_subprocess(
    ...         "hyd.py start_server 8080 LahnH multiple_runs.xml",
    ...         blocking=False, verbose=False)
    ...     result = run_subprocess(
    ...         "hyd.py await_server 8080 10", verbose=False)

    We define a test function simplifying sending the following requests,
    offering two optional arguments.  Without passing a value to `id_`,
    `test` does not add a query parameter `id` to the URL.  When passing
    a string to `data`, `test` sends a POST request, otherwise a GET request:

    >>> from urllib import request
    >>> def test(name, id_=None, data=None):
    ...     if id_ is None:
    ...         url = f"http://localhost:8080/{name}"
    ...     else:
    ...         url = f"http://localhost:8080/{name}?id={id_}"
    ...     if data is None:
    ...         response = request.urlopen(url)
    ...     else:
    ...         data = bytes(data, encoding="utf-8")
    ...         response = request.urlopen(url, data=data)
    ...     print(str(response.read(), encoding="utf-8"))

    Asking for its status tells us that the server is ready, provided that
    the selected *HydPy* project has been initialised already (which may
    take a while, depending on the size of the particular project):

    >>> test("status")
    status = ready

    |HydPyServer| returns the error code `400` if it realises the URL to be
    wrongthe and the error code `500` in all other cases of error:

    >>> test("missing")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 400: RuntimeError: \
No method `GET_missing` available.

    >>> test("parameteritemvalues", data="alpha = []")    # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: ValueError: While trying to \
execute method `POST_parameteritemvalues`, the following error occurred: \
When trying to convert the value(s) `[]` assigned to SetItem `alpha` to a \
numpy array of shape `()` and type `float`, the following error occurred: \
could not broadcast input array from shape (0,) into shape ()...

    Some methods require identity information, passed as query parameter
    `id`, used for internal bookmarking:

    >>> test("save_conditionvalues")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `GET_save_conditionvalues`, the following error occurred: \
For the GET method `save_conditionvalues` no query parameter `id` is given.

    POST methods always expect an arbitrary number of lines, each one
    assigning some values to some variable (in most cases numbers to
    exchange items):

    >>> test("parameteritems",
    ...      data=("x = y\\n"
    ...            "   \\n"
    ...            "x == y\\n"
    ...            "x = y"))
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 400: RuntimeError: The POST method \
`parameteritems` received a wrongly formated data body.  The following line \
has been extracted but cannot be further processed: `x == y`.

    Before explaining the more offical methods, we introduce the method
    |HydPyServer.POST_evaluate|, which allows evaluating any expression
    within the server process.  Its most likelely use-case ist to access
    the (sub)attributes of the single instance of class |ServerState|
    available in module |servertools|.  This method can be of help when
    being puzzled about the state of the *HydPy* server.  Use it, for
    example, to find out which |Node| objects are available and to see,
    to which one is the outlet node of |Element| object `land_dill`:

    >>> test("evaluate",
    ...      data=("nodes = state.hp.nodes\\n"
    ...            "elements = state.hp.elements.land_dill"))
    nodes = Nodes("dill", "lahn_1", "lahn_2", "lahn_3")
    elements = Element("land_dill", outlets="dill", keywords="catchment")

    Method |HydPyServer.GET_itemtypes|, already described in the
    main documentation of module |servertools|, returns all available
    exchange item types at once. However, it also possible to query those
    that are related to setting parameter values
    (|HydPyServer.GET_parameteritemtypes|), setting condition values
    (|HydPyServer.GET_conditionitemtypes|), and getting different kinds
    of values (|HydPyServer.GET_getitemtypes|) separately:

    >>> test("parameteritemtypes")
    alpha = Double0D
    beta = Double0D
    lag = Double0D
    damp = Double0D
    sfcf_1 = Double0D
    sfcf_2 = Double0D
    sfcf_3 = Double1D
    >>> test("conditionitemtypes")
    sm_lahn_2 = Double0D
    sm_lahn_1 = Double1D
    quh = Double0D
    >>> test("getitemtypes")
    land_dill_fluxes_qt = Double0D
    land_dill_fluxes_qt_series = TimeSeries0D
    land_dill_states_sm = Double1D
    land_lahn_1_states_sm = Double1D
    land_lahn_2_states_sm = Double1D
    land_lahn_3_states_sm = Double1D
    land_lahn_3_states_sm_series = TimeSeries1D
    dill_nodes_sim_series = TimeSeries0D

    One can query (|HydPyServer.GET_timegrid|) and change
    (|HydPyServer.POST_timegrid|) the current simulation
    period, which is identical with the initialisation period at first:

    >>> test("timegrid")
    firstdate = 1996-01-01T00:00:00+01:00
    lastdate = 1996-01-06T00:00:00+01:00
    stepsize = 1d
    >>> test("timegrid",
    ...      data=("firstdate = 1996-01-01\\n"
    ...            "lastdate = 1996-01-02"))
    <BLANKLINE>
    >>> test("timegrid")
    firstdate = 1996-01-01T00:00:00+01:00
    lastdate = 1996-01-02T00:00:00+01:00
    stepsize = 1d

    Eventually, one might require to memorise simulation periods for different
    simulation members.  Use method |HydPyServer.GET_save_timegrid| for
    storing and method |HydPyServer.GET_savedtimegrid| querying this kind of
    information.  Note that |HydPyServer.GET_savedtimegrid| returns the
    initialisation period instead of the simulation period when
    |HydPyServer.GET_save_timegrid| has not been called with the same `id`
    query parameter value before:

    >>> test("savedtimegrid", id_="0")
    firstdate = 1996-01-01T00:00:00+01:00
    lastdate = 1996-01-06T00:00:00+01:00
    stepsize = 1d
    >>> test("save_timegrid", id_="0")
    <BLANKLINE>
    >>> test("savedtimegrid", id_="0")
    firstdate = 1996-01-01T00:00:00+01:00
    lastdate = 1996-01-02T00:00:00+01:00
    stepsize = 1d

    Posting values of parameter items (|HydPyServer.POST_parameteritemvalues|)
    does directly update the values of the corresponding |Parameter| objects:

    >>> control = "state.hp.elements.land_dill.model.parameters.control"
    >>> test("evaluate",
    ...      data=(f"alpha = {control}.alpha\\n"
    ...            f"sfcf = {control}.sfcf"))
    alpha = alpha(1.0)
    sfcf = sfcf(1.1)
    >>> test("parameteritemvalues",
    ...      data=("alpha = 3.0\\n"
    ...            "beta = 2.0\\n"
    ...            "lag = 1.0\\n"
    ...            "damp = 0.5\\n"
    ...            "sfcf_1 = 0.3\\n"
    ...            "sfcf_2 = 0.2\\n"
    ...            "sfcf_3 = 0.1\\n"))
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=(f"alpha = {control}.alpha\\n"
    ...            f"sfcf = {control}.sfcf"))
    alpha = alpha(3.0)
    sfcf = sfcf(1.34283)

    The list of exchange items must be complete:
    >>> test("parameteritemvalues",
    ...      data=("alpha = 3.0\\n"
    ...            "beta = 2.0"))
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `POST_parameteritemvalues`, the following error occurred: \
A value for parameter item `lag` is missing.

    Note that the related GET request
    (|HydPyServer.GET_parameteritemvalues|) does return the
    lastly applied values of the exchange items instead of the modified
    values of the |Parameter| objects:

    >>> test("parameteritemvalues")
    alpha = 3.0
    beta = 2.0
    lag = 1.0
    damp = 0.5
    sfcf_1 = 0.3
    sfcf_2 = 0.2
    sfcf_3 = [ 0.1  0.1  0.1  0.1  0.1  0.1  0.1  0.1  0.1  0.1  \
0.1  0.1  0.1  0.1]

    The same is true for exchange items handling condition sequences
    via methods |HydPyServer.POST_conditionitemvalues| and
    |HydPyServer.GET_conditionitemvalues| (note that the too high
    value for |hland_states.SM| is trimmed to its highest possible value
    |hland_control.FC|):

    >>> sequences = "state.hp.elements.land_lahn_2.model.sequences"
    >>> test("evaluate",
    ...      data=(f"sm = {sequences}.states.sm \\n"
    ...            f"quh = {sequences}.logs.quh"))    # doctest: +ELLIPSIS
    sm = sm(138.31396, ..., 164.63255)
    quh = quh(0.7, 0.0)
    >>> test("conditionitemvalues",
    ...      data=("sm_lahn_2 = 246.0\\n"
    ...            "sm_lahn_1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)\\n"
    ...            "quh = 1.0\\n"))
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=(f"sm = {sequences}.states.sm\\n"
    ...            f"quh = {sequences}.logs.quh"))    # doctest: +ELLIPSIS
    sm = sm(197.0, ... 197.0)
    quh = quh(1.0, 0.0)
    >>> test("conditionitemvalues")
    sm_lahn_2 = 246.0
    sm_lahn_1 = [  1.   2.   3.   4.   5.   6.   7.   8.   9.  10.  \
11.  12.  13.]
    quh = 1.0
    >>> test("conditionitemvalues",
    ...      data="sm_lahn_2 = 246.0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `POST_conditionitemvalues`, the following error occurred: \
A value for condition item `sm_lahn_1` is missing.

    The "official" way to gain information on modified parameters or
    conditions is to use the method |HydPyServer.GET_getitemvalues|:

    >>> test("getitemvalues")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = nan
    land_dill_fluxes_qt_series = [nan]
    land_dill_states_sm = [185.13164, ...]
    land_lahn_1_states_sm = [1.0, 2.0, ..., 12.0, 13.0]
    land_lahn_2_states_sm = [197.0, ..., 197.0]
    land_lahn_3_states_sm = [101.31248, ...]
    land_lahn_3_states_sm_series = [[nan, ..., nan]]
    dill_nodes_sim_series = [nan]

    You can save both the current values of the exchange items (methods
    |HydPyServer.GET_save_parameteritemvalues| and
    |HydPyServer.GET_save_getitemvalues| for the parameter related
    |ChangeItem| objects and for the|GetItem| objects, respectively), as
    well as the values of the current condition sequences (method
    |HydPyServer.GET_save_conditionvalues| for an arbitrary `id` string:

    >>> test("save_parameteritemvalues", id_="1")
    <BLANKLINE>
    >>> test("save_getitemvalues", id_="1")
    <BLANKLINE>
    >>> test("save_conditionvalues", id_="two")
    <BLANKLINE>

    We now modify the parameter and condition values again, but this time
    in one step through calling method |HydPyServer.POST_changeitemvalues|,
    and trigger a simulation run afterwards by calling method
    |HydPyServer.GET_simulate|:

    >>> test("changeitemvalues",
    ...      data=("alpha = 1.0\\n"
    ...            "beta = 1.0\\n"
    ...            "lag = 0.0\\n"
    ...            "damp = 0.0\\n"
    ...            "sfcf_1 = 0.0\\n"
    ...            "sfcf_2 = 0.0\\n"
    ...            "sfcf_3 = 0.0\\n"
    ...            "sm_lahn_2 = 100.0\\n"
    ...            "sm_lahn_1 = 50.\\n"
    ...            "quh = .0\\n"))
    <BLANKLINE>
    >>> test("simulate")
    <BLANKLINE>
    >>> test("changeitemvalues")    # doctest: +ELLIPSIS
    alpha = 1.0
    ...
    sm_lahn_2 = 100.0
    ...

    Now both the current and the saved |GetItem| values are available by
    invoking methods|HydPyServer.GET_getitemvalues| and
    |HydPyServer.GET_savedgetitemvalues|, respectively:

    >>> test("getitemvalues")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = 7.735543
    ...
    land_lahn_2_states_sm = [99.848023, ..., 99.848023]
    ...
    dill_nodes_sim_series = [7.735543]
    >>> test("savedgetitemvalues", id_="1")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = nan
    ...
    land_lahn_2_states_sm = [197.0, ..., 197.0]
    ...
    dill_nodes_sim_series = [nan]

    The same holds for the saved |ChangeItem| values and
    methods |HydPyServer.GET_parameteritemvalues| and
    |HydPyServer.GET_savedparameteritemvalues|:

    >>> test("parameteritemvalues")    # doctest: +ELLIPSIS
    alpha = 1.0
    ...
    >>> test("savedparameteritemvalues", id_="1")    # doctest: +ELLIPSIS
    alpha = 3.0
    ...

    Be aware that, for unknown values of query parameter `id`, both
    methods |HydPyServer.GET_savedgetitemvalues| and
    |HydPyServer.GET_savedparameteritemvalues| fall back to methods
    |HydPyServer.GET_getitemvalues| and |HydPyServer.GET_parameteritemvalues|,
    respectively:

    >>> test("savedgetitemvalues", id_="?")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = 7.735543
    ...
    >>> test("savedparameteritemvalues", id_="?")    # doctest: +ELLIPSIS
    alpha = 1.0
    ...

    The *HydPy* server can memorise different exchange item values for
    different values of query parameter `id`.  Making things more complicated,
    memorisation of the actual condition values also takes the current time
    point into account.  You load conditions for the current start date
    of the simulation period, and you save them for the current end date,
    this may become more understandable by looking at the following
    example, where method |HydPyServer.GET_load_conditionvalues|
    overwrites the first soil moisture value for element `land_lahn_1`
    (99.8 mm) with different values.  The value 138.3 mm was initially
    available for the start of the first date of the initialisation
    period, the value 197.0 has been saved when the end of the first
    day of the initialisation period was identical with the end of the
    simulation period:

    >>> test("evaluate",
    ...      data=f"sm = {sequences}.states.sm")    # doctest: +ELLIPSIS
    sm = sm(99.848023, ..., 99.848023)
    >>> test("load_conditionvalues", id_="two")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=f"sm = {sequences}.states.sm")    # doctest: +ELLIPSIS
    sm = sm(138.31396, ..., 164.63255)
    >>> test("timegrid",
    ...      data=("firstdate = 1996-01-02\\n"
    ...            "lastdate = 1996-01-03"))
    <BLANKLINE>
    >>> test("load_conditionvalues", id_="two")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=f"sm = {sequences}.states.sm")    # doctest: +ELLIPSIS
    sm = sm(197.0, ..., 197.0)

    Loading condition values for a specific time point requires saving
    them before

    >>> test("timegrid",
    ...      data=("firstdate = 1996-01-04\\n"
    ...            "lastdate = 1996-01-05"))
    <BLANKLINE>
    >>> test("load_conditionvalues", id_="two")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `GET_load_conditionvalues`, the following error occurred: \
Conditions for ID `two` and time point `1996-01-04 00:00:00` are required, \
but have not been calculated so far.

    Some algorithms both provide new information about initial conditions
    but also require information on how the conditions evolve during a
    simulation run.  For such purposes, you can use method
    |HydPyServer.GET_save_modifiedconditionitemvalues| to store the current
    conditions under an arbitrary `id`, and use method
    |HydPyServer.GET_savedmodifiedconditionitemvalues| to query them later.
    Please note that these methods are not flexible enough for some
    real-world applications yet and are going to be improved later:

    >>> test("save_modifiedconditionitemvalues", id_="before")
    <BLANKLINE>
    >>> test("simulate")
    <BLANKLINE>
    >>> test("save_modifiedconditionitemvalues", id_="after")
    <BLANKLINE>
    >>> test("savedmodifiedconditionitemvalues",
    ...     id_="before")    # doctest: +ELLIPSIS
    sm_lahn_2 = [ 197.  ...]
    sm_lahn_1 = [  1.   ...]
    quh = [ 1.  0.]
    >>> test("savedmodifiedconditionitemvalues",
    ...     id_="after")    # doctest: +ELLIPSIS
    sm_lahn_2 = [ 196.621130...]
    sm_lahn_1 = [  0.99808...]
    quh = [ 0.0005...]

    To close the *HydPy* server, call |HydPyServer.GET_close_server|:

    >>> test("close_server")
    <BLANKLINE>
    >>> process.kill()
    >>> _ = process.communicate()
    """
    # pylint: disable=invalid-name
    # due to "GET" and "POST" method names in accordance
    # with BaseHTTPRequestHandler

    _requesttype: str  # either "GET" or "POST"
    _statuscode: int  # either 200, 400, or 500
    _inputs: Dict[str, str]
    _outputs: Dict[str, Any]

    def do_GET(self) -> None:
        """Select and apply the currently requested GET method."""
        self._requesttype = "GET"
        self._do_get_or_post()

    def do_POST(self) -> None:
        """Select and apply the currently requested POST method."""
        self._requesttype = "POST"
        self._do_get_or_post()

    def _do_get_or_post(self) -> None:
        self._statuscode = 200
        try:
            if self._requesttype == "POST":
                self._prepare_inputs()
            self._outputs = collections.OrderedDict()
            method = self._get_method(self._methodname)
            self._apply_method(method)
            self._write_output()
        except BaseException as exc:
            if self._statuscode not in (200, 400):
                self._statuscode = 500
            self.send_error(self._statuscode, f"{type(exc).__name__}: {exc}")

    def _prepare_inputs(self) -> None:
        content_length = int(self.headers["Content-Length"])
        string = str(self.rfile.read(content_length), encoding="utf-8")
        self._inputs = collections.OrderedDict()
        for line in string.split("\n"):
            try:
                line = line.strip()
                if line:
                    key, value = line.split("=")
                    self._inputs[key.strip()] = value.strip()
            except BaseException as exc:
                self._statuscode = 400
                raise RuntimeError(
                    f"The POST method `{self._externalname}` received a "
                    f"wrongly formated data body.  The following line has been "
                    f"extracted but cannot be further processed: `{line}`."
                ) from exc

    @property
    def _id(self) -> str:
        return self._get_queryparameter("id")

    def _get_queryparameter(self, name) -> str:
        query = urllib.parse.urlparse(self.path).query
        try:
            return urllib.parse.parse_qs(query)[name][0]
        except KeyError:
            self._statuscode = 400
            raise RuntimeError(
                f"For the {self._requesttype} method `{self._externalname}` "
                f"no query parameter `{name}` is given."
            ) from None

    @property
    def _externalname(self) -> str:
        return urllib.parse.urlparse(self.path).path[1:]

    @property
    def _methodname(self) -> str:
        return f"{self._requesttype}_{self._externalname}"

    def _get_method(self, name) -> types.MethodType:
        try:
            return getattr(self, name)
        except AttributeError:
            self._statuscode = 400
            raise RuntimeError(f"No method `{name}` available.") from None

    def _apply_method(self, method) -> None:
        try:
            method()
        except BaseException:
            self._statuscode = 500
            objecttools.augment_excmessage(
                f"While trying to execute method `{method.__name__}`"
            )

    def _write_output(self) -> None:
        string = "\n".join(f"{key} = {value}" for key, value in self._outputs.items())
        bstring = bytes(string, encoding="utf-8")
        self.send_response(self._statuscode)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bstring)

    def GET_execute(self) -> None:
        """Execute an arbitrary number of GET methods.

        The method names must be passed as query parameters, as explained
        in the main documentation on module |servertools|.
        """
        self._execute()

    def POST_execute(self) -> None:
        """Execute an arbitrary number of POST and GET methods.

        The method names must be passed as query parameters, as explained
        in the main documentation on module |servertools|.
        """
        self._execute()

    def _execute(self) -> None:
        for name in self._get_queryparameter("methods").split(","):
            self._apply_method(self._get_method(name))

    def POST_evaluate(self) -> None:
        """Evaluate any valid Python expression with the *HydPy* server
        process and get its result.

        Method |HydPyServer.POST_evaluate| serves to test and debug, primarily.
        The main documentation on module |servertools| explains its usage.
        """
        for name, value in self._inputs.items():
            result = eval(value)
            self._outputs[name] = objecttools.flatten_repr(result)

    def GET_status(self) -> None:
        """Return "status = ready" as soon as possible."""
        self._outputs["status"] = "ready"

    def GET_close_server(self) -> None:
        """Stop and close the *HydPy* server."""

        def _close_server():
            self.server.shutdown()
            self.server.server_close()

        shutter = threading.Thread(target=_close_server)
        shutter.deamon = True
        shutter.start()

    def GET_itemtypes(self) -> None:
        """Get the types of all current exchange items."""
        self.GET_changeitemtypes()
        self.GET_getitemtypes()

    def GET_changeitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change the
        values of |Parameter|, |StateSequence|, or |LogSequence| objects."""
        self.GET_parameteritemtypes()
        self.GET_conditionitemtypes()

    def GET_parameteritemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change
        the values of |Parameter| objects."""
        for item in state.parameteritems:
            self._outputs[item.name] = self._get_itemtype(item)

    def GET_conditionitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change
        the values of |StateSequence| or |LogSequence| objects."""
        for item in state.conditionitems:
            self._outputs[item.name] = self._get_itemtype(item)

    def GET_getitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to return
        the values of |Parameter| or |Sequence_| objects or the time series
        of |IOSequence| objects."""
        for item in state.getitems:
            type_ = self._get_itemtype(item)
            for name, _ in item.yield_name2value():
                self._outputs[name] = type_

    def GET_timegrid(self) -> None:
        """Get the current simulation |Timegrid|."""
        self._write_timegrid(hydpy.pub.timegrids.sim)

    def POST_timegrid(self) -> None:
        """Change the current simulation |Timegrid|."""
        init = hydpy.pub.timegrids.init
        sim = hydpy.pub.timegrids.sim
        sim.firstdate = self._inputs["firstdate"]
        sim.lastdate = self._inputs["lastdate"]
        state.idx1 = init[sim.firstdate]
        state.idx2 = init[sim.lastdate]

    @staticmethod
    def GET_simulate() -> None:
        """Perform a simulation run."""
        state.hp.simulate()

    def GET_changeitemvalues(self) -> None:
        """Get the values of all |ChangeItem| objects."""
        self.GET_parameteritemvalues()
        self.GET_conditionitemvalues()

    def POST_changeitemvalues(self) -> None:
        """Change the values of all |ChangeItem| objects and apply them
        on the respective |Variable| objects."""
        self.POST_parameteritemvalues()
        self.POST_conditionitemvalues()

    def GET_parameteritemvalues(self) -> None:
        """Get the values of all |ChangeItem| objects handling |Parameter|
        objects."""
        for item in state.parameteritems:
            self._outputs[item.name] = item.value

    def POST_parameteritemvalues(self) -> None:
        """Change the values of the relevant |ChangeItem| objects and apply
        them to their respective |Parameter| objects."""
        self._post_itemvalues("parameter", state.parameteritems)

    def GET_conditionitemvalues(self) -> None:
        """Get the values of all |ChangeItem| objects handling |StateSequence|
        or |LogSequence| objects."""
        for item in state.conditionitems:
            self._outputs[item.name] = item.value

    def POST_conditionitemvalues(self) -> None:
        """Change the values of the relevant |ChangeItem| objects and apply
        them to their respective |StateSequence| or |LogSequence| objects."""
        self._post_itemvalues("condition", state.conditionitems)

    def GET_getitemvalues(self) -> None:
        """Get the values of all |Variable| objects observed by the
        current |GetItem| objects.

        For |GetItem| objects observing time series,
        |HydPyServer.GET_getitemvalues| returns only the values within
        the current simulation period.
        """
        for item in state.getitems:
            for name, value in item.yield_name2value(state.idx1, state.idx2):
                self._outputs[name] = value

    def GET_load_conditionvalues(self) -> None:
        """Assign the |StateSequence| or |LogSequence| object values available
        for the current simulation start point to the current |HydPy| instance.

        When the simulation start point is identical with the initialisation
        time point, and you did not save conditions for it beforehand, the
        "original" initial conditions are used (usually those of the
        conditions files of the respective *HydPy*  project).
        """
        try:
            state.hp.conditions = state.conditions[self._id][state.idx1]
        except KeyError:
            if state.idx1:
                self._statuscode = 500
                raise RuntimeError(
                    f"Conditions for ID `{self._id}` and time point "
                    f"`{hydpy.pub.timegrids.sim.firstdate}` are required, "
                    f"but have not been calculated so far."
                ) from None
            state.hp.conditions = state.init_conditions

    def GET_save_conditionvalues(self) -> None:
        """Save the |StateSequence| and |LogSequence| object values of the
        current |HydPy| instance for the current simulation endpoint."""
        state.conditions[self._id] = state.conditions.get(self._id, {})
        state.conditions[self._id][state.idx2] = state.hp.conditions

    def GET_save_parameteritemvalues(self) -> None:
        """Save the values of those |ChangeItem| objects which are
        handling |Parameter| objects."""
        for item in state.parameteritems:
            state.parameteritemvalues[self._id][item.name] = item.value.copy()

    def GET_savedparameteritemvalues(self) -> None:
        """Get the previously saved values of those |ChangeItem| objects
        which are handling |Parameter| objects."""
        dict_ = state.parameteritemvalues.get(self._id)
        if dict_ is None:
            self.GET_parameteritemvalues()
        else:
            for name, value in dict_.items():
                self._outputs[name] = value

    def GET_save_modifiedconditionitemvalues(self) -> None:
        """ToDo: extend functionality"""
        for item in state.conditionitems:
            state.modifiedconditionitemvalues[self._id][item.name] = copy.deepcopy(
                list(item.device2target.values())[0].value
            )

    def GET_savedmodifiedconditionitemvalues(self) -> None:
        """ToDo: extend functionality"""
        dict_ = state.modifiedconditionitemvalues.get(self._id)
        if dict_ is None:
            self.GET_conditionitemvalues()
        else:
            for name, value in dict_.items():
                self._outputs[name] = value

    def GET_save_getitemvalues(self) -> None:
        """Save the values of all current |GetItem| objects."""
        for item in state.getitems:
            for name, value in item.yield_name2value(state.idx1, state.idx2):
                state.getitemvalues[self._id][name] = value

    def GET_savedgetitemvalues(self) -> None:
        """Get the previously saved values of all |GetItem| objects."""
        dict_ = state.getitemvalues.get(self._id)
        if dict_ is None:
            self.GET_getitemvalues()
        else:
            for name, value in dict_.items():
                self._outputs[name] = value

    def GET_save_timegrid(self) -> None:
        """Save the current simulation period."""
        state.timegrids[self._id] = copy.deepcopy(hydpy.pub.timegrids.sim)

    def GET_savedtimegrid(self) -> None:
        """Get the previously saved simulation period."""
        try:
            self._write_timegrid(state.timegrids[self._id])
        except KeyError:
            self._write_timegrid(hydpy.pub.timegrids.init)

    @staticmethod
    def _get_itemtype(item) -> str:
        if item.targetspecs.series:
            return f"TimeSeries{item.ndim-1}D"
        return f"Double{item.ndim}D"

    def _write_timegrid(self, timegrid):
        utcoffset = hydpy.pub.options.utcoffset
        self._outputs["firstdate"] = timegrid.firstdate.to_string("iso1", utcoffset)
        self._outputs["lastdate"] = timegrid.lastdate.to_string("iso1", utcoffset)
        self._outputs["stepsize"] = timegrid.stepsize

    def _post_itemvalues(self, typename, items) -> None:
        for item in items:
            try:
                value = self._inputs[item.name]
            except KeyError:
                self._statuscode = 500
                raise RuntimeError(
                    f"A value for {typename} item `{item.name}` is missing."
                ) from None
            item.value = eval(value)
            item.update_variables()


def start_server(
    socket: Union[int, str],
    projectname: str,
    xmlfilename: str,
) -> None:
    """Start the *HydPy* server using the given socket.

    The folder with the given `projectname` must be available within the
    current working directory.  The XML configuration file must be placed
    within the project folder unless `xmlfilename` is an absolute file path.
    The XML configuration file must be valid concerning the schema file
    `HydPyConfigMultipleRuns.xsd` (see class |ServerState| for further information).

    Note that function |start_server| tries to read the "mime types" from
    a dictionary stored in the file `mimetypes.txt` available in subpackage
    `conf`, and passes it as attribute `extension_map` to class |HydPyServer|.
    The reason is to avoid the long computation time of function
    |mimetypes.init| of module |mimetypes|, usually called when defining
    class `BaseHTTPRequestHandler` of module `http.server`.  If file
    `mimetypes.txt` does not exist or does not work for some reasons,
    |start_server| calls |mimetypes.init| as usual, (over)writes
    `mimetypes.txt`, and tries to proceed as expected.
    """
    confpath: str = conf.__path__[0]  # type: ignore[attr-defined, name-defined]
    filepath = os.path.join(confpath, "mimetypes.txt")
    try:
        with open(filepath) as file_:
            dict_ = eval(open(file_.read()))
    except BaseException:
        mimetypes.init()
        dict_ = mimetypes.types_map.copy()
        dict_.update(
            {
                "": "application/octet-stream",
                ".py": "text/plain",
                ".c": "text/plain",
                ".h": "text/plain",
            }
        )
        with open(filepath, "w") as file_:
            file_.write(str(dict_))
    HydPyServer.extensions_map = dict_
    state.initialise(projectname, xmlfilename)
    server = http.server.HTTPServer(("", int(socket)), HydPyServer)
    server.serve_forever()


def await_server(
    port: Union[int, str],
    seconds: Union[float, str],
) -> None:
    """Block the current process until either the *HydPy* server is responding
    on the given `port` or the given number of `seconds` elapsed.

    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     result = run_subprocess("hyd.py await_server 8080 0.1")
    Invoking hyd.py with arguments `await_server, 8080, 0.1` resulted in \
the following error:
    <urlopen error Waited for 0.1 seconds without response on port 8080.>
    ...

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> with TestIO():
    ...     process = run_subprocess(
    ...         "hyd.py start_server 8080 LahnH multiple_runs.xml",
    ...         blocking=False, verbose=False)
    ...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

    >>> from urllib import request
    >>> _ = request.urlopen("http://localhost:8080/close_server")
    >>> process.kill()
    >>> _ = process.communicate()
    """
    now = time.perf_counter()
    end = now + float(seconds)
    while now <= end:
        try:
            urllib.request.urlopen(f"http://localhost:{port}/status")
            break
        except urllib.error.URLError:
            time.sleep(0.1)
            now = time.perf_counter()
    else:
        raise urllib.error.URLError(
            f"Waited for {seconds} seconds without response on port {port}."
        )
