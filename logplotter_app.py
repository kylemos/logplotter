#!/usr/bin/env python

import Tkinter as tk
import ttk as ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib import style
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
                                               NavigationToolbar2TkAgg)
import json # temporary, in place of db
from functools import partial  # <-- Genius tool!!!

style.use('bmh')

"""
TODO:
 * Use matplotlib's 'set_data' method to update graph
 * 
"""

f = Figure(figsize=(5,5), dpi=100)
f.patch.set_facecolor('w')
ax = f.add_subplot(111)

class LogPlotterApp(tk.Tk):

    def __init__(self):
    
        tk.Tk.__init__(self)
        container = tk.Frame(self)
        
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        frame = StartPage(container, self)
        frame.grid(row=0, column=0, sticky="nsew")
        
        # dict to hold frames
        self.frames = {}
        self.frames[StartPage] = frame
        
        self.show_frame(StartPage)
        
    def show_frame(self, cont):
    
        frame = self.frames[cont]
        frame.tkraise()
        
                                               
class StartPage(tk.Frame):

    def __init__(self, parent, controller):
    
        # setup frame
        tk.Frame.__init__(self, parent)
        self.master = controller
        self.master.title("Logplotter")
        self.pack(fill="both", expand=1)
        
        # load list of holes
        with open('holes.json','r') as fp:
            holes = json.load(fp)
        
        # add a menu bar
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        # file menu
        fileMenu = tk.Menu(menu, tearoff=False)
        fileMenu.add_command(label="Save as image")
        fileMenu.add_separator()
        fileMenu.add_command(label="Exit", command=self.client_exit)
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
        
        # add canvas
        self.canvas = FigureCanvasTkAgg(f, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        
    # menu methods
    def display_log(self, hole):
    
        # step1: get data from db
        with open('data.json','r') as fp:
            data = json.load(fp)
        xs,ys = data.get(hole)
        
        # step2: update graph
        # f = Figure(figsize=(5,5), dpi=100)
        # f.patch.set_facecolor('w')
        # ax = f.add_subplot(111)
        
        ax.cla()
        ax.plot(xs,ys,'r')
        self.canvas.draw()
        
    def change_background(self):
        
        
    def client_exit(self):
        exit()
        
        
# main loop
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("400x300")
    root.mainloop()
