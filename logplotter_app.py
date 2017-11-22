from __future__ import print_function, division
import Tkinter as tk
import ttk as ttk
from tkColorChooser import askcolor
from tkFileDialog import asksaveasfilename

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from functools import partial
import json # temporary in place of db
import pandas as pd
import io
from PIL import Image

from logplotter_sql import dbConnect
from panels import LogPanel, LithoPanel

style.use('bmh')

"""
TODO:
* Maintain MVC design pattern
* Use matplotlib's 'set_data' method to update graph (i.e. instead of cla(), draw())?
* Fix save_as_image method, see https://tkinter.unpythonic.net/wiki/tkFileDialog
* Use caching to store recently-loaded logs (to avoid excessive db fetches).
* Add legend on second page (linked to figure properties, which should be class in separate module)
* Implement application-level logging (using logging)
"""

# Structure:   https://stackoverflow.com/questions/17466561/best-way-to-structure-a-tkinter-application
# REFERENCE:   http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm
# Caching:     https://www.blog.pythonlibrary.org/2016/02/25/python-an-intro-to-caching/
#              http://effbot.org/tkinterbook/canvas.htm


class LogPlotterApp(tk.Tk):

    '''Application-level controller class'''

    def __init__(self):

        '''Initialiser'''

        tk.Tk.__init__(self)

        # set up model
        self.model = Model(self)

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
        self.c1 = LithoPanel(self)
        self.c2 = LogPanel(self)
        self.c3 = LogPanel(self)
        self.canvases = [self.c1, self.c2, self.c3]

        # grid and configure log panels
        for i, c in enumerate(self.canvases):
            c.show()
            c.get_tk_widget().grid(row=0, column=i+1, sticky='nsew', rowspan=6)
            self.columnconfigure(i+1, weight=1)
        self.rowconfigure(0, weight=1)

        # add pager buttons, label
        self.pgLabel = tk.Label(self, anchor='e', textvariable=self.master.model._page)
        self.pgLabel.grid(row=1, column=0)
        self.pgupButton = ControlButton(self, text=u'\u21E7', command=self.pg_up, width=45, height=45)
        self.pgdnButton = ControlButton(self, text=u'\u21E9', command=self.pg_dn, width=45, height=45, state='disabled')
        self.pgupButton.grid(row=0, column=0)
        self.pgdnButton.grid(row=2, column=0)

        # add depth tracker label
        self.depthVar = tk.StringVar()
        self.depthLabel = tk.Label(self, relief='groove', anchor='w', textvariable=self.depthVar)
        self.depthLabel.grid(row=6, column=1, sticky='nsew')
        for c in self.canvases:
            c.mpl_connect('motion_notify_event', self.on_move_event)

    def save_as_image(self):

        '''Save figure as image'''

        # get desired filetype from user
        filetypes = [('Portable Network Graphics', '*.png'),
                     ('JPEG', '*.jpg'),
                     ('Adobe Portable Document Format', '*.pdf')]
        savename = asksaveasfilename(defaultextension='.png', filetypes=filetypes)

        # combine figures
        if savename:
            figures = [c.save_image() for c in self.canvases]
            width  = sum([f.size[1] for f in figures])
            height = max([f.size[0] for f in figures])
            image = Image.new('RGBA', (width, height))
            x_offset = 0
            for f in figures:
                image.paste(f, (x_offset, 0))
                x_offset += f.size[0]

        # save to file
        image.save(savename)

    def display_log(self, bh, page=1):

        '''Select log to display'''

        # get data dataFrame
        df, lith = self.master.model.get_data(bh, page)
        if not df.empty:
            xs,ys = df.x.values, df.y.values

        # redraw
        for c in self.canvases:
            if isinstance(c, LithoPanel):
                c.plot_data(lith)
            else:
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

    def pg_up(self):

        '''Increment page, update pager buttons'''

        # skip in no bh loaded
        if not self.master.model.current_bh:
            return

        # get page number
        pgnum = self.master.model.page

        # update buttons, page number
        if pgnum == self.master.model.pagemax - 1 and self.pgupButton.state == 'normal':
            self.pgupButton.state = 'disabled'
        elif pgnum == 1 and self.pgdnButton.state == 'disabled':
            self.pgdnButton.state = 'normal'
        self.master.model.pg_up()

        # update data
        self.display_log(self.master.model.current_bh,
                         self.master.model.page)

    def pg_dn(self):

        '''Decrement page, update pager buttons'''

        # skip in no bh loaded
        if not self.master.model.current_bh:
            return

        # get page number
        pgnum = self.master.model.page

        # update buttons, page number
        if pgnum == self.master.model.pagemax and self.pgupButton.state == 'disabled':
            self.pgupButton.state = 'normal'
        elif pgnum <= 2 and self.pgdnButton.state == 'normal':
            self.pgdnButton.state = 'disabled'
        self.master.model.pg_dn()

        # update data
        self.display_log(self.master.model.current_bh,
                         self.master.model.page)


class MenuBar(tk.Menu):

    '''Menu bar class'''

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


class Model(object):

    '''Data model'''

    @property
    def page(self):
        return self._page.get()

    @page.setter
    def page(self, num):
        self._page.set(num)

    def __init__(self, parent):

        '''Initialiser'''

        self.parent = parent
        self.bhs = json.load(open('holes.json', 'r'))
        self.data = pd.DataFrame(columns=['x', 'y'])
        self.current_bh = None
        self._page = tk.IntVar()
        self.page = 1
        self.pagemax = 1
        
        # TEMP: litho dataframe
        self.lith = pd.DataFrame(columns=['end','start','lithname'])

    def db_fetch(self, bh):

        '''Fetch data from sqlite database'''

        # fetch data
        data = {}
        with dbConnect('./example.db') as c:
            tables = c.execute(dbConnect.qry_tables).fetchall()
            for table, in tables:
                data[table] = c.execute(dbConnect.qry_data.replace('?', table)).fetchall()

        # set data, current bh, max pages
        self.data.x, self.data.y = zip(*data['tbl_pspr'])
        self.current_bh = bh
        self.pagemax = (self.data.x.max() // 100) + 1
        
        # TEMP: set self.lith to store lithology info
        self.lith.end, self.lith.start, self.lith.lithname = zip(*data['tbl_lith'])

    def get_data(self, bh, page):

        '''Return data for plotting (page 1 by default)'''

        # reload model if necessary
        if not bh == self.current_bh:
            # TODO: check if cache contains bh
            self.db_fetch(bh)

        # return specified page
        ymin, ymax = (page - 1)*100, page*100
        return (self.data[(self.data['x'] >= ymin) & (self.data['x'] < ymax)],
                self.lith[(self.lith['start'] >= ymin) & (self.lith['end'] < ymax)])

    def pg_up(self):

        '''Page up'''

        if not self.page == self.pagemax:
            self.page += 1

    def pg_dn(self):

        '''Page down'''

        if not self.page == 1:
            self.page -= 1


class ControlButton(ttk.Frame, object):

    '''Implementation of ttk.Button with size adjustment & state property'''

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._btn.configure(state=state)
        self._state = state

    def __init__(self, parent, height=None, width=None, text='', command=None, state='normal'):

        '''Initialiser'''

        self._state = state
        ttk.Frame.__init__(self, parent, height=height, width=width)
        self.pack_propagate(0)
        s = ttk.Style()
        s.configure('CButton.TButton', font=('Helvetica, 26'))
        self._btn = ttk.Button(self, text=text, command=command, 
                               state=state, style='CButton.TButton')
        self._btn.pack(fill=tk.BOTH, expand=1)


# main loop
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("500x650")
    root.mainloop()
