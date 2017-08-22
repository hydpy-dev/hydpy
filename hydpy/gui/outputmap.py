
# import...
# ...from standard library
from __future__ import division, print_function
import os
import tkinter
# ...from site-packages
import numpy
# ...from HydPy
from . import selector
from . import colorbar
from . import outputmapdate

hydpy = None


class OutputMap(tkinter.Tk):
    """Visualisation of model parameters and time series in (multiple) maps."""

    def __init__(self):
        tkinter.Tk.__init__(self)
        self.loadshapes()
        self.menu = Menu(self)
        self.menu.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.map = Map(self, width=200, height=200)
        self.map.pack(side=tkinter.TOP)
        tkinter.mainloop()

    def loadshapes(self):
        shapedir = os.path.join('shapes', 'große_röder')

        xmin, ymin = numpy.inf, numpy.inf
        xmax, ymax = -numpy.inf, -numpy.inf
        for (name, element) in hydpy.elements:
            shapepath = os.path.join(shapedir, '%s.npy' % name)
            shape = numpy.load(shapepath)
            xmin = min(xmin, numpy.min(shape[:, 0]))
            xmax = max(xmax, numpy.max(shape[:, 0]))
            ymin = min(ymin, numpy.min(shape[:, 1]))
            ymax = max(ymax, numpy.max(shape[:, 1]))
            element.temp = {'points': shape}

        for (name, element) in hydpy.elements:
            shape = element.temp['points'].copy()
            shape[:, 0] = (shape[:, 0]-xmin)/(xmax-xmin)
            shape[:, 1] = (ymax-shape[:, 1])/(ymax-ymin)
            element.temp['normpoints'] = shape


class Menu(tkinter.Frame):
    """The single menu of :class:`OutputMap`."""

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.arrangement = Arrangement(self)
        self.arrangement.pack(side=tkinter.LEFT)
        self.date = outputmapdate.Date(self, hydpy)
        self.date.pack(side=tkinter.LEFT)


class Arrangement(tkinter.Frame):
    """Defines the number of :class:`Submap` instances."""

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        # Define command and selection buttons.
        self.button = tkinter.Button(self, text='rearrange')
        self.button.grid(row=0, columnspan=4, sticky=tkinter.EW)
        self.button.bind('<Double-Button-1>', self.rearrange)
        # Define entry boxes for the number of rows and columns.
        label = tkinter.Label(self, text='rows:')
        label.grid(row=1, column=0, sticky=tkinter.E)
        self.rowsentry = IntEntry(self, width=1)
        self.rowsentry.grid(row=1, column=1)
        label = tkinter.Label(self, text='columns:')
        label.grid(row=2, column=0, sticky=tkinter.E)
        self.columnsentry = IntEntry(self, width=1)
        self.columnsentry.grid(row=2, column=1)
        # Define entry boxes for the width and height of each submap.
        label = tkinter.Label(self, text='width:')
        label.grid(row=1, column=2, sticky=tkinter.E)
        self.widthentry = IntEntry(self, width=4)
        self.widthentry.grid(row=1, column=3)
        label = tkinter.Label(self, text='height:')
        label.grid(row=2, column=2, sticky=tkinter.E)
        self.heightentry = IntEntry(self, width=4)
        self.heightentry.grid(row=2, column=3)

    def rearrange(self, event):
        self.master.master.map.resize(rows=self.rowsentry.getint(),
                                      columns=self.columnsentry.getint(),
                                      width=self.widthentry.getint(),
                                      height=self.heightentry.getint())


class IntEntry(tkinter.Entry):
    """Defines the number of :class:`Submap` instances in one dimension."""

    def getint(self):
        try:
            return int(self.get())
        except ValueError:
            return 1


class Map(tkinter.Frame):
    """The actual frame for the (muliple) maps of :class:`OutputMap`."""

    def __init__(self, master, width, height):
        tkinter.Frame.__init__(self, master)
        self.shape = (1, 1)
        self.submaps = None
        self.frames = None
        self.drawsubmaps(width=width, height=height)

    def drawsubmaps(self, width, height):
        self.submaps = numpy.empty(self.shape, dtype=object)
        self.frames = []
        for idx in range(self.shape[0]):
            frame = tkinter.Frame(self)
            frame.pack(side=tkinter.TOP)
            self.frames.append(frame)
            for jdx in range(self.shape[1]):
                submap = Submap(frame, width=width, height=height)
                submap.pack(side=tkinter.LEFT)
                self.submaps[idx, jdx] = submap

    def resize(self, rows, columns, width, height):
        for frame in self.frames:
            frame.destroy()
        self.shape = (rows, columns)
        self.drawsubmaps(width=width, height=height)

    def recolor(self):
        for mapsinrow in self.submaps:
            for submap in mapsinrow:
                submap.recolor()


class Submap(tkinter.Frame):
    """One single map contained in :class:`Map`."""

    def __init__(self, master, width, height):
        tkinter.Frame.__init__(self, master, bd=0)
        self.selections = []
        self.geoarea = GeoArea(self, width=width, height=height)
        self.geoarea.pack(side=tkinter.LEFT)
        self.infoarea = InfoArea(self, width=60, height=height)
        self.infoarea.pack(side=tkinter.RIGHT)

    def recolor(self):
        self.infoarea.recolor()
        self.geoarea.recolor()


class GeoArea(tkinter.Canvas):
    """The plotting area for geo objects within a :class:`SubMap`."""

    def __init__(self, master, width, height):
        tkinter.Canvas.__init__(self, master, width=width, height=height)
        for (name, element) in hydpy.elements:
            if hasattr(element, 'temp'):
                points = element.temp['normpoints'].copy()
                points[:, 0] = points[:, 0]*(width-10)+5
                points[:, 1] = points[:, 1]*(height-10)+5
                points = list(points.flatten())
                element.temp['polygon'] = self.create_polygon(points,
                                                              outline='black',
                                                              width=1,
                                                              fill='white')

    def recolor(self):
        for (name, element) in hydpy.elements:
            if hasattr(element, 'temp'):
                self.itemconfig(element.temp['polygon'], fill='blue')


class InfoArea(tkinter.Frame):
    """Area reserved for additional information within a :class:`SubMap`."""

    def __init__(self, master, width, height):
        tkinter.Frame.__init__(self, master, width=width, height=height)
        self.description = Description(self)
        self.description.pack(side=tkinter.TOP)
        self.colorbar = colorbar.Colorbar(self, width=width, height=height-70,
                                          selections=self.master.selections)
        self.colorbar.pack(side=tkinter.BOTTOM)

    def recolor(self):
        self.colorbar.recolor()


class Description(tkinter.Label):
    """Description for a single :class:`SubMap`."""

    def __init__(self, master):
        tkinter.Label.__init__(self, master, text='None')
        self.master.master.selections = []
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        sel = selector.Selector(self.master.master.selections, hydpy)
        self.wait_window(sel)
        varnames = []
        for selection in self.master.master.selections:
            if selection.variablestr not in varnames:
                varnames.append(selection.variablestr)
        if varnames:
            self.configure(text='\n'.join(varnames))
        else:
            self.configure(text='None')
        self.master.colorbar.newselections(self.master.master.selections)
