#!/usr/bin/env python

import Tkinter as tk
import ttk as ttk
from tkColorChooser import askcolor
from tkFileDialog import asksaveasfilename

import matplotlib
matplotlib.use("TkAgg")
from matplotlib import style
from matplotlib.figure import Figure
#from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
                                               NavigationToolbar2TkAgg)
from functools import partial
import time
import json # temporary, in place of db
import pandas as pd
import numpy as np

style.use('bmh')

"""
TODO:
 * MVC design pattern!
 * Separate menu from viewpage (i.e. own class)
 * Possibly also separate figure from viewpage (make it more modular)
 * Use matplotlib's 'set_data' method to update graph (i.e. instead of cla(), draw())?
 * Improve save_as_image method (filename list, etc...) - see https://tkinter.unpythonic.net/wiki/tkFileDialog
 * Add live-updating statusbar
 * Add scrollbar (when figure properly implemented)
 * Add key on second page (linked to figure properties)
 * Implement application-level logging (using logging)
"""

class LogPlotterApp(tk.Tk):

    '''Application-level controller class'''

    def __init__(self):
    
        '''initialiser'''
        
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
        
        # (default) show ViewPage
        self.show_frame(ViewPage)
        
        
    def show_frame(self, frm):
    
        '''Raise page'''
        
        frame = self.frames[frm]
        frame.tkraise()
        
    def exit(self):
    
        '''Quit application'''
        
        root.destroy()
        

class ViewPage(tk.Frame):

    '''Viewer class'''

    def __init__(self, parent, controller):
    
        '''initialiser'''
    
        # setup frame
        tk.Frame.__init__(self, parent)
        self.master = controller
        self.master.title("Logplotter")
        self.pack(fill="both", expand=1)
        
        # load boreholes from model (breaks design pattern slightly?)
        holes = self.master.model.bhs
        
        # add a menu bar
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        # file menu
        fileMenu = tk.Menu(menu, tearoff=False)
        fileMenu.add_command(label="Save as image", command=self.save_as_image)
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=controller.exit)
        # view menu
        viewMenu = tk.Menu(menu, tearoff=False)
        viewMenu.add_command(label="Set background colour", command=self.change_background)
        # view submenu: display log
        logMenu = tk.Menu(viewMenu, tearoff=False)
        for hole in holes:
            logMenu.add_command(label=hole, command=partial(self.display_log, hole))
        viewMenu.add_cascade(label="Display Log", menu=logMenu)
        # add submenus to menu bar
        menu.add_cascade(label="File", menu=fileMenu)
        menu.add_cascade(label="View", menu=viewMenu)
        
        # set up figure & canvas
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.fig.patch.set_facecolor('w')
        self.ax = self.fig.add_subplot(111)
        # self.line1 = a line (for e.g. change colour access)
        # self.line2 = another line
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
    def save_as_image(self):
    
        '''Save figure as image'''
        
        savename = asksaveasfilename(defaultextension='.png')
        if savename:
            self.fig.savefig(savename, dpi=150)
        
    def display_log(self, hole):
    
        '''Select log to display'''
        
        # display temporary load screen ?????
        
        # get data df
        df = self.master.model.fetch_data(hole)
        if not df.empty:
            xs,ys = df.x.values, df.y.values

        # redraw
        self.ax.clear()
        self.ax.plot(xs,ys,'r')
        self.canvas.draw()
        
    def change_background(self):
    
        '''Change figure background'''
        
        color = askcolor(initialcolor="#ffffff", title="Choose background colour")
        self.fig.patch.set_facecolor(color[1])
        self.canvas.draw()
        
        
class Menu(tk.Frame):
    pass
        

class Model(object):
    
    '''Model class'''
    
    def __init__(self):
        '''initialiser'''
        self.bhs = json.load(open('holes.json','r'))
        self.data = pd.DataFrame(columns=['x','y'])
        
    def fetch_data(self, bh):
        '''fetch data from "database"'''
        try:
            df = pd.read_json('./db/{}.json'.format(bh), orient='columns')
        except ValueError:
            print 'Data could not be loaded from db'
        else:
            self.data.x = df.x.values
            self.data.y = df.y.values
            return self.data
        
        
# main loop
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("400x300")
    root.mainloop()
