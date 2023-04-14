import os
import tkinter as tk
import customtkinter as ctk
import matplotlib as mpl

from CustomTKWidgets import *
from Helpers import *
from LoadTab import *
from FilterTab import *
from ImagingTab import *

class App(ctk.CTk):
    # TODO: settings memory
    # TODO: object reference passing cleanup
    '''
    Main app window for holding all the other components.
    '''
    def __init__(self):
        # set some parameters and do super init
        super().__init__()
        self.title("TPX3 Workshop")
        self.minsize(1500,950)

        # define the global data for the whole app
        self.raw_data = ReferentialNpArray()
        self.filtered_data = ReferentialNpArray()
        self.errors = ErrorBox(master=self, label_text="Errors")
        self.raw_data_updates = CanvasList(self.raw_data)
        self.filtered_data_updates = CanvasList(self.filtered_data)
        try:
            self.recall = RecallFile()
        except Exception as e:
            self.errors.append(
                f'Error trying to read or create recal file:', True)

        # call matplotlib inits
        self.set_mpl_params()

        # create tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.add("Load")
        self.tabs.add("Filter")
        self.tabs.add("Imaging")
        self.left_align_tabs() # must be done after all tabs are defined
        self.tabs.set("Load")

        # create widgets in tabs and then place them
        self.loadtab = LoadTab(master=self.tabs.tab("Load"),\
            raw_data=self.raw_data, filtered_data=self.filtered_data,\
                raw_data_updates=self.raw_data_updates, \
                    filtered_data_updates=self.filtered_data_updates, \
                        recall=self.recall, errors=self.errors)
        self.loadtab.pack(padx=0,pady=0,anchor='center',expand=True,\
            fill='both')
        self.filtertab = FilterTab(master=self.tabs.tab("Filter"),\
            raw_data=self.raw_data, filtered_data=self.filtered_data,\
                raw_data_updates=self.raw_data_updates, \
                    filtered_data_updates=self.filtered_data_updates)
        self.filtertab.pack(padx=0,pady=0,anchor='center',expand=True,\
            fill='both')
        self.imagetab = ImagingTab(master=self.tabs.tab("Imaging"),\
            filtered_data=self.filtered_data)
        self.imagetab.pack(padx=0,pady=0,anchor='center',expand=True,\
            fill='both')

        # layout tabs
        self.tabs.pack(padx=10, pady=10, anchor='center', expand=True, \
            fill='both')

    def set_mpl_params(self):
        if ctk.get_appearance_mode() == "Light":
            mpl.rcParams.update(mpl.rcParamsDefault)
        else:
            mpl.rcParams['text.color'] = '#DCE4EE'
            mpl.rcParams['axes.facecolor'] = '#2B2B2B'
            mpl.rcParams['axes.edgecolor'] = '#DCE4EE'
            mpl.rcParams['xtick.color'] = '#DCE4EE'
            mpl.rcParams['ytick.color'] = '#DCE4EE'
            mpl.rcParams['axes.labelcolor'] = '#DCE4EE'
            mpl.rcParams['figure.facecolor'] = '#2B2B2B'

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
            
    def save_state(self,file_name:str=''):
        new_params = self.recall.parameters.copy()
        try:
            new_params['file'] = self.loadtab.inp_file.get()
            new_params['calib_file'] = self.loadtab.calibration_file.get()
            new_params['spaceWindow'] = self.loadtab.process.settings.spaceWindow.get()
            new_params['timeWindow'] = self.loadtab.process.settings.timeWindow.get()
            new_params['coincWindow'] = self.loadtab.process.settings.coincWindow.get()
            new_params['clusterRange'] = self.loadtab.process.settings.clusterRange.get()
            new_params['numScans'] = self.loadtab.process.settings.numScans.get()
            new_params['beamI'] = self.loadtab.beamI[0].toString()
            new_params['beamS'] = self.loadtab.beamS[0].toString()
        except:
            pass
        self.recall.write_file(new_params, file_name)

    def recallAll(self):
        self.loadtab.inp_file.set(self.recall.parameters['file'])
        self.loadtab.calibration_file.set(self.recall.parameters['calib_file'])
        self.loadtab.process.settings.spaceWindow.set(self.recall.parameters['spaceWindow']) #type:ignore
        self.loadtab.process.settings.timeWindow.set(self.recall.parameters['timeWindow']) #type:ignore
        self.loadtab.process.settings.coincWindow.set(self.recall.parameters['coincWindow']) #type:ignore
        self.loadtab.process.settings.clusterRange.set(self.recall.parameters['clusterRange']) #type:ignore
        self.loadtab.process.settings.numScans.set(self.recall.parameters['numScans']) #type:ignore
        self.loadtab.beamI.append(t3.Beam.fromString(self.recall.parameters['beamI']))
        self.loadtab.beamS.append(t3.Beam.fromString(self.recall.parameters['beamS']))
        # BUG: So it looks like I am somehow not setting the object reference,
        # but instead the object itself. For the Settings this is not an issue,
        # yet for the files it is... I am unsure of the cause. Mostly though it
        # only affects the entry boxes and prevents them from showing the 
        # internal data, yet the data is still there. Maybe I just need to 
        # somehow get the widget to refresh? That's pretty much what I have to
        # do with my custom stuff below

        try: # Sees how far it can get with refreshing stuff
            self.loadtab.loader.load_preview(True)
            self.loadtab.beamSelector.redraw_beams()
        except:
            pass

    def quit_cleanup(self):
        self.save_state()
        self.quit()


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
#    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    app = App()
    app.protocol("WM_DELETE_WINDOW",app.quit_cleanup)
    app.mainloop()