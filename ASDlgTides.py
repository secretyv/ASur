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
#
# generated by wxGlade 0.7.2 on Sat Oct 01 09:03:16 2016
#

"""
Boite de dialog de choix des marées
"""

import wx

class ASDlgTides(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ASDlgTides.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, *args, **kwds)
        self.chk_lst  = wx.CheckListBox(self, wx.ID_ANY, style=wx.LB_EXTENDED)
        self.btn_ok   = wx.Button(self, wx.ID_OK, '')
        self.btn_cncl = wx.Button(self, wx.ID_CANCEL, '')

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_btn_ok,     self.btn_ok)
        self.Bind(wx.EVT_BUTTON, self.on_btn_cancel, self.btn_cncl)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ASDlgTides.__set_properties
        self.SetTitle('Paramètres')
        self.SetSize((400, 300))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ASDlgTides.__do_layout
        szr_main = wx.BoxSizer(wx.VERTICAL)
        szr_btn  = wx.BoxSizer(wx.HORIZONTAL)
        szr_main.Add(self.chk_lst, 4, wx.EXPAND, 0)
        szr_btn.Add((20, 6),       4, wx.EXPAND, 0)
        szr_btn.Add(self.btn_ok,   1, 0, 0)
        szr_btn.Add(self.btn_cncl, 1, 0, 0)
        szr_main.Add(szr_btn, 0, 0, 0)
        self.SetSizer(szr_main)
        self.Layout()
        # end wxGlade

    def setItems(self, items):
        self.chk_lst.Clear()
        self.chk_lst.InsertItems(items, 0)
        self.SetSize( (400, len(items)*18+80) )
        #self.Layout()
        #szr_main.Fit(self)
        
    def checkItems(self, items):
        self.chk_lst.SetCheckedStrings(items)
        
    def getCheckedItems(self):
        return self.chk_lst.GetCheckedStrings()
        
    def on_btn_ok(self, event):
        event.Skip()

    def on_btn_cancel(self, event):
        event.Skip()

# end of class ASDlgTides


if __name__ == "__main__":
    import wx
    app = wx.PySimpleApp()
    fr = wx.Frame(None, title='test')
    panel = ASDlgTides(fr)
    panel.setItems([ str(i) for i in range(20) ])
    panel.ShowModal()
    fr.Show()
    app.MainLoop()
