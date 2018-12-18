#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
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

"""
Modèle de temps d'arrivée de surverses
"""

import datetime
import enum
import logging
import os
import optparse
import pytz
import sys
import traceback

try:
    import addLogLevel
    addLogLevel.addLoggingLevel('TRACE', logging.DEBUG - 5)
except AttributeError:
    pass

import wx
import wx.adv          as wx_adv
import wx.lib.wordwrap as wx_ww
import wx.aui          as wx_AUI
import wx.html         as wx_html

if getattr(sys, 'frozen', False):
    supPath = sys._MEIPASS
else:
    try:
        supPath = os.path.join( os.environ['INRS_DEV'], 'H2D2-tools', 'script'  )
    except KeyError:
        supPath = os.path.normpath( os.environ['INRS_H2D2_TOOLS'] )
if os.path.isdir(supPath):
    if supPath not in sys.path:
        sys.path.append(supPath)
else:
    raise RuntimeError('Supplementary import path not found: "%s"' % supPath)

from __about__ import __author__, __version__, __copyright__
from ASGlobalParameters import ASGlobalParameters
from ASPanelScenario  import ASPanelScenario
from ASPanelPlot      import ASPanelPlot
from ASPanelPath      import ASPanelPath
from ASPathParameters import ASPathParameters, CLR_SRC, ELL_STL
from ASTranslator     import translator
from ASEvents         import ASEVT_MOTION, ASEVT_BUTTON
from ASConst          import DATE_MIN, DATE_MAX, LOCAL_TZ
import ASDlgLogger
import ASDlgParamGlobal
import ASDlgParamPath
import ASDlgTides
import ASModel

#--- Help provider for contexutal help (broken!!)
# provider = wx.SimpleHelpProvider()
# wx.HelpProvider.Set(provider)

#--- States
GlbStates = enum.Enum('GlbStates', ('started', 'data_loaded'))
BtnStates = enum.Enum('BtnStates', ('off', 'on', 'pan', 'zoom'))
GlbModes  = enum.Enum('GlbModes',  ('standard', 'expert', 'debug'))

if getattr(sys, 'frozen', False):
    ICON_ROOT = os.path.join(sys._MEIPASS, 'bitmaps')
else:
    ICON_ROOT = os.path.join(os.path.dirname(__file__), 'bitmaps')

licTxt = """
ASur  Version %s
%s

Sous licence Apache, Version 2.0 (la "Licence") ;
vous ne pouvez pas utiliser ce fichier, sauf conformément avec la licence.
Vous pouvez obtenir une copie de la Licence sur
       http://www.apache.org/licenses/LICENSE-2.0

Sauf si requis par la loi en vigueur ou par accord écrit, le logiciel distribué sous la licence est distribué "TEL QUEL", SANS GARANTIE NI CONDITION DE QUELQUE NATURE QUE CE SOIT, implicite ou explicite.
Consultez la Licence pour connaître la terminologie spécifique régissant les autorisations et les limites prévues par la licence.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
""" % (__version__, __copyright__)

appName  = "ASur-2"
appTitle = "Arrivée d'une SURverse"

class ASur(wx.Frame):
    CLC_DELTAS = 300
    CLC_DELTAT = datetime.timedelta(seconds=CLC_DELTAS)

    # ID_MDL = [ wx.Window.NewControlId() for i in range(9)]

    def __init__(self, *args, **kwds):
        self.appMode = kwds.pop("appMode", GlbModes.standard)

        #self.logHndlr = CTTextCtrlHandler.CTTextCtrlHandler(self.txt_log)
        self.logHndlr = logging.StreamHandler()
        FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.logHndlr.setFormatter( logging.Formatter(FORMAT) )
        self.LOGGER = logging.getLogger("INRS.ASur") # .frame")
        self.LOGGER.addHandler(self.logHndlr)
        self.LOGGER.setLevel(logging.INFO)
        self.LOGGER.info('Start')

        wx.Frame.__init__(self, *args, **kwds)

        self.nbk_dspl  = wx_AUI.AuiNotebook (self, wx.ID_ANY)
        self.pnl_pnts  = ASPanelScenario    (self.nbk_dspl, wx.ID_ANY)
        self.pnl_asur  = ASPanelPlot        (self.nbk_dspl, wx.ID_ANY)
        self.pnl_slin  = ASPanelPath        (self.nbk_dspl, wx.ID_ANY)
        self.dlgHelp   = None
        self.dlgParamPath = None # ASDlgParamPath.ASDlgParamPath(None)
        self.statusbar = self.CreateStatusBar(2)

        self.histCfg = wx.Config('ASur - File history', style=wx.CONFIG_USE_LOCAL_FILE)
        self.prmsCfg = wx.Config('ASur - Parameters',   style=wx.CONFIG_USE_LOCAL_FILE)

        self.__create_menu_bar()
        self.__create_tool_bar()
        self.__set_properties()
        self.__do_layout()

        # ---  Event processing
        self.Bind(wx.EVT_MENU,      self.on_mnu_file_open,  self.mnu_file_open)
        self.Bind(wx.EVT_MENU,      self.on_mnu_file_add,   self.mnu_file_add)
        self.Bind(wx.EVT_MENU_RANGE,self.on_mnu_file_hist, id=wx.ID_FILE1, id2=wx.ID_FILE9)
        # TODO : il faut regenerer les ID à chaque appel
        # self.Bind(wx.EVT_MENU_RANGE,self.on_mnu_file_xone, id=self.ID_MDL[0], id2=self.ID_MDL[-1])
        self.Bind(wx.EVT_MENU,      self.on_mnu_file_close, self.mnu_file_close)
        self.Bind(wx.EVT_MENU,      self.on_mnu_file_quit,  self.mnu_file_quit)
        self.Bind(wx.EVT_MENU,      self.on_mnu_parm_maree, self.mnu_parm_maree)
        self.Bind(wx.EVT_MENU,      self.on_mnu_parm_path,  self.mnu_parm_path)
        self.Bind(wx.EVT_MENU,      self.on_mnu_parm_glbx,  self.mnu_parm_glbx)
        if self.appMode == GlbModes.debug:
            self.Bind(wx.EVT_MENU,      self.on_mnu_help_reload,self.mnu_help_reload)
            self.Bind(wx.EVT_MENU,      self.on_mnu_help_log,   self.mnu_help_log)
        self.Bind(wx.EVT_MENU,      self.on_mnu_help_help,  self.mnu_help_help)
        self.Bind(wx.EVT_MENU,      self.on_mnu_help_info,  self.mnu_help_info)
        self.Bind(wx.EVT_MENU,      self.on_mnu_help_about, self.mnu_help_about)
        self.Bind(wx.EVT_BUTTON,    self.on_btn_apply,      self.btn_apply)

        self.Bind(wx.EVT_TOOL,      self.on_btn_rst,        self.btn_rst)
        self.Bind(wx.EVT_TOOL,      self.on_btn_bck,        self.btn_bck)
        self.Bind(wx.EVT_TOOL,      self.on_btn_fwd,        self.btn_fwd)
        self.Bind(wx.EVT_TOOL,      self.on_btn_pan,        self.btn_pan)
        self.Bind(wx.EVT_TOOL,      self.on_btn_zsl,        self.btn_zsl)

        self.Bind(wx_AUI.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_page_change, self.nbk_dspl)
        self.Bind(ASEVT_MOTION, self.cb_panel)
        #self.Bind(ASEVT_BUTTON, self.on_btn_parm_path)

        self.mnu_states = {
            GlbStates.started  : (
                [self.mnu_file,         # off
                 self.mnu_parm,
                 self.mnu_help],
                [self.mnu_file,         # on
                 self.mnu_parm_path,
                 self.mnu_parm_glbx,
                 self.mnu_help]),
            GlbStates.data_loaded : (
                [],                     # off
                [self.mnu_file,         # on
                 self.mnu_parm,
                 self.mnu_help])
        }
        self.btn_states = {
            BtnStates.off  : (
                [self.toolbar],        # off
                [self.btn_apply]),     # on
            BtnStates.on : (
                [],                    # off
                [self.toolbar]),       # on
            BtnStates.pan : (
                [self.toolbar],        # off
                [self.btn_rst,
                 self.btn_bck,
                 self.btn_fwd,
                 self.btn_pan,
                 self.btn_apply]),     # on
            BtnStates.zoom : (
                [self.toolbar],        # off
                [self.btn_rst,
                 self.btn_bck,
                 self.btn_fwd,
                 self.btn_zsl,
                 self.btn_apply]),     # on
        }
        self.mnuState = None
        self.btnState = None
        self.__set_state(GlbStates.started, BtnStates.off)

        # ---  Initialize data attributes
        self.dirname = ''
        self.bbModels = []
        self.bbCycles = []
        self.__initConfig()

    def __initConfig(self):
        gPrm = self.__getGlobalParameters()
        try:
            translator.loadFromFile(gPrm.fileTrnsl)
        except FileNotFoundError:
            pass
        pPrm = self.__getPathParameters()
        self.pnl_slin.setBackground(gPrm.projBbox, gPrm.fileBgnd, gPrm.fileShore)
        self.pnl_slin.setParameters(pPrm)

    def __set_properties(self):
        # ---  Main title
        self.SetTitle(appTitle)
        self.SetSize((800, 600))
        self.nbk_dspl.SetSelection(0)

        # ---  Status bar
        self.statusbar.SetStatusWidths([-1,-1])
        statusbar_fields = ["Status", "Position"]
        for i, f in enumerate(statusbar_fields):
            self.statusbar.SetStatusText(f, i)

    def __do_layout(self):
        szr_main = wx.BoxSizer(wx.HORIZONTAL)

        self.nbk_dspl.AddPage(self.pnl_pnts, "Surverses")
        self.nbk_dspl.AddPage(self.pnl_asur, "Graphes")
        self.nbk_dspl.AddPage(self.pnl_slin, "Trajectoires")

        szr_main.Add(self.nbk_dspl, 1, wx.EXPAND, 0)
        self.SetSizer(szr_main)
        self.Layout()
        wx.CallAfter(self.nbk_dspl.SendSizeEvent)

    def __create_menu_bar(self):
        # ---  File history
        self.history= wx.FileHistory(5)
        self.history.Load(self.histCfg)
        self.hist_mnu = wx.Menu()
        self.history.UseMenu(self.hist_mnu)
        self.history.AddFilesToMenu()

        # ---  Loaded files
        self.bbmdl_mnu = wx.Menu()

        # ---  Set up menus
        self.menubar = wx.MenuBar()
        self.mnu_file = wx.Menu()
        self.mnu_file_open = wx.MenuItem(self.mnu_file, wx.ID_ANY, 'Ouvrir...\tCTRL+O', 'Sélectionner le répertoire des données - Ferme toutes les données chargées', wx.ITEM_NORMAL)
        self.mnu_file.Append(self.mnu_file_open)
        self.mnu_file_add  = wx.MenuItem(self.mnu_file, wx.ID_ANY, 'Ajouter...\tCTRL+P', 'Ajouter un répertoire des données', wx.ITEM_NORMAL)
        self.mnu_file.Append(self.mnu_file_add)
        self.mnu_file.Append(wx.ID_ANY, 'Ajouter un répertoire récent\tCtrl+R', self.hist_mnu)
        self.mnu_file.AppendSeparator()
        self.mnu_file.Append(wx.ID_ANY, 'Fermer un jeu de données\tCtrl+W', self.bbmdl_mnu)
        self.mnu_file_close = wx.MenuItem(self.mnu_file, wx.ID_ANY, 'Fermer tout',  'Fermer tous les jeux de données', wx.ITEM_NORMAL)
        self.mnu_file.Append(self.mnu_file_close)
        self.mnu_file.AppendSeparator()
        self.mnu_file_quit = wx.MenuItem(self.mnu_file, wx.ID_ANY, 'Quitter\tCTRL+Q',  "Quitter l'application", wx.ITEM_NORMAL)
        self.mnu_file.Append(self.mnu_file_quit)
        self.menubar.Append(self.mnu_file, 'Fichier')

        self.mnu_parm = wx.Menu()
        self.mnu_parm_maree = wx.MenuItem(self.mnu_parm, wx.ID_ANY, 'Marées...\tCTRL+M', 'Sélectionner les marées prise en compte dans le calcul', wx.ITEM_NORMAL)
        self.mnu_parm.Append(self.mnu_parm_maree)
        self.mnu_parm_path  = wx.MenuItem(self.mnu_parm, wx.ID_ANY, 'Panaches...\tCTRL+T', 'Sélectionner TODO: A_COMPLETER', wx.ITEM_NORMAL)
        self.mnu_parm.Append(self.mnu_parm_path)
        self.mnu_parm_glbx  = wx.MenuItem(self.mnu_parm, wx.ID_ANY, 'Globaux...', 'Paramètre globaux', wx.ITEM_NORMAL)
        self.mnu_parm.Append(self.mnu_parm_glbx)
        self.menubar.Append(self.mnu_parm, 'Paramètres')

        self.mnu_help = wx.Menu()
        if self.appMode == GlbModes.debug:
            self.mnu_help_reload = wx.MenuItem(self.mnu_help, wx.ID_ANY, 'Reload module...', '', wx.ITEM_NORMAL)
            self.mnu_help.Append(self.mnu_help_reload)
            self.mnu_help_log    = wx.MenuItem(self.mnu_help, wx.ID_ANY, 'Log level...', '', wx.ITEM_NORMAL)
            self.mnu_help.Append(self.mnu_help_log)
            self.mnu_help.AppendSeparator()
        self.mnu_help_help = wx.MenuItem(self.mnu_help, wx.ID_ANY, 'Aide...\tF1', '', wx.ITEM_NORMAL)
        self.mnu_help.Append(self.mnu_help_help)
        self.mnu_help_info = wx.MenuItem(self.mnu_help, wx.ID_ANY, 'Info...', '', wx.ITEM_NORMAL)
        self.mnu_help.Append(self.mnu_help_info)
        self.mnu_help_about = wx.MenuItem(self.mnu_help, wx.ID_ANY, 'À propos...', '', wx.ITEM_NORMAL)
        self.mnu_help.Append(self.mnu_help_about)
        self.menubar.Append(self.mnu_help, 'Aide')

        self.SetMenuBar(self.menubar)

    def __create_tool_bar(self):
        rst_bmp = wx.Bitmap(os.path.join(ICON_ROOT, 'mActionZoomFullExtent.png'),  wx.BITMAP_TYPE_ANY)
        bck_bmp = wx.Bitmap(os.path.join(ICON_ROOT, 'mActionMoveBackFeature.png'), wx.BITMAP_TYPE_ANY)
        fwd_bmp = wx.Bitmap(os.path.join(ICON_ROOT, 'mActionMoveFeature.png'),     wx.BITMAP_TYPE_ANY)
        zsl_bmp = wx.Bitmap(os.path.join(ICON_ROOT, 'mActionZoomToSelected.png'),  wx.BITMAP_TYPE_ANY)
        pan_bmp = wx.Bitmap(os.path.join(ICON_ROOT, 'mActionPan.png'),             wx.BITMAP_TYPE_ANY)
        nil_bmp = wx.NullBitmap

        tsize = (16,16)
        self.toolbar = wx.ToolBar(self)
        self.toolbar.SetToolBitmapSize(tsize)
        self.btn_rst = self.toolbar.AddTool(wx.ID_ANY, "Home",          rst_bmp, nil_bmp, shortHelp="Home",              longHelp="Long help for 'Home'")
        self.btn_bck = self.toolbar.AddTool(wx.ID_ANY, "Move backward", bck_bmp, nil_bmp, shortHelp="Move backward",     longHelp="Long help for 'Forward'")
        self.btn_fwd = self.toolbar.AddTool(wx.ID_ANY, "Move forward",  fwd_bmp, nil_bmp, shortHelp="Move forward",      longHelp="Long help for 'Backward'")
        self.btn_pan = self.toolbar.AddTool(wx.ID_ANY, "Pan",           pan_bmp, nil_bmp, shortHelp="Pan",               longHelp="Long help for 'Pan'")
        self.btn_zsl = self.toolbar.AddTool(wx.ID_ANY, "Zoom",          zsl_bmp, nil_bmp, shortHelp="Zoom to selection", longHelp="Long help for 'Zoom'")
        self.toolbar.AddStretchableSpace()
        self.toolbar.Realize()
        self.btn_apply = wx.Button(self.toolbar, wx.ID_APPLY, 'Affiche')
        self.toolbar.AddControl(self.btn_apply)

        self.SetToolBar(self.toolbar)

    def __set_mnu_state(self, status):
        for it in self.mnu_states[status][0]:
            if isinstance(it, wx.Menu):
                for m in it.GetMenuItems(): m.Enable(False)
            else:
                it.Enable(False)
        for it in self.mnu_states[status][1]:
            if isinstance(it, wx.Menu):
                for m in it.GetMenuItems(): m.Enable(True)
            else:
                it.Enable(True)
        self.mnuState = status

    def __set_btn_state(self, status):
        for it in self.btn_states[status][0]:
            if isinstance(it, wx.ToolBar):
                for i in range(it.GetToolsCount()):
                    id = it.GetToolByPos(i).GetId()
                    self.toolbar.EnableTool(id, False)
            else:
                id = it.GetId()
                self.toolbar.EnableTool(id, False)
        for it in self.btn_states[status][1]:
            if isinstance(it, wx.ToolBar):
                for i in range(it.GetToolsCount()):
                    id = it.GetToolByPos(i).GetId()
                    self.toolbar.EnableTool(id, True)
            else:
                id = it.GetId()
                self.toolbar.EnableTool(id, True)
        self.btnState = status

    def __set_state(self, glb, btn):
        # self.LOGGER.info('Global state: %s' % glb)
        self.__set_mnu_state(glb)
        self.__set_btn_state(btn)

    def __fillModelMenu(self):
        for item in self.bbmdl_mnu.GetMenuItems():
            self.bbmdl_mnu.Delete(item)
        id_mdl = []
        for bbModel in self.bbModels:
            fpath = bbModel.getDataDir()
            label = os.path.basename(fpath)
            id = wx.Window.NewControlId()
            self.bbmdl_mnu.Append(id, label, helpString=fpath)
            id_mdl.append(id)
        if id_mdl:
            self.Bind(wx.EVT_MENU_RANGE,self.on_mnu_file_xone, id=id_mdl[0], id2=id_mdl[-1])

    def __fillPoints(self):
        addTides = self.appMode is GlbModes.expert
        self.pnl_pnts.fillTree(self.bbModels, self.bbCycles, addTides)

    def __getCycles(self, bbModel):
        """
        Returns all know cycles contained in the data
        """
        uniquer = set()
        for pnt in bbModel.getPointNames():
            for tide in bbModel.getPointTideNames(pnt):
                uniquer.add(tide)
        return [ item for item in sorted(uniquer) ]

    def __getAllCycles(self):
        """
        Returns all know cycles contained in the data
        """
        uniquer = set()
        for bbModel in self.bbModels:
            for pnt in bbModel.getPointNames():
                for tide in bbModel.getPointTideNames(pnt):
                    uniquer.add(tide)
        return [ item for item in sorted(uniquer) ]

    def __getActivCycles(self, bbModel):
        """
        Returns all the activated cycles from config
        """
        allCycles = self.__getCycles(bbModel)
        return [ cycle for cycle in allCycles if self.prmsCfg.ReadBool('/ActivCycles/%s' % cycle, True) ]

    def __getAllActivCycles(self):
        """
        Returns all the activated cycles from config
        """
        allCycles = self.__getAllCycles()
        return [ cycle for cycle in allCycles if self.prmsCfg.ReadBool('/ActivCycles/%s' % cycle, True) ]

    def __getGlobalParameters(self):
        """
        Returns the global parameters from config
        """
        prm = ASGlobalParameters()
        for item in prm.iterOnAttributeNames():
            try:
                tk = self.prmsCfg.Read('/GlobalParameters/%s' % item)
                if tk:
                    try:
                        value = eval(tk, {}, {})
                    except SyntaxError as e:
                        value = tk
                    setattr(prm, item, value)
            except Exception as e:
                self.LOGGER.error('%s\n%s', str(e), traceback.format_exc())
        return prm

    def __getPathParameters(self):
        """
        Returns the path parameters from config
        """
        prm = ASPathParameters()
        for item in prm.iterOnAttributeNames():
            try:
                tk = self.prmsCfg.Read('/PathParameters/%s' % item)
                if tk:
                    try:
                        value = eval(tk, {}, {'COLOR_SOURCE':CLR_SRC, 'ELLIPSE_STYLE':ELL_STL})
                    except SyntaxError:
                        value = tk
                    setattr(prm, item, value)
            except Exception as e:
                self.LOGGER.error('%s\n%s', str(e), traceback.format_exc())
        return prm

    def __getTIni(self):
        """
        Return computation start time in UTC
        """
        d  = self.ctl_dini.GetValue()
        t  = self.ctl_tini.GetValue().split(':')
        dt = datetime.datetime(d.Year, d.Month+1, d.Day, int(t[0]), int(t[1]))
        dt = LOCAL_TZ.localize(dt)
        dt = dt.astimezone(pytz.utc)
        return dt

    def __getTFin(self):
        """
        Return computation end time in UTC
        """
        d  = self.ctl_dfin.GetValue()
        t  = self.ctl_tfin.GetValue().split(':')
        dt = datetime.datetime(d.Year, d.Month+1, d.Day, int(t[0]), int(t[1]))
        dt = LOCAL_TZ.localize(dt)
        dt = dt.astimezone(pytz.utc)
        return dt

    def __getPoints(self, item = None, lvl = 0):
        if not item:
            item = self.lst_pnts.GetRootItem()

        res = []
        if lvl == 0:
            if item.HasChildren():
                for child in item.GetChildren():
                    r = self.__getPoints(item=child, lvl=lvl+1)
                    res.extend(r)
        elif lvl == 1:
            if item.HasChildren():
                for child in item.GetChildren():
                    r = self.__getPoints(item=child, lvl=lvl+1)
                    res.extend(r)
        elif lvl == 2:
            if item.HasChildren():
                for child in item.GetChildren():
                    r = self.__getPoints(item=child, lvl=lvl+1)
                    res.extend(r)
                if res: res = [ [ item.GetText(), res] ]
            elif item.IsChecked():
                res = item.GetData()
                if res: res = [ [ item.GetText(), res] ]
        elif lvl == 3:
            if item.IsChecked():
                res = [ item.GetText() ]
        return res

    def __getPlotData(self, bbModel, overflows, do_merge):
        """
        Compute the global arrival time windows
        """
        res = bbModel.getOverflowData(ASur.CLC_DELTAT, overflows, do_merge)
        dtini = min(ofl.tini for ofl in overflows)
        dtmax = dtini
        for pt, dtaPt in res:
            for dtaTr in dtaPt:
                for dtaXpo in dtaTr:
                    if not dtaXpo: continue
                    dtmax_arr = dtaXpo[-1][0]
                    if dtmax_arr: dtmax = max(dtmax, dtmax_arr)
        ndays = (dtmax - dtini).days + 1
        return res, (dtini, dtini+datetime.timedelta(days=ndays))

    def __getPlotDataZoom(self, bbModel, dtini, dtfin, pts, do_merge):
        """
        Compute the global arrival time windows
        """
        res = []
        point, tides = pts
        for t in tides:
            r = bbModel.getOverflowData(dtini, dtfin, ASur.CLC_DELTAT, [ [point, [t]] ], do_merge)
            res.extend(r)
        dtmax = dtfin
        for pt, dtaPt in res:
            for dtaTr in dtaPt:
                for dtaXpo in dtaTr:
                    if not dtaXpo: continue
                    dtmax_arr = dtaXpo[-1][0]
                    if dtmax_arr: dtmax = max(dtmax, dtmax_arr)
        ndays = (dtmax - dtini).days + 1
        return res, (dtini, dtini+datetime.timedelta(days=ndays))

    def __getPathData(self, bbModel, overflows):
        """
        """
        res = bbModel.getOverflowPlumes(ASur.CLC_DELTAT, overflows)
        return res

    def __printPlotData(self, dta):
        """
        """
        for pt, dtaPt in dta:
            print(pt)
            print('[')
            for dtaTr in dtaPt:
                print(' '*3, '[')
                for dtaXpo in dtaTr:
                    if not dtaXpo: continue
                    print(' '*6, '[')
                    for d in dtaXpo:
                        print('%s (%s, %s, %f)' % (' '*9, d[0].isoformat(), d[1].isoformat(), d[2]))
                    print(' '*6, ']')
                print(' '*3, ']')
            print(']')

    def on_data_dclick(self, point):
        if not self.appMode is GlbModes.expert: return

        errMsg = ''
        if not errMsg:
            dtini = self.__getTIni()
            dtfin = self.__getTFin()
            if dtini >= dtfin:
                errMsg = 'Temps invalides: Le temps initial doit être inférieur au temps final'

        if not errMsg:
            pts = None
            for p in self.__getPoints():
                if p[0] == point:
                    pts = [p]
                    break
            if not pts:
                errMsg = 'La sélection de points de surverse est vide'

        if not errMsg:
            wx.BeginBusyCursor()
            try:
                dtmax = dtini
                # ---  With 1 model, do not merge transfer times
                if len(self.bbModels) == 1:
                    bbModel = self.bbModels[0]
                    dtaGlb, (dtmin, dtmax) = self.__getPlotDataZoom(bbModel, dtini, dtfin, pts[0], False)
                    self.pnl_asur.plotZoom(bbModel, dtaGlb, dtini, dtfin, dtmax, title='Différentes marées - Différentes vitesses')
                # ---  With many models, merge transfer times and reorganize
                else:
                    dtaGlb = []
                    for bbModel in reversed(self.bbModels):
                        dta, (dtmin_, dtmax_) = self.__getPlotDataZoom(bbModel, dtini, dtfin, pts[0], True)
                        if dtaGlb:
                            for dtaCl, d in zip(dtaGlb, dta):
                                dtaCl[1].extend(d[1])
                        else:
                            dtaGlb = dta
                        dtmax = max(dtmax, dtmax_)
                    self.pnl_asur.plotZoom(self.bbModels[0], dtaGlb, dtini, dtfin, dtmax, title='Différentes marées - Différentes dilutions')
            except Exception as e:
                errMsg = '%s\n%s' % (str(e), traceback.format_exc())
                #errMsg = '%s' % str(e)
            finally:
                wx.EndBusyCursor()

        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_btn_rst(self, event):
        ipage = self.nbk_dspl.GetSelection()
        try:
            page  = self.nbk_dspl.GetPage(ipage)
            page.on_btn_reset()
        except:
            pass

    def on_btn_fwd(self, event):
        ipage = self.nbk_dspl.GetSelection()
        page  = self.nbk_dspl.GetPage(ipage)
        page.on_btn_forward()

    def on_btn_bck(self, event):
        ipage = self.nbk_dspl.GetSelection()
        page  = self.nbk_dspl.GetPage(ipage)
        page.on_btn_backward()

    def on_btn_pan(self, event):
        ipage = self.nbk_dspl.GetSelection()
        page  = self.nbk_dspl.GetPage(ipage)
        page.on_btn_pan(self.btnState is not BtnStates.on)
        if self.btnState is BtnStates.on:
            self.__set_btn_state(BtnStates.pan)
        elif self.btnState is BtnStates.pan:
            self.__set_btn_state(BtnStates.on)

    def on_btn_zsl(self, event):
        ipage = self.nbk_dspl.GetSelection()
        page  = self.nbk_dspl.GetPage(ipage)
        page.on_btn_zoom_to_rectangle(self.btnState is not BtnStates.on)
        if self.btnState is BtnStates.on:
            self.__set_btn_state(BtnStates.zoom)
        elif self.btnState is BtnStates.zoom:
            self.__set_btn_state(BtnStates.on)

    def on_page_change(self, event):
        ipage = self.nbk_dspl.GetSelection()
        page  = self.nbk_dspl.GetPage(ipage)
        # ---  Reset zomm/pan
        self.pnl_asur.resetToolbar()
        self.pnl_slin.resetToolbar()
        # ---  Set button state
        if self.mnuState in [GlbStates.started]:
            self.__set_btn_state(BtnStates.off)
        elif page is self.pnl_pnts:
            self.__set_btn_state(BtnStates.off)
        else:
            self.__set_btn_state(BtnStates.on)
        # ---  Reset statusbar
        self.statusbar.SetStatusText('', 1)

    def on_btn_apply(self, event):
        errMsg = ''
        erMsg, overflows = self.pnl_pnts.getPointsChecked()

        wx.BeginBusyCursor()
        try:
            dtaGlb= []
            pthGlb= []
            dtini = DATE_MAX
            dtfin = DATE_MIN
            dtmax = dtfin
            # ---  With 1 model, do not merge transfer times
            if len(self.bbModels) == 1:
                bbModel = self.bbModels[0]
                dtaGlb, (dtmin_, dtmax_) = self.__getPlotData(bbModel, overflows, False)
                pthGlb                   = self.__getPathData(bbModel, overflows)
                for ofl in overflows:
                    dtini = min(dtini, ofl.tini)
                    dtfin = max(dtfin, ofl.tend)
                    dtmax = max(dtmax, dtmax_)
                self.pnl_asur.plotAll  (self.bbModels[0], dtaGlb, dtini, dtfin, dtmax, title='Différentes vitesses en rivière')
                self.pnl_slin.plotPaths(self.bbModels[0], pthGlb, dtini, dtfin, dtmax)
            # ---  With many models, merge transfer times and reorganize
            else:
                for ofl in overflows:
                    dtaPt = []
                    for bbModel in reversed(self.bbModels):
                        dta, (dtmin_, dtmax_) = self.__getPlotData(bbModel, [ofl], True)
                        #self.__printPlotData(dta)
                        dtini = min(dtini, ofl.tini)
                        dtfin = max(dtfin, ofl.tend)
                        dtmax = max(dtmax, dtmax_)
                        dtaMdl = dta[0][1]
                        if dtaMdl:
                            dtaPt.append( dtaMdl[0] )
                        else:
                            dtaPt.append( [] )
                    dtaGlb.append( (ofl.name, dtaPt) )
                self.pnl_asur.plotAll  (self.bbModels[0], dtaGlb, dtini, dtfin, dtmax, title='Différentes dilutions')

                for bbModel in reversed(self.bbModels):
                    for ofl in overflows:
                        pth = self.__getPathData(bbModel, [ofl])
                        pthGlb.extend( pth )
                self.pnl_slin.plotPaths(self.bbModels[0], pthGlb, dtini, dtfin, dtmax)

            self.__set_state(GlbStates.data_loaded, BtnStates.on)
        except Exception as e:
            errMsg = '%s\n%s' % (str(e), traceback.format_exc())
            #errMsg = '%s' % str(e)
        finally:
            wx.EndBusyCursor()

        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def __do_mnu_open(self, dirname):
        # ---  Check if allready open
        for bbModel in self.bbModels:
            if dirname == bbModel.getDataDir():
                return
        # ---  Construct model
        self.bbModels.append( ASModel.ASModel(dirname) )
        self.bbModels.sort(key = ASModel.ASModel.getDataDir)
        # ---  Fill activ cycles list
        self.bbCycles = self.__getAllActivCycles()
        # ---  Fill list
        self.__fillPoints()
        # ---  Set title
        #dn = os.path.basename(dirname)
        #self.SetTitle("%s - %s" % (appTitle, dn))

        self.dirname = dirname
        self.history.AddFileToHistory(self.dirname)
        self.history.Save(self.histCfg)

        self.__set_state(GlbStates.data_loaded, BtnStates.off)

    def on_mnu_file_open(self, event):
        errMsg = ''
        dlg = wx.DirDialog(self, 'Répertoire des données', self.dirname)
        if (dlg.ShowModal() == wx.ID_OK):
            dirname = dlg.GetPath()
            if (len(dirname) > 0):
                wx.BeginBusyCursor()
                try:
                    self.bbModels = []
                    subdirs = next(os.walk(dirname))[1]
                    if subdirs:
                        for subdir in subdirs:
                            fullpath = os.path.join(dirname, subdir)
                            self.__do_mnu_open(fullpath)
                    else:
                        self.__do_mnu_open(dirname)
                    self.__fillModelMenu()
                except Exception as e:
                    errMsg = '%s\n%s' % (str(e), traceback.format_exc())
                    #errMsg = str(e)
                finally:
                    wx.EndBusyCursor()
            else:
                errMsg = 'Sélectionner le répertoire de données'
        dlg.Destroy()
        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_mnu_file_add(self, event):
        errMsg = ''
        dlg = wx.DirDialog(self, 'Répertoire des données à ajouter', self.dirname)
        if (dlg.ShowModal() == wx.ID_OK):
            dirname = dlg.GetPath()
            if (len(dirname) > 0):
                wx.BeginBusyCursor()
                try:
                    self.__do_mnu_open(dirname)
                    self.__fillModelMenu()
                except Exception as e:
                    errMsg = '%s\n%s' % (str(e), traceback.format_exc())
                    #errMsg = str(e)
                finally:
                    wx.EndBusyCursor()
            else:
                errMsg = 'Sélectionner un répertoire de données'
        dlg.Destroy()
        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_mnu_file_hist(self, event):
        errMsg = ''
        fileNum = event.GetId() - wx.ID_FILE1
        dirname = self.history.GetHistoryFile(fileNum)
        if (len(dirname) > 0):
            wx.BeginBusyCursor()
            try:
                self.__do_mnu_open(dirname)
                self.__fillModelMenu()
            except Exception as e:
                self.history.RemoveFileFromHistory(fileNum)
                errMsg = '%s\n%s' % (str(e), traceback.format_exc())
                #errMsg = str(e)
            finally:
                wx.EndBusyCursor()
        else:
            errMsg = 'Nom du répertoire de données vide'

        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_mnu_file_xone(self, event):
        """
        Close one data set
        """
        errMsg = ''
        mnuItem = self.bbmdl_mnu.FindItemById(event.GetId())
        dirname = mnuItem.GetHelp()
        if (len(dirname) > 0):
            wx.BeginBusyCursor()
            try:
                bbModel = next(b for b in self.bbModels if b.getDataDir() == dirname)
                self.bbModels.remove(bbModel)
                self.__fillPoints()
                self.__fillModelMenu()
                del bbModel
                if not self.bbModels:
                    self.__set_state(GlbStates.started, BtnStates.off)
            except Exception as e:
                errMsg = '%s\n%s' % (str(e), traceback.format_exc())
                #errMsg = str(e)
            finally:
                wx.EndBusyCursor()
        else:
            errMsg = 'Nom du répertoire de données vide'

        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_mnu_file_close(self, event):
        dlg = wx.MessageDialog(self, ' Êtes-vous sûr(e)? \n', 'Fermer', wx.YES_NO)
        if (dlg.ShowModal() == wx.ID_YES):
            self.bbModels = []
            self.__fillPoints()
            self.__fillModelMenu()
            self.__set_state(GlbStates.started, BtnStates.off)

    def on_mnu_file_quit(self, event):
        dlg = wx.MessageDialog(self, ' Êtes-vous sûr(e)? \n', 'Fermer', wx.YES_NO)
        if (dlg.ShowModal() == wx.ID_YES):
            self.bbModels = []
            self.Close(True)

    def on_mnu_parm_maree(self, event):
        errMsg = None
        try:
            allCycles = self.__getAllCycles()
            atvCycles = self.__getAllActivCycles()
            dlg = ASDlgTides.ASDlgTides(self)
            dlg.setItems  (allCycles)
            dlg.checkItems(atvCycles)
            if (dlg.ShowModal() == wx.ID_OK):
                atvCycles = dlg.getCheckedItems()

                self.prmsCfg.DeleteGroup('/ActivCycles')
                for cycle in allCycles:
                    self.prmsCfg.WriteBool('/ActivCycles/%s' % cycle, cycle in atvCycles)
                self.prmsCfg.Flush()

                self.bbCycles = self.__getAllActivCycles()
                self.__fillPoints()
            dlg.Destroy()
        except Exception as e:
            self.LOGGER.error('%s\n%s', str(e), traceback.format_exc())
            errMsg = str(e)
        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_mnu_parm_path(self, event):
        errMsg = None
        try:
            self.dlgParamPath = ASDlgParamPath.ASDlgParamPath(self)
            # self.Bind(ASEVT_BUTTON, self.on_btn_parm_path) #, self.dlgParamPath)
            prm = self.pnl_slin.getParameters()
            self.dlgParamPath.setParameters(prm)
            if (self.dlgParamPath.ShowModal() == wx.ID_OK):
                self.on_btn_parm_path(None)
            self.dlgParamPath.Destroy()
            self.dlgParamPath = None
        except Exception as e:
            self.LOGGER.error('%s\n%s', str(e), traceback.format_exc())
            errMsg = str(e)
        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_btn_parm_path(self, event):
        self.LOGGER.trace('ASur.on_btn_parm_path')
        prm = self.dlgParamPath.getParameters()

        self.prmsCfg.DeleteGroup('/PathParameters')
        for item in prm.iterOnAttributeNames():
            self.prmsCfg.Write('/PathParameters/%s' % item, str(getattr(prm, item)))
        self.prmsCfg.Flush()

        self.pnl_slin.setParameters(prm)
            
    def on_mnu_parm_glbx(self, event):
        errMsg = None
        try:
            prm = self.__getGlobalParameters()
            dlg = ASDlgParamGlobal.ASDlgParamGlobal(self)
            dlg.setParameters(prm)
            if (dlg.ShowModal() == wx.ID_OK):
                prm = dlg.getParameters()
                
                self.prmsCfg.DeleteGroup('/GlobalParameters')
                for item in prm.iterOnAttributeNames():
                    self.prmsCfg.Write('/GlobalParameters/%s' % item, str(getattr(prm, item)))
                self.prmsCfg.Flush()

                translator.loadFromFile(prm.fileTrnsl)
                self.pnl_slin.setBackground(prm.projBbox, prm.fileBgnd, prm.fileShore)
            dlg.Destroy()
        except Exception as e:
            errMsg = str(e)
        if errMsg:
            dlg = wx.MessageDialog(self, errMsg, 'Erreur', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def on_mnu_help_help(self, event):
        if not self.dlgHelp:
            self.dlgHelp = wx_html.HtmlHelpController(style=wx_html.HF_DEFAULT_STYLE, parentWindow=None)
            self.dlgHelp.AddBook('help/ASur.hhp')
        self.dlgHelp.DisplayContents()

    def on_mnu_help_reload(self, event):
        import imp
        lst = list(sys.modules.keys())
        lst.sort()
        dlg = wx.SingleChoiceDialog(
                self, 'Reload a module', 'Reload a Python module',
                lst,
                wx.CHOICEDLG_STYLE
                )
        dlg.SetSize( (300, 500) )
        if dlg.ShowModal() == wx.ID_OK:
            nam = dlg.GetStringSelection()
            mdl = sys.modules[nam]
            imp.reload(mdl)
        dlg.Destroy()

    def on_mnu_help_log(self, event):
        dlg = ASDlgLogger.ASDlgLogZone(self)
        if dlg.ShowModal() == wx.ID_OK:
            LVLS = {'info' : logging.INFO, 'debug': logging.DEBUG, 'trace': logging.TRACE}
            z, l = dlg.getValues()
            self.LOGGER.removeHandler(self.logHndlr)
            self.LOGGER = logging.getLogger(z)
            self.LOGGER.addHandler(self.logHndlr)
            self.LOGGER.setLevel(LVLS[l])
        dlg.Destroy()

    def on_mnu_help_info(self, event):
        info = []
        for bbModel in self.bbModels:
            info.append(bbModel.getDataDir())
            info.extend(bbModel.getInfo())
            info.append('-----------------------')
        infoTxt = '\n'.join(info[:-1])
        infoDlg = wx_adv.AboutDialogInfo()
        #infoDlg.Name = appTitle
        infoDlg.Name = '\n'.join(['%s %s' % (appName, __version__), appTitle])
        infoDlg.Copyright = __copyright__
        infoDlg.Description = wx_ww.wordwrap(infoTxt, 450, wx.ClientDC(self))
        wx_adv.AboutBox(infoDlg)

    def on_mnu_help_about(self, event):
        infoDlg = wx_adv.AboutDialogInfo()
        infoDlg.Name = '\n'.join(['%s %s' % (appName, __version__), appTitle])
        #infoDlg.Version = __version__
        infoDlg.Copyright = __copyright__
        infoDlg.Developers  = [ __author__ ]
        infoDlg.License     = wx_ww.wordwrap(licTxt, 450, wx.ClientDC(self))
        wx_adv.AboutBox(infoDlg)

    def cb_panel(self, evt):
        xy = evt.xy if hasattr(evt, 'xy') else ()
        ll = evt.ll if hasattr(evt, 'll') else ()
        th = evt.th if hasattr(evt, 'th') else ()
        c  = evt.c  if hasattr(evt, 'c')  else None
        try:
            s = []
            if xy:
                x, y = xy
                s.append( 'x={x:,.2f}'.format(x=x) )
                s.append( 'y={y:,.2f}'.format(y=y) )
            if ll:
                x, y = ll
                s.append( 'x={x:,.6f}'.format(x=x) )
                s.append( 'y={y:,.6f} (WGS84)'.format(y=y) )
            if th:
                t, h = th
                t = t.replace(microsecond=0)
                t = t.astimezone(LOCAL_TZ)
                t = t.isoformat(' ')
                s.append( 't={t:s}'.format(t=t) )
                s.append( 'h={h:,.2f}'.format(h=h) )
            if c:
                s.append( 'c={c:,.2e}'.format(c=c) )
            s = ' : '.join(s)
            self.statusbar.SetStatusText('Position: %s' % s, 1)
        except Exception as e:
            print(str(e))
            pass

"""
Utilise une fonction plutôt qu'une classe
car l'héritage fait planter cython
"""
def createASurApp(*args, **kwargs):
    self = wx.App()
    frame = ASur(None, -1, '', *args, **kwargs)
    self.SetTopWindow(frame)
    frame.Show()
    return self, 1

if __name__ == "__main__":
    def main(opt_args = None):
        #import logging
        #logHndlr = logging.StreamHandler()
        #FORMAT = "%(asctime)s %(levelname)s %(message)s"
        #logHndlr.setFormatter( logging.Formatter(FORMAT) )

        #logger = logging.getLogger("INRS.ASur")
        #logger.addHandler(logHndlr)
        #logger.setLevel(logging.INFO)

        # ---  Parse les options
        parser = optparse.OptionParser()
        #parser.add_option("-x", "--expert-mode", dest="xpr", default=False, action='store_true', help="start in expert mode")
        parser.add_option("-x", "--expert-mode", dest="xpr", default=False, action='store_true', help=optparse.SUPPRESS_HELP)
        parser.add_option("-d", "--debug-mode",  dest="dbg", default=False, action='store_true')
        parser.add_option("-l", "--locale",      dest="lcl", default=None, help="Fichier de traduction des noms de station")

        # --- Parse les arguments de la ligne de commande
        if (not opt_args): opt_args = sys.argv[1:]
        (options, args) = parser.parse_args(opt_args)

        # --- Configure le traducteur
        if options.lcl: translator.loadFromFile(options.lcl)

        # --- Crée l'app
        appMode = GlbModes.debug  if options.dbg else GlbModes.standard
        appMode = GlbModes.expert if options.xpr else appMode
        app, err = createASurApp(appMode=appMode)

        # --- Go
        app.MainLoop()

    main()
