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
Ouput panel to display
"""

"""
1D Plot
"""

import datetime
import logging
import pytz
import numpy as np

import sys
if 'matplotlib' not in sys.modules:
    import matplotlib
    matplotlib.use('WXAgg') # do this before importing pyplot

import matplotlib as mpl
from matplotlib.collections import LineCollection
from matplotlib import pyplot as plt
from matplotlib import dates  as mpldt
import mpldatacursor

import wx

from ASTranslator import translator as translate
from ASConst      import LOCAL_TZ
from ASModel      import DTA_DELTAT
from ASEvents     import ASEventMotion, ASEVT_MOTION
from ASPanelWxMPL import ASPanelWxMPL

LOGGER = logging.getLogger("INRS.ASur.panel.plot")

DSP_DELTAS = 300
DSP_DELTAT = datetime.timedelta(seconds=DSP_DELTAS)
FONT_SIZE  = 8

COLOR_TBL = ['#FFA500',   # 'orange',
             '#7FFF00',   # 'chartreuse', 7FFF00
             '#00BFFF',   # 'deepskyblue',
             '#9400D3',   # 'darkviolet',
             '#FF1493',   # 'deeppink',
             '#FFFF00',   # 'yellow',
             '#008000',   # 'green',
             '#00FFFF',   # 'cyan',
             '#0000FF',   # 'blue',
             '#FF00FF',   # 'magenta',
             '#FF0000',   # 'red'
            ]
def get_color(i):
    return COLOR_TBL[i % len(COLOR_TBL)]

class DADataCursor(mpldatacursor.DataCursor):
    """
    Spécialise mpldatacursor.DataCursor
    Gére les données et lance un évenement
    """
    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent', None)
        mpldatacursor.DataCursor.__init__(self, *args, **kwargs)

    def update(self, event, annotation):
        annotation.set_visible(False)

        info = self.event_info(event)
        if self.props_override is not None:
            info = self.props_override(**info)
        x = info['x']
        y = info['y']
        c = info['c']
        if c:
            c = pow(10.0,c)
        wnd = self.parent
        wx.PostEvent(wnd, ASEventMotion(wnd.GetId(), xy=(x,y), c=c))

class ASPanelPlot(ASPanelWxMPL):
    def __init__(self, *args, **kwargs):
        super(ASPanelPlot, self).__init__(*args, **kwargs)

        self.axes = None
        self.DC   = []
        self.CS   = []
        self.asurMdl = None
        self.status_onZoom = False

        self.Bind(ASEVT_MOTION, self.onMotion)

        #canvas = self.get_figure().canvas
        #canvas.mpl_connect('pick_event', self._onPick)

    #def __dateFormatter(self, x):
    #    """ formatter for date x-data. primitive, and probably needs
    #    improvement, following matplotlib's date methods.
    #    """
    #    span = self.axes.xaxis.get_view_interval()
    #    tmin = time.mktime(dates.num2date(min(span)).timetuple())
    #    tmax = time.mktime(dates.num2date(max(span)).timetuple())
    #    nhours = (tmax - tmin)/3600.0
    #    fmt = "%m/%d"
    #    if nhours < 0.1:
    #        fmt = "%H:%M\n%Ssec"
    #    elif nhours < 4:
    #        fmt = "%m/%d\n%H:%M"
    #    elif nhours < 24*8:
    #        fmt = "%m/%d\n%H:%M"
    #    return time.strftime(fmt, dates.num2date(x).timetuple())

    def _onPick(self, evt):
        self.status_onzoom = True
        pnt = evt.artist.get_gid()
        if self.cb_dclk: self.cb_dclk(pnt)

    #def _onKeyDown(self, evt):
    #    print '_onKeyDown', evt
    #    wxmpl.PlotPanel._onKeyDown(self, evt)

    #def _onKeyUp(self, evt):
    #    print '_onKeyUp', evt
    #    wxmpl.PlotPanel._onKeyUp(self, evt)

    #def _onLeftButtonDClick(self, evt):
    #    """
    #    Overrides the C{FigureCanvasWxAgg} left-dclick event handler, to take care
    #    of exception http://stackoverflow.com/questions/25332225/choosing-a-point-in-matplotlib-embedded-in-wxpython,
    #    before dispatching the event to the parent.
    #    """
    #    canvas = self.get_figure().canvas
    #    if canvas.HasCapture(): canvas.ReleaseMouse()
    #    wxmpl.PlotPanel._onLeftButtonDClick(self, evt)

    def onMotion(self, evt):
        """
        Change x to time and skip event
        """
        try:
            x, y = evt.xy
            t = mpldt.num2date(x, tz=pytz.utc)   # x is matplotlib time UTC
            evt.th = (t, y)
            evt.xy = None
            evt.Skip()
        except ValueError:
            pass

    def __plotClearPlot(self):
        fig = self.get_figure()
        fig.clf()
        fig.subplots_adjust(hspace  = 0.090,
                            wspace  = 0.010,
                            bottom  = 0.089,
                            top     = 0.951,
                            left    = 0.050,
                            right   = 0.973)
        self.axes = fig.gca()
        self.CS   = []
        self.DC   = []

    def __plotTide(self, dtmin, dtmax):
        """
        Plot the tide signal
        Returns the data bounding box
        """
        # ---  Plot data
        tide = self.asurMdl.getTideSignal(dtmin-DTA_DELTAT, dtmax+DTA_DELTAT, DTA_DELTAT)
        tideX = [ dt for dt,wl in tide ]
        tideY = [ wl for dt,wl in tide ]

        # ---  Plot
        kwargs = {}
        kwargs['label']     = 'Marée'
        kwargs['linewidth'] = 1.5
        kwargs['linestyle'] = 'solid'
        kwargs['color']     = '#0000FF'   # blue
        kwargs['marker']    = None
        self.axes.plot_date(tideX, tideY, xdate=True, ydate=False, **kwargs)
        return (dtmin, min(tideY)), (dtmax, max(tideY))

    def __plotOneXpo(self, X0, X1, Y, Z, gid = ' ', label = ''):
        if len(X0) < 1: return None
        if len(X1) < 1: return None
        if len(Y)  < 1: return None
        if len(Z)  < 1: return None

        kwargs = {}
        kwargs['linewidth'] = 3
        kwargs['linestyle'] = 'solid'
        kwargs['cmap']      = plt.cm.jet
        kwargs['norm']      = plt.Normalize(-6.0,-2.0)
        kwargs['picker']    = 5
        kwargs['gid']       = gid

        X0Y = np.array([X0,Y]).T.reshape(-1,1,2)
        X1Y = np.array([X1,Y]).T.reshape(-1,1,2)
        XY = np.concatenate([X0Y,X1Y], axis=1)
        C  = np.log10( np.array(Z) )
        lc = LineCollection(XY, array=C, **kwargs)
        cs = self.axes.add_collection(lc)

        if label:
            kwargs = {}
            kwargs['fontsize'] = FONT_SIZE+2
            kwargs['verticalalignment'] = 'top'
            xy = XY[0,0]
            self.axes.text(xy[0], xy[1]-0.05, label, **kwargs)
        return cs

    def __plotPoints(self, data, dtmin, dtmax, bboxTide):
        (d0, ymin), (d1, ymax) = bboxTide

        # ---  Plot windows
        iplt = 0
        dy = (ymax-ymin) / (len(data) + 1)
        for pt,dtaPt in data:                       # Pour chaque point de surverse

            lbl  = translate[pt][0]
            gid  = pt
            iplt = iplt + 1
            for it,dtaTr in enumerate(dtaPt):       # Pour chaque transit
                for dtaXpo in dtaTr:                # Pour chaque fenêtre de temps d'arrivée
                    if not dtaXpo: continue
                    T0, T1, Z = zip(*dtaXpo)

                    T0 = [ mpldt.date2num(t0) for t0 in T0]
                    T1 = [ mpldt.date2num(t1) for t1 in T1]
                    y  = ymin + dy*(iplt + it*0.1)
                    Y  = [y] * len(T0)
                    cs = self.__plotOneXpo(T0, T1, Y, Z, gid=gid, label=lbl)
                    if cs:
                        self.CS.append(cs)
                        lbl = ''

        dc = DADataCursor(self.CS, hover=True, parent=self)
        self.DC.append(dc)

    def __plotOnePointZoom(self, data, dtmin, dtmax, bboxTide):
        (d0, ymin), (d1, ymax) = bboxTide

        # ---  Plot windows
        iplt = 0
        dy = (ymax-ymin) / (len(data) + 1)
        for pt,dtaPt in data:                       # Pour chaque point de surverse

            if iplt == 0: lbl = translate[pt]
            gid  = pt
            iplt = iplt + 1
            for it,dtaTr in enumerate(dtaPt):       # Pour chaque transit
                for dtaXpo in dtaTr:                # Pour chaque fenêtre de temps d'arrivée
                    if not dtaXpo: continue
                    T0, T1, Z = zip(*dtaXpo)

                    T0 = [ mpldt.date2num(t0) for t0 in T0]
                    T1 = [ mpldt.date2num(t1) for t1 in T1]
                    y = ymin + dy*(iplt + it*0.1)
                    Y = [y] * len(T0)
                    cs = self.__plotOneXpo(T0, T1, Y, Z, gid=gid, label=lbl)
                    if cs:
                        self.CS.append(cs)
                        lbl = ''

        dc = DADataCursor(self.CS, hover=True, parent=self)
        self.DC.append(dc)

    def __plotLimits(self, data, dtmin, dtmax):
        """
        Plot the injection limit as vertical lines
        """
        # ---  Plot limits
        kwargs = {}
        kwargs['linestyle'] = 'dashed'
        kwargs['linewidth'] = 1.5
        kwargs['color']     = '#C0C0C0'   # light gray
        kwargs['marker']    = None
        self.axes.axvline(dtmin, **kwargs, label='Fenêtre de surverse')
        self.axes.axvline(dtmax, **kwargs)

    def __plotColorBar(self):
        """
        Plot the color bar for dilution
        """
        if not self.CS: return
        kwargs = {}
        kwargs['shrink']   = 0.85
        kwargs['fraction'] = 0.05
        kwargs['pad']      = 0.03
        kwargs['use_gridspec'] = False # http://matplotlib.1069221.n5.nabble.com/Missing-anchor-for-colorbar-td44594.html
        kwargs['anchor']   = (0.0, 0.40)
        kwargs['extend']   = 'both'
        kwargs['format']   = '$10^{%i}$'
        kwargs['ticks']    = [-6, -5, -4, -3, -2]
        #kwargs['drawedges']= True
        cbar = self.get_figure().colorbar(self.CS[0], **kwargs)
        kwargs = {}
        kwargs['labelsize'] = FONT_SIZE+1
        cbar.ax.tick_params(**kwargs)
        kwargs = {}
        kwargs['fontsize'] = FONT_SIZE
        kwargs['rotation'] = 0.0
        kwargs['x'] = 0.00
        kwargs['y'] = 1.07
        kwargs['labelpad'] = -20
        cbar.set_label('Dilution', **kwargs)

    def __plotLegend(self):
        """
        Plot the legend
        """
        kwargs = {}
        kwargs['loc']       = 'lower right'
        kwargs['fontsize']  = FONT_SIZE
        self.axes.legend(**kwargs)

    def plotAll(self, asurMdl, data, dtini, dtfin, dtmax, title = ''):
        mpl.rcParams['timezone'] = 'UTC'
        self.status_onzoom = False

        # ---  Plot the data
        self.asurMdl = asurMdl
        self.__plotClearPlot()
        bboxTide = self.__plotTide(dtini, dtmax)
        self.__plotPoints(data, dtini, dtmax, bboxTide)
        self.__plotLimits(data, dtini, dtfin)
        self.__plotColorBar()
        self.__plotLegend()
        self.asurMdl = None

        # ---  Finalize plot setup
        #self.axes.set_autoscale_on(False)
        #self.axes.set_xlim((bboxTide[0][0],bboxTide[1][0]))
        #self.axes.set_ylim((bboxTide[0][1],bboxTide[1][1]))

        # ---  Adjust axis param
        self.axes.tick_params(axis='both', which='major', labelsize=FONT_SIZE)
        self.axes.tick_params(axis='both', which='minor', labelsize=FONT_SIZE)
        #self.axes.set_xlabel('Temps', fontsize=FONT_SIZE)
        self.axes.set_ylabel ('m',     fontsize=FONT_SIZE)
        self.axes.grid(True)

        # ---  Adjust axis format
        dateFmt = mpldt.DateFormatter('%m/%d\n%H:%M', tz=LOCAL_TZ)
        self.axes.xaxis.set_major_formatter(dateFmt)

        # ---  Set title
        if title:
            kwargs = {}
            kwargs['loc']       = 'right'
            kwargs['fontdict']  = {'fontsize': FONT_SIZE+2}
            kwargs['position']  = (0.97, 0.93)
            self.axes.set_title(title, **kwargs)

        self.redraw()

    def plotZoom(self, asurMdl, data, dtini, dtfin, dtmax, title = ''):
        mpl.rcParams['timezone'] = 'UTC'
        self.status_onzoom = True

        # ---  Plot the data
        self.asurMdl = asurMdl
        self.__plotClearPlot()
        bboxTide = self.__plotTide(dtini, dtmax)
        self.__plotOnePointZoom(data, dtini, dtmax, bboxTide)
        self.__plotLimits(data, dtini, dtfin)
        self.__plotColorBar()
        self.__plotLegend()
        self.asurMdl = None

        # ---  Adjust axis param
        self.axes.tick_params(axis='both', which='major', labelsize=FONT_SIZE)
        self.axes.tick_params(axis='both', which='minor', labelsize=FONT_SIZE)
        #self.axes.set_xlabel('Temps', fontsize=FONT_SIZE)
        self.axes.set_ylabel ('m',     fontsize=FONT_SIZE)
        self.axes.grid(True)

        # ---  Adjust axis format
        dateFmt = mpldt.DateFormatter('%m/%d\n%H:%M', tz=LOCAL_TZ)
        self.axes.xaxis.set_major_formatter(dateFmt)

        # ---  Set title
        if title:
            kwargs = {}
            kwargs['loc']       = 'right'
            kwargs['fontdict']  = {'fontsize': FONT_SIZE+2}
            kwargs['position']  = (0.97, 0.93)
            self.axes.set_title(title, **kwargs)

        self.redraw()

if __name__ == "__main__":
    app = wx.App()
    fr = wx.Frame(None, title='test')
    panel = ASPanelPlot(parent=fr)
    panel.redraw()
    fr.Show()
    app.MainLoop()
