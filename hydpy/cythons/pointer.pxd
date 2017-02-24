
cdef class DoubleBase(object):
    pass


cdef class Double(DoubleBase):
    
    cdef double value
    
    
cdef class PDouble(DoubleBase):
    
    cdef double *p_value 


cdef class PPDouble(object):
    
    cdef object ready
    cdef int length
    cdef double **pp_value