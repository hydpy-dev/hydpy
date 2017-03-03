# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy import pub
from hydpy.framework import objecttools


class Model(object):
    """Base class for hydrological models."""

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None

    def connect(self):
        """Connect the link sequences of the actual model."""
        conname_isexit_pairs = (('inlets', True),
                                ('receivers', True),
                                ('outlets', False),
                                ('senders', False))
        for (conname, isexit) in conname_isexit_pairs:
            nodes = getattr(self.element, conname).slaves
            if len(nodes) == 1:
                node = nodes[0]
                links = getattr(self.sequences, conname)
                seq = getattr(links, node.variable.lower(), None)
                if seq is None:
                    RuntimeError('ToDo')
                elif isexit:
                    seq.setpointer(node.getdouble_via_exits())
                else:
                    seq.setpointer(node.getdouble_via_entries())
            else:
                NotImplementedError('ToDo')
#        nodes = self.element.inlets.slaves
#        if len(nodes) == 1:
#            node = nodes[0]
#            seq = getattr(self.sequences.inlets, node.variable.lower(), None)
#            if seq is None:
#                RuntimeError('ToDo')
#            else:
#                seq.setpointer(node.getdouble_via_exits())
#        else:
#            NotImplementedError('ToDo')
#        nodes = self.element.outlets.slaves
#        if not nodes:
#            RuntimeError('ToDo')
#        elif len(nodes) == 1:
#            node = nodes[0]
#            seq = getattr(self.sequences.outlets, node.variable.lower(), None)
#            if seq is None:
#                RuntimeError('ToDo')
#            else:
#                seq.setpointer(node.getdouble_via_entries())
#        else:
#            NotImplementedError('ToDo')

    def updatereceivers(self, idx):
        pass

    def updatesenders(self, idx):
        pass

    def doit(self, idx):
        self.loaddata(idx)
        self.updateinlets(idx)
        self.run(idx)
        self.updateoutlets(idx)
        self.updatesenders(idx)
        self.new2old()
        self.savedata(idx)

    def loaddata(self, idx):
        self.sequences.loaddata(idx)

    def savedata(self, idx):
        self.sequences.savedata(idx)

    def updateinlets(self, idx):
        """Maybe."""
        pass

    def updateoutlets(self, idx):
        """In any case."""
        pass

    def new2old(self):
        """Assign the new/final state values of the actual time step to the
        new/initial state values of the next time step.  Needs to be
        overwritten in Cython mode.
        """
        try:
            self.sequences.states.new2old()
        except AttributeError:
            pass

    def __dir__(self):
        return objecttools.dir_(self)




class _Model(object):

    def __init__(self, nodes):
        """ general settings """

        self.nodes = nodes
        try:
            self.area = float(info['area'])
        except KeyError:
            self.area = None
        # determine factor for time unit conversion of parameters
        if not hasattr(self, 'par_timestep'):
            self.par_timestep = info.get('par_timestep', '1d')
        self.unitfactor = pub.timegrids.parfactor(self.par_timestep)

        if self.usecython:
            cythonizer = modelutillas.Cythonizer(self)
            cythonizer.update(info)
            module = cythonizer.cymodule
        else:
            module = None

        self.cymodel = None

        self.parameters = parameters.Parameters(module)
        self.initParameters(info)
        self.sequences = sequences.Sequences(module)
        self.initArrays(info)

        if self.usecython:
            self.cymodel = cythonizer.getmodel()
            self.doit = self.cymodel.doit
            self.openfiles = self.cymodel.openfiles
            self.closefiles = self.cymodel.closefiles


    def initParameters(self,info):
        """ Initiaze all parameters.
        All parameters are taken from the dictionary 'info'.
        "1d" is the standard parameter time unit.
        Checking of parameter bounds is performed.
        """

        self.parameters.control % info

        # get solver parameters for numerical integration
        #if self.solver != 'adhoc':
        if False:
            self.setSolverPars(info)

        # calculate secondary parameters, which are not changed during calibration
        self.calcStaticSecPars(info)

        # calculate secondary parameters, which are not changed during calibration
        self.calcDynamicSecPars()

        #self.loadPfracMetaParameters(info)

    def calcStaticSecPars(self, info):
        """ calculate secondary parameters, which are not changed during calibration """
        pass

    def calcDynamicSecPars(self, info):
        """ calculate secondary parameters, which can be changed during calibration """
        pass

    def set_contrpars(self, info, float2array):
        """ parameter updating and array reseting
        (no change of initial storage values) """

        # update parameter values
        self.parameters.update(self.standardParameters, info,
                            self.timestepFactorUser, float2array)
        # calculate secondary parameters, which are not changed during calibration
        self.calcDynamicSecPars()
        # reset storage and flux arrays
        self.reset()

    def getContrPars(self):
        """ returns one list with all keywords and one list with all
        parameter values of the zone model as strings. only useful for
        writing the parameter zone control file """

        # get model specific parameters from parameter handler
        info = self.parameters.getFileInfo(True,
                                        self.standardParameters,
                                        self.timestepFactorUser)
        # general parameters
        info['unitsTimestep'] = str(self.unitsTimestepUser)
        try: info['area'] = str(self.area)
        except: pass

        return info

    def initArrays(self, info=None):
        """ Initialize all sequences.

        "Flux-arrays" have a length equal to the number of timesteps.
        "Storage-arrays" have one more entry: the first one is the initial value.
        """
        # set initial values if an info dictionary is given
        if info is not None:
            self.set_initvals(info)

    def set_initvals(self, info, float2array=True, idx_date=0):
        """ set initial storage values und initial Q values """
        self.sequences.set_initvals(info, idx_date)

    def get_initvals(self, idxDate, valuesAsText=False):
        """ returns one list with all keywords and one list with all
        initial values of the zone model as strings. only useful for
        writing  the parameter zone control file """

        # get storage values
        info = self.sequences.getFileInfo(idxDate, valuesAsText)

        return info

    def setInput(self, sim, idxDateStart=None, idxDateEnd=None, idxFlux=None):

        pass

    def getOutput(self, idxDateStart=None, idxDateEnd=None, idxFlux=None):

        pass

    def reset(self, idxDateStart=None, idxDateEnd=None):
        """ set array values of the zone model to 0,
        except initial values """
        # ToDo
        pass

    def run(self, idx):
        """ """
        pass

    def modifyInputArrays(self,info):

        for arrayName,arrayValues in info.iteritems():
            exec('s.sequences.input.%s[:] = arrayValues'%arrayName)


    def writeArrays(self, arrayInfo, suffix='', mode=None,
                    idxDateStart=None, idxDateEnd=None):
        """ write specified arrays """

        self.sequences.writeArrays(self, arrayInfo, suffix, mode,
                             idxDateStart, idxDateEnd)


    def getShortcuts(s):
        return '\n'.join(('ph = s.parameters',
                          'phSt = ph.statSecPars',
                          'phDy = ph.dynSecPars',
                          'phSo = ph.solverPars',
                          'ih = s.sequences.input',
                          'fh = s.sequences.flux',
                          'sh = s.sequences.storage'))


    def get_addmethods(self):
        a = modelutils.AddMethods()
        with a.nextmethod(self.doit, functype='cpdef', inline=True):
            with a.nexttype(int):
                a.addvars('idx')
        with a.nextmethod(self.run, functype='cdef', inline=True):
            with a.nexttype(int):
                a.addvars('idx')
        with a.nextmethod(self.getinputs, functype='cdef', inline=True):
            with a.nexttype(int):
                a.addvars('idx')
        with a.nextmethod(self.addoutputs, functype='cdef', inline=True):
            with a.nexttype(int):
                a.addvars('idx')
        return a

    def doit(self, idx):
        self.loaddata(idx)
        self.getinputs(idx)
        self.run(idx)
        self.addoutputs(idx)
        self.new2old()
        self.savedata(idx)

    def openfiles(self, idx):
        self.sequences.openfiles(idx)

    def closefiles(self):
        self.sequences.closefiles()

    def loaddata(self, idx):
        self.sequences.inputs.loaddata(idx)

    def savedata(self, idx):
        self.sequences.fluxes.savedata(idx)
        self.sequences.states.savedata(idx)

    def getinputs(self, idx):
        """Maybe."""
        pass

    def addoutputs(self, idx):
        """In any case."""
        pass

    def new2old(self):
        """Assign the new/final state values of the actual time step to the
        new/initial state values of the next time step.  Needs to be
        overwritten in Cython mode.
        """
        self.sequences.states.new2old()