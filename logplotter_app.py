#!/usr/bin/env python

import Tkinter as tk
import ttk as ttk  # basically the CSS for tkinter!

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
                                               NavigationToolbar2TkAgg)


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
        tk.Frame.__init__(self, parent)
        self.master = controller
        self.init_window()
        
    def init_window(self):
        # add title
        self.master.title("Logplotter application")
        self.pack(fill="both", expand=1)
        
        # add a menu bar
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        file, edit = tk.Menu(menu, tearoff=False), tk.Menu(menu, tearoff=False)
        file.add_command(label="Exit", command=self.client_exit)
        edit.add_command(label="Display log", command=self.display_log)
        menu.add_cascade(label="File", menu=file)
        menu.add_cascade(label="Edit", menu=edit)
        
    # menu functions
    def display_log(self):
        f = Figure(figsize=(5,5), dpi=100)
        f.patch.set_facecolor('w')
        ax = f.add_subplot(111)
        ax.plot([1,2,5,3,7,8],[5,4,9,3,2,7])
        canvas = FigureCanvasTkAgg(f, self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
    def client_exit(self):
        exit()

        
# main loop
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("400x300")
    root.mainloop()
