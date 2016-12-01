# -*- coding: utf-8 -*-

# This is an automatically generated file.
# Manual changes will be overwritten without warning!

import cython

cimport datetime
cimport BBModel

# cdef class PaBeau(wx.Frame):
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
    # cdef                    __set_properties  (PaBeau self)
    # cdef                    __do_layout       (PaBeau self)
    # cdef                    __create_menu_bar (PaBeau self)
    # @cython.locals (d = str, t = str, dt = datetime.datetime)
    # cdef datetime.datetime  __getTIni         (PaBeau self)
    # @cython.locals (d = str, t = str, dt = datetime.datetime)
    # cdef datetime.datetime  __getTFin         (PaBeau self)
    # @cython.locals (res = list)
    # cdef list               __getPoints       (PaBeau self, object item=?)
    # cdef tuple              __getPlotData     (PaBeau self, datetime.datetime dtini, datetime.datetime dtfin, list pts)
    # cdef                    __plotClearPlot   (PaBeau self)
    # @cython.locals (kwargs = dict)
    # cdef                    __plotTide        (PaBeau self, datetime.datetime dtmin, datetime.datetime dtmax)
    # @cython.locals (kwargs = dict)
    # cdef                    __plotPoints      (PaBeau self, object data, datetime.datetime dtmin, datetime.datetime dtmax, bboxTide)
    # @cython.locals (kwargs = dict)
    # cdef                    __plotLimits      (PaBeau self, object data, datetime.datetime dtmin, datetime.datetime dtmax)
    # cdef                    __plot            (PaBeau self, object data, datetime.datetime dtmin, datetime.datetime dtmax)
    # cdef                    on_btn_apply      (PaBeau self, object event)
    # cdef                    on_btn_close      (PaBeau self, object event)
    # cdef                    on_btn_help       (PaBeau self, object event)
    # cdef                    cb_panel          (PaBeau self, str txt, object panel=?)

# cdef class PaBeauApp(wx.App):
    # cdef OnInit(PaBeauApp self)

cpdef main()
