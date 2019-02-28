#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2018
# --- Institut National de la Recherche Scientifique (INRS)
# --- Copyright (c) Yves Secretan 2018
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

import wx

zones = [
"INRS",
"INRS.ASModel",
"INRS.ASModel.ASModel",
"INRS.ASModel.overflow",
"INRS.ASModel.plume",
"INRS.ASModel.river",
"INRS.ASModel.station",
"INRS.ASModel.tide",
"INRS.ASur",
"INRS.ASur.frame",
"INRS.ASur.panel.path",
"INRS.ASur.panel.path.plot",
"INRS.ASur.panel.path.tree",
"INRS.ASur.panel.plot",
"INRS.ASur.panel.scenario",
"INRS.H2D2",
"INRS.H2D2.Tools",
"INRS.H2D2.Tools.ImageProcessor",
"INRS.H2D2.Tools.ImageProcessor.GDAL",
]

levels = [
"error",
"warning",
"info",
"debug",
"trace",
]

class ASDlgLogZone(wx.Dialog):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        super(ASDlgLogZone, self).__init__(*args, **kwds)

        self.szr_zne_staticbox = wx.StaticBox(self, wx.ID_ANY, "Zone")
        self.szr_lvl_staticbox = wx.StaticBox(self, wx.ID_ANY, "Level")

        self.cbx_zne = wx.ComboBox (self, wx.ID_ANY, choices=zones,  style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cbx_lvl = wx.ComboBox (self, wx.ID_ANY, choices=levels, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.btn_ok     = wx.Button(self, wx.ID_OK, "")
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_btn_ok,     self.btn_ok)
        self.Bind(wx.EVT_BUTTON, self.on_btn_cancel, self.btn_cancel)

        self.cb = None

    def __set_properties(self):
        self.SetTitle("Logging zone")
        self.cbx_zne.SetSelection(0)
        self.cbx_lvl.SetSelection(0)
        self.btn_ok.SetDefault()

    def __do_layout(self):
        szr_main = wx.BoxSizer(wx.VERTICAL)
        szr_btn  = wx.BoxSizer(wx.HORIZONTAL)
        szr_dta  = wx.BoxSizer(wx.VERTICAL)
        szr_zne  = wx.StaticBoxSizer(self.szr_zne_staticbox,  wx.VERTICAL)
        szr_lvl  = wx.StaticBoxSizer(self.szr_lvl_staticbox,  wx.VERTICAL)

        szr_zne.Add(self.cbx_zne, 1, wx.EXPAND, 0)
        szr_lvl.Add(self.cbx_lvl, 1, wx.EXPAND, 0)

        szr_dta.Add(szr_zne, 1, wx.EXPAND, 0)
        szr_dta.Add(szr_lvl, 1, wx.EXPAND, 0)
        szr_main.Add(szr_dta, 0, 0, 0)

        szr_btn.AddStretchSpacer(prop=4)
        szr_btn.Add(self.btn_ok, 0, wx.EXPAND, 0)
        szr_btn.Add(self.btn_cancel, 0, wx.EXPAND, 0)
        szr_main.Add(szr_btn, 1, wx.EXPAND, 0)

        self.SetSizer(szr_main)
        szr_main.Fit(self)
        self.Layout()

    def getValues(self):
        return self.cbx_zne.GetValue(), self.cbx_lvl.GetValue()

    def setValues(self, zone, level):
        pass

    def on_btn_ok(self, event):
        event.Skip()
        #self.EndModal(wx.ID_OK)

    def on_btn_cancel(self, event):
        event.Skip()
        #self.EndModal(wx.ID_CANCEL)

if __name__ == "__main__":
    class MyApp(wx.App):
        def OnInit(self):
            dlg = ASDlgLogZone(None, wx.ID_ANY, "")
            if dlg.ShowModal() == wx.ID_OK:
                print(dlg.getValues())
            return True

    app = MyApp(0)
    app.MainLoop()
