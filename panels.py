import Tkinter as tk
import ttk as ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import patches

import pandas as pd
import io
from PIL import Image

style.use('bmh')

'''
TODO:   Store colours, properties in separate module
'''

class LogPanel(FigureCanvasTkAgg):

    '''Log panel class'''

    def __init__(self, parent):

        '''Initialiser'''

        # set up figure, axes
        self.parent = parent
        self.fig, self.axes = plt.subplots(nrows=2, sharex=True, figsize=(1, 4),
                                           gridspec_kw={'height_ratios': [1, 12]})
        self.ax_hdr, self.ax_log = self.axes
        FigureCanvasTkAgg.__init__(self, self.fig, self.parent)

        # format axes
        self.fig.set_facecolor('w')
        for ax in self.axes:
            ax.patch.set_facecolor('w')
            ax.yaxis.set_major_formatter(plt.NullFormatter())
            ax.tick_params(labelsize=8)
        self.ax_hdr.grid(False)
        plt.setp(self.ax_hdr.get_yticklines(), visible=False)
        plt.setp(self.ax_hdr.get_xticklines(), visible=False)
        self.fig.subplots_adjust(left=.08, right=.92, bottom=.04, top=.98, hspace=.02)

    def plot_data(self, xs, ys):

        '''Plot x/y data on log axes'''

        # if self.ax_log.get_lines():
            # self.ax_log.lines[0].set_ydata(ys)
        # else:
        self.ax_log.cla()
        self.ax_log.plot(ys, xs, 'r')
        self.draw()

    def set_facecolor(self, color):

        '''Set figure background colour'''

        self.fig.set_facecolor(color[1])
        self.draw()

    def save_image(self):

        '''Return figure as pillow.Image instance'''

        buf = io.BytesIO()
        self.fig.savefig(buf, format='png')
        buf.seek(0)
        img = Image.open(buf)
        buf.close()
        return img


class LithoPanel(LogPanel):

    '''Lithology-type panel'''

    def __init__(self, parent):

        '''Initialiser'''

        super(LithoPanel, self).__init__(parent)

    def plot_data(self, df):

        '''Plot lithology-type data in blocks'''

        d_color = {'VGN':'#00FBFF','DGN':'#0BADB3','MGN':'#0066FF','TGG':'#FFFF00',
                   'PGR':'#FF0000','SGN':'#8000FF', 'MFGN':'#006466','QGN':'#002673',
                   'DB':'#3A274D','KFP':'#FF3300','UNKNOWN':'#C8C8C8'}
        self.ax_log.cla()
        for i, row in df.iterrows():
            lit_to   = row.end
            lit_from = row.start
            litho    = row.lithname
            self.ax_log.add_patch(patches.Rectangle((0, lit_from), 1, lit_to-lit_from, 
                                  facecolor=d_color.get(litho,'#757575'), lw=0))
        self.ax_log.set_ylim([df.start.min(), df.end.max()])
        self.ax_log.set_xlim([0, 1])
        self.draw()