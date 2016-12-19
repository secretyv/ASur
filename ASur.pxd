# -*- coding: utf-8 -*-

# This is an automatically generated file.
# Manual changes will be overwritten without warning!

import cython

cimport datetime
cimport ASModel

# cdef class ASur(wx.Frame):
    # # ---  Attributes
    # cdef public btn_apply
    # cdef public ctl_dfin
    # cdef public ctl_dini
    # cdef public ctl_tfin
    # cdef public ctl_tini
    # cdef public lst_pnts
    # cdef public menubar
    # cdef public mnu_file
    # cdef public mnu_file_quit
    # cdef public mnu_help
    # cdef public mnu_help_about
    # cdef public pnl_wx
    # cdef public splt
    # cdef public spn_tfin
    # cdef public spn_tini
    # cdef public ssh_lft
    # cdef public ssh_rht
    # cdef public statusbar
    # cdef public txt_tfin
    # cdef public txt_tini

    # # ---  Methods
    # @cython.locals (statusbar_fields = list)
    # cdef                    __set_properties  (ASur self)
    # cdef                    __do_layout       (ASur self)
    # cdef                    __create_menu_bar (ASur self)
    # @cython.locals (d = str, t = str, dt = datetime.datetime)
    # cdef datetime.datetime  __getTIni         (ASur self)
    # @cython.locals (d = str, t = str, dt = datetime.datetime)
    # cdef datetime.datetime  __getTFin         (ASur self)
    # @cython.locals (res = list)
    # cdef list               __getPoints       (ASur self, object item=?)
    # cdef tuple              __getPlotData     (ASur self, datetime.datetime dtini, datetime.datetime dtfin, list pts)
    # cdef                    __plotClearPlot   (ASur self)
    # @cython.locals (kwargs = dict)
    # cdef                    __plotTide        (ASur self, datetime.datetime dtmin, datetime.datetime dtmax)
    # @cython.locals (kwargs = dict)
    # cdef                    __plotPoints      (ASur self, object data, datetime.datetime dtmin, datetime.datetime dtmax, bboxTide)
    # @cython.locals (kwargs = dict)
    # cdef                    __plotLimits      (ASur self, object data, datetime.datetime dtmin, datetime.datetime dtmax)
    # cdef                    __plot            (ASur self, object data, datetime.datetime dtmin, datetime.datetime dtmax)
    # cdef                    on_btn_apply      (ASur self, object event)
    # cdef                    on_btn_close      (ASur self, object event)
    # cdef                    on_btn_help       (ASur self, object event)
    # cdef                    cb_panel          (ASur self, str txt, object panel=?)

# cdef class PaBeauApp(wx.App):
    # cdef OnInit(PaBeauApp self)

cpdef main()
