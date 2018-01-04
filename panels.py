"""
Log-panel classes:

BasePanel (class)  -   Base class for log panels.
DepthPanel (class)   - Depth panel, showing chainage and elevation.
LithoPanel (class)   - Lithology panel, showing rock-type or ductile domain.
ModPanel (class)     - Panel for displaying elastic moduli data.
PSPRPanel (class)    - Panel for displaying PFL-SPR measurements.
HTUPanel (class)     - Panel to display HTU and PFL transmissivity data.
TadpolePanel (class) - Panel to display fracture orientation 'tadpoles'.

TODO:
 * Store colours, properties in separate module.
"""

from __future__ import print_function, division
from math import sin, cos, radians
import io
from PIL import Image
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import patches

style.use('bmh')


class BasePanel(FigureCanvasTkAgg):

    """Log panel class"""

    def __init__(self, parent):

        """Initialise"""

        # set up figure, axes
        self.parent = parent
        gs_kw = {'height_ratios': [1, 12]}
        self.fig, self.axes = plt.subplots(nrows=2, #sharex=True,
                                           figsize=(1, 4), gridspec_kw=gs_kw)
        self.ax_hdr, self.ax_log = self.axes
        FigureCanvasTkAgg.__init__(self, self.fig, self.parent)

        # format axes
        self.fig.set_facecolor('w')
        for ax in self.axes:
            ax.patch.set_facecolor('w')
            ax.yaxis.set_major_formatter(plt.NullFormatter())
            ax.tick_params(labelsize=8)
        self.ax_hdr.grid(False)
        self.ax_log.invert_yaxis()
        plt.setp(self.ax_hdr.get_yticklines(), visible=False)
        plt.setp(self.ax_hdr.get_xticklines(), visible=False)
        self.fig.subplots_adjust(left=.08, right=.92, hspace=.02,
                                 bottom=.04, top=.98)

    def set_depthlims(self, ymin, ymax):

        """Set depth limits on log panel"""

        self.ax_log.set_ylim(ymax, ymin)
        self.draw()
        
    def clear_axes(self):

        """Clear axes for replotting"""

        for ax in self.axes[1:]:
            del ax.lines[:], ax.artists[:], ax.texts[:]

    def set_facecolor(self, color):

        """Set panel background colour"""

        self.fig.set_facecolor(color[1])
        self.draw()

    def save_image(self):

        """Return figure as pillow.Image instance"""

        buf = io.BytesIO()
        self.fig.savefig(buf, format='png')
        buf.seek(0)
        img = Image.open(buf)
        buf.close()
        return img


class DepthPanel(BasePanel):

    """Depth panel"""

    def __init__(self, parent):

        """Initialise"""

        super(DepthPanel, self).__init__(parent)
        self.parent = parent

        self.ax_log.grid(False)
        self.ax_log.xaxis.set_major_formatter(plt.NullFormatter())
        plt.setp(self.ax_log.get_xticklines(), visible=False)
        self.ax_hdr.text(0.5, 0.5, 'Depth', va='center', ha='center',
                         rotation=90, size=11, weight='semibold')

    def plot(self, df):

        """Plot measured depth and elevation"""

        self.clear_axes()

        # get max pages, calculate and plot chainages
        pagemax = self.parent.master.model.pagemax
        labels = [int(x) for x in np.linspace(0, (pagemax+1)*100, pagemax*11)]
        for lbl in labels:
            self.ax_log.text(0.45, lbl, str(lbl), fontsize=10, rotation=90,
                             va='center', ha='center', clip_on=True)

        # get corresponding elevations from df and plot
        for _, rw in df.iterrows():
            self.ax_log.text(0.8, rw.chainage, str(int(rw.elevation)),
                             va='center', ha='center', color='r', fontsize=8,
                             rotation=90, clip_on=True)


class LithoPanel(BasePanel):

    """Lithology data panel"""

    def __init__(self, parent, name):

        """Initialise"""

        super(LithoPanel, self).__init__(parent)
        self.parent = parent

        self.ax_log.grid(False)
        self.ax_hdr.text(0.5, 0.5, name, va='center', ha='center',
                         rotation=90, size=11, weight='semibold')

    def plot(self, df):

        """Plot lithology-type data in blocks"""

        colors = {'VGN': '#00FBFF', 'DGN': '#0BADB3', 'MGN': '#0066FF',
                  'TGG': '#FFFF00', 'PGR': '#FF0000', 'SGN': '#8000FF',
                  'MFGN': '#006466', 'QGN': '#002673', 'DB': '#3A274D',
                  'KFP': '#FF3300', 'UNKNOWN': '#C8C8C8'}

        self.clear_axes()

        for _, rw in df.iterrows():
            lit_to = rw.lithology_to
            lit_from = rw.lithology_from
            lith = rw.lithology
            rect = patches.Rectangle((0, lit_from), 1,
                                     lit_to-lit_from, lw=0,
                                     facecolor=colors.get(lith, '#757575'))
            self.ax_log.add_patch(rect)
        self.ax_log.set_ylim([df.lithology_from.min(), df.lithology_to.max()])
        self.ax_log.set_xlim([0, 1])


class ModPanel(BasePanel):

    """Modulus data panel with twin x-axes"""

    def __init__(self, parent, modulus='Young'):

        """Initialise"""

        super(ModPanel, self).__init__(parent)
        self.parent = parent
        self.modulus = modulus

        self.ax_log.grid(False)
        self.ax_hdr.text(0.5, 0.5, self.modulus, va='center', ha='center',
                         size=11, weight='semibold')

        # add twin axes for derivative
        self.ax_dlog = self.ax_log.twiny()
        self.axes = np.append(self.axes, np.array([self.ax_dlog]))
        # for ax in self.axes:
            # ax.xaxis.set_major_formatter(plt.NullFormatter())
            # plt.setp(ax.get_yticklines(), visible=False)
            # ax.tick_params(labelsize=8)

    def plot(self, df):

        """Plot modulus and spatial derivative"""

        self.clear_axes()
        del self.ax_dlog.lines[:]

        if self.modulus == 'Young':
            self.ax_log.plot(df.young_average, df.depth, 'b-', lw=1.)
            self.ax_dlog.plot(df.young_variability, df.depth, 'b--', lw=1.)

        elif self.modulus == 'Poisson':
            self.ax_log.plot(df.poisson_average, df.depth, 'r-', lw=1.)
            self.ax_dlog.plot(df.poisson_variability, df.depth, 'r--', lw=1.)


class PSPRPanel(BasePanel):

    """PFL-SPR data panel"""

    def __init__(self, parent):

        """Initialise"""

        super(PSPRPanel, self).__init__(parent)
        self.parent = parent

        self.ax_log.grid(False)
        self.ax_hdr.text(0.5, 0.5, 'PFL-SPR', va='center', ha='center',
                         size=11, weight='semibold')

    def plot(self, df):

        """Plot PFL-SPR data"""

        self.clear_axes()
        self.ax_log.plot(df.resistance, df.depth, c='r', lw=1.)


class HTUPanel(BasePanel):

    """HTU-PFL data panel"""

    def __init__(self, parent):

        """Initialise"""

        super(HTUPanel, self).__init__(parent)
        self.parent = parent
        self.ax_hdr.text(0.5, 0.5, 'HTU-PFL', va='center', ha='center',
                         size=11, weight='semibold')

    def plot(self, dfh, dfp):

        """Plot HTU scatters and PFL lines"""

        self.clear_axes()

        # plot HTU data
        for _, rw in dfh.iterrows():
            self.ax_log.plot([rw[2], rw[2]], [rw[1], rw[1]+1.7], 'm', lw=3.,
                             alpha=(0.3 if rw[3] == 0 else 1.))

        # plot PFL data
        self.ax_log.scatter(dfp.trans, dfp.pfl_depth, s=65, marker='D',
                            facecolor='c', lw=.5)

        # add off-scale PFL datapoints
        dfo = dfp[dfp.trans > 1.E-5]
        self.ax_log.scatter([6.E-6]*len(dfo), dfo.pfl_depth, s=65, marker='D',
                            facecolor='none', edgecolor='c', lw=2.)
        self.ax_log.set_xscale('log')


class TadpolePanel(BasePanel):

    """Tadpole plot panel"""

    def __init__(self, parent):

        """Initialise"""

        super(TadpolePanel, self).__init__(parent)
        self.parent = parent

        self.ax_hdr.text(0.5, 0.5, 'Fractures', va='center', ha='center',
                         size=10, weight='semibold')

    def plot(self, df):

        """Plot fracture orientation tadpoles"""

        colors = ['#FFFFFF', '#FFFF81', '#00A3E8', '#5DE136', '#FF4A49',
                  '#FFA200', '#A349A3', '#C69376', '#E1E1E1']
        lithos = dict(zip(xrange(9), colors))

        self.clear_axes()

        for _, d in df.iterrows():
            self.ax_log.scatter(d.dip, d.depth, s=500, c='k', lw=1.5, zorder=3,
                                marker=((0, 0), (sin(radians(d.azimuth)),
                                                 cos(radians(d.azimuth)))))
            if pd.notnull(d.dip) and d.wcf_match == 0:
                self.ax_log.scatter(d.dip, d.depth, s=30, lw=.5, zorder=4,
                                    facecolor=lithos.get(d.mineralogy))
            else:
                self.ax_log.scatter(TadpolePanel.coalesce([d.dip, 3.]),
                                    d.depth, s=30, lw=2., zorder=4,
                                    facecolor=lithos.get(d.mineralogy))

    @staticmethod
    def coalesce(items):

        """Return first non-null item in list"""

        return next(item for item in items if pd.notnull(item))
