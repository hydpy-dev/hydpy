
# import...
# ...from standard library
from __future__ import division, print_function
import tkinter
# ...from HydPy
from ..framework import pub


class Modifier(tkinter.Toplevel):

    def __init__(self, master):
        tkinter.Toplevel.__init__(self, master)
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.alldates = self.getdates()
        self.seldates = None
        self.yearlistbox = tkinter.Listbox(self)
        self.yearlistbox.pack(side=tkinter.LEFT)
        self.yearlistbox.bind('<Double-Button-1>', self.selectyear)
        self.monthlistbox = tkinter.Listbox(self)
        self.monthlistbox.pack(side=tkinter.LEFT)
        self.updateyear()

    def getdates(self):
        dates = []
        date = pub.date_startsim
        while date < pub.date_endsim:
            dates.append(date)
            date += self.master.master.deltadate
        return dates

    def updateyear(self):
        self.yearlistbox.delete(0, tkinter.END)
        years = sorted(set(date.year for date in self.alldates))
        for year in years:
            self.yearlistbox.insert(tkinter.END, str(year))

    def selectyear(self):
        idx = int(self.yearlistbox.curselection(0))
        self.year = int(self.yearlistbox.get(idx))
        self.seldates = [date for date in self.alldates
                         if date.year == self.year]
        self.monthlistbox.update()

    def updatemonth(self):
        self.monthlistbox.delete(0, tkinter.END)
        months = sorted(set(date.month for date in self.seldates))
        for month in months:
            self.monthlistbox.insert(tkinter.END, str(month))
