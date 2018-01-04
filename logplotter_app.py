"""
Logplotter application

TODO:
 * Make scatterplots faster
 * Fix panel formatting
 * Use matplotlib's 'set_data' method to update graph?
 * Fix save_as_image, see https://tkinter.unpythonic.net/wiki/tkFileDialog
 * Use caching to store logs <-- USE A 'MEMOIZE' DECORATOR!
 * Add legend on second page (linked to figure properties, in new module)
 * Implement application-level logging (using logging)

NOTES:
 * Structure: https://stackoverflow.com/questions/17466561/best-way-to-structure-a-tkinter-application
 * REFERENCE: http://www.tcl.tk/man/tcl8.5/TkCmd/contents.htm
 * Caching: https://www.blog.pythonlibrary.org/2016/02/25/python-an-intro-to-caching/
 * http://effbot.org/tkinterbook/canvas.htm
"""

from __future__ import print_function, division
import json
from functools import partial
import Tkinter as tk
from tkColorChooser import askcolor
from tkFileDialog import asksaveasfilename
import pandas as pd
from PIL import Image

import matplotlib
matplotlib.use("TkAgg")
from matplotlib import style

from logplotter_sql import dbConnect
from panels import (LithoPanel, DepthPanel, PSPRPanel,
                    ModPanel, HTUPanel, TadpolePanel)
from widgets import ControlButton

__version__ = '0.1'

style.use('bmh')


class LogPlotterApp(tk.Tk):

    """Application-level controller class"""

    def __init__(self):

        """Initialise"""

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

        """Raise page"""

        frame = self.frames[frm]
        frame.tkraise()

    @staticmethod
    def _exit():

        """Quit application"""

        root.quit()
        root.destroy()


class ViewPage(tk.Frame):

    """Viewer class"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, parent, controller):

        """Initialise"""

        # setup frame
        tk.Frame.__init__(self, parent)
        self.master = controller
        self.master.title("Logplotter")
        self.pack(fill="both", expand=1)

        # set log panel visibility
        self.visible = {}
        for i in xrange(7):
            self.visible[i] = tk.BooleanVar()
            self.visible[i].set(True)

        # add a MenuBar
        menu = MenuBar(self)
        self.master.config(menu=menu)

        # set up log panels
        c1 = DepthPanel(self)
        c2 = LithoPanel(self, name='Litho.')
        c3 = ModPanel(self, modulus='Young')
        c4 = ModPanel(self, modulus='Poisson')
        c5 = HTUPanel(self)
        c6 = PSPRPanel(self)
        c7 = TadpolePanel(self)
        self.canvases = [c1, c2, c3, c4, c5, c6, c7]

        # grid and configure log panels
        for i, c in enumerate(self.canvases):
            c.show()
            c.get_tk_widget().grid(row=0, column=i+1, sticky='nsew', rowspan=6)
            self.columnconfigure(i+1, weight=8 if i < 2 else 1)
        self.rowconfigure(0, weight=1)

        # add pager buttons, label
        self.pg_label = tk.Label(self, anchor='e',
                                 textvariable=self.master.model.page)
        self.pg_label.grid(row=1, column=0, columnspan=3)
        self.pgup_button = ControlButton(self, text=u'\u21E7', width=45,
                                         height=45, command=self.pg_dn,
                                         state='disabled')
        self.pgdn_button = ControlButton(self, text=u'\u21E9', width=45,
                                         height=45, command=self.pg_up)
        self.quit_button = ControlButton(self, text=u'\u274C', width=45,
                                         height=45, command=self.master._exit)
        self.pgup_button.grid(row=0, column=0, sticky='n')
        self.pgdn_button.grid(row=1, column=0, sticky='n')
        self.quit_button.grid(row=2, column=0, sticky='n')

        # add depth tracker label
        self.depth_var = tk.StringVar()
        self.depth_label = tk.Label(self, relief='groove', anchor='w',
                                    textvariable=self.depth_var)
        self.depth_label.grid(row=6, column=1, sticky='nsew', columnspan=2)
        for c in self.canvases:
            c.mpl_connect('motion_notify_event', self.on_move_event)

    def save_as_image(self):

        """Save figure as image"""

        # get desired filetype from user
        ftypes = [('Portable Network Graphics', '*.png'),
                  ('JPEG', '*.jpg'),
                  ('Adobe Portable Document Format', '*.pdf')]
        savename = asksaveasfilename(defaultextension='.png', filetypes=ftypes)

        # combine figures
        if savename:
            figures = [c.save_image() for c in self.canvases]
            width = sum([f.size[1] for f in figures])
            height = max([f.size[0] for f in figures])
            image = Image.new('RGBA', (width, height))
            x_offset = 0
            for f in figures:
                image.paste(f, (x_offset, 0))
                x_offset += f.size[0]

        # save to file
        image.save(savename)

    def display_log(self, bh):

        """Select log to display"""

        # get data dataFrame
        data = self.master.model.get_data(bh)

        # disable pd_dn_button
        self.pgup_button.state = 'disabled'

        # redraw
        for c in self.canvases:
            if isinstance(c, DepthPanel):
                c.plot(data['tbl_elev'])
            elif isinstance(c, LithoPanel):
                c.plot(data['tbl_lith'])
            elif isinstance(c, PSPRPanel):
                c.plot(data['tbl_pspr'])
            elif isinstance(c, ModPanel):
                c.plot(data['tbl_mods'])
            elif isinstance(c, HTUPanel):
                c.plot(data['tbl_htus'], data['tbl_pfls'])
            elif isinstance(c, TadpolePanel):
                c.plot(data['tbl_dips'])
            c.set_depthlims(0, 100)

    def change_background(self):

        """Change figure background"""

        color = askcolor(initialcolor="#ffffff", title="Set background colour")
        for c in self.canvases:
            c.set_facecolor(color)

    def toggle_panel(self, i):

        """Toggle log panels on/off"""

        if self.visible[i]:
            self.canvases[i].get_tk_widget().grid_remove()
        else:
            self.canvases[i].get_tk_widget().grid()
        self.visible[i] = not self.visible[i]

    def on_move_event(self, event):

        """Report depth by tracking mouse position"""

        c = self.canvases[0]
        f, ax = c.figure, c.ax_log
        top = ax.get_position().y1 * f.get_size_inches()[1] * f.dpi
        if event.inaxes and event.y < top:
            self.depth_var.set('mD: {:.2f} m'.format(event.ydata))

    def pg_up(self):

        """Increment page, update pager button state"""

        # skip in no bh loaded
        if not self.master.model.current_bh:
            return

        # get page number, pagemax
        pg = self.master.model.page
        pgmax = self.master.model.pagemax

        # update buttons, page number
        if pg == pgmax-1 and self.pgdn_button.state == 'normal':
            self.pgdn_button.state = 'disabled'
        elif pg == 1 and self.pgup_button.state == 'disabled':
            self.pgup_button.state = 'normal'
        self.master.model.page += 1

        # update data
        pg = self.master.model.page
        ymin, ymax = (pg-1)*100, pg*100
        for c in self.canvases:
            c.set_depthlims(ymin, ymax)

    def pg_dn(self):

        """Decrement page, update pager button state"""

        # skip if no bh loaded
        if not self.master.model.current_bh:
            return

        # get page number, pagemax
        pg = self.master.model.page
        pgmax = self.master.model.pagemax

        # update buttons, page number
        if pg == pgmax and self.pgdn_button.state == 'disabled':
            self.pgdn_button.state = 'normal'
        elif pg <= 2 and self.pgup_button.state == 'normal':
            self.pgup_button.state = 'disabled'
        self.master.model.page -= 1

        # update data
        pg = self.master.model.page
        ymin, ymax = (pg-1)*100, pg*100
        for c in self.canvases:
            c.set_depthlims(ymin, ymax)


class MenuBar(tk.Menu):

    """Menu bar class"""

    def __init__(self, parent):

        """Initialise"""

        tk.Menu.__init__(self, parent)

        # file menu
        file_menu = tk.Menu(self, tearoff=False)
        file_menu.add_command(label="Save as image",
                              command=parent.save_as_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=parent.master._exit)

        # view menu
        view_menu = tk.Menu(self, tearoff=False)
        view_menu.add_command(label="Set background colour",
                              command=parent.change_background)

        # view submenu: display borehole data
        log_menu = tk.Menu(view_menu, tearoff=False)
        for bh, in parent.master.model.bhs:
            log_menu.add_command(label=bh,
                                 command=partial(parent.display_log, bh))
        view_menu.add_cascade(label="Display Log", menu=log_menu)

        # view submenu: display panels
        panel_menu = tk.Menu(view_menu, tearoff=False)
        for i in xrange(7):
            panel_menu.add_checkbutton(label='Panel {}'.format(i),
                                       onvalue=True, offvalue=False,
                                       variable=parent.visible[i],
                                       command=partial(parent.toggle_panel, i))
        view_menu.add_cascade(label='Toggle Panels', menu=panel_menu)

        # add menus to menu bar
        self.add_cascade(label="File", menu=file_menu)
        self.add_cascade(label="View", menu=view_menu)


class Model(object):

    """Data model"""

    @property
    def page(self):
        return self._page.get()

    @page.setter
    def page(self, num):
        self._page.set(num)

    def __init__(self, parent):

        """Initialise"""

        self.parent = parent
        
        # get boreholes from db
        # self.bhs = json.load(open('holes.json', 'r'))
        with dbConnect('./sqlite/example2.db') as cur:
            self.bhs = cur.execute(dbConnect.qry_bhs).fetchall()
        self.current_bh = None
        self.data = {}

        # init page numbers
        self._page = tk.IntVar()
        self.page = 1
        self.pagemax = 1

    def db_fetch(self, bh):

        """Fetch data from sqlite database"""

        # fetch data to dict
        with dbConnect('./sqlite/example2.db') as cur:
            tables = cur.execute(dbConnect.qry_tables).fetchall()
            for t, in tables:
                rows = cur.execute(dbConnect.qry_data.format(t, bh)).fetchall()
                cols = zip(*cur.description)[0]
                self.data[t] = pd.DataFrame(rows, columns=cols)

        # set current bh, max pages
        self.current_bh = bh
        self.pagemax = int(1+(self.data['tbl_elev']['chainage'].max() // 100))

    def get_data(self, bh):

        """Return data for plotting"""

        # reload model if necessary
        if not bh == self.current_bh:
            # TODO: check if cache contains bh
            self.page = 1
            self.db_fetch(bh)
            return self.data


# main loop
if __name__ == '__main__':

    root = LogPlotterApp()
    root.geometry("500x650")
    root.mainloop()
