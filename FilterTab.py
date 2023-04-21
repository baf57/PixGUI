import customtkinter as ctk

from Helpers import *
from CustomTKWidgets import *
import tpx3_toolkit as t3
import tpx3_toolkit.viewer as t3view

class FilterTab(ctk.CTkFrame):
    # TODO: Space filter
    '''
    The tab where all of the data filtering stuff occurs
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
                                   fmin = self.fmin, fmax = self.fmax, \
                                   filtered_data_updates= \
                                   self.filtered_data_updates, \
                                    hist_update=self.update_histogram, \
                                    get_apply_filter=self.get_apply_filter, \
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

    def get_apply_filter(self):
        dt = self.raw_data.get()[1,2,:] - self.raw_data.get()[0,2,:]
        (tmin, tmax) = self.histogram.get_clicks()
        self.histogram.clickx = None
        self.histogram.prevclickx = None
        if tmin == 0 and tmax == 0:
            tmin = self.fmin.get()
            tmax = self.fmax.get()
        else:
            self.fmin.set(tmin)
            self.fmax.set(tmax)

        f = np.logical_and(dt >= tmin, dt <= tmax)

        self.filtered_data.set(self.raw_data.get()[:,:,f])
        self.filtered_data_updates.update_all()

class TimeInfo(LabeledFrame):
    def __init__(self, *args, raw_data:ReferentialNpArray, \
                 filtered_data:ReferentialNpArray, min_bin:tk.IntVar,\
                     max_bin:tk.IntVar, fmin:tk.IntVar, fmax:tk.IntVar, \
                        filtered_data_updates:CanvasList,\
                         hist_update:Callable, get_apply_filter:Callable, \
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
        self.fmin = fmin
        self.fmax = fmax
        self.hist_update = hist_update
        self.get_apply_filter = get_apply_filter
        
        filtered_data_updates.append([self.update_info])

        # init widgets
        f = self.get_frame()
        self.minBinController = LabeledEntry(f, var_ref=self.min_bin, \
                                            label_text='Minimum time bin: ',\
                                                label_side='before')
        self.maxBinController = LabeledEntry(f, var_ref=self.max_bin, \
                                            label_text='Maximum time bin: ',\
                                                label_side='before')
        self.update_button = ctk.CTkButton(f,text='Update Histogram',width=0,\
                                           command=self.update_info_from_button)
        self.show_f_counts = LabeledEntry(f, var_ref=self.filtered_counts, \
                                        label_text=\
                                        "# counts with filter: ",\
                                            label_side='before')
        self.show_t_counts = LabeledEntry(f, var_ref=self.tot_counts, \
                                        label_text=\
                                        "Total counts: ",\
                                            label_side='before')
        self.filter_button = ctk.CTkButton(f, text='Selected to Filter',width=0,\
                                          command=self.get_apply_filter)
        self.fmin_show = LabeledEntry(f, var_ref=self.fmin, \
                                      label_text="Filter minimum", \
                                        label_side='before')
        self.fmax_show = LabeledEntry(f, var_ref=self.fmax, \
                                      label_text="Filter maximum", \
                                        label_side='before')
    
        # layout widgets
        self.show_f_counts.grid(row=0,column=0,padx=(5,0),pady=(5,0),sticky='ew')
        self.show_t_counts.grid(row=0,column=1,padx=5,pady=(5,0),sticky='ew')
        self.minBinController.grid(row=1,column=0,padx=(5,0),pady=3,sticky='ew')
        self.maxBinController.grid(row=1,column=1,padx=3,pady=3,sticky='ew')
        self.update_button.grid(row=1,column=2,padx=(0,5),pady=3,sticky='ew')
        self.fmin_show.grid(row=2,column=0,padx=(5,0),pady=(0,5),sticky='ew')
        self.fmax_show.grid(row=2,column=1,padx=3,pady=(0,5),sticky='ew')
        self.filter_button.grid(row=2,column=2,padx=(0,5),pady=(0,5),sticky='ew')

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
        self.x_slope = tk.DoubleVar(self, -45)
        self.y_slope = tk.DoubleVar(self, -45)

        # define widgets
        self.preview = SubplotCanvas(master=self, mode='save only', cwidth=375,\
                                   cheight=750,
                                   label_text='Filtered Data Preview', \
                                   axis_1_label='Idler', axis_2_label='Signal')
        self.correlations = AngleCanvas(master=self,mode='cursor',cwidth=375,\
                                          cheight=750, angle_1=self.x_slope, \
                                            angle_2=self.y_slope, \
                                              label_text='X-Y Correlations',
                                                axis_1_label='X Correlations', \
                                                  axis_2_label='Y Correlations')
        self.x_control = SlopeControl(master=self, slope=self.x_slope, \
                                  command=self.correlations.show_preview_0, \
                                    label_text='X-Control', direction='X')
        self.y_control = SlopeControl(master=self, slope=self.y_slope, \
                                  command=self.correlations.show_preview_1, \
                                    direction='Y', label_text='Y-Control')

        # modify widgets
        self.filtered_data_updates.append([self.update_preview, \
                                       self.update_correlations])
        
        # layout widgets
        self.columnconfigure(2,weight=1)
        self.preview.grid(row=0,rowspan=2,column=0,padx=(5,3),pady=5,\
                          sticky='ew')
        self.correlations.grid(row=0,rowspan=2,column=1,padx=0,pady=(5,3),\
                               sticky='ew')
        self.x_control.grid(row=0,column=2,padx=(3,5),pady=(5,3),sticky='ew')
        self.y_control.grid(row=1,column=2,padx=(3,5),pady=(0,5),sticky='ew')

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

class SlopeControl(LabeledFrame):
    def __init__(self, *args, slope:tk.DoubleVar, direction:str, \
                 command: Callable, **kwargs):
        super().__init__(*args, **kwargs)

        f = self.get_frame()
        self.slopeLabel = ctk.CTkLabel(master=f, \
                                       text=f'{direction}-Slope Angle: ')
        self.slopeSlider = ctk.CTkSlider(master=f, from_=-90, to=90, \
                                         number_of_steps=180*4, \
                                          command=command, \
                                             variable=slope)
        self.slopeView = ctk.CTkEntry(master=f, width=50, \
                                      textvariable=slope)
        
        f.columnconfigure(1, weight=1)
        self.slopeLabel.grid(row=0,column=0,padx=(5,3),pady=5,sticky='ew')
        self.slopeSlider.grid(row=0,column=1,padx=0,pady=5,sticky='ew')
        self.slopeView.grid(row=0,column=2,padx=(3,5),pady=5,sticky='ew')