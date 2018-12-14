#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
# --- Institut National de la Recherche Scientifique (INRS)
# ---
# --- Licensed under the Apache License, Version 2.0 (the "License");
# --- you may not use this file except in compliance with the License.
# --- You may obtain a copy of the License at
# ---
# ---     http://www.apache.org/licenses/LICENSE-2.0
# ---
# --- Unless required by applicable law or agreed to in writing, software
# --- distributed under the License is distributed on an "AS IS" BASIS,
# --- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# --- See the License for the specific language governing permissions and
# --- limitations under the License.
#************************************************************************

"""
Events emmited by the class
    ASEvents.ASEventMotion on mouse motion

"""

import sys
if 'matplotlib' not in sys.modules:
    import matplotlib
    matplotlib.use('WXAgg') # do this before importing pyplot

from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure                 import Figure

import wx

from ASEvents import ASEventMotion

class ASPanelWxMPL(wx.Panel):
    """
    Encapsulate a matplotlib Figure and its toolbar
    """
    DEFAULT_SIZE = (6.0, 3.70)
    DEFAULT_DPI  = 96
    
    def __init__(self, *args, **kwargs):
        super(ASPanelWxMPL, self).__init__(*args)

        self.figure = kwargs.pop('figure', None)
        if not self.figure:
            self.figure = Figure(ASPanelWxMPL.DEFAULT_SIZE, ASPanelWxMPL.DEFAULT_DPI)

        self.canvas  = FigureCanvasWxAgg(self, -1, self.figure)
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)
        self.toolbar.Hide()

        self.__set_size()

        self.Bind(wx.EVT_SIZE, self.on_resize)
        #self.Bind(wx.EVT_PAINT, self.on_redraw)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        #self.canvas.mpl_connect('button_press_event',  self.on_mouse_click)
        #self.canvas.mpl_connect('button_press_event',  self.on_pick_event)

    def __set_size(self):
        self.canvas.SetSize(self.GetSize())

    def __getattr__(self, name):
        attr = getattr(self.figure, name)
        if hasattr(attr, '__call__'):
            def newfunc(*args, **kwargs):
                wx.BeginBusyCursor()
                result = attr(*args, **kwargs)
                wx.EndBusyCursor()
                return result
            return newfunc
        else:
            return attr

    def get_figure(self):
        return self.figure

    def get_toolbar(self):
        return self.toolbar

    def resetToolbar(self):
        tb = self.toolbar
        if tb._active == 'PAN':
            tb.pan('off')
            tb.ToggleTool(tb.wx_ids['Pan'],  False)
        if tb._active == 'ZOOM':
            tb.ToggleTool(tb.wx_ids['Zoom'], False)
            tb.zoom('off')

    def redraw(self):
        self.canvas.draw()

    def show(self, b):
        pass

    def on_mouse_move(self, evt):
        if (evt.inaxes is None): return
        if (evt.xdata  is None): return
        wx.PostEvent(self, ASEventMotion(self.GetId(), xy=(evt.xdata, evt.ydata)))

    def on_pick_event(self, evt):
        if (evt.inaxes is None): return
        if (evt.xdata  is None): return
        #thisline = event.artist
        #xdata, ydata = thisline.get_data()
        #ind = event.ind
        #print('on pick line:', zip(xdata[ind], ydata[ind]))
        #self.cb_on_pick_event(evt.xdata, evt.ydata)

    def on_btn_reset(self):
        self.toolbar.home()

    def on_btn_backward(self):
        self.toolbar.back()

    def on_btn_forward(self):
        self.toolbar.forward()

    def on_btn_pan(self, enable):
        self.toolbar.pan()

    def on_btn_zoom_to_rectangle(self, enable):
        self.toolbar.zoom()

    def on_resize(self, *args, **kwargs):
        self.__set_size()

    def on_redraw(self, *args, **kwargs):
        self.canvas.draw()
