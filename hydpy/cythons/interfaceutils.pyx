# -*- coding: utf-8 -*-


cdef class BaseInterface:

    cdef void load_data(self) nogil:
        pass

    cdef void save_data(self, int idx) nogil:
        pass
