# -*- coding: utf-8 -*-
"""This module facilitates using *HydPy* as an HTTP server application.

.. _`OpenDA`: https://www.openda.org/
.. _`curl`: https://curl.haxx.se/
.. _`HydPy-OpenDA-Black-Box-Model-Wrapper`: \
https://github.com/hydpy-dev/OpenDA/tree/master/extensions/\
HydPyOpenDABBModelWrapper
.. _`issue`: https://github.com/hydpy-dev/OpenDA/issues

*HydPy* is designed to be used interactively or by executing individual Python scripts.
Consider the typical steps of calibrating model parameters.  Usually, one first
prepares an instance of class |HydPy|, then changes some parameter values and performs
a simulation, and finally inspects whether the new simulation results are better than
the ones of the original parameterisation or not.  One can perform these steps
manually (in a Python console) or apply optimisation tools like those provided by
|scipy| (usually in a Python script).

Performing or implementing such procedures is relatively simple, as long as all tools
are written in Python or come with a Python interface, which is not the case for some
relevant optimisation tools.  One example is `OpenDA`_, being written in Java, which
was the original reason for adding module |servertools| to the *HydPy* framework.

Module |servertools| solves such integration problems by running *HydPy* within an
HTTP server.  After starting such a server, one can use any HTTP client (e.g. `curl`_)
to perform the above steps.

The server's API is relatively simple, allowing performing a "normal" calibration using
only a few server methods.  However, it is also more restrictive than controlling
*HydPy* within a Python process.  Within a Python process, you are free to do anything.
Using the *HydPy* server, you are much more restricted to what was anticipated by the
framework developers.

Commonly but not mandatory, one configures the initial state of a *HydPy* server with
an XML file.  As an example, we prepare the `HydPy-H-Lahn` project by calling function
|prepare_full_example_1|, which contains the XML configuration file
`multiple_runs_alpha.xml`:

>>> from hydpy.core.testtools import prepare_full_example_1
>>> prepare_full_example_1()

To start the server in a new process, open a command-line tool and insert the following
command (see module |hyd| for general information on how to use *HydPy* via the command
line):

>>> command = "hyd.py start_server 8080 HydPy-H-Lahn multiple_runs_alpha.xml"
>>> from hydpy import run_subprocess, TestIO
>>> with TestIO():
...     process = run_subprocess(command, blocking=False, verbose=False)
...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

The *HydPy* server should now be running on port 8080.  You can use any HTTP client to
check it is working.  For example, you can type the following URLs in your web browser
to get information on the types and initial values of the exchange items defined in
`multiple_runs_alpha.xml` (in a format required by the
`HydPy-OpenDA-Black-Box-Model-Wrapper`_):

>>> from urllib import request
>>> url = "http://127.0.0.1:8080/query_itemtypes"
>>> print(str(request.urlopen(url).read(), encoding="utf-8"))
alpha = Double0D
dill_assl_nodes_sim_series = TimeSeries0D

>>> url = "http://127.0.0.1:8080/query_initialitemvalues"
>>> print(str(request.urlopen(url).read(), encoding="utf-8"))
alpha = 2.0
dill_assl_nodes_sim_series = [nan, nan, nan, nan, nan]

It is generally possible to control the *HydPy* server via invoking each method with a
separate HTTP request.  However, alternatively, one can use methods
|HydPyServer.GET_execute| and |HydPyServer.POST_execute| to execute many methods with
only one HTTP request.  We now define three such metafunctions.  The first one changes
the value of the parameter |hland_control.Alpha|  The second one runs a simulation.
The third one prints the newly calculated discharge at the outlet of the headwater
catchment `Dill`.  All of this is very similar to what the
`HydPy-OpenDA-Black-Box-Model-Wrapper`_ does.

Function `set_itemvalues` wraps the POST methods
|HydPyServer.POST_register_simulationdates|,
|HydPyServer.POST_register_parameteritemvalues|, and
|HydPyServer.POST_register_conditionitemvalues|.  The *HydPy* server will execute
these methods in the given order.   The arguments `firstdate_sim`, `lastdate_sim`,
and `alpha` allow changing the start and end date of the simulation period and the
value of parameter |hland_control.alpha| later:

>>> def set_itemvalues(id_, firstdate, lastdate, alpha):
...     content = (f"firstdate_sim = {firstdate}\\n"
...                f"lastdate_sim = {lastdate}\\n"
...                f"alpha = {alpha}").encode("utf-8")
...     methods = ",".join(("POST_register_simulationdates",
...                         "POST_register_parameteritemvalues",
...                         "POST_register_conditionitemvalues"))
...     url = f"http://127.0.0.1:8080/execute?id={id_}&methods={methods}"
...     request.urlopen(url, data=content)

Function `simulate` wraps only GET methods and triggers the next simulation run.  As
for all GET and POST methods, one should pass the query parameter `id`, used by the
*HydPy* server for internal bookmarking:

>>> def simulate(id_):
...     methods = ",".join(("GET_activate_simulationdates",
...                         "GET_activate_parameteritemvalues",
...                         "GET_load_internalconditions",
...                         "GET_activate_conditionitemvalues",
...                         "GET_simulate",
...                         "GET_save_internalconditions",
...                         "GET_update_conditionitemvalues",
...                         "GET_update_getitemvalues"))
...     url = f"http://127.0.0.1:8080/execute?id={id_}&methods={methods}"
...     request.urlopen(url)

Function `print_itemvalues` also wraps only GET methods and prints the current value of
parameter |hland_control.Alpha| as well as the lastly simulated discharge values
corresponding to the given `id` value:

>>> from hydpy import print_vector
>>> def print_itemvalues(id_):
...     methods = ",".join(("GET_query_simulationdates",
...                         "GET_query_parameteritemvalues",
...                         "GET_query_conditionitemvalues",
...                         "GET_query_getitemvalues"))
...     url = f"http://127.0.0.1:8080/execute?id={id_}&methods={methods}"
...     data = str(request.urlopen(url).read(), encoding="utf-8")
...     for line in data.split("\\n"):
...         if line.startswith("alpha"):
...             alpha = line.split("=")[1].strip()
...         if line.startswith("dill_assl"):
...             discharge = eval(line.split("=")[1])
...     print(f"{alpha}: ", end="")
...     print_vector(discharge)

For the sake of brevity, we also define `do_everything` for calling the other functions
at once:

>>> def do_everything(id_, firstdate, lastdate, alpha):
...     set_itemvalues(id_, firstdate, lastdate, alpha)
...     simulate(id_)
...     print_itemvalues(id_)

In the simplest example, we perform a simulation throughout five days for an
|hland_control.Alpha| value of 2:

>>> do_everything("1a", "1996-01-01", "1996-01-06", 2.0)
2.0: 35.494358, 7.730125, 5.01782, 4.508775, 4.244626

The following example shows interlocked simulation runs.  The first call only triggers
a simulation run for the first initialised day:

>>> do_everything("1b", "1996-01-01", "1996-01-02", 2.0)
2.0: 35.494358

The second call repeats the first one with a different `id` value:

>>> do_everything("2", "1996-01-01", "1996-01-02", 2.0)
2.0: 35.494358

The third call covers the first three initialisation days:

>>> do_everything("3", "1996-01-01", "1996-01-04", 2.0)
2.0: 35.494358, 7.730125, 5.01782

The fourth call continues the simulation of the first call, covering the last four
initialised days:

>>> do_everything("1b", "1996-01-02", "1996-01-06", 2.0)
2.0: 7.730125, 5.01782, 4.508775, 4.244626

The results of the very first call of function `do_everything` (with`id=1`) are
identical with the pulled-together discharge values of the calls with `id=1b`, made
possible by the internal bookmarking feature of the *HydPy* server.  Here we use
numbers, but any other strings are valid `id` values.

This example extends the last one by applying different parameter values:

>>> do_everything("4", "1996-01-01", "1996-01-04", 2.0)
2.0: 35.494358, 7.730125, 5.01782
>>> do_everything("5", "1996-01-01", "1996-01-04", 1.0)
1.0: 11.757526, 8.865079, 7.101815
>>> do_everything("4", "1996-01-04", "1996-01-06", 2.0)
2.0: 4.508775, 4.244626
>>> do_everything("5", "1996-01-04", "1996-01-06", 1.0)
1.0: 5.994195, 5.301584
>>> do_everything("5", "1996-01-01", "1996-01-06", 1.0)
1.0: 11.757526, 8.865079, 7.101815, 5.994195, 5.301584

The order in which function `do_everything` calls its subfunctions seems quite natural,
but some tools might require do deviate from it.  For example, `OpenDA`_ offers
ensemble-based algorithms triggering the simulation of all memberse before starting to
query any simulation results.  The final example shows that the underlying atomic
methods support such an execution sequence:

>>> set_itemvalues("6", "1996-01-01", "1996-01-03", 2.0)
>>> simulate("6")
>>> set_itemvalues("7", "1996-01-01", "1996-01-03", 1.0)
>>> simulate("7")
>>> print_itemvalues("6")
2.0: 35.494358, 7.730125
>>> print_itemvalues("7")
1.0: 11.757526, 8.865079

When working in parallel mode, `OpenDA`_ might not always call the functions
`set_itemvalues` and `simulate` for the same `id` directly one after another, which
also causes no problem:

>>> set_itemvalues("6", "1996-01-03", "1996-01-06", 2.0)
>>> set_itemvalues("7", "1996-01-03", "1996-01-06", 1.0)
>>> simulate("6")
>>> simulate("7")
>>> print_itemvalues("6")
2.0: 5.01782, 4.508775, 4.244626
>>> print_itemvalues("7")
1.0: 7.101815, 5.994195, 5.301584

Finally, we close the server and kill its process (just closing your command-line tool
works likewise):

>>> _ = request.urlopen("http://127.0.0.1:8080/close_server")
>>> process.kill()
>>> _ = process.communicate()

The above description focussed on coupling *HydPy* to `OpenDA`_.  However, the applied
atomic submethods of class |HydPyServer| also allow coupling *HydPy*  with other
software products. See the documentation on class |HydPyServer| for further information.
"""
# import...
# ...from standard library
from __future__ import annotations
import collections
import mimetypes
import os

# import http.server  # moved below for efficiency reasons
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import types

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import conf
from hydpy import config
from hydpy.core import hydpytools
from hydpy.core import itemtools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.exe import commandtools
from hydpy.exe import xmltools
from hydpy.core.typingtools import *


# pylint: disable=wrong-import-position, wrong-import-order
# see the documentation on method `start_server` for explanations
mimetypes.inited = True
import http.server

mimetypes.inited = False
# pylint: enable=wrong-import-position, wrong-import-order


ID = NewType("ID", str)
ID.__doc__ = """Type for strings that identify "artificial" *HydPy* instances (from a 
client's point of view)."""


class ServerState:
    """Singleton class handling states like the current |HydPy| instance exchange items.

    The instance of class |ServerState| is available as the member `state` of class
    |HydPyServer| after calling the function |start_server|.  You could create other
    instances (like we do in the following examples), but you most likely shouldn't.
    The primary purpose of this instance is to store information between successive
    initialisations of class |HydPyServer|.

    We use the `HydPy-H-Lahn` project and its (complicated) XML configuration file
    `multiple_runs.xml` as an example (module |xmltools| provides information on
    interpreting this file):

    >>> from hydpy.core.testtools import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import print_vector, TestIO
    >>> from hydpy.exe.servertools import ServerState
    >>> with TestIO():  # doctest: +ELLIPSIS
    ...     state = ServerState("HydPy-H-Lahn", "multiple_runs.xml")
    Start HydPy project `HydPy-H-Lahn` (...).
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
    SetItem("alpha", "hland_96", "control.alpha", None, "global")
    SetItem("beta", "hland_96", "control.beta", None, "global")
    SetItem("lag", "musk_classic", "control.nmbsegments", "lag", "global")
    SetItem("damp", "musk_classic", "control.coefficients", "damp", "global")
    AddItem("sfcf_1", "hland_96", "control.sfcf", "control.rfcf", "global")
    AddItem("sfcf_2", "hland_96", "control.sfcf", "control.rfcf", "global")
    AddItem("sfcf_3", "hland_96", "control.sfcf", "control.rfcf", "subunit")
    MultiplyItem("k4", "hland_96", "control.k4", "control.k", "global")
    >>> for item in state.conditionitems:
    ...     print(item)
    SetItem("ic_lahn_leun", "hland_96", "states.ic", None, "device")
    SetItem("ic_lahn_marb", "hland_96", "states.ic", None, "subunit")
    SetItem("sm_lahn_leun", "hland_96", "states.sm", None, "device")
    SetItem("sm_lahn_marb", "hland_96", "states.sm", None, "subunit")
    SetItem("quh", "rconc_uh", "logs.quh", None, "device")
    >>> for item in state.getitems:
    ...     print(item)
    GetItem("?", "hland_96", "factors.contriarea")
    GetItem("current_discharge", "hland_96", "fluxes.qt")
    GetItem("entire_discharge_series", "hland_96", "fluxes.qt.series")
    GetItem("?", "hland_96", "states.sm")
    GetItem("?", "hland_96", "states.sm.series")
    GetItem("?", "nodes", "nodes.sim.series")

    The initialisation also memorises the initial conditions of all elements:

    >>> for element in state.init_conditions:
    ...     print(element)
    land_dill_assl
    land_lahn_kalk
    land_lahn_leun
    land_lahn_marb
    stream_dill_assl_lahn_leun
    stream_lahn_leun_lahn_kalk
    stream_lahn_marb_lahn_leun

    The initialisation also prepares all selected series arrays and reads the
    required input data:

    >>> print_vector(state.hp.elements.land_dill_assl.model.sequences.inputs.t.series)
    0.0, -0.5, -2.4, -6.8, -7.8
    >>> state.hp.nodes.dill_assl.sequences.sim.series
    InfoArray([nan, nan, nan, nan, nan])
    """

    interface: xmltools.XMLInterface
    hp: hydpytools.HydPy
    parameteritems: list[itemtools.ChangeItem]
    inputitems: list[itemtools.SetItem]
    conditionitems: list[itemtools.SetItem]
    outputitems: list[itemtools.SetItem]
    getitems: list[itemtools.GetItem]
    conditions: dict[ID, dict[int, Conditions]]
    parameteritemvalues: dict[ID, dict[Name, Any]]
    inputitemvalues: dict[ID, dict[Name, Any]]
    conditionitemvalues: dict[ID, dict[Name, Any]]
    outputitemvalues: dict[ID, dict[Name, Any]]
    getitemvalues: dict[ID, dict[Name, str]]
    initialparameteritemvalues: dict[Name, Any]
    initialinputitemvalues: dict[Name, Any]
    initialconditionitemvalues: dict[Name, Any]
    initialgetitemvalues: dict[Name, Any]
    timegrids: dict[ID, timetools.Timegrid]
    init_conditions: Conditions
    inputconditiondirs: dict[ID, str]
    outputconditiondirs: dict[ID, str]
    serieswriterdirs: dict[ID, str]
    seriesreaderdirs: dict[ID, str]
    outputcontroldirs: dict[ID, str]
    idx1: int
    idx2: int

    def __init__(
        self,
        projectname: str,
        xmlfile: str,
        load_conditions: bool = True,
        load_series: bool = True,
    ) -> None:
        write = commandtools.print_textandtime
        write(f"Start HydPy project `{projectname}`")
        hp = hydpytools.HydPy(projectname)
        write(f"Read configuration file `{xmlfile}`")
        self.interface = xmltools.XMLInterface(xmlfile)
        write("Interpret the defined options")
        self.interface.update_options()
        write("Interpret the defined period")
        self.interface.update_timegrids()
        write("Read all network files")
        self.interface.network_io.prepare_network()
        write("Create the custom selections (if defined)")
        self.interface.update_selections()
        write("Activate the selected network")
        hp.update_devices(selection=self.interface.fullselection, silent=True)
        write("Read the required control files")
        self.interface.control_io.prepare_models()
        if load_conditions:
            write("Read the required condition files")
            self.interface.conditions_io.load_conditions()
        if load_series:
            write("Read the required time series files")
        self.interface.series_io.prepare_series()
        self.interface.exchange.prepare_series()
        if load_series:
            self.interface.series_io.load_series()
        self.hp = hp
        self.parameteritems = self.interface.exchange.parameteritems
        self.inputitems = self.interface.exchange.inputitems
        self.conditionitems = self.interface.exchange.conditionitems
        self.outputitems = self.interface.exchange.outputitems
        self.getitems = self.interface.exchange.getitems
        self.initialparameteritemvalues = {
            item.name: item.value for item in self.parameteritems
        }
        self.initialinputitemvalues = {
            item.name: item.value for item in self.inputitems
        }
        self.initialconditionitemvalues = {
            item.name: item.value for item in self.conditionitems
        }
        self.initialoutputitemvalues = {
            item.name: item.value for item in self.outputitems
        }
        self.initialgetitemvalues = {
            name: value
            for item in self.getitems
            for name, value in item.yield_name2value(*hydpy.pub.timegrids.simindices)
        }
        self.conditions = {}
        self.parameteritemvalues = {}
        self.inputitemvalues = {}
        self.conditionitemvalues = {}
        self.outputitemvalues = {}
        self.getitemvalues = {}
        self.init_conditions = hp.conditions
        self.timegrids = {}
        self.serieswriterdirs = {}
        self.seriesreaderdirs = {}
        self.inputconditiondirs = {}
        self.outputconditiondirs = {}
        self.outputcontroldirs = {}
        self.idx1 = 0
        self.idx2 = 0


class HydPyServer(http.server.BaseHTTPRequestHandler):
    """The API of the *HydPy* server.

    Technically and strictly speaking, |HydPyServer| is, only the HTTP request handler
    for the real HTTP server class (from the standard library).

    After initialising the *HydPy* server, each communication via a GET or POST request
    is handled by a new instance of |HydPyServer|.  This handling occurs in a unified
    way using either method |HydPyServer.do_GET| or [HydPyServer.do_POST|, which select
    and apply the actual GET or POST method.  All methods provided by class
    |HydPyServer| starting with "GET" or "POST" are accessible via HTTP.

    In the main documentation on module |servertools|, we use the
    `multiple_runs_alpha.xml` file of the `HydPy-H-Lahn` project as an example.
    However, now we select the more complex XML configuration file `multiple_runs.xml`,
    covering a higher number of cases:

    >>> from hydpy.core.testtools import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():
    ...     process = run_subprocess(
    ...         "hyd.py start_server 8080 HydPy-H-Lahn multiple_runs.xml "
    ...         "debugging=enable",
    ...         blocking=False,
    ...         verbose=False,
    ...     )
    ...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

    We define a test function that simplifies sending the following requests and offers
    two optional arguments.  When passing a value to `id_`, `test` adds this value as
    the query parameter `id` to the URL.  When passing a string to `data`, `test` sends
    a POST request containing the given data; otherwise, a GET request without
    additional data:

    >>> from urllib import request
    >>> def test(name, id_=None, data=None, return_result=False):
    ...     url = f"http://127.0.0.1:8080/{name}"
    ...     if id_:
    ...         url = f"{url}?id={id_}"
    ...     if data:
    ...         data = bytes(data, encoding="utf-8")
    ...     response = request.urlopen(url, data=data)
    ...     result = str(response.read(), encoding="utf-8")
    ...     print(result)
    ...     return result if return_result else None

    Asking for its status tells us that the server is ready (which may take a while,
    depending on the project's size):

    >>> test("status")
    status = ready

    You can query the current version number of the *HydPy* installation used to start
    the server:

    >>> result = test("version", return_result=True)  # doctest: +ELLIPSIS
    version = ...
    >>> hydpy.__version__ in result
    True

    |HydPyServer| returns the error code `400` if it realises the URL to be wrong:

    >>> test("missing")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 400: RuntimeError: No method `GET_missing` \
available.

    The error code is `500` in all other cases of error:

    >>> test("register_parameteritemvalues", id_="0", data="alpha = []")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `POST_register_parameteritemvalues`, the following error occurred: A value for \
parameter item `beta` is missing.

    Some methods require identity information, passed as query parameter `id`, used for
    internal bookmarking:

    >>> test("query_parameteritemvalues")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_parameteritemvalues`, the following error occurred: For the GET \
method `query_parameteritemvalues` no query parameter `id` is given.

    POST methods always expect an arbitrary number of lines, each one assigning some
    values to some variable (in most cases, numbers to exchange items):

    >>> test("parameteritemvalues",
    ...      id_="a",
    ...      data=("x = y\\n"
    ...            "   \\n"
    ...            "x == y\\n"
    ...            "x = y"))
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 400: RuntimeError: The POST method \
`parameteritemvalues` received a wrongly formated data body.  The following line has \
been extracted but cannot be further processed: `x == y`.

    Before explaining the more offical methods, we introduce the method
    |HydPyServer.POST_evaluate|, which evaluates arbitrary valid Python code within the
    server process.  Its most likely use-case is to access the (sub)attributes of the
    single instance of class |ServerState|, available as a member of class
    |HydPyServer|.  This method can help when being puzzled about the state of the
    *HydPy* server.  Use it, for example, to find out which |Node| objects are
    available and to see which one is the outlet node of the |Element| object
    `land_dill_assl`:

    >>> test("evaluate",
    ...      data=("nodes = HydPyServer.state.hp.nodes\\n"
    ...            "elements = HydPyServer.state.hp.elements.land_dill_assl"))
    nodes = Nodes("dill_assl", "lahn_kalk", "lahn_leun", "lahn_marb")
    elements = Element("land_dill_assl", outlets="dill_assl", keywords="catchment")

    Method |HydPyServer.GET_query_itemtypes|, already described in the main
    documentation of module |servertools|, returns all available exchange item types
    at once.  However, it is also possible to query those that are related to setting
    parameter values (|HydPyServer.GET_query_parameteritemtypes|), setting condition
    values (|HydPyServer.GET_query_conditionitemtypes|), setting input time series
    (|HydPyServer.GET_query_inputitemtypes|), getting values or series of factors or
    fluxes in the "setitem style" (|HydPyServer.GET_query_outputitemtypes|) and getting
    different kinds of values or series in the "getitem style"
    (|HydPyServer.GET_query_getitemtypes|) separately:

    >>> test("query_parameteritemtypes")
    alpha = Double0D
    beta = Double0D
    lag = Double0D
    damp = Double0D
    sfcf_1 = Double0D
    sfcf_2 = Double0D
    sfcf_3 = Double1D
    k4 = Double0D
    >>> test("query_conditionitemtypes")
    ic_lahn_leun = Double1D
    ic_lahn_marb = Double1D
    sm_lahn_leun = Double1D
    sm_lahn_marb = Double1D
    quh = Double1D
    >>> test("query_inputitemtypes")
    t_headwaters = TimeSeries1D
    >>> test("query_outputitemtypes")
    swe_headwaters = TimeSeries1D
    >>> test("query_getitemtypes")
    land_dill_assl_factors_contriarea = Double0D
    land_dill_assl_fluxes_qt = Double0D
    land_dill_assl_fluxes_qt_series = TimeSeries0D
    land_dill_assl_states_sm = Double1D
    land_lahn_kalk_states_sm = Double1D
    land_lahn_leun_states_sm = Double1D
    land_lahn_marb_states_sm = Double1D
    land_lahn_kalk_states_sm_series = TimeSeries1D
    dill_assl_nodes_sim_series = TimeSeries0D

    The same holds for the initial values of the exchange items.  Method
    |HydPyServer.GET_query_initialitemvalues| returns them all at once, while the
    methods |HydPyServer.GET_query_initialparameteritemvalues|,
    |HydPyServer.GET_query_initialconditionitemvalues|,
    |HydPyServer.GET_query_initialinputitemvalues|,
    |HydPyServer.GET_query_initialoutputitemvalues|, and
    (|HydPyServer.GET_query_initialgetitemvalues| return the relevant subgroup only.
    Note that for the exchange items related to state sequence |hland_states.SM|
    (`sm_lahn_marb` and `sm_lahn_leun`), the initial values stem from the XML file.
    For the items related to state sequence |hland_states.Ic| and input sequence
    |hland_inputs.T|, the XML file does not provide such information.  Thus, the
    initial values of `ic_lahn_marb`, `ic_lahn_leun`, and `t_headwaters` stem from the
    corresponding sequences themselves (and thus, indirectly, from the respective
    condition and time series files):

    >>> test("query_initialparameteritemvalues")
    alpha = 2.0
    beta = 1.0
    lag = 5.0
    damp = 0.5
    sfcf_1 = 0.3
    sfcf_2 = 0.2
    sfcf_3 = [0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.2, 0.2]
    k4 = 10.0
    >>> test("query_initialconditionitemvalues")
    ic_lahn_leun = [1.184948]
    ic_lahn_marb = [0.96404, 1.36332, 0.96458, 1.46458, 0.96512, 1.46512, 0.96565, \
1.46569, 0.96617, 1.46617, 0.96668, 1.46668, 1.46719]
    sm_lahn_leun = [123.0]
    sm_lahn_marb = [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, \
200.0, 210.0, 220.0, 230.0]
    quh = [10.0]
    >>> test("query_initialinputitemvalues")
    t_headwaters = [[0.0, -0.5, -2.4, -6.8, -7.8], [-0.7, -1.5, -4.6, -8.2, -8.7]]
    >>> test("query_initialoutputitemvalues")
    swe_headwaters = [[nan, nan, nan, nan, nan], [nan, nan, nan, nan, nan]]
    >>> test("query_initialgetitemvalues")  # doctest: +ELLIPSIS
    land_dill_assl_factors_contriarea = nan
    land_dill_assl_fluxes_qt = nan
    land_dill_assl_fluxes_qt_series = [nan, nan, nan, nan, nan]
    land_dill_assl_states_sm = [185.13164...]
    land_lahn_kalk_states_sm = [101.31248...]
    land_lahn_leun_states_sm = [138.31396...]
    land_lahn_marb_states_sm = [99.27505...]
    land_lahn_kalk_states_sm_series = [[nan, ...], [nan, ...], ..., [nan, ...]]
    dill_assl_nodes_sim_series = [nan, nan, nan, nan, nan]

    Some external tools require ways to identify specific sub-values of different
    exchange items.  For example, they need to map those sub-values to location data
    available in a separate database. Method |HydPyServer.GET_query_itemsubnames|
    provides artificial sub names suitable for such a mapping. See property
    |ChangeItem.subnames| of class |ChangeItem| and method |GetItem.yield_name2subnames|
    of class |GetItem| for the specification of the sub names. Here, note the special
    handling for change items addressing the `global` level, for which we cannot define
    a meaningful sub name.  Method |HydPyServer.GET_query_itemsubnames| returns the
    string `*global*` in such cases:

    >>> test("query_itemsubnames") # doctest: +ELLIPSIS
    alpha = *global*
    beta = *global*
    lag = *global*
    damp = *global*
    sfcf_1 = *global*
    sfcf_2 = *global*
    sfcf_3 = [land_lahn_kalk_0, ..., land_lahn_kalk_13]
    k4 = *global*
    t_headwaters = [land_dill_assl, land_lahn_marb]
    ic_lahn_leun = [land_lahn_leun]
    ic_lahn_marb = [land_lahn_marb_0, ..., land_lahn_marb_12]
    sm_lahn_leun = [land_lahn_leun]
    sm_lahn_marb = [land_lahn_marb_0, ..., land_lahn_marb_12]
    quh = [land_lahn_leun]
    swe_headwaters = [land_dill_assl, land_lahn_marb]
    land_dill_assl_factors_contriarea = land_dill_assl
    land_dill_assl_fluxes_qt = land_dill_assl
    land_dill_assl_fluxes_qt_series = land_dill_assl
    land_dill_assl_states_sm = ('land_dill_assl_0', ..., 'land_dill_assl_11')
    land_lahn_kalk_states_sm = ('land_lahn_kalk_0', ..., 'land_lahn_kalk_13')
    land_lahn_leun_states_sm = ('land_lahn_leun_0', ..., 'land_lahn_leun_9')
    land_lahn_marb_states_sm = ('land_lahn_marb_0', ..., 'land_lahn_marb_12')
    land_lahn_kalk_states_sm_series = ('land_lahn_kalk_0', ..., 'land_lahn_kalk_13')
    dill_assl_nodes_sim_series = dill_assl

    The |Timegrids.init| time grid is immutable once the server is ready.  Method
    |HydPyServer.GET_query_initialisationtimegrid| returns the fixed first date, last
    date, and stepsize of the whole initialised period:

    >>> test("query_initialisationtimegrid")
    firstdate_init = 1996-01-01T00:00:00+01:00
    lastdate_init = 1996-01-06T00:00:00+01:00
    stepsize = 1d

    The dates of the |Timegrids.sim| time grid, on the other hand, are mutable and can
    vary for different `id` query parameters.  This flexibility makes things a little
    more complicated, as the |Timegrids| object of the global |pub| module handles only
    one |Timegrids.sim| object at once.  Hence, we differentiate between registered
    simulation dates of the respective `id` values and the current simulation dates of
    the |Timegrids| object.

    Method |HydPyServer.GET_query_simulationdates| asks for registered simulation dates
    and thus fails at first:

    >>> test("query_simulationdates", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_simulationdates`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.

    After logging new simulation dates via the POST method
    |HydPyServer.POST_register_simulationdates|, method
    |HydPyServer.GET_query_simulationdates| returns them correctly:

    >>> test("register_simulationdates", id_="0",
    ...      data=("firstdate_sim = 1996-01-01\\n"
    ...            "lastdate_sim = 1996-01-02"))
    <BLANKLINE>
    >>> test("query_simulationdates", id_="0")
    firstdate_sim = 1996-01-01T00:00:00+01:00
    lastdate_sim = 1996-01-02T00:00:00+01:00

    Our initial call to the POST method |HydPyServer.POST_register_simulationdates| did
    not affect the currently active simulation dates.  We need to do this manually by
    calling method |HydPyServer.GET_activate_simulationdates|:

    >>> test("evaluate", data="lastdate = hydpy.pub.timegrids.sim.lastdate")
    lastdate = Date("1996-01-06T00:00:00")
    >>> test("activate_simulationdates", id_="0")
    <BLANKLINE>
    >>> test("evaluate", data="lastdate = hydpy.pub.timegrids.sim.lastdate")
    lastdate = Date("1996-01-02 00:00:00")

    Generally, passing a missing `id` while others are available results in error
    messages like the following:

    >>> test("activate_simulationdates", id_="1")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_activate_simulationdates`, the following error occurred: Nothing \
registered under the id `1`.  The available ids are: 0.

    The logic of the parameter-related GET and POST methods is very similar to the one
    of the simulation date-related methods discussed above.  Method
    |HydPyServer.POST_register_parameteritemvalues| registers new values of the
    exchange items, and method |HydPyServer.GET_activate_parameteritemvalues| activates
    them (assigns them to the relevant parameters):

    >>> test("register_parameteritemvalues", id_="0",
    ...      data=("alpha = 3.0\\n"
    ...            "beta = 2.0\\n"
    ...            "lag = 1.0\\n"
    ...            "damp = 0.5\\n"
    ...            "sfcf_1 = 0.3\\n"
    ...            "sfcf_2 = 0.2\\n"
    ...            "sfcf_3 = 0.1\\n"
    ...            "k4 = 10.0\\n"))
    <BLANKLINE>
    >>> control = ("HydPyServer.state.hp.elements.land_dill_assl.model.parameters."
    ...            "control")
    >>> test("evaluate",
    ...      data=(f"alpha = {control}.alpha\\n"
    ...            f"sfcf = {control}.sfcf"))
    alpha = alpha(1.0)
    sfcf = sfcf(1.1)

    >>> test("activate_parameteritemvalues", id_="0")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=(f"alpha = {control}.alpha\\n"
    ...            f"sfcf = {control}.sfcf"))
    alpha = alpha(3.0)
    sfcf = sfcf(1.34283)

    The list of exchange items must be complete:

    >>> test("register_parameteritemvalues", id_="0",
    ...      data=("alpha = 3.0\\n"
    ...            "beta = 2.0"))
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `POST_register_parameteritemvalues`, the following error occurred: A value for \
parameter item `lag` is missing.

    Note that the related query method (|HydPyServer.GET_query_parameteritemvalues|)
    returns the logged values of the |ChangeItem| objects instead of the (eventually
    modified) values of the |Parameter| objects:

    >>> test("query_parameteritemvalues", id_="0")
    alpha = 3.0
    beta = 2.0
    lag = 1.0
    damp = 0.5
    sfcf_1 = 0.3
    sfcf_2 = 0.2
    sfcf_3 = 0.1
    k4 = 10.0

    The condition-related methods |HydPyServer.POST_register_conditionitemvalues|,
    |HydPyServer.GET_activate_conditionitemvalues|, and
    |HydPyServer.GET_query_conditionitemvalues| work like the parameter-related
    methods described above:

    >>> test("register_conditionitemvalues", id_="0",
    ...      data=("sm_lahn_leun = 246.0\\n"
    ...            "sm_lahn_marb = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]\\n"
    ...            "ic_lahn_leun = 642.0\\n"
    ...            "ic_lahn_marb = [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]\\n"
    ...            "quh = 1.0\\n"))
    <BLANKLINE>
    >>> test("query_conditionitemvalues", id_="0")
    ic_lahn_leun = 642.0
    ic_lahn_marb = [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    sm_lahn_leun = 246.0
    sm_lahn_marb = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    quh = 1.0

    Note the trimming of the too-high value for the state sequence |hland_states.SM| to
    its highest possible value defined by control parameter |hland_control.FC|):

    >>> for element in ("land_lahn_marb", "land_lahn_leun"):
    ...     path_element = f"HydPyServer.state.hp.elements.{element}"
    ...     path_sequences_model = f"{path_element}.model.sequences"
    ...     path_sequences_submodel = f"{path_element}.model.rconcmodel.sequences"
    ...     test("evaluate",  # doctest: +ELLIPSIS
    ...          data=(f"sm = {path_sequences_model}.states.sm \\n"
    ...                f"quh = {path_sequences_submodel}.logs.quh"))
    sm = sm(99.27505, ..., 142.84148)
    quh = quh(0.0)
    sm = sm(138.31396, ..., 164.63255)
    quh = quh(0.7, 0.0)
    >>> test("activate_conditionitemvalues", id_="0")
    <BLANKLINE>
    >>> for element in ("land_lahn_marb", "land_lahn_leun"):
    ...     path_element = f"HydPyServer.state.hp.elements.{element}"
    ...     path_sequences_model = f"{path_element}.model.sequences"
    ...     path_sequences_submodel = f"{path_element}.model.rconcmodel.sequences"
    ...     test("evaluate",  # doctest: +ELLIPSIS
    ...          data=(f"sm = {path_sequences_model}.states.sm \\n"
    ...                f"quh = {path_sequences_submodel}.logs.quh"))
    sm = sm(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0)
    quh = quh(0.0)
    sm = sm(197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0)
    quh = quh(1.0, 0.0)

    The methods |HydPyServer.POST_register_inputitemvalues|,
    |HydPyServer.GET_activate_inputitemvalues|, and
    |HydPyServer.GET_query_inputitemvalues| always focus on the currently relevant
    simulation time grid:

    >>> test("update_inputitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_inputitemvalues", id_="0")
    t_headwaters = [[0.0], [-0.7]]
    >>> t = "HydPyServer.state.hp.elements.land_lahn_marb.model.sequences.inputs.t"
    >>> test("evaluate", data=(f"t_series = {t}.series\\n"
    ...                        f"t_simseries = {t}.simseries\\n"))
    t_series = InfoArray([-0.7, -1.5, -4.6, -8.2, -8.7])
    t_simseries = InfoArray([-0.7])

    >>> test("register_inputitemvalues", id_="0",
    ...      data="t_headwaters = [[1.0], [2.0]]\\n")
    <BLANKLINE>
    >>> test("activate_inputitemvalues", id_="0")
    <BLANKLINE>
    >>> test("evaluate", data=(f"t_series = {t}.series\\n"
    ...                        f"t_simseries = {t}.simseries\\n"))
    t_series = InfoArray([ 2. , -1.5, -4.6, -8.2, -8.7])
    t_simseries = InfoArray([2.])

    The "official" way to gain information on modified parameters or conditions is to
    use the method |HydPyServer.GET_query_getitemvalues|:

    >>> test("query_getitemvalues", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_getitemvalues`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.

    As the error message explains, we first need to fill the registry for the given
    `id` parameter.  Unlike the examples above, we do not do this by sending external
    data via a POST request but by retrieving the server's currently active data.  We
    accomplish this task by calling the GET method
    |HydPyServer.GET_update_getitemvalues|:

    >>> test("update_getitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_getitemvalues", id_="0")  # doctest: +ELLIPSIS
    land_dill_assl_factors_contriarea = nan
    land_dill_assl_fluxes_qt = nan
    land_dill_assl_fluxes_qt_series = [nan]
    land_dill_assl_states_sm = [185.13164, ...]
    land_lahn_kalk_states_sm = [101.31248, ...]
    land_lahn_leun_states_sm = [197.0, ..., 197.0]
    land_lahn_marb_states_sm = [1.0, 2.0, ..., 12.0, 13.0]
    land_lahn_kalk_states_sm_series = [[nan, ..., nan]]
    dill_assl_nodes_sim_series = [nan]

    Besides the "official" way for retrieving information (which we sometimes call the
    "getitem style"), some sequences types (namely those derived from |FactorSequence|
    and |FluxSequence|) also allow retrieving information in the so-called "setitem
    style" via the methods |HydPyServer.GET_update_outputitemvalues| and
    |HydPyServer.GET_query_outputitemvalues|:

    >>> test("query_outputitemvalues", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_outputitemvalues`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.
    >>> test("update_outputitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_outputitemvalues", id_="0")
    swe_headwaters = [[nan], [nan]]

    We now modify the parameter, condition, and input time series values again, but
    this time in one step through calling |HydPyServer.POST_register_changeitemvalues|
    and |HydPyServer.GET_activate_changeitemvalues|:

    >>> test("register_changeitemvalues", id_="0",
    ...      data=("alpha = 1.0\\n"
    ...            "beta = 1.0\\n"
    ...            "lag = 0.0\\n"
    ...            "damp = 0.0\\n"
    ...            "sfcf_1 = 0.0\\n"
    ...            "sfcf_2 = 0.0\\n"
    ...            "sfcf_3 = 0.0\\n"
    ...            "k4 = 5.0\\n"
    ...            "ic_lahn_marb = 1.0\\n"
    ...            "ic_lahn_leun = 2.0\\n"
    ...            "sm_lahn_marb = 50.0\\n"
    ...            "sm_lahn_leun = 100.0\\n"
    ...            "quh = 0.0\\n"
    ...            "t_headwaters = [[-0.29884643], [-0.70539496]]\\n"))
    <BLANKLINE>
    >>> test("activate_changeitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_changeitemvalues", id_="0")  # doctest: +ELLIPSIS
    alpha = 1.0
    beta = 1.0
    lag = 0.0
    damp = 0.0
    sfcf_1 = 0.0
    sfcf_2 = 0.0
    sfcf_3 = 0.0
    k4 = 5.0
    t_headwaters = [[-0.29884...], [-0.70539...]]
    ic_lahn_leun = 2.0
    ic_lahn_marb = 1.0
    sm_lahn_leun = 100.0
    sm_lahn_marb = 50.0
    quh = 0.0

    Next, we trigger a simulation run by calling the GET method
    |HydPyServer.GET_simulate|:

    >>> test("simulate", id_="0")
    <BLANKLINE>

    Calling methods |HydPyServer.GET_update_getitemvalues| and
    |HydPyServer.GET_query_getitemvalues| as well as methods
    |HydPyServer.GET_update_outputitemvalues| and
    |HydPyServer.GET_query_outputitemvalues| reveals how the simulation results:

    >>> test("update_getitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_getitemvalues", id_="0")  # doctest: +ELLIPSIS
    land_dill_assl_factors_contriarea = 0.759579
    land_dill_assl_fluxes_qt = 5.508952
    ...
    land_lahn_leun_states_sm = [100.341052, ..., 100.0]
    ...
    dill_assl_nodes_sim_series = [5.508952]
    >>> test("update_outputitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_outputitemvalues", id_="0")
    swe_headwaters = [[0.074231], [0.0]]

    So far, we have explained how the *HydPy* server memorises different exchange item
    values for different values of query parameter `id`.  Complicating matters,
    memorising condition values must also consider the relevant time point.  You load
    conditions for the simulation period's current start date with method
    |HydPyServer.GET_load_internalconditions| and save them for the current end date
    with method |HydPyServer.GET_save_internalconditions|.  For example, we first save
    the states calculated for the end time of the last simulation run (January 2):

    >>> test("query_simulationdates", id_="0")
    firstdate_sim = 1996-01-01T00:00:00+01:00
    lastdate_sim = 1996-01-02T00:00:00+01:00
    >>> test("evaluate",
    ...      data=f"sm_lahn2 = {path_sequences_model}.states.sm")  # doctest: +ELLIPSIS
    sm_lahn2 = sm(100.341052, ..., 100.0)
    >>> test("save_internalconditions", id_="0")
    <BLANKLINE>

    Calling method |HydPyServer.GET_load_internalconditions| without changing the
    simulation dates reloads the initial conditions for January 1, originally read from
    disk:

    >>> test("load_internalconditions", id_="0")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=f"sm_lahn2 = {path_sequences_model}.states.sm")  # doctest: +ELLIPSIS
    sm_lahn2 = sm(138.31396, ..., 164.63255)

    If we set the first date of the simulation period to January 2, method
    |HydPyServer.GET_load_internalconditions| loads the conditions we saved for
    January 2 previously:

    >>> test("register_simulationdates", id_="0",
    ...      data=("firstdate_sim = 1996-01-02\\n"
    ...            "lastdate_sim = 1996-01-03"))
    <BLANKLINE>
    >>> test("activate_simulationdates", id_="0")
    <BLANKLINE>
    >>> test("load_internalconditions", id_="0")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=f"sm_lahn2 = {path_sequences_model}.states.sm")  # doctest: +ELLIPSIS
    sm_lahn2 = sm(100.341052, ..., 100.0)

    Loading condition values for a specific time point requires saving them before:

    >>> test("register_simulationdates", id_="0",
    ...      data=("firstdate_sim = 1996-01-03\\n"
    ...            "lastdate_sim = 1996-01-05"))
    <BLANKLINE>
    >>> test("activate_simulationdates", id_="0")
    <BLANKLINE>
    >>> test("load_internalconditions", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_load_internalconditions`, the following error occurred: Conditions for \
ID `0` and time point `1996-01-03 00:00:00` are required, but have not been \
calculated so far.

    For example, when restarting data assimilation subsequent forecasting periods, you
    might need to get and set all internal conditions from the client side.  Then, you
    have two options.  The more efficient way relies on methods
    |HydPyServer.GET_query_internalconditions| and
    |HydPyServer.POST_register_internalconditions|.  Method
    |HydPyServer.GET_query_internalconditions| returns the information registered for
    the end of the current simulation period.  All data is within a single nested
    |dict| object (created  by the |HydPy.conditions| property of class |HydPy|):

    >>> test("register_simulationdates", id_="0",
    ...      data=("firstdate_sim = 1996-01-01\\n"
    ...            "lastdate_sim = 1996-01-02"))
    <BLANKLINE>
    >>> test("activate_simulationdates", id_="0")
    <BLANKLINE>
    >>> conditions = test("query_internalconditions", id_="0",
    ...                   return_result=True)[13:]  # doctest: +ELLIPSIS
    conditions = {'land_dill_assl': {'model': {'states': {'ic': array([0.73040403, \
1.23040403, 0.73046025...

    Due to the steps above, the returned dictionary agrees with the current state of
    the |HydPy| instance:

    >>> sequences = f"HydPyServer.state.hp.elements.land_dill_assl.model.sequences"
    >>> test("evaluate",
    ...      data=f"ic_dill_assl = {sequences}.states.ic")  # doctest: +ELLIPSIS
    ic_dill_assl = ic(0.730404, 1.230404, 0.73046,...

    To show that registering new internal conditions also works, we first convert the
    string representation of the data to actual Python objects by using Python's |eval|
    function.  Therefore, we need to clarify that "array" means the array creation
    function |numpy.array| of |numpy|:

    >>> import numpy
    >>> conditions = eval(conditions, {"array": numpy.array})

    Next, we modify an arbitrary state and convert the dictionary back to a single-line
    string:

    >>> conditions["land_dill_assl"]["model"]["states"]["ic"][:2] = 0.5, 2.0
    >>> conditions = str(conditions).replace("\\n", " ")

    Now we can send the modified data back to the server by using the
    |HydPyServer.POST_register_internalconditions| method, which stores it for the
    start of the simulation period:

    >>> test("register_internalconditions", id_="0", data=f"conditions = {conditions}")
    <BLANKLINE>
    >>> ic_dill_assl = ("self.state.conditions['0'][0]['land_dill_assl']['model']"
    ...                 "['states']['ic']")
    >>> test("evaluate",
    ...      data=f"ic_dill_assl = {ic_dill_assl}")  # doctest: +ELLIPSIS
    ic_dill_assl = array([0.5       , 2.        , 0.73046025...

    After calling method |HydPyServer.GET_load_internalconditions|, the freshly
    registered states are ready to be used by the next simulation run:

    >>> test("load_internalconditions", id_="0")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=f"ic_dill_assl = {sequences}.states.ic")  # doctest: +ELLIPSIS
    ic_dill_assl = ic(0.5, 2.0, 0.73046,...

    Keeping the internal conditions for multiple time points can use plenty of RAM.
    Use the GET method |HydPyServer.GET_deregister_internalconditions| to remove all
    conditions data available under the given `id` to avoid that:

    >>> test("query_internalconditions", id_="0")  # doctest: +ELLIPSIS
    conditions = {'land_dill_assl': {'model': {'states': {'ic': array([0.7304...
    >>> test("deregister_internalconditions", id_="0")
    <BLANKLINE>
    >>> test("query_internalconditions", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_internalconditions`, the following error occurred: No internal \
conditions registered under the id `0` for `1996-01-02 00:00:00`.

    Some algorithms provide new information about initial conditions and require
    information on how they evolve during a simulation.  For such purposes, you can
    use method |HydPyServer.GET_update_conditionitemvalues| to store the current
    conditions under an arbitrary `id` and use method
    |HydPyServer.GET_query_conditionitemvalues| to query them later.  Note that this
    approach so far only works when using |SetItem| objects that modify their target
    sequence on the `device` or `subunit` level (please tell us if you encounter other
    relevant use-cases):

    >>> test("update_conditionitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_conditionitemvalues", id_="0")  # doctest: +ELLIPSIS
    ic_lahn_leun = [0.955701]
    ic_lahn_marb = [0.7421...]
    sm_lahn_leun = [100.1983...]
    sm_lahn_marb = [49.9304...]
    quh = [0.000395]

    The second option for handling multiple "simultaneous" initial conditions is
    telling the *HydPy* server to read them from and write them to disk, which is
    easier but often less efficient due to higher IO activity.  Use methods
    |HydPyServer.GET_load_conditions| and |HydPyServer.GET_save_conditions| for this
    purpose.  Reading from or writing to different directories than those defined in
    `multiple_runs.xml` requires registering them beforehand.  If we, for example,
    create a new empty directory with method
    |HydPyServer.POST_register_inputconditiondir|, loading conditions from it must
    fail:

    >>> test("register_inputconditiondir", id_="0", data="inputconditiondir = new")
    <BLANKLINE>
    >>> test("load_conditions", id_="0")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: FileNotFoundError: While trying to \
execute method `GET_load_conditions`, the following error occurred: While trying to \
load the initial conditions of element `land_dill_assl`, the following error occurred: \
[Errno 2] No such file or directory: ...land_dill_assl.py'

    >>> test("register_outputconditiondir", id_="0", data="outputconditiondir = new")
    <BLANKLINE>
    >>> test("save_conditions", id_="0")
    <BLANKLINE>

    Hence, we better first write suitable conditions into the new directory:

    >>> lz_dill_assl = "self.state.hp.elements.land_dill_assl.model.sequences.states.lz"
    >>> test("evaluate", data=f"lz_dill_assl = {lz_dill_assl}")  # doctest: +ELLIPSIS
    lz_dill_assl = lz(9.493...)

    To prove reading and writing conditions works, we first set the current value of
    sequence |hland_states.LZ| of catchment "Dill" to zero:

    >>> test("evaluate", data=f"nothing = {lz_dill_assl}(0.0)")
    nothing = None
    >>> test("evaluate", data=f"lz_dill_assl = {lz_dill_assl}")
    lz_dill_assl = lz(0.0)

    As expected, applying |HydPyServer.GET_load_conditions| on the previously written
    data resets the value of |hland_states.LZ|:

    >>> test("load_conditions", id_="0")
    <BLANKLINE>
    >>> test("evaluate", data=f"lz_dill_assl = {lz_dill_assl}")  # doctest: +ELLIPSIS
    lz_dill_assl = lz(9.493...)

    Use the GET methods |HydPyServer.GET_query_inputconditiondir| and
    |HydPyServer.GET_deregister_inputconditiondir| to query or remove the currently
    registered input condition directory:

    >>> test("query_inputconditiondir", id_="0")
    inputconditiondir = new
    >>> test("deregister_inputconditiondir", id_="0")
    <BLANKLINE>
    >>> test("query_inputconditiondir", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_inputconditiondir`, the following error occurred: Nothing \
registered under the id `0`.  There is nothing registered, so far.

    Use the GET methods |HydPyServer.GET_query_outputconditiondir| and
    |HydPyServer.GET_deregister_outputconditiondir| to query or remove the currently
    registered output condition directory:

    >>> test("query_outputconditiondir", id_="0")
    outputconditiondir = new
    >>> test("deregister_outputconditiondir", id_="0")
    <BLANKLINE>
    >>> test("query_outputconditiondir", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_outputconditiondir`, the following error occurred: Nothing \
registered under the id `0`.  There is nothing registered, so far.

    Above, we explained the recommended way to query the initial values of all or a
    subgroup of the available exchange items.  Alternatively, you can first register
    the initial values and query them later, which is a workaround for retrieving
    initial and intermediate values with the same HTTP request (an `OpenDA`_
    requirement):

    >>> test("register_initialitemvalues", id_="1")
    <BLANKLINE>
    >>> test("query_itemvalues", id_="1")  # doctest: +ELLIPSIS
    alpha = 2.0
    beta = 1.0
    lag = 5.0
    damp = 0.5
    sfcf_1 = 0.3
    sfcf_2 = 0.2
    sfcf_3 = [0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.2, 0.2, 0.2]
    k4 = 10.0
    t_headwaters = [[0.0, -0.5, -2.4, -6.8, -7.8], [-0.7, -1.5, -4.6, -8.2, -8.7]]
    ic_lahn_leun = [1.18494...]
    ic_lahn_marb = [0.96404...]
    sm_lahn_leun = [123.0]
    sm_lahn_marb = [110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, \
200.0, 210.0, 220.0, 230.0]
    quh = [10.0]
    swe_headwaters = [[nan, nan, nan, nan, nan], [nan, nan, nan, nan, nan]]
    land_dill_assl_factors_contriarea = nan
    land_dill_assl_fluxes_qt = nan
    land_dill_assl_fluxes_qt_series = [nan, nan, nan, nan, nan]
    land_dill_assl_states_sm = [185.13164...]
    land_lahn_kalk_states_sm = [101.31248...]
    land_lahn_leun_states_sm = [138.31396...]
    land_lahn_marb_states_sm = [99.27505...]
    land_lahn_kalk_states_sm_series = [[nan, ...], [nan, ...], ..., [nan, ...]]
    dill_assl_nodes_sim_series = [nan, nan, nan, nan, nan]

    In contrast to running a single simulation via method |run_simulation|, the *HydPy*
    server does (usually) not write calculated time series automatically.  Instead, one
    must manually call method |HydPyServer.GET_save_allseries|:

    >>> test("save_allseries", id_="0")
    <BLANKLINE>

    According to the fixed configuration of `multiple_runs.xml`,
    |HydPyServer.GET_save_allseries| wrote averaged soil moisture values into the
    directory `mean_sm`:

    >>> import netCDF4
    >>> from hydpy import print_vector
    >>> filepath = "HydPy-H-Lahn/series/mean_sm/hland_96_state_sm_mean.nc"
    >>> with TestIO(), netCDF4.Dataset(filepath) as ncfile:
    ...     print_vector(ncfile["hland_96_state_sm_mean"][:, 0])
    211.467386, 0.0, 0.0, 0.0, 0.0

    To save the results of subsequent simulations without overwriting the previous
    ones, change the current series writer directory by the GET method
    |HydPyServer.POST_register_serieswriterdir|:

    >>> test("register_serieswriterdir", id_="0", data="serieswriterdir = sm_averaged")
    <BLANKLINE>
    >>> test("save_allseries", id_="0")
    <BLANKLINE>
    >>> filepath = "HydPy-H-Lahn/series/sm_averaged/hland_96_state_sm_mean.nc"
    >>> with TestIO(), netCDF4.Dataset(filepath) as ncfile:
    ...     print_vector(ncfile["hland_96_state_sm_mean"][:, 0])
    211.467386, 0.0, 0.0, 0.0, 0.0

    |HydPyServer.GET_deregister_serieswriterdir| removes the currently set directory
    from the registry so that the HydPy server falls back to the
    configuration of `multiple_runs.xml`:

    >>> test("query_serieswriterdir", id_="0")
    serieswriterdir = sm_averaged
    >>> test("deregister_serieswriterdir", id_="0")
    <BLANKLINE>
    >>> test("query_serieswriterdir", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_serieswriterdir`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.

    The same holds for time series to be written "just in time" during simulation runs.
    The `temperature` writer in `multiple_runs.xml` select the `jit` mode.  This
    setting triggered that the *HydPy* server wrote the time series of sequences
    |hland_inputs.T| and |evap_inputs.NormalAirTemperature| to the directory
    `temperature` during the last simulation:

    >>> filepath = "HydPy-H-Lahn/series/temperature/hland_96_input_t.nc"
    >>> with TestIO(), netCDF4.Dataset(filepath) as ncfile:
    ...     print_vector(ncfile["hland_96_input_t"][:, 0])
    -0.298846, 0.0, 0.0, 0.0, 0.0

    The input sequences |hland_inputs.P| and |evap_inputs.NormalEvapotranspiration| are
    instead reading their time series "just in time" (reading and writing data for the
    same |IOSequence| object is not supported).  We query the last read value of
    |evap_inputs.NormalEvapotranspiration| for the Dill catchment:

    >>> submodel = ("HydPyServer.state.hp.elements.land_dill_assl.model.aetmodel."
    ...             "petmodel")
    >>> net = f"{submodel}.sequences.inputs.normalevapotranspiration"
    >>> test("evaluate", data=f"net_dill_assl = {net}")  # doctest: +ELLIPSIS
    net_dill_assl = normalevapotranspiration(0.3)

    We can change the series writer directory before starting another simulation run to
    write the time series of |hland_inputs.T| and |evap_inputs.NormalAirTemperature| to
    another
    directory:

    >>> test("register_serieswriterdir", id_="0", data="serieswriterdir = temp")
    <BLANKLINE>
    >>> test("simulate", id_="0")
    <BLANKLINE>
    >>> filepath = "HydPy-H-Lahn/series/temp/hland_96_input_t.nc"
    >>> with TestIO(), netCDF4.Dataset(filepath) as ncfile:
    ...     print_vector(ncfile["hland_96_input_t"][:, 0])
    -0.298846, 0.0, 0.0, 0.0, 0.0

    The "just in time" reading of the series of |hland_inputs.P| and
    |evap_inputs.NormalEvapotranspiration| still worked, showing the registered series
    directory "temp" only applied for writing data:

    >>> test("evaluate", data=f"net_dill_assl = {net}")  # doctest: +ELLIPSIS
    net_dill_assl = normalevapotranspiration(0.3)

    Changing the series reader directory works as explained for the series writer
    directory.  After setting it to an empty folder, |HydPyServer.GET_load_allseries|
    and |HydPyServer.GET_simulate| cannot find suitable files and report this problem:

    >>> test("register_seriesreaderdir", id_="0", data="seriesreaderdir = no_data")
    <BLANKLINE>
    >>> test("query_seriesreaderdir", id_="0")
    seriesreaderdir = no_data

    >>> test("load_allseries", id_="0")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: FileNotFoundError: While trying to \
execute method `GET_load_allseries`, the following error occurred: While trying to \
load the time series data of sequence `t` of element `land_dill_assl`, the following \
error occurred: [Errno 2] No such file or directory: \
...land_dill_assl_hland_96_input_t.asc'

    >>> test("simulate", id_="0")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: FileNotFoundError: While trying to \
execute method `GET_simulate`, the following error occurred: While trying to prepare \
NetCDF files for reading or writing data "just in time" during the current simulation \
run, the following error occurred: No file `...hland_96_input_p.nc` available for \
reading.

    After deregistering the "no_data" directory, both methods work again:

    >>> test("deregister_seriesreaderdir", id_="0")
    <BLANKLINE>
    >>> test("query_seriesreaderdir", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_seriesreaderdir`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.

    >>> test("load_allseries", id_="0")
    <BLANKLINE>
    >>> test("simulate", id_="0")
    <BLANKLINE>

    As described for time series, one must explicitly pass (comparable) requests to
    the *HydPy* Server to let it write parameter control files.  The control files
    reflect the current parameter values of all model instances:

    >>> test("register_outputcontroldir", id_="0", data="outputcontroldir = calibrated")
    <BLANKLINE>
    >>> test("query_outputcontroldir", id_="0")
    outputcontroldir = calibrated

    >>> test("save_controls", id_="0")
    <BLANKLINE>
    >>> with TestIO(), open("HydPy-H-Lahn/control/calibrated/"
    ...                     "land_dill_assl.py") as file_:
    ...     print(file_.read())  # doctest: +ELLIPSIS
    # -*- coding: utf-8 -*-
    <BLANKLINE>
    from hydpy.models.hland_96 import *
    from hydpy.models import evap_aet_hbv96
    from hydpy.models import evap_pet_hbv96
    from hydpy.models import rconc_uh
    <BLANKLINE>
    simulationstep("1d")
    parameterstep("1d")
    ...
    beta(1.0)
    ...

    >>> parameterstep = "hydpy.pub.options.parameterstep"
    >>> simulationstep = "hydpy.pub.options.simulationstep"
    >>> beta = ("HydPyServer.state.hp.elements.land_dill_assl.model.parameters."
    ...         "control.beta")
    >>> test("evaluate", data=(f"simulationstep = {simulationstep}\\n"
    ...                        f"parameterstep = {parameterstep}\\n"
    ...                        f"beta = {beta}"))
    simulationstep = Period("1d")
    parameterstep = Period("1d")
    beta = beta(1.0)

    >>> test("deregister_outputcontroldir", id_="0")
    <BLANKLINE>
    >>> test("query_outputcontroldir", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_outputcontroldir`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.

    To close the *HydPy* server, call |HydPyServer.GET_close_server|:

    >>> test("close_server")
    <BLANKLINE>
    >>> process.kill()
    >>> _ = process.communicate()
    """

    # pylint: disable=invalid-name
    # due to "GET" and "POST" method names in accordance with BaseHTTPRequestHandler

    server: _HTTPServerBase
    state: ClassVar[ServerState]
    extensions_map: ClassVar[dict[str, str]]
    _requesttype: Literal["GET", "POST"]
    _statuscode: Literal[200, 400, 500]
    _inputs: dict[str, str]
    _outputs: dict[str, object]

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
                    f"The POST method `{self._externalname}` received a wrongly "
                    f"formated data body.  The following line has been extracted but "
                    f"cannot be further processed: `{line}`."
                ) from exc

    @property
    def _id(self) -> ID:
        return self._get_queryparameter("id")

    def _get_queryparameter(self, name: str) -> ID:
        query = urllib.parse.urlparse(self.path).query
        try:
            return cast(ID, urllib.parse.parse_qs(query)[name][0])
        except KeyError:
            self._statuscode = 400
            raise RuntimeError(
                f"For the {self._requesttype} method `{self._externalname}` no query "
                f"parameter `{name}` is given."
            ) from None

    @property
    def _externalname(self) -> str:
        return urllib.parse.urlparse(self.path).path[1:]

    @property
    def _methodname(self) -> str:
        return f"{self._requesttype}_{self._externalname}"

    def _get_method(self, name: str) -> types.MethodType:
        try:
            method = getattr(self, name)
            assert isinstance(method, types.MethodType)
            return method
        except AttributeError:
            self._statuscode = 400
            raise RuntimeError(f"No method `{name}` available.") from None

    def _apply_method(self, method: types.MethodType) -> None:
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

        The method names must be passed as query parameters, as explained in the main
        documentation on module |servertools|.
        """
        self._execute()

    def POST_execute(self) -> None:
        """Execute an arbitrary number of POST and GET methods.

        The method names must be passed as query parameters, as explained in the main
        documentation on module |servertools|.
        """
        self._execute()

    def _execute(self) -> None:
        for name in self._get_queryparameter("methods").split(","):
            self._apply_method(self._get_method(name))

    def POST_evaluate(self) -> None:
        """Evaluate any valid Python expression with the *HydPy* server process and get
        its result.

        Method |HydPyServer.POST_evaluate| serves to test and debug, primarily.  The
        main documentation on class |HydPyServer| explains its usage.

        For safety purposes, method |HydPyServer.POST_evaluate| only works if you start
        the *HydPy* Server in debug mode by writing "debugging=enable", as we do in the
        examples of the main documentation on class |HydPyServer|.  When not working in
        debug mode, invoking this method results in the following error message:

        >>> from hydpy.core.testtools import prepare_full_example_1
        >>> prepare_full_example_1()
        >>> from hydpy import run_subprocess, TestIO
        >>> with TestIO():
        ...     process = run_subprocess(
        ...         "hyd.py start_server 8080 HydPy-H-Lahn multiple_runs_alpha.xml",
        ...         blocking=False, verbose=False)
        ...     _ = run_subprocess("hyd.py await_server 8080 10", verbose=False)
        >>> from urllib import request
        >>> request.urlopen("http://127.0.0.1:8080/evaluate", data=b"")
        Traceback (most recent call last):
        ...
        urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `POST_evaluate`, the following error occurred: You can only use the POST \
method `evaluate` if you have started the `HydPy Server` in debugging mode.

        >>> _ = request.urlopen("http://127.0.0.1:8080/close_server")
        >>> process.kill()
        >>> _ = process.communicate()
        """
        if not self.server.debugmode:
            raise RuntimeError(
                "You can only use the POST method `evaluate` if you have started the "
                "`HydPy Server` in debugging mode."
            )
        for name, value in self._inputs.items():
            result = eval(value)
            self._outputs[name] = objecttools.flatten_repr(result)

    def GET_status(self) -> None:
        """Return "status = ready" as soon as possible."""
        self._outputs["status"] = "ready"

    def GET_version(self) -> None:
        """Return Hydpy's version number."""
        self._outputs["version"] = hydpy.__version__

    def GET_close_server(self) -> None:
        """Stop and close the *HydPy* server."""

        def _close_server() -> None:
            self.server.shutdown()
            self.server.server_close()

        shutter = threading.Thread(target=_close_server)
        shutter.start()

    @staticmethod
    def _get_query_itemtype(item: itemtools.ExchangeItem) -> str:
        if item.targetspecs.series:
            return f"TimeSeries{item.ndim-1}D"
        return f"Double{item.ndim}D"

    def GET_query_itemtypes(self) -> None:
        """Get the types of all current exchange items."""
        self.GET_query_changeitemtypes()
        self.GET_query_outputitemtypes()
        self.GET_query_getitemtypes()

    def GET_query_changeitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change the values of
        |Parameter|, |StateSequence|, or |LogSequence| objects."""
        self.GET_query_parameteritemtypes()
        self.GET_query_inputitemtypes()
        self.GET_query_conditionitemtypes()

    def GET_query_parameteritemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change the values of
        |Parameter| objects."""
        for item in self.state.parameteritems:
            self._outputs[item.name] = self._get_query_itemtype(item)

    def GET_query_inputitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change the series of
        |InputSequence| objects."""
        for item in self.state.inputitems:
            self._outputs[item.name] = self._get_query_itemtype(item)

    def GET_query_conditionitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change the values of
        |StateSequence| or |LogSequence| objects."""
        for item in self.state.conditionitems:
            self._outputs[item.name] = self._get_query_itemtype(item)

    def GET_query_outputitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to return the values or
        series of |FactorSequence| or |FluxSequence| objects in the "setitem style"."""
        for item in self.state.outputitems:
            self._outputs[item.name] = self._get_query_itemtype(item)

    def GET_query_getitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to return the values of
        |Parameter| or |Sequence_| objects or the time series of |IOSequence|
        objects in the "getitem style"."""
        for item in self.state.getitems:
            type_ = self._get_query_itemtype(item)
            for name, _ in item.yield_name2value():
                self._outputs[name] = type_

    def GET_query_itemsubnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects."""
        self.GET_query_changeitemsubnames()
        self.GET_query_outputitemnames()
        self.GET_query_getitemsubnames()

    def GET_query_changeitemsubnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects supposed to change the values of |Parameter|, |StateSequence|,
        or |LogSequence| objects."""
        self.GET_query_parameteritemnames()
        self.GET_query_inputitemnames()
        self.GET_query_conditionitemnames()

    def GET_query_parameteritemnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects supposed to change the values of |Parameter| objects."""
        self._query_changeitemsubnames(self.state.parameteritems)

    def GET_query_inputitemnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects supposed to change the values of |InputSequence| objects."""
        self._query_changeitemsubnames(self.state.inputitems)

    def GET_query_conditionitemnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects supposed to change the values of |StateSequence| or
        |LogSequence| objects."""
        self._query_changeitemsubnames(self.state.conditionitems)

    def GET_query_outputitemnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects supposed to return the values of or series of |FactorSequence|
        or |FluxSequence| objects in the "setitem style"."""
        self._query_changeitemsubnames(self.state.outputitems)

    def GET_query_getitemsubnames(self) -> None:
        """Get names (suitable as IDs) describing the individual values of all current
        exchange objects supposed to return the values of |Parameter| or |Sequence_|
        objects or the time series of |IOSequence| objects in the "getitem style"."""
        for item in self.state.getitems:
            for name, subnames in item.yield_name2subnames():
                self._outputs[name] = subnames

    def _query_changeitemsubnames(self, items: Iterable[itemtools.ChangeItem]) -> None:
        for item in items:
            subnames = item.subnames
            if subnames is None:
                self._outputs[item.name] = "*global*"
            else:
                self._outputs[item.name] = f"[{', '.join(subnames)}]"

    def GET_query_initialitemvalues(self) -> None:
        """Get the initial values of all current exchange items."""
        self.GET_query_initialchangeitemvalues()
        self.GET_query_initialoutputitemvalues()
        self.GET_query_initialgetitemvalues()

    def GET_register_initialitemvalues(self) -> None:
        """Register the initial values of all current exchange items under the given
        `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialitemvalues|.
        """
        self.GET_register_initialchangeitemvalues()
        self.GET_register_initialoutputitemvalues()
        self.GET_register_initialgetitemvalues()

    def GET_query_initialchangeitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change the
        values of |Parameter|, |InputSequence|, |StateSequence|, or |LogSequence|
        objects."""
        self.GET_query_initialparameteritemvalues()
        self.GET_query_initialinputitemvalues()
        self.GET_query_initialconditionitemvalues()

    def GET_register_initialchangeitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to change
        the values of |Parameter|, |InputSequence|, |StateSequence|, or |LogSequence|
        objects under the given `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialchangeitemvalues|.
        """
        self.GET_register_initialparameteritemvalues()
        self.GET_register_initialinputitemvalues()
        self.GET_register_initialconditionitemvalues()

    @staticmethod
    def _array2output(
        values: Union[float, VectorInputObject, MatrixInputObject]
    ) -> str:
        # duck-typing for simplicity:
        try:
            try:
                return objecttools.assignrepr_list2(
                    values, prefix=""  # type: ignore[arg-type]
                ).replace("\n", "")
            except TypeError:
                return objecttools.repr_list(values)  # type: ignore[arg-type]
        except TypeError:
            return objecttools.repr_(values)

    def GET_query_initialparameteritemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change the
        values of |Parameter| objects."""
        for name, value in self.state.initialparameteritemvalues.items():
            self._outputs[name] = self._array2output(value)

    def GET_register_initialparameteritemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to change
        the values of |Parameter| objects under the given `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialparameteritemvalues|.
        """
        state = self.state
        state.parameteritemvalues[self._id] = state.initialparameteritemvalues.copy()

    def GET_query_initialinputitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change the
        series of |InputSequence| objects."""
        for name, value in self.state.initialinputitemvalues.items():
            self._outputs[name] = self._array2output(value)

    def GET_register_initialinputitemvalues(self) -> None:
        """Register the initial series of all current exchange items supposed to change
        the values of |InputSequence| objects under the given `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialinputitemvalues|.
        """
        self.state.inputitemvalues[self._id] = self.state.initialinputitemvalues.copy()

    def GET_query_initialconditionitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change the
        values of |StateSequence| or |LogSequence| objects."""
        for name, value in self.state.initialconditionitemvalues.items():
            self._outputs[name] = self._array2output(value)

    def GET_register_initialconditionitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to change
        the values of |StateSequence| or |LogSequence| objects under the given `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialconditionitemvalues|.
        """
        state = self.state
        state.conditionitemvalues[self._id] = state.initialconditionitemvalues.copy()

    def GET_query_initialoutputitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to return the
        values or sequences of |FactorSequence| or |FluxSequence| objects in the
        "setitem style"."""
        for name, value in self.state.initialoutputitemvalues.items():
            self._outputs[name] = self._array2output(value)

    def GET_register_initialoutputitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to return
        the values or sequences of |FactorSequence| or |FluxSequence| objects in the
        "setitem style" under the given `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialoutputitemvalues|.
        """
        state = self.state
        state.outputitemvalues[self._id] = state.initialoutputitemvalues.copy()

    def GET_query_initialgetitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to return the
        values of |Parameter| or |Sequence_| objects or the time series of |IOSequence|
        objects in the "getitems style"."""
        for name, value in self.state.initialgetitemvalues.items():
            self._outputs[name] = value

    def GET_register_initialgetitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to return
        the values of |Parameter| or |Sequence_| objects or the time series of
        |IOSequence| objects in the "getitem style" under the given `id`.

        Implemented as a workaround to support `OpenDA`_.  Better use method
        |HydPyServer.GET_query_initialgetitemvalues|.
        """
        self.state.getitemvalues[self._id] = self.state.initialgetitemvalues.copy()

    def GET_query_initialisationtimegrid(self) -> None:
        """Return the general |Timegrids.init| time grid."""
        tg = hydpy.pub.timegrids.init
        utc = hydpy.pub.options.utcoffset
        self._outputs["firstdate_init"] = tg.firstdate.to_string("iso1", utc)
        self._outputs["lastdate_init"] = tg.lastdate.to_string("iso1", utc)
        self._outputs["stepsize"] = tg.stepsize

    def _get_registered_content(self, dict_: dict[ID, T]) -> T:
        try:
            return dict_[self._id]
        except KeyError:
            message = f"Nothing registered under the id `{self._id}`."
            if dict_:
                message += f"  The available ids are: {objecttools.enumeration(dict_)}."
            else:
                message += "  There is nothing registered, so far."
            raise RuntimeError(message) from None

    def POST_register_simulationdates(self) -> None:
        """Register the send simulation dates under the given `id`."""
        self.state.timegrids[self._id] = timetools.Timegrid(
            firstdate=self._inputs["firstdate_sim"],
            lastdate=self._inputs["lastdate_sim"],
            stepsize=hydpy.pub.timegrids.stepsize,
        )

    def GET_activate_simulationdates(self) -> None:
        """Activate the simulation dates registered under the given `id`."""
        init = hydpy.pub.timegrids.init
        sim = hydpy.pub.timegrids.sim
        sim.dates = self._get_registered_content(self.state.timegrids).dates
        self.state.idx1 = init[sim.firstdate]
        self.state.idx2 = init[sim.lastdate]

    def GET_query_simulationdates(self) -> None:
        """Return the simulation dates registered under the given `id`."""
        tg = self._get_registered_content(self.state.timegrids)
        utc = hydpy.pub.options.utcoffset
        self._outputs["firstdate_sim"] = tg.firstdate.to_string("iso1", utc)
        self._outputs["lastdate_sim"] = tg.lastdate.to_string("iso1", utc)

    def GET_query_itemvalues(self) -> None:
        """Get the values of all |ExchangeItem| objects registered under the given
        `id`."""
        self.GET_query_changeitemvalues()
        self.GET_query_outputitemvalues()
        self.GET_query_getitemvalues()

    def POST_register_changeitemvalues(self) -> None:
        """Register the send values of all |ChangeItem| objects under the given `id`."""
        self.POST_register_parameteritemvalues()
        self.POST_register_inputitemvalues()
        self.POST_register_conditionitemvalues()

    def GET_activate_changeitemvalues(self) -> None:
        """Activate the values of the |ChangeItem| objects registered under the given
        `id`."""
        self.GET_activate_parameteritemvalues()
        self.GET_activate_inputitemvalues()
        self.GET_activate_conditionitemvalues()

    def GET_query_changeitemvalues(self) -> None:
        """Get the values of all |ChangeItem| objects registered under the given
        `id`."""
        self.GET_query_parameteritemvalues()
        self.GET_query_inputitemvalues()
        self.GET_query_conditionitemvalues()

    def _post_register_itemvalues(
        self,
        typename: str,
        items: Iterable[itemtools.ChangeItem],
        itemvalues: dict[ID, dict[Name, Any]],
    ) -> None:
        item2value: dict[Name, Any] = {}
        for item in items:
            try:
                value = self._inputs[item.name]
            except KeyError:
                self._statuscode = 500
                raise RuntimeError(
                    f"A value for {typename} item `{item.name}` is missing."
                ) from None
            item2value[item.name] = eval(value)
        itemvalues[self._id] = item2value

    def POST_register_parameteritemvalues(self) -> None:
        """Register the send parameter values under the given `id`."""
        self._post_register_itemvalues(
            typename="parameter",
            items=self.state.parameteritems,
            itemvalues=self.state.parameteritemvalues,
        )

    def GET_activate_parameteritemvalues(self) -> None:
        """Activate the parameter values registered under the given `id`."""
        item2value = self._get_registered_content(self.state.parameteritemvalues)
        for item in self.state.parameteritems:
            item.value = item2value[item.name]
            item.update_variables()

    def GET_query_parameteritemvalues(self) -> None:
        """Return the parameter values registered under the given `id`."""
        item2value = self._get_registered_content(self.state.parameteritemvalues)
        for item, value in item2value.items():
            self._outputs[item] = self._array2output(value)

    def POST_register_inputitemvalues(self) -> None:
        """Register the send input item values under the given `id`."""
        self._post_register_itemvalues(
            typename="input",
            items=self.state.inputitems,
            itemvalues=self.state.inputitemvalues,
        )

    def GET_activate_inputitemvalues(self) -> None:
        """Apply the input item values registered under the given `id` to modify the
        current |InputSequence| values."""
        item2value = self._get_registered_content(self.state.inputitemvalues)
        for item in self.state.inputitems:
            item.value = item2value[item.name]
            item.update_variables()

    def GET_update_inputitemvalues(self) -> None:
        """Convert the current |InputSequence| values to input item values (when
        necessary) and register them under the given `id`."""
        item2value = {}
        for item in self.state.inputitems:
            item.extract_values()
            item2value[item.name] = item.value
        self.state.inputitemvalues[self._id] = item2value

    def GET_query_inputitemvalues(self) -> None:
        """Return the input item values registered under the given `id`."""
        item2value = self._get_registered_content(self.state.inputitemvalues)
        for item, value in item2value.items():
            self._outputs[item] = self._array2output(value)

    def POST_register_conditionitemvalues(self) -> None:
        """Register the send condition item values under the given `id`."""
        self._post_register_itemvalues(
            typename="condition",
            items=self.state.conditionitems,
            itemvalues=self.state.conditionitemvalues,
        )

    def GET_activate_conditionitemvalues(self) -> None:
        """Apply the condition item values registered under the given `id` to modify
        the current |StateSequence| and |LogSequence| values."""
        item2value = self._get_registered_content(self.state.conditionitemvalues)
        for item in self.state.conditionitems:
            item.value = item2value[item.name]
            item.update_variables()

    def GET_update_conditionitemvalues(self) -> None:
        """Convert the current |StateSequence| and |LogSequence| values to condition
        item values (when necessary) and register them under the given `id`."""
        item2value = {}
        for item in self.state.conditionitems:
            item.extract_values()
            item2value[item.name] = item.value
        self.state.conditionitemvalues[self._id] = item2value

    def GET_query_conditionitemvalues(self) -> None:
        """Return the condition item values registered under the given `id`."""
        item2value = self._get_registered_content(self.state.conditionitemvalues)
        for item, value in item2value.items():
            self._outputs[item] = self._array2output(value)

    def GET_update_outputitemvalues(self) -> None:
        """Convert the current |FactorSequence| and |FluxSequence| values or series to
        output item values (when necessary) and register them under the given `id`."""
        item2value = {}
        for item in self.state.outputitems:
            item.extract_values()
            item2value[item.name] = item.value
        self.state.outputitemvalues[self._id] = item2value

    def GET_query_outputitemvalues(self) -> None:
        """Return the output item values registered under the given `id`."""
        item2value = self._get_registered_content(self.state.outputitemvalues)
        for item, value in item2value.items():
            self._outputs[item] = self._array2output(value)

    def GET_save_internalconditions(self) -> None:
        """Register the |StateSequence| and |LogSequence| values of the |HydPy|
        instance for the current simulation endpoint under the given `id`."""
        self.state.conditions[self._id] = self.state.conditions.get(self._id, {})
        self.state.conditions[self._id][self.state.idx2] = self.state.hp.conditions

    def GET_load_internalconditions(self) -> None:
        """Activate the |StateSequence| or |LogSequence| values registered for the
        current simulation start point under the given `id`.

        When the simulation start point is identical with the initialisation time
        point, and you do not register alternative conditions manually, method
        |HydPyServer.GET_load_internalconditions| uses the "original" initial
        conditions of the current process (usually those of the conditions files of the
        respective *HydPy*  project).
        """
        try:
            self.state.hp.conditions = self.state.conditions[self._id][self.state.idx1]
        except KeyError:
            if self.state.idx1:
                self._statuscode = 500
                raise RuntimeError(
                    f"Conditions for ID `{self._id}` and time point "
                    f"`{hydpy.pub.timegrids.sim.firstdate}` are required, but have "
                    f"not been calculated so far."
                ) from None
            self.state.hp.conditions = self.state.init_conditions

    def POST_register_internalconditions(self) -> None:
        """Register the send internal conditions under the given `id`."""
        conditions = eval(self._inputs["conditions"], {"array": numpy.array})
        self.state.conditions[self._id][self.state.idx1] = conditions

    def GET_deregister_internalconditions(self) -> None:
        """Remove all internal condition directories registered under the given `id`."""
        self.state.conditions[self._id] = {}

    def GET_query_internalconditions(self) -> None:
        """Get the internal conditions registered under the given `id`."""
        all_conditions = self._get_registered_content(self.state.conditions)
        try:
            relevant_conditons = all_conditions[self.state.idx2]
        except KeyError:
            raise RuntimeError(
                f"No internal conditions registered under the id `{self._id}` for "
                f"`{self.state.timegrids[self._id].lastdate}`."
            ) from None
        self._outputs["conditions"] = str(relevant_conditons).replace("\n", " ")

    def POST_register_inputconditiondir(self) -> None:
        """Register the send input condition directory under the given `id`."""
        self.state.inputconditiondirs[self._id] = self._inputs["inputconditiondir"]

    def GET_deregister_inputconditiondir(self) -> None:
        """Remove the input condition directory registered under the `id`."""
        self.state.inputconditiondirs.pop(self._id, None)

    def GET_query_inputconditiondir(self) -> None:
        """Return the input condition directory registered under the `id`."""
        dir_ = self._get_registered_content(self.state.inputconditiondirs)
        self._outputs["inputconditiondir"] = dir_

    def POST_register_outputconditiondir(self) -> None:
        """Register the send output condition directory under the given `id`."""
        self.state.outputconditiondirs[self._id] = self._inputs["outputconditiondir"]

    def GET_deregister_outputconditiondir(self) -> None:
        """Remove the output condition directory registered under the `id`."""
        self.state.outputconditiondirs.pop(self._id, None)

    def GET_query_outputconditiondir(self) -> None:
        """Return the output condition directory registered under the `id`."""
        dir_ = self._get_registered_content(self.state.outputconditiondirs)
        self._outputs["outputconditiondir"] = dir_

    def GET_load_conditions(self) -> None:
        """Load the (initial) conditions."""
        dir_ = self.state.inputconditiondirs.get(self._id)
        self.state.interface.conditions_io.load_conditions(dir_)

    def GET_save_conditions(self) -> None:
        """Save the (resulting) conditions."""
        dir_ = self.state.outputconditiondirs.get(self._id)
        self.state.interface.conditions_io.save_conditions(dir_)

    def GET_update_getitemvalues(self) -> None:
        """Register the current |GetItem| values under the given `id`.

        For |GetItem| objects observing time series, method
        |HydPyServer.GET_update_getitemvalues| registers only the values within the
        current simulation period.
        """
        item2value = {}
        for item in self.state.getitems:
            for name, value in item.yield_name2value(self.state.idx1, self.state.idx2):
                item2value[name] = value
        self.state.getitemvalues[self._id] = item2value

    def GET_query_getitemvalues(self) -> None:
        """Get the |GetItem| values registered under the given `id`."""
        item2value = self._get_registered_content(self.state.getitemvalues)
        for name, value in item2value.items():
            self._outputs[name] = value

    def GET_simulate(self) -> None:
        """Perform a simulation run."""
        readerdir = self.state.seriesreaderdirs.get(self._id, None)
        writerdir = self.state.serieswriterdirs.get(self._id, None)
        sio = self.state.interface.series_io
        with sio.modify_inputdir(readerdir), sio.modify_outputdir(writerdir):
            self.state.hp.simulate()

    def POST_register_seriesreaderdir(self) -> None:
        """Register the send series reader directory under the given `id`."""
        self.state.seriesreaderdirs[self._id] = self._inputs["seriesreaderdir"]

    def GET_deregister_seriesreaderdir(self) -> None:
        """Remove the series reader directory registered under the `id`."""
        self.state.seriesreaderdirs.pop(self._id, None)

    def GET_query_seriesreaderdir(self) -> None:
        """Return the series reader directory registered under the `id`."""
        dir_ = self._get_registered_content(self.state.seriesreaderdirs)
        self._outputs["seriesreaderdir"] = dir_

    def POST_register_serieswriterdir(self) -> None:
        """Register the send series writer directory under the given `id`."""
        self.state.serieswriterdirs[self._id] = self._inputs["serieswriterdir"]

    def GET_deregister_serieswriterdir(self) -> None:
        """Remove the series writer directory registered under the `id`."""
        self.state.serieswriterdirs.pop(self._id, None)

    def GET_query_serieswriterdir(self) -> None:
        """Return the series writer directory registered under the `id`."""
        dir_ = self._get_registered_content(self.state.serieswriterdirs)
        self._outputs["serieswriterdir"] = dir_

    def GET_load_allseries(self) -> None:
        """Load the time series of all sequences selected for (non-jit) reading."""
        state = self.state
        state.interface.series_io.load_series(state.seriesreaderdirs.get(self._id))

    def GET_save_allseries(self) -> None:
        """Save the time series of all sequences selected for (non-jit) writing."""
        state = self.state
        state.interface.series_io.save_series(state.serieswriterdirs.get(self._id))

    def POST_register_outputcontroldir(self) -> None:
        """Register the send output control directory under the given `id`."""
        self.state.outputcontroldirs[self._id] = self._inputs["outputcontroldir"]

    def GET_deregister_outputcontroldir(self) -> None:
        """Remove the output control directory registered under the `id`."""
        self.state.outputcontroldirs.pop(self._id, None)

    def GET_query_outputcontroldir(self) -> None:
        """Return the output control directory registered under the `id`."""
        dir_ = self._get_registered_content(self.state.outputcontroldirs)
        self._outputs["outputcontroldir"] = dir_

    def GET_save_controls(self) -> None:
        """Save the control files of all model instances."""
        state = self.state
        controldir = self._get_registered_content(state.outputcontroldirs)
        hydpy.pub.controlmanager.currentdir = controldir
        state.hp.save_controls()


class _HTTPServerBase(http.server.HTTPServer):
    debugmode: bool = False


def start_server(
    socket: Union[int, str],
    projectname: str,
    xmlfilename: str,
    load_conditions: Union[bool, str] = True,
    load_series: Union[bool, str] = True,
    maxrequests: Union[int, str] = 5,
    debugging: Literal["enable", "disable"] = "disable",
) -> None:
    """Start the *HydPy* server using the given socket.

    The folder with the given `projectname` must be available within the current
    working directory.  The XML configuration file must be placed within the project
    folder unless `xmlfilename` is an absolute file path. The XML configuration file
    must be valid concerning the schema file `HydPyConfigMultipleRuns.xsd` (see class
    |ServerState| for further information).

    The |HydPyServer| allows for five still unhandled requests before refusing new
    connections by default.  Use the optional `maxrequests` argument to increase this
    number (which might be necessary when parallelising optimisation or data
    assimilation):

    >>> from hydpy.core.testtools import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> command = (
    ...     "hyd.py start_server 8080 HydPy-H-Lahn multiple_runs_alpha.xml "
    ...     "debugging=enable maxrequests=100")
    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():
    ...     process = run_subprocess(command, blocking=False, verbose=False)
    ...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

    >>> from urllib import request
    >>> command = "maxrequests = self.server.request_queue_size"
    >>> response = request.urlopen("http://127.0.0.1:8080/evaluate",
    ...                            data=bytes(command, encoding="utf-8"))
    >>> print(str(response.read(), encoding="utf-8"))
    maxrequests = 100

    >>> _ = request.urlopen("http://127.0.0.1:8080/close_server")
    >>> process.kill()
    >>> _ = process.communicate()

    Please see the documentation on method |HydPyServer.POST_evaluate| that explains
    the "debugging" argument.

    Note that function |start_server| tries to read the "mime types" from a dictionary
    stored in the file `mimetypes.txt` available in subpackage `conf` and passes it as
    attribute `extension_map` to class |HydPyServer|.  The reason is to avoid the long
    computation time of function |mimetypes.init| of module |mimetypes|, usually called
    when defining class `BaseHTTPRequestHandler` of module `http.server`.  If file
    `mimetypes.txt` does not exist or does not work for , |start_server| calls
    |mimetypes.init| as usual, (over)writes `mimetypes.txt` and tries to proceed as
    expected.
    """
    confpath: str = conf.__path__[0]
    filepath = os.path.join(confpath, "mimetypes.txt")
    try:
        with open(filepath, encoding=config.ENCODING) as file_:
            types_map: dict[str, str] = eval(str(file_.read()))
    except BaseException:
        mimetypes.init()
        types_map = mimetypes.types_map.copy()
        types_map.update(
            {
                "": "application/octet-stream",
                ".py": "text/plain",
                ".c": "text/plain",
                ".h": "text/plain",
            }
        )
        with open(filepath, "w", encoding=config.ENCODING) as file_:
            file_.write(str(types_map))
    HydPyServer.extensions_map = types_map
    HydPyServer.state = ServerState(
        projectname=projectname,
        xmlfile=xmlfilename,
        load_conditions=objecttools.value2bool("load_conditions", load_conditions),
        load_series=objecttools.value2bool("load_series", load_series),
    )

    class _HTTPServer(_HTTPServerBase):
        debugmode = debugging == "enable"
        request_queue_size = int(maxrequests)

    server = _HTTPServer(("", int(socket)), HydPyServer)
    server.serve_forever()


def await_server(port: Union[int, str], seconds: Union[float, str]) -> None:
    """Block the current process until either the *HydPy* server is responding on the
    given `port` or the given number of `seconds` elapsed.

    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():  # doctest: +ELLIPSIS
    ...     result = run_subprocess("hyd.py await_server 8080 0.1")
    Invoking hyd.py with arguments `await_server, 8080, 0.1` resulted in the \
following error:
    <urlopen error Waited for 0.1 seconds without response on port 8080.>
    ...

    >>> from hydpy.core.testtools import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> with TestIO():
    ...     process = run_subprocess(
    ...         "hyd.py start_server 8080 HydPy-H-Lahn multiple_runs.xml",
    ...         blocking=False, verbose=False)
    ...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

    >>> from urllib import request
    >>> _ = request.urlopen("http://127.0.0.1:8080/close_server")
    >>> process.kill()
    >>> _ = process.communicate()
    """
    now = time.perf_counter()
    end = now + float(seconds)
    while now <= end:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/status"):
                break
        except urllib.error.URLError:
            time.sleep(0.1)
            now = time.perf_counter()
    else:
        raise urllib.error.URLError(
            f"Waited for {seconds} seconds without response on port {port}."
        )
