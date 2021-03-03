# -*- coding: utf-8 -*-
"""This module implements features for using *HydPy* as an HTTP server
application.

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
to perform the steps described above.

The *HydPy* server's API is relatively simple, allowing to perform a "normal"
calibration using a few server methods only.  However, it is also more restrictive
than controlling *HydPy* within a Python process.  Within a Python process, you are
free to do anything. Using the *HydPy* server, you are much more restricted to what
was anticipated by the framework developers.

Commonly but not mandatory, one configures the initial state of a *HydPy* server
with an XML file.  As an example, we prepare the `LahnH` project by calling
function |prepare_full_example_1|, which contains the XML configuration file
`multiple_runs_alpha.xml`:

>>> from hydpy.examples import prepare_full_example_1
>>> prepare_full_example_1()

To start the server in a new process, open a command-line tool and insert the
following command (see module |hyd| for general information on how to use *HydPy*
via the command line):

>>> command = "hyd.py start_server 8080 LahnH multiple_runs_alpha.xml"
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
>>> url = "http://localhost:8080/query_itemtypes"
>>> print(str(request.urlopen(url).read(), encoding="utf-8"))
alpha = Double0D
dill_nodes_sim_series = TimeSeries0D

>>> url = "http://localhost:8080/query_initialitemvalues"
>>> print(str(request.urlopen(url).read(), encoding="utf-8"))
alpha = 2.0
dill_nodes_sim_series = [nan, nan, nan, nan, nan]

In general, it is possible to control the *HydPy* server via invoking each method
with a separate HTTP request.  However, one can use methods |HydPyServer.GET_execute|
and |HydPyServer.POST_execute| alternatively to execute a larger number of methods
with only one HTTP request.  We now define three such metafunctions.  The first one
changes the value of the parameter |hland_control.Alpha|  The second one runs a
simulation.  The third one prints the newly calculated discharge at the outlet of
the headwater catchment `Dill`.  All of this is very similar to what the
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
...     url = f"http://localhost:8080/execute?id={id_}&methods={methods}"
...     request.urlopen(url, data=content)

Function `simulate` wraps only GET methods and triggers the next simulation run.
As for all GET and POST methods, one should pass the query parameter `id`, used by
the *HydPy* server for internal bookmarking:

>>> def simulate(id_):
...     methods = ",".join(("GET_activate_simulationdates",
...                         "GET_activate_parameteritemvalues",
...                         "GET_load_internalconditions",
...                         "GET_activate_conditionitemvalues",
...                         "GET_simulate",
...                         "GET_save_internalconditions",
...                         "GET_update_conditionitemvalues",
...                         "GET_update_getitemvalues"))
...     url = f"http://localhost:8080/execute?id={id_}&methods={methods}"
...     request.urlopen(url)

Function `print_itemvalues` also wraps only GET methods and prints the current
value of parameter |hland_control.Alpha| as well as the lastly simulated
discharge values corresponding to the given `id` value:

>>> from hydpy import print_values
>>> def print_itemvalues(id_):
...     methods = ",".join(("GET_query_simulationdates",
...                         "GET_query_parameteritemvalues",
...                         "GET_query_conditionitemvalues",
...                         "GET_query_getitemvalues"))
...     url = f"http://localhost:8080/execute?id={id_}&methods={methods}"
...     data = str(request.urlopen(url).read(), encoding="utf-8")
...     for line in data.split("\\n"):
...         if line.startswith("alpha"):
...             alpha = line.split("=")[1].strip()
...         if line.startswith("dill"):
...             discharge = eval(line.split("=")[1])
...     print(f"{alpha}: ", end="")
...     print_values(discharge)

For the sake of brevity, we also define `do_everything` for calling the other
functions at once:

>>> def do_everything(id_, firstdate, lastdate, alpha):
...     set_itemvalues(id_, firstdate, lastdate, alpha)
...     simulate(id_)
...     print_itemvalues(id_)

In the simplest example, we perform a simulation throughout five days for an
|hland_control.Alpha| value of 2:

>>> do_everything("1a", "1996-01-01", "1996-01-06", 2.0)
2.0: 35.537828, 7.741064, 5.018981, 4.501784, 4.238874

The next example shows interlocked simulation runs.  The first call only triggers
a simulation run for the first initialised day:

>>> do_everything("1b", "1996-01-01", "1996-01-02", 2.0)
2.0: 35.537828

The second call repeats the first one with a different `id` value:

>>> do_everything("2", "1996-01-01", "1996-01-02", 2.0)
2.0: 35.537828

The third call covers the first three initialisation days:

>>> do_everything("3", "1996-01-01", "1996-01-04", 2.0)
2.0: 35.537828, 7.741064, 5.018981

The fourth call continues the simulation of the first call, covering the last four
initialised days:

>>> do_everything("1b", "1996-01-02", "1996-01-06", 2.0)
2.0: 7.741064, 5.018981, 4.501784, 4.238874

The results of the very first call of function `do_everything` (with`id=1`) are
identical with the pulled-together discharge values of the calls with `id=1b`,
made possible by the internal bookmarking feature of the *HydPy* server.  Here we
use numbers, but any other strings are valid `id` values.

This example extends the last one by applying different parameter values:

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
natural, but some tools might require do deviate from it.  For example, `OpenDA`_
offers ensemble-based algorithms triggering the simulation of all memberse before
starting to query any simulation results.  The final example shows that the
underlying atomic methods do support such an execution sequence:

>>> set_itemvalues("6", "1996-01-01", "1996-01-03", 2.0)
>>> simulate("6")
>>> set_itemvalues("7", "1996-01-01", "1996-01-03", 1.0)
>>> simulate("7")
>>> print_itemvalues("6")
2.0: 35.537828, 7.741064
>>> print_itemvalues("7")
1.0: 11.78038, 8.901179

When working in parallel mode, `OpenDA`_ might not always call the functions
`set_itemvalues` and `simulate` for the same `id` directly one after another,
which also causes no problem:

>>> set_itemvalues("6", "1996-01-03", "1996-01-06", 2.0)
>>> set_itemvalues("7", "1996-01-03", "1996-01-06", 1.0)
>>> simulate("6")
>>> simulate("7")
>>> print_itemvalues("6")
2.0: 5.018981, 4.501784, 4.238874
>>> print_itemvalues("7")
1.0: 7.131072, 6.017787, 5.313211

Finally, we close the server and kill its process (just closing your command-line
tool works as well):

>>> _ = request.urlopen("http://localhost:8080/close_server")
>>> process.kill()
>>> _ = process.communicate()

The above description focussed on coupling *HydPy* to `OpenDA`_.  However, the applied
atomic submethods of class |HydPyServer| also allow to couple *HydPy*  with other
software products. See the documentation on class |HydPyServer| for further information.
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
from typing_extensions import Literal  # type: ignore[misc]

# ...from HydPy
import hydpy
from hydpy import conf
from hydpy.auxs import xmltools
from hydpy.core import hydpytools
from hydpy.core import itemtools
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.exe import commandtools
from hydpy.core.typingtools import *


# pylint: disable=wrong-import-position, wrong-import-order
# see the documentation on method `start_server` for explanations
mimetypes.inited = True
import http.server

mimetypes.inited = False
# pylint: enable=wrong-import-position, wrong-import-order


ID = NewType("ID", str)


class ServerState:
    """Singleton class handling states like the current |HydPy| instance exchange items.

    The instance of class |ServerState| is available as the member `state` of class
    |HydPyServer| after calling the function |start_server|.  You could create other
    instances (like we do in the following examples), but most likely, you shouldn't.
    The primary purpose of this instance is to store information between successive
    initialisations of class |HydPyServer|.

    We use the `LahnH` project and its (complicated) XML configuration file
    `multiple_runs.xml` as an example (module |xmltools| provides information on
    interpreting this file):

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import print_values, TestIO
    >>> from hydpy.exe.servertools import ServerState
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     state = ServerState("LahnH", "multiple_runs.xml")
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

    The initialisation also memorises the initial conditions of all elements:

    >>> for element in state.init_conditions:
    ...     print(element)
    land_dill
    land_lahn_1
    land_lahn_2
    land_lahn_3
    stream_dill_lahn_2
    stream_lahn_1_lahn_2
    stream_lahn_2_lahn_3

    The initialisation also prepares all selected series arrays and reads the
    required input data:

    >>> print_values(
    ...     state.hp.elements.land_dill.model.sequences.inputs.t.series)
    -0.298846, -0.811539, -2.493848, -5.968849, -6.999618
    >>> state.hp.nodes.dill.sequences.sim.series
    InfoArray([ nan,  nan,  nan,  nan,  nan])
    """

    hp: hydpytools.HydPy
    parameteritems: List[itemtools.ChangeItem]
    conditionitems: List[itemtools.ChangeItem]
    getitems: List[itemtools.GetItem]
    conditions: Dict[ID, Dict[int, hydpytools.ConditionsType]]
    parameteritemvalues: Dict[ID, Dict[Name, Any]]
    conditionitemvalues: Dict[ID, Dict[Name, Any]]
    getitemvalues: Dict[ID, Dict[Name, str]]
    initialparameteritemvalues: Dict[Name, Any]
    initialconditionitemvalues: Dict[Name, Any]
    initialgetitemvalues: Dict[Name, Any]
    timegrids: Dict[ID, timetools.Timegrid]
    init_conditions: hydpytools.ConditionsType
    idx1: int
    idx2: int

    def __init__(self, projectname: str, xmlfile: str) -> None:
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
        self.initialparameteritemvalues = {
            item.name: item.value for item in self.parameteritems
        }
        self.initialconditionitemvalues = {
            item.name: item.value for item in self.conditionitems
        }
        self.initialgetitemvalues = {
            name: value
            for item in self.getitems
            for name, value in item.yield_name2value(*hydpy.pub.timegrids.simindices)
        }
        self.conditions = {}
        self.parameteritemvalues = {}
        self.conditionitemvalues = {}
        self.getitemvalues = {}
        self.init_conditions = hp.conditions
        self.timegrids = {}


class HydPyServer(http.server.BaseHTTPRequestHandler):
    """The API of the *HydPy* server.

    Technically and strictly speaking, |HydPyServer| is, only the HTTP request handler
    for the real HTTP server class (from the standard library).

    After initialising the *HydPy* server, each communication via a GET or POST
    request is handled by a new instance of |HydPyServer|.  This handling takes
    place in a unified way through using either method |HydPyServer.do_GET| or
    [HydPyServer.do_POST|, which select and apply the actual GET or POST method.
    All methods provided by class |HydPyServer| starting with "GET" or "POST"
    are accessible via HTTP.

    As in the main documentation on module |servertools|, we use the
    `multiple_runs_alpha.xml` file of the `LahnH` project as an example.  However,
    this time we select the more complex XML configuration file `multiple_runs.xml`,
    covering a higher number of cases:

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():
    ...     process = run_subprocess(
    ...         "hyd.py start_server 8080 LahnH multiple_runs.xml",
    ...         blocking=False, verbose=False)
    ...     result = run_subprocess(
    ...         "hyd.py await_server 8080 10", verbose=False)

    We define a test function simplifying sending the following requests, offering
    two optional arguments.  When passing a value to `id_`, `test` adds this value
    as the query parameter `id` to the URL.  When passing a string to `data`, `test`
    sends a POST request containing the given data, otherwise a GET request without
    additional data:

    >>> from urllib import request
    >>> def test(name, id_=None, data=None, return_result=False):
    ...     url = f"http://localhost:8080/{name}"
    ...     if id_:
    ...         url = f"{url}?id={id_}"
    ...     if data:
    ...         data = bytes(data, encoding="utf-8")
    ...     response = request.urlopen(url, data=data)
    ...     result = str(response.read(), encoding="utf-8")
    ...     print(result)
    ...     return result if return_result else None

    Asking for its status tells us that the server is ready (which may take a while,
    depending on the particular project's size):

    >>> test("status")
    status = ready

    You can query the current version number of the *HydPy* installation used to
    start the server:

    >>> result = test("version", return_result=True)   # doctest: +ELLIPSIS
    version = ...
    >>> hydpy.__version__ in result
    True

    |HydPyServer| returns the error code `400` if it realises the URL to be wrong:

    >>> test("missing")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 400: RuntimeError: \
No method `GET_missing` available.

    The error code is `500` in all other cases of error:

    >>> test("register_parameteritemvalues", id_="0",
    ...      data="alpha = []")    # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `POST_register_parameteritemvalues`, the following error occurred: \
A value for parameter item `beta` is missing.

    Some methods require identity information, passed as query parameter `id`, used
    for internal bookmarking:

    >>> test("query_parameteritemvalues")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `GET_query_parameteritemvalues`, the following error occurred: \
For the GET method `query_parameteritemvalues` no query parameter `id` is given.

    POST methods always expect an arbitrary number of lines, each one assigning
    some values to some variable (in most cases, numbers to exchange items):

    >>> test("parameteritemvalues",
    ...      id_="a",
    ...      data=("x = y\\n"
    ...            "   \\n"
    ...            "x == y\\n"
    ...            "x = y"))
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 400: RuntimeError: The POST method \
`parameteritemvalues` received a wrongly formated data body.  The following line \
has been extracted but cannot be further processed: `x == y`.

    Before explaining the more offical methods, we introduce the method
    |HydPyServer.POST_evaluate|, which evaluates arbitrary valid Python code within
    the server process.  Its most likelely use-case is to access the (sub)attributes
    of the single instance of class |ServerState|, available as a member of class
    |HydPyServer|.  This method can be of help when being puzzled about the state
    of the *HydPy* server.  Use it, for example, to find out which |Node| objects
    are available and to see which one is the outlet node of the |Element| object
    `land_dill`:

    >>> test("evaluate",
    ...      data=("nodes = HydPyServer.state.hp.nodes\\n"
    ...            "elements = HydPyServer.state.hp.elements.land_dill"))
    nodes = Nodes("dill", "lahn_1", "lahn_2", "lahn_3")
    elements = Element("land_dill", outlets="dill", keywords="catchment")

    Method |HydPyServer.GET_query_itemtypes|, already described in the main
    documentation of module |servertools|, returns all available exchange item types
    at once.  However, it is also possible to query those that are related to setting
    parameter values (|HydPyServer.GET_query_parameteritemtypes|), setting condition
    values (|HydPyServer.GET_query_conditionitemtypes|), and getting different kinds
    of values (|HydPyServer.GET_query_getitemtypes|) separately:

    >>> test("query_parameteritemtypes")
    alpha = Double0D
    beta = Double0D
    lag = Double0D
    damp = Double0D
    sfcf_1 = Double0D
    sfcf_2 = Double0D
    sfcf_3 = Double1D
    >>> test("query_conditionitemtypes")
    sm_lahn_2 = Double0D
    sm_lahn_1 = Double1D
    quh = Double0D
    >>> test("query_getitemtypes")
    land_dill_fluxes_qt = Double0D
    land_dill_fluxes_qt_series = TimeSeries0D
    land_dill_states_sm = Double1D
    land_lahn_1_states_sm = Double1D
    land_lahn_2_states_sm = Double1D
    land_lahn_3_states_sm = Double1D
    land_lahn_3_states_sm_series = TimeSeries1D
    dill_nodes_sim_series = TimeSeries0D

    The same holds for the initial values of the exchange-items.  Method
    |HydPyServer.GET_query_initialitemvalues| returns them all at once while the
    methods |HydPyServer.GET_query_initialparameteritemvalues|,
    |HydPyServer.GET_query_initialconditionitemvalues|), and
    (|HydPyServer.GET_query_initialgetitemvalues|) return the relevant subgroup only:

    >>> test("query_initialparameteritemvalues")
    alpha = 2.0
    beta = 1.0
    lag = 5.0
    damp = 0.5
    sfcf_1 = 0.3
    sfcf_2 = 0.2
    sfcf_3 = [ 0.1  0.2  0.1  0.2  0.1  0.2  0.1  0.2  0.1  0.2  0.1  0.2  0.2  0.2]
    >>> test("query_initialconditionitemvalues")
    sm_lahn_2 = 123.0
    sm_lahn_1 = [ 110.  120.  130.  140.  150.  160.  170.  180.  190.  200.  210.  220.
      230.]
    quh = 10.0
    >>> test("query_initialgetitemvalues")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = nan
    land_dill_fluxes_qt_series = [nan, nan, nan, nan, nan]
    land_dill_states_sm = [185.13164...]
    land_lahn_1_states_sm = [99.27505...]
    land_lahn_2_states_sm = [138.31396...]
    land_lahn_3_states_sm = [101.31248...]
    land_lahn_3_states_sm_series = [[nan, ...], [nan, ...], ..., [nan, ...]]
    dill_nodes_sim_series = [nan, nan, nan, nan, nan]

    The |Timegrids.init| time grid is immutable once the server is ready.  Method
    |HydPyServer.GET_query_initialisationtimegrid| returns the fixed first date,
    last date, and stepsize of the whole initialised period:

    >>> test("query_initialisationtimegrid")
    firstdate_init = 1996-01-01T00:00:00+01:00
    lastdate_init = 1996-01-06T00:00:00+01:00
    stepsize = 1d

    The dates of the |Timegrids.sim| time grid, on the other hand, are mutable and
    can vary for different `id` query parameters.  This flexibility makes things a
    little more complicated, as the |Timegrids| object of the global |pub| module
    handles only one |Timegrids.sim| object at once.  Hence, we differentiate between
    registered simulation dates of the respective `id` values and the currently
    active simulation dates of the |Timegrids| object.

    Method |HydPyServer.GET_query_simulationdates| asks for registered simulation
    dates and thus fails at first:

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

    Our initial call to the POST method |HydPyServer.POST_register_simulationdates|
    did not affect the currently active simulation dates.  We need to do this manually
    by calling method |HydPyServer.GET_activate_simulationdates|:

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
method `GET_activate_simulationdates`, the following error occurred: \
Nothing registered under the id `1`.  The available ids are: 0.

    The logic of the parameter-related GET and POST methods is very similar to the
    logic of the simulation date-related methods discussed above.  Method
    |HydPyServer.POST_register_parameteritemvalues| registers new values of the
    exchange-items, and method |HydPyServer.GET_activate_parameteritemvalues|
    activates them (applies them on the relevant parameters):

    >>> test("register_parameteritemvalues", id_="0",
    ...      data=("alpha = 3.0\\n"
    ...            "beta = 2.0\\n"
    ...            "lag = 1.0\\n"
    ...            "damp = 0.5\\n"
    ...            "sfcf_1 = 0.3\\n"
    ...            "sfcf_2 = 0.2\\n"
    ...            "sfcf_3 = 0.1\\n"))
    <BLANKLINE>
    >>> control = "HydPyServer.state.hp.elements.land_dill.model.parameters.control"
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

    The list of exchange-items must be complete:

    >>> test("register_parameteritemvalues", id_="0",
    ...      data=("alpha = 3.0\\n"
    ...            "beta = 2.0"))
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to \
execute method `POST_register_parameteritemvalues`, the following error occurred: \
A value for parameter item `lag` is missing.

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

    The condition-related methods |HydPyServer.POST_register_conditionitemvalues|,
    |HydPyServer.GET_activate_conditionitemvalues|, and
    |HydPyServer.GET_query_conditionitemvalues| work like the parameter-related
    methods described above:

    >>> test("register_conditionitemvalues", id_="0",
    ...      data=("sm_lahn_2 = 246.0\\n"
    ...            "sm_lahn_1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)\\n"
    ...            "quh = 1.0\\n"))
    <BLANKLINE>
    >>> test("query_conditionitemvalues", id_="0")
    sm_lahn_2 = 246.0
    sm_lahn_1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)
    quh = 1.0

    Note the trimming of the too-high value for the state sequence |hland_states.SM|
    to its highest possible value defined by control parameter |hland_control.FC|):

    >>> sequences = "HydPyServer.state.hp.elements.land_lahn_2.model.sequences"
    >>> test("evaluate",
    ...      data=(f"sm = {sequences}.states.sm \\n"
    ...            f"quh = {sequences}.logs.quh"))    # doctest: +ELLIPSIS
    sm = sm(138.31396, ..., 164.63255)
    quh = quh(0.7, 0.0)
    >>> test("activate_conditionitemvalues", id_="0")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=(f"sm = {sequences}.states.sm \\n"
    ...            f"quh = {sequences}.logs.quh"))    # doctest: +ELLIPSIS
    sm = sm(197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0, 197.0)
    quh = quh(1.0, 0.0)

    The "official" way to gain information on modified parameters or conditions is
    to use the method |HydPyServer.GET_query_getitemvalues|:

    >>> test("query_getitemvalues", id_="0")
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 500: RuntimeError: While trying to execute \
method `GET_query_getitemvalues`, the following error occurred: Nothing registered \
under the id `0`.  There is nothing registered, so far.

    As the error message explains, we first need to fill the registry for the given
    `id` parameter.  As opposed to the examples above, we do not do this by sending
    external data via a POST request but by retrieving the server's currently active
    data.  We accomplish this task by calling the GET method
    |HydPyServer.GET_update_getitemvalues|:

    >>> test("update_getitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_getitemvalues", id_="0")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = nan
    land_dill_fluxes_qt_series = [nan]
    land_dill_states_sm = [185.13164, ...]
    land_lahn_1_states_sm = [1.0, 2.0, ..., 12.0, 13.0]
    land_lahn_2_states_sm = [197.0, ..., 197.0]
    land_lahn_3_states_sm = [101.31248, ...]
    land_lahn_3_states_sm_series = [[nan, ..., nan]]
    dill_nodes_sim_series = [nan]

    We now modify the parameter and condition values again, but this time in one
    step through calling |HydPyServer.POST_register_changeitemvalues| and
    |HydPyServer.GET_activate_changeitemvalues|:

    >>> test("register_changeitemvalues", id_="0",
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
    >>> test("activate_changeitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_changeitemvalues", id_="0")
    alpha = 1.0
    beta = 1.0
    lag = 0.0
    damp = 0.0
    sfcf_1 = 0.0
    sfcf_2 = 0.0
    sfcf_3 = 0.0
    sm_lahn_2 = 100.0
    sm_lahn_1 = 50.0
    quh = 0.0

    Next, we trigger a simulation run by calling the GET method
    |HydPyServer.GET_simulate|:

    >>> test("simulate")
    <BLANKLINE>

    Calling methods |HydPyServer.GET_update_getitemvalues| and
    |HydPyServer.GET_query_getitemvalues| now reveals how the simulation run
    modified our change items:

    >>> test("update_getitemvalues", id_="0")    # doctest: +ELLIPSIS
    <BLANKLINE>
    >>> test("query_getitemvalues", id_="0")    # doctest: +ELLIPSIS
    land_dill_fluxes_qt = 7.735543
    ...
    land_lahn_2_states_sm = [99.848023, ..., 99.848023]
    ...
    dill_nodes_sim_series = [7.735543]

    So far, we have explained how the *HydPy* server memorises different exchange
    item values for different values of query parameter `id`.  Complicating matters,
    memorising condition values must also take the relevant time point into account.
    You load conditions for the simulation period's current start date with method
    |HydPyServer.GET_load_internalconditions|, and you save them for the current end
    date with method |HydPyServer.GET_save_internalconditions|.  To give an example,
    we first save the states calculated for the end time of the last simulation run
    (January 2):

    >>> test("query_simulationdates", id_="0")
    firstdate_sim = 1996-01-01T00:00:00+01:00
    lastdate_sim = 1996-01-02T00:00:00+01:00
    >>> test("evaluate",
    ...      data=f"sm_lahn2 = {sequences}.states.sm")    # doctest: +ELLIPSIS
    sm_lahn2 = sm(99.848023, ..., 99.848023)
    >>> test("save_internalconditions", id_="0")
    <BLANKLINE>

    Calling method |HydPyServer.GET_load_internalconditions| without changing the
    simulation dates reloads the initial conditions for January 1, originally read
    from disk:

    >>> test("load_internalconditions", id_="0")
    <BLANKLINE>
    >>> test("evaluate",
    ...      data=f"sm_lahn2 = {sequences}.states.sm")    # doctest: +ELLIPSIS
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
    ...      data=f"sm_lahn2 = {sequences}.states.sm")    # doctest: +ELLIPSIS
    sm_lahn2 = sm(99.848023, ..., 99.848023)

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

    Some algorithms provide new information about initial conditions and require
    information on how they evolve during a simulation.  For such purposes, you can
    use method |HydPyServer.GET_update_conditionitemvalues| to store the current
    conditions under an arbitrary `id` and use method
    |HydPyServer.GET_query_conditionitemvalues| to query them later.  Please note
    that these methods are not flexible enough for many real-world applications
    yet and we will improve them later:

    >>> test("update_conditionitemvalues", id_="0")
    <BLANKLINE>
    >>> test("query_conditionitemvalues", id_="0")    # doctest: +ELLIPSIS
    sm_lahn_2 = [ 99.84802...]
    sm_lahn_1 = [ 49.92944...]
    quh = [ 0.00081...]

    Above, we explained the recommended way to query the initial values of all or
    a subgroup of the available exchange items.  Alternatively, you can first register
    the initial values and query them later, which is a workaround for retrieving
    initial and intermediate values with the same HTTP request (a requirement of
    `OpenDA`_):

    >>> test("register_initialitemvalues", id_="1")
    <BLANKLINE>
    >>> test("query_itemvalues", id_="1")    # doctest: +ELLIPSIS
    alpha = 2.0
    beta = 1.0
    lag = 5.0
    damp = 0.5
    sfcf_1 = 0.3
    sfcf_2 = 0.2
    sfcf_3 = [ 0.1  0.2  0.1  0.2  0.1  0.2  0.1  0.2  0.1  0.2  0.1  0.2  0.2  0.2]
    sm_lahn_2 = 123.0
    sm_lahn_1 = [ 110.  120.  130.  140.  150.  160.  170.  180.  190.  200.  210.  220.
      230.]
    quh = 10.0
    land_dill_fluxes_qt = nan
    land_dill_fluxes_qt_series = [nan, nan, nan, nan, nan]
    land_dill_states_sm = [185.13164...]
    land_lahn_1_states_sm = [99.27505...]
    land_lahn_2_states_sm = [138.31396...]
    land_lahn_3_states_sm = [101.31248...]
    land_lahn_3_states_sm_series = [[nan, ...], [nan, ...], ..., [nan, ...]]
    dill_nodes_sim_series = [nan, nan, nan, nan, nan]

    To close the *HydPy* server, call |HydPyServer.GET_close_server|:

    >>> test("close_server")
    <BLANKLINE>
    >>> process.kill()
    >>> _ = process.communicate()
    """

    # pylint: disable=invalid-name
    # due to "GET" and "POST" method names in accordance with BaseHTTPRequestHandler

    state: ClassVar[ServerState]
    extensions_map: ClassVar[Dict[str, str]]
    _requesttype: Literal["GET", "POST"]
    _statuscode: Literal[200, 400, 500]
    _inputs: Dict[str, str]
    _outputs: Dict[str, object]

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
    def _id(self) -> ID:
        return self._get_queryparameter("id")

    def _get_queryparameter(self, name: str) -> ID:
        query = urllib.parse.urlparse(self.path).query
        try:
            return cast(ID, urllib.parse.parse_qs(query)[name][0])
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
        """Evaluate any valid Python expression with the *HydPy* server process
        and get its result.

        Method |HydPyServer.POST_evaluate| serves to test and debug, primarily.
        The main documentation on class |HydPyServer| explains its usage.
        """
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
        self.GET_query_getitemtypes()

    def GET_query_changeitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change the
        values of |Parameter|, |StateSequence|, or |LogSequence| objects."""
        self.GET_query_parameteritemtypes()
        self.GET_query_conditionitemtypes()

    def GET_query_parameteritemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change
        the values of |Parameter| objects."""
        for item in self.state.parameteritems:
            self._outputs[item.name] = self._get_query_itemtype(item)

    def GET_query_conditionitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to change
        the values of |StateSequence| or |LogSequence| objects."""
        for item in self.state.conditionitems:
            self._outputs[item.name] = self._get_query_itemtype(item)

    def GET_query_getitemtypes(self) -> None:
        """Get the types of all current exchange items supposed to return
        the values of |Parameter| or |Sequence_| objects or the time series
        of |IOSequence| objects."""
        for item in self.state.getitems:
            type_ = self._get_query_itemtype(item)
            for name, _ in item.yield_name2value():
                self._outputs[name] = type_

    def GET_query_initialitemvalues(self) -> None:
        """Get the initial values of all current exchange items."""
        self.GET_query_initialchangeitemvalues()
        self.GET_query_initialgetitemvalues()

    def GET_register_initialitemvalues(self) -> None:
        """Register the initial values of all current exchange items under the
        given `id`.

        Implemented as a workaround to support `OpenDA`.  Better use method
        |HydPyServer.GET_query_initialitemvalues|.
        """
        self.GET_register_initialchangeitemvalues()
        self.GET_register_initialgetitemvalues()

    def GET_query_initialchangeitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change
        the values of |Parameter|, |StateSequence|, or |LogSequence| objects."""
        self.GET_query_initialparameteritemvalues()
        self.GET_query_initialconditionitemvalues()

    def GET_register_initialchangeitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to
        change the values of |Parameter|, |StateSequence|, or |LogSequence| objects
        under the given `id`.

        Implemented as a workaround to support `OpenDA`.  Better use method
        |HydPyServer.GET_query_initialchangeitemvalues|.
        """
        self.GET_register_initialparameteritemvalues()
        self.GET_register_initialconditionitemvalues()

    def GET_query_initialparameteritemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change
        the values of |Parameter| objects."""
        for name, value in self.state.initialparameteritemvalues.items():
            self._outputs[name] = value

    def GET_register_initialparameteritemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to
        change the values of |Parameter| objects under the given `id`.

        Implemented as a workaround to support `OpenDA`.  Better use method
        |HydPyServer.GET_query_initialparameteritemvalues|.
        """
        item2value = {}
        for name, value in self.state.initialparameteritemvalues.items():
            item2value[name] = value
        self.state.parameteritemvalues[self._id] = item2value

    def GET_query_initialconditionitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to change
        the values of |StateSequence| or |LogSequence| objects."""
        for name, value in self.state.initialconditionitemvalues.items():
            self._outputs[name] = value

    def GET_register_initialconditionitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to
        change the values of |StateSequence| or |LogSequence|  objects under the
        given `id`.

        Implemented as a workaround to support `OpenDA`.  Better use method
        |HydPyServer.GET_query_initialconditionitemvalues|.
        """
        item2value = {}
        for name, value in self.state.initialconditionitemvalues.items():
            item2value[name] = value
        self.state.conditionitemvalues[self._id] = item2value

    def GET_query_initialgetitemvalues(self) -> None:
        """Get the initial values of all current exchange items supposed to return
        the values of |Parameter| or |Sequence_| objects or the time series
        of |IOSequence| objects."""
        for name, value in self.state.initialgetitemvalues.items():
            self._outputs[name] = value

    def GET_register_initialgetitemvalues(self) -> None:
        """Register the initial values of all current exchange items supposed to
        return the values of |Parameter| or |Sequence_| objects or the time series
        of |IOSequence| objects under the given `id`.

        Implemented as a workaround to support `OpenDA`.  Better use method
        |HydPyServer.GET_query_initialgetitemvalues|.
        """
        item2value = {}
        for name, value in self.state.initialgetitemvalues.items():
            item2value[name] = value
        self.state.getitemvalues[self._id] = item2value

    def GET_query_initialisationtimegrid(self) -> None:
        """Return the general |Timegrids.init| time grid."""
        tg = hydpy.pub.timegrids.init
        utc = hydpy.pub.options.utcoffset
        self._outputs["firstdate_init"] = tg.firstdate.to_string("iso1", utc)
        self._outputs["lastdate_init"] = tg.lastdate.to_string("iso1", utc)
        self._outputs["stepsize"] = tg.stepsize

    def _get_registered_content(self, dict_: Dict[ID, T]) -> T:
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
        self.GET_query_getitemvalues()

    def POST_register_changeitemvalues(self) -> None:
        """Register the send values of all |ChangeItem| objects under the given
        `id`."""
        self.POST_register_parameteritemvalues()
        self.POST_register_conditionitemvalues()

    def GET_activate_changeitemvalues(self) -> None:
        """Activate the values of the |ChangeItem| objects registered under the
        given `id`."""
        self.GET_activate_parameteritemvalues()
        self.GET_activate_conditionitemvalues()

    def GET_query_changeitemvalues(self) -> None:
        """Get the values of all |ChangeItem| objects registered under the given
        `id`."""
        self.GET_query_parameteritemvalues()
        self.GET_query_conditionitemvalues()

    def _post_register_itemvalues(
        self,
        typename: str,
        items: Iterable[itemtools.ChangeItem],
        itemvalues: Dict[ID, Dict[Name, Any]],
    ) -> None:
        item2value: Dict[Name, Any] = {}
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
            self._outputs[item] = value

    def POST_register_conditionitemvalues(self) -> None:
        """Register the send condition values under the given `id`."""
        self._post_register_itemvalues(
            typename="condition",
            items=self.state.conditionitems,
            itemvalues=self.state.conditionitemvalues,
        )

    def GET_activate_conditionitemvalues(self) -> None:
        """Activate the condition values logged under the given `id`."""
        item2value = self._get_registered_content(self.state.conditionitemvalues)
        for item in self.state.conditionitems:
            item.value = item2value[item.name]
            item.update_variables()

    def GET_update_conditionitemvalues(self) -> None:
        """ToDo: extend functionality"""
        item2value = self._get_registered_content(self.state.conditionitemvalues)
        for item in self.state.conditionitems:
            item2value[item.name] = copy.deepcopy(
                list(item.device2target.values())[0].value
            )

    def GET_query_conditionitemvalues(self) -> None:
        """Return the condition values logged under the given `id`."""
        item2value = self._get_registered_content(self.state.conditionitemvalues)
        for item, value in item2value.items():
            self._outputs[item] = value

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
        conditions of the current process (usually those of the conditions files
        of the respective *HydPy*  project).
        """
        try:
            self.state.hp.conditions = self.state.conditions[self._id][self.state.idx1]
        except KeyError:
            if self.state.idx1:
                self._statuscode = 500
                raise RuntimeError(
                    f"Conditions for ID `{self._id}` and time point "
                    f"`{hydpy.pub.timegrids.sim.firstdate}` are required, "
                    f"but have not been calculated so far."
                ) from None
            self.state.hp.conditions = self.state.init_conditions

    def GET_update_getitemvalues(self) -> None:
        """Register the current |GetItem| values under the given `id`.

        For |GetItem| objects observing time series, method
        |HydPyServer.GET_update_getitemvalues| registers only the values within
        the current simulation period.
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

    @classmethod
    def GET_simulate(cls) -> None:
        """Perform a simulation run."""
        cls.state.hp.simulate()


def start_server(
    socket: Union[int, str],
    projectname: str,
    xmlfilename: str,
    maxrequests: Union[int, str] = 5,
) -> None:
    """Start the *HydPy* server using the given socket.

    The folder with the given `projectname` must be available within the
    current working directory.  The XML configuration file must be placed
    within the project folder unless `xmlfilename` is an absolute file path.
    The XML configuration file must be valid concerning the schema file
    `HydPyConfigMultipleRuns.xsd` (see class |ServerState| for further information).

    The |HydPyServer| allows for five still unhandled requests before refusing new
    connections by default.  Use the optional `maxrequests` argument to increase this
    number (which might be necessary when parallelising optimisation or data
    assimilation):

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> command = \
"hyd.py start_server 8080 LahnH multiple_runs_alpha.xml maxrequests=100"
    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():
    ...     process = run_subprocess(command, blocking=False, verbose=False)
    ...     result = run_subprocess("hyd.py await_server 8080 10", verbose=False)

    >>> from urllib import request
    >>> command = "maxrequests = self.server.request_queue_size"
    >>> response = request.urlopen("http://localhost:8080/evaluate",
    ...                            data=bytes(command, encoding="utf-8"))
    >>> print(str(response.read(), encoding="utf-8"))
    maxrequests = 100

    >>> _ = request.urlopen("http://localhost:8080/close_server")
    >>> process.kill()
    >>> _ = process.communicate()

    Note that function |start_server| tries to read the "mime types" from
    a dictionary stored in the file `mimetypes.txt` available in subpackage
    `conf` and passes it as attribute `extension_map` to class |HydPyServer|.
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
            types_map: Dict[str, str] = eval(str(open(file_.read())))
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
        with open(filepath, "w") as file_:
            file_.write(str(types_map))
    HydPyServer.extensions_map = types_map
    HydPyServer.state = ServerState(
        projectname=projectname,
        xmlfile=xmlfilename,
    )

    class _HTTPServer(http.server.HTTPServer):

        request_queue_size = int(maxrequests)

    server = _HTTPServer(("", int(socket)), HydPyServer)
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
