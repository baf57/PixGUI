import customtkinter as ctk

from Helpers import *
from CustomTKWidgets import *
import tpx3_toolkit.viewer as t3view
import tpx3_toolkit.filter as t3filter
import scipy.ndimage as snd

class ReferenceImage():
    def __init__(self, errors:ErrorBox):
        self.errors = errors
        self.file = tk.StringVar(value='')
        self.scale = tk.DoubleVar(value=1.085)
        self.angle = tk.DoubleVar(value=-3.5)
        self.thresh = tk.DoubleVar(value=0.4)
        self.lower = tk.IntVar(value=25)
        self.upper = tk.IntVar(value=150)
        self.binning = tk.IntVar(value=3)
        self.ref = ReferentialNpArray()
        self.ref_g = ReferentialNpArray()

    def calc_fidelities(self, direct, ghost):
        try:
            cxc_d = t3view.cross_correlation(self.ref.get(),
                                            direct,
                                            flipped=False,
                                            plot=False)
            cxc_g = t3view.cross_correlation(self.ref_g.get(),
                                            ghost,
                                            flipped=True,
                                            plot=False)
            
            direct_fid = cxc_d.max()
            ghost_fid = cxc_g.max()

            return(direct_fid, ghost_fid)
        except Exception as e:
            self.errors.append('Error performing cross-correlation:',True)
            return (0,0)

    def load_ref(self):
        try:
            ref = np.load(self.file.get())
            (ref,_,_) = t3view._make_view(ref[1,:,:])
            
            ref_g = ReferenceImage.magnify_rot(ref,
                                                self.scale.get(),
                                                self.angle.get())
            
            ref = (ref > self.thresh.get() * ref.max())
            ref_g = (ref_g > self.thresh.get() * ref_g.max())

            ref = ReferenceImage.bin(\
                ref[self.lower.get():self.upper.get(),:], 
                self.binning.get())
            ref_g = ReferenceImage.bin(\
                ref_g[self.lower.get():self.upper.get(),:], 
                self.binning.get())
            
            self.ref.set(ref)
            self.ref_g.set(ref_g)
        except:
            self.errors.append('Error loading fidelity reference:',True)

    @staticmethod
    def magnify_rot(ref:np.ndarray, M, rot):
        ref_z = snd.zoom(ref, M)
        ref_z = snd.rotate(ref_z,rot)
        
        ref_z[ref_z<0] = 0

        return ref_z

    @staticmethod
    def bin(data, binsize:int):
        xcomp = data
        for i in range(binsize - 1):
            xcomp += np.roll(data,i,0)
        xcomp = xcomp[::binsize,:]

        ycomp = xcomp
        for i in range(binsize - 1):
            ycomp += np.roll(xcomp,i,1)
        ycomp = ycomp[::binsize,:]

        return ycomp

    def recall(self, recall:RecallFile):
        self.file.set(recall.parameters['ref_file'])
        self.scale.set(recall.parameters['ref_scale'])
        self.angle.set(recall.parameters['ref_angle'])
        self.thresh.set(recall.parameters['ref_thresh'])
        self.lower.set(recall.parameters['ref_lower'])
        self.upper.set(recall.parameters['ref_upper'])
        self.binning.set(recall.parameters['ref_binning'])

    def save(self, new_params:dict):
        new_params['ref_file'] = self.file.get()
        new_params['ref_scale'] = self.scale.get()
        new_params['ref_angle'] = self.angle.get()
        new_params['ref_thresh'] = self.thresh.get()
        new_params['ref_lower'] = self.lower.get()
        new_params['ref_upper'] = self.upper.get()
        new_params['ref_binning'] = self.binning.get()

class FilterTab(ctk.CTkFrame):
    '''
    The tab where all of the data filtering occurs
    '''
    def __init__(self, *args, raw_data:ReferentialNpArray,
                 filtered_data:ReferentialNpArray,
                 raw_data_updates:CanvasList,
                 filtered_data_updates:CanvasList, 
                 errors:ErrorBox, **kwargs):
        super().__init__(*args, **kwargs)

        # from init
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.errors = errors

        # top-level data shared between widgets
        self.dir = tk.StringVar(self,
                                os.path.dirname(os.path.realpath(__file__)))
        self.ref_image = ReferenceImage(errors=self.errors)

        # add sub-tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.add("Time")
        self.tabs.add("Space")
        self.left_align_tabs()
        self.tabs.set("Time")

        # add widgets to tabs
        self.timetab = TimeTab(master=self.tabs.tab("Time"),
                               raw_data=self.raw_data,
                               filtered_data=self.filtered_data,
                               filtered_data_updates=self.filtered_data_updates,
                               ref_image=self.ref_image,
                               dir=self.dir)
        self.spacetab = SpaceTab(master=self.tabs.tab("Space"),
                                 raw_data=self.raw_data,
                                 filtered_data=self.filtered_data,
                                 filtered_data_updates=\
                                    self.filtered_data_updates,
                                 ref_image=self.ref_image,
                                 dir=self.dir)

        # layout tabs
        self.timetab.pack(padx=0,pady=0,anchor='center',expand=True,fill='both')
        self.spacetab.pack(padx=0,pady=0,
                           anchor='center',expand=True,fill='both')
        self.tabs.pack(padx=5, pady=0, anchor='center', expand=True,fill='both')

    def left_align_tabs(self):
        self.tabs._segmented_button.grid(row=1, 
                                         rowspan=2, 
                                         column=0,
                                         columnspan=1, 
                                         padx=\
                      self.tabs._apply_widget_scaling(self.tabs._corner_radius), 
                                         sticky="w")
        for name in self.tabs._name_list:
            self.tabs._tab_dict[name].grid(row=3,
                                           column=0, 
                                           sticky="w",
                                           padx=\
                  self.tabs._apply_widget_scaling(max(self.tabs._corner_radius,
                                                      self.tabs._border_width)),
                                           pady=\
                  self.tabs._apply_widget_scaling(max(self.tabs._corner_radius, 
                                                      self.tabs._border_width)))

    def save(self, new_params:dict):
        self.timetab.save(new_params)
        self.ref_image.save(new_params)
            
    def recall(self, recall:RecallFile):
        self.timetab.recall(recall)
        self.ref_image.recall(recall)
    
    def recall_dir(self, recall:RecallFile):
        self.dir.set(recall.parameters['dir'])
    
    def recall_settings(self, recall:RecallFile):
        self.ref_image.recall(recall)

        self.timetab.ref.file_select.populate()
        self.spacetab.ref.file_select.populate()
        if len(self.ref_image.file.get()) != 0:
            self.timetab.ref.reload._state = tk.NORMAL
            self.timetab.ref.reload._draw()

            self.spacetab.ref.reload._state = tk.NORMAL
            self.spacetab.ref.reload._draw()

class PreviewCanvas(SubplotCanvas):
    def __init__(self, *args, filtered_data_updates:CanvasList, 
                 ref_image:ReferenceImage, **kwargs):
        super().__init__(*args, **kwargs)

        self.ref_image = ref_image

        filtered_data_updates.append([self.update_plot])

    def update_plot(self, data):
        self.ax_1.clear()
        self.ax_2.clear()
        self.ax_1.set_xlabel("$X$ (pixels)")
        self.ax_1.set_ylabel("$Y$ (pixels)")
        self.ax_2.set_xlabel("$X$ (pixels)")
        self.ax_2.set_ylabel("$Y$ (pixels)")

        (_,direct,ghost) = t3view.plot_coincidences(data.get(), 
                                                    fig=self.figure)

        if self.ref_image.ref.get().size != 0:
            fidelities = self.ref_image.calc_fidelities(direct,ghost)
            self.rename_plots(f"Idler - Fidelity: {fidelities[1]*100:.2f}%",
                              f"Signal - Fidelity: {fidelities[0]*100:.2f}%")

        self.redraw()
            
class ReferenceInfo(LabeledFrame):
    def __init__(self, *args, ref_image:ReferenceImage,
                 preview_canvas:PreviewCanvas, 
                 dir:tk.StringVar, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.ref_image = ref_image
        self.preview_canvas = preview_canvas
        self.dir = dir

        # create interal frames
        f = self.get_frame()
        self.settings = ctk.CTkFrame(master=f)
        self.settings_scale = LabeledEntry(master=self.settings,
                                           var_ref=self.ref_image.scale,
                                           label_text="Scale:",
                                           label_side='before')
        self.settings_angle = LabeledEntry(master=self.settings,
                                           var_ref=self.ref_image.angle,
                                           label_text="Angle:",
                                           label_side='before')
        self.settings_thresh = LabeledEntry(master=self.settings,
                                           var_ref=self.ref_image.thresh,
                                           label_text="Threshold:",
                                           label_side='before')
        self.settings_lower = LabeledEntry(master=self.settings,
                                           var_ref=self.ref_image.lower,
                                           label_text="Range: Lower:",
                                           label_side='before')
        self.settings_upper = LabeledEntry(master=self.settings,
                                           var_ref=self.ref_image.upper,
                                           label_text="Upper:",
                                           label_side='before')
        self.settings_spin_label = ctk.CTkLabel(master=self.settings,
                                                text="Binning: ",
                                                anchor='w')
        self.settings_binning = SpinBox(master=self.settings,
                                        var_ref=self.ref_image.binning)
        
        self.settings_scale.grid(row=0,column=0,columnspan=2,
                                 padx=(5,3),pady=(5,3),sticky='ew')
        self.settings_angle.grid(row=0,column=2,columnspan=2,
                                 padx=0,pady=(5,3),sticky='ew')
        self.settings_thresh.grid(row=0,column=4,columnspan=2,
                                  padx=(3,5),pady=(5,3),sticky='ew')
        self.settings_lower.grid(row=1,column=0,columnspan=4,
                                 padx=(5,3),pady=0,sticky='ew')
        self.settings_upper.grid(row=1,column=4,columnspan=2,
                                 padx=(0,5),pady=0,sticky='ew')
        self.settings_spin_label.grid(row=2,column=0,columnspan=2,
                                      padx=(5,3),pady=(3,5),sticky='ew')
        self.settings_binning.grid(row=2,column=2,columnspan=4,
                                   padx=(0,5),pady=(3,5),sticky='ew')
        
        self.preview = CanvasFrame(master=f,
                                   mode='preview',
                                   label_text='',
                                   cwidth=250,
                                   cheight=250)
        self.preview.ax.set_xticks([])
        self.preview.ax.set_yticks([])
        self.preview.redraw()

        # create widgets
        self.prompt = ctk.CTkLabel(master=f,
                                   text="Select refernce file",
                                   anchor='w')
        self.file_select = LoadEntry(master=f,
                                     command=self.load_ref,
                                     defaultextension='.npy',
                                     filetypes=[("NumPy data file",'*.npy')],
                                     load_var=self.ref_image.file,
                                     root=self.dir)
        self.reload = ctk.CTkButton(master=f,
                                    text="Reload",
                                    state=tk.DISABLED,
                                    command=self.load_ref)
        self.settings_dropdown = DropDownFrame(master=f,
                                               label_text="Reference Settings",
                                               frame=self.settings)
        self.preview_dropdown = DropDownFrame(master=f,
                                              label_text="Preivew",
                                              frame=self.preview,
                                              command=self.show_ref)
        
        # layout
        f.grid_columnconfigure(0,weight=1)
        self.prompt.grid(row=0,column=0,columnspan=2,
                         padx=5,pady=(5,3),sticky='ew')
        self.file_select.grid(row=1,column=0,padx=(5,3),pady=0,sticky='ew')
        self.reload.grid(row=1,column=1,padx=(5,3),pady=0,sticky='ew')
        self.settings_dropdown.grid(row=2,column=0,columnspan=2,
                                    padx=5,pady=3,sticky='ew')
        self.preview_dropdown.grid(row=3,column=0,columnspan=2,
                                    padx=5,pady=(3,5),sticky='ew')
        
    def load_ref(self):
        # only load the reference and call the preveiw update if there is data? 
        # (dropdown too if open)
        # calls to master are fine since I know the master will have these 
        # attributes
        self.reload._state = tk.NORMAL
        self.reload._draw()

        if len(self.ref_image.file.get()) != 0:
            self.ref_image.load_ref()

            if self.master.filtered_data.get().size != 0:
                self.preview_canvas.update_plot(self.master.filtered_data)

            if self.preview_dropdown.state == 'shown':
                self.show_ref()

    def show_ref(self):
        # show ref in preview dropdown
        if self.ref_image.ref.get().size != 0:
            self.preview.ax.imshow(self.ref_image.ref_g.get(),
                                   origin='lower',
                                   aspect='auto',#'equal',
                                   interpolation='none')
            self.preview.redraw()

class TimeTab(ctk.CTkFrame):
    def __init__(self, *args, raw_data:ReferentialNpArray, 
                 filtered_data:ReferentialNpArray,
                 filtered_data_updates:CanvasList,
                 ref_image:ReferenceImage, 
                 dir:tk.StringVar, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.filtered_data_updates = filtered_data_updates
        self.ref_image = ref_image
        self.dir = dir
        self.min_bin = tk.IntVar(self,-200)
        self.max_bin = tk.IntVar(self,200)
        self.num_bin = tk.IntVar(self,44)
        self.fmin = tk.IntVar(self,-200)
        self.fmax = tk.IntVar(self,200)

        # define widgets
        self.preview = PreviewCanvas(master=self,
                                     filtered_data_updates=\
                                        self.filtered_data_updates,
                                     ref_image=self.ref_image, 
                                     mode='save only',
                                     cwidth=375,
                                     cheight=750,
                                     label_text='Filtered Data Preview',
                                     axis_1_label='Idler', 
                                     axis_2_label='Signal')
        self.ref = ReferenceInfo(master=self,
                                 label_text="Reference Image",
                                 ref_image=self.ref_image,
                                 preview_canvas=self.preview,
                                 dir=self.dir)
        self.histogram = HistogramCanvas(master=self, 
                                         mode='cursor',
                                         cwidth=563, 
                                         cheight=750,
                                         figsize=(4,6),
                                         label_text='Histogram',
                                         min_bin=self.min_bin,
                                         max_bin=self.max_bin,
                                         title='Time of Arrival Differences')
        self.timeInfo = TimeInfo(master=self, 
                                 raw_data = self.raw_data,
                                 filtered_data = self.filtered_data, 
                                 min_bin=self.min_bin, 
                                 max_bin=self.max_bin,
                                 num_bin=self.num_bin, 
                                 fmin = self.fmin, 
                                 fmax = self.fmax, 
                                 filtered_data_updates=\
                                    self.filtered_data_updates, 
                                 hist_update=self.update_histogram, 
                                 get_apply_filter=self.get_apply_filter, 
                                 reset=self.reset,
                                 label_text="Time Statistics")
        
        # modify widgets
        self.filtered_data_updates.append([self.update_histogram])

        # layout
        self.columnconfigure(2,weight=1)
        self.preview.grid(row=0,rowspan=2,column=0,
                          padx=(5,3),pady=5,sticky='ew')
        self.histogram.grid(row=0,rowspan=2,column=1,padx=0,pady=5,sticky='ew')
        self.timeInfo.grid(row=0,column=2,padx=(3,5),pady=(5,3),sticky='ew')
        self.ref.grid(row=1,column=2,padx=(3,5),pady=(0,5),sticky='ew')
    
    def update_histogram(self, data):
        self.histogram.ax.clear()
        t3view.plot_histogram(data.get(), 
                              min_bin=self.min_bin.get(),
                              max_bin=self.max_bin.get(),
                              fig = self.histogram.figure)
        self.histogram.redraw()
        self.histogram.init_home()

    def get_apply_filter(self):
        (tmin, tmax) = self.histogram.get_clicks()
        self.histogram.clickx = None
        self.histogram.prevclickx = None
        if tmin == 0 and tmax == 0:
            tmin = self.fmin.get()
            tmax = self.fmax.get()
        else:
            self.fmin.set(tmin)
            self.fmax.set(tmax)

        data = t3filter.time_filter(self.raw_data.get(),tmin,tmax)

        self.filtered_data.set(data)
        self.filtered_data_updates.update_all()

    def recall(self, recall:RecallFile):
        self.fmin.set(recall.parameters['fmin']) #type:ignore
        self.fmax.set(recall.parameters['fmax']) #type:ignore

    def save(self, new_params:dict):
        new_params['fmin'] = self.fmin.get()
        new_params['fmax'] = self.fmax.get()

    def reset(self):
        self.filtered_data.set(self.raw_data.get())
        self.filtered_data_updates.update_all()

class TimeInfo(LabeledFrame):
    def __init__(self, *args, raw_data:ReferentialNpArray,
                 filtered_data:ReferentialNpArray, 
                 min_bin:tk.IntVar,
                 max_bin:tk.IntVar, 
                 num_bin:tk.IntVar, 
                 fmin:tk.IntVar,
                 fmax:tk.IntVar,
                 filtered_data_updates:CanvasList,
                 hist_update:Callable, 
                 get_apply_filter:Callable,
                 reset:Callable, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.tot_counts = tk.IntVar(self, value=0)
        self.filtered_counts = tk.IntVar(self, value=0)
        self.dt_raw = np.zeros(0)
        self.dt = np.zeros(0)
        self.min_bin = min_bin
        self.max_bin = max_bin
        self.num_bin = num_bin
        self.fmin = fmin
        self.fmax = fmax
        self.hist_update = hist_update
        self.get_apply_filter = get_apply_filter
        
        filtered_data_updates.append([self.update_info])

        # init widgets
        f = self.get_frame()
        self.minBinController = LabeledEntry(f, 
                                             var_ref=self.min_bin,
                                             label_text='Bin range:',
                                             label_side='before')
        self.maxBinController = LabeledEntry(f, 
                                             var_ref=self.max_bin,
                                             label_text=':',
                                             label_side='before')
        self.numBinController = LabeledEntry(f, 
                                             var_ref=self.num_bin, 
                                             label_text=':',
                                             label_side='before')
        self.update_button = ctk.CTkButton(f,
                                           text='Update histogram',
                                           width=0,
                                           command=self.update_info_from_button)
        self.show_f_counts = LabeledEntry(f, 
                                          var_ref=self.filtered_counts, 
                                          label_text="# counts with filter: ",
                                          label_side='before')
        self.show_t_counts = LabeledEntry(f, 
                                          var_ref=self.tot_counts,
                                          label_text="Total counts: ",
                                          label_side='before')
        self.filter_button = ctk.CTkButton(f, 
                                           text='Selected to filter',
                                           width=0,
                                           command=self.get_apply_filter)
        self.fmin_show = LabeledEntry(f, 
                                      var_ref=self.fmin,
                                      label_text="Filter minimum",
                                      label_side='before')
        self.fmax_show = LabeledEntry(f, 
                                      var_ref=self.fmax,
                                      label_text="Filter maximum",
                                      label_side='before')
        self.reset_button = ctk.CTkButton(f, 
                                          text='Reset all filtering',
                                          width=0,
                                          command=reset)
    
        # layout widgets
        self.show_f_counts.grid(row=0,column=0,columnspan=4,
                                padx=(5,0),pady=(5,0),sticky='ew')
        self.show_t_counts.grid(row=0,column=4,columnspan=4,
                                padx=3,pady=(5,0),sticky='ew')
        self.reset_button.grid(row=0,column=8,columnspan=4,
                               padx=(0,5),pady=(5,0),sticky='ew')
        self.minBinController.grid(row=1,column=0,columnspan=3,
                                   padx=(5,0),pady=3,sticky='ew')
        self.maxBinController.grid(row=1,column=3,columnspan=3,
                                   padx=3,pady=3,sticky='ew')
        self.numBinController.grid(row=1,column=6,columnspan=3,
                                   padx=0,pady=3,sticky='ew')
        self.update_button.grid(row=1,column=9,columnspan=3,
                                padx=(3,5),pady=3,sticky='ew')
        self.fmin_show.grid(row=2,column=0,columnspan=4,
                            padx=(5,0),pady=(0,5),sticky='ew')
        self.fmax_show.grid(row=2,column=4,columnspan=4,
                            padx=3,pady=(0,5),sticky='ew')
        self.filter_button.grid(row=2,column=8,columnspan=4,
                                padx=(0,5),pady=(0,5),sticky='ew')

    def update_info_from_button(self):
        self.dt_raw = self.raw_data.get()[1,2,:] - self.raw_data.get()[0,2,:]
        self.dt = self.filtered_data.get()[1,2,:] - \
            self.filtered_data.get()[0,2,:]
        self.hist_update(data=self.filtered_data)

    def update_info(self,data):
        self.dt_raw = self.raw_data.get()[1,2,:] - self.raw_data.get()[0,2,:]
        self.tot_counts.set(self.dt_raw.size)
        self.dt = self.filtered_data.get()[1,2,:] - \
            self.filtered_data.get()[0,2,:]
        self.filtered_counts.set(self.dt.size)
        self.hist_update(data)
        

class SpaceTab(ctk.CTkFrame):
    def __init__(self, *args, raw_data:ReferentialNpArray, 
                 filtered_data:ReferentialNpArray, 
                 filtered_data_updates:CanvasList, 
                 ref_image:ReferenceImage, 
                 dir:tk.StringVar, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.filtered_data_updates = filtered_data_updates
        self.ref_image = ref_image
        self.dir = dir
        self.threshold = tk.DoubleVar(self, 0.2)
        self.current_xbin = 1
        self.current_ybin = 1
        self.unbined_data = self.filtered_data.get()

        # define widgets
        self.preview = PreviewCanvas(master=self,
                                     filtered_data_updates=\
                                        self.filtered_data_updates,
                                     ref_image=self.ref_image, 
                                     mode='save only',
                                     cwidth=375,
                                     cheight=750,
                                     label_text='Filtered Data Preview',
                                     axis_1_label='Idler', 
                                     axis_2_label='Signal')
        self.ref = ReferenceInfo(master=self,
                                 label_text="Reference Image",
                                 ref_image=self.ref_image,
                                 preview_canvas=self.preview,
                                 dir=self.dir)
        self.correlations = SubplotCanvas(master=self,
                                          mode='save only',
                                          cwidth=375,
                                          cheight=750,
                                          label_text='X-Y Correlations', 
                                          axis_1_label='X Correlations', 
                                          axis_2_label='Y Correlations')
        self.space_info = SpaceInfo(master=self, 
                                    label_text='Space Filter Control', 
                                    raw_data=self.raw_data,
                                    filtered_data=self.filtered_data, 
                                    filtered_data_updates=\
                                        self.filtered_data_updates, 
                                    threshold=self.threshold, 
                                    get_apply_filter=self.get_apply_filter, 
                                    update_binning=self.update_binning,
                                    reset=self.reset)

        # modify widgets
        self.filtered_data_updates.append([self.update_correlations])
        
        # layout widgets
        self.columnconfigure(2,weight=1)
        self.preview.grid(row=0,rowspan=2,column=0,
                          padx=(5,3),pady=5,sticky='ew')
        self.correlations.grid(row=0,rowspan=2,column=1,
                               padx=0,pady=(5,3),sticky='ew')
        self.space_info.grid(row=0,column=2,padx=(3,5),pady=5,sticky='ew')
        self.ref.grid(row=1,column=2,padx=(3,5),pady=(0,5),sticky='ew')

    def update_correlations(self, data):
        self.correlations.ax_1.clear()
        self.correlations.ax_2.clear()
        self.correlations.ax_1.set_xlabel("$X_i$ (pixels)")
        self.correlations.ax_1.set_ylabel("$X_s$ (pixels)")
        self.correlations.ax_2.set_xlabel("$Y_i$ (pixels)")
        self.correlations.ax_2.set_ylabel("$Y_s$ (pixels)")

        t3view.plot_correlations(data.get(), fig=self.correlations.figure)
        self.correlations.redraw()
        self.correlations.init_home()

    def get_apply_filter(self,alt=False):
        self.reset() # adds a bit of overhead. Remove this if it gets too slow
        self.update_binning()

        if alt:
            (data,_) = t3filter.space_filter_alt(self.filtered_data.get(), 
                                             self.threshold.get())
        else:
            data = t3filter.space_filter(self.filtered_data.get(), 
                                         self.threshold.get())

        self.filtered_data.set(data)
        self.filtered_data_updates.update_all()

    def update_binning(self):
        bin_data = t3filter.bin(self.filtered_data.get(), \
                                self.space_info.xbinsize.get(), \
                                self.space_info.ybinsize.get())
        self.current_xbin = self.space_info.xbinsize.get()
        self.current_ybin = self.space_info.ybinsize.get()
        self.filtered_data.set(bin_data)
        self.filtered_data_updates.update_all()

    def reset(self):
        # this is an ugly reference but it's the way that requires the least 
        # amount of work to do the filter reset so this is what you get
        self.master.master.master.timetab.get_apply_filter()
        self.current_xbin = 1
        self.current_ybin = 1


class SpaceInfo(LabeledFrame):
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, \
                  filtered_data_updates:CanvasList, \
                   threshold:tk.DoubleVar, \
                    get_apply_filter:Callable, \
                     update_binning:Callable, \
                      reset:Callable, \
                       **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.dx_raw = np.zeros(0)
        self.dy_raw = np.zeros(0)
        self.dx = np.zeros(0)
        self.dy = np.zeros(0)
        self.tot_counts = tk.IntVar(self, value=0)
        self.filtered_counts = tk.IntVar(self, value=0)
        self.xbinsize = ctk.IntVar(self, 1)
        self.ybinsize = self.xbinsize
        self.ybinhold = ctk.IntVar(self,1)
        lockimage = ctk.CTkImage(Image.open(\
            os.path.dirname(os.path.realpath(__file__))+r'/assets/lock.png'))
        unlockimage = ctk.CTkImage(Image.open(\
            os.path.dirname(os.path.realpath(__file__))+r'/assets/unlock.png'))
        
        # modify widgets
        filtered_data_updates.append([self.update_info])

        # layout widgets
        f = self.get_frame()
        self.threshold_box = LabeledEntry(f, 
                                          var_ref=threshold,
                                          label_text="Filter threshold", 
                                          label_side='before')
        self.filter_button_alt = \
                        ctk.CTkButton(f,
                                    text='Apply filter',
                                    width=0,
                                    command=lambda: get_apply_filter(alt=True))
        self.reset_button = ctk.CTkButton(f, 
                                          text='Reset space filter',
                                          width=0,
                                          command=reset)
        self.x_bin_box = SpinBox(f, var_ref=self.xbinsize)
        self.y_bin_box = SpinBox(f, var_ref=self.xbinsize)
        self.lock = ToggleButton(f, 
                                 on_command=self.same_bins, 
                                 off_command=self.diff_bins, 
                                 on_image=lockimage,
                                 off_image=unlockimage, 
                                 default_state=True)
        self.bin_button = ctk.CTkButton(f, 
                                        text="Apply binning", 
                                        width=0, 
                                        command=update_binning)
        
        self.threshold_box.grid(row=0,column=0,columnspan=2,
                                padx=(5,3),pady=(5,3),sticky='e')
        self.filter_button_alt.grid(row=0,column=2,
                                    padx=0,pady=(5,3),sticky='ew')
        self.reset_button.grid(row=0,column=3,padx=(3,5),pady=(5,3),sticky='ew')
        self.x_bin_box.grid(row=1,column=0,padx=(5,3),pady=(3,5),sticky='ew')
        self.lock.grid(row=1,column=1,padx=0,pady=(3,5))
        self.y_bin_box.grid(row=1,column=2,padx=3,pady=(3,5),sticky='ew')
        self.bin_button.grid(row=1,column=3,padx=(0,5),pady=(3,5),sticky='ew')

        self.same_bins()

    def update_info(self, data):
        pass

    def same_bins(self):
        self.ybinsize = self.xbinsize
        self.y_bin_box.update_var(self.xbinsize)

    def diff_bins(self):
        self.ybinhold.set(self.xbinsize.get())
        self.ybinsize = self.ybinhold
        self.y_bin_box.update_var(self.ybinsize)