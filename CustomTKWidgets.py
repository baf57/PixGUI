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
from tkinter import font
from matplotlib.figure import Figure
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
        mode:Literal['cursor','save only','preview']='cursor', cwidth=100, \
            cheight=100, **kwargs):
        super().__init__(*args, width=cwidth, height=cheight, **kwargs)

        # init data
        self.mouse_move = None
        self.click = None
        self.axes_enter = None
        self.axes_leave = None

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
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=2,\
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
            self.seperator.grid(row=1,column=0,columnspan=2,sticky='ew')

        self.x = 0
        self.y = 0
        self.clickx = None
        self.clicky = None
        self.prevclickx = None
        self.prevclicky = None
        self.lastvline = None
        self.lasthline = None
        self.clickvline = None
        self.clickhline = None

        if mode == 'cursor':
            self.statusbartext = tk.StringVar(self,\
                f"Mouse Position ({self.x:.0f},{self.y:.0f})")
            self.statusbar = ctk.CTkLabel(master=self.frame,\
                textvariable=self.statusbartext, height=1)
            self.statusbar.grid(row=2, column=0, sticky='w')
        if mode == 'cursor' or mode == 'save only':
            saveicon = ctk.CTkImage(\
                Image.open(\
                    os.path.dirname(os.path.realpath(__file__))+\
                        r'/assets/save.png'))
            self.savebutton = ctk.CTkButton(master=self.frame, image=saveicon, \
                command=self.save_image, text ='', border_width=0, \
                    border_spacing=0, width=28)
            self.savebutton.grid(row=2, column=1, sticky='nsew',pady=3)

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
        self.statusbartext.set(f"Mouse Position ({self.x:.0f},{self.y:.0f})")

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

        self.prevclickx = self.clickx
        self.clickx = self.x # closest integer value
        self.prevclicky = self.clicky
        self.clicky = self.y # closest integer value

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

    def update_mode(self,mode:str):
        if not(self.mouse_move is None):
            self.canvas.mpl_disconnect(self.mouse_move)
            self.canvas.mpl_disconnect(self.click) #type:ignore
            self.canvas.mpl_disconnect(self.axes_enter) #type:ignore
            self.canvas.mpl_disconnect(self.axes_leave) #type:ignore
            self.return_mouse('')
        if hasattr(self,'statusbar'): self.statusbar.grid_forget()
        if hasattr(self,'seperator'): self.seperator.grid_forget()
        if hasattr(self,'savebutton'): self.savebutton.grid_forget()
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

class SubplotCanvas(CanvasFrame):
    def __init__(self, *args, axis_1_label:str='', axis_2_label:str='', \
                 **kwargs):
        super().__init__(*args, **kwargs)

        self.ax.remove() # type:ignore
        self.ax_1 = self.figure.add_subplot(211)
        self.ax_2 = self.figure.add_subplot(212)

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

class AngleCanvas(SubplotCanvas):
    # This whole class is less than optimal, but it works so I'm leaving it
    # TODO: Need some sort of get_clicklines() method
    def __init__(self, *args, angle_1:tk.DoubleVar, angle_2:tk.DoubleVar,\
                  **kwargs):
        super().__init__(*args, **kwargs)

        self.angle = None

        self.angle_1 = angle_1
        self.angle_2 = angle_2

    def clicked(self,event):
        xlims = self.ax.get_xlim() #type:ignore ax will have a handle
        m = np.tan(np.deg2rad(self.angle.get())) #type:ignore angle will have a handle

        x = np.array(xlims)
        y = m * (x - self.x) + self.y

        if self.clickvline is not None:
            self.clickvline.remove()
            self.clickvline = None
        else:
            self.clickvline = self.ax.plot(x,y,color="red",ls=":")[0] #type:ignore ax will have a handle
        
        if self.clickhline is not None:
            self.clickhline.remove()
            self.clickhline = None
        else:
            self.clickhline = self.ax.plot(x,y,color="red",ls=":")[0] #type:ignore ax will have a handle

        self.prevclickx = self.clickx
        self.clickx = self.x
        self.prevclicky = self.clicky
        self.clicky = self.y

    def remove_mouse(self,event):
        self.configure(cursor="none")
        self.ax = event.inaxes
        if self.ax is self.ax_1:
            self.angle = self.angle_1
        else:
            self.angle = self.angle_2
    
    def return_mouse(self,event):
        self.configure(cursor="")
        self.ax = None
        self.angle = None

    def update_cursor(self):
        xlims = self.ax.get_xlim() #type:ignore ax will have a handle
        ylims = self.ax.get_ylim() #type:ignore ax will have a handle
        m = np.tan(np.deg2rad(self.angle.get())) #type:ignore angle will have a handle

        x = np.array(xlims)
        y = m * (x - self.x) + self.y

        if self.lastvline is not None: self.lastvline.remove()
        self.lastvline = self.ax.plot(x,y,color="red",ls=":")[0] #type:ignore ax will have a handle
        if self.lasthline is not None: self.lasthline.remove()
        self.lasthline = self.ax.plot(x,y,color="red",ls=":")[0] #type:ignore ax will have a handle

        self.ax.set_xlim(xlims[0], xlims[1]) #type:ignore ax will have a handle
        self.ax.set_ylim(ylims[0], ylims[1]) #type:ignore ax will have a handle

        self.redraw()

    def show_preview_0(self,angle):
        self.ax = self.ax_1

        xlims = self.ax.get_xlim()
        ylims = self.ax.get_ylim()
        m = np.tan(np.deg2rad(angle))

        x1 = np.average(xlims)
        y1 = np.average(ylims)

        x = np.array(xlims)
        y = m * (x - x1) + y1

        if self.lastvline is not None: self.lastvline.remove()
        self.lastvline = self.ax.plot(x,y,color="red",ls=":")[0]
        if self.lasthline is not None: self.lasthline.remove()
        self.lasthline = self.ax.plot(x,y,color="red",ls=":")[0]

        self.ax.set_xlim(xlims[0], xlims[1])
        self.ax.set_ylim(ylims[0], ylims[1])

        self.ax = None

        self.redraw()

    def show_preview_1(self,angle):
        self.ax = self.ax_2

        xlims = self.ax.get_xlim()
        ylims = self.ax.get_ylim()
        m = np.tan(np.deg2rad(angle))

        x1 = np.average(xlims)
        y1 = np.average(ylims)

        x = np.array(xlims)
        y = m * (x - x1) + y1

        if self.lastvline is not None: self.lastvline.remove()
        self.lastvline = self.ax.plot(x,y,color="red",ls=":")[0]
        if self.lasthline is not None: self.lasthline.remove()
        self.lasthline = self.ax.plot(x,y,color="reTODOd",ls=":")[0]

        self.ax.set_xlim(xlims[0], xlims[1])
        self.ax.set_ylim(ylims[0], ylims[1])

        self.ax = None

        self.redraw()

    def get_clicks(self) -> tuple[int,int,int]:
        # Return clicks as x1,y1,slope1,x2,y2,slope2
        # TODO: This is just wrong and I gotta fix it
        if not None in \
            [self.prevclickx,self.prevclicky,self.clickx,self.clicky]:
            slope1 = self.angle_1.get()
            x1 = min(self.clickx,self.prevclickx) # type: ignore
            y1 = max(self.clickx,self.prevclickx) # type: ignore
            slope2 = self.angle_2.get()
            x2 = min(self.clicky,self.prevclicky) # type: ignore
            y2 = max(self.clicky,self.prevclicky) # type: ignore
        else:
            slope1,x1,y1,slope2,x2,y2 = 0, 0, 0, 0, 0, 0

        return (slope1,x1,y1,slope2,x2,y2) # type: ignore

class HistogramCanvas(CanvasFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update_cursor(self):
        if self.lastvline is not None: self.lastvline.remove()
        self.lastvline = self.ax.axvline(self.x,color="gray",ls=":")
        if self.lasthline is not None: self.lasthline.remove()
        self.lasthline = self.ax.axvline(self.x,color="gray",ls=":")
        self.redraw()

    def clicked(self,event):
        # BUG: broken in an unkown way
        if self.clickvline is not None: 
            self.clickvline.remove()
            self.clickvline = None
        else:
            self.clickvline = self.ax.axvline(self.x,color="gray",ls=":")

        if self.clickhline is not None:
            self.clickhline.remove()
            self.clickhline = None
        else:
            self.clickhline = self.ax.axvline(self.y,color="gray",ls=":")

        self.prevclickx = self.clickx
        self.clickx = self.x # closest integer value
        self.prevclicky = self.clicky
        self.clicky = self.y # closest integer value

        self.redraw()

    def get_clicks(self) -> tuple[int,int]:
        # Return clicks as x1,x2
        if not None in \
            [self.prevclickx,self.prevclicky,self.clickx,self.clicky]:
            x1 = min(self.clickx,self.prevclickx) # type: ignore
            x2 = max(self.clickx,self.prevclickx) # type: ignore
        else:
            x1,x2 = 0, 0

        return (x1,x2)

class LabeledEntry(ctk.CTkFrame):
    '''
    An entry box which also has a units label after it.

    # Parameters
    var_ref:tk.Variable
        A reference to the variable which will be modified and displayed
    label_text:str
        The label text

    # Notes
    This and the below function should be refactored to be sibling classes
    '''
    def __init__(self, *args, var_ref:tk.Variable, label_text:str='', \
        label_side:str='after', **kwargs):
        super().__init__(*args, width=0, bg_color='transparent',\
            fg_color='transparent', **kwargs)
        
        # init data
        self.var_ref = var_ref

        # init widgets
        self.entry = ctk.CTkEntry(self, width=70, textvariable=self.var_ref)
        self.label = ctk.CTkLabel(self, text=label_text)

        # layout widgets
        if label_side == 'after':
            self.grid_columnconfigure(0, weight=1) # extry expands

            self.entry.grid(row=0,column=0,padx=(0,3))
            self.label.grid(row=0,column=1)
        elif label_side == 'before':
            self.grid_columnconfigure(1, weight=1) # extry expands

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

    # Notes
    This and the above function should be refactored to be sibling classes
    '''
    def __init__(self, *args, load_var:tk.StringVar, \
        defaultextension:str, filetypes:list[tuple[str,str]],\
            command:Callable=lambda: None, **kwargs):
        super().__init__(*args, width=0, bg_color='transparent',\
            fg_color='transparent', **kwargs)

        # init data
        self.load_var = load_var
        self.defaultextension = defaultextension
        self.filetypes = filetypes
        self.command = command

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
        self.entry.delete(0, 'end')
        self.insert(index,string)

    def populate(self):
        # needed since self.load_var is not the textvariable of self.entry
        self.clear_and_insert(0,os.path.basename(self.load_var.get()))

    def open_dialog(self):
        initdir = os.path.dirname(os.path.realpath(self.get()))
        initfile = os.path.basename(os.path.realpath(self.get()))
        fname = tkinter.filedialog.askopenfilename(initialdir=initdir, \
            initialfile=initfile, defaultextension=self.defaultextension, \
                filetypes=self.filetypes)
        if fname != ():
            print(fname)
            self.load_var.set(fname)
            self.populate()
            self.command()

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
    def __init__(self, *args, label_text:str, frame:ctk.CTkFrame, \
        init_state:Literal['hidden','shown']='hidden', **kwargs):
        super().__init__(*args, bg_color='transparent', fg_color='transparent',\
                          **kwargs)
        self.label_text = label_text
        self.collapsable_frame = frame
        self.state = init_state
        self.master_frame = kwargs.get('master')

        self.label = ctk.CTkButton(master=self,text=f'▶ {self.label_text}',\
                                   height=0,width=0,bg_color='transparent',\
                                    fg_color='transparent',\
                                        command=self.collapse)

        self.grid_rowconfigure(1,weight=1)
        self.label.grid(row=0,column=0,padx=5,pady=3,sticky='w')

    def collapse(self):
        if self.state == 'shown':
            self.state = 'hidden'
            self.label.configure(text=f'▶ {self.label_text}')
            self.collapsable_frame.grid_forget()
        else:
            self.state = 'shown'
            self.label.configure(text=f'▼ {self.label_text}')
            self.collapsable_frame.lift()
            self.collapsable_frame.grid(row=1,column=0,padx=5,pady=(0,3),\
                                        sticky='ew')
