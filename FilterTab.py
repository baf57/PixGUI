import customtkinter as ctk

from Helpers import *
from CustomTKWidgets import *
import tpx3_toolkit as t3
import tpx3_toolkit.viewer as t3view
import tpx3_toolkit.filter as t3filter

class FilterTab(ctk.CTkFrame):
    # TODO: Space filter
    '''
    The tab where all of the data filtering occurs
    '''
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, \
                    raw_data_updates:CanvasList, \
                        filtered_data_updates:CanvasList, **kwargs):
        super().__init__(*args, **kwargs)

        # from init
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates

        # add sub-tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.add("Time")
        self.tabs.add("Space")
        self.left_align_tabs()
        self.tabs.set("Time")

        # add widgets to tabs
        self.timetab = TimeTab(master=self.tabs.tab("Time"), \
                               raw_data=self.raw_data, \
                                filtered_data=self.filtered_data, \
                                    raw_data_updates=self.raw_data_updates,\
                                        filtered_data_updates=self.filtered_data_updates)
        self.spacetab = SpaceTab(master=self.tabs.tab("Space"), \
                               raw_data=self.raw_data, \
                                filtered_data=self.filtered_data, \
                                    raw_data_updates=self.raw_data_updates, \
                                        filtered_data_updates=self.filtered_data_updates)

        # layout tabs
        self.timetab.pack(padx=0,pady=0,anchor='center',expand=True, \
                          fill='both')
        self.spacetab.pack(padx=0,pady=0,anchor='center',expand=True, \
                          fill='both')
        self.tabs.pack(padx=5, pady=0, anchor='center', expand=True, \
                       fill='both')

    def left_align_tabs(self):
        self.tabs._segmented_button.grid(row=1, rowspan=2, column=0, \
            columnspan=1, padx=self.tabs._apply_widget_scaling(\
            self.tabs._corner_radius), sticky="w")
        for name in self.tabs._name_list:
            self.tabs._tab_dict[name].grid(row=3, column=0, sticky="w",
                padx=self.tabs._apply_widget_scaling(max(\
                self.tabs._corner_radius, self.tabs._border_width)),
                pady=self.tabs._apply_widget_scaling(max(\
                self.tabs._corner_radius, self.tabs._border_width)))
            
class TimeTab(ctk.CTkFrame):
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                filtered_data:ReferentialNpArray, \
                     raw_data_updates:CanvasList, \
                        filtered_data_updates:CanvasList, **kwargs):
        # TODO: add time filtering
        super().__init__(*args, **kwargs)

        # init data
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.min_bin = tk.IntVar(self,-200)
        self.max_bin = tk.IntVar(self,200)
        self.num_bin = tk.IntVar(self,44)
        self.fmin = tk.IntVar(self,-200)
        self.fmax = tk.IntVar(self,200)

        # define widgets
        self.preview = SubplotCanvas(master=self, mode='save only', cwidth=375,\
                                   cheight=750,
                                   label_text='Filtered Data Preview',
                                   axis_1_label='Idler', axis_2_label='Signal')
        self.histogram = HistogramCanvas(master=self, mode='cursor', \
                                         cwidth=563, cheight=750, \
                                            figsize=(4,6), \
                                                label_text='Histogram', \
                                                min_bin=self.min_bin, \
                                                max_bin=self.max_bin, \
                                            title='Time of Arrival Differences')
        self.timeInfo = TimeInfo(master=self, raw_data = self.raw_data,\
                                 filtered_data = self.filtered_data, \
                                  min_bin=self.min_bin, max_bin=self.max_bin,\
                                   num_bin=self.num_bin, fmin = self.fmin, \
                                    fmax = self.fmax, filtered_data_updates= \
                                   self.filtered_data_updates, \
                                    hist_update=self.update_histogram, \
                                    get_apply_filter=self.get_apply_filter, \
                                     reset=self.reset,\
                                        label_text="Time Statistics")
        
        # modify widgets
        self.filtered_data_updates.append([self.update_preview, \
                                       self.update_histogram])

        # layout
        self.columnconfigure(2,weight=1)
        self.preview.grid(row=0,column=0,padx=(5,3),pady=5,sticky='ew')
        self.histogram.grid(row=0,column=1,padx=0,pady=5,sticky='ew')
        self.timeInfo.grid(row=0,column=2,padx=(3,5),pady=5,sticky='ew')

    def update_preview(self, data):
        self.preview.ax_1.clear()
        self.preview.ax_2.clear()
        self.preview.ax_1.set_xlabel("$X$ (pixels)")
        self.preview.ax_1.set_ylabel("$Y$ (pixels)")
        self.preview.ax_2.set_xlabel("$X$ (pixels)")
        self.preview.ax_2.set_ylabel("$Y$ (pixels)")

        t3view.plot_coincidences(data.get(), fig=self.preview.figure)
        self.preview.redraw()
    
    def update_histogram(self, data):
        self.histogram.ax.clear()
        t3view.plot_histogram(data.get(), min_bin=self.min_bin.get(),\
                              max_bin=self.max_bin.get(),\
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
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, min_bin:tk.IntVar,\
                     max_bin:tk.IntVar, num_bin:tk.IntVar, fmin:tk.IntVar, \
                         fmax:tk.IntVar, filtered_data_updates:CanvasList,\
                         hist_update:Callable, get_apply_filter:Callable, \
                          reset:Callable, \
                              **kwargs):
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
        self.minBinController = LabeledEntry(f, var_ref=self.min_bin, \
                                            label_text='Bin range:',\
                                                label_side='before')
        self.maxBinController = LabeledEntry(f, var_ref=self.max_bin, \
                                            label_text=':',\
                                                label_side='before')
        self.numBinController = LabeledEntry(f, var_ref=self.num_bin, \
                                            label_text=':',\
                                                label_side='before')
        self.update_button = ctk.CTkButton(f,text='Update histogram',width=0,\
                                           command=self.update_info_from_button)
        self.show_f_counts = LabeledEntry(f, var_ref=self.filtered_counts, \
                                        label_text=\
                                        "# counts with filter: ",\
                                            label_side='before')
        self.show_t_counts = LabeledEntry(f, var_ref=self.tot_counts, \
                                        label_text=\
                                        "Total counts: ",\
                                            label_side='before')
        self.filter_button = ctk.CTkButton(f, text='Selected to filter',width=0,\
                                          command=self.get_apply_filter)
        self.fmin_show = LabeledEntry(f, var_ref=self.fmin, \
                                      label_text="Filter minimum", \
                                        label_side='before')
        self.fmax_show = LabeledEntry(f, var_ref=self.fmax, \
                                      label_text="Filter maximum", \
                                        label_side='before')
        self.reset_button = ctk.CTkButton(f, text='Reset all filtering',width=0,\
                                          command=reset)
    
        # layout widgets
        self.show_f_counts.grid(row=0,column=0,columnspan=4,padx=(5,0),pady=(5,0),sticky='ew')
        self.show_t_counts.grid(row=0,column=4,columnspan=4,padx=3,pady=(5,0),sticky='ew')
        self.reset_button.grid(row=0,column=8,columnspan=4,padx=(0,5),pady=(5,0),sticky='ew')
        self.minBinController.grid(row=1,column=0,columnspan=3,padx=(5,0),pady=3,sticky='ew')
        self.maxBinController.grid(row=1,column=3,columnspan=3,padx=3,pady=3,sticky='ew')
        self.numBinController.grid(row=1,column=6,columnspan=3,padx=0,pady=3,sticky='ew')
        self.update_button.grid(row=1,column=9,columnspan=3,padx=(3,5),pady=3,sticky='ew')
        self.fmin_show.grid(row=2,column=0,columnspan=4,padx=(5,0),pady=(0,5),sticky='ew')
        self.fmax_show.grid(row=2,column=4,columnspan=4,padx=3,pady=(0,5),sticky='ew')
        self.filter_button.grid(row=2,column=8,columnspan=4,padx=(0,5),pady=(0,5),sticky='ew')

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
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, \
                     raw_data_updates:CanvasList, \
                        filtered_data_updates:CanvasList, **kwargs):
        # TODO: add space filtering
        super().__init__(*args, **kwargs)

        # init data
        self.raw_data = raw_data
        self.filtered_data = filtered_data
        self.raw_data_updates = raw_data_updates
        self.filtered_data_updates = filtered_data_updates
        self.threshold = tk.DoubleVar(self, 0.2)
        self.current_xbin = 1
        self.current_ybin = 1
        self.unbined_data = self.filtered_data.get()

        # define widgets
        self.preview = SubplotCanvas(master=self, mode='save only', cwidth=375,\
                                      cheight=750, \
                                       label_text='Filtered Data Preview', \
                                        axis_1_label='Idler', \
                                         axis_2_label='Signal')
        self.correlations = SubplotCanvas(master=self,mode='save only',cwidth=375,\
                                           cheight=750, \
                                            label_text='X-Y Correlations', \
                                             axis_1_label='X Correlations', \
                                              axis_2_label='Y Correlations')
        self.space_info = SpaceInfo(master=self, \
                                     label_text='Space Filter Control', \
                                      raw_data=self.raw_data, \
                                       filtered_data=self.filtered_data, \
                                        filtered_data_updates=self.filtered_data_updates, \
                                         threshold=self.threshold, \
                                          get_apply_filter=self.get_apply_filter, \
                                            update_binning=self.update_binning,\
                                             reset=self.reset)

        # modify widgets
        self.filtered_data_updates.append([self.update_preview, \
                                       self.update_correlations])
        
        # layout widgets
        self.columnconfigure(2,weight=1)
        self.preview.grid(row=0,column=0,padx=(5,3),pady=5,\
                          sticky='ew')
        self.correlations.grid(row=0,column=1,padx=0,pady=(5,3),\
                               sticky='ew')
        self.space_info.grid(row=0,column=2,padx=(3,5),pady=5,sticky='ew')

    def update_preview(self, data):
        self.preview.ax_1.clear()
        self.preview.ax_2.clear()
        self.preview.ax_1.set_xlabel("$X$ (pixels)")
        self.preview.ax_1.set_ylabel("$Y$ (pixels)")
        self.preview.ax_2.set_xlabel("$X$ (pixels)")
        self.preview.ax_2.set_ylabel("$Y$ (pixels)")

        t3view.plot_coincidences(data.get(), fig=self.preview.figure)
        self.preview.redraw()

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
        if alt:
            data = t3filter.space_filter_alt(self.filtered_data.get(), self.threshold.get())
        else:
            data = t3filter.space_filter(self.filtered_data.get(), self.threshold.get())

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
        
        filtered_data_updates.append([self.update_info])

        f = self.get_frame()
        self.threshold_box = LabeledEntry(f, var_ref=threshold, \
                                      label_text="Filter threshold", \
                                        label_side='before')
        #self.filter_button = ctk.CTkButton(f,text='Apply filter',width=0,\
        #                                   command=get_apply_filter)
        self.filter_button_alt = ctk.CTkButton(f,text='Apply filter',width=0,\
                                           command=lambda: get_apply_filter(alt=True))
        self.reset_button = ctk.CTkButton(f, text='Reset space filter',width=0,\
                                          command=reset)
        self.x_bin_box = SpinBox(f, var_ref=self.xbinsize)
        self.y_bin_box = SpinBox(f, var_ref=self.xbinsize)
        self.lock = ToggleButton(f, on_command=self.same_bins, \
                                 off_command=self.diff_bins, on_image=lockimage,
                                 off_image=unlockimage, default_state=True)
        self.bin_button = ctk.CTkButton(f, text="Apply binning", width=0, \
                                        command=update_binning)
        
        self.threshold_box.grid(row=0,column=0,columnspan=2,padx=(5,3),pady=(5,3),sticky='e')
        #self.filter_button.grid(row=0,column=2,padx=0,pady=(5,3),sticky='ew')
        self.filter_button_alt.grid(row=0,column=2,padx=0,pady=(5,3),sticky='ew')
        #self.filter_button_alt.grid(row=0,column=3,padx=(3,5),pady=(5,3),sticky='ew')
        self.reset_button.grid(row=0,column=3,padx=(3,5),pady=(5,3),sticky='ew')

        self.x_bin_box.grid(row=1,column=0,padx=(5,3),pady=(3,5),sticky='ew')
        self.lock.grid(row=1,column=1,padx=0,pady=(3,5))
        self.y_bin_box.grid(row=1,column=2,padx=3,pady=(3,5),sticky='ew')
        self.bin_button.grid(row=1,column=3,padx=(0,5),pady=(3,5),sticky='ew')

        #self.reset_button.grid(row=0,rowspan=2,column=4,padx=5,pady=5,sticky='ew')

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