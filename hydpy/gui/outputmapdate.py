
# import...
# ...from standard library
from __future__ import division, print_function
import tkinter
import copy
# ...from HydPy
import hydpy


class Date(tkinter.Frame):

    def __init__(self, menu, hp):
        tkinter.Frame.__init__(self, menu)
        self.menu = menu
        self.hp = hp
        self.deltaidx = 1
        self.timegrid = copy.deepcopy(hydpy.pub.timegrids.sim)
        self.timegrid.lastdate = self.timegrid.firstdate+self.timegrid.stepsize
        self.show = Show(self)
        self.show.pack(side=tkinter.TOP)
        self.change = Change(self)
        self.change.pack(side=tkinter.TOP)

    def stepbackwards(self, event):
        newfirstdate = self.timegrid.firstdate - hydpy.pub.timegrids.stepsize
        if newfirstdate >= hydpy.pub.timegrids.sim.firstdate:
            self.timegrid.firstdate = newfirstdate
            self.timegrid.lastdate -= hydpy.pub.timegrids.stepsize
            self.show.update()
            self.menu.main.map.recolor(
                    hydpy.pub.timegrids.init[self.timegrid.firstdate])

    def stepforwards(self, event):
        newlastdate = self.timegrid.lastdate + hydpy.pub.timegrids.stepsize
        if newlastdate <= hydpy.pub.timegrids.sim.lastdate:
            self.timegrid.lastdate = newlastdate
            self.timegrid.firstdate += hydpy.pub.timegrids.stepsize
            self.show.update()
            self.menu.main.map.recolor(
                    hydpy.pub.timegrids.init[self.timegrid.firstdate])


class Show(tkinter.Label):

    def __init__(self, master):
        tkinter.Label.__init__(self, master)
        self.labelformat = 'start date: %s\n  end date: %s'
        self.update()
        self.bind('<Double-Button-1>', self.modify)

    def update(self):
        self.configure(text=self.labelformat % (self.master.timegrid.firstdate,
                                                self.master.timegrid.lastdate))

    def modify(self, event):
        mod = Modifier(self)
        mod.wait_window(mod)
        self.update()


class Modifier(tkinter.Toplevel):

    def __init__(self, master):
        tkinter.Toplevel.__init__(self, master)
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        label = tkinter.Label(self, text='\n'.join('year'))
        label.pack(side=tkinter.LEFT)
        self.yearlistbox = tkinter.Listbox(self, width=4)
        self.yearlistbox.pack(side=tkinter.LEFT)
        self.yearlistbox.bind('<Double-Button-1>', self.selectyear)
        label = tkinter.Label(self, text='\n'.join('month'))
        label.pack(side=tkinter.LEFT)
        self.monthlistbox = tkinter.Listbox(self, width=4)
        self.monthlistbox.pack(side=tkinter.LEFT)
        self.monthlistbox.bind('<Double-Button-1>', self.selectmonth)
        label = tkinter.Label(self, text='\n'.join('day'))
        label.pack(side=tkinter.LEFT)
        self.daylistbox = tkinter.Listbox(self, width=4)
        self.daylistbox.pack(side=tkinter.LEFT)
        self.daylistbox.bind('<Double-Button-1>', self.selectday)
        label = tkinter.Label(self, text='\n'.join('hour'))
        label.pack(side=tkinter.LEFT)
        self.hourlistbox = tkinter.Listbox(self, width=4)
        self.hourlistbox.pack(side=tkinter.LEFT)
        self.hourlistbox.bind('<Double-Button-1>', self.selecthour)
        label = tkinter.Label(self, text='\n'.join('minute'))
        label.pack(side=tkinter.LEFT)
        self.minutelistbox = tkinter.Listbox(self, width=4)
        self.minutelistbox.pack(side=tkinter.LEFT)
        self.minutelistbox.bind('<Double-Button-1>', self.selectminute)
        self.updateyear()

    def updateyear(self):
        self.yearlistbox.delete(0, tkinter.END)
        years = set(date.year for date in hydpy.pub.timegrids.sim)
        for year in years:
            self.yearlistbox.insert(tkinter.END, str(year))

    def selectyear(self, event):
        idx = int(self.yearlistbox.curselection()[0])
        self.year = int(self.yearlistbox.get(idx))
        self.updatemonth()

    def updatemonth(self):
        self.monthlistbox.delete(0, tkinter.END)
        months = set(date.month for date in hydpy.pub.timegrids.sim
                     if date.year == self.year)
        for month in months:
            self.monthlistbox.insert(tkinter.END, str(month))

    def selectmonth(self, event):
        idx = int(self.monthlistbox.curselection()[0])
        self.month = int(self.monthlistbox.get(idx))
        self.updateday()

    def updateday(self):
        self.daylistbox.delete(0, tkinter.END)
        days = set(date.day for date in hydpy.pub.timegrids.sim
                   if (date.year == self.year and
                       date.month == self.month))
        for day in days:
            self.daylistbox.insert(tkinter.END, str(day))

    def selectday(self, event):
        idx = int(self.daylistbox.curselection()[0])
        self.day = int(self.daylistbox.get(idx))
        self.updatehour()

    def updatehour(self):
        self.hourlistbox.delete(0, tkinter.END)
        hours = set(date.hour for date in hydpy.pub.timegrids.sim
                    if (date.year == self.year and
                        date.month == self.month and
                        date.day == self.day))
        for hour in hours:
            self.hourlistbox.insert(tkinter.END, str(hour))

    def selecthour(self, event):
        idx = int(self.hourlistbox.curselection()[0])
        self.hour = int(self.hourlistbox.get(idx))
        self.updateminute()

    def updateminute(self):
        self.minutelistbox.delete(0, tkinter.END)
        minutes = set(date.minute for date in hydpy.pub.timegrids.sim
                      if (date.year == self.year and
                          date.month == self.month and
                          date.day == self.day and
                          date.hour == self.hour))
        for minute in minutes:
            self.minutelistbox.insert(tkinter.END, str(minute))

    def selectminute(self, event):
        idx = int(self.minutelistbox.curselection()[0])
        self.minute = int(self.minutelistbox.get(idx))
        firstdate = self.master.master.timegrid.firstdate
        firstdate.year = self.year
        firstdate.month = self.month
        firstdate.day = self.day
        firstdate.hour = self.hour
        firstdate.minute = self.minute
        self.master.master.timegrid.lastdate = (
                firstdate + self.master.master.timegrid.stepsize)


class Change(tkinter.Frame):

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.backwardbutton = tkinter.Button(self, text='-')
        self.backwardbutton.pack(side=tkinter.LEFT)
        self.backwardbutton.bind('<Double-Button-1>',
                                 self.master.stepbackwards)
        self.forwardbutton = tkinter.Button(self, text='+')
        self.forwardbutton.pack(side=tkinter.RIGHT)
        self.forwardbutton.bind('<Double-Button-1>',
                                self.master.stepforwards)
