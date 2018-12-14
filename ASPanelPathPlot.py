#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2018
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
2D Plot
"""

if __name__ == "__main__":
    import os
    import sys
    supPath = r'E:\bld-1810\H2D2-tools\script'
    if os.path.isdir(supPath) and supPath not in sys.path: sys.path.append(supPath)

import datetime
import logging
import math
import threading
import traceback

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes as inax
import mpldatacursor
from osgeo import ogr
import wx

from ASPanelWxMPL import ASPanelWxMPL
from ASConst      import LOCAL_TZ

from CTCommon import CTUtil
from IPImageProcessor.GDAL import GDLBasemap

from ASPathParameters import ASPathParameters, CLR_SRC
from ASEvents         import ASEventMotion

try:
    import addLogLevel
    addLogLevel.addLoggingLevel('TRACE', logging.DEBUG - 5)
except AttributeError:
    pass
LOGGER = logging.getLogger("INRS.ASur.panel.path")

FONT_SIZE  = 8

class ASDataCursor(mpldatacursor.DataCursor):
    def __init__(self, *args, **kwargs):
        super(ASDataCursor, self).__init__(*args, **kwargs)

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        self.disable()
        for fig in self.figures:
            try:
                fig._mpldatacursors.remove(self)
            except:
                pass

    def _select(self, event):
        try:
            mpldatacursor.DataCursor._select(self, event)
        except:
            pass


## class ASPanelPathWeb(wx.Panel):
##     def __init__(self, *args, **kwargs):
##         super(ASPanelPathPlot, self).__init__(*args, **kwargs)
##
##         self.browser = wx.html2.WebView.New(self)
##
##         self.__do_layout()
##
##         self.browser.LoadURL('http://www.google.ca')
##
##     def __do_layout(self):
##         szr_main = wx.BoxSizer(wx.HORIZONTAL)
##         szr_main.Add(self.browser, 1, wx.EXPAND, 0)
##         self.SetSizer(szr_main)
##         self.Layout()
##     def resetToolbar(self):
##         pass

class ASPanelPathPlot(ASPanelWxMPL):
    DPI = 96
    PRJ_BBLL = (636130, 5185695)    # Project BoundingBox Lower-Left
    PRJ_BBUR = (646190, 5194425)    # Project BoundingBox Upper-Right
    PRJ_WKT  = """
    PROJCS[
        "EC-MTL-BSP (Modified UTM18)",
        GEOGCS[
            "GRS 1980(IUGG, 1980)",
            DATUM[
                "unknown",
                SPHEROID[
                    "GRS80",6378137,298.257222101
                ]
            ],
            PRIMEM[
                "Greenwich",0
            ],
            UNIT[
                "degree",0.0174532925199433
            ]
        ],
        PROJECTION[
            "Transverse_Mercator"
        ],
        PARAMETER["latitude_of_origin", 0],
        PARAMETER["central_meridian", -73],
        PARAMETER["scale_factor",0.9996],
        PARAMETER["false_easting",500000],
        PARAMETER["false_northing",0],
        UNIT["Meter",1]
    ]
    """                             # Project Spatial Reference System

    def __init__(self, *args, **kwargs):
        super(ASPanelPathPlot, self).__init__(*args, **kwargs)

        self.CSS  = []
        self.cbar = None

        self.window = None
        self.screen = None
        self.srs_proj = None
        self.srs_wgs  = None
        self.proj2wgs = None
        self.axes     = None
        self.bgMapFil = ''
        self.bgMapImg = None
        self.bgMapCS  = None
        self.bgShrFil = ''
        self.bgShrPly = None
        self.bgShrCS  = None
        self.threads  = {}  # {thread: doRun}
        self.lock     = threading.Lock()
        self.dataCursors = []

        self.plumes = []
        self.params = ASPathParameters()

        self.SetSize((200, 200))

        self.Bind(wx.EVT_SIZE, self.onResize)

        self.window = (ASPanelPathPlot.PRJ_BBLL[0],
                       ASPanelPathPlot.PRJ_BBLL[1],
                       ASPanelPathPlot.PRJ_BBUR[0],
                       ASPanelPathPlot.PRJ_BBUR[1])

        self.__setAxes()
        self.__setSrsProj()

    def on_mouse_move(self, evt):
        """
        Overload version from parent to implement coord transform.
        """
        if (evt.inaxes is None): return
        if (evt.xdata  is None): return
        x, y = evt.xdata, evt.ydata
        x, y, z = self.proj2wgs.TransformPoint(x, y)
        wx.PostEvent(self, ASEventMotion(self.GetId(), ll=(x, y)))

    ## def __add_one_item(self, cs):
    ##     if isinstance(cs, mpl.collections.Collection):
    ##         self.axes.add_collection(cs)
    ##     elif isinstance(cs, mpl.artist.Artist):
    ##         self.axes.add_artist(cs)
    ##     else:
    ##         raise ValueError('Unhandled type: %s' % type(cs))
    ##
    ## def __add_collections(self):
    ##     for lyr in self.layers:
    ##         for itm in lyr:
    ##             if not itm.visible: continue
    ##             if isinstance( itm.cs, (list,tuple) ):
    ##                 for c in itm.cs: self.__add_one_item(c)
    ##             elif hasattr(itm.cs, 'collections'):
    ##                 for c in itm.cs.collections: self.__add_one_item(c)
    ##             else:
    ##                 self.__add_one_item(itm.cs)

    def __drawBgndMap(self):
        LOGGER.trace('ASPanelPathPlot.__drawBgndMap %s', self.bgMapImg)
        if not self.bgMapImg: return

        w = self.screen.getWindow()
        xtnt = (w[0], w[2], w[1], w[3])
        LOGGER.trace('   %s', xtnt)
        if self.bgMapCS:
            self.bgMapCS.set_extent(xtnt)
            self.bgMapCS.set_data(self.bgMapImg)
        else:
            self.bgMapCS = self.axes.imshow(self.bgMapImg,
                                            interpolation='bilinear',
                                            aspect='equal',
                                            extent=xtnt,
                                            alpha=1.0)

    def __drawBgndShore(self):
        LOGGER.trace('ASPanelPathPlot.__drawBgndShore')
        if not self.bgShrPly: return

        lc = mpl.collections.LineCollection(self.bgShrPly,
                                            color=self.params.shorelineColor)
        self.bgShrCS = self.axes.add_collection(lc)

    def __drawBgnd(self):
        LOGGER.trace('ASPanelPathPlot.__drawBgnd: begin')
        if self.params.doDrawBGMap:     self.__drawBgndMap  ()
        if self.params.doDrawShoreline: self.__drawBgndShore()
        LOGGER.trace('ASPanelPathPlot.__drawBgnd: end')

    def __loadBgndMap(self):
        """
        Load the background map as a PIL Image
        uses the screen size
        """
        LOGGER.trace('ASPanelPathPlot.__loadBgndMap %s %s', self.bgMapFil, self.bgMapImg)
        if self.bgMapImg: return

        LOGGER.trace('ASPanelPathPlot.__loadBgndMap')
        srs_file = GDLBasemap.IPSpatialReference()
        errMsg = srs_file.ImportFromFileAndGuess(self.bgMapFil)
        bgnd = GDLBasemap.IPGdalOgr(toSpacialReference=self.srs_proj, toGeoTransform=self.screen)
        bgnd.addGeoTIFF(self.bgMapFil, fileSpacialReference=srs_file)
        self.bgMapImg = bgnd.exportAsPILImage()
        LOGGER.trace('ASPanelPathPlot.__loadBgndMap end')

    def __loadBgndShr(self):
        """
        Load the shoreline as a list of lines segments
        """
        if self.bgShrPly: return

        LOGGER.trace('ASPanelPathPlot.__loadBgndShr')
        srs_file = GDLBasemap.IPSpatialReference()
        errMsg  = srs_file.ImportFromFileAndGuess(self.bgShrFil)
        shp2prj = GDLBasemap.IPCoordinateTransformation(srs_file, self.srs_proj)

        inDtaSrc  = ogr.Open(self.bgShrFil, 0)
        inLayer   = inDtaSrc.GetLayer()
        inFeature = inLayer.GetNextFeature()
        XY = []
        while inFeature:
            geom = inFeature.GetGeometryRef()
            geom.Transform(shp2prj)
            XY.append( (geom.GetPoint(0)[:2], geom.GetPoint(1)[:2]) )
            inFeature = inLayer.GetNextFeature()

        self.bgShrPly = XY
        LOGGER.trace('ASPanelPathPlot.__loadBgndShr end')

    def __loadBgnd(self):
        """
        Load all the background data
        """
        LOGGER.trace('ASPanelPathPlot.__loadBgnd: begin - %s', self.GetSize())
        w = threading.current_thread()
        LOGGER.debug('ASPanelPathPlot.__loadBgnd: thread: %s', w)
        LOGGER.debug('ASPanelPathPlot.__loadBgnd: before SetSize %s', self.GetSize())
        if self.threads[w]: self.canvas.SetSize(self.GetSize())
        LOGGER.debug('ASPanelPathPlot.__loadBgnd: after SetSize')
        if self.threads[w]: self.__resizeScreen()
        LOGGER.debug('ASPanelPathPlot.__loadBgnd: after __resizeScreen')
        if self.threads[w]: self.__resizeAxes()
        LOGGER.debug('ASPanelPathPlot.__loadBgnd: after __resizeScreen')
        if self.threads[w]: self.__loadBgndMap()
        if self.threads[w]: self.__loadBgndShr()
        LOGGER.debug('ASPanelPathPlot.__loadBgnd: thread: %s', w)
        LOGGER.trace('ASPanelPathPlot.__loadBgnd: end')

    def __remove_one_CS(self, cs):
        try:
            if isinstance( cs, (list,tuple) ):
                for c in cs: c.remove()
            elif hasattr(cs, 'collections'):
                for c in cs.collections: c.remove()
            else:
                cs.remove()
        except:
            pass

    def __remove_all_CS(self):
        for cs in self.CSS:
            self.__remove_one_CS(cs)
        self.CSS = []
        if self.bgMapCS: 
            self.__remove_one_CS(self.bgMapCS)
            self.bgMapCS = None
        if self.bgShrCS: 
            self.__remove_one_CS(self.bgShrCS)
            self.bgShrCS = None

    def __remove_all_DC_thread(self, dataCursors):
        for dc in reversed(dataCursors):
            dc.hide().disable()
            dc.disconnect()
        
    def __remove_all_DC(self,):
        if not self.dataCursors: return

        # ---  Swap the container for an empty one
        self.lock.acquire(blocking=True)
        DCS = self.dataCursors
        self.dataCursors = []
        self.lock.release()
        # ---  Start the cleaning thread
        worker = threading.Thread(target=self.__remove_all_DC_thread, args=(DCS,))
        worker.start()

    def __resizeAxes(self):
        w = self.screen.getWindow()
        self.axes.set_autoscale_on(False)
        self.axes.update_datalim( ((w[0],w[1]), (w[2],w[3])) )
        self.axes.set_xlim(w[0], w[2])
        self.axes.set_ylim(w[1], w[3])
        self.axes.set_aspect('equal', 'box', anchor='C')

    def __resizeScreen(self):
        w, h = self.GetSize()
        size = (float(w)/ASPanelPathPlot.DPI, float(h)/ASPanelPathPlot.DPI)
        self.screen = GDLBasemap.IPGeoTransform()
        self.screen.setWindow(self.window)
        self.screen.setViewportFromSize(size, ASPanelPathPlot.DPI)
        self.screen.resizeWindowToViewport()

    def __setAxes(self):
        fig = self.get_figure()
        ax  = fig.add_subplot(1, 1, 1, aspect='equal')
        fig.subplots_adjust(hspace=0.0, wspace=0.0, bottom=0.0, top=1.0, left=0.0, right=1.0)
        ax.axis('off')
        self.axes = ax

    def __setSrsProj(self):
        self.srs_proj = GDLBasemap.IPSpatialReference()
        self.srs_proj.ImportFromWkt(ASPanelPathPlot.PRJ_WKT)
        self.srs_wgs = GDLBasemap.IPSpatialReference()
        self.srs_wgs.SetWellKnownGeogCS("WGS84")
        self.proj2wgs = GDLBasemap.IPCoordinateTransformation(self.srs_proj, self.srs_wgs)

    def dataCursorPathFormatter(self, **kwargs):
        LOGGER.trace('dataCursorPathFormatter: %s', kwargs)
        try:
            ip = int( kwargs['label'][9:] )
            inds = kwargs['ind']
            plume = self.plumes[ip]
            ti = plume.injectionTime.astimezone(LOCAL_TZ)
            t0 = plume.plume[ 0][0]
            s = []
            for jj in inds:
                tx = plume.plume[jj][0]
                cx = plume.plume[jj][3]
                dt = datetime.timedelta(seconds=(tx-t0))
                st0 = 't0={t:s}'.format(t=ti.isoformat())
                sta = 'ta={t:s}'.format(t=(ti+dt).isoformat())
                sdh = 'dt={d:s}'.format(d=CTUtil.seconds_to_iso(tx-t0))
                scm = 'c.max={c:,.3e}'.format(c=cx)
                s.extend((st0, sta, sdh, scm))
            return '\n'.join(s)
        except Exception as e:
            errMsg = '%s\n%s' % (str(e), traceback.format_exc())
            LOGGER.error(errMsg)

    def dataCursorEllpsFormatter(self, **kwargs):
        LOGGER.trace('dataCursorEllpsFormatter: %s', kwargs)
        try:
            ip = int( kwargs['label'][9:] )
            inds = kwargs['ind']
            plume = self.plumes[ip]
            ti = plume.injectionTime.astimezone(LOCAL_TZ)
            cl = plume.dilution
            t0 = plume.plume[0][0]
            s = []
            for jj in inds:
                tx = plume.plume[jj][0]
                cx = plume.plume[jj][3]
                dt = datetime.timedelta(seconds=(tx-t0))
                st0 = 't0={t:s}'.format(t=ti.isoformat())
                sta = 'ta={t:s}'.format(t=(ti+dt).isoformat())
                sdh = 'dt={d:s}'.format(d=CTUtil.seconds_to_iso(tx-t0))
                scm = 'c.max={c:,.3e}'.format(c=cx)
                scl = 'c.lim={c:,.3e}'.format(c=cl)
                s.extend((st0, sta, sdh, scm, scl))
            return '\n'.join(s)
        except Exception as e:
            errMsg = '%s\n%s' % (str(e), traceback.format_exc())
            LOGGER.error(errMsg)

    def getParameters(self):
        return self.params

    def setParameters(self, prm):
        self.params = prm

    def setBackground(self, fmap, fshr):
        self.bgMapFil = fmap
        self.bgShrFil = fshr

    def on_btn_pan(self, enable):
        fnc = ASDataCursor.enable if enable else ASDataCursor.disable
        for dc in self.dataCursors:
            fnc(dc)
        super(ASPanelPathPlot, self).on_btn_pan(enable)

    def on_btn_zoom_to_rectangle(self, enable):
        fnc = ASDataCursor.enable if enable else ASDataCursor.disable
        for dc in self.dataCursors:
            fnc(dc)
        super(ASPanelPathPlot, self).on_btn_zoom_to_rectangle(enable)

    def onResizeThread(self):
        LOGGER.info('ASPanelPathPlot.onResizeThread: begin %s locked: %s ', self.GetSize(), self.lock.locked())
        doWork = self.GetSize()[0] > 30 and self.GetSize()[1] > 30
        self.lock.acquire(blocking=True)
        w = threading.current_thread()  # Worker
        LOGGER.debug('ASPanelPathPlot.onResizeThread: thread %s', w)
        try:
            if doWork and self.threads[w]: self.__loadBgnd()
            if doWork and self.threads[w]: self.__drawBgnd()
            if doWork and self.threads[w]: self.redraw()
            del self.threads[w]
        except Exception as e:
            LOGGER.debug('Exception: %s', str(e))
            LOGGER.debug('   %s', traceback.format_exc())
        LOGGER.debug('ASPanelPathPlot.onResizeThread: threads=%s', self.threads)
        LOGGER.info('ASPanelPathPlot.onResizeThread: end')
        self.lock.release()

    def onResize(self, event):
        LOGGER.trace('ASPanelPathPlot.onResize: begin')
        for worker in self.threads:
            LOGGER.info('Thread: %s stopping' % worker)
            self.threads[worker] = False
            # self.thread.join(5.0)
            LOGGER.info('Thread: %s stopped' % worker)

        self.bgMapImg = None      # Force reload
        self.bgMapCS  = None      # Force reload
        worker = threading.Thread(target=self.onResizeThread)
        self.threads[worker] = True
        LOGGER.debug('ASPanelPathPlot.onResize: starting %s', worker)
        worker.start()
        LOGGER.trace('ASPanelPathPlot.onResize: end')

    def __plotColorBar(self):
        """
        Plot the color bar for dilution
        """
        class TimeFormatter(mpl.ticker.ScalarFormatter):
            def __call__(self, val, pos=None):
                s = val
                h =  int(s/3600)
                s -= h*3600
                m =  int(s/60)
                s -= h*60
                return '%02d:%02d' % (h, m)

        LABELS = {CLR_SRC.TIME: 'Temps (HH:MM)', CLR_SRC.DILUTION: 'Dilution'}

        if not self.CSS: return
        if not self.params.doDrawPath: return
        
        fig = self.get_figure()
        if self.cbar:
            fig.delaxes(self.cbar.ax)
            fig.subplots_adjust()

        kwargs = {}
        kwargs['shrink']   = 0.85
        kwargs['fraction'] = 0.07
        kwargs['pad']      = 0.02
        kwargs['use_gridspec'] = False # http://matplotlib.1069221.n5.nabble.com/Missing-anchor-for-colorbar-td44594.html
        kwargs['anchor']   = (-0.8, 0.40)
        if self.params.pathColorSource == CLR_SRC.TIME:
            kwargs['format']   = TimeFormatter()
            kwargs['ticks']    = [ h*3600 for h in range(8) ]
        elif self.params.pathColorSource == CLR_SRC.DILUTION:
            kwargs['extend']   = 'both'
            kwargs['format']   = '$10^{%i}$'
            kwargs['ticks']    = [-6, -5, -4, -3, -2, -1, 0]
        else:
                raise ValueError('Invalid color source')
        self.cbar = fig.colorbar(self.CSS[0], **kwargs)

        kwargs = {}
        kwargs['labelsize'] = FONT_SIZE+1
        self.cbar.ax.tick_params(**kwargs)
        kwargs = {}
        kwargs['fontsize'] = FONT_SIZE
        kwargs['rotation'] = 0.0
        kwargs['x'] = 0.00
        kwargs['y'] = 1.07
        kwargs['labelpad'] = -30
        self.cbar.set_label(LABELS[self.params.pathColorSource], **kwargs)

    def __drawOnePlume(self, C, X, Y, **kwargs):
        """
        Plot a path in the form:
        [ (t,x,y), ... ]
        """
        # Path must be decomposed in segments, each segment can then
        # be attributed a value for coloring
        # inspired from http://matplotlib.org/examples/pylab_examples/multicolored_line.html
        XY = np.column_stack((X,Y)).reshape(-1,1,2)
        XY = np.concatenate([XY[:-1],XY[1:]], axis=1)
        lc = mpl.collections.LineCollection(XY, array=C, **kwargs)
        CS = self.axes.add_collection(lc)
        return CS

    def __drawOneEllipses(self, C, X, Y, E, f, **kwargs):
        """
        Plot ellipses for one plume:
        [ (x,y,w,h,a), ... ]
        """
        if 'cmap'  not in kwargs: kwargs['cmap']  = plt.cm.jet
        if 'alpha' not in kwargs: kwargs['alpha'] = 0.4
        XY = np.column_stack((X,Y)).reshape(-1,1,2)
        ZIP = list(zip(XY,E))
        if f <= 0:
            ells = [ mpl.patches.Ellipse(xy[0], width=2*e[0], height=2*e[1], angle=math.degrees(e[2])) for xy, e in ZIP[-1:] ]
        else:
            ells = [ mpl.patches.Ellipse(xy[0], width=2*e[0], height=2*e[1], angle=math.degrees(e[2])) for xy, e in ZIP[::f] ]
        LOGGER.trace('__drawOneEllipses: size=%d', len(ells))
        pc = mpl.collections.PatchCollection(ells, **kwargs)
        #pc = mpl.collections.PatchCollection(ells, array=T, **kwargs)
        CS = self.axes.add_collection(pc)
        return CS

    def __drawPolygons(self, polys, **kwargs):
        """
        polys is a list
        [
            [(x0, y0), ... ]...
        ]
        """
        if 'color'     not in kwargs: kwargs['color']     = 'k'
        if 'linewidth' not in kwargs: kwargs['linewidth'] = 0.5
        xs,ys = [], []
        for poly in polys:
            for x, y in poly:
                xs.append(x)
                ys.append(y)
            xs.append(poly[0][0])
            ys.append(poly[0][1])
            xs.append(None)
            ys.append(None)
        CS = self.axes.plot(xs, ys, **kwargs)
        return CS

    def plotPlumes(self, plumes):
        LOGGER.trace('ASPanelPathPlot.plotPlumes: size=%d', len(plumes))
        kwPath = {}
        #kwPath['norm'] = mpl.colors.Normalize(dtini, dtmax)
        kwPath['cmap'] = plt.cm.jet
        kwEllp = {}
        kwEllp['color'] = self.params.ellipseColor
        kwEllp['alpha'] = self.params.ellipseAlpha
        kwPoly = {}
        kwPoly['color'] = self.params.polygonColor
        kwPoly['linewidth'] = 1.0

        self.__remove_all_DC()
        self.__remove_all_CS()
        self.__drawBgnd()

        hasColor = False
        polys = {}
        ipl = 0
        if plumes and plumes[0].stationName == 'Root':
            plume = plumes[0]
            polys[plume.stationName] = plume.stationPolygon
            ipl = 1
        for ip, plume in enumerate(plumes[ipl:]):
            polys[plume.stationName] = plume.stationPolygon
            txy = np.array(plume.plume)
            # ---  Indice du temps de contact
            # Les temps sont en epoch par rapport à une référence bâtarde
            # Les temps inversés sont en négatifs
            # Ici, on calcule le delta par rapport à l'injection
            # pour repérer l'indice du contact
            T = txy[:,0]
            DT = T - T[0]
            dt = (plume.contactTime - plume.injectionTime).total_seconds()
            imax = DT.shape[0] - 1
            try:
                itx = np.searchsorted(DT, dt, side='right') if self.params.doClipPath else imax
                itx = min(itx+2, imax)  # Pour s'assurer de pogner
            except:
                itx = imax
            if txy[0,0] < 0.0:
                dt = DT[itx]
                DT = dt - DT

            # ---  Slices X et Y
            X = txy[:itx,1]
            Y = txy[:itx,2]
            # ---  La couleur
            if self.params.pathColorSource == CLR_SRC.TIME:
                C = DT[:itx] # txy[:itx,0]
            elif self.params.pathColorSource == CLR_SRC.DILUTION:
                C = np.log(txy[:itx,3])
            else:
                raise ValueError('Invalid color source')
            E = txy[:itx,4:]

            if self.params.doDrawPath:
                kwPath['label'] = 'path_id: %06i' % ip
                CS = self.__drawOnePlume(C, X, Y, **kwPath)
                self.CSS.append(CS)
                hasColor = True
                if self.params.doPathCursor:
                    dc = ASDataCursor(CS, formatter=self.dataCursorPathFormatter,  xytext=(5,5))
                    self.dataCursors.append(dc)

            if self.params.doDrawEllipse:
                kwEllp['label'] = 'path_id: %06i' % ip
                CS = self.__drawOneEllipses(C, X, Y, E, self.params.ellipseFrequency, **kwEllp)
                self.CSS.append(CS)
                if self.params.doEllipseCursor:
                    dc = ASDataCursor(CS, formatter=self.dataCursorEllpsFormatter, xytext=(5,5))
                    self.dataCursors.append(dc)

        if self.params.doDrawPolygon and polys:
            CS = self.__drawPolygons(polys.values(), **kwPoly)
            self.CSS.append(CS)
        if self.params.doDrawColorbar and hasColor:
            self.__plotColorBar()

        self.redraw()

        self.plumes = plumes

if __name__ == "__main__":
    from ASModel import ASPlume
    
    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    LOGGER.addHandler(logHndlr)
    LOGGER.setLevel(logging.TRACE)
    
    app = wx.App()
    fr = wx.Frame(None, title='test')
    fr.SetSize((800, 600))
    panel = ASPanelPathPlot(fr, wx.ID_ANY)
    panel.params.doDrawEllipse = False
    panel.params.doDrawPolygon = False
    
    tnow = datetime.datetime.now()
    T = np.linspace(0, 1, 50)
    X = np.linspace(ASPanelPathPlot.PRJ_BBLL[0], ASPanelPathPlot.PRJ_BBUR[0], 50)
    Y = np.linspace(ASPanelPathPlot.PRJ_BBLL[1], ASPanelPathPlot.PRJ_BBUR[1], 50)
    TXY = np.stack((T, X, Y), axis=-1)
    plume = ASPlume(dilution=1.0e-03, name='tt', poly=None, tide=(), t0=tnow, tc=tnow, isDirect=False, plume=TXY)

    panel.plotPlumes([plume])
    #panel.redraw()
    fr.Show()
    app.MainLoop()
