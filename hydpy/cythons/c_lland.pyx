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
cdef public numpy.int32_t GLETS = 8
cdef public numpy.int32_t VERS = 3
cdef public numpy.int32_t FEUCHT = 10
cdef public numpy.int32_t OBSTB = 6
cdef public numpy.int32_t ACKER = 4
cdef public numpy.int32_t SIED_L = 2
cdef public numpy.int32_t BODEN = 7
cdef public numpy.int32_t SIED_D = 1
cdef public numpy.int32_t LAUBW = 14
cdef public numpy.int32_t MISCHW = 15
cdef public numpy.int32_t WASSER = 16
cdef public numpy.int32_t BAUMB = 12
cdef public numpy.int32_t NADELW = 13
cdef public numpy.int32_t GRUE_E = 11
cdef public numpy.int32_t WEINB = 5
cdef public numpy.int32_t GRUE_I = 9
@cython.final
cdef class ControlParameters(object):
    cdef public double ft
    cdef public numpy.int32_t nhru
    cdef public double[:] fhru
    cdef public numpy.int32_t[:] lnk
    cdef public double[:] hnn
    cdef public double[:] kg
    cdef public double[:] kt
    cdef public double[:] ke
    cdef public double[:] kf
    cdef public double[:,:] fln
    cdef public double[:] hinz
    cdef public double[:,:] lai
    cdef public double[:] treft
    cdef public double[:] trefn
    cdef public double[:] tgr
    cdef public double[:] gtf
    cdef public double rschmelz
    cdef public double cpwasser
    cdef public double[:] pwmax
    cdef public double grasref_r
    cdef public double[:] nfk
    cdef public double[:] relwb
    cdef public double[:] relwz
    cdef public double[:] beta
    cdef public double[:] dmin
    cdef public double[:] dmax
    cdef public double[:] bsf
    cdef public double tind
    cdef public double eqb
    cdef public double eqi1
    cdef public double eqi2
    cdef public double eqd
@cython.final
cdef class DerivedParameters(object):
    cdef public double[:] relsubarea
    cdef public numpy.int32_t[:] moy
    cdef public double[:,:] kinz
    cdef public double[:] wb
    cdef public double[:] wz
    cdef public double kb
    cdef public double ki1
    cdef public double ki2
    cdef public double kd
    cdef public double qfactor
@cython.final
cdef class StateSequences(object):
    cdef public double[:] inzp
    cdef public int _inzp_ndim
    cdef public int _inzp_length
    cdef public int _inzp_length_0
    cdef public bint _inzp_diskflag
    cdef public str _inzp_path
    cdef FILE *_inzp_file
    cdef public bint _inzp_ramflag
    cdef public double[:,:] _inzp_array
    cdef public double[:] wats
    cdef public int _wats_ndim
    cdef public int _wats_length
    cdef public int _wats_length_0
    cdef public bint _wats_diskflag
    cdef public str _wats_path
    cdef FILE *_wats_file
    cdef public bint _wats_ramflag
    cdef public double[:,:] _wats_array
    cdef public double[:] waes
    cdef public int _waes_ndim
    cdef public int _waes_length
    cdef public int _waes_length_0
    cdef public bint _waes_diskflag
    cdef public str _waes_path
    cdef FILE *_waes_file
    cdef public bint _waes_ramflag
    cdef public double[:,:] _waes_array
    cdef public double[:] bowa
    cdef public int _bowa_ndim
    cdef public int _bowa_length
    cdef public int _bowa_length_0
    cdef public bint _bowa_diskflag
    cdef public str _bowa_path
    cdef FILE *_bowa_file
    cdef public bint _bowa_ramflag
    cdef public double[:,:] _bowa_array
    cdef public double[:] wrel
    cdef public int _wrel_ndim
    cdef public int _wrel_length
    cdef public int _wrel_length_0
    cdef public bint _wrel_diskflag
    cdef public str _wrel_path
    cdef FILE *_wrel_file
    cdef public bint _wrel_ramflag
    cdef public double[:,:] _wrel_array
    cdef public double qdgz
    cdef public int _qdgz_ndim
    cdef public int _qdgz_length
    cdef public bint _qdgz_diskflag
    cdef public str _qdgz_path
    cdef FILE *_qdgz_file
    cdef public bint _qdgz_ramflag
    cdef public double[:] _qdgz_array
    cdef public double qigz1
    cdef public int _qigz1_ndim
    cdef public int _qigz1_length
    cdef public bint _qigz1_diskflag
    cdef public str _qigz1_path
    cdef FILE *_qigz1_file
    cdef public bint _qigz1_ramflag
    cdef public double[:] _qigz1_array
    cdef public double qigz2
    cdef public int _qigz2_ndim
    cdef public int _qigz2_length
    cdef public bint _qigz2_diskflag
    cdef public str _qigz2_path
    cdef FILE *_qigz2_file
    cdef public bint _qigz2_ramflag
    cdef public double[:] _qigz2_array
    cdef public double qbgz
    cdef public int _qbgz_ndim
    cdef public int _qbgz_length
    cdef public bint _qbgz_diskflag
    cdef public str _qbgz_path
    cdef FILE *_qbgz_file
    cdef public bint _qbgz_ramflag
    cdef public double[:] _qbgz_array
    cdef public double qdga
    cdef public int _qdga_ndim
    cdef public int _qdga_length
    cdef public bint _qdga_diskflag
    cdef public str _qdga_path
    cdef FILE *_qdga_file
    cdef public bint _qdga_ramflag
    cdef public double[:] _qdga_array
    cdef public double qiga1
    cdef public int _qiga1_ndim
    cdef public int _qiga1_length
    cdef public bint _qiga1_diskflag
    cdef public str _qiga1_path
    cdef FILE *_qiga1_file
    cdef public bint _qiga1_ramflag
    cdef public double[:] _qiga1_array
    cdef public double qiga2
    cdef public int _qiga2_ndim
    cdef public int _qiga2_length
    cdef public bint _qiga2_diskflag
    cdef public str _qiga2_path
    cdef FILE *_qiga2_file
    cdef public bint _qiga2_ramflag
    cdef public double[:] _qiga2_array
    cdef public double qbga
    cdef public int _qbga_ndim
    cdef public int _qbga_length
    cdef public bint _qbga_diskflag
    cdef public str _qbga_path
    cdef FILE *_qbga_file
    cdef public bint _qbga_ramflag
    cdef public double[:] _qbga_array
    cpdef openfiles(self, int idx):
        if self._inzp_diskflag:
            self._inzp_file = fopen(str(self._inzp_path), "rb+")
            fseek(self._inzp_file, idx*self._inzp_length*8, SEEK_SET)
        if self._wats_diskflag:
            self._wats_file = fopen(str(self._wats_path), "rb+")
            fseek(self._wats_file, idx*self._wats_length*8, SEEK_SET)
        if self._waes_diskflag:
            self._waes_file = fopen(str(self._waes_path), "rb+")
            fseek(self._waes_file, idx*self._waes_length*8, SEEK_SET)
        if self._bowa_diskflag:
            self._bowa_file = fopen(str(self._bowa_path), "rb+")
            fseek(self._bowa_file, idx*self._bowa_length*8, SEEK_SET)
        if self._wrel_diskflag:
            self._wrel_file = fopen(str(self._wrel_path), "rb+")
            fseek(self._wrel_file, idx*self._wrel_length*8, SEEK_SET)
        if self._qdgz_diskflag:
            self._qdgz_file = fopen(str(self._qdgz_path), "rb+")
            fseek(self._qdgz_file, idx*8, SEEK_SET)
        if self._qigz1_diskflag:
            self._qigz1_file = fopen(str(self._qigz1_path), "rb+")
            fseek(self._qigz1_file, idx*8, SEEK_SET)
        if self._qigz2_diskflag:
            self._qigz2_file = fopen(str(self._qigz2_path), "rb+")
            fseek(self._qigz2_file, idx*8, SEEK_SET)
        if self._qbgz_diskflag:
            self._qbgz_file = fopen(str(self._qbgz_path), "rb+")
            fseek(self._qbgz_file, idx*8, SEEK_SET)
        if self._qdga_diskflag:
            self._qdga_file = fopen(str(self._qdga_path), "rb+")
            fseek(self._qdga_file, idx*8, SEEK_SET)
        if self._qiga1_diskflag:
            self._qiga1_file = fopen(str(self._qiga1_path), "rb+")
            fseek(self._qiga1_file, idx*8, SEEK_SET)
        if self._qiga2_diskflag:
            self._qiga2_file = fopen(str(self._qiga2_path), "rb+")
            fseek(self._qiga2_file, idx*8, SEEK_SET)
        if self._qbga_diskflag:
            self._qbga_file = fopen(str(self._qbga_path), "rb+")
            fseek(self._qbga_file, idx*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._bowa_diskflag:
            fclose(self._bowa_file)
        if self._inzp_diskflag:
            fclose(self._inzp_file)
        if self._qbga_diskflag:
            fclose(self._qbga_file)
        if self._qbgz_diskflag:
            fclose(self._qbgz_file)
        if self._qdga_diskflag:
            fclose(self._qdga_file)
        if self._qdgz_diskflag:
            fclose(self._qdgz_file)
        if self._qiga1_diskflag:
            fclose(self._qiga1_file)
        if self._qiga2_diskflag:
            fclose(self._qiga2_file)
        if self._qigz1_diskflag:
            fclose(self._qigz1_file)
        if self._qigz2_diskflag:
            fclose(self._qigz2_file)
        if self._waes_diskflag:
            fclose(self._waes_file)
        if self._wats_diskflag:
            fclose(self._wats_file)
        if self._wrel_diskflag:
            fclose(self._wrel_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._inzp_diskflag:
            fwrite(&self.inzp[0], 8, self._inzp_length, self._inzp_file)
        elif self._inzp_ramflag:
            for jdx0 in range(self._inzp_length_0):
                self._inzp_array[idx,jdx0] = self.inzp[jdx0]
        if self._wats_diskflag:
            fwrite(&self.wats[0], 8, self._wats_length, self._wats_file)
        elif self._wats_ramflag:
            for jdx0 in range(self._wats_length_0):
                self._wats_array[idx,jdx0] = self.wats[jdx0]
        if self._waes_diskflag:
            fwrite(&self.waes[0], 8, self._waes_length, self._waes_file)
        elif self._waes_ramflag:
            for jdx0 in range(self._waes_length_0):
                self._waes_array[idx,jdx0] = self.waes[jdx0]
        if self._bowa_diskflag:
            fwrite(&self.bowa[0], 8, self._bowa_length, self._bowa_file)
        elif self._bowa_ramflag:
            for jdx0 in range(self._bowa_length_0):
                self._bowa_array[idx,jdx0] = self.bowa[jdx0]
        if self._wrel_diskflag:
            fwrite(&self.wrel[0], 8, self._wrel_length, self._wrel_file)
        elif self._wrel_ramflag:
            for jdx0 in range(self._wrel_length_0):
                self._wrel_array[idx,jdx0] = self.wrel[jdx0]
        if self._qdgz_diskflag:
            fwrite(&self.qdgz, 8, 1, self._qdgz_file)
        elif self._qdgz_ramflag:
            self._qdgz_array[idx] = self.qdgz
        if self._qigz1_diskflag:
            fwrite(&self.qigz1, 8, 1, self._qigz1_file)
        elif self._qigz1_ramflag:
            self._qigz1_array[idx] = self.qigz1
        if self._qigz2_diskflag:
            fwrite(&self.qigz2, 8, 1, self._qigz2_file)
        elif self._qigz2_ramflag:
            self._qigz2_array[idx] = self.qigz2
        if self._qbgz_diskflag:
            fwrite(&self.qbgz, 8, 1, self._qbgz_file)
        elif self._qbgz_ramflag:
            self._qbgz_array[idx] = self.qbgz
        if self._qdga_diskflag:
            fwrite(&self.qdga, 8, 1, self._qdga_file)
        elif self._qdga_ramflag:
            self._qdga_array[idx] = self.qdga
        if self._qiga1_diskflag:
            fwrite(&self.qiga1, 8, 1, self._qiga1_file)
        elif self._qiga1_ramflag:
            self._qiga1_array[idx] = self.qiga1
        if self._qiga2_diskflag:
            fwrite(&self.qiga2, 8, 1, self._qiga2_file)
        elif self._qiga2_ramflag:
            self._qiga2_array[idx] = self.qiga2
        if self._qbga_diskflag:
            fwrite(&self.qbga, 8, 1, self._qbga_file)
        elif self._qbga_ramflag:
            self._qbga_array[idx] = self.qbga
@cython.final
cdef class InputSequences(object):
    cdef public double nied
    cdef public int _nied_ndim
    cdef public int _nied_length
    cdef public bint _nied_diskflag
    cdef public str _nied_path
    cdef FILE *_nied_file
    cdef public bint _nied_ramflag
    cdef public double[:] _nied_array
    cdef public double teml
    cdef public int _teml_ndim
    cdef public int _teml_length
    cdef public bint _teml_diskflag
    cdef public str _teml_path
    cdef FILE *_teml_file
    cdef public bint _teml_ramflag
    cdef public double[:] _teml_array
    cdef public double glob
    cdef public int _glob_ndim
    cdef public int _glob_length
    cdef public bint _glob_diskflag
    cdef public str _glob_path
    cdef FILE *_glob_file
    cdef public bint _glob_ramflag
    cdef public double[:] _glob_array
    cpdef inline loaddata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._nied_diskflag:
            fread(&self.nied, 8, 1, self._nied_file)
        elif self._nied_ramflag:
            self.nied = self._nied_array[idx]
        if self._teml_diskflag:
            fread(&self.teml, 8, 1, self._teml_file)
        elif self._teml_ramflag:
            self.teml = self._teml_array[idx]
        if self._glob_diskflag:
            fread(&self.glob, 8, 1, self._glob_file)
        elif self._glob_ramflag:
            self.glob = self._glob_array[idx]
    cpdef openfiles(self, int idx):
        if self._nied_diskflag:
            self._nied_file = fopen(str(self._nied_path), "rb+")
            fseek(self._nied_file, idx*8, SEEK_SET)
        if self._teml_diskflag:
            self._teml_file = fopen(str(self._teml_path), "rb+")
            fseek(self._teml_file, idx*8, SEEK_SET)
        if self._glob_diskflag:
            self._glob_file = fopen(str(self._glob_path), "rb+")
            fseek(self._glob_file, idx*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._glob_diskflag:
            fclose(self._glob_file)
        if self._nied_diskflag:
            fclose(self._nied_file)
        if self._teml_diskflag:
            fclose(self._teml_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._nied_diskflag:
            fwrite(&self.nied, 8, 1, self._nied_file)
        elif self._nied_ramflag:
            self._nied_array[idx] = self.nied
        if self._teml_diskflag:
            fwrite(&self.teml, 8, 1, self._teml_file)
        elif self._teml_ramflag:
            self._teml_array[idx] = self.teml
        if self._glob_diskflag:
            fwrite(&self.glob, 8, 1, self._glob_file)
        elif self._glob_ramflag:
            self._glob_array[idx] = self.glob
@cython.final
cdef class FluxSequences(object):
    cdef public double[:] nkor
    cdef public int _nkor_ndim
    cdef public int _nkor_length
    cdef public int _nkor_length_0
    cdef public bint _nkor_diskflag
    cdef public str _nkor_path
    cdef FILE *_nkor_file
    cdef public bint _nkor_ramflag
    cdef public double[:,:] _nkor_array
    cdef public double[:] tkor
    cdef public int _tkor_ndim
    cdef public int _tkor_length
    cdef public int _tkor_length_0
    cdef public bint _tkor_diskflag
    cdef public str _tkor_path
    cdef FILE *_tkor_file
    cdef public bint _tkor_ramflag
    cdef public double[:,:] _tkor_array
    cdef public double[:] et0
    cdef public int _et0_ndim
    cdef public int _et0_length
    cdef public int _et0_length_0
    cdef public bint _et0_diskflag
    cdef public str _et0_path
    cdef FILE *_et0_file
    cdef public bint _et0_ramflag
    cdef public double[:,:] _et0_array
    cdef public double[:] evpo
    cdef public int _evpo_ndim
    cdef public int _evpo_length
    cdef public int _evpo_length_0
    cdef public bint _evpo_diskflag
    cdef public str _evpo_path
    cdef FILE *_evpo_file
    cdef public bint _evpo_ramflag
    cdef public double[:,:] _evpo_array
    cdef public double[:] nbes
    cdef public int _nbes_ndim
    cdef public int _nbes_length
    cdef public int _nbes_length_0
    cdef public bint _nbes_diskflag
    cdef public str _nbes_path
    cdef FILE *_nbes_file
    cdef public bint _nbes_ramflag
    cdef public double[:,:] _nbes_array
    cdef public double[:] evi
    cdef public int _evi_ndim
    cdef public int _evi_length
    cdef public int _evi_length_0
    cdef public bint _evi_diskflag
    cdef public str _evi_path
    cdef FILE *_evi_file
    cdef public bint _evi_ramflag
    cdef public double[:,:] _evi_array
    cdef public double[:] evb
    cdef public int _evb_ndim
    cdef public int _evb_length
    cdef public int _evb_length_0
    cdef public bint _evb_diskflag
    cdef public str _evb_path
    cdef FILE *_evb_file
    cdef public bint _evb_ramflag
    cdef public double[:,:] _evb_array
    cdef public double[:] wgtf
    cdef public int _wgtf_ndim
    cdef public int _wgtf_length
    cdef public int _wgtf_length_0
    cdef public bint _wgtf_diskflag
    cdef public str _wgtf_path
    cdef FILE *_wgtf_file
    cdef public bint _wgtf_ramflag
    cdef public double[:,:] _wgtf_array
    cdef public double[:] schm
    cdef public int _schm_ndim
    cdef public int _schm_length
    cdef public int _schm_length_0
    cdef public bint _schm_diskflag
    cdef public str _schm_path
    cdef FILE *_schm_file
    cdef public bint _schm_ramflag
    cdef public double[:,:] _schm_array
    cdef public double[:] wada
    cdef public int _wada_ndim
    cdef public int _wada_length
    cdef public int _wada_length_0
    cdef public bint _wada_diskflag
    cdef public str _wada_path
    cdef FILE *_wada_file
    cdef public bint _wada_ramflag
    cdef public double[:,:] _wada_array
    cdef public double[:] qdb
    cdef public int _qdb_ndim
    cdef public int _qdb_length
    cdef public int _qdb_length_0
    cdef public bint _qdb_diskflag
    cdef public str _qdb_path
    cdef FILE *_qdb_file
    cdef public bint _qdb_ramflag
    cdef public double[:,:] _qdb_array
    cdef public double[:] qib1
    cdef public int _qib1_ndim
    cdef public int _qib1_length
    cdef public int _qib1_length_0
    cdef public bint _qib1_diskflag
    cdef public str _qib1_path
    cdef FILE *_qib1_file
    cdef public bint _qib1_ramflag
    cdef public double[:,:] _qib1_array
    cdef public double[:] qib2
    cdef public int _qib2_ndim
    cdef public int _qib2_length
    cdef public int _qib2_length_0
    cdef public bint _qib2_diskflag
    cdef public str _qib2_path
    cdef FILE *_qib2_file
    cdef public bint _qib2_ramflag
    cdef public double[:,:] _qib2_array
    cdef public double[:] qbb
    cdef public int _qbb_ndim
    cdef public int _qbb_length
    cdef public int _qbb_length_0
    cdef public bint _qbb_diskflag
    cdef public str _qbb_path
    cdef FILE *_qbb_file
    cdef public bint _qbb_ramflag
    cdef public double[:,:] _qbb_array
    cdef public double q
    cdef public int _q_ndim
    cdef public int _q_length
    cdef public bint _q_diskflag
    cdef public str _q_path
    cdef FILE *_q_file
    cdef public bint _q_ramflag
    cdef public double[:] _q_array
    cpdef openfiles(self, int idx):
        if self._nkor_diskflag:
            self._nkor_file = fopen(str(self._nkor_path), "rb+")
            fseek(self._nkor_file, idx*self._nkor_length*8, SEEK_SET)
        if self._tkor_diskflag:
            self._tkor_file = fopen(str(self._tkor_path), "rb+")
            fseek(self._tkor_file, idx*self._tkor_length*8, SEEK_SET)
        if self._et0_diskflag:
            self._et0_file = fopen(str(self._et0_path), "rb+")
            fseek(self._et0_file, idx*self._et0_length*8, SEEK_SET)
        if self._evpo_diskflag:
            self._evpo_file = fopen(str(self._evpo_path), "rb+")
            fseek(self._evpo_file, idx*self._evpo_length*8, SEEK_SET)
        if self._nbes_diskflag:
            self._nbes_file = fopen(str(self._nbes_path), "rb+")
            fseek(self._nbes_file, idx*self._nbes_length*8, SEEK_SET)
        if self._evi_diskflag:
            self._evi_file = fopen(str(self._evi_path), "rb+")
            fseek(self._evi_file, idx*self._evi_length*8, SEEK_SET)
        if self._evb_diskflag:
            self._evb_file = fopen(str(self._evb_path), "rb+")
            fseek(self._evb_file, idx*self._evb_length*8, SEEK_SET)
        if self._wgtf_diskflag:
            self._wgtf_file = fopen(str(self._wgtf_path), "rb+")
            fseek(self._wgtf_file, idx*self._wgtf_length*8, SEEK_SET)
        if self._schm_diskflag:
            self._schm_file = fopen(str(self._schm_path), "rb+")
            fseek(self._schm_file, idx*self._schm_length*8, SEEK_SET)
        if self._wada_diskflag:
            self._wada_file = fopen(str(self._wada_path), "rb+")
            fseek(self._wada_file, idx*self._wada_length*8, SEEK_SET)
        if self._qdb_diskflag:
            self._qdb_file = fopen(str(self._qdb_path), "rb+")
            fseek(self._qdb_file, idx*self._qdb_length*8, SEEK_SET)
        if self._qib1_diskflag:
            self._qib1_file = fopen(str(self._qib1_path), "rb+")
            fseek(self._qib1_file, idx*self._qib1_length*8, SEEK_SET)
        if self._qib2_diskflag:
            self._qib2_file = fopen(str(self._qib2_path), "rb+")
            fseek(self._qib2_file, idx*self._qib2_length*8, SEEK_SET)
        if self._qbb_diskflag:
            self._qbb_file = fopen(str(self._qbb_path), "rb+")
            fseek(self._qbb_file, idx*self._qbb_length*8, SEEK_SET)
        if self._q_diskflag:
            self._q_file = fopen(str(self._q_path), "rb+")
            fseek(self._q_file, idx*8, SEEK_SET)
    cpdef inline closefiles(self):
        if self._et0_diskflag:
            fclose(self._et0_file)
        if self._evb_diskflag:
            fclose(self._evb_file)
        if self._evi_diskflag:
            fclose(self._evi_file)
        if self._evpo_diskflag:
            fclose(self._evpo_file)
        if self._nbes_diskflag:
            fclose(self._nbes_file)
        if self._nkor_diskflag:
            fclose(self._nkor_file)
        if self._q_diskflag:
            fclose(self._q_file)
        if self._qbb_diskflag:
            fclose(self._qbb_file)
        if self._qdb_diskflag:
            fclose(self._qdb_file)
        if self._qib1_diskflag:
            fclose(self._qib1_file)
        if self._qib2_diskflag:
            fclose(self._qib2_file)
        if self._schm_diskflag:
            fclose(self._schm_file)
        if self._tkor_diskflag:
            fclose(self._tkor_file)
        if self._wada_diskflag:
            fclose(self._wada_file)
        if self._wgtf_diskflag:
            fclose(self._wgtf_file)
    cpdef inline savedata(self, int idx):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        if self._nkor_diskflag:
            fwrite(&self.nkor[0], 8, self._nkor_length, self._nkor_file)
        elif self._nkor_ramflag:
            for jdx0 in range(self._nkor_length_0):
                self._nkor_array[idx,jdx0] = self.nkor[jdx0]
        if self._tkor_diskflag:
            fwrite(&self.tkor[0], 8, self._tkor_length, self._tkor_file)
        elif self._tkor_ramflag:
            for jdx0 in range(self._tkor_length_0):
                self._tkor_array[idx,jdx0] = self.tkor[jdx0]
        if self._et0_diskflag:
            fwrite(&self.et0[0], 8, self._et0_length, self._et0_file)
        elif self._et0_ramflag:
            for jdx0 in range(self._et0_length_0):
                self._et0_array[idx,jdx0] = self.et0[jdx0]
        if self._evpo_diskflag:
            fwrite(&self.evpo[0], 8, self._evpo_length, self._evpo_file)
        elif self._evpo_ramflag:
            for jdx0 in range(self._evpo_length_0):
                self._evpo_array[idx,jdx0] = self.evpo[jdx0]
        if self._nbes_diskflag:
            fwrite(&self.nbes[0], 8, self._nbes_length, self._nbes_file)
        elif self._nbes_ramflag:
            for jdx0 in range(self._nbes_length_0):
                self._nbes_array[idx,jdx0] = self.nbes[jdx0]
        if self._evi_diskflag:
            fwrite(&self.evi[0], 8, self._evi_length, self._evi_file)
        elif self._evi_ramflag:
            for jdx0 in range(self._evi_length_0):
                self._evi_array[idx,jdx0] = self.evi[jdx0]
        if self._evb_diskflag:
            fwrite(&self.evb[0], 8, self._evb_length, self._evb_file)
        elif self._evb_ramflag:
            for jdx0 in range(self._evb_length_0):
                self._evb_array[idx,jdx0] = self.evb[jdx0]
        if self._wgtf_diskflag:
            fwrite(&self.wgtf[0], 8, self._wgtf_length, self._wgtf_file)
        elif self._wgtf_ramflag:
            for jdx0 in range(self._wgtf_length_0):
                self._wgtf_array[idx,jdx0] = self.wgtf[jdx0]
        if self._schm_diskflag:
            fwrite(&self.schm[0], 8, self._schm_length, self._schm_file)
        elif self._schm_ramflag:
            for jdx0 in range(self._schm_length_0):
                self._schm_array[idx,jdx0] = self.schm[jdx0]
        if self._wada_diskflag:
            fwrite(&self.wada[0], 8, self._wada_length, self._wada_file)
        elif self._wada_ramflag:
            for jdx0 in range(self._wada_length_0):
                self._wada_array[idx,jdx0] = self.wada[jdx0]
        if self._qdb_diskflag:
            fwrite(&self.qdb[0], 8, self._qdb_length, self._qdb_file)
        elif self._qdb_ramflag:
            for jdx0 in range(self._qdb_length_0):
                self._qdb_array[idx,jdx0] = self.qdb[jdx0]
        if self._qib1_diskflag:
            fwrite(&self.qib1[0], 8, self._qib1_length, self._qib1_file)
        elif self._qib1_ramflag:
            for jdx0 in range(self._qib1_length_0):
                self._qib1_array[idx,jdx0] = self.qib1[jdx0]
        if self._qib2_diskflag:
            fwrite(&self.qib2[0], 8, self._qib2_length, self._qib2_file)
        elif self._qib2_ramflag:
            for jdx0 in range(self._qib2_length_0):
                self._qib2_array[idx,jdx0] = self.qib2[jdx0]
        if self._qbb_diskflag:
            fwrite(&self.qbb[0], 8, self._qbb_length, self._qbb_file)
        elif self._qbb_ramflag:
            for jdx0 in range(self._qbb_length_0):
                self._qbb_array[idx,jdx0] = self.qbb[jdx0]
        if self._q_diskflag:
            fwrite(&self.q, 8, 1, self._q_file)
        elif self._q_ramflag:
            self._q_array[idx] = self.q
@cython.final
cdef class AideSequences(object):
    cdef public double temp
    cdef public int _temp_ndim
    cdef public int _temp_length
    cdef public double[:] sfa
    cdef public int _sfa_ndim
    cdef public int _sfa_length
    cdef public int _sfa_length_0
    cdef public double[:] exz
    cdef public int _exz_ndim
    cdef public int _exz_length
    cdef public int _exz_length_0
    cdef public double[:] bvl
    cdef public int _bvl_ndim
    cdef public int _bvl_length
    cdef public int _bvl_length_0
    cdef public double[:] mvl
    cdef public int _mvl_ndim
    cdef public int _mvl_length
    cdef public int _mvl_length_0
    cdef public double[:] rvl
    cdef public int _rvl_ndim
    cdef public int _rvl_length
    cdef public int _rvl_length_0
    cdef public double epw
    cdef public int _epw_ndim
    cdef public int _epw_length
@cython.final
cdef class Model(object):
    cdef public ControlParameters control
    cdef public DerivedParameters derived
    cdef public StateSequences states
    cdef public InputSequences inputs
    cdef public FluxSequences fluxes
    cdef public AideSequences aides
    cdef public StateSequences old_states
    cdef public StateSequences new_states
    cpdef inline void doit(self, int idx):
        self.loaddata(idx)
        self.run(idx)
        self.new2old()
        self.savedata(idx)
    cpdef inline void openfiles(self, int idx):
        self.states.openfiles(idx)
        self.inputs.openfiles(idx)
        self.fluxes.openfiles(idx)
    cpdef inline void closefiles(self):
        self.states.closefiles()
        self.inputs.closefiles()
        self.fluxes.closefiles()
    cpdef inline void loaddata(self, int idx):
        self.inputs.loaddata(idx)
    cpdef inline void savedata(self, int idx):
        self.states.savedata(idx)
        self.fluxes.savedata(idx)
    cpdef inline void new2old(self):
        cdef int jdx0, jdx1, jdx2, jdx3, jdx4, jdx5
        for jdx0 in range(self.states._bowa_length_0):
            self.old_states.bowa[jdx0] = self.new_states.bowa[jdx0]
        for jdx0 in range(self.states._inzp_length_0):
            self.old_states.inzp[jdx0] = self.new_states.inzp[jdx0]
        self.old_states.qbga = self.new_states.qbga
        self.old_states.qbgz = self.new_states.qbgz
        self.old_states.qdga = self.new_states.qdga
        self.old_states.qdgz = self.new_states.qdgz
        self.old_states.qiga1 = self.new_states.qiga1
        self.old_states.qiga2 = self.new_states.qiga2
        self.old_states.qigz1 = self.new_states.qigz1
        self.old_states.qigz2 = self.new_states.qigz2
        for jdx0 in range(self.states._waes_length_0):
            self.old_states.waes[jdx0] = self.new_states.waes[jdx0]
        for jdx0 in range(self.states._wats_length_0):
            self.old_states.wats[jdx0] = self.new_states.wats[jdx0]
        for jdx0 in range(self.states._wrel_length_0):
            self.old_states.wrel[jdx0] = self.new_states.wrel[jdx0]
    cpdef inline void calc_evpo(self, int idx):
        cdef int k
        for k in range(self.control.nhru):
            self.fluxes.evpo[k] = (self.control.fln[self.control.lnk[k]-1, self.derived.moy[idx]]
                          * self.fluxes.et0[k])
    cpdef inline void calc_qbgz(self):
        cdef int k
        self.states.qbgz = 0.
        for k in range(self.control.nhru):
            self.states.qbgz += self.control.fhru[k]*self.fluxes.qbb[k]
    cpdef inline void calc_qigz2(self):
        cdef int k
        self.states.qigz2 = 0.
        for k in range(self.control.nhru):
            self.states.qigz2 += self.control.fhru[k]*self.fluxes.qib2[k]
    cpdef inline void calc_qdb(self):
        cdef int k
        for k in range(self.control.nhru):
            if ((self.control.lnk[k] != WASSER) and (self.control.lnk[k] != VERS)
              and (self.control.nfk[k] > 0.)):
                if self.states.bowa[k] < self.control.nfk[k]:
                    self.aides.sfa[k] = (
                        (1.-self.states.bowa[k]/self.control.nfk[k])**(1./(self.control.bsf[k]+1.)) -
                        (self.fluxes.wada[k]/((self.control.bsf[k]+1.)*self.control.nfk[k])))
                else:
                    self.aides.sfa[k] = 0.
                self.aides.exz[k] = self.states.bowa[k]+self.fluxes.wada[k]-self.control.nfk[k]
                self.fluxes.qdb[k] = self.aides.exz[k]
                if self.aides.sfa[k] > 0.:
                    self.fluxes.qdb[k] += self.aides.sfa[k]**(self.control.bsf[k]+1.)*self.control.nfk[k]
                self.fluxes.qdb[k] = max(self.fluxes.qdb[k], 0.)
            else:
                self.fluxes.qdb[k] = self.fluxes.wada[k]
    cpdef inline void calc_qib1(self):
        cdef int k
        for k in range(self.control.nhru):
            if ((self.control.lnk[k] != WASSER) and (self.control.lnk[k] != VERS)
                    and (self.states.bowa[k] > self.derived.wb[k])):
                self.fluxes.qib1[k] = self.control.dmin[k]*(self.states.bowa[k]/self.control.nfk[k])
            else:
                self.fluxes.qib1[k] = 0.
    cpdef inline void calc_wada_waes(self):
        cdef int k
        for k in range(self.control.nhru):
            if self.control.lnk[k] != WASSER:
                self.states.waes[k] += self.fluxes.nbes[k]
                self.fluxes.wada[k] = max(self.states.waes[k]-self.control.pwmax[k]*self.states.wats[k], 0.)
                self.states.waes[k] -= self.fluxes.wada[k]
            else:
                self.states.waes[k] = 0.
                self.fluxes.wada[k] = self.fluxes.nbes[k]
    cpdef inline void calc_qigz1(self):
        cdef int k
        self.states.qigz1 = 0.
        for k in range(self.control.nhru):
            self.states.qigz1 += self.control.fhru[k]*self.fluxes.qib1[k]
    cpdef inline void calc_et0(self):
        cdef int k
        for k in range(self.control.nhru):
            self.fluxes.et0[k] = (self.control.ke[k]*(((8.64*self.inputs.glob+93.*self.control.kf[k]) *
                                      (self.fluxes.tkor[k]+22.)) /
                                     (165.*(self.fluxes.tkor[k]+123.) *
                                      (1.+0.00019*min(self.control.hnn[k], 600.)))))
    cpdef inline void calc_q(self):
        cdef int k
        self.fluxes.q = self.states.qbga+self.states.qiga1+self.states.qiga2+self.states.qdga
        self.aides.epw = 0.
        for k in range(self.control.nhru):
            if self.control.lnk[k] == WASSER:
                self.aides.epw += self.control.fhru[k]*self.fluxes.evi[k]
        if self.fluxes.q > self.aides.epw:
            self.fluxes.q -= self.aides.epw
        else:
            for k in range(self.control.nhru):
                if self.control.lnk[k] == WASSER:
                    self.fluxes.evi[k] *= self.fluxes.q/self.aides.epw
            self.fluxes.q = 0.
    cpdef inline void calc_tkor(self):
        cdef int k
        for k in range(self.control.nhru):
            self.fluxes.tkor[k] = self.control.kt[k] + self.inputs.teml
    cpdef inline void calc_qib2(self):
        cdef int k
        for k in range(self.control.nhru):
            if ((self.control.lnk[k] != WASSER) and (self.control.lnk[k] != VERS)
              and (self.states.bowa[k] > self.derived.wz[k]) and (self.control.nfk[k] > self.derived.wz[k])):
                self.fluxes.qib2[k] = ((self.control.dmax[k]-self.control.dmin[k]) *
                               ((self.states.bowa[k]-self.derived.wz[k]) /
                                (self.control.nfk[k]-self.derived.wz[k]))**1.5)
            else:
                self.fluxes.qib2[k] = 0.
    cpdef inline void calc_evb(self):
        cdef int k
        for k in range(self.control.nhru):
            if ((self.control.lnk[k] != WASSER) and (self.control.lnk[k] != VERS) and
                    (self.control.nfk[k] > 0.)):
                self.aides.temp = exp(-self.control.grasref_r *
                                          self.states.bowa[k]/self.control.nfk[k])
                self.fluxes.evb[k] = ((self.fluxes.evpo[k]-self.fluxes.evi[k]) * (1.-self.aides.temp) /
                              (1.+self.aides.temp-2.*exp(-self.control.grasref_r)))
            else:
                self.fluxes.evb[k] = 0.
    cpdef inline void calc_nkor(self):
        cdef int k
        for k in range(self.control.nhru):
            self.fluxes.nkor[k] = self.control.kg[k] * self.inputs.nied
    cpdef inline void calc_qbga(self):
        if self.derived.kb <= 0.:
            self.new_states.qbga = self.new_states.qbgz
        elif self.derived.kb > 1e200:
            self.new_states.qbga = self.old_states.qbga+self.new_states.qbgz-self.old_states.qbgz
        else:
            self.aides.temp = (1.-exp(-1./self.derived.kb))
            self.new_states.qbga = (self.old_states.qbga +
                       (self.old_states.qbgz-self.old_states.qbga)*self.aides.temp +
                       (self.new_states.qbgz-self.old_states.qbgz)*(1.-self.derived.kb*self.aides.temp))
    cpdef inline void calc_qbb(self):
        cdef int k
        for k in range(self.control.nhru):
            if ((self.control.lnk[k] != WASSER) and (self.control.lnk[k] != VERS)
              and (self.states.bowa[k] > self.derived.wb[k]) and (self.control.nfk[k] > 0.)):
                self.fluxes.qbb[k] = self.control.beta[k]*(self.states.bowa[k]-self.derived.wb[k])
            else:
                self.fluxes.qbb[k] = 0.
    cpdef inline void calc_qiga2(self):
        if self.derived.ki2 <= 0.:
            self.new_states.qiga2 = self.new_states.qigz2
        elif self.derived.ki2 > 1e200:
            self.new_states.qiga2 = self.old_states.qiga2+self.new_states.qigz2-self.old_states.qigz2
        else:
            self.aides.temp = (1.-exp(-1./self.derived.ki2))
            self.new_states.qiga2 = (self.old_states.qiga2 +
                        (self.old_states.qigz2-self.old_states.qiga2)*self.aides.temp +
                        (self.new_states.qigz2-self.old_states.qigz2)*(1.-self.derived.ki2*self.aides.temp))
    cpdef inline void calc_schm_wats(self):
        cdef int k
        for k in range(self.control.nhru):
            if self.control.lnk[k] != WASSER:
                if self.fluxes.tkor[k] < self.control.tgr[k]:
                    self.states.wats[k] += self.fluxes.nbes[k]
                self.fluxes.schm[k] = min(self.fluxes.wgtf[k], self.states.wats[k])
                self.states.wats[k] -= self.fluxes.schm[k]
            else:
                self.states.wats[k] = 0.
                self.fluxes.schm[k] = 0.
    cpdef inline void calc_qiga1(self):
        if self.derived.ki1 <= 0.:
            self.new_states.qiga1 = self.new_states.qigz1
        elif self.derived.ki1 > 1e200:
            self.new_states.qiga1 = self.old_states.qiga1+self.new_states.qigz1-self.old_states.qigz1
        else:
            self.aides.temp = (1.-exp(-1./self.derived.ki1))
            self.new_states.qiga1 = (self.old_states.qiga1 +
                        (self.old_states.qigz1-self.old_states.qiga1)*self.aides.temp +
                        (self.new_states.qigz1-self.old_states.qigz1)*(1.-self.derived.ki1*self.aides.temp))
    cpdef inline void calc_qdga(self):
        if self.derived.kd <= 0.:
            self.new_states.qdga = self.new_states.qdgz
        elif self.derived.kd > 1e200:
            self.new_states.qdga = self.old_states.qdga+self.new_states.qdgz-self.old_states.qdgz
        else:
            self.aides.temp = (1.-exp(-1./self.derived.kd))
            self.new_states.qdga = (self.old_states.qdga +
                       (self.old_states.qdgz-self.old_states.qdga)*self.aides.temp +
                       (self.new_states.qdgz-self.old_states.qdgz)*(1.-self.derived.kd*self.aides.temp))
    cpdef inline void calc_nbes_inzp(self, int idx):
        cdef int k
        for k in range(self.control.nhru):
            if self.control.lnk[k] != WASSER:
                self.fluxes.nbes[k] = \
                    max(self.fluxes.nkor[k]+self.states.inzp[k] -
                        self.derived.kinz[self.control.lnk[k]-1, self.derived.moy[idx]], 0.)
                self.states.inzp[k] += self.fluxes.nkor[k]-self.fluxes.nbes[k]
            else:
                self.fluxes.nbes[k] = self.fluxes.nkor[k]
                self.states.inzp[k] = 0.
    cpdef inline void calc_evi_inzp(self):
        cdef int k
        for k in range(self.control.nhru):
            if self.control.lnk[k] != WASSER:
                self.fluxes.evi[k] = min(self.fluxes.evpo[k], self.states.inzp[k])
                self.states.inzp[k] -= self.fluxes.evi[k]
            else:
                self.fluxes.evi[k] = self.fluxes.evpo[k]
    cpdef inline void calc_bowa(self):
        cdef int k
        for k in range(self.control.nhru):
            if (self.control.lnk[k] != WASSER) and (self.control.lnk[k] != VERS):
                self.aides.bvl[k] = (self.fluxes.evb[k] +
                              self.fluxes.qbb[k]+self.fluxes.qib1[k]+self.fluxes.qib2[k]+self.fluxes.qdb[k])
                self.aides.mvl[k] = self.states.bowa[k]+self.fluxes.wada[k]
                if self.aides.bvl[k] > self.aides.mvl[k]:
                    self.aides.rvl[k] = self.aides.mvl[k]/self.aides.bvl[k]
                    self.fluxes.evb[k] *= self.aides.rvl[k]
                    self.fluxes.qbb[k] *= self.aides.rvl[k]
                    self.fluxes.qib1[k] *= self.aides.rvl[k]
                    self.fluxes.qib2[k] *= self.aides.rvl[k]
                    self.fluxes.qdb[k] *= self.aides.rvl[k]
                    self.states.bowa[k] = 0.
                else:
                    self.states.bowa[k] = self.aides.mvl[k]-self.aides.bvl[k]
            else:
                self.states.bowa[k] = 0.
    cpdef inline void calc_wgtf(self):
        cdef int k
        for k in range(self.control.nhru):
            if self.control.lnk[k] != WASSER:
                self.fluxes.wgtf[k] = (
                  max(self.control.gtf[k]*(self.fluxes.tkor[k]-self.control.treft[k]), 0) +
                  max(self.control.cpwasser/self.control.rschmelz*(self.fluxes.tkor[k]-self.control.trefn[k]), 0.)
                  )
            else:
                self.fluxes.wgtf[k] = 0.
    cpdef inline void calc_qdgz(self):
        cdef int k
        self.states.qdgz = 0.
        for k in range(self.control.nhru):
            self.states.qdgz += self.control.fhru[k]*self.fluxes.qdb[k]
    cpdef inline void run(self, int idx):
        self.calc_nkor()
        self.calc_tkor()
        self.calc_et0()
        self.calfln()
