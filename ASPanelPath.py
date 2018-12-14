#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) Yves Secretan
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
#
# generated by wxGlade 0.8.3 on Thu Nov 29 09:28:39 2018
#

"""
"""

if __name__ == "__main__":
    import os
    import sys
    supPath = r'E:\bld-1810\H2D2-tools\script'
    if os.path.isdir(supPath) and supPath not in sys.path: sys.path.append(supPath)

import logging    

import wx

from ASPanelPathPlot import ASPanelPathPlot
from ASPanelPathTree import ASPanelPathTree

LOGGER = logging.getLogger("INRS.ASur.panel.path")

class ASPanelPath(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        
        self.SetSize((800, 600))
        self.sptMain = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_3D|wx.SP_BORDER)
        self.pnlCtrl = ASPanelPathTree(self.sptMain, wx.ID_ANY, cbOnTreeCheck=self.onTreeCheck)
        self.pnlPath = ASPanelPathPlot(self.sptMain, wx.ID_ANY)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.sptMain.SetMinSize((-1,-1))
        self.sptMain.SetSashGravity(0.0)
        self.sptMain.SetMinimumPaneSize(100)
        self.sptMain.SetSashPosition(200)

    def __do_layout(self):
        szrMain = wx.BoxSizer(wx.VERTICAL)
        self.sptMain.SplitVertically(self.pnlCtrl, self.pnlPath)
        szrMain.Add(self.sptMain, 1, wx.EXPAND, 0)
        self.SetSizer(szrMain)
        szrMain.Fit(self)
        self.Layout()

    def __getattr__(self, name):
        """
        Transfer all unknown calls to the pnlPath
        """
        try:
            return getattr(self.pnlPath, name)
        except AttributeError as e:
            raise

    def onTreeCheck(self):
        try:
            plumes = self.pnlCtrl.getCheckedItems()
        except AttributeError:  # provision for empty tree
            plumes = []
        self.pnlPath.plotPlumes(plumes)
    
    def plotPaths(self, asurMdl, plumes, dtini, dtfin, dtmax):
        self.pnlPath.plotPlumes(plumes)
        self.pnlCtrl.fillTree  (plumes)

    def setParameters(self, prm):
        self.pnlPath.params = prm
        self.onTreeCheck()
        
if __name__ == "__main__":
    class MyDialogBox(wx.Dialog):
        def __init__(self, *args, **kwargs):
            style = 0
            style |= wx.CAPTION
            style |= wx.CLOSE_BOX
            style |= wx.MINIMIZE_BOX
            style |= wx.MAXIMIZE_BOX
            style |= wx.SYSTEM_MENU
            style |= wx.RESIZE_BORDER
            style |= wx.CLIP_CHILDREN
            kwargs["style"] = style
            super(MyDialogBox, self).__init__(*args, **kwargs)

            self.pnl = ASPanelPath(self)

            self.btn_cancel = wx.Button(self, wx.ID_CANCEL, "")
            self.btn_ok     = wx.Button(self, wx.ID_OK, "")

            szr_frm = wx.BoxSizer(wx.VERTICAL)
            szr_frm.Add(self.pnl, 1, wx.EXPAND, 0)

            szr_btn = wx.BoxSizer(wx.HORIZONTAL)
            szr_btn.Add(self.btn_cancel,0, wx.EXPAND, 0)
            szr_btn.Add(self.btn_ok,    0, wx.EXPAND, 0)
            szr_frm.Add(szr_btn, 0, wx.EXPAND, 0)

            self.SetSizer(szr_frm)
            self.SetSize((600, 800))
            self.Layout()

            # self.pnl.pnlCtrl.fillTree( { "1" : ("11", "12", "13", "14"), "2" : ("21", "22", "23")} )

        def onBtnApply(self, event):
            print('onBtnApply', event.overflows)

    class MyApp(wx.App):
        def OnInit(self):
            dlg = MyDialogBox(None)
            if dlg.ShowModal() == wx.ID_OK:
                print('OK')
            return True

    app = MyApp(False)
    app.MainLoop()
