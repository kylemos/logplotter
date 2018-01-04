"""
Widget classes for use in logplotter application:

ControlButton (class)   - derived from ttk.Button but with 'state' as property.
"""

import Tkinter as tk
import ttk as ttk

class ControlButton(ttk.Frame, object):

    """Implementation of ttk.Button with size adjustment & state property"""

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._btn.configure(state=state)
        self._state = state

    def __init__(self, parent, height=None, width=None,
                 text='', command=None, state='normal'):

        """Initialise"""

        self._state = state
        ttk.Frame.__init__(self, parent, height=height, width=width)
        self.pack_propagate(0)
        s = ttk.Style()
        s.configure('CButton.TButton', font=('Helvetica, 24'))
        self._btn = ttk.Button(self, text=text, command=command, 
                               state=state, style='CButton.TButton')
        self._btn.pack(fill=tk.BOTH, expand=1)
