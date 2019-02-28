#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
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
#
# generated by wxGlade 0.8.3 on Tue Dec 04 10:45:50 2018
#

import os
import sys

import wx

from ASGlobalParameters import ASGlobalParameters

if getattr(sys, 'frozen', False):
    ROOT_DIR = sys._MEIPASS
else:
    ROOT_DIR = os.path.dirname(__file__)

class ASDlgItem(wx.Control):
    def __init__(self, *args, **kwds):
        super(ASDlgItem, self).__init__(*args, **kwds)

    def getValue(self):
        raise NotImplementedError

    def setValue(self, value):
        raise NotImplementedError
        
class ASDlgItemText(ASDlgItem):
    def __init__(self, *args, **kwds):
        title = kwds.pop('title', 'Title shall be provided')
        value = kwds.pop('value', '')
        super(ASDlgItemText, self).__init__(*args, **kwds)

        self.txtItem = wx.TextCtrl(self, wx.ID_ANY, "")

        self.__set_properties()
        self.__do_layout(title)

        self.txtItem.SetValue(value)

    def __set_properties(self):
        pass

    def __do_layout(self, title):
        szrItem = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, title), wx.HORIZONTAL)
        szrItem.Add(self.txtItem, 1, wx.EXPAND,      0)
            
        self.SetSizer(szrItem)
        szrItem.Fit(self)
        self.Layout()

    def getValue(self):
        return self.txtItem.GetValue()

    def setValue(self, value):
        self.txtItem.SetValue(value)
        
class ASDlgItemFile(ASDlgItem):
    def __init__(self, *args, **kwds):
        title = kwds.pop('title', 'Title shall be provided')
        value = kwds.pop('value', '')
        patrn = kwds.pop('pattern', '')
        folder= kwds.pop('folder', '')
        super(ASDlgItemFile, self).__init__(*args, **kwds)

        self.txtItem = wx.TextCtrl(self, wx.ID_ANY, "")
        self.btnItem = wx.Button  (self, wx.ID_ANY, " ... ", style=wx.BU_EXACTFIT)

        self.__set_properties()
        self.__do_layout(title)

        self.Bind(wx.EVT_BUTTON, self.onBtnItem, self.btnItem)

        self.fldr = folder    
        self.wcrd = '|'.join( (patrn, "All files (*.*)|*.*") )
        self.txtItem.SetValue(value)

    def __set_properties(self):
        pass

    def __do_layout(self, title):
        szrItem = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, title), wx.HORIZONTAL)
        szrItem.Add(self.txtItem, 1, wx.EXPAND,      0)
        szrItem.Add(self.btnItem, 0, wx.ALIGN_RIGHT, 0)
            
        self.SetSizer(szrItem)
        szrItem.Fit(self)
        self.Layout()

    def onBtnItem(self, event):
        defaultDir = os.path.join(ROOT_DIR, self.fldr)
        dlg = wx.FileDialog(self, "Select file", defaultDir, "", self.wcrd, wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetFilenames()
            dirname   = dlg.GetDirectory()
            fullPath = os.path.normpath( os.path.join(dirname, filenames[0]) )
            self.txtItem.SetValue(fullPath)

    def getValue(self):
        return self.txtItem.GetValue()

    def setValue(self, value):
        self.txtItem.SetValue(value)
        
class ASDlgItemChoice(ASDlgItem):
    def __init__(self, *args, **kwds):
        title = kwds.pop('title', 'Key shall be provided')
        value = kwds.pop('value', ' ')
        choices = kwds.pop('choices', [])
        super(ASDlgItemChoice, self).__init__(*args, **kwds)

        idx = choices.index(value)
        self.cbxItem = wx.ComboBox(self, wx.ID_ANY, choices=choices, value=choices[idx], style=wx.CB_DROPDOWN | wx.CB_READONLY)

        self.__do_layout(title)

    def __do_layout(self, title):
        szrItem = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, title), wx.HORIZONTAL)
        szrItem.Add(self.cbxItem, 1, wx.EXPAND, 0)
            
        self.SetSizer(szrItem)
        szrItem.Fit(self)
        self.Layout()

    def getValue(self):
        return self.cbxItem.GetValue()

    def setValue(self, value):
        self.cbxItem.SetValue(value)
        
class ASDlgItemColor(ASDlgItem):
    def __init__(self, *args, **kwds):
        title = kwds.pop('title', 'Title shall be provided')
        value = kwds.pop('value', '')
        super(ASDlgItemColor, self).__init__(*args, **kwds)

        self.btnItem = wxcsel.ColourSelect(self, wx.ID_ANY, " "*15)

        self.__set_properties()
        self.__do_layout(title)

        self.Bind(wx.EVT_BUTTON, self.onBtnItem, self.btnItem)

        self.btnItem.SetValue(value)

    def __set_properties(self):
        pass

    def __do_layout(self, title):
        szrItem = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, title), wx.HORIZONTAL)
        szrItem.Add(self.btnItem, 1, wx.ALIGN_RIGHT, 0)
            
        self.SetSizer(szrItem)
        szrItem.Fit(self)
        self.Layout()

    def getValue(self):
        return self.btnItem.GetValue().GetAsString(flags=wx.C2S_HTML_SYNTAX)

    def setValue(self, value):
        self.btnItem.SetValue(value)
        
class ASDlgParamGlobal(wx.Dialog):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        self.items = []
        self.items.append( ASDlgItemText(self, title="Zone d'étude (WGS84)",value='(0,0,1,1)') )
        self.items.append( ASDlgItemFile(self, title="Fond de carte",       value='Missing', pattern="GeoTIFF files(*.tif)|*.tif", folder='background') )
        self.items.append( ASDlgItemFile(self, title="Ligne de berge",      value='Missing', pattern="Shape files (*.shp)|*.shp", folder='background') )
        self.items.append( ASDlgItemFile(self, title="Idiome des stations", value='Missing', pattern="Asur Translation Files (*.atf)|*.atf", folder='traduction') )
        
        self.btnOK     = wx.Button(self, wx.ID_OK, "")
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onBtnOK,     self.btnOK)
        self.Bind(wx.EVT_BUTTON, self.onBtnCancel, self.btnCancel)

    def __set_properties(self):
        self.SetTitle("ASur - Paramètres globaux")
        self.SetSize((500, 290))

    def __do_layout(self):
        szrMain = wx.BoxSizer(wx.VERTICAL)
        szrBtm  = wx.BoxSizer(wx.HORIZONTAL)
        szrTop  = wx.BoxSizer(wx.VERTICAL)
        
        for item in self.items:
            szrTop.Add(item, 1, wx.EXPAND, 0)

        szrBtm.Add((20, 0),         1, wx.EXPAND, 0)
        szrBtm.Add(self.btnOK,      0, 0, 0)
        szrBtm.Add(self.btnCancel,  0, 0, 0)
        
        szrMain.Add(szrTop, 1, wx.EXPAND, 0)
        szrMain.Add((0, 5), 1, wx.EXPAND, 0)
        szrMain.Add(szrBtm, 0, wx.EXPAND, 0)
        self.SetSizer(szrMain)
        self.Layout()

    def onBtnOK(self, event):
        event.Skip()

    def onBtnCancel(self, event):
        event.Skip()

    def getParameters(self):
        prm = ASGlobalParameters()
        prm.projBbox  = eval(self.items[0].getValue())
        prm.fileBgnd  = self.items[1].getValue()
        prm.fileShore = self.items[2].getValue()
        prm.fileTrnsl = self.items[3].getValue()
        return prm

    def setParameters(self, prm):
        self.items[0].setValue(str(prm.projBbox))
        self.items[1].setValue(prm.fileBgnd)
        self.items[2].setValue(prm.fileShore)
        self.items[3].setValue(prm.fileTrnsl)

if __name__ == "__main__":
    class MyApp(wx.App):
        def OnInit(self):
            self.dialog = ASDlgParamGlobal(None, wx.ID_ANY, "")
            self.SetTopWindow(self.dialog)
            self.dialog.ShowModal()
            self.dialog.Destroy()
            return True

    app = MyApp(0)
    app.MainLoop()
