#!python
#cython: boundscheck=False
#cython: wraparound=False
#cython: initializedcheck=False
import numpy
cimport numpy
from libc.math cimport exp
from libc.stdio cimport *
from libc.stdlib cimport *
import cython
from cpython.mem cimport PyMem_Malloc
from cpython.mem cimport PyMem_Realloc
from cpython.mem cimport PyMem_Free
from hydpy.cythons cimport pointer
from hydpy.cythons import pointer
cdef public numpy.int32_t FOREST = 2
cdef public numpy.int32_t GLACIER = 3
cdef public numpy.int32_t FIELD = 1
cdef public numpy.int32_t ILAKE = 4
@cython.final
cdef class ControlParameters(object):
    cdef public double area
    cdef public numpy.int32_t nmbzones
    cdef public numpy.int32_t[:] zonetype
    cdef public double[:] zonearea
    cdef public double[:] zonez
    cdef public double zrelp
    cdef public double zrelt
    cdef public double zrele
    cdef public double[:] pcorr
    cdef public double[:] pcalt
    cdef public double[:] rfcf
    cdef public double[:] sfcf
    cdef public double[:] tcalt
    cdef public double[:] ecorr
    cdef public double[:] ecalt
    cdef public double[:] epf
    cdef public double[:] etf
    cdef public double[:] ered
    cdef public double[:] ttice
    cdef public double[:] icmax
    cdef public double[:] tt
    cdef public double[:] ttint
    cdef public double[:] dttm
    cdef public double[:] cfmax
    cdef public double[:] gmelt
    cdef public double[:] cfr
    cdef public double[:] whc
    cdef public double[:] fc
    cdef public double[:] lp
    cdef public double[:] beta
    cdef public double percmax
    cdef public double[:] cflux
    cdef public bint resparea
    cdef public numpy.int32_t recstep
    cdef public double alpha
    cdef public double k
    cdef public double k4
    cdef public double gamma
    cdef public double maxbaz
    cdef public double abstr
@cython.final
cdef class DerivedParameters(object):
    cdef public double[:] relzonearea
    cdef public double relsoilarea
    cdef public double[:] relsoilzonearea
    cdef public double[:] rellandzonearea
    cdef public double rellandarea
    cdef public double[:] ttm
    cdef public double dt
    cdef public numpy.int32_t nmbuh
    cdef public double[:] uh
    cdef public double qfactor
@cython.final
cdef class InputSequences(object):
    cdef public double p
    cdef public int _p_ndim
    cdef public int _p_length
    cdef public bint _p_diskflag
    cdef public str _p_path
    cdef FILE *_p_file
    cdef public bint _p_ramflag
    cdef public double[:] _p_array
    cdef public double t
    cdef public int _t_ndim
    cdef public int _t_length
    cdef public bint _t_diskflag
    cdef public str _t_path
    cdef FILE *_t_file
    cdef public bint _t_ramflag
    cdef public double[:] _t_array
    cdef public double tn
    cdef public int _tn_ndim
    cdef public int _tn_length
    cdef public bint _tn_diskflag
    cdef public str _tn_path
    cdef FILE *_tn_file
    cdef public bint _tn_ramflag
    cdef public double[:] _tn_array
    cdef public double epn
    cdef public int _epn_ndim
    cdef public int _epn_length
    cdef public bint _epn_diskflag
    cdef public str _epn_path
    cdef FILE *_epn_file
    cdef public bint _epn_ramflag
    cdef public double[:] _epn_array
    cpdef inline loaddata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._p_diskflag:
            fread(&self.p, 8, 1, self._p_file)
        elif self._p_ramflag:
            self.p = self._p_array[idx]
        if self._t_diskflag:
            fread(&self.t, 8, 1, self._t_file)
        elif self._t_ramflag:
            self.t = self._t_array[idx]
        if self._tn_diskflag:
            fread(&self.tn, 8, 1, self._tn_file)
        elif self._tn_ramflag:
            self.tn = self._tn_array[idx]
        if self._epn_diskflag:
            fread(&self.epn, 8, 1, self._epn_file)
        elif self._epn_ramflag:
            self.epn = self._epn_array[idx]
    cpdef openfiles(self, int idx):
        if self._p_diskflag:
            self._p_file = fopen(str(self._p_path), "rb+")
            fseek(self._p_file, idx*8, SEEK_SET)
        if self._t_diskflag:
            self._t_file = fopen(str(self._t_path), "rb+")
            fseek(self._t_file, idx*8, SEEK_SET)
        if self._tn_diskflag:
            self._tn_file = fopen(str(self._tn_path), "rb+")
            fseek(self._tn_file, idx*8, SEEK_SET)
        if self._epn_diskflag:
            self._epn_file = fopen(str(self._epn_path), "rb+")
            fseek(self._epn_file, idx*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._epn_diskflag:
            fclose(self._epn_file)
        if self._p_diskflag:
            fclose(self._p_file)
        if self._t_diskflag:
            fclose(self._t_file)
        if self._tn_diskflag:
            fclose(self._tn_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._p_diskflag:
            fwrite(&self.p, 8, 1, self._p_file)
        elif self._p_ramflag:
            self._p_array[idx] = self.p
        if self._t_diskflag:
            fwrite(&self.t, 8, 1, self._t_file)
        elif self._t_ramflag:
            self._t_array[idx] = self.t
        if self._tn_diskflag:
            fwrite(&self.tn, 8, 1, self._tn_file)
        elif self._tn_ramflag:
            self._tn_array[idx] = self.tn
        if self._epn_diskflag:
            fwrite(&self.epn, 8, 1, self._epn_file)
        elif self._epn_ramflag:
            self._epn_array[idx] = self.epn
@cython.final
cdef class LogSequences(object):
    cdef public double[:] quh
    cdef public int _quh_ndim
    cdef public int _quh_length
    cdef public int _quh_length_0
@cython.final
cdef class OutletSequences(object):
    cdef double *q
    cdef public int _q_ndim
    cdef public int _q_length
    cpdef inline setpointer0d(self, str name, pointer.PDouble value):
        if name == "q":
            self.q = value.p_value
@cython.final
cdef class StateSequences(object):
    cdef public double[:] ic
    cdef public int _ic_ndim
    cdef public int _ic_length
    cdef public int _ic_length_0
    cdef public bint _ic_diskflag
    cdef public str _ic_path
    cdef FILE *_ic_file
    cdef public bint _ic_ramflag
    cdef public double[:,:] _ic_array
    cdef public double[:] sp
    cdef public int _sp_ndim
    cdef public int _sp_length
    cdef public int _sp_length_0
    cdef public bint _sp_diskflag
    cdef public str _sp_path
    cdef FILE *_sp_file
    cdef public bint _sp_ramflag
    cdef public double[:,:] _sp_array
    cdef public double[:] wc
    cdef public int _wc_ndim
    cdef public int _wc_length
    cdef public int _wc_length_0
    cdef public bint _wc_diskflag
    cdef public str _wc_path
    cdef FILE *_wc_file
    cdef public bint _wc_ramflag
    cdef public double[:,:] _wc_array
    cdef public double[:] sm
    cdef public int _sm_ndim
    cdef public int _sm_length
    cdef public int _sm_length_0
    cdef public bint _sm_diskflag
    cdef public str _sm_path
    cdef FILE *_sm_file
    cdef public bint _sm_ramflag
    cdef public double[:,:] _sm_array
    cdef public double uz
    cdef public int _uz_ndim
    cdef public int _uz_length
    cdef public bint _uz_diskflag
    cdef public str _uz_path
    cdef FILE *_uz_file
    cdef public bint _uz_ramflag
    cdef public double[:] _uz_array
    cdef public double lz
    cdef public int _lz_ndim
    cdef public int _lz_length
    cdef public bint _lz_diskflag
    cdef public str _lz_path
    cdef FILE *_lz_file
    cdef public bint _lz_ramflag
    cdef public double[:] _lz_array
    cpdef openfiles(self, int idx):
        if self._ic_diskflag:
            self._ic_file = fopen(str(self._ic_path), "rb+")
            fseek(self._ic_file, idx*self._ic_length*8, SEEK_SET)
        if self._sp_diskflag:
            self._sp_file = fopen(str(self._sp_path), "rb+")
            fseek(self._sp_file, idx*self._sp_length*8, SEEK_SET)
        if self._wc_diskflag:
            self._wc_file = fopen(str(self._wc_path), "rb+")
            fseek(self._wc_file, idx*self._wc_length*8, SEEK_SET)
        if self._sm_diskflag:
            self._sm_file = fopen(str(self._sm_path), "rb+")
            fseek(self._sm_file, idx*self._sm_length*8, SEEK_SET)
        if self._uz_diskflag:
            self._uz_file = fopen(str(self._uz_path), "rb+")
            fseek(self._uz_file, idx*8, SEEK_SET)
        if self._lz_diskflag:
            self._lz_file = fopen(str(self._lz_path), "rb+")
            fseek(self._lz_file, idx*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._ic_diskflag:
            fclose(self._ic_file)
        if self._lz_diskflag:
            fclose(self._lz_file)
        if self._sm_diskflag:
            fclose(self._sm_file)
        if self._sp_diskflag:
            fclose(self._sp_file)
        if self._uz_diskflag:
            fclose(self._uz_file)
        if self._wc_diskflag:
            fclose(self._wc_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._ic_diskflag:
            fwrite(&self.ic[0], 8, self._ic_length, self._ic_file)
        elif self._ic_ramflag:
            for jdx0 in range(self._ic_length_0):
                self._ic_array[idx,jdx0] = self.ic[jdx0]
        if self._sp_diskflag:
            fwrite(&self.sp[0], 8, self._sp_length, self._sp_file)
        elif self._sp_ramflag:
            for jdx0 in range(self._sp_length_0):
                self._sp_array[idx,jdx0] = self.sp[jdx0]
        if self._wc_diskflag:
            fwrite(&self.wc[0], 8, self._wc_length, self._wc_file)
        elif self._wc_ramflag:
            for jdx0 in range(self._wc_length_0):
                self._wc_array[idx,jdx0] = self.wc[jdx0]
        if self._sm_diskflag:
            fwrite(&self.sm[0], 8, self._sm_length, self._sm_file)
        elif self._sm_ramflag:
            for jdx0 in range(self._sm_length_0):
                self._sm_array[idx,jdx0] = self.sm[jdx0]
        if self._uz_diskflag:
            fwrite(&self.uz, 8, 1, self._uz_file)
        elif self._uz_ramflag:
            self._uz_array[idx] = self.uz
        if self._lz_diskflag:
            fwrite(&self.lz, 8, 1, self._lz_file)
        elif self._lz_ramflag:
            self._lz_array[idx] = self.lz
@cython.final
cdef class AideSequences(object):
    cdef public double perc
    cdef public int _perc_ndim
    cdef public int _perc_length
    cdef public double q0
    cdef public int _q0_ndim
    cdef public int _q0_length
@cython.final
cdef class FluxSequences(object):
    cdef public double tmean
    cdef public int _tmean_ndim
    cdef public int _tmean_length
    cdef public bint _tmean_diskflag
    cdef public str _tmean_path
    cdef FILE *_tmean_file
    cdef public bint _tmean_ramflag
    cdef public double[:] _tmean_array
    cdef public double[:] tc
    cdef public int _tc_ndim
    cdef public int _tc_length
    cdef public int _tc_length_0
    cdef public bint _tc_diskflag
    cdef public str _tc_path
    cdef FILE *_tc_file
    cdef public bint _tc_ramflag
    cdef public double[:,:] _tc_array
    cdef public double[:] fracrain
    cdef public int _fracrain_ndim
    cdef public int _fracrain_length
    cdef public int _fracrain_length_0
    cdef public bint _fracrain_diskflag
    cdef public str _fracrain_path
    cdef FILE *_fracrain_file
    cdef public bint _fracrain_ramflag
    cdef public double[:,:] _fracrain_array
    cdef public double[:] rfc
    cdef public int _rfc_ndim
    cdef public int _rfc_length
    cdef public int _rfc_length_0
    cdef public bint _rfc_diskflag
    cdef public str _rfc_path
    cdef FILE *_rfc_file
    cdef public bint _rfc_ramflag
    cdef public double[:,:] _rfc_array
    cdef public double[:] sfc
    cdef public int _sfc_ndim
    cdef public int _sfc_length
    cdef public int _sfc_length_0
    cdef public bint _sfc_diskflag
    cdef public str _sfc_path
    cdef FILE *_sfc_file
    cdef public bint _sfc_ramflag
    cdef public double[:,:] _sfc_array
    cdef public double[:] pc
    cdef public int _pc_ndim
    cdef public int _pc_length
    cdef public int _pc_length_0
    cdef public bint _pc_diskflag
    cdef public str _pc_path
    cdef FILE *_pc_file
    cdef public bint _pc_ramflag
    cdef public double[:,:] _pc_array
    cdef public double[:] ep
    cdef public int _ep_ndim
    cdef public int _ep_length
    cdef public int _ep_length_0
    cdef public bint _ep_diskflag
    cdef public str _ep_path
    cdef FILE *_ep_file
    cdef public bint _ep_ramflag
    cdef public double[:,:] _ep_array
    cdef public double[:] epc
    cdef public int _epc_ndim
    cdef public int _epc_length
    cdef public int _epc_length_0
    cdef public bint _epc_diskflag
    cdef public str _epc_path
    cdef FILE *_epc_file
    cdef public bint _epc_ramflag
    cdef public double[:,:] _epc_array
    cdef public double[:] ei
    cdef public int _ei_ndim
    cdef public int _ei_length
    cdef public int _ei_length_0
    cdef public bint _ei_diskflag
    cdef public str _ei_path
    cdef FILE *_ei_file
    cdef public bint _ei_ramflag
    cdef public double[:,:] _ei_array
    cdef public double[:] tf
    cdef public int _tf_ndim
    cdef public int _tf_length
    cdef public int _tf_length_0
    cdef public bint _tf_diskflag
    cdef public str _tf_path
    cdef FILE *_tf_file
    cdef public bint _tf_ramflag
    cdef public double[:,:] _tf_array
    cdef public double[:] tfwat
    cdef public int _tfwat_ndim
    cdef public int _tfwat_length
    cdef public int _tfwat_length_0
    cdef public bint _tfwat_diskflag
    cdef public str _tfwat_path
    cdef FILE *_tfwat_file
    cdef public bint _tfwat_ramflag
    cdef public double[:,:] _tfwat_array
    cdef public double[:] tfice
    cdef public int _tfice_ndim
    cdef public int _tfice_length
    cdef public int _tfice_length_0
    cdef public bint _tfice_diskflag
    cdef public str _tfice_path
    cdef FILE *_tfice_file
    cdef public bint _tfice_ramflag
    cdef public double[:,:] _tfice_array
    cdef public double[:] glmelt
    cdef public int _glmelt_ndim
    cdef public int _glmelt_length
    cdef public int _glmelt_length_0
    cdef public bint _glmelt_diskflag
    cdef public str _glmelt_path
    cdef FILE *_glmelt_file
    cdef public bint _glmelt_ramflag
    cdef public double[:,:] _glmelt_array
    cdef public double[:] meltpot
    cdef public int _meltpot_ndim
    cdef public int _meltpot_length
    cdef public int _meltpot_length_0
    cdef public bint _meltpot_diskflag
    cdef public str _meltpot_path
    cdef FILE *_meltpot_file
    cdef public bint _meltpot_ramflag
    cdef public double[:,:] _meltpot_array
    cdef public double[:] melt
    cdef public int _melt_ndim
    cdef public int _melt_length
    cdef public int _melt_length_0
    cdef public bint _melt_diskflag
    cdef public str _melt_path
    cdef FILE *_melt_file
    cdef public bint _melt_ramflag
    cdef public double[:,:] _melt_array
    cdef public double[:] refrpot
    cdef public int _refrpot_ndim
    cdef public int _refrpot_length
    cdef public int _refrpot_length_0
    cdef public bint _refrpot_diskflag
    cdef public str _refrpot_path
    cdef FILE *_refrpot_file
    cdef public bint _refrpot_ramflag
    cdef public double[:,:] _refrpot_array
    cdef public double[:] refr
    cdef public int _refr_ndim
    cdef public int _refr_length
    cdef public int _refr_length_0
    cdef public bint _refr_diskflag
    cdef public str _refr_path
    cdef FILE *_refr_file
    cdef public bint _refr_ramflag
    cdef public double[:,:] _refr_array
    cdef public double[:] in_
    cdef public int _in__ndim
    cdef public int _in__length
    cdef public int _in__length_0
    cdef public bint _in__diskflag
    cdef public str _in__path
    cdef FILE *_in__file
    cdef public bint _in__ramflag
    cdef public double[:,:] _in__array
    cdef public double[:] r
    cdef public int _r_ndim
    cdef public int _r_length
    cdef public int _r_length_0
    cdef public bint _r_diskflag
    cdef public str _r_path
    cdef FILE *_r_file
    cdef public bint _r_ramflag
    cdef public double[:,:] _r_array
    cdef public double[:] ea
    cdef public int _ea_ndim
    cdef public int _ea_length
    cdef public int _ea_length_0
    cdef public bint _ea_diskflag
    cdef public str _ea_path
    cdef FILE *_ea_file
    cdef public bint _ea_ramflag
    cdef public double[:,:] _ea_array
    cdef public double[:] cfpot
    cdef public int _cfpot_ndim
    cdef public int _cfpot_length
    cdef public int _cfpot_length_0
    cdef public bint _cfpot_diskflag
    cdef public str _cfpot_path
    cdef FILE *_cfpot_file
    cdef public bint _cfpot_ramflag
    cdef public double[:,:] _cfpot_array
    cdef public double[:] cf
    cdef public int _cf_ndim
    cdef public int _cf_length
    cdef public int _cf_length_0
    cdef public bint _cf_diskflag
    cdef public str _cf_path
    cdef FILE *_cf_file
    cdef public bint _cf_ramflag
    cdef public double[:,:] _cf_array
    cdef public double perc
    cdef public int _perc_ndim
    cdef public int _perc_length
    cdef public bint _perc_diskflag
    cdef public str _perc_path
    cdef FILE *_perc_file
    cdef public bint _perc_ramflag
    cdef public double[:] _perc_array
    cdef public double contriarea
    cdef public int _contriarea_ndim
    cdef public int _contriarea_length
    cdef public bint _contriarea_diskflag
    cdef public str _contriarea_path
    cdef FILE *_contriarea_file
    cdef public bint _contriarea_ramflag
    cdef public double[:] _contriarea_array
    cdef public double inuz
    cdef public int _inuz_ndim
    cdef public int _inuz_length
    cdef public bint _inuz_diskflag
    cdef public str _inuz_path
    cdef FILE *_inuz_file
    cdef public bint _inuz_ramflag
    cdef public double[:] _inuz_array
    cdef public double q0
    cdef public int _q0_ndim
    cdef public int _q0_length
    cdef public bint _q0_diskflag
    cdef public str _q0_path
    cdef FILE *_q0_file
    cdef public bint _q0_ramflag
    cdef public double[:] _q0_array
    cdef public double[:] el
    cdef public int _el_ndim
    cdef public int _el_length
    cdef public int _el_length_0
    cdef public bint _el_diskflag
    cdef public str _el_path
    cdef FILE *_el_file
    cdef public bint _el_ramflag
    cdef public double[:,:] _el_array
    cdef public double q1
    cdef public int _q1_ndim
    cdef public int _q1_length
    cdef public bint _q1_diskflag
    cdef public str _q1_path
    cdef FILE *_q1_file
    cdef public bint _q1_ramflag
    cdef public double[:] _q1_array
    cdef public double inuh
    cdef public int _inuh_ndim
    cdef public int _inuh_length
    cdef public bint _inuh_diskflag
    cdef public str _inuh_path
    cdef FILE *_inuh_file
    cdef public bint _inuh_ramflag
    cdef public double[:] _inuh_array
    cdef public double outuh
    cdef public int _outuh_ndim
    cdef public int _outuh_length
    cdef public bint _outuh_diskflag
    cdef public str _outuh_path
    cdef FILE *_outuh_file
    cdef public bint _outuh_ramflag
    cdef public double[:] _outuh_array
    cdef public double qt
    cdef public int _qt_ndim
    cdef public int _qt_length
    cdef public bint _qt_diskflag
    cdef public str _qt_path
    cdef FILE *_qt_file
    cdef public bint _qt_ramflag
    cdef public double[:] _qt_array
    cpdef openfiles(self, int idx):
        if self._tmean_diskflag:
            self._tmean_file = fopen(str(self._tmean_path), "rb+")
            fseek(self._tmean_file, idx*8, SEEK_SET)
        if self._tc_diskflag:
            self._tc_file = fopen(str(self._tc_path), "rb+")
            fseek(self._tc_file, idx*self._tc_length*8, SEEK_SET)
        if self._fracrain_diskflag:
            self._fracrain_file = fopen(str(self._fracrain_path), "rb+")
            fseek(self._fracrain_file, idx*self._fracrain_length*8, SEEK_SET)
        if self._rfc_diskflag:
            self._rfc_file = fopen(str(self._rfc_path), "rb+")
            fseek(self._rfc_file, idx*self._rfc_length*8, SEEK_SET)
        if self._sfc_diskflag:
            self._sfc_file = fopen(str(self._sfc_path), "rb+")
            fseek(self._sfc_file, idx*self._sfc_length*8, SEEK_SET)
        if self._pc_diskflag:
            self._pc_file = fopen(str(self._pc_path), "rb+")
            fseek(self._pc_file, idx*self._pc_length*8, SEEK_SET)
        if self._ep_diskflag:
            self._ep_file = fopen(str(self._ep_path), "rb+")
            fseek(self._ep_file, idx*self._ep_length*8, SEEK_SET)
        if self._epc_diskflag:
            self._epc_file = fopen(str(self._epc_path), "rb+")
            fseek(self._epc_file, idx*self._epc_length*8, SEEK_SET)
        if self._ei_diskflag:
            self._ei_file = fopen(str(self._ei_path), "rb+")
            fseek(self._ei_file, idx*self._ei_length*8, SEEK_SET)
        if self._tf_diskflag:
            self._tf_file = fopen(str(self._tf_path), "rb+")
            fseek(self._tf_file, idx*self._tf_length*8, SEEK_SET)
        if self._tfwat_diskflag:
            self._tfwat_file = fopen(str(self._tfwat_path), "rb+")
            fseek(self._tfwat_file, idx*self._tfwat_length*8, SEEK_SET)
        if self._tfice_diskflag:
            self._tfice_file = fopen(str(self._tfice_path), "rb+")
            fseek(self._tfice_file, idx*self._tfice_length*8, SEEK_SET)
        if self._glmelt_diskflag:
            self._glmelt_file = fopen(str(self._glmelt_path), "rb+")
            fseek(self._glmelt_file, idx*self._glmelt_length*8, SEEK_SET)
        if self._meltpot_diskflag:
            self._meltpot_file = fopen(str(self._meltpot_path), "rb+")
            fseek(self._meltpot_file, idx*self._meltpot_length*8, SEEK_SET)
        if self._melt_diskflag:
            self._melt_file = fopen(str(self._melt_path), "rb+")
            fseek(self._melt_file, idx*self._melt_length*8, SEEK_SET)
        if self._refrpot_diskflag:
            self._refrpot_file = fopen(str(self._refrpot_path), "rb+")
            fseek(self._refrpot_file, idx*self._refrpot_length*8, SEEK_SET)
        if self._refr_diskflag:
            self._refr_file = fopen(str(self._refr_path), "rb+")
            fseek(self._refr_file, idx*self._refr_length*8, SEEK_SET)
        if self._in__diskflag:
            self._in__file = fopen(str(self._in__path), "rb+")
            fseek(self._in__file, idx*self._in__length*8, SEEK_SET)
        if self._r_diskflag:
            self._r_file = fopen(str(self._r_path), "rb+")
            fseek(self._r_file, idx*self._r_length*8, SEEK_SET)
        if self._ea_diskflag:
            self._ea_file = fopen(str(self._ea_path), "rb+")
            fseek(self._ea_file, idx*self._ea_length*8, SEEK_SET)
        if self._cfpot_diskflag:
            self._cfpot_file = fopen(str(self._cfpot_path), "rb+")
            fseek(self._cfpot_file, idx*self._cfpot_length*8, SEEK_SET)
        if self._cf_diskflag:
            self._cf_file = fopen(str(self._cf_path), "rb+")
            fseek(self._cf_file, idx*self._cf_length*8, SEEK_SET)
        if self._perc_diskflag:
            self._perc_file = fopen(str(self._perc_path), "rb+")
            fseek(self._perc_file, idx*8, SEEK_SET)
        if self._contriarea_diskflag:
            self._contriarea_file = fopen(str(self._contriarea_path), "rb+")
            fseek(self._contriarea_file, idx*8, SEEK_SET)
        if self._inuz_diskflag:
            self._inuz_file = fopen(str(self._inuz_path), "rb+")
            fseek(self._inuz_file, idx*8, SEEK_SET)
        if self._q0_diskflag:
            self._q0_file = fopen(str(self._q0_path), "rb+")
            fseek(self._q0_file, idx*8, SEEK_SET)
        if self._el_diskflag:
            self._el_file = fopen(str(self._el_path), "rb+")
            fseek(self._el_file, idx*self._el_length*8, SEEK_SET)
        if self._q1_diskflag:
            self._q1_file = fopen(str(self._q1_path), "rb+")
            fseek(self._q1_file, idx*8, SEEK_SET)
        if self._inuh_diskflag:
            self._inuh_file = fopen(str(self._inuh_path), "rb+")
            fseek(self._inuh_file, idx*8, SEEK_SET)
        if self._outuh_diskflag:
            self._outuh_file = fopen(str(self._outuh_path), "rb+")
            fseek(self._outuh_file, idx*8, SEEK_SET)
        if self._qt_diskflag:
            self._qt_file = fopen(str(self._qt_path), "rb+")
            fseek(self._qt_file, idx*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._cf_diskflag:
            fclose(self._cf_file)
        if self._cfpot_diskflag:
            fclose(self._cfpot_file)
        if self._contriarea_diskflag:
            fclose(self._contriarea_file)
        if self._ea_diskflag:
            fclose(self._ea_file)
        if self._ei_diskflag:
            fclose(self._ei_file)
        if self._el_diskflag:
            fclose(self._el_file)
        if self._ep_diskflag:
            fclose(self._ep_file)
        if self._epc_diskflag:
            fclose(self._epc_file)
        if self._fracrain_diskflag:
            fclose(self._fracrain_file)
        if self._glmelt_diskflag:
            fclose(self._glmelt_file)
        if self._in__diskflag:
            fclose(self._in__file)
        if self._inuh_diskflag:
            fclose(self._inuh_file)
        if self._inuz_diskflag:
            fclose(self._inuz_file)
        if self._melt_diskflag:
            fclose(self._melt_file)
        if self._meltpot_diskflag:
            fclose(self._meltpot_file)
        if self._outuh_diskflag:
            fclose(self._outuh_file)
        if self._pc_diskflag:
            fclose(self._pc_file)
        if self._perc_diskflag:
            fclose(self._perc_file)
        if self._q0_diskflag:
            fclose(self._q0_file)
        if self._q1_diskflag:
            fclose(self._q1_file)
        if self._qt_diskflag:
            fclose(self._qt_file)
        if self._r_diskflag:
            fclose(self._r_file)
        if self._refr_diskflag:
            fclose(self._refr_file)
        if self._refrpot_diskflag:
            fclose(self._refrpot_file)
        if self._rfc_diskflag:
            fclose(self._rfc_file)
        if self._sfc_diskflag:
            fclose(self._sfc_file)
        if self._tc_diskflag:
            fclose(self._tc_file)
        if self._tf_diskflag:
            fclose(self._tf_file)
        if self._tfice_diskflag:
            fclose(self._tfice_file)
        if self._tfwat_diskflag:
            fclose(self._tfwat_file)
        if self._tmean_diskflag:
            fclose(self._tmean_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._tmean_diskflag:
            fwrite(&self.tmean, 8, 1, self._tmean_file)
        elif self._tmean_ramflag:
            self._tmean_array[idx] = self.tmean
        if self._tc_diskflag:
            fwrite(&self.tc[0], 8, self._tc_length, self._tc_file)
        elif self._tc_ramflag:
            for jdx0 in range(self._tc_length_0):
                self._tc_array[idx,jdx0] = self.tc[jdx0]
        if self._fracrain_diskflag:
            fwrite(&self.fracrain[0], 8, self._fracrain_length, self._fracrain_file)
        elif self._fracrain_ramflag:
            for jdx0 in range(self._fracrain_length_0):
                self._fracrain_array[idx,jdx0] = self.fracrain[jdx0]
        if self._rfc_diskflag:
            fwrite(&self.rfc[0], 8, self._rfc_length, self._rfc_file)
        elif self._rfc_ramflag:
            for jdx0 in range(self._rfc_length_0):
                self._rfc_array[idx,jdx0] = self.rfc[jdx0]
        if self._sfc_diskflag:
            fwrite(&self.sfc[0], 8, self._sfc_length, self._sfc_file)
        elif self._sfc_ramflag:
            for jdx0 in range(self._sfc_length_0):
                self._sfc_array[idx,jdx0] = self.sfc[jdx0]
        if self._pc_diskflag:
            fwrite(&self.pc[0], 8, self._pc_length, self._pc_file)
        elif self._pc_ramflag:
            for jdx0 in range(self._pc_length_0):
                self._pc_array[idx,jdx0] = self.pc[jdx0]
        if self._ep_diskflag:
            fwrite(&self.ep[0], 8, self._ep_length, self._ep_file)
        elif self._ep_ramflag:
            for jdx0 in range(self._ep_length_0):
                self._ep_array[idx,jdx0] = self.ep[jdx0]
        if self._epc_diskflag:
            fwrite(&self.epc[0], 8, self._epc_length, self._epc_file)
        elif self._epc_ramflag:
            for jdx0 in range(self._epc_length_0):
                self._epc_array[idx,jdx0] = self.epc[jdx0]
        if self._ei_diskflag:
            fwrite(&self.ei[0], 8, self._ei_length, self._ei_file)
        elif self._ei_ramflag:
            for jdx0 in range(self._ei_length_0):
                self._ei_array[idx,jdx0] = self.ei[jdx0]
        if self._tf_diskflag:
            fwrite(&self.tf[0], 8, self._tf_length, self._tf_file)
        elif self._tf_ramflag:
            for jdx0 in range(self._tf_length_0):
                self._tf_array[idx,jdx0] = self.tf[jdx0]
        if self._tfwat_diskflag:
            fwrite(&self.tfwat[0], 8, self._tfwat_length, self._tfwat_file)
        elif self._tfwat_ramflag:
            for jdx0 in range(self._tfwat_length_0):
                self._tfwat_array[idx,jdx0] = self.tfwat[jdx0]
        if self._tfice_diskflag:
            fwrite(&self.tfice[0], 8, self._tfice_length, self._tfice_file)
        elif self._tfice_ramflag:
            for jdx0 in range(self._tfice_length_0):
                self._tfice_array[idx,jdx0] = self.tfice[jdx0]
        if self._glmelt_diskflag:
            fwrite(&self.glmelt[0], 8, self._glmelt_length, self._glmelt_file)
        elif self._glmelt_ramflag:
            for jdx0 in range(self._glmelt_length_0):
                self._glmelt_array[idx,jdx0] = self.glmelt[jdx0]
        if self._meltpot_diskflag:
            fwrite(&self.meltpot[0], 8, self._meltpot_length, self._meltpot_file)
        elif self._meltpot_ramflag:
            for jdx0 in range(self._meltpot_length_0):
                self._meltpot_array[idx,jdx0] = self.meltpot[jdx0]
        if self._melt_diskflag:
            fwrite(&self.melt[0], 8, self._melt_length, self._melt_file)
        elif self._melt_ramflag:
            for jdx0 in range(self._melt_length_0):
                self._melt_array[idx,jdx0] = self.melt[jdx0]
        if self._refrpot_diskflag:
            fwrite(&self.refrpot[0], 8, self._refrpot_length, self._refrpot_file)
        elif self._refrpot_ramflag:
            for jdx0 in range(self._refrpot_length_0):
                self._refrpot_array[idx,jdx0] = self.refrpot[jdx0]
        if self._refr_diskflag:
            fwrite(&self.refr[0], 8, self._refr_length, self._refr_file)
        elif self._refr_ramflag:
            for jdx0 in range(self._refr_length_0):
                self._refr_array[idx,jdx0] = self.refr[jdx0]
        if self._in__diskflag:
            fwrite(&self.in_[0], 8, self._in__length, self._in__file)
        elif self._in__ramflag:
            for jdx0 in range(self._in__length_0):
                self._in__array[idx,jdx0] = self.in_[jdx0]
        if self._r_diskflag:
            fwrite(&self.r[0], 8, self._r_length, self._r_file)
        elif self._r_ramflag:
            for jdx0 in range(self._r_length_0):
                self._r_array[idx,jdx0] = self.r[jdx0]
        if self._ea_diskflag:
            fwrite(&self.ea[0], 8, self._ea_length, self._ea_file)
        elif self._ea_ramflag:
            for jdx0 in range(self._ea_length_0):
                self._ea_array[idx,jdx0] = self.ea[jdx0]
        if self._cfpot_diskflag:
            fwrite(&self.cfpot[0], 8, self._cfpot_length, self._cfpot_file)
        elif self._cfpot_ramflag:
            for jdx0 in range(self._cfpot_length_0):
                self._cfpot_array[idx,jdx0] = self.cfpot[jdx0]
        if self._cf_diskflag:
            fwrite(&self.cf[0], 8, self._cf_length, self._cf_file)
        elif self._cf_ramflag:
            for jdx0 in range(self._cf_length_0):
                self._cf_array[idx,jdx0] = self.cf[jdx0]
        if self._perc_diskflag:
            fwrite(&self.perc, 8, 1, self._perc_file)
        elif self._perc_ramflag:
            self._perc_array[idx] = self.perc
        if self._contriarea_diskflag:
            fwrite(&self.contriarea, 8, 1, self._contriarea_file)
        elif self._contriarea_ramflag:
            self._contriarea_array[idx] = self.contriarea
        if self._inuz_diskflag:
            fwrite(&self.inuz, 8, 1, self._inuz_file)
        elif self._inuz_ramflag:
            self._inuz_array[idx] = self.inuz
        if self._q0_diskflag:
            fwrite(&self.q0, 8, 1, self._q0_file)
        elif self._q0_ramflag:
            self._q0_array[idx] = self.q0
        if self._el_diskflag:
            fwrite(&self.el[0], 8, self._el_length, self._el_file)
        elif self._el_ramflag:
            for jdx0 in range(self._el_length_0):
                self._el_array[idx,jdx0] = self.el[jdx0]
        if self._q1_diskflag:
            fwrite(&self.q1, 8, 1, self._q1_file)
        elif self._q1_ramflag:
            self._q1_array[idx] = self.q1
        if self._inuh_diskflag:
            fwrite(&self.inuh, 8, 1, self._inuh_file)
        elif self._inuh_ramflag:
            self._inuh_array[idx] = self.inuh
        if self._outuh_diskflag:
            fwrite(&self.outuh, 8, 1, self._outuh_file)
        elif self._outuh_ramflag:
            self._outuh_array[idx] = self.outuh
        if self._qt_diskflag:
            fwrite(&self.qt, 8, 1, self._qt_file)
        elif self._qt_ramflag:
            self._qt_array[idx] = self.qt
@cython.final
cdef class Model(object):
    cdef public ControlParameters control
    cdef public DerivedParameters derived
    cdef public InputSequences inputs
    cdef public LogSequences logs
    cdef public OutletSequences outlets
    cdef public StateSequences states
    cdef public AideSequences aides
    cdef public FluxSequences fluxes
    cdef public StateSequences old_states
    cdef public StateSequences new_states
    cpdef inline void doit(self, int idx):
        self.loaddata(idx)
        self.run(idx)
        self.updateoutlets(idx)
        self.new2old()
        self.savedata(idx)
    cpdef inline void openfiles(self, int idx):
        self.inputs.openfiles(idx)
        self.states.openfiles(idx)
        self.fluxes.openfiles(idx)
    cpdef inline void closefiles(self):
        self.inputs.closefiles()
        self.states.closefiles()
        self.fluxes.closefiles()
    cpdef inline void loaddata(self, int idx):
        self.inputs.loaddata(idx)
    cpdef inline void savedata(self, int idx):
        self.states.savedata(idx)
        self.fluxes.savedata(idx)
    cpdef inline void new2old(self):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        for jdx0 in range(self.states._ic_length_0):
            self.old_states.ic[jdx0] = self.new_states.ic[jdx0]
        self.old_states.lz = self.new_states.lz
        for jdx0 in range(self.states._sm_length_0):
            self.old_states.sm[jdx0] = self.new_states.sm[jdx0]
        for jdx0 in range(self.states._sp_length_0):
            self.old_states.sp[jdx0] = self.new_states.sp[jdx0]
        self.old_states.uz = self.new_states.uz
        for jdx0 in range(self.states._wc_length_0):
            self.old_states.wc[jdx0] = self.new_states.wc[jdx0]
    cpdef inline void calc_epc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            self.fluxes.epc[k] = (self.fluxes.ep[k]*self.control.ecorr[k] *
                          (1. - self.control.ecalt[k]*(self.control.zonez[k]-self.control.zrele)))
            self.fluxes.epc[k] *= exp(-self.control.epf[k]*self.fluxes.pc[k])
    cpdef inline void calc_outuh_quh(self):
        cdef int jdx
        self.fluxes.outuh = self.derived.uh[0]*self.fluxes.inuh+self.logs.quh[0]
        for jdx in range(1, self.derived.nmbuh):
            self.logs.quh[jdx-1] = self.derived.uh[jdx]*self.fluxes.inuh+self.logs.quh[jdx]
    cpdef inline void calc_tf_ic(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if (self.control.zonetype[k] == FIELD) or (self.control.zonetype[k] == FOREST):
                self.fluxes.tf[k] = max(self.fluxes.pc[k]-(self.control.icmax[k]-self.states.ic[k]), 0.)
                self.states.ic[k] += self.fluxes.pc[k]-self.fluxes.tf[k]
            else:
                self.fluxes.tf[k] = self.fluxes.pc[k]
                self.states.ic[k] = 0.
    cpdef inline void calc_inuz(self):
        cdef int k
        self.fluxes.inuz = 0.
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] != ILAKE:
                self.fluxes.inuz += self.derived.rellandzonearea[k]*(self.fluxes.r[k]-self.fluxes.cf[k])
    cpdef inline void calc_sp_wc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] != ILAKE:
                if (self.fluxes.rfc[k]+self.fluxes.sfc[k]) > 0.:
                    self.states.wc[k] += self.fluxes.tf[k]*self.fluxes.rfc[k]/(self.fluxes.rfc[k]+self.fluxes.sfc[k])
                    self.states.sp[k] += self.fluxes.tf[k]*self.fluxes.sfc[k]/(self.fluxes.rfc[k]+self.fluxes.sfc[k])
            else:
                self.states.wc[k] = 0.
                self.states.sp[k] = 0.
    cpdef inline void updateoutlets(self, int idx):
        self.outlets.q[0] += self.derived.qfactor*self.fluxes.qt
    cpdef inline void calc_tc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            self.fluxes.tc[k] = self.inputs.t-self.control.tcalt[k]*(self.control.zonez[k]-self.control.zrelt)
    cpdef inline void calc_tmean(self):
        cdef int k
        self.fluxes.tmean = 0.
        for k in range(self.control.nmbzones):
            self.fluxes.tmean += self.derived.relzonearea[k]*self.fluxes.tc[k]
    cpdef inline void calc_contriarea(self):
        cdef int k
        if self.control.resparea and (self.derived.relsoilarea > 0.):
            self.fluxes.contriarea = 0.
            for k in range(self.control.nmbzones):
                if (self.control.zonetype[k] == FIELD) or (self.control.zonetype[k] == FOREST):
                    if self.control.fc[k] > 0.:
                        self.fluxes.contriarea += (self.derived.relsoilzonearea[k]*
                                           (self.states.sm[k]/self.control.fc[k])**self.control.beta[k])
                    else:
                        self.fluxes.contriarea += self.derived.relsoilzonearea[k]
        else:
            self.fluxes.contriarea = 1.
    cpdef inline void calc_inuh(self):
        self.fluxes.inuh = self.derived.rellandarea*self.fluxes.q0+self.fluxes.q1
    cpdef inline void calc_el_lz(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if (self.control.zonetype[k] == ILAKE) and (self.fluxes.tc[k] > self.control.ttice[k]):
                self.fluxes.el[k] = self.fluxes.epc[k]
                self.states.lz -= self.derived.relzonearea[k]*self.fluxes.el[k]
            else:
                self.fluxes.el[k] = 0.
    cpdef inline void calc_fracrain(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if self.fluxes.tc[k] >= (self.control.tt[k]+self.control.ttint[k]/2.):
                self.fluxes.fracrain[k] = 1.
            elif self.fluxes.tc[k] <= (self.control.tt[k]-self.control.ttint[k]/2.):
                self.fluxes.fracrain[k] = 0.
            else:
                self.fluxes.fracrain[k] = ((self.fluxes.tc[k]-(self.control.tt[k]-self.control.ttint[k]/2.)) /
                                   self.control.ttint[k])
    cpdef inline void calc_q1_lz(self):
        if self.states.lz > 0.:
            self.fluxes.q1 = self.control.k4*self.states.lz**(1.+self.control.gamma)
        else:
            self.fluxes.q1 = 0.
        self.states.lz -= self.fluxes.q1
    cpdef inline void calc_lz(self):
        cdef int k
        self.states.lz += self.derived.rellandarea*self.fluxes.perc
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] == ILAKE:
                self.states.lz += self.derived.relzonearea[k]*self.fluxes.pc[k]
    cpdef inline void calc_melt_sp_wc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] != ILAKE:
                if self.fluxes.tc[k] > self.derived.ttm[k]:
                    self.fluxes.melt[k] = min(self.control.cfmax[k] *
                                      (self.fluxes.tc[k]-self.derived.ttm[k]), self.states.sp[k])
                    self.states.sp[k] -= self.fluxes.melt[k]
                    self.states.wc[k] += self.fluxes.melt[k]
                else:
                    self.fluxes.melt[k] = 0.
            else:
                self.fluxes.melt[k] = 0.
                self.states.wc[k] = 0.
                self.states.sp[k] = 0.
    cpdef inline void calc_pc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            self.fluxes.pc[k] = self.inputs.p*self.control.pcorr[k]
            self.fluxes.pc[k] *= 1.+self.control.pcalt[k]*(self.control.zonez[k]-self.control.zrelp)
            self.fluxes.pc[k] *= self.fluxes.rfc[k]+self.fluxes.sfc[k]
    cpdef inline void calc_rfc_sfc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            self.fluxes.rfc[k] = self.fluxes.fracrain[k]*self.control.rfcf[k]
            self.fluxes.sfc[k] = (1.-self.fluxes.fracrain[k])*self.control.sfcf[k]
    cpdef inline void calc_qt(self):
        self.fluxes.qt = max(self.fluxes.outuh-self.control.abstr, 0.)
    cpdef inline void calc_refr_sp_wc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] != ILAKE:
                if self.fluxes.tc[k] < self.derived.ttm[k]:
                    self.fluxes.refr[k] = min(self.control.cfr[k]*self.control.cfmax[k] *
                                      (self.derived.ttm[k]-self.fluxes.tc[k]), self.states.wc[k])
                    self.states.sp[k] += self.fluxes.refr[k]
                    self.states.wc[k] -= self.fluxes.refr[k]
                else:
                    self.fluxes.refr[k] = 0.
            else:
                self.fluxes.refr[k] = 0.
                self.states.wc[k] = 0.
                self.states.sp[k] = 0.
    cpdef inline void calc_q0_perc_uz(self):
        cdef int jdx
        self.fluxes.perc = 0.
        self.fluxes.q0 = 0.
        for jdx in range(self.control.recstep):
            self.states.uz += self.derived.dt*self.fluxes.inuz
            self.aides.perc = min(self.derived.dt*self.control.percmax*self.fluxes.contriarea, self.states.uz)
            self.states.uz -= self.aides.perc
            self.fluxes.perc += self.aides.perc
            if self.states.uz > 0.:
                if self.fluxes.contriarea > 0.:
                    self.aides.q0 = (self.derived.dt*self.control.k *
                              (self.states.uz/self.fluxes.contriarea)**(1.+self.control.alpha))
                    self.aides.q0 = min(self.aides.q0, self.states.uz)
                else:
                    self.aides.q0 = self.states.uz
                self.states.uz -= self.aides.q0
                self.fluxes.q0 += self.aides.q0
            else:
                self.aides.q0 = 0.
    cpdef inline void calc_glmelt_in(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] == GLACIER:
                if (self.states.sp[k] <= 0.) and (self.fluxes.tc[k] > self.derived.ttm[k]):
                    self.fluxes.glmelt[k] = self.control.gmelt[k]*(self.fluxes.tc[k]-self.derived.ttm[k])
                    self.fluxes.in_[k] += self.fluxes.glmelt[k]
                else:
                    self.fluxes.glmelt[k] = 0.
    cpdef inline void calc_ea_sm(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if (self.control.zonetype[k] == FIELD) or (self.control.zonetype[k] == FOREST):
                if self.states.sp[k] <= 0.:
                    if (self.control.lp[k]*self.control.fc[k]) > 0.:
                        self.fluxes.ea[k] = self.fluxes.epc[k]*self.states.sm[k]/(self.control.lp[k]*self.control.fc[k])
                        self.fluxes.ea[k] = min(self.fluxes.ea[k], self.fluxes.epc[k])
                    else:
                        self.fluxes.ea[k] = self.fluxes.epc[k]
                    self.fluxes.ea[k] -= max(self.control.ered[k] *
                                     (self.fluxes.ea[k]+self.fluxes.ei[k]-self.fluxes.epc[k]), 0.)
                    self.fluxes.ea[k] = min(self.fluxes.ea[k], self.states.sm[k])
                else:
                    self.fluxes.ea[k] = 0.
                self.states.sm[k] -= self.fluxes.ea[k]
            else:
                self.fluxes.ea[k] = 0.
                self.states.sm[k] = 0.
    cpdef inline void calc_in_wc(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if self.control.zonetype[k] != ILAKE:
                self.fluxes.in_[k] = max(self.states.wc[k]-self.control.whc[k]*self.states.sp[k], 0.)
                self.states.wc[k] -= self.fluxes.in_[k]
            else:
                self.fluxes.in_[k] = self.fluxes.tf[k]
                self.states.wc[k] = 0.
    cpdef inline void calc_r_sm(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if (self.control.zonetype[k] == FIELD) or (self.control.zonetype[k] == FOREST):
                if self.control.fc[k] > 0.:
                    self.fluxes.r[k] = self.fluxes.in_[k]*(self.states.sm[k]/self.control.fc[k])**self.control.beta[k]
                    self.fluxes.r[k] = max(self.fluxes.r[k], self.states.sm[k]+self.fluxes.in_[k]-self.control.fc[k])
                else:
                    self.fluxes.r[k] = self.fluxes.in_[k]
                self.states.sm[k] += self.fluxes.in_[k]-self.fluxes.r[k]
            else:
                self.fluxes.r[k] = self.fluxes.in_[k]
                self.states.sm[k] = 0.
    cpdef inline void calc_cf_sm(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if (self.control.zonetype[k] == FIELD) or (self.control.zonetype[k] == FOREST):
                if self.control.fc[k] > 0.:
                    self.fluxes.cf[k] = self.control.cflux[k]*(1.-self.states.sm[k]/self.control.fc[k])
                    self.fluxes.cf[k] = min(self.fluxes.cf[k], self.states.uz+self.fluxes.r[k])
                    self.fluxes.cf[k] = min(self.fluxes.cf[k], self.control.fc[k]-self.states.sm[k])
                else:
                    self.fluxes.cf[k] = 0.
                self.states.sm[k] += self.fluxes.cf[k]
            else:
                self.fluxes.cf[k] = 0.
                self.states.sm[k] = 0.
    cpdef inline void calc_ep(self):
        cdef int k
        for k in range(self.control.nmbzones):
            self.fluxes.ep[k] = self.inputs.epn*(1.+self.control.etf[k]*(self.fluxes.tmean-self.inputs.tn))
            self.fluxes.ep[k] = min(max(self.fluxes.ep[k], 0.), 2.*self.inputs.epn)
    cpdef inline void calc_ei_ic(self):
        cdef int k
        for k in range(self.control.nmbzones):
            if (self.control.zonetype[k] == FIELD) or (self.control.zonetype[k] == FOREST):
                self.fluxes.ei[k] = min(self.fluxes.epc[k], self.states.ic[k])
                self.states.ic[k] -= self.fluxes.ei[k]
            else:
                self.fluxes.ei[k] = 0.
                self.states.ic[k] = 0.
    cpdef inline void run(self, int idx):
        self.calc_tc()
        self.calc_tmean()
        self.calc_fracrain()
        self.calc_rfc_sfc()
        self.calc_pc()
        self.calc_ep()
        self.calc_epc()
        self.calc_tf_ic()
        self.calc_ei_ic()
        self.calc_sp_wc()
        self.calc_melt_sp_wc()
        self.calc_refr_sp_wc()
        self.calc_in_wc()
        self.calc_r_sm()
        self.calc_cf_sm()
        self.calc_ea_sm()
        self.calc_inuz()
        self.calc_contriarea()
        self.calc_q0_perc_uz()
        self.calc_lz()
        self.calc_el_lz()
        self.calc_q1_lz()
        self.calc_inuh()
        self.calc_outuh_quh()
        self.calc_qt()
