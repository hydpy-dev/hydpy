
# import...
# ...from standard library
from __future__ import division, print_function
import tkinter
#import tkColorChooser
# ...from site-packages
import numpy


class Colorbar(tkinter.Canvas):
    """Color scale for a single :class:`SubMap`."""

    def __init__(self, master, width, height, selections):
        tkinter.Canvas.__init__(self, master, width=width, height=height)
        self.selections = None
        self.minimum = None
        self.maximum = None
        self.values = []
        self.hexcolors = []
        self.rgbcolors = []
        self.newselections(selections)
        #self.bind('<Double-Button-1>', self.)

    def getminmax(self):
        if self.selections:
            self.minimum = numpy.inf
            self.maximum = -numpy.inf
            for selection in self.selections:
                for variable in selection.variables:
                    values = variable.series[:]
                    self.minimum = min(numpy.min(values), self.minimum)
                    self.maximum = max(numpy.max(values), self.maximum)
        else:
            self.minimum = None
            self.maximum = None

    def newselections(self, selections):
        self.selections = selections
        self.getminmax()
        if self.selections:
            self.values = [self.minimum, self.maximum]
            self.hexcolors = ['#4263ff', '#ff4246']
            self.hexcolor2rgbcolor()
            self.draw()
        else:
            self.delete('all')
            self.values = []
            self.hexcolors = []

    def hexcolor2rgbcolor(self):
        self.rgbcolors = numpy.empty((len(self.hexcolors), 3))
        for (i, hexcolor) in enumerate(self.hexcolors):
            for j in range(3):
                self.rgbcolors[i, j] = int(hexcolor[1+2*j:1+2*(j+1)], 16)

    def draw(self):
        nidxs = 10
        self.delete('all')
        width = float(self['width'])
        height = float(self['height'])
        for idx in range(nidxs):
            xy1 = (0, (nidxs-idx-1)/nidxs*(height-20)+10)
            xy2 = (width/4., (nidxs-idx)/nidxs*(height-20)+10)
            relvalue = (idx+.5)/nidxs
            absvalue = self.minimum + relvalue*(self.maximum-self.minimum)
            hexcolor = self.value2hexcolor(absvalue)
            self.create_rectangle(xy1, xy2, fill=hexcolor, width=0)
        for value in self.values:
            relvalue = (value-self.minimum) / (self.maximum-self.minimum)
            valuestr = '%.1e' % value
            valuestr = valuestr.replace('+0', '+')
            valuestr = valuestr.replace('-0', '-')
            self.create_text(width/4.+5, (1.-relvalue)*(height-20)+10,
                             text=valuestr, anchor=tkinter.W)

    def value2hexcolor(self, value):
        rgbcolor = numpy.empty(3)
        for j in range(3):
            rgbcolor[j] = numpy.interp(value, self.values,
                                       self.rgbcolors[:, j])
        hexcolor = '#%02x%02x%02x' % tuple(int(c) for c in rgbcolor)
        return hexcolor


class Colors(tkinter.Frame):

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.entry = tkinter.Entry(self)
        self.entry.grid(row=0, column=0)
        self.listbox = ColorListbox(self)
        self.listbox.grid(row=1, columnspan=2)
        self.button = tkinter.Button(self, text='recolor')
        self.button.grid(row=0, column=1)
        self.button.bind('<Double-Button-1>', self.recolor)

    def recolor(self, event):
        value = float(self.entry.get())
        for idx in range(self.listbox.size()):
            nextvalue = float(self.listbox.get(idx))
            if value == nextvalue:
                self.listbox.delete(idx)
                return
            elif value < nextvalue:
                self.listbox.insert(idx, value)
                self.listbox.itemconfig(idx, bg='#ffffff')
                return
        self.listbox.insert(tkinter.END, value)
        self.listbox.itemconfig(tkinter.END, bg='#ffffff')
        self.master.master.map.recolor()


class ColorListbox(tkinter.Listbox):

    def __init__(self, master):
        tkinter.Listbox.__init__(self, master)
        for (value, color) in zip(getminmax(None), ['#4263ff', '#ff4246']):
            self.insert(tkinter.END, str(float(value)))
            self.itemconfig(tkinter.END, bg=color)
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        selidx = int(self.curselection()[0])
        color = self.itemcget(selidx, 'bg')
        color = tkColorChooser.askcolor(color)[1]
        self.itemconfig(selidx, bg=color)
