import time
import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from threading import Thread

from Helpers import *
from CustomTKWidgets import *
import tpx3_toolkit as t3
import tpx3_toolkit.viewer as t3view # type: ignore

class LoadTab(ctk.CTkFrame):
    '''
    The tab where all of the loading stuff occurs
    '''
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, raw_data_updates:CanvasList,\
                    filtered_data_updates:CanvasList, recall: RecallFile, \
                        errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        # data from initializer
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.recall = recall
        self.errors = errors

        # global load data
        self.inp_file = tk.StringVar(self)
        self.calibration_file = tk.StringVar(self, os.path.join(os.path.curdir,\
            'tpx3_workshop','config',\
                'TOT correction curve new firmware GST.txt'))

        # default settings
        self.beamI = []
        self.beamS = []
        self.load_state = tk.StringVar(self,'Select Input File...')

        # since the above values will be possibly changed and used by different
        # classes, I have them as tk.*Var to handle them like C variables when 
        # passing by reference

        # init widgets
        self.beamCanvas = CanvasFrame(master=self, label_text='Beam Selector',\
            mode='save only', cwidth=800, cheight=800)
        self.loader = LoadingFrame(master=self, inp_file=self.inp_file,\
            beamCanvas = self.beamCanvas, load_state=self.load_state, \
                errors=self.errors, label_text="Load", label_sticky='left')
        self.beamSelector = BeamSelect(master=self, label_text='Beams',\
            canvas=self.beamCanvas, beamI=self.beamI, beamS=self.beamS, \
                load_state=self.load_state, recall=self.recall)
        self.process = ProcessFrame(master=self, inp_file=self.inp_file,\
            calib_file=self.calibration_file, beamI=self.beamI, \
                beamS=self.beamS, raw_data=self.raw_data, \
                    filtered_data=self.filtered_data,\
                        load_state = self.load_state, \
                            raw_data_updates=self.raw_data_updates, \
                                filtered_data_updates=self.filtered_data_updates, \
                                    errors=self.errors, \
                                        label_text="Process", \
                                            label_sticky='left')

        # layout widgets
        self.grid_columnconfigure(1,weight=1)

        self.beamCanvas.grid(row=0,column=0,rowspan=4,padx=5,pady=5,\
            sticky='nsew')
        self.loader.grid(row=0,column=1,padx=5,pady=5,sticky='ew')
        self.beamSelector.grid(row=1,column=1,padx=5,pady=5,sticky='ew')
        self.process.grid(row=2,column=1,padx=5,pady=5,sticky='ew')
        self.errors.grid(in_=self,row=3,column=1,padx=5,pady=5,sticky='ew')
        self.errors.lift() # needed to not draw behind frame since it was
                           # created before the frame was
        
class SettingsFrame(ctk.CTkFrame):
    '''
    A settings frame which contains some entry boxes with default values for
    changing the settings.
    '''
    def __init__(self, *args, calibration_file, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.calibration_file = calibration_file
        self.spaceWindow = tk.IntVar(self,20)
        self.timeWindow = tk.IntVar(self,250)
        self.coincWindow = tk.IntVar(self,1000)
        self.clusterRange = tk.IntVar(self,30)
        self.numScans = tk.IntVar(self,20)

        # init widgets
        self.spaceLabel = ctk.CTkLabel(self,text='Space Window:')
        self.spaceEntry = LabeledEntry(master=self, \
            var_ref=self.spaceWindow, label_text='pixels') #type: ignore
        self.timeLabel = ctk.CTkLabel(self,text='Time Window:')
        self.timeEntry = LabeledEntry(master=self, \
            var_ref=self.timeWindow, label_text='ns') #type: ignore
        self.coincLabel = ctk.CTkLabel(self,text='Coincidences Time Window:')
        self.coincEntry = LabeledEntry(master=self, \
            var_ref=self.coincWindow, label_text='ns') #type: ignore
        self.clusterLabel = ctk.CTkLabel(self,text='Cluster Range:')
        self.clusterEntry = ctk.CTkEntry(self, width=70, \
            textvariable=self.clusterRange) #type: ignore
        self.scansLabel = ctk.CTkLabel(self,text='Number of Scans:')
        self.scansEntry = LabeledEntry(master=self, \
            var_ref=self.numScans, label_text='scans') #type: ignore
        self.configLabel = ctk.CTkLabel(self,text='Configuration file:')
        self.configEntry = LoadEntry(master=self,\
            defaultextension='.txt', filetypes=[('Text file','*.txt')],\
                load_var=self.calibration_file)
        self.configEntry.populate()
        # the above will be populated by the load tab global on runtime

        # layout widgets
        self.grid_columnconfigure(1,weight=1)

        self.spaceLabel.grid(row=0,column=0,padx=5,pady=5,sticky='e')
        self.spaceEntry.grid(row=0,column=1,padx=(0,5),pady=5,sticky='w')
        self.timeLabel.grid(row=1,column=0,padx=5,pady=5,sticky='e')
        self.timeEntry.grid(row=1,column=1,padx=(0,5),pady=5,sticky='w')
        self.coincLabel.grid(row=2,column=0,padx=5,pady=5,sticky='e')
        self.coincEntry.grid(row=2,column=1,padx=(0,5),pady=5,sticky='w')
        self.clusterLabel.grid(row=3,column=0,padx=5,pady=5,sticky='e')
        self.clusterEntry.grid(row=3,column=1,padx=(0,5),pady=5,sticky='w')
        self.scansLabel.grid(row=4,column=0,padx=5,pady=5,sticky='e')
        self.scansEntry.grid(row=4,column=1,padx=(0,5),pady=5,sticky='w')
        self.configLabel.grid(row=5,column=0,padx=5,pady=5,sticky='e')
        self.configEntry.grid(row=5,column=1,padx=(0,5),pady=5,sticky='ew')

class LoadingFrame(LabeledFrame):
    def __init__(self, *args, inp_file:tk.StringVar, beamCanvas:CanvasFrame,\
        load_state:tk.StringVar, errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.inp_file = inp_file
        self.errors = errors
        self.beamCanvas = beamCanvas
        self.load_state = load_state

        # init widgets
        f = self.frame
        self.load_dialog = LoadEntry(master=f,\
            command=self.load_preview, defaultextension='.tpx3',\
                filetypes=[("TimePix3 raw file",'*.tpx3')],\
                    load_var=self.inp_file)
        self.load_dialog.populate()
        self.reload_button = ctk.CTkButton(master=f, \
                                           text="Reload entire previous state",\
                                            command=self.master.master.master.master.recallAll) #type:ignore
        # this is a reference to a function of top level app, but I mean... if I
        # assume it's a duck, I should also assume it can quack
        

        f.grid_columnconfigure(0,weight=1)

        # layout widgits
        self.load_dialog.grid(row=0,padx=5,pady=(5,0),sticky='ew')
        self.reload_button.grid(row=1,padx=5,pady=(3,5),sticky='ew')

    def load_preview(self,reloaded=False):
        try:
            if self.inp_file.get() != '':
                (tdc,pix) = t3.parse_raw_file(self.inp_file.get())
                t3view.plot_hits(pix,fig=self.beamCanvas.figure)
                self.beamCanvas.ax.set_xlabel("$X$ (pixels)")
                self.beamCanvas.ax.set_ylabel("$Y$ (pixels)")
                self.beamCanvas.redraw()
                if not(reloaded):
                    self.load_state.set('Select beams...') 
            else:
                print('load error')
                self.errors.append(f'Please select an input file when loading')
        except Exception as e:
            self.errors.append(f'Exception thrown during load:', True)

class BeamSelect(LabeledFrame):
    # TODO: previous beam locations memory
    def __init__(self, *args, canvas:CanvasFrame, beamI:list[t3.Beam], \
        beamS:list[t3.Beam], load_state:tk.StringVar, recall:RecallFile, \
            **kwargs):
        super().__init__(*args, **kwargs)
    
        # data
        self.canvas = canvas
        self.beamI = beamI
        self.beamS = beamS
        self.load_state = load_state
        self.recall = recall
        self.beamIString = tk.StringVar(self,'{[]}')
        self.beamSString = tk.StringVar(self,'{[]}')
        self.mode = ''
        self.click_counter = 0
        self.boxes = list()
        self.click_id = None

        # create widgets
        f = self.get_frame()
        self.idlersLabel = ctk.CTkLabel(f, text='Idler Beams:')
        self.signalsLabel = ctk.CTkLabel(f, text='Signal Beams:')
        self.idlers = ctk.CTkEntry(f, width=0, textvariable=self.beamIString)
        self.signals = ctk.CTkEntry(f, width=0, textvariable=self.beamSString)
        self.idlersButton = ctk.CTkButton(f,text="Select",width=0,\
            command=self.enable_idler_select,fg_color='green')
        self.signalsButton = ctk.CTkButton(f,text="Select",width=0,\
            command=self.enable_signal_select,fg_color='red')
        self.resetButton = ctk.CTkButton(f,text='Reset beam selection',width=0,\
            command=self.reset_beams)

        # layout widgets
        f.columnconfigure(1, weight=1)

        self.idlersLabel.grid(row=0,column=0,padx=(5,0),pady=5,sticky='e')
        self.idlers.grid(row=0,column=1,padx=5,pady=5,sticky='ew')
        self.idlersButton.grid(row=0,column=2,padx=(0,5),pady=5,sticky='w')
        self.signalsLabel.grid(row=1,column=0,padx=(5,0),pady=5,sticky='e')
        self.signals.grid(row=1,column=1,padx=5,pady=5,sticky='ew')
        self.signalsButton.grid(row=1,column=2,padx=(0,5),pady=5,sticky='w')
        self.resetButton.grid(row=2,column=0,columnspan=3,padx=5,pady=5,\
            sticky='ew')

    def enable_select(self):
        self.canvas.update_mode('cursor')
        # disconnect previous click event and reconnect it to the new function
        # count_click which is managed here
        self.canvas.canvas.mpl_disconnect(self.canvas.click) #type:ignore
        self.click_id = self.canvas.canvas.mpl_connect('button_press_event',\
            self.count_click)

    def disable_select(self):
        self.click_counter = 0
        if len(self.beamI) > 0 and len(self.beamS) > 0:
            self.mode='ready'
            self.load_state.set("Ready to process...")
        else:
            self.mode = ''
        self.canvas.update_mode('save only')
        if not(self.click_id is None):
            self.canvas.canvas.mpl_disconnect(self.click_id)
            self.click_id = None

    def enable_idler_select(self):
        self.enable_select()
        if self.mode == 'signal':
            self.signalsButton.configure(text='+',\
                command=self.enable_signal_select)
        self.mode = 'idler'
        self.idlersButton.configure(text='Done',\
            command=self.disable_idler_select)

    def enable_signal_select(self):
        self.enable_select()
        if self.mode == 'idler':
            self.idlersButton.configure(text='+',\
                command=self.enable_idler_select)
        self.mode = 'signal'
        self.signalsButton.configure(text='Done',\
            command=self.disable_signal_select)

    def disable_idler_select(self):
        self.disable_select()
        self.idlersButton.configure(text='+',\
            command=self.enable_idler_select)

    def disable_signal_select(self):
        self.disable_select()
        self.signalsButton.configure(text='+',\
            command=self.enable_signal_select)

    def count_click(self,event):
        self.canvas.clicked(event) # preserve internal functionality

        self.click_counter += 1
        if (self.click_counter % 2) == 0:
            self.update_beams()

    def update_beams(self):
            clickinfo = self.canvas.get_clicks()
            newbeam = t3.Beam(clickinfo[0], clickinfo[1], clickinfo[2],\
                clickinfo[3])
            newstring = newbeam.toString()

            if self.mode == 'idler':
                drawing = t3view.draw_beam_box(self.canvas.ax,[newbeam],['g'])
                self.boxes.append(drawing)
                self.beamI.append(newbeam)
                oldstring = self.beamIString.get()[1:-1]
                if len(self.beamI) == 1:
                    self.beamIString.set(f'{{{newstring}}}')
                    if len(self.beamSString.get()) < 5:
                        self.enable_signal_select() # convert to signal select
                        self.configure(cursor="") # not clean, but clears up a
                        # bug where the cursor returns to the graph for a second
                    else:
                        self.disable_idler_select() # finish selecting
                else:
                    self.beamIString.set(f'{{{oldstring}, {newstring}}}')
            elif self.mode == 'signal':
                drawing = t3view.draw_beam_box(self.canvas.ax,[newbeam],['r'])
                self.boxes.append(drawing)
                self.beamS.append(newbeam)
                oldstring = self.beamSString.get()[1:-1]
                if len(self.beamS) == 1:
                    self.beamSString.set(f'{{{newstring}}}')
                    if len(self.beamIString.get()) < 5:
                        self.enable_idler_select() # convert to idler select
                        self.configure(cursor="") # not clean, but clears up a
                        # bug where the cursor returns to the graph for a second
                    else:
                        self.disable_signal_select() # finsih selecting
                else:
                    self.beamSString.set(f'{{{oldstring}, {newstring}}}')

    def redraw_beams(self):
        t3view.draw_beam_box(self.canvas.ax,self.beamI,['g'])
        t3view.draw_beam_box(self.canvas.ax,self.beamS,['r'])
        self.canvas.redraw()

    def reset_beams(self):
        self.beamI.clear()
        self.beamS.clear()
        self.beamIString.set('{[]}')
        self.beamSString.set('{[]}')

        try:
            for handle in self.boxes:
                for drawing in handle:
                    drawing.remove() 
                    # BUG: something wrong is happening here sometimes, but it's
                    # not a visual error to the user so oh well
        except Exception as e:
            self.master.errors.append('Exception thrown during beam reset.' + # type: ignore
                                      ' This exception is known to not cause' +
                                      f' any significnt issue.')

        self.disable_select()
        self.idlersButton.configure(text='Select',\
            command=self.enable_idler_select)
        self.signalsButton.configure(text='Select',\
            command=self.enable_signal_select)

class ProcessFrame(LabeledFrame):
    def __init__(self, *args, inp_file:tk.StringVar, calib_file:tk.StringVar, \
        beamI:list[t3.Beam], beamS:list[t3.Beam], raw_data:ReferentialNpArray, \
            filtered_data:ReferentialNpArray, load_state:tk.StringVar, \
                raw_data_updates:CanvasList, filtered_data_updates:CanvasList, \
                    errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.inp_file = inp_file
        self.calib_file = calib_file
        self.beamI = beamI
        self.beamS = beamS
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.load_state = load_state
        self.errors = errors

        # create widgets
        f = self.frame
        self.settings = SettingsFrame(master=f,calibration_file=self.calib_file)
        self.settings_dropdown = DropDownFrame(master=f, label_text='Settings',\
            frame=self.settings)
        self.load_bar = ctk.CTkProgressBar(master=f,mode='determinate')
        self.load_bar.set(0)
        self.load_button = ctk.CTkButton(master=f,width=0,text='Process',\
                                         command=self.process)
        self.state = ctk.CTkEntry(master=f,textvariable=self.load_state)

        f.grid_columnconfigure(0,weight=1)

        self.settings_dropdown.grid(row=0,column=0,columnspan=2,padx=5,\
                                    pady=(5,3), sticky='ew')
        self.load_bar.grid(row=1,column=0,padx=(5,3),pady=0,sticky='ew')
        self.load_button.grid(row=1,column=1,padx=(0,5),pady=0,sticky='ew')
        self.state.grid(row=2,column=0,columnspan=2,padx=5,pady=(3,5),\
            sticky='ew')
    
    def process(self):
        try:
            self.load_state.set('Processing...')
            self.load_bar.configure(mode='indeterminate')
            thread = ReturnThread(target=t3.process_Coincidences, \
                            args=(self.inp_file.get(), self.calib_file.get(), \
                                  self.beamS, self.beamI, \
                                   self.settings.timeWindow.get(),\
                                    self.settings.spaceWindow.get(),\
                                     self.settings.coincWindow.get(),\
                                      self.settings.clusterRange.get(),\
                                       self.settings.numScans.get()))
            thread.start()
            self.monitor(thread)
        except Exception as e:
            self.load_state.set('Error while processing! See below.')
            self.errors.append(str(e))
        
    def monitor(self,thread:ReturnThread):
        if thread.is_alive():
            self.load_bar.step()
            self.load_bar.update_idletasks()
            self.after(50,lambda: self.monitor(thread))
        else:
            self.raw_data.set(thread.get()) #type: ignore
            self.filtered_data.set(self.raw_data.get())
            self.raw_data_updates.update_all()
            self.filtered_data_updates.update_all()

            self.load_bar.configure(mode='determinate')
            self.load_bar.set(1)
            self.load_state.set(\
                f'Processing complete! Number of coincidences is {self.raw_data.get().shape[2]}.')
