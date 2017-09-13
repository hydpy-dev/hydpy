
# import...
# ...from standard library
from __future__ import division, print_function
import tkinter


class Selection(object):

    def __init__(self):
        self.models = []
        self.modelstr = None
        self.groups = []
        self.groupstr = None
        self.subgroups = []
        self.subgroupstr = None
        self.variables = []
        self.variablestr = None

    def modelupdate(self, modelstr, hydpy):
        self.modelstr = modelstr
        self.models = []
        for (name, element) in hydpy.elements:
            if modelstr == model2str(element.model):
                self.models.append(element.model)
        self.groupdelete()

    def groupdelete(self):
        self.groups = []
        self.groupstr = None
        self.subgroupdelete()

    def groupupdate(self, groupstr):
        self.groupstr = groupstr
        self.groups = []
        for model in self.models:
            self.groups.append(getattr(model, groupstr))
        self.subgroupdelete()

    def subgroupdelete(self):
        self.subgroups = []
        self.subgroupstr = None
        self.variabledelete()

    def subgroupupdate(self, subgroupstr):
        self.subgroupstr = subgroupstr
        self.subgroups = []
        for group in self.groups:
            self.subgroups.append(getattr(group, subgroupstr))
        self.variabledelete()

    def variabledelete(self):
        self.variables = []
        self.variablestr = None

    def variableupdate(self, variablestr):
        self.variablestr = variablestr
        self.variables = []
        for subgroup in self.subgroups:
            self.variables.append(getattr(subgroup, variablestr))


    def __eq__(self, other):
        return ((self.modelstr == other.modelstr) and
                (self.groupstr == other.groupstr) and
                (self.subgroupstr == other.subgroupstr) and
                (self.variablestr == other.variablestr))


def model2str(model):
    return str(type(model)).split('.')[-2]


class Selector(tkinter.Toplevel):

    def __init__(self, selections, hydpy):
        tkinter.Toplevel.__init__(self)
        self.hydpy = hydpy
        self.selection = Selection()
        self.selections = selections
        self.modellistbox = ModelListbox(self)
        self.modellistbox.pack(side=tkinter.LEFT)
        self.grouplistbox = GroupListbox(self)
        self.grouplistbox.pack(side=tkinter.LEFT)
        self.variablelistbox = VariableListbox(self)
        self.variablelistbox.pack(side=tkinter.LEFT)
        self.resultlistbox = ResultListbox(self)
        self.resultlistbox.pack(side=tkinter.LEFT)


class ModelListbox(tkinter.Listbox):

    def __init__(self, master):
        tkinter.Listbox.__init__(self, master, exportselection=0)
        names = []
        for (name, element) in self.master.hydpy.elements:
            name = model2str(element.model)
            if name not in names:
                names.append(name)
        for name in sorted(names):
            self.insert(tkinter.END, name)
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        idx = int(self.curselection()[0])
        self.master.selection.modelupdate(self.get(idx), self.master.hydpy)
        self.master.grouplistbox.update()


class GroupListbox(tkinter.Listbox):

    def __init__(self, master):
        tkinter.Listbox.__init__(self, master, exportselection=0)
        self.bind('<Double-Button-1>', self.select)

    def update(self):
        self.delete(0, tkinter.END)
        self.master.selection.groupupdate('sequences')
        names = []
        for (name, subgroup) in self.master.selection.groups[0]:
            if name not in ('aides', 'logs', 'links') and subgroup:
                names.append(name)
        for name in sorted(names):
            self.insert(tkinter.END, name)
        self.master.variablelistbox.delete(0, tkinter.END)

    def select(self, event):
        idx = int(self.curselection()[0])
        self.master.selection.subgroupupdate(self.get(idx))
        self.master.variablelistbox.update()


class VariableListbox(tkinter.Listbox):

    def __init__(self, master):
        tkinter.Listbox.__init__(self, master, exportselection=0)
        self.bind('<Double-Button-1>', self.select)

    def update(self):
        self.delete(0, tkinter.END)
        names = []
        for (name, variable) in self.master.selection.subgroups[0]:
            names.append(name)
        for name in sorted(names):
            self.insert(tkinter.END, name)

    def select(self, event):
        idx = int(self.curselection()[0])
        self.master.selection.variableupdate(self.get(idx))
        if self.master.selection not in self.master.selections:
            sel = self.master.selection
            self.master.selections.append(sel)
            rlb = self.master.resultlistbox
            rlb.insert(tkinter.END, sel.variablestr)
            rlb.models[self.master.selection.modelstr] = sel.models[0]
            rlb.groups[self.master.selection.groupstr] = sel.groups[0]
            rlb.subgroups[self.master.selection.subgroupstr] = sel.subgroups[0]
            rlb.variables[self.master.selection.variablestr] = sel.variables[0]
        self.master.grouplistbox.delete(0, tkinter.END)
        self.master.variablelistbox.delete(0, tkinter.END)
        self.master.selection = Selection()


class ResultListbox(tkinter.Listbox):

    def __init__(self, master):
        tkinter.Listbox.__init__(self, master, exportselection=1)
        for selection in self.master.selections:
            self.insert(tkinter.END, selection.variablestr)
        self.bind('<Double-Button-1>', self.deselect)
        self.models = {}
        self.groups = {}
        self.subgroups = {}
        self.variables = {}

    def deselect(self, event):
        idx = int(self.curselection()[0])
        del(self.master.selections[idx])
        self.delete(idx)
