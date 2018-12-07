# -*- coding: utf-8 -*-
"""


>>> from hydpy.core.examples import prepare_full_example_1
>>> prepare_full_example_1()

>>> from hydpy import run_subprocess, TestIO
>>> import subprocess
>>> with TestIO():
...     process = subprocess.Popen(
...         'hyd.py start_server 8080 LahnH 1996-01-01 1996-01-06 1d',
...         shell=True)
...     run_subprocess('hyd.py await_server 8080 10', verbose=False)

>>> from urllib import request
>>> from hydpy import print_values
>>> def test(id_, time_, alpha):
...     content = (f"alpha= [{alpha}] \\n"
...                f"refdate= '01 jan 1996' \\n"
...                f"unit= '1d' \\n"
...                f"time={time_} \\n"
...                f"dill.discharge=[0.0] \\n"
...                f"lahn_1.discharge=[0.0]").encode('utf-8')
...     for methodname in ('period', 'parametervalues', 'load_conditionvalues',
...                  'conditionvalues', 'simulate', 'save_conditionvalues',
...                  'itemvalues'):
...         url = f'http://localhost:8080/{methodname}?id={id_}'
...         if methodname in ('period', 'parametervalues', 'conditionvalues'):
...             response = request.urlopen(url, data=content)
...         else:
...             response = request.urlopen(url)
...         result = response.read()
...     lines = str(result, encoding='utf-8').split('\\n')
...     for line in lines:
...         if line.startswith('dill.discharge'):
...             values = eval(line.split('=')[1])
...             print_values(values)

Single simulation run:

>>> test(id_='workingdir1', time_=[0.0,1.0,5.0], alpha=2.0)
35.250827, 7.774062, 5.035808, 4.513706, 4.251594

Multiple interlockingsimulation runs:

>>> test(id_='workingdir2', time_=[0.0,1.0,1.0], alpha=2.0)
35.250827

>>> test(id_='workingdir3', time_=[0.0,1.0,3.0], alpha=2.0)
35.250827, 7.774062, 5.035808

>>> test(id_='workingdir2', time_=[1.0,1.0,5.0], alpha=2.0)
7.774062, 5.035808, 4.513706, 4.251594

Parallel runs with different parameterisations:

>>> test(id_='workingdir4', time_=[0.0,1.0,3.0], alpha=2.0)
35.250827, 7.774062, 5.035808

>>> test(id_='workingdir5', time_=[0.0,1.0,3.0], alpha=1.0)
11.658511, 8.842278, 7.103614

>>> test(id_='workingdir4', time_=[3.0,1.0,5.0], alpha=2.0)
4.513706, 4.251594

>>> test(id_='workingdir5', time_=[3.0,1.0,5.0], alpha=1.0)
6.00763, 5.313751

>>> test(id_='workingdir1', time_=[0.0, 1.0, 5.0], alpha=1.0)
11.658511, 8.842278, 7.103614, 6.00763, 5.313751


>>> _ = request.urlopen('http://localhost:8080/close_server')
>>> process.kill()
>>> _ = process.communicate()
"""
# import...
# ...from standard library
import collections
import http.server
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import List
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import hydpytools


class ServerState(object):

    def __init__(self):
        self.hp: hydpytools.HydPy = None
        self.conditions: collections.defaultdict = None
        self.init_conditions: dict = None
        self.id_: str = None
        self.idx1: int = None
        self.idx2: int = None
        self.inputlines: List[str] = None
        self.outputlines: List[str] = None

    def initialize(self, projectname):
        self.hp = hydpytools.HydPy(projectname)
        hp = self.hp
        pub.options.printprogress = False
        hp.prepare_network()
        hp.init_models()
        hp.prepare_simseries()
        hp.prepare_modelseries()
        hp.load_inputseries()
        hp.load_conditions()
        self.conditions = collections.defaultdict(lambda: {})
        self.init_conditions = hp.conditions


state = ServerState()

        
class HydPyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        try:
            self._set_headers()
            externalname = urllib.parse.urlparse(self.path).path[1:]
            internalname = f'get_{externalname}'
            try:
                state.id_ = urllib.parse.parse_qsl(self.path)[0][1]
            except IndexError:
                state.id_ = None
            try:
                method = getattr(self, internalname)
            except AttributeError:
                raise AttributeError(
                    f'No GET method for property `{externalname}` available.')
            try:
                method()
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying execute the GET method '
                    f'of property {externalname}')
            if method is not self.get_close_server:
                output = '\n'.join(state.outputlines)
            self.wfile.write(bytes(output, encoding='utf-8'))
        except BaseException as exc:
            self.wfile.write(bytes(f'{type(exc)}: {exc}', encoding='utf-8'))

    def do_POST(self):
        try:
            self._set_headers()
            externalname = urllib.parse.urlparse(self.path).path[1:]
            internalname = f'post_{externalname}'
            content_length = int(self.headers['Content-Length'])
            state.id_ = urllib.parse.parse_qsl(self.path)[0][1]
            state.inputlines = str(
                self.rfile.read(content_length), encoding='utf-8').split('\n')
            state.outputlines = []
            try:
                method = getattr(self, internalname)
            except AttributeError:
                raise AttributeError(
                    f'No POST method for property `{externalname}` available.')
            try:
                method()
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying execute the POST method '
                    f'of property {externalname}')
            output = '\n'.join(state.outputlines)
            self.wfile.write(bytes(output, encoding='utf-8'))
        except BaseException as exc:
            self.wfile.write(bytes(f'{type(exc)}: {exc}', encoding='utf-8'))

    def get_status(self):
        self.outputlines.append('ready')

    def get_close_server(self):
        self.wfile.write(b'shutting down server')
        shutter = threading.Thread(target=self.server.shutdown)
        shutter.deamon = True
        shutter.start()



    def post_process_input(self):
        self.post_period()
        self.post_parametervalues()
        self.get_load_conditionvalues()
        self.post_conditionvalues()
        self.get_simulate()
        self.get_save_conditionvalues()
        self.get_itemvalues()

    def get_period(self):

    def post_period(self):
        for line in state.inputlines:
            if line.startswith('time'):
                time_ = [int(t) for t in eval(line.split('=')[1])]
        init = pub.timegrids.init
        sim = pub.timegrids.sim
        sim.firstdate = init.firstdate + f'{time_[0]}d'
        sim.lastdate = init.firstdate + f'{time_[2]}d'
        state.idx1 = init[sim.firstdate]
        state.idx2 = init[sim.lastdate]

    def post_parametervalues(self):
        alpha = None
        for line in state.inputlines:
            if line.startswith('alpha'):
                alpha = eval(line.split('=')[1])[0]
        if alpha is not None:
            for element in state.hp.elements.catchment:
                getattr(element.model.parameters.control, 'alpha')(alpha)

    def post_conditionvalues(self):
        lz = None
        for line in state.inputlines:
            if line.startswith('lz'):
                lz = eval(line.split('=')[1])[0]
        if lz is not None:
            element = state.hp.elements.land_lahn_1
            element.model.sequences.states.lz(lz)

    def get_load_conditionvalues(self):
        if not state.idx1:
            state.hp.conditions = state.init_conditions
        else:
            state.hp.conditions = state.conditions[state.id_][state.idx1]

    def get_save_conditionvalues(self):
        state.conditions[state.id_][
            state.idx2] = state.hp.conditions

    def get_simulate(self):
        state.hp.doit()

    def get_itemvalues(self):
        outlines = []
        for line in state.inputlines:
            key = line.split('=')[0]
            if key.endswith('.discharge'):
                node = getattr(state.hp.nodes, key[:-10])
                series = node.sequences.sim.series
                line = f'{key}={list(series[state.idx1:state.idx2])}'
            if 'lz' in key:
                element = state.hp.elements.land_lahn_1
                line = f'lz = [{element.model.sequences.states.lz.value}]'
            outlines.append(line)
        state.outputlines = outlines


def start_server(
        socket, projectname, firstdate, lastdate, stepsize,
        *, logfile=None) -> None:
    pub.timegrids = firstdate, lastdate, stepsize
    state.initialize(projectname)
    server = http.server.HTTPServer(('', int(socket)), HydPyHTTPRequestHandler)
    server.serve_forever()


def await_server(port, seconds):
    """

    >>> from hydpy import run_subprocess, TestIO
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     run_subprocess('hyd.py await_server 8080 0.1')
    Invoking hyd.py with arguments `...hyd.py, await_server, 8080, 0.1` \
resulted in the following error:
    <urlopen error Waited for 0.1 seconds without response on port 8080.>
    ...

    >>> import subprocess
    >>> from hydpy.core.examples import prepare_full_example_1
    >>> prepare_full_example_1()
    >>> with TestIO():
    ...     process = subprocess.Popen(
    ...         'hyd.py start_server 8080 LahnH 1996-01-01 1996-01-06 1d',
    ...         shell=True)
    ...     run_subprocess('hyd.py await_server 8080 10')

    >>> from urllib import request
    >>> _ = request.urlopen('http://localhost:8080/close_server')
    >>> process.kill()
    >>> _ = process.communicate()
    """
    now = time.perf_counter()
    end = now + float(seconds)
    while now <= end:
        try:
            urllib.request.urlopen(f'http://localhost:{port}/status')
            break
        except urllib.error.URLError:
            time.sleep(0.1)
            now = time.perf_counter()
    else:
        raise urllib.error.URLError(
            f'Waited for {seconds} seconds without response on port {port}.')


pub.scriptfunctions['start_server'] = start_server
pub.scriptfunctions['await_server'] = await_server


autodoctools.autodoc_module()
