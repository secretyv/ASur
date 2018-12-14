# -*- coding: utf-8 -*-

# This is an automatically generated file.
# Manual changes will be merged and conflicts marked!
#
# Generated by py2pxd_ version 0.0.3 on 2018-12-13 16:06:54

import cython
cimport datetime

cpdef bint         is_sequence     (object arg)

cdef class Overflow:
    cdef public str          name
    cdef public datetime.datetime tend
    cdef public list         tides
    cdef public datetime.datetime tini
    #
    @cython.locals (errLst = list, errMsg = str)
    cpdef str          isValid         (Overflow self)

@cython.locals (dt = datetime.datetime, item = Overflow)
cpdef              main            ()

