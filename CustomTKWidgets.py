import os
import traceback
import tkinter as tk
import tkinter.filedialog
import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime
from PIL import Image
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Callable
from typing_extensions import Literal

class LabeledFrame(ctk.CTkFrame):
    '''
    A regular frame but with a label at the top
    '''
    def __init__(self, *args, label_text:str='', label_sticky:str='left', \
        **kwargs):
        super().__init__(*args, fg_color='transparent', bg_color='transparent',\
        **kwargs)

        self.labelFrame = ctk.CTkFrame(self)
        self.label = ctk.CTkLabel(self.labelFrame,text=label_text)
        self.split = ttk.Separator(master=self,orient='horizontal')
        self.frame = ctk.CTkFrame(self)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1,weight=1)

        if label_sticky == 'left':
            s = 'w'
            c = 0
        elif label_sticky == 'center':
            s = 'ew'
            c = 1
        else:
            s = 'e'
            c = 2

        self.label.grid(row=0,column=c,padx=5,pady=3,sticky=s)
        self.labelFrame.grid(row=0,column=0,columnspan=3,sticky='ew',padx=0,\
            pady=0)
        self.split.grid(row=1,column=0,columnspan=3,sticky='ew',padx=0,pady=0)
        self.frame.grid(row=2,column=0,columnspan=3,sticky='nsew',padx=0,pady=0)

    def get_frame(self):
        return self.frame
        
class CanvasFrame(LabeledFrame):
    '''
    A canvas frame which contains a canvas with a matplotlib figure inside of
    it. The frame also provides a statusbar which shows the current coordinate
    (as an int). The cursor position is also shown within the data view as two
    lines in order to help with picking exact positions on the graph.
    '''
    def __init__(self, *args, figsize:tuple[float,float]=(6.0,6.0), \
        mode:Literal['cursor','save only','preview']='cursor', zoom=False, \
            cwidth=100, cheight=100, **kwargs):
        super().__init__(*args, width=cwidth, height=cheight, **kwargs)

        # init data
        self.mouse_move = None
        self.click = None
        self.axes_enter = None
        self.axes_leave = None
        self.state = 'normal'
        self.x = 0
        self.y = 0
        self.xlim = (0,0)
        self.ylim = (0,0)
        self.xlimh = (-np.inf,np.inf)
        self.ylimh = (-np.inf,np.inf)
        self.zoomxs = []
        self.zoomys = []
        self.clickx = None
        self.clicky = None
        self.clicks = 0
        self.prevclickx = None
        self.prevclicky = None
        self.lastvline = None
        self.lasthline = None
        self.clickvline = None
        self.clickhline = None

        # create 2x1 grid where the graph object is resizeable and the statusbar
        # is  not
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        # BUG: resizing is causing the cursor stuff to freak out I tried to fix
        # it using the cwidth cheight stuff but it is still off but at least
        # useable
        # It only appears to occur when the cursor moves in and out of the 
        # figure now. Maybe there is something I can do to get the figure to 
        # match the grid size

        self.figure = plt.figure(figsize=figsize)
        # this is for getting labels to show up
        offset = 0.1 * (1 + (650 - cwidth) / 650)
        width = 0.95 - offset
        self.ax = self.figure.add_axes([offset,offset,width,width])

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=4,\
            sticky='nsew',padx=3,pady=3)
        self.canvas.get_tk_widget().configure(width=cwidth,height=cheight)

        if mode == 'cursor':        
            self.mouse_move = self.canvas.mpl_connect('motion_notify_event',\
                self.update_mouse_pos)
            self.click = self.canvas.mpl_connect('button_press_event',\
                self.clicked)
            self.axes_enter = self.canvas.mpl_connect('axes_enter_event',\
                self.remove_mouse)
            self.axes_leave = self.canvas.mpl_connect('axes_leave_event',\
                self.return_mouse)
        if mode == 'cursor' or mode == 'save only':
            self.seperator = ttk.Separator(master=self.frame,\
                orient='horizontal')
            self.seperator.grid(row=1,column=0,columnspan=4,sticky='ew')

        if mode == 'cursor':
            self.statusbartext = tk.StringVar(self,\
                f"Mouse Position ({self.x:.0f},{self.y:.0f})")
            self.statusbar = ctk.CTkLabel(master=self.frame,\
                textvariable=self.statusbartext, height=1)
            self.statusbar.grid(row=2, column=0, padx=2, sticky='w')
        if zoom:
            homeicon = ctk.CTkImage(\
                Image.open(\
                    os.path.dirname(os.path.realpath(__file__))+\
                        r'/assets/home.png'))
            self.homebutton = ctk.CTkButton(master=self.frame, image=homeicon, \
                command=self.go_home, text ='', border_width=0, \
                    border_spacing=0, width=28, height=28)
            self.homebutton.grid(row=2, column=2, padx=2, stick='nse')
            self.state = 'zoom'
        if mode == 'cursor' or mode == 'save only':
            saveicon = ctk.CTkImage(\
                Image.open(\
                    os.path.dirname(os.path.realpath(__file__))+\
                        r'/assets/save.png'))
            self.savebutton = ctk.CTkButton(master=self.frame, image=saveicon, \
                command=self.save_image, text ='', border_width=0, \
                    border_spacing=0, width=28, height=28)
            self.savebutton.grid(row=2, column=3, padx=2, sticky='nsew')

        self.redraw()

    def zoom_mode(self):
        self.zoomxs = []
        self.zoomys = []
        self.clicks = 0
        self.state = 'zoom'
        self.update_statusbar()

    def zoom(self):
        self.xlim = (np.min(self.zoomxs), np.max(self.zoomxs))
        self.ylim = (np.min(self.zoomys), np.max(self.zoomys))

        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim) #type:ignore

        self.zoomxs = []
        self.zoomys = []
        self.clicks = 0

        self.redraw()

    def init_home(self):
        if self.xlimh[1] == np.inf:
            self.xlimh = self.ax.get_xlim()
            self.ylimh = self.ax.get_ylim()

    def go_home(self):
        self.ax.set_xlim(self.xlimh)
        self.ax.set_ylim(self.ylimh) #type:ignore

        self.update_statusbar()
        self.redraw()
    
    def redraw(self):
        self.canvas.draw()

# this probably should not be here because it requires hooking up A LOT of stuff
#    def replace_figure(self, figure:Figure):
#        self.figure = figure
#
#        self.canvas.get_tk_widget().pack_forget()
#        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
#        self.canvas.draw()
#        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        
    def update_mouse_pos(self,event):
        if event.xdata is not None:
            self.x = round(event.xdata)
            self.y = round(event.ydata)
            self.update_statusbar()
            self.update_cursor()

    def update_statusbar(self):
        if self.state == 'normal':
            self.statusbartext.set(f"Mouse Position ({self.x:.0f},{self.y:.0f})")
        elif self.state == 'zoom':
            self.statusbartext.set(f"ZOOM: Mouse Position ({self.x:.0f},{self.y:.0f})")

    def update_cursor(self):
        if self.lastvline is not None: self.lastvline.remove()
        self.lastvline = self.ax.axvline(self.x,color="gray",ls=":")
        if self.lasthline is not None: self.lasthline.remove()
        self.lasthline = self.ax.axhline(self.y,color="gray",ls=":")
        self.redraw()

    def remove_mouse(self,event):
        self.configure(cursor="none")
    
    def return_mouse(self,event):
        self.configure(cursor="")

    def clicked(self,event):
        if self.clickvline is not None: 
            self.clickvline.remove()
            self.clickvline = None
        else:
            self.clickvline = self.ax.axvline(self.x,color="gray",ls=":")

        if self.clickhline is not None:
            self.clickhline.remove()
            self.clickhline = None
        else:
            self.clickhline = self.ax.axhline(self.y,color="gray",ls=":")

        if self.state == 'normal':
            self.prevclickx = self.clickx
            self.clickx = self.x # closest integer value
            self.prevclicky = self.clicky
            self.clicky = self.y # closest integer value
        elif self.state == 'zoom':
            self.clicks = self.clicks + 1
            self.zoomxs.append(self.x)
            self.zoomys.append(self.y)
            if self.clicks == 2:
                self.zoom()

        self.redraw()

    def get_clicks(self) -> tuple[int,int,int,int]:
        # Return clicks as left, bottom, right, top
        if not None in \
            [self.prevclickx,self.prevclicky,self.clickx,self.clicky]:
            left = min(self.clickx,self.prevclickx) # type: ignore
            right = max(self.clickx,self.prevclickx) # type: ignore
            bottom = min(self.clicky,self.prevclicky) # type: ignore
            top = max(self.clicky,self.prevclicky) # type: ignore
        else:
            left, right, bottom, top = 0, 0, 0, 0

        return (left, bottom, right, top)

    def save_image(self):
        f = tkinter.filedialog.asksaveasfile(initialdir=os.getcwd(), \
            initialfile='Untitled.png', defaultextension='.png', \
                filetypes=[('PNG Image','*.png'),('PDF Page','*.pdf'),\
                    ("Vector Graphic",'*.svg')])
        if f is not None:
            self.figure.savefig(os.path.realpath(f.name),dpi=100)

    def update_mode(self,mode:str,zoom=False):
        if not(self.mouse_move is None):
            self.canvas.mpl_disconnect(self.mouse_move)
            self.canvas.mpl_disconnect(self.click) #type:ignore
            self.canvas.mpl_disconnect(self.axes_enter) #type:ignore
            self.canvas.mpl_disconnect(self.axes_leave) #type:ignore
            self.return_mouse('')
        if hasattr(self,'statusbar'): self.statusbar.grid_forget()
        if hasattr(self,'seperator'): self.seperator.grid_forget()
        if hasattr(self,'savebutton'): self.savebutton.grid_forget()
        if hasattr(self,'zoombutton'): self.zoombutton.grid_forget()
        if hasattr(self,'homebutton'): self.homebutton.grid_forget()
        if not(self.lasthline is None): 
            self.lasthline.remove()
            self.lasthline = None
        if not(self.lastvline is None): 
            self.lastvline.remove()
            self.lastvline = None
        if not(self.clickhline is None): 
            self.clickhline.remove()
            self.clickhline = None
        if not(self.clickvline is None): 
            self.clickvline.remove()
            self.clickvline = None

        if mode == 'cursor':        
            self.mouse_move = self.canvas.mpl_connect('motion_notify_event',\
                self.update_mouse_pos)
            self.click = self.canvas.mpl_connect('button_press_event',\
                self.clicked)
            self.axes_enter = self.canvas.mpl_connect('axes_enter_event',\
                self.remove_mouse)
            self.axes_leave = self.canvas.mpl_connect('axes_leave_event',\
                self.return_mouse)

            self.statusbartext = tk.StringVar(self,\
                f"Mouse Position ({self.x:.0f},{self.y:.0f})")
            self.statusbar = ctk.CTkLabel(master=self.frame,\
                textvariable=self.statusbartext, height=1)
            self.statusbar.grid(row=2, column=0, sticky='w')
        if mode == 'cursor' or mode == 'save only':
            self.seperator = ttk.Separator(master=self.frame,\
                orient='horizontal')
            self.seperator.grid(row=1,column=0,columnspan=2,sticky='ew')

            saveicon = ctk.CTkImage(\
                Image.open(\
                    os.path.dirname(os.path.realpath(__file__))+\
                        r'/assets/save.png'))
            self.savebutton = ctk.CTkButton(master=self.frame, image=saveicon, \
                command=self.save_image, text ='', border_width=0, \
                    border_spacing=0, width=28)
            self.savebutton.grid(row=2, column=1, sticky='nsew',pady=3)
        if zoom:
            zoomicon = ctk.CTkImage(\
                Image.open(\
                    os.path.dirname(os.path.realpath(__file__))+\
                        r'/assets/zoom.png'))
            homeicon = ctk.CTkImage(\
                Image.open(\
                    os.path.dirname(os.path.realpath(__file__))+\
                        r'/assets/home.png'))
            self.zoombutton = ctk.CTkButton(master=self.frame, image=zoomicon, \
                command=self.zoom_mode, text ='', border_width=0, \
                    border_spacing=0, width=28, height=28)
            self.homebutton = ctk.CTkButton(master=self.frame, image=homeicon, \
                command=self.go_home, text ='', border_width=0, \
                    border_spacing=0, width=28, height=28)
            self.zoombutton.grid(row=2, column=1, padx=2, stick='nse')
            self.homebutton.grid(row=2, column=2, padx=2, stick='nse')

class SubplotCanvas(CanvasFrame):
    def __init__(self, *args, axis_1_label:str='', axis_2_label:str='', \
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.figure.delaxes(self.ax) # type: ignore
        self.ax = None
        self.ax_1 = self.figure.add_subplot(211) # type: ignore
        self.ax_2 = self.figure.add_subplot(212) # type: ignore
        self.xlimh2 = self.xlim
        self.ylimh2 = self.ylim

        self.figure.tight_layout()
        self.figure.subplots_adjust(hspace=0.25,left=0.15)

        self.ax_1.set_title(axis_1_label)
        self.ax_2.set_title(axis_2_label)

        self.redraw()
        
    def remove_mouse(self,event):
        self.configure(cursor="none")
        self.ax = event.inaxes
    
    def return_mouse(self,event):
        self.configure(cursor="")
        self.ax = None

    def rename_plots(self, name_top, name_bottom):
        self.ax_1.set_title(name_top)
        self.ax_2.set_title(name_bottom)

        self.redraw()

    def init_home(self):
        if self.xlimh[1] == np.inf:
            self.xlimh = self.ax_1.get_xlim()
            self.ylimh = self.ax_1.get_ylim()
            self.xlimh2 = self.ax_2.get_xlim()
            self.ylimh2 = self.ax_2.get_ylim()

    def go_home(self):
        self.ax_1.set_xlim(self.xlimh)
        self.ax_1.set_ylim(self.ylimh) #type:ignore
        self.ax_2.set_xlim(self.xlimh2)
        self.ax_2.set_ylim(self.ylimh2) #type:ignore

        self.redraw()
        self.update_statusbar()
        self.state = 'normal'

class TraceCanvas(SubplotCanvas):
    def __init__(self, *args, \
                 orientation_1:tk.StringVar, orientation_2:tk.StringVar, \
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.orientation = None

        self.orientation_1 = orientation_1
        self.orientation_2 = orientation_2

    def clicked(self,event):
        if self.ax is self.ax_1:
            while len(self.ax.lines) > 0: #type:ignore
                self.ax.lines[-1].remove() #type:ignore
            if self.orientation.get() == 'x': #type:ignore
                self.clickhline = self.ax.axhline(self.y, color='grey') #type:ignore
                self.clickx = self.y
            else:
                self.clickhline = self.ax.axvline(self.x, color='grey') #type:ignore
                self.clickx = self.x
        elif self.ax is self.ax_2:
            while len(self.ax.lines) > 0: #type:ignore
                self.ax.lines[-1].remove() #type:ignore
            if self.orientation.get() == 'x': #type:ignore
                self.clickvline = self.ax.axhline(self.y, color='grey') #type:ignore
                self.clicky = self.y
            else:
                self.clickvline = self.ax.axvline(self.x, color='grey') #type:ignore
                self.clicky = self.x
        self.redraw()
    
    def remove_mouse(self,event):
        self.configure(cursor="none")
        self.ax = event.inaxes
        if self.ax is self.ax_1:
            self.orientation = self.orientation_1
        else:
            self.orientation = self.orientation_2
    
    def return_mouse(self,event):
        self.configure(cursor="")
        self.ax = None
        self.loc = None
        self.orientation = None

    def update_cursor(self):
        if self.ax is self.ax_1:
            while len(self.ax.lines) > 1:  #type:ignore
                self.ax.lines[-1].remove() #type:ignore
            if self.orientation.get() == 'x': #type:ignore
                self.lasthline = self.ax.axhline(self.y, color='gray',ls=':') #type:ignore
            else:
                self.lasthline = self.ax.axvline(self.x, color='gray',ls=':') #type:ignore
        elif self.ax is self.ax_2:
            while len(self.ax.lines) > 1:  #type:ignore
                self.ax.lines[-1].remove() #type:ignore
            if self.orientation.get() == 'x': #type:ignore
                self.lastvline = self.ax.axhline(self.y, color='gray',ls=':') #type:ignore
            else:
                self.lastvline = self.ax.axvline(self.x, color='gray',ls=':') #type:ignore
        self.redraw()

    def show_1(self, loc):
        while len(self.ax_1.lines) > 0: 
            self.ax_1.lines[-1].remove()
        if self.orientation_1.get() == 'x':
            self.clickhline = self.ax_1.axhline(loc, color='red')
            self.clickx = loc
        else:
            self.clickhline = self.ax_1.axvline(loc, color='red')
            self.clickx = loc
        self.redraw()

    def show_2(self, loc):
        while len(self.ax_2.lines) > 0: 
            self.ax_2.lines[-1].remove()
        if self.orientation_2.get() == 'x':
            self.clickvline = self.ax_2.axhline(loc, color='red')
            self.clicky = loc
        else:
            self.clickvline = self.ax_2.axvline(loc, color='red')
            self.clicky = loc
        self.redraw()

    def get_clicks(self) -> tuple[int, int]:
        # returns loc1, orient1, loc2, orient2
        if not None in [self.clickx,self.clicky]:
            loc1 = self.clickx
            loc2 = self.clicky
        else:
            (loc1, loc2) = (-1,-1)
        
        return (loc1, loc2)
        
class HistogramCanvas(CanvasFrame):
    def __init__(self, *args, min_bin:tk.IntVar, max_bin:tk.IntVar, \
                 title:str='', **kwargs):
        self.min_bin = min_bin
        self.max_bin = max_bin
        super().__init__(*args, **kwargs)
        self.ax.set_title(title)
        self.fbarmin = None
        self.fbarmax = None
        self.redraw()

    def update_cursor(self):
        if self.lastvline is not None: self.lastvline.remove()
        self.lastvline = self.ax.axvline(self.x,color="gray",ls=":")
        if self.lasthline is not None: self.lasthline.remove()
        self.lasthline = self.ax.axvline(self.x,color="gray",ls=":")
        self.redraw()

    def clicked(self,event):
        if self.clickhline is not None: self.clickhline.remove() 

        self.clickhline = self.clickvline # hline -> 2 clicks ago
        self.clickvline = self.ax.axvline(self.x,color="gray",ls=":") # vline -> last click

        self.prevclickx = self.clickx
        self.clickx = self.x # closest integer value

        self.redraw() # I fixed the bug here

    def get_clicks(self) -> tuple[int,int]:
        # Return clicks as x1,x2
        if not None in \
            [self.prevclickx,self.clickx]:
            x1 = min(self.clickx,self.prevclickx) # type: ignore
            x2 = max(self.clickx,self.prevclickx) # type: ignore

            self.clickx = None
            self.prevclickx = None

            if self.clickhline is not None: self.clickhline.remove() 
            if self.clickvline is not None: self.clickvline.remove() 
            self.clickhline = None
            self.clickvline = None
            if self.fbarmin is not None: self.fbarmin.remove()
            if self.fbarmax is not None: self.fbarmax.remove()

            self.fbarmin = self.ax.axvline(x1,color="black") #BUG: not showing up
            self.fbarmax = self.ax.axvline(x2,color="black") #BUG: not showing up
        else:
            x1,x2 = 0, 0
        self.redraw()

        return (x1,x2)
    
    def redraw(self):
        # this is an annoying fix but needed to fix the bug from above 
        self.ax.set_xlim(left=self.min_bin.get(), right=self.max_bin.get())
        self.canvas.draw()

class LabeledEntry(ctk.CTkFrame):
    '''
    An entry box which also has a units label after it.

    # Parameters
    var_ref:tk.Variable
        A reference to the variable which will be modified and displayed
    label_text:str
        The label text
    '''
    def __init__(self, *args, var_ref:tk.Variable, label_text:str='', \
        label_side:str='after', **kwargs):
        super().__init__(*args, width=0, bg_color='transparent',\
            fg_color='transparent', **kwargs)
        
        # init data
        self.var_ref = var_ref

        # init widgets
        self.entry = ctk.CTkEntry(self, width=70, textvariable=var_ref)
        self.label = ctk.CTkLabel(self, text=label_text)

        # layout widgets
        if label_side == 'after':
            self.grid_columnconfigure(0, weight=1) # entry expands

            self.entry.grid(row=0,column=0,padx=(0,3))
            self.label.grid(row=0,column=1)
        elif label_side == 'before':
            self.grid_columnconfigure(1, weight=1) # entry expands

            self.entry.grid(row=0,column=1,padx=(3,0))
            self.label.grid(row=0,column=0)

    def _insert(self,index:int=0, string:str=''):
        self.entry.insert(index,string)

    def _clear_and_insert(self,index:int=0, string:str=''):
        self.entry.delete(0, 'end')
        self._insert(index,string)

    def get(self):
        return self.var_ref.get()

class LoadEntry(ctk.CTkFrame):
    '''
    An entry box which is populated by a file select prompt

    # Parameters
    load_var:tk.StringVar
        The variable which the filename will be loaded into. Works like C pass
        by reference.
    defaultextension:str
        The default file extension showed by the load dialog box
    filetypes:list[tuple[str,str]]
        A list of paired string tuples each giving a description and file 
        extension
    command:Callable = lambda x: None
        Optional. A command which is called after the file is loaded
    '''
    def __init__(self, *args, load_var:tk.StringVar, \
        defaultextension:str, filetypes:list[tuple[str,str]],\
            command:Callable=lambda: None, root:tk.StringVar=None,\
                 **kwargs):
        super().__init__(*args, width=0, bg_color='transparent',\
            fg_color='transparent', **kwargs)

        # init data
        self.load_var = load_var
        self.defaultextension = defaultextension
        self.filetypes = filetypes
        self.command = command
        self.root = root

        # init widgets
        self.entry = ctk.CTkEntry(self)
        openicon = ctk.CTkImage(Image.open(\
                os.path.dirname(os.path.realpath(__file__))+r'/assets/open.png'))
        self.openbutton = ctk.CTkButton(master=self, image=openicon, \
            command=self.open_dialog, text ='', border_width=0, \
                border_spacing=0, width=28)

        # layout widgets
        self.grid_columnconfigure(0, weight=1) # entry expands

        self.entry.grid(row=0,column=0,padx=(0,3),stick='ew')
        self.openbutton.grid(row=0,column=1)

    def get(self):
        return self.load_var.get()

    def insert(self,index:int=0, string:str=''):
        self.entry.insert(index,string)

    def clear_and_insert(self,index:int=0, string:str=''):
        self.entry.delete(index, 'end')
        self.insert(index,string)

    def populate(self):
        self.clear_and_insert(0,os.path.basename(self.get()))

    def open_dialog(self):
        if self.root is None:
            initdir = os.path.dirname(os.path.realpath(__file__))
        else:
            initdir = self.root.get()
            
        # need to check for empty, as realpath('') returns directory
        if self.get() != '':
            initfile = os.path.basename(os.path.realpath(self.get()))
        else:
            initfile = ''
            
        fnames = tkinter.filedialog.askopenfilename(initialdir=initdir, \
            initialfile=initfile, defaultextension=self.defaultextension, \
                filetypes=self.filetypes)
        if fnames != () and fnames != '':
            self.load_var.set(fnames)
            self.populate()
            self.command()

class MultiLoadEntry(LoadEntry):
    '''
    An entry box which is populated by a file select prompt to select mutliple 
    files. The return is a list of file name strings.

    # Parameters
    load_var:tk.StringVar
        The variable which the filename will be loaded into. Works like C pass
        by reference.
    defaultextension:str
        The default file extension showed by the load dialog box
    filetypes:list[tuple[str,str]]
        A list of paired string tuples each giving a description and file 
        extension
    command:Callable = lambda x: None
        Optional. A command which is called after the file is loaded
    '''
    def populate(self):
        # needed since self.load_var is not the textvariable of self.entry
        try:
            index = 0
            for fname in self.get():
                self.clear_and_insert(index,os.path.basename(fname)+', ')
                index += len(os.path.basename(fname)+', ')
            self.entry.delete(index-2, 'end')
        except:
            self.clear_and_insert()

    def open_dialog(self):
        if self.root is None:
            initdir = os.path.dirname(os.path.realpath(__file__))
        else:
            initdir = self.root.get()
            
        fnames = tkinter.filedialog.askopenfilenames(initialdir=initdir, 
                                                     defaultextension=\
                                                        self.defaultextension,
                                                     filetypes=self.filetypes)
        if fnames != () and fnames != '':
            self.load_var.set(fnames)
            self.populate()
            self.command()

    def get(self):
        # the below list comprehension is how we need to parse the output
        return [x.replace("'",'').strip() for x in self.load_var.get()[1:-2].split(',')]

class ErrorBox(LabeledFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        f = self.frame
        self.errors = ctk.CTkTextbox(f,width=500)

        self.errors.pack(padx=0, pady=0, anchor='center', expand=True,\
            fill='both')

    def append(self, new_error:str, tracebackFlag=False):
        try:
            if not(str.isspace(new_error)):
                hms = datetime.now().strftime("%H:%M:%S")
                ms = datetime.now().microsecond // 10000
                timestamp = f'[{hms}.{ms:02d}]'
                self.errors.insert('end', \
                    f'{timestamp}: {new_error}'.replace(r'\n', r'\n    '))
                self.errors.insert('end','\n')

                if tracebackFlag:
                    tb = traceback.format_exc().split(r'\n')
                    for line in tb:
                        self.errors.insert('end', \
                            f'  {line} \n')
                    self.errors.insert('end','\n')
        except Exception as e:
            self.errors.insert('end', \
                'Exception thrown during error handling\n')
            self.errors.insert('end', f'    {e}'.replace(r'\n',r'\n    '))
            self.errors.insert('end',r'\n')

class DropDownFrame(ctk.CTkFrame):
    def __init__(self, *args, label_text:str, 
                 frame:ctk.CTkFrame,
                 init_state:Literal['hidden','shown']='hidden', 
                 command:Callable=lambda: None, **kwargs):
        super().__init__(*args, bg_color='transparent', fg_color='transparent',\
                          **kwargs)
        self.label_text = label_text
        self.collapsable_frame = frame
        self.state = init_state
        self.command = command # runs on open
        self.master_frame = kwargs.get('master')

        self.label = ctk.CTkButton(master=self,text=f'▶ {self.label_text}',\
                                   height=0,width=0,bg_color='transparent',\
                                    fg_color='transparent',\
                                        command=self.collapse)

        self.grid_rowconfigure(0,weight=1)
        self.label.grid(row=0,column=0,padx=5,pady=3,sticky='w')

    def collapse(self):
        if self.state == 'shown':
            self.state = 'hidden'
            self.label.configure(text=f'▶ {self.label_text}')
            self.collapsable_frame.grid_forget()
        else:
            self.state = 'shown'
            self.command()
            self.label.configure(text=f'▼ {self.label_text}')
            self.collapsable_frame.lift()
            self.collapsable_frame.grid(row=1,column=0,padx=5,pady=(0,3),\
                                        sticky='ew', in_=self)

class ToggleButton(ctk.CTkButton):
    def __init__(self, *args, on_command:callable, off_command:callable, \
                 on_image:ctk.CTkImage, off_image:ctk.CTkImage, \
                    default_state:bool=False, **kwargs):
        super().__init__(*args, width=0, text='', command=self.toggle, **kwargs)
        self._state = default_state
        self._on_command = on_command
        self._off_command = off_command
        self._on_image = on_image
        self._off_image = off_image
        self._update_view()

    def toggle(self):
        self._state = not self._state
        self._update_view()
        if self._state:
            self._on_command()
        else:
            self._off_command()

    def _update_view(self):
        if self._state:
            self.configure(True, image=self._on_image)
        else:
            self.configure(True, image=self._off_image)

class SpinBox(ctk.CTkFrame):
    '''
    An entry box which also has incrementing buttons.

    # Parameters
    var_ref:tk.Variable
        A reference to the variable which will be modified and displayed
    label_text:str
        The label text
    '''
    def __init__(self, *args, var_ref:tk.Variable, min_val=1, max_val=9, 
                 **kwargs):
        super().__init__(*args, width=0, bg_color='transparent',\
            fg_color='transparent', **kwargs)
        
        self.var_ref = var_ref
        self.min_val = min_val
        self.max_val = max_val

        self.entry = ctk.CTkEntry(self, width=30, textvariable=self.var_ref)
        self.plus = ctk.CTkButton(self, width=0, text='+', command=self.add)
        self.minus = ctk.CTkButton(self, width=0, text='-', command=self.sub)
        
        self.plus.grid(row=0,column=0,sticky='nsew')
        self.entry.grid(row=0,column=1,sticky='nsew')
        self.minus.grid(row=0,column=2,sticky='nsew')

    def add(self):
        if self.var_ref.get() + 1 <= self.max_val:
            self.var_ref.set(self.var_ref.get() + 1)

    def sub(self):
        if self.var_ref.get() - 1 >= self.min_val:
            self.var_ref.set(self.var_ref.get() - 1)
    
    def update_var(self, new_var):
        self.var_ref = new_var
        self.entry.configure(True, textvariable=new_var)

    def get(self):
        return self.var_ref.get()
    
class Popup(ctk.CTkToplevel):
    def __init__(self, fg_color = None, text_color = None, 
                 button_fg_color = None, button_hover_color = None, 
                 button_text_color = None, entry_fg_color = None, 
                 entry_border_color = None, entry_text_color = None,
                 title: str = "CTkDialog",
                 text: str = "CTkDialog",
                 default_value = None):
        super().__init__(fg_color=fg_color)

        self._fg_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkToplevel"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._text_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else self._check_color_type(button_hover_color)
        self._button_fg_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkButton"]["fg_color"] if button_fg_color is None else self._check_color_type(button_fg_color)
        self._button_hover_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkButton"]["hover_color"] if button_hover_color is None else self._check_color_type(button_hover_color)
        self._button_text_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkButton"]["text_color"] if button_text_color is None else self._check_color_type(button_text_color)
        self._entry_fg_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkEntry"]["fg_color"] if entry_fg_color is None else self._check_color_type(entry_fg_color)
        self._entry_border_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkEntry"]["border_color"] if entry_border_color is None else self._check_color_type(entry_border_color)
        self._entry_text_color = ctk.windows.widgets.theme.ThemeManager.theme["CTkEntry"]["text_color"] if entry_text_color is None else self._check_color_type(entry_text_color)

        self._user_input = None
        self._running: bool = False
        self._text = text
        self._default_value = default_value

        self.title(title)
        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(10, self._create_widgets)  # create widgets with slight delay, to avoid white flickering of background
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable

    def _create_widgets(self):

        self.grid_columnconfigure((0, 1), weight=1)
        self.rowconfigure(0, weight=1)

        self._label = ctk.CTkLabel(master=self,
                               width=300,
                               wraplength=300,
                               fg_color="transparent",
                               text_color=self._text_color,
                               text=self._text,)
        self._label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        self._entry = ctk.CTkEntry(master=self,
                               width=230,
                               fg_color=self._entry_fg_color,
                               border_color=self._entry_border_color,
                               text_color=self._entry_text_color)
        self._entry.insert(0, self._default_value)
        self._entry.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        self._ok_button = ctk.CTkButton(master=self,
                                    width=100,
                                    border_width=0,
                                    fg_color=self._button_fg_color,
                                    hover_color=self._button_hover_color,
                                    text_color=self._button_text_color,
                                    text='Ok',
                                    command=self._ok_event)
        self._ok_button.grid(row=2, column=0, columnspan=1, padx=(20, 10), pady=(0, 20), sticky="ew")

        self._cancel_button = ctk.CTkButton(master=self,
                                        width=100,
                                        border_width=0,
                                        fg_color=self._button_fg_color,
                                        hover_color=self._button_hover_color,
                                        text_color=self._button_text_color,
                                        text='Cancel',
                                        command=self._ok_event)
        self._cancel_button.grid(row=2, column=1, columnspan=1, padx=(10, 20), pady=(0, 20), sticky="ew")

        self.after(150, lambda: self._entry.focus())  # set focus to entry with slight delay, otherwise it won't work
        self._entry.bind("<Return>", self._ok_event)

    def _ok_event(self, event=None):
        self._user_input = self._entry.get()
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self.grab_release()
        self.destroy()

    def _cancel_event(self):
        self.grab_release()
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self._user_input