import customtkinter as ctk
import tpx3_toolkit as t3
import tpx3_toolkit.viewer as t3view

from Helpers import *
from CustomTKWidgets import *

class AnalysisTab(ctk.CTkFrame):
    '''
    The tab where all of the analysis work occurs
    '''
    def __init__(self, *args, filtered_data:ReferentialNpArray, \
                 filtered_data_updates, **kwargs):
        super().__init__(*args, **kwargs)

        # init
        self.filtered_data = filtered_data
        self.filtered_data_updates = filtered_data_updates

        # add sub-tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.add("Traces")
        self.tabs.add("Correlation")
        self.left_align_tabs()
        self.tabs.set("Traces")

        # add widgets to tabs
        self.tracestab = TracesTab(master=self.tabs.tab("Traces"),\
                                filtered_data=self.filtered_data, \
                                filtered_data_updates=self.filtered_data_updates)
        self.correlationtab = CorrelationTab(master=self.tabs.tab("Correlation"),\
                                filtered_data=self.filtered_data, \
                                filtered_data_updates=self.filtered_data_updates)

        # layout tabs
        self.tracestab.pack(padx=0,pady=0,anchor='center',expand=True,\
                                  fill='both')
        self.correlationtab.pack(padx=0,pady=0,anchor='center',expand=True,\
                                 fill='both')
        self.tabs.pack(padx=5, pady=0, anchor='center',expand=True,fill='both')

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
            
class TracesTab(ctk.CTkFrame):
    def __init__(self, *args, filtered_data:ReferentialNpArray, \
                 filtered_data_updates:CanvasList, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.filtered_data = filtered_data
        self.filtered_data_updates = filtered_data_updates
        self.x_loc = tk.IntVar(self,-1)
        self.x_orientation = tk.StringVar(self,'x')
        self.xtracemin = tk.IntVar(self,0)
        self.xtracemax = tk.IntVar(self,0)
        self.y_loc = tk.IntVar(self,-1)
        self.y_orientation = tk.StringVar(self,'x')
        self.ytracemin = tk.IntVar(self,0)
        self.ytracemax = tk.IntVar(self,0)
        self.xfwhmmin = tk.IntVar(self,0)
        self.xfwhmmax = tk.IntVar(self,0)
        self.xfwhm = tk.DoubleVar(self,0)
        self.yfwhmmin = tk.IntVar(self,0)
        self.yfwhmmax = tk.IntVar(self,0)
        self.yfwhm = tk.DoubleVar(self,0)

        # define widgets
        self.correlations = TraceCanvas(master=self, mode='cursor', \
                                        cwidth=375, cheight=750, \
                                        orientation_1=self.x_orientation, \
                                        orientation_2=self.y_orientation, \
                                        label_text="X-Y Correlations",\
                                        axis_1_label="X Correlations",\
                                        axis_2_label="Y Correlations")
        self.traces = SubplotCanvas(master=self, mode='save only', \
                                    cwidth=375, cheight=750, \
                                    label_text="X-Y Correlation Traces", \
                                    axis_1_label='X Trace', \
                                    axis_2_label='Y Trace')
        self.traceinfo_x = TraceControl(master=self,loc=self.x_loc,\
                                     direction='X-Trace', \
                                     orientation=self.x_orientation, \
                                     tracemin=self.xtracemin, \
                                     tracemax=self.xtracemax, \
                                     redrawcommand=self.update_trace_1, \
                                     filtered_data=self.filtered_data, \
                                     fwhmmin=self.xfwhmmin,\
                                     fwhmmax=self.xfwhmmax,\
                                     fwhm=self.xfwhm,\
                                     label_text='X-Control and Info')
        self.traceinfo_y = TraceControl(master=self,loc=self.y_loc,\
                                     direction='Y-Trace',\
                                     orientation=self.y_orientation, \
                                     tracemin=self.ytracemin, \
                                     tracemax=self.ytracemax, \
                                     redrawcommand=self.update_trace_2, \
                                     filtered_data=self.filtered_data, \
                                     fwhmmin=self.yfwhmmin,\
                                     fwhmmax=self.yfwhmmax,\
                                     fwhm=self.yfwhm,\
                                     label_text='Y-Control and Info')
        
        # modify widgets
        self.filtered_data_updates.append([self.update_correlations, \
                                           self.update_trace_1, \
                                           self.update_trace_2])

        # layout widgets
        self.columnconfigure(2,weight=1)
        self.correlations.grid(row=0,rowspan=2,column=0,padx=(5,3),pady=5,\
                          sticky='ew')
        self.traces.grid(row=0,rowspan=2,column=1,padx=0,pady=5,\
                          sticky='ew')
        self.traceinfo_x.grid(row=0,column=2,padx=(3,5),pady=(5,3),sticky='ew')
        self.traceinfo_y.grid(row=1,column=2,padx=(3,5),pady=(0,5),sticky='ew')

    def update_correlations(self, data:ReferentialNpArray):
        self.correlations.ax_1.clear()
        self.correlations.ax_2.clear()
        self.correlations.ax_1.set_xlabel("$X_i$ (pixels)")
        self.correlations.ax_1.set_ylabel("$X_s$ (pixels)")
        self.correlations.ax_2.set_xlabel("$Y_i$ (pixels)")
        self.correlations.ax_2.set_ylabel("$Y_s$ (pixels)")

        t3view.plot_correlations(data.get(), fig=self.correlations.figure)
        self.correlations.show_1(self.x_loc.get())
        self.correlations.show_2(self.y_loc.get())
        self.correlations.redraw()
        self.correlations.init_home()
    
    def update_trace_1(self, data:ReferentialNpArray):
        (loc1, loc2) = self.correlations.get_clicks()
        self.correlations.clickx = None
        if loc1 >= 0:
            self.x_loc.set(loc1)
        if self.x_loc.get() == -1:
            # avoids the issue that range is based on selected size
            idlmin = np.min(self.filtered_data.get()[0,0,:])
            idlmax = np.max(self.filtered_data.get()[0,0,:])
            idl = idlmax - idlmin
            sigmin = np.min(self.filtered_data.get()[1,0,:])
            sigmax = np.max(self.filtered_data.get()[1,0,:])
            sig = sigmax - sigmin
            self.x_loc.set(sig // 2)
            self.xtracemin.set(0)
            self.xtracemax.set(sig)

        self.traces.ax_1.clear()
        (fig,out,allout) = t3view.plot_coincidence_trace(data.get()[:,0,:],\
                                            self.x_loc.get(), \
                                            self.x_orientation.get(), \
                                            self.xtracemin.get(),\
                                            self.xtracemax.get(), \
                                            self.traces.ax_1)
        self.traces.redraw()
        self.correlations.show_1(self.x_loc.get())
        self.correlations.redraw()

        (fwhmmin,fwhmmax,fwhm) = self.fwhm_avg(allout, self.x_orientation)
        self.xfwhmmin.set(fwhmmin)
        self.xfwhmmax.set(fwhmmax)
        self.xfwhm.set(fwhm)
    
    def update_trace_2(self, data:ReferentialNpArray):
        (loc1, loc2) = self.correlations.get_clicks()
        self.correlations.clicky = None
        if loc2 >= 0:
            self.y_loc.set(loc2)
        if self.y_loc.get() == -1:
            # avoids the issue that range is based on selected size
            idlmin = np.min(self.filtered_data.get()[0,1,:])
            idlmax = np.max(self.filtered_data.get()[0,1,:])
            idl = idlmax - idlmin
            sigmin = np.min(self.filtered_data.get()[1,1,:])
            sigmax = np.max(self.filtered_data.get()[1,1,:])
            sig = sigmax - sigmin
            self.y_loc.set(sig // 2)
            self.ytracemin.set(0)
            self.ytracemax.set(idl)

        self.traces.ax_2.clear()
        (fig,out,allout) = t3view.plot_coincidence_trace(data.get()[:,1,:],\
                                            self.y_loc.get(), \
                                            self.y_orientation.get(), \
                                            self.ytracemin.get(),\
                                            self.ytracemax.get(), \
                                            self.traces.ax_2)
        self.traces.redraw()
        self.correlations.show_2(self.y_loc.get())
        self.correlations.redraw()

        (fwhmmin,fwhmmax,fwhm) = self.fwhm_avg(allout, self.y_orientation)
        self.yfwhmmin.set(fwhmmin)
        self.yfwhmmax.set(fwhmmax)
        self.yfwhm.set(fwhm)

    def fwhm_avg(self,view:np.ndarray,orientation:tk.StringVar) \
                                                        -> tuple[int,int,float]:
        fwhm_list = []
        if orientation.get() == 'x':
            halfmaxs = np.max(view,axis=0,keepdims=True) / 2
            halfmaxs[halfmaxs <= 5] = np.inf # bg tends to be around 5
            test = view >= halfmaxs

            for (col,maxi,viewi) in zip(test.T,halfmaxs.T,view.T):
                indc = np.nonzero(col)[0]
                if indc.size > 0: # ignore excluded cols
                    fwhm_list.append((indc[-1]+1) - indc[0])
        else:
            halfmaxs = np.max(view,axis=1,keepdims=True) / 2
            halfmaxs[halfmaxs <= 5] = np.inf # bg tends to be around 5
            test = view >= halfmaxs

            for row in test:
                indc = np.nonzero(row)[0]
                if indc.size > 0: # ignore excluded rows
                    fwhm_list.append((indc[-1]+1) - indc[0])

        # removing outliers
        fwhm_list = np.array(fwhm_list)
        fwhm_list = fwhm_list[np.abs(fwhm_list - np.mean(fwhm_list)) < 2 * np.std(fwhm_list)]

        return (np.min(fwhm_list), np.max(fwhm_list), np.mean(fwhm_list)) #type:ignore

class TraceControl(LabeledFrame):
    def __init__(self, *args, loc:tk.IntVar, direction:str, \
                 orientation:tk.StringVar, tracemin:tk.IntVar,\
                 tracemax:tk.IntVar, redrawcommand:Callable, \
                 filtered_data:ReferentialNpArray, fwhmmin:tk.IntVar, \
                 fwhmmax:tk.IntVar, fwhm:tk.DoubleVar, **kwargs):
        super().__init__(*args, **kwargs)
        self.loc = loc
        self.redrawcommand = redrawcommand
        self.filtered_data = filtered_data

        f = self.get_frame()
        self.traceloc = LabeledEntry(f, var_ref=loc, 
                                     label_text=f"{direction} Trace Location: ",\
                                     label_side='before')
        self.orientationchoice = ctk.CTkComboBox(master=f, \
                                                 variable=orientation,\
                                                 values=['x','y'],width=0)
        self.tracebutton = ctk.CTkButton(f,text='Show Trace',width=0,
                                         command=self.update_redraw)
        self.tracemin = LabeledEntry(f, var_ref=tracemin,\
                                     label_text='Trace min: ', \
                                        label_side='before')
        self.tracemax = LabeledEntry(f, var_ref=tracemax,\
                                     label_text='Trace max: ', \
                                        label_side='before')
        self.redrawtrace = ctk.CTkButton(f,text='Update Trace', width=0, \
                                         command=self.update_redraw)
        self.fwhmmin = LabeledEntry(f, var_ref=fwhmmin, \
                                    label_text='Min(Sum(FWHM)): ', \
                                    label_side='before')
        self.fwhmmax = LabeledEntry(f, var_ref=fwhmmax, \
                                    label_text='Max(Sum(FWHM)): ', \
                                    label_side='before')
        self.fwhm = LabeledEntry(f, var_ref=fwhm, \
                                    label_text='Avg(Sum(FWHM)): ', \
                                    label_side='before')
        
        f.columnconfigure(2, weight=1)
        self.traceloc.grid(row=0,column=0,padx=(5,0),pady=(5,0),sticky='ew')
        self.orientationchoice.grid(row=0,column=1,padx=3,pady=(5,0),sticky='ew')
        self.tracebutton.grid(row=0,column=2,padx=(0,5),pady=(5,0),sticky='ew')
        self.tracemin.grid(row=1,column=0,padx=(5,0),pady=3,sticky='ew')
        self.tracemax.grid(row=1,column=1,padx=3,pady=3,sticky='ew')
        self.redrawtrace.grid(row=1,column=2,padx=(0,5),pady=3,sticky='ew')
        self.fwhm.grid(row=2,column=0,padx=(5,0),pady=(0,5),sticky='ew')
        self.fwhmmin.grid(row=2,column=1,padx=3,pady=(0,5),sticky='ew')
        self.fwhmmax.grid(row=2,column=2,padx=(0,5),pady=(0,5),sticky='ew')

    def update_redraw(self):
        self.redrawcommand(data=self.filtered_data)

class CorrelationTab(ctk.CTkFrame):
    def __init__(self, *args, filtered_data:ReferentialNpArray, \
        filtered_data_updates:CanvasList, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.filtered_data = filtered_data
        self.filtered_data_updates = filtered_data_updates

        # create widgets
        self.plot = CanvasFrame(master=self, label_text='X-Y Correlations', \
                                mode='cursor', zoom=True, cwidth=800, \
                                cheight=800)
        self.plotcontrol = XYControl(master=self, label_text='X-Y Control')

        # modify widgets
        self.filtered_data_updates.append([self.update_plot])

        # layout widgets
        self.columnconfigure(1,weight=1)
        self.plot.grid(row=0,column=0,padx=(5,0),pady=5,sticky='ew')
        self.plotcontrol.grid(row=0,column=1,padx=(3,5),pady=5,sticky='ew')

    def update_plot(self, data:ReferentialNpArray):
        self.plot.ax.clear()
        self.plot.ax.set_title('Coincidences')

        (fig, view) = t3view.plot_coincidence_xy(data.get(), \
                                                 fig=self.plot.figure)

        max_ind = np.unravel_index(view.argmax(), view.shape)
        self.plotcontrol.update_center(np.mean(max_ind[0]), np.mean(max_ind[1])) #type:ignore
        self.plotcontrol.fwhm_x.set(self.fwhm(\
                                    view[:,int(self.plotcontrol.center_pos_y)])) # type:ignore
        self.plotcontrol.fwhm_y.set(self.fwhm(\
                                    view[int(self.plotcontrol.center_pos_x),:])) # type:ignore

        self.plot.redraw()
        self.plot.init_home()

    def fwhm(self, view) -> int:
        halfmax = np.max(view) / 2
        indc = np.nonzero(view >= halfmax)[0]

        return (indc[-1]+1) - indc[0]

class XYControl(LabeledFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # init data
        self.center_pos_x = 0
        self.center_pos_y = 0
        self.center_pos = tk.StringVar(self, '(0,0)')
        self.fwhm_x = tk.IntVar(self, -1)
        self.fwhm_y = tk.IntVar(self, -1)

        # create widgets
        f = self.get_frame()
        self.pos_view = LabeledEntry(master=f, var_ref=self.center_pos, \
                                     label_text='Center: ', label_side='before')
        self.fwhm_x_view = LabeledEntry(master=f, var_ref=self.fwhm_x, \
                                        label_text='FWHM_x: ', \
                                        label_side='before')
        self.fwhm_y_view = LabeledEntry(master=f, var_ref=self.fwhm_y, \
                                        label_text='FWHM_y: ', \
                                        label_side='before')

        # layout widgets
        self.pos_view.grid(row=0,column=0,padx=5,pady=(5,0),sticky='ew')
        self.fwhm_x_view.grid(row=1,column=0,padx=5,pady=3,sticky='ew')
        self.fwhm_y_view.grid(row=2,column=0,padx=5,pady=(0,5),sticky='ew')

    def update_center(self, x:float, y:float):
        self.center_pos_x = x
        self.center_pos_y = y
        self.center_pos.set(f'({self.center_pos_x},{self.center_pos_y})')