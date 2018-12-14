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

"""
Input panel to control an overflow scenario.
Overflow points can be activated/deactivated and
overflow duration specified per point.
"""

import datetime
import pytz
import logging

import wx
import wx.lib.masked   as MSK
import wx.adv          as ADV
import wx.lib.agw.hypertreelist  as HTL

from ASTranslator     import translator as translate
from ASConst          import LOCAL_TZ
from ASModel.overflow import Overflow

try:
    import addLogLevel
    addLogLevel.addLoggingLevel('TRACE', logging.DEBUG - 5)
except AttributeError:
    pass
LOGGER = logging.getLogger("INRS.ASur.panel.scenario")

class ASDateHour(wx.Control):
    """
    Control for single date-hour input
    """
    def __init__(self, *args, **kwds):
        label     = kwds.pop('label', '')
        self.onChangeClient = kwds.pop('on_change', self.onChangeClientDefault)
        super(ASDateHour, self).__init__(*args, **kwds)

        self.txt = wx.StaticText          (self, wx.ID_ANY, label) if label else None
        self.ctl_date = ADV.DatePickerCtrl(self, wx.ID_ANY, style=ADV.DP_DROPDOWN)
        self.ctl_time = MSK.TimeCtrl      (self, wx.ID_ANY, format='24HHMM')

        self.__set_properties()
        self.__do_layout()

        self.Bind(ADV.EVT_DATE_CHANGED, self.onChange, self.ctl_date)
        self.Bind(MSK.EVT_TIMEUPDATE,   self.onChange, self.ctl_time)
        
    def __set_properties(self):
        h = self.ctl_time.GetSize().height
        self.spn_time = wx.SpinButton(self, wx.ID_ANY, wx.DefaultPosition, (-1, h), wx.SP_VERTICAL)
        self.ctl_time.BindSpinButton(self.spn_time)
        
        self.setTime()

    def __do_layout(self):
        szr_main = wx.BoxSizer(wx.HORIZONTAL)

        szr_time = wx.BoxSizer(wx.HORIZONTAL)
        szr_time.Add(self.ctl_time, 1, wx.EXPAND, 0)
        szr_time.Add(self.spn_time, 0, wx.EXPAND, 0)

        if self.txt:
            szr_main.Add(self.txt,      1, wx.EXPAND | wx.ALIGN_RIGHT, 0)
        szr_main.Add(self.ctl_date, 2, wx.EXPAND, 0)
        szr_main.Add(szr_time,      2, wx.EXPAND, 0)

        self.SetSizer(szr_main)
        szr_main.Fit(self)
        self.Layout()

    def onChangeClientDefault(self, event):
        pass
    
    def onChange(self, event):
        event.SetId( self.GetId() )
        self.onChangeClient(event)
        
    def getTime(self):
        """
        Return time in UTC as a datetime.datetime
        """
        d = self.ctl_date.GetValue()
        d = d.FormatISODate().split('-')
        t = self.ctl_time.GetValue().split(':')
        dt = datetime.datetime(int(d[0]), int(d[1]), int(d[2]), int(t[0]), int(t[1]))
        dt = LOCAL_TZ.localize(dt)
        dt = dt.astimezone(pytz.utc)
        return dt

    def setTime(self, dt=datetime.datetime.now(pytz.utc)):
        """
        Set the date/time.
        dt is a datetime.datetime in UTC
        """
        dl = dt.astimezone()    # to local TZ
        d  = wx.DateTime(dl.day, dl.month-1, dl.year, dl.hour, dl.minute, 0, 0)
        self.ctl_date.SetValue(d)
        self.ctl_time.SetValue(d)

class ASDuration(wx.Control):
    """
    Control for injection duration with two date-hour input
    """
    def __init__(self, *args, **kwds):
        label1 = kwds.pop('label1', '')
        label2 = kwds.pop('label2', '')
        spacer = kwds.pop('spacer', 20)
        onChange = kwds.pop('on_change', self.onChange)
        super(ASDuration, self).__init__(*args, **kwds)

        self.start = ASDateHour(self, wx.ID_ANY, label=label1, on_change=onChange)
        self.end   = ASDateHour(self, wx.ID_ANY, label=label2, on_change=onChange)

        self.__set_properties()
        self.__do_layout(spacer=spacer)

    def __set_properties(self):
        pass

    def __do_layout(self, spacer=20):
        szr_main = wx.BoxSizer(wx.HORIZONTAL)
        szr_main.Add(self.start, 1, wx.EXPAND, 0)
        szr_main.AddSpacer(spacer)
        szr_main.Add(self.end,   1, wx.EXPAND, 0)
        self.SetSizer(szr_main)
        szr_main.Fit(self)
        self.Layout()
        
    def onChange(self, event):
        id = event.GetId()
        t1 = self.start.getTime()
        t2 = self.end.getTime()
        if id == self.start.GetId():
            if t1 > t2:
                self.end.setTime(t1)
        elif id == self.end.GetId():
            if t2 < t1:
                self.start.setTime(t2)
        else:
            raise RuntimeError('')

    def getTIni(self):
        """
        Return computation start time in UTC
        """
        return self.start.getTime()

    def getTFin(self):
        """
        Return computation end time in UTC
        """
        return self.end.getTime()

class ASPanelScenario(wx.Panel):
    """
    Paneau pour la gestion des points d'injection
    Les points sont présentés sous forme d'un arbre avec possibilité
    de spécifier les temps d'injection pour chaque point.
    """
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)

        agwStyle  = 0
        agwStyle |= HTL.TR_HIDE_ROOT
        agwStyle |= HTL.TR_DEFAULT_STYLE
        agwStyle |= HTL.TR_HAS_BUTTONS
        agwStyle |= HTL.TR_HAS_VARIABLE_ROW_HEIGHT
        agwStyle |= HTL.TR_AUTO_CHECK_CHILD
        agwStyle |= HTL.TR_AUTO_TOGGLE_CHILD
        agwStyle |= HTL.TR_AUTO_CHECK_PARENT
        agwStyle |= HTL.TR_ELLIPSIZE_LONG_ITEMS

        self.tree = HTL.HyperTreeList(self, wx.ID_ANY, agwStyle=agwStyle)

        self.__set_properties()
        self.__do_layout()

        self.tree.Bind(HTL.EVT_TREE_ITEM_CHECKED,   self.onTreeCheck)
        # http://wxpython-users.1045709.n5.nabble.com/Tooltips-on-CustomTreeCtrl-HyperTreeList-leaves-td5718763.html
        self.tree.GetMainWindow().Bind(wx.EVT_TREE_ITEM_GETTOOLTIP, self.onToolTip)

    def __set_properties(self):
        self.tree.AddColumn("Points de surverse")
        self.tree.AddColumn("Début/Fin")
        self.tree.SetMainColumn (0) # the one with the tree in it...
        self.tree.SetColumnWidth(0, 175)
        self.tree.SetColumnWidth(1, 350)

        self.tree.AddRoot('ASur')

    def __do_layout(self):
        szr_main = wx.BoxSizer(wx.VERTICAL)
        szr_main.Add(self.tree, 1, wx.EXPAND, 0)
        self.SetSizer(szr_main)
        szr_main.Fit(self)
        self.Layout()

    def __deleteAllItems(self, item=None):
        isRoot = False
        if not item:
            item = self.tree.GetRootItem()
            isRoot = True

        if item.HasChildren():
            for child in item.GetChildren():
                self.__deleteAllItems(child)

        wnd = self.tree.GetItemWindow(item, 1)
        if wnd: wnd.Destroy()

        if isRoot:
            self.tree.DeleteAllItems()

    def fillTree(self, bbModels, bbTides=[], addTides=False):
        """
        Fill the tree with the supplied data.

        Args:
            bbModels (list):    List of models
            bbTides (list):     List of activ tides
            addTides (bool):    True to add tides

         Returns:
            None
        """
        self.tree.Hide()
        pnts = {}
        for bbModel in bbModels:
            for pnt in bbModel.getPointNames():
                pnts.setdefault(pnt, [])
                pnts[pnt].append(bbModel)

        self.__deleteAllItems()
        root = self.tree.AddRoot('ASur')
        gname = ''
        for pnt in sorted(pnts.keys()):
            if pnt.split('-')[0] != gname:
                gname = pnt.split('-')[0]
                node = self.tree.AppendItem(root, gname, ct_type=1)
                node.Set3State(True)
            pnt_dspl, pnt_help = translate[pnt]
            child = self.tree.AppendItem(node, pnt_dspl, ct_type=1)
            child.SetData( dict() )
            child.GetData()['id']   = pnt
            child.GetData()['dspl'] = pnt_dspl
            child.GetData()['help'] = pnt_help
            child.Set3State(False)
            self.tree.SetItemWindow(child, ASDuration(self.tree.GetMainWindow(), spacer=5), 1)
            self.tree.GetItemWindow(child, 1).Enable(False)

            uniquer = set()
            for bbModel in pnts[pnt]:
                for tide in bbModel.getPointTideNames(pnt):
                    uniquer.add(tide)
            tides = sorted(uniquer)
            if bbTides:
                tides = [ t for t in tides if t in bbTides ]
            child.GetData()['tides'] = tides
            if tides and addTides:
                for t in tides:
                    self.tree.AppendItem(child, t, ct_type=1)
                child.Set3State(True)
        self.tree.Show()
        self.Refresh()

    def getPoints(self, item = None, lvl = 0):
        """
        Retourne la liste des points sélectionnés et les temps
        d'injection.

        Args:
            item (TreeItem):
            lvl (int):   Tree level

        Returns:
            list:   List of Overflow
        """
        if not item:
            item = self.tree.GetRootItem()
        LOGGER.trace('getPoints(): %s, level=%d', item.GetText(), lvl)
        res = []
        if lvl == 0:
            if item.HasChildren():
                for child in item.GetChildren():
                    r = self.getPoints(item=child, lvl=lvl+1)
                    res.extend(r)
        elif lvl == 1:
            if item.HasChildren():
                for child in item.GetChildren():
                    r = self.getPoints(item=child, lvl=lvl+1)
                    res.extend(r)
        elif lvl == 2:
            if item.HasChildren():
                for child in item.GetChildren():
                    r = self.getPoints(item=child, lvl=lvl+1)
                    res.extend(r)
                if res: res = [ [ item.GetData()['id'], res] ]
            elif item.IsChecked():
                tides = item.GetData()['tides']
                dt1 = self.tree.GetItemWindow(item, 1).getTIni()
                dt2 = self.tree.GetItemWindow(item, 1).getTFin()
                if tides:
                    res = [ Overflow(item.GetData()['id'], dt1, dt2, tides) ]
        elif lvl == 3:
            if item.IsChecked():
                res = [ item.GetText() ]
        LOGGER.trace('getPoints() checked points: %s', res)
        return res

    def getPointsChecked(self):
        """
        Get points et check them
        """
        # ---  Retrieve and check points
        pnts = self.getPoints()
        if len(pnts) == 0:
            errMsg = 'La sélection de points de surverse est vide'
        else:
            errLst = [ p.isValid() for p in pnts if p.isValid()]
            errMsg = '\n'.join(errLst)
        return errMsg, pnts

    @staticmethod
    def setNode3State(node):
        """
        Set the tree state. According to the number of selected
        childrens, a node will be checked, unchecked or undetermined.
        """
        nCheck = 0
        nChild = 0
        if node.HasChildren():
            for child in node.GetChildren():
                nChild += 1
                nCheck += ASPanelScenario.setNode3State(child)
            try:
                if nCheck == 0:
                    node.Set3StateValue(wx.CHK_UNCHECKED)
                    nCheck = 0
                elif nCheck == nChild:
                    node.Set3StateValue(wx.CHK_CHECKED)
                    nCheck = 1
                else:
                    node.Set3StateValue(wx.CHK_UNDETERMINED)
                    nCheck = .5
            except Exception:
                pass
        else:
            nChild = 1
            if node.IsChecked():
                nCheck = 1
        return nCheck/nChild

    @staticmethod
    def checkNodeRecurse(node, checked):
        """
        Check/uncheck all nodes recursively.
        """
        if node.HasChildren():
            for child in node.GetChildren():
                ASPanelScenario.checkNodeRecurse(child, checked)
        else:
            node.Check(checked)

    def onTimeChange(self, event):
        """
        Handler for event ...
        """
        print('onTimeChange', event)
        
    def onToolTip(self, event):
        """
        Handler for event EVT_TREE_ITEM_GETTOOLTIP
        """
        item = event.GetItem()
        data = item.GetData()
        if data:
            ttip = item.GetData()['help']
            event.SetToolTip(ttip)
        
    def onTreeCheck(self, event):
        """
        Handler for event tree check, call when an item in the tree
        is checked/unchecked. The state of the tree will be modified to
        reflect the selection.
        """
        item = event.GetItem()
        try:
            self.tree.GetItemWindow(item, 1).Enable(item.IsChecked())
        except AttributeError:  # level 1 nodes have no ItemWindow
            pass    
        # ---
        node = event.GetItem()
        if node.Is3State() and node.Get3StateValue() == wx.CHK_UNDETERMINED:
            ASPanelScenario.checkNodeRecurse(node, False)
        # ---
        root = self.tree.GetRootItem()
        ASPanelScenario.setNode3State(root)
        # ---
        self.tree.Refresh()

if __name__ == "__main__":
    from ASModel  import ASModel
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

            self.pnl = ASPanelScenario(self)

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

            self.Bind(wx.EVT_BUTTON, self.onBtnOK,     self.btn_ok)
            self.Bind(wx.EVT_BUTTON, self.onBtnCancel, self.btn_cancel)
            
            #dirname = r'E:\Projets_simulation\VilleDeQuebec\Beauport\BBData_v3.2\data.lim=1e-2'
            dirname = r'E:\Projets_simulation\VilleDeQuebec\Beauport\Simulation\PIO\BBData_v1812\data.lim=1.0e-03'
            bbModels = [ ASModel(dirname) ]
            bbModels.sort(key = ASModel.getDataDir)
            self.pnl.fillTree(bbModels)

        def onBtnOK(self, event):
            event.Skip()

        def onBtnCancel(self, event):
            self.Destroy()
            
    class MyApp(wx.App):
        def OnInit(self):
            dlg = MyDialogBox(None)
            if dlg.ShowModal() == wx.ID_OK:
                print('OK')
            return True
            
    app = MyApp(False)
    app.MainLoop()
