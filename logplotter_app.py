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

style.use('bmh')

"""
TODO:
 * MVC design pattern!
 * Use matplotlib's 'set_data' method to update graph?
 * Improve save_as_image method (filename list, etc...) - see https://tkinter.unpythonic.net/wiki/tkFileDialog
 * Add live-updating statusbar
"""

f = Figure(figsize=(5,5), dpi=100)
f.patch.set_facecolor('w')
ax = f.add_subplot(111)

class LogPlotterApp(tk.Tk):

    '''Application-level controller class'''

    def __init__(self):
    
        '''initialiser'''
        
        tk.Tk.__init__(self)
        
        # set up container frame
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # store page classes in dict
        self.frames = {}
        for F in [ViewPage]:
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        # (default) show ViewPage
        self.show_frame(ViewPage)
        
    def show_frame(self, cont):
    
        '''Raise page'''
        
        frame = self.frames[cont]
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
        
        # load list of holes
        with open('holes.json','r') as fp:
            holes = json.load(fp)
        
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
        
        # add canvas
        self.canvas = FigureCanvasTkAgg(f, self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
    def save_as_image(self):
    
        '''Save figure as image'''
        
        savename = asksaveasfilename(defaultextension='.png')
        if savename:
            f.savefig(savename, dpi=150)
        
    def display_log(self, hole):
    
        '''Select log to display'''
        
        # display load screen
        # w = self.canvas.create_text(text="Loading...", font=("Helvetica", 16))
        # time.sleep(2)
    
        # step1: get data from db
        with open('data.json','r') as fp:
            data = json.load(fp)
        xs,ys = data.get(hole)
        # w.delete()
        
        #line1.set_data(xs,ys)
        ax.clear()
        ax.plot(xs,ys,'r')
        self.canvas.draw()
        
    def change_background(self):
    
        '''Change figure background'''
        
        color = askcolor(initialcolor="#ffffff", title="Choose background colour")
        f.patch.set_facecolor(color[1])
        self.canvas.draw()
        

class Model(object):
    
    '''Model class'''
    
    def __init__(self):
        pass
    
        
        
# main loop
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("400x300")
    root.mainloop()
