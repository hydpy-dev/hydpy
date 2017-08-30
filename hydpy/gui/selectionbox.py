# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import tkinter
# ...from HydPy
from hydpy import pub


class SelectionBox(tkinter.Toplevel):

    def __init__(self, master):
        tkinter.Toplevel.__init__(self, master)
        self.listbox = ListBox(self)
        self.listbox.pack(side=tkinter.LEFT)


class ListBox(tkinter.Listbox):

    def __init__(self, master):
        tkinter.Listbox.__init__(self, master)
        for name in pub.selections.names:
            self.insert(tkinter.END, name)
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        name = self.get(int(self.curselection()[0]))
        self.master.master.master.master.update_selection(getattr(pub.selections, name))
