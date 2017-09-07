# -*- coding: utf-8 -*-

import tkinter
import numpy


class TypeDescriptor(object):
    """Descriptor for..."""

    def __init__(self, value):
        self.value = value

    def __get__(self, obj, type_=None):
        return self.value

    def __set__(self, obj, value):
        try:
            self.value = self.TYPE(value)
        except BaseException:
            raise TypeError(
                'The input `%s` is not valid.  %s' % (value, self.TEXT))


class Int(TypeDescriptor):
    TYPE = int
    TEXT = 'Please insert a whole number.'


class Float(TypeDescriptor):
    TYPE = float
    TEXT = 'Please insert a number.'


class Settings(object):

    nmb_rows = Int(1)
    nmb_columns = Int(1)
    width_submap = Float(500)
    heigth_submap = Float(500)


class NumberEntry(tkinter.Entry):
    """A base class for tkinter entries restricted to numbers."""

    def __init__(self, master, dtype, **kwargs):
        self.dtype = dtype
        self.minvalue = kwargs.pop('minvalue', -numpy.inf)
        self.maxvalue = kwargs.pop('maxvalue', numpy.inf)
        tkinter.Entry.__init__(
                self, master, **kwargs, validate='key',
                validatecommand=(master.register(self.validate), '%P'))

    def validate(self, P):
        try:
            value = self.dtype(P)
        except BaseException:
            self.bell()
            return False
        if self.minvalue <= value <= self.maxvalue:
            return True
        else:
            self.bell()
            return False

    def get(self):
        return self.dtype(tkinter.Entry.get(self))
