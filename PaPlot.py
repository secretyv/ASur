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
Plot 
"""

__version__ = '1.0'

import datetime
import time
import tzlocal
import pytz
import numpy as np

import wxmpl
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import dates as mpldt
from matplotlib import ticker as mpltk
import mpldatacursor

import BBModel
from BBModel import DTA_DELTAT

LOCAL_TZ   = tzlocal.get_localzone()
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


# ---  Remplace wxmpl.format_coord pour
#      récupérer les coord
def format_coord(axes, xdata, ydata):
    if xdata is None or ydata is None:
        return ''
    return (xdata, ydata)
wxmpl.format_coord = format_coord

# ---  Spécialise wxmpl.Painter pour transférer
#      les appels au cb avec les coord
class LocationPainter(wxmpl.Painter):
    def __init__(self, view, cb):
        wxmpl.Painter.__init__(self, view)
        self.cb = cb

    def formatValue(self, value):
        return value[0]

    def drawValue(self, dc, value):
        try:
            x, y = value
            t = mpldt.num2date(x, tz=pytz.utc)   # x is matplotlib time UTC
            self.cb((t,y))
        except:
            pass

    def clearValue(self, dc, value):
        self.cb(None)

# ---  Spécialise mpldatacursor.DataCursor pour transférer
#      les appels au cb avec les infos
class DADataCursor(mpldatacursor.DataCursor):
    def __init__(self, *args, **kwargs):
        self.cb_msg = kwargs.pop("messenger", None)
        mpldatacursor.DataCursor.__init__(self, *args, **kwargs)

    def update(self, event, annotation):
        annotation.set_visible(False)

        info = self.event_info(event)
        if self.props_override is not None:
            info = self.props_override(**info)
        x = info['x']
        y = info['y']
        c = info['c']
        t = mpldt.num2date(x, tz=pytz.utc)   # x is matplotlib time UTC
        if c:
            self.cb_msg( (t, y, pow(10.0,c)) )
        else:
            self.cb_msg( (t, y) )


class PaPlot(wxmpl.PlotPanel):
    def __init__(self, *args, **kwargs):
        self.cb_msg  = kwargs.pop("messenger", None)
        self.cb_dclk = kwargs.pop("on_dclick", None)
        wxmpl.PlotPanel.__init__(self, *args, **kwargs)

        self.location = LocationPainter(self, self.cb_msg)
        self.axes = None
        self.DC   = []
        self.CS   = []
        self.bbModel = None
        self.status_onZoom = False

        self.get_figure().canvas.mpl_connect('pick_event', self._onPick)
        
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

    def __displayMessage(self, info):
        self.msgDisplayed = True
        self.cb_msg(info)

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

    def _onLeftButtonDClick(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-dclick event handler, to take care
        of exception http://stackoverflow.com/questions/25332225/choosing-a-point-in-matplotlib-embedded-in-wxpython,
        before dispatching the event to the parent.
        """
        canvas = self.get_figure().canvas
        if canvas.HasCapture(): canvas.ReleaseMouse()
        wxmpl.PlotPanel._onLeftButtonDClick(self, evt)

    def _onMotion(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} mouse motion event handler,
        dispatching first to the datacursor and, if not consumed, to the parent.
        """
        self.msgDisplayed = False
        # ---  Dispatch aux datacursors
        x = evt.GetX()
        y = self.figure.bbox.height - evt.GetY()
        try:
            mpl.backend_bases.FigureCanvasBase.motion_notify_event(self, x, y, guiEvent=evt)
            # ---  Dispatch au parent
            if not self.msgDisplayed:
                #evt.Skip(True)
                wxmpl.PlotPanel._onMotion(self, evt)
        except IndexError:
            pass

    def __plotClearPlot(self):
        self.get_figure().clf()
        self.axes = self.figure.gca()
        self.figure.subplots_adjust(hspace  = 0.090,
                                    wspace  = 0.010,
                                    bottom  = 0.089,
                                    top     = 0.951,
                                    left    = 0.050,
                                    right   = 0.973)
        self.CS   = []
        self.DC   = []

    def __plotTide(self, dtmin, dtmax):
        """
        Plot the tide signal
        Returns the data bounding box
        """
        # ---  Plot data
        tide = self.bbModel.getTideSignal(dtmin-DTA_DELTAT, dtmax+DTA_DELTAT, DTA_DELTAT)
        tideX = [ dt for dt,wl in tide ]
        tideY = [ wl for dt,wl in tide ]

        # ---  Plot
        kwargs = {}
        kwargs['label']     = u'Marée'
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
        lc = mpl.collections.LineCollection(XY, array=C, **kwargs)
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

            lbl  = pt
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

        dc = DADataCursor(self.CS, hover=True, messenger=self.__displayMessage)
        self.DC.append(dc)

    def __plotOnePointZoom(self, data, dtmin, dtmax, bboxTide):
        (d0, ymin), (d1, ymax) = bboxTide

        # ---  Plot windows
        iplt = 0
        dy = (ymax-ymin) / (len(data) + 1)
        for pt,dtaPt in data:                       # Pour chaque point de surverse

            if iplt == 0: lbl  = pt
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

        dc = DADataCursor(self.CS, hover=True, messenger=self.__displayMessage)
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
        self.axes.axvline(dtmin, **kwargs)
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
        cbar = self.figure.colorbar(self.CS[0], **kwargs)
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

    def plotAll(self, bbModel, data, dtini, dtfin, dtmax, title = u''):
        mpl.rcParams['timezone'] = 'UTC'
        self.status_onzoom = False
        
        # ---  Plot the data
        self.bbModel = bbModel
        self.__plotClearPlot()
        bboxTide = self.__plotTide(dtini, dtmax)
        self.__plotPoints(data, dtini, dtmax, bboxTide)
        self.__plotLimits(data, dtini, dtfin)
        self.__plotColorBar()
        self.__plotLegend()
        self.bbModel = None

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

        self.draw()

    def plotZoom(self, bbModel, data, dtini, dtfin, dtmax, title = u''):
        mpl.rcParams['timezone'] = 'UTC'
        self.status_onzoom = True

        # ---  Plot the data
        self.bbModel = bbModel
        self.__plotClearPlot()
        bboxTide = self.__plotTide(dtini, dtmax)
        self.__plotOnePointZoom(data, dtini, dtmax, bboxTide)
        self.__plotLimits(data, dtini, dtfin)
        self.__plotColorBar()
        self.__plotLegend()
        self.bbModel = None

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

        self.draw()

if __name__ == "__main__":
    import wx
    app = wx.PySimpleApp()
    fr = wx.Frame(None, title='test')
    panel = PaPlot(fr, wx.ID_ANY)
    panel.draw()
    fr.Show()
    app.MainLoop()
