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
>>> def test(dirname, time_, alpha):
...     with TestIO():
...         if not os.path.exists(dirname):
...             os.mkdir(dirname)
...         dirpath = os.path.abspath(dirname).encode('utf-8')
...         with open(f'{dirname}/hydpy.exchange', 'w') as infile:
...             _ = infile.write(f'alpha= [{alpha}] \\n')
...             _ = infile.write("refdate= '01 jan 1996' \\n")
...             _ = infile.write("unit= '1d' \\n")
...             _ = infile.write(f'time={time_} \\n')
...             _ = infile.write('dill.discharge=[0.0] \\n')
...             _ = infile.write('lahn_1.discharge=[0.0] \\n')
...         _ = request.urlopen(
...             'http://localhost:8080/process_input', data=dirpath)
...         with open(f'{dirname}/hydpy.exchange') as outfile:
...             for line in outfile.readlines():
...                 if line.startswith('dill.discharge'):
...                     values = eval(line.split('=')[1])
...                     print_values(values)

Single simulation run:

>>> test(dirname='workingdir1', time_=[0.0,1.0,5.0], alpha=2.0)
35.250827, 7.774062, 5.035808, 4.513706, 4.251594

Multiple interlockingsimulation runs:

>>> test(dirname='workingdir2', time_=[0.0,1.0,1.0], alpha=2.0)
35.250827

>>> test(dirname='workingdir3', time_=[0.0,1.0,3.0], alpha=2.0)
35.250827, 7.774062, 5.035808

>>> test(dirname='workingdir2', time_=[1.0,1.0,5.0], alpha=2.0)
7.774062, 5.035808, 4.513706, 4.251594

Parallel runs with different parameterisations:

>>> test(dirname='workingdir4', time_=[0.0,1.0,3.0], alpha=2.0)
35.250827, 7.774062, 5.035808

>>> test(dirname='workingdir5', time_=[0.0,1.0,3.0], alpha=1.0)
11.658511, 8.842278, 7.103614

>>> test(dirname='workingdir4', time_=[3.0,1.0,5.0], alpha=2.0)
4.513706, 4.251594

>>> test(dirname='workingdir5', time_=[3.0,1.0,5.0], alpha=1.0)
6.00763, 5.313751

>>> test(dirname='workingdir1', time_=[0.0, 1.0, 5.0], alpha=1.0)
11.658511, 8.842278, 7.103614, 6.00763, 5.313751


>>> _ = request.urlopen('http://localhost:8080/close_server')
>>> process.kill()
>>> _ = process.communicate()
"""
# import...
# ...from standard library
import collections
import http.server
import os
import threading
import time
import urllib.error
import urllib.request
# ...from HydPy
from hydpy import pub
from hydpy.core import autodoctools
from hydpy.core import objecttools
from hydpy.core import hydpytools


class HydPyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        try:
            externalname = self.path[1:]
            internalname = f'get_{externalname}'
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
        except BaseException:
            self._set_headers()
            self.wfile.write(bytes(f'{type(exc)}: {exc}', encoding='utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            externalname = self.path[1:]
            internalname = f'post_{externalname}'
            try:
                method = getattr(self, internalname)
            except AttributeError:
                raise AttributeError(
                    f'No POST method for property `{externalname}` available.')
            try:
                method(post_data)
            except BaseException:
                objecttools.augment_excmessage(
                    f'While trying execute the POST method '
                    f'of property {externalname}')
            self._set_headers()
            self.wfile.write(
                bytes(f'POST request for {self.path}', encoding='utf-8'))
        except BaseException as exc:
            self._set_headers()
            self.wfile.write(bytes(f'{type(exc)}: {exc}', encoding='utf-8'))

    def get_status(self):
        self._set_headers()
        self.wfile.write(b'ready')

    def get_close_server(self):
        self._set_headers()
        self.wfile.write(b'shutting down server')
        shutter = threading.Thread(target=self.server.shutdown)
        shutter.deamon = True
        shutter.start()

    def post_process_input(self, post_data):
        dirpath = str(post_data, encoding='utf-8')
        filepath = os.path.join(dirpath, 'hydpy.exchange')
        alpha = None
        lz = None
        with open(filepath, 'r') as infile:
            lines = infile.readlines()
            for line in lines:
                if line.startswith('alpha'):
                    alpha = eval(line.split('=')[1])[0]
                if line.startswith('lz'):
                    lz = eval(line.split('=')[1])[0]
                if line.startswith('time'):
                    time_ = [int(t) for t in eval(line.split('=')[1])]
        init = pub.timegrids.init
        sim = pub.timegrids.sim
        sim.firstdate = init.firstdate + f'{time_[0]}d'
        sim.lastdate = init.firstdate + f'{time_[2]}d'
        idx1 = init[sim.firstdate]
        idx2 = init[sim.lastdate]
        if not idx1:
            self.server.hp.conditions = self.server.init_conditions
        else:
            self.server.hp.conditions = self.server.conditions[dirpath][idx1]
        if alpha is not None:
            for element in self.server.hp.elements.catchment:
                getattr(element.model.parameters.control, 'alpha')(alpha)
        if lz is not None:
            element = self.server.hp.elements.land_lahn_1
            element.model.sequences.states.lz(lz)
        self.server.hp.doit()
        self.server.conditions[dirpath][idx2] = self.server.hp.conditions
        filepath = os.path.join(dirpath, 'hydpy.exchange')
        with open(filepath, 'w') as outfile:
            for line in lines:
                key = line.split('=')[0]
                if key.endswith('.discharge'):
                    node = getattr(self.server.hp.nodes, key[:-10])
                    line = f'{key}={list(node.sequences.sim.series[idx1:idx2])}\n'
                if 'lz' in key:
                    line = f'lz = [{self.server.hp.elements.land_lahn_1.model.sequences.states.lz.value}]\n'
                outfile.write(line)


class HydPyHTTPServer(http.server.HTTPServer):

    hp: hydpytools.HydPy
    conditions: collections.defaultdict
    init_conditions: dict


    def prepare_hydpy(self, projectname):
        self.hp = hydpytools.HydPy(projectname)
        hp = self.hp
        pub.options.printprogress = False
        pub.sequencemanager.generalfiletype = 'nc'
        hp.prepare_network()
        hp.init_models()
        hp.prepare_simseries()
        hp.prepare_modelseries()
        pub.sequencemanager.open_netcdf_reader(
            flatten=True, isolate=True, timeaxis=0)
        hp.load_inputseries()
        pub.sequencemanager.close_netcdf_reader()
        hp.load_conditions()
        self.conditions = collections.defaultdict(lambda: {})
        self.init_conditions = hp.conditions


def start_server(
        socket, projectname, firstdate, lastdate, stepsize,
        *, logfile=None) -> None:
    server = HydPyHTTPServer(('', int(socket)), HydPyHTTPRequestHandler)
    pub.timegrids = firstdate, lastdate, stepsize
    server.prepare_hydpy(projectname)
    server.serve_forever()


def await_server(port, seconds, *, logfile=None):
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
