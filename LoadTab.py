import tkinter as tk
import customtkinter as ctk
import os
import time as t

from Helpers import *
from CustomTKWidgets import *
import tpx3_toolkit as t3
import tpx3_toolkit.viewer as t3view

class LoadTab(ctk.CTkFrame):
    '''
    The tab where all of the loading occurs
    '''
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, raw_data_updates:CanvasList,\
                    filtered_data_updates:CanvasList, errors:ErrorBox, \
                        **kwargs):
        super().__init__(*args, **kwargs)

        # data from initializer
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.errors = errors
        self.dir = tk.StringVar(self,
                                os.path.dirname(os.path.realpath(__file__)))

        # global load data
        self.inp_file = tk.StringVar(self)

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
        self.beamSelector = BeamSelect(master=self, label_text='Beams',\
                                       canvas=self.beamCanvas, \
                                       beamI=self.beamI, \
                                       beamS=self.beamS, \
                                       load_state=self.load_state)
        self.io = ImportExportFrame(master=self, \
                                    raw_data=self.raw_data,\
                                    filtered_data=self.filtered_data,\
                                    raw_data_updates=self.raw_data_updates,\
                                    filtered_data_updates=self.filtered_data_updates,\
                                    load_state=self.load_state, \
                                    errors=self.errors, label_text="Import/Export",\
                                    label_sticky="left")
        self.loader = LoadingFrame(master=self, inp_file=self.inp_file,\
                                   beamCanvas = self.beamCanvas, \
                                   io = self.io, \
                                   load_state=self.load_state, \
                                   beamSelector = self.beamSelector, \
                                   errors=self.errors, label_text="Load", \
                                   label_sticky='left')
        self.process = ProcessFrame(master=self, inp_file=self.inp_file,\
                                    beamI=self.beamI, \
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

        self.beamCanvas.grid(row=0,column=0,rowspan=5,padx=5,pady=5,\
                             sticky='nsew')
        self.loader.grid(row=0,column=1,padx=5,pady=5,sticky='ew')
        self.beamSelector.grid(row=1,column=1,padx=5,pady=5,sticky='ew')
        self.process.grid(row=2,column=1,padx=5,pady=5,sticky='ew')
        self.io.grid(row=3,column=1,padx=5,pady=5,sticky='ew')
        self.errors.grid(in_=self,row=4,column=1,padx=5,pady=5,sticky='ew')
        self.errors.lift() # needed to not draw behind frame since it was
                           # created before the frame was

    def save(self, new_params:dict):
        new_params['file'] = "100000000000000"
        if len(self.inp_file.get()) > 0:
            new_params['file'] = self.inp_file.get()
        if self.raw_data.get().size > 0 or self.filtered_data.get().size > 0:
            new_params['dir'] = self.dir.get()
        if len(self.beamI) > 0:
            new_params['beamI'] = str(self.beamI[0])
        if len(self.beamS) > 0:
            new_params['beamS'] = str(self.beamS[0])
        self.process.settings.save(new_params)

    def recall(self, recall:RecallFile):
        self.inp_file.set(recall.parameters['file'])
        self.loader.load_dialog.populate()
        self.loader.load_preview(True)

        self.beamI.append(t3.Beam.fromString(recall.parameters['beamI']))
        self.beamS.append(t3.Beam.fromString(recall.parameters['beamS']))
        self.beamSelector.redraw_beams()
    
    def recall_dir(self, recall:RecallFile):
        self.dir.set(recall.parameters['dir'])

    def recall_settings(self, recall:RecallFile):
        self.process.settings.recall(recall)

        
class SettingsFrame(ctk.CTkFrame):
    '''
    A settings frame which contains some entry boxes with default values for
    changing the settings.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # init data 
        self.calibration_file = tk.StringVar()
        self.spaceWindow = tk.IntVar(self,20)
        self.timeWindow = tk.IntVar(self,250)
        self.coincWindow = tk.IntVar(self,1000)
        self.clusterRange = tk.IntVar(self,30)
        self.numScans = tk.IntVar(self,20)

        # init widgets
        self.spaceLabel = ctk.CTkLabel(self,text='Space Window:')
        self.spaceEntry = LabeledEntry(master=self, \
                                       var_ref=self.spaceWindow, \
                                       label_text='pixels')
        self.timeLabel = ctk.CTkLabel(self,text='Time Window:')
        self.timeEntry = LabeledEntry(master=self, \
            var_ref=self.timeWindow, label_text='ns')
        self.coincLabel = ctk.CTkLabel(self,text='Coincidences Time Window:')
        self.coincEntry = LabeledEntry(master=self, \
            var_ref=self.coincWindow, label_text='ns')
        self.clusterLabel = ctk.CTkLabel(self,text='Cluster Range:')
        self.clusterEntry = ctk.CTkEntry(self, width=70, \
            textvariable=self.clusterRange)
        self.scansLabel = ctk.CTkLabel(self,text='Number of Scans:')
        self.scansEntry = LabeledEntry(master=self, \
            var_ref=self.numScans, label_text='scans')
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

    def recall(self, recall:RecallFile):
        self.calibration_file.set(recall.parameters['calib_file'])
        self.spaceWindow.set(recall.parameters['spaceWindow']) #type:ignore
        self.timeWindow.set(recall.parameters['timeWindow']) #type:ignore
        self.coincWindow.set(recall.parameters['coincWindow']) #type:ignore
        self.clusterRange.set(recall.parameters['clusterRange']) #type:ignore
        self.numScans.set(recall.parameters['numScans']) #type:ignore

    def save(self, new_params:dict):
        if len(self.calibration_file.get()) > 0:
            new_params['calib_file'] = self.calibration_file.get()

        new_params['spaceWindow'] = self.spaceWindow.get()
        new_params['timeWindow'] = self.timeWindow.get()
        new_params['coincWindow'] = self.coincWindow.get()
        new_params['clusterRange'] = self.clusterRange.get()
        new_params['numScans'] = self.numScans.get()

class BeamSelect(LabeledFrame):
    def __init__(self, *args, canvas:CanvasFrame, beamI:list[t3.Beam], \
        beamS:list[t3.Beam], load_state:tk.StringVar, **kwargs):
        super().__init__(*args, **kwargs)
    
        # data
        self.canvas = canvas
        self.beamI = beamI
        self.beamS = beamS
        self.load_state = load_state
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

        self.idlersLabel.grid(row=0,column=0,padx=(5,0),pady=(5,3),sticky='e')
        self.idlers.grid(row=0,column=1,padx=5,pady=(5,3),sticky='ew')
        self.idlersButton.grid(row=0,column=2,padx=(0,5),pady=(5,3),sticky='w')
        self.signalsLabel.grid(row=1,column=0,padx=(5,0),pady=0,sticky='e')
        self.signals.grid(row=1,column=1,padx=5,pady=0,sticky='ew')
        self.signalsButton.grid(row=1,column=2,padx=(0,5),pady=0,sticky='w')
        self.resetButton.grid(row=2,column=0,columnspan=3,padx=5,pady=(3,5),\
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
            newstring = str(newbeam)

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
        if len(self.beamI) > 0 and len(self.beamS) > 0:
            self.beamIString.set(f'{{{self.beamI[0]}}}')
            self.beamSString.set(f'{{{self.beamS[0]}}}')
            for i in range(len(self.beamI)-1):
                oldIString = self.beamIString.get()[1:-1]
                oldSString = self.beamSString.get()[1:-1]
                newIString = str(self.beamI[i+1])
                newSString = str(self.beamS[i+1])
                self.beamIString.set(f'{{{oldIString}, {newIString}}}')
                self.beamSString.set(f'{{{oldSString}, {newSString}}}')

            beamIDrawing = t3view.draw_beam_box(self.canvas.ax,self.beamI,['g'])
            beamSDrawing = t3view.draw_beam_box(self.canvas.ax,self.beamS,['r'])
            self.boxes.append(beamIDrawing)
            self.boxes.append(beamSDrawing)
            self.canvas.redraw()
            self.load_state.set("Ready to process...")

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
            self.canvas.redraw()
        except Exception as e:
            self.master.errors.append('Exception thrown during beam reset.' + # type: ignore
                                      ' This exception is known to not cause' +
                                      f' any significnt issue.')

        self.disable_select()
        self.idlersButton.configure(text='Select',\
            command=self.enable_idler_select)
        self.signalsButton.configure(text='Select',\
            command=self.enable_signal_select)

class ImportExportFrame(LabeledFrame):
    def __init__(self, *args, raw_data: ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, raw_data_updates:CanvasList,\
                 filtered_data_updates:CanvasList, load_state:tk.StringVar, \
                 errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.load_state = load_state
        self.errors = errors
        self.export_file = ctk.StringVar(self)
        self.import_files = ctk.StringVar(self)

        # tabs
        f = self.frame
        self.tabs = ctk.CTkTabview(master=f,height=0)
        self.tabs.add("Import")
        self.tabs.add("Export")
        self.left_align_tabs()
        self.tabs.set("Import")

        # import stuff
        self.import_select = MultiLoadEntry(master=self.tabs.tab("Import"), \
                                    command=self.imprt, defaultextension='.npy',\
                                    filetypes=[("NumPy data file",'*.npy')],\
                                    load_var=self.import_files, root=self.master.dir)
        self.import_info = ctk.CTkTextbox(self.tabs.tab("Import"),height=56)
        self.import_info.insert('end',"Note: importing will not update anything on this tab except for this dialog box.")

        self.tabs.tab("Import").grid_columnconfigure(0,weight=1)
        self.import_select.grid(row=0,column=0,padx=5,pady=(5,3),sticky='ew')
        self.import_info.grid(row=1,column=0,padx=5,pady=(0,5),sticky='ew')

        # export stuff
        self.file_display = ctk.CTkEntry(self.tabs.tab("Export"))
        self.export_button = ctk.CTkButton(self.tabs.tab("Export"), \
                                           text='Export', width=0, \
                                            command=self.export)
        self.export_as_button = ctk.CTkButton(self.tabs.tab("Export"), \
                                              text='Export as...', \
                                                command=self.export_as)

        self.tabs.tab("Export").grid_columnconfigure(0, weight=1)
        self.file_display.grid(row=0,column=0,padx=(5,3),pady=(5,3),sticky='ew')
        self.export_button.grid(row=0,column=1,padx=(0,5),pady=(5,3),sticky='ew')
        self.export_as_button.grid(row=1,column=0,columnspan=2,padx=5,\
                                   pady=(0,5),sticky='ew')

        self.tabs.pack(padx=5,pady=5,expand=True,fill='both')
                                
    def left_align_tabs(self):
        self.tabs._segmented_button.grid(row=1, rowspan=2, column=0, \
            columnspan=1, padx=self.tabs._apply_widget_scaling(\
            self.tabs._corner_radius), sticky="w")
        for name in self.tabs._name_list:
            self.tabs._tab_dict[name].grid(row=3, column=0, sticky="w",
                padx=self.tabs._apply_widget_scaling(max(\
                self.tabs._corner_radius, self.tabs._border_width)), \
                pady=self.tabs._apply_widget_scaling(max(\
                self.tabs._corner_radius, self.tabs._border_width)))
            
    def imprt(self):
        try:
            if self.import_select.get() == "":
                self.errors.append("Please select a file for importing.")
                return
            
            arrs = self.import_select.get()
            self.master.dir.set(os.path.dirname(arrs[0]))
            
            self.import_info.delete('1.0', 'end')
            self.import_info.insert('1.0', f'Importing file(s):\n')
            self.import_info.insert('end', f'\tImport progress: {0.0:4.1f}%')
            self.master.update_idletasks()
            loaded_arr = np.load(arrs[0])
            for i,arr in enumerate(arrs[1:]):
                if i==0:
                    percent = 1/len(arrs)*100
                    self.import_info.delete('2.1', 'end')
                    self.import_info.insert('2.1', 
                                            f'Import progress: {percent:4.1f}%')
                    self.master.update_idletasks()
                loaded_arr = np.concatenate((loaded_arr, np.load(arr)), axis=2)
                percent = (i+2)/len(arrs)*100
                self.import_info.delete('2.1', 'end')
                self.import_info.insert('2.1', f'Import progress: {percent:4.1f}%')
                self.master.update_idletasks()

            self.import_info.insert('end', f'\n\tUpdating plots (may take some time)...')
            self.master.update_idletasks()

            self.raw_data.set(loaded_arr)
            self.filtered_data.set(loaded_arr)
            self.raw_data_updates.update_all()
            self.filtered_data_updates.update_all()

            self.import_info.delete('1.0', 'end')
            self.import_info.insert('1.0',f'Import completed with {self.raw_data.get().shape[-1]} coincidences!')

            self.update(arrs[0])
        except Exception as e:
            self.errors.append(f'Exception thrown during import:', True)
        
    def export(self):
        if self.export_file.get() == "":
            self.errors.append("A valid path to an export file must be selected.")
            return
        if self.filtered_data.get().shape[0] == 0:
            self.errors.append("The file must be processed to export.")
            return
        try:
            np.save(self.export_file.get(), self.filtered_data.get())
            self.file_display.insert('end', " - Exported!")
        except Exception as e:
            self.errors.append("Error during export:", True)

    def export_as(self):
        initdir = os.path.dirname(os.path.realpath(self.export_file.get()))
        initfile = os.path.basename(os.path.realpath(self.export_file.get()))
        fname = tkinter.filedialog.asksaveasfilename(initialdir=initdir, \
            initialfile=initfile, defaultextension=".npy", \
                filetypes=[("NumPy data file","*.npy")])
        self.update(fname)
        self.export()

    def update(self, file_name:str):
        if file_name != "" and file_name[-4:] != ".npy":
            file_name = '.'.join(file_name.split('.')[:-1])
            file_name = file_name + ".npy"
        self.export_file.set(file_name)
        self.master.dir.set(os.path.dirname(file_name))
        self.file_display.delete(0,'end')
        self.file_display.insert(0, os.path.basename(self.export_file.get()))
        
class LoadingFrame(LabeledFrame):
    def __init__(self, *args, inp_file:tk.StringVar, beamCanvas:CanvasFrame,\
                 io:ImportExportFrame, load_state:tk.StringVar, \
                    beamSelector:BeamSelect, errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.inp_file = inp_file
        self.errors = errors
        self.io = io
        self.beamCanvas = beamCanvas
        self.load_state = load_state
        self.beamSelector = beamSelector

        # init widgets
        f = self.frame
        self.load_dialog = LoadEntry(master=f,\
            command=self.load_preview, defaultextension='.tpx3',\
                filetypes=[("TimePix3 raw file",'*.tpx3')],\
                    load_var=self.inp_file,root=self.master.dir)
        self.load_dialog.populate()
        self.reload_button = ctk.CTkButton(master=f,
                                           text="Reload entire previous state",
                                           command=self.master.master.master.master.recall_all) #type:ignore
        # this is a reference to a function of top level app, but I mean... if I
        # assume it's a duck, I should also assume it can quack
        

        f.grid_columnconfigure(0,weight=1)

        # layout widgits
        self.load_dialog.grid(row=0,padx=5,pady=(5,0),sticky='ew')
        self.reload_button.grid(row=1,padx=5,pady=(3,5),sticky='ew')

    def load_preview(self,reloaded=False):
        if self.check_size():
            return
        
        self.io.update(self.inp_file.get())        
        try:
            if self.inp_file.get() != '':
                self.master.dir.set(os.path.dirname(self.inp_file.get()))
                (tdc,pix) = t3.parse_raw_file(self.inp_file.get())
                self.beamCanvas.ax.clear()
                t3view.plot_hits(pix,fig=self.beamCanvas.figure)
                self.beamCanvas.ax.set_xlabel("$X$ (pixels)")
                self.beamCanvas.ax.set_ylabel("$Y$ (pixels)")
                self.beamCanvas.redraw()
                self.beamCanvas.init_home()
                if not(reloaded):
                    self.load_state.set('Select beams...') 
                self.beamSelector.redraw_beams()
            else:
                self.errors.append(f'Please select an input file when loading')
        except Exception as e:
            print(f'{self.inp_file.get()=}')
            self.errors.append(f'Exception thrown during load:', True)
            
    def check_size(self):
        file_size_MB = os.stat(self.inp_file.get()).st_size / (1024**2)
        if file_size_MB > 500:
            warning_text = f"The file '{os.path.basename(self.inp_file.get())}' is {file_size_MB:.0f}MB " +\
                "in size! This is likely too big to parse all at once. " +\
                "Please enter the size in MB of the files it wil be chopped "+\
                "into. For context, 500MB is a good size for 8GB of VRAM.\n" +\
                "NOTE: This process can take a *long* time."

            parse_dialog = Popup(title="WARNING!", text=warning_text, 
                                 default_value="500")
            parse_file = parse_dialog.get_input()
            
            if parse_file:
                try:
                    thread = ReturnThread(target=t3.chop_large_file,
                                          args=(self.inp_file.get(),
                                                float(parse_file)))
                    thread.start() # hangs on thread start. not sure why
                    self.monitor(thread, 0)
                except Exception as e:
                    self.errors.append("Chopping error: ", True)
            return bool(parse_file)
        return False
                
    def monitor(self, thread:ReturnThread, dot):
        if thread.is_alive():
            self.load_dialog.clear_and_insert(0, 
                    f"Chopping {os.path.basename(self.inp_file.get())}" +\
                        ("." * int((dot/10)%4)))
            dot += 1
            self.after(50,lambda: self.monitor(thread, dot))
        else:
            self.inp_file.set(f"{self.inp_file.get()[:-5]}/part_000.tpx3")
            self.load_dialog.populate()
            self.load_preview()

class ProcessFrame(LabeledFrame):
    def __init__(self, *args, inp_file:tk.StringVar, beamI:list[t3.Beam], \
                 beamS:list[t3.Beam], raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, load_state:tk.StringVar, \
                 raw_data_updates:CanvasList, filtered_data_updates:CanvasList,\
                 errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.inp_file = inp_file
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
        self.settings = SettingsFrame(master=f)
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
        if len(self.settings.calibration_file.get()) == 0:
            self.errors.append('Please select a calibration file!')
            return
        if len(self.inp_file.get()) == 0:
            self.errors.append('Please select an input file!')
            return
        try:
            self.load_state.set('Processing...')
            self.load_bar.configure(mode='indeterminate')
            thread = ReturnThread(target=t3.process_Coincidences, \
                                  args=(self.inp_file.get(), \
                                        self.settings.calibration_file.get(), \
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
            self.errors.append("Process error: ", True)
        
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
                f'Complete! Number of coincidences is {self.raw_data.get().shape[2]}.')
