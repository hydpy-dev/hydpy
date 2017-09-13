
# import...
# ...from standard library
from __future__ import division, print_function
import tkinter
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.gui import shapetools
from . import selector
from . import colorbar
from . import outputmapdate
from hydpy.gui import selectionbox
from hydpy.gui import settingtools

hydpy = None


class Main(tkinter.Tk):
    """Visualisation of model parameters and time series data in (multiple)
    maps.

    It consists of a menue bar (:class:`Menu`) on top and the map view area
    (:class:`Map`) below.
    """

    def __init__(self, hydpy, width, height):
        tkinter.Tk.__init__(self)
        self.hydpy = hydpy
        self.menu = Menu(self, width, height)
        self.menu.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.map = Map(self, width=width, height=height)
        self.map.pack(side=tkinter.TOP)
        tkinter.mainloop()


class Menu(tkinter.Frame):
    """The single menu on top of the main window."""

    def __init__(self, main, width, height):
        tkinter.Frame.__init__(self, main)
        self.main = main
        self.arrangement = Arrangement(self, width, height)
        self.arrangement.pack(side=tkinter.LEFT)
        self.date = outputmapdate.Date(self, self.master.hydpy)
        self.date.pack(side=tkinter.LEFT)


class Arrangement(tkinter.Frame):
    """Defines the number of :class:`Submap` instances."""

    def __init__(self, menu, width, height):
        tkinter.Frame.__init__(self, menu)
        self.menu = menu
        # Define command and selection buttons.
        self.button = tkinter.Button(self, text='rearrange')
        self.button.grid(row=0, columnspan=4, sticky=tkinter.EW)
        self.button.bind('<Double-Button-1>', self.rearrange)
        # Define entry boxes for the number of rows and columns.
        label = tkinter.Label(self, text='rows:')
        label.grid(row=1, column=0, sticky=tkinter.E)
        self.rowsentry = settingtools.NumberEntry(self, int, minvalue=1,
                                                  width=2)
        self.rowsentry.grid(row=1, column=1)
        label = tkinter.Label(self, text='columns:')
        label.grid(row=2, column=0, sticky=tkinter.E)
        self.columnsentry = settingtools.NumberEntry(self, int,
                                                     minvalue=1, width=2)
        self.columnsentry.grid(row=2, column=1)
        # Define entry boxes for the width and height of each submap.
        label = tkinter.Label(self, text='width:')
        label.grid(row=1, column=2, sticky=tkinter.E)
        self.widthentry = settingtools.NumberEntry(self, float,
                                                   minvalue=1., width=5)
        self.widthentry.grid(row=1, column=3)
        label = tkinter.Label(self, text='height:')
        label.grid(row=2, column=2, sticky=tkinter.E)
        self.heightentry = settingtools.NumberEntry(self, float,
                                                    minvalue=1., width=5)
        self.heightentry.grid(row=2, column=3)

    def rearrange(self, event):
        self.menu.main.map.resize(rows=self.rowsentry.get(),
                                  columns=self.columnsentry.get(),
                                  width=self.widthentry.get(),
                                  height=self.heightentry.get())


class Map(tkinter.Frame):
    """The actual frame for the (muliple) maps of :class:`MainWindow`."""

    def __init__(self, main, width, height):
        tkinter.Frame.__init__(self, main)
        self.main = main
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

    def recolor(self, idx):
        for mapsinrow in self.submaps:
            for submap in mapsinrow:
                submap.recolor(idx)


class Submap(tkinter.Frame):
    """One single map contained in :class:`Map`."""

    def __init__(self, map_, width, height):
        tkinter.Frame.__init__(self, map_, bd=0)
        self.map_ = map_
        self.width = width
        self.height = height
        self.update_selection(pub.selections.complete)

    def recolor(self, idx):
        self.infoarea.recolor()
        self.geoarea.recolor(idx)

    def update_selection(self, selection):
        self.selection = selection
        if hasattr(self, 'geoarea'):
            self.geoarea.destroy()
            self.infoarea.destroy()
        self.geoarea = GeoArea(self, width=self.width, height=self.height)
        self.geoarea.pack(side=tkinter.LEFT)
        self.infoarea = InfoArea(self, width=60, height=self.height)
        self.infoarea.pack(side=tkinter.RIGHT)


class GeoArea(tkinter.Canvas):
    """The plotting area for geo objects within a :class:`SubMap`."""

    def __init__(self, submap, width, height):
        tkinter.Canvas.__init__(self, submap, width=width, height=height)
        self.submap = submap
        for layer in range(1, 4):
            for shape in self.submap.selection.shapes.values():
                points = shape.vertices.copy()
                points[:, 0] = points[:, 0]*(width-10)+5
                points[:, 1] = points[:, 1]*(height-10)+5
                points = list(points.flatten())
                if shape.layer != layer:
                    continue
                elif isinstance(shape, shapetools.Plane):
                    shape.polygon = self.create_polygon(
                            points,  outline='black', width=1, fill='white')
                elif isinstance(shape, shapetools.Line):
                    shape.polygon = self.create_line(
                            points, width=3, fill='blue')
                elif isinstance(shape, shapetools.Point):
                    x1, y1 = points
                    x2, y2 = x1+5., y1+5.
                    shape.polygon = self.create_oval(x1, y1, x2, y2,
                                                     width=1, fill='red')

    def recolor(self, idx):
        for (name, shape) in self.submap.selection.shapes.items():
            #seqname = self.submap.infoarea.colorbar.selections[0].variablesstr[0]
            #seq = getattr(self.submap.selection, name).value = .series[idx]
            if name in self.submap.selection.elements:
                element = self.submap.selection.elements[name]
                descr = self.submap.infoarea.description
                if type(element.model) is type(descr.model):
                    subgroup = getattr(element.model.sequences, descr.subgroup.name)
                    variable = getattr(subgroup, descr.variable.name)
                    value = variable.series[idx]
                    color = self.submap.infoarea.colorbar.value2hexcolor(value)
                    self.itemconfig(shape.polygon, fill=color)


class InfoArea(tkinter.Frame):
    """Area reserved for additional information within a :class:`SubMap`."""

    def __init__(self, submap, width, height):
        tkinter.Frame.__init__(self, submap, width=width, height=height)
        self.submap = submap
        self.selection = Selection(self)
        self.selection.pack(side=tkinter.TOP)
        self.description = Description(self)
        self.description.pack(side=tkinter.TOP)
        self.colorbar = colorbar.Colorbar(self, width=width, height=height-70,
                                          selections=self.master.selections)
        self.colorbar.pack(side=tkinter.BOTTOM)

    def recolor(self):
        pass
        # self.colorbar.recolor()


class Description(tkinter.Label):
    """Description for a single :class:`SubMap`."""

    def __init__(self, infoarea):
        tkinter.Label.__init__(self, infoarea, text='None')
        self.infoarea = infoarea
        self.master.master.selections = []
        self.variable = None
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        sel = selector.Selector(self.infoarea.submap.selections,
                                self.infoarea.submap.map_.master.main.hydpy)
        self.wait_window(sel)
        varnames = []
        for selection in self.master.master.selections:
            if selection.variablestr not in varnames:
                varnames.append(selection.variablestr)
        if varnames:
            self.configure(text='\n'.join(varnames))
        else:
            self.configure(text='None')
        self.infoarea.colorbar.newselections(self.infoarea.submap.selections)
        self.model = list(sel.resultlistbox.models.values())[0]
        self.group = list(sel.resultlistbox.groups.values())[0]
        self.subgroup = list(sel.resultlistbox.subgroups.values())[0]
        self.variable = list(sel.resultlistbox.variables.values())[0]



class Selection(tkinter.Label):
    """Description for a single :class:`SubMap`."""

    def __init__(self, infoarea):
        tkinter.Label.__init__(self, infoarea,
                               text=infoarea.submap.selection.name)
        self.infoarea = infoarea
        self.bind('<Double-Button-1>', self.select_selection)

    def select_selection(self, event):
        sel = selectionbox.SelectionBox(self)
        self.wait_window(sel)
