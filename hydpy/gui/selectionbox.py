# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
import tkinter
# ...from HydPy
import hydpy


class SelectionBox(tkinter.Toplevel):

    def __init__(self, selection):
        tkinter.Toplevel.__init__(self, selection)
        self.selection = selection
        self.listbox = ListBox(self)
        self.listbox.pack(side=tkinter.LEFT)


class ListBox(tkinter.Listbox):

    def __init__(self, selectionbox):
        tkinter.Listbox.__init__(self, selectionbox)
        self.selectionbox = selectionbox
        for name in hydpy.pub.selections.names:
            self.insert(tkinter.END, name)
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        name = self.get(int(self.curselection()[0]))
        self.selectionbox.selection.infoarea.submap.update_selection(
                                    getattr(hydpy.pub.selections, name))
