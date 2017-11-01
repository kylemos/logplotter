#!/usr/bin/env python
from __future__ import print_function
import Tkinter as tk
# import ttk as ttk
from tkColorChooser import askcolor
from tkFileDialog import asksaveasfilename

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from functools import partial
# import json # temporary in place of db
import pandas as pd
from logplotter_sql import dbConnect

style.use('bmh')

"""
TODO:
 * Maintain MVC design pattern
 * Use matplotlib's 'set_data' method to update graph (i.e. instead of cla(), draw())?
 * Fix save_as_image method, see https://tkinter.unpythonic.net/wiki/tkFileDialog
 * Use caching to store recently-loaded logs (to avoid excessive db fetches).
 * Add scrollbar
 * Add legend on second page (linked to figure properties, which should be part of model?)
 * Implement application-level logging (using logging)
"""

# Structure:   https://stackoverflow.com/questions/17466561/best-way-to-structure-a-tkinter-application
# REFERENCE:   http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm
# Caching:     https://www.blog.pythonlibrary.org/2016/02/25/python-an-intro-to-caching/
# Also useful: https://stackoverflow.com/questions/8707039/difference-between-pack-and-configure-for-widgets-in-tkinter
#              http://effbot.org/tkinterbook/canvas.htm


class LogPlotterApp(tk.Tk):

    '''Application-level controller class'''

    def __init__(self):

        '''Initialiser'''

        tk.Tk.__init__(self)

        # set up model
        self.model = Model()

        # set up container frame
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # store view classes in dict
        self.frames = {}
        for F in [ViewPage]:
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # show ViewPage (default)
        self.show_frame(ViewPage)

    def show_frame(self, frm):

        '''Raise page'''

        frame = self.frames[frm]
        frame.tkraise()

    def _exit(self):

        '''Quit application'''

        root.quit()
        root.destroy()


class ViewPage(tk.Frame):

    '''Viewer class'''

    def __init__(self, parent, controller):

        '''Initialiser'''

        # setup frame
        tk.Frame.__init__(self, parent)
        self.master = controller
        self.master.title("Logplotter")
        self.pack(fill="both", expand=1)

        # initialise log panel visibility
        self.visible = {}
        for i in xrange(3):
            self.visible[i] = tk.BooleanVar()
            self.visible[i].set(True)

        # add a MenuBar
        menu = MenuBar(self)
        self.master.config(menu=menu)

        # set up log panels
        self.c1 = LogPanel(self)
        self.c2 = LogPanel(self)
        self.c3 = LogPanel(self)
        self.canvases = [self.c1, self.c2, self.c3]

        # grid and configure log panels
        for i, c in enumerate(self.canvases):
            c.show()
            c.get_tk_widget().grid(row=0, column=i, sticky='nsew')
            self.columnconfigure(i, weight=1)
        self.rowconfigure(0, weight=1)

        # add depth tracker label
        self.depthVar = tk.StringVar()
        self.depthLabel = tk.Label(self, relief='groove', anchor='w', textvariable=self.depthVar)
        self.depthLabel.grid(row=1, column=0, sticky='nsew')
        for c in self.canvases:
            c.mpl_connect('motion_notify_event', self.on_move_event)

    def save_as_image(self):

        '''Save figure as image'''
        
        filetypes = [('Portable Network Graphics','*.png'),
                     ('JPEG','*.jpg'),
                     ('Adobe Portable Document Format','*.pdf')]
        savename = asksaveasfilename(defaultextension='.png', filetypes=filetypes)
        if savename:
            self.fig.savefig(savename, dpi=150)

    def display_log(self, hole):

        '''Select log to display'''

        # get data dataFrame
        df = self.master.model.db_fetch(hole)
        if not df.empty:
            xs,ys = df.x.values, df.y.values

        # redraw
        for c in self.canvases:
            c.plot_data(xs, ys)

    def change_background(self):

        '''Change figure background'''

        color = askcolor(initialcolor="#ffffff", title="Choose background colour")
        for c in self.canvases:
            c.set_facecolor(color)

    def toggle_panel(self, i):

        '''Toggle log panels on/off'''

        if self.visible[i]:
            self.canvases[i].get_tk_widget().grid_remove()
        else:
            self.canvases[i].get_tk_widget().grid()
        self.visible[i] = not self.visible[i]

    def on_move_event(self, event):
    
        '''Track depth by mouse position'''
        
        c = self.canvases[0]
        f, ax = c.figure, c.ax_log
        top = ax.get_position().y1 * f.get_size_inches()[1] * f.dpi
        if event.inaxes and event.y < top:
            self.depthVar.set('mD: {:.2f} m'.format(event.ydata))


class MenuBar(tk.Menu):

    '''Menu bar class (for better modularisation)'''

    def __init__(self, parent):
    
        '''Initialiser'''

        tk.Menu.__init__(self, parent)

        # file menu
        fileMenu = tk.Menu(self, tearoff=False)
        fileMenu.add_command(label="Save as image", command=parent.save_as_image)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=parent.master._exit)

        # view menu
        viewMenu = tk.Menu(self, tearoff=False)
        viewMenu.add_command(label="Set background colour", command=parent.change_background)

        # view submenu: display borehole data
        logMenu = tk.Menu(viewMenu, tearoff=False)
        for hole in parent.master.model.bhs:
            logMenu.add_command(label=hole, command=partial(parent.display_log, hole))
        viewMenu.add_cascade(label="Display Log", menu=logMenu)

        # view submenu: display panels
        panelMenu = tk.Menu(viewMenu, tearoff=False)
        for i in xrange(3):
            panelMenu.add_checkbutton(label='Log {}'.format(i), onvalue=True, offvalue=False,
                                      variable=parent.visible[i], command=partial(parent.toggle_panel, i))
        viewMenu.add_cascade(label='Toggle Panels', menu=panelMenu)

        # add menus to menu bar
        self.add_cascade(label="File", menu=fileMenu)
        self.add_cascade(label="View", menu=viewMenu)


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
            ax.yaxis.set_ticklabels([])
            ax.tick_params(labelsize=8)
        self.ax_hdr.grid(False)
        plt.setp(self.ax_hdr, yticks=[])
        plt.setp(self.ax_hdr.get_xticklines(), visible=False)
        self.fig.subplots_adjust(left=.08, right=.92, bottom=.04, top=.98, hspace=.02)
        
    def plot_data(self, xs, ys):
    
        '''Plot x/y data on log axes'''
    
        self.ax_log.cla()
        self.ax_log.plot(ys, xs, 'r')
        self.draw()
        
    def set_facecolor(self, color):
    
        '''Set figure background colour'''

        self.fig.set_facecolor(color[1])
        self.draw()


class Model(object):

    '''Data model'''

    def __init__(self):

        '''Initialiser'''

        self.bhs = json.load(open('holes.json', 'r'))
        self.data = pd.DataFrame(columns=['x', 'y'])

    # def fetch_data(self, bh):

        # '''Fetch data from "database"'''

        # try:
            # df = pd.read_json('./db/{}.json'.format(bh), orient='columns')
        # except ValueError:
            # print('Data could not be loaded from db')
        # else:
            # self.data.x = df.x.values
            # self.data.y = df.y.values
            # return self.data
            
    def db_fetch(self, bh):

        '''Fetch data from sqlite database'''

        data = {}
        with dbConnect('./example.db') as c:

            tables = c.execute(dbConnect.qry_tables).fetchall()
            for table, in tables:
                data[table] = c.execute(dbConnect.qry_data.replace('?', table)).fetchall()

        self.data.x, self.data.y = zip(*data['tbl_pspr'])
        return self.data


# main
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("500x650")
    root.mainloop()
