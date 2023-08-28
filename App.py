import tkinter as tk
import customtkinter as ctk
import matplotlib as mpl

from CustomTKWidgets import *
from Helpers import *
from LoadTab import *
from FilterTab import *
from AnalysisTab import *

class App(ctk.CTk):
    # TODO: object reference passing cleanup
    # TODO: fix the redraw bug - this is annoying but not an functional issue
    '''
    Main app window for holding all the other components.
    '''
    def __init__(self):
        # set some parameters and do super init
        super().__init__()
        self.title("PixGUI")
        self.geometry("1520x930")

        # define the global data for the whole app
        self.raw_data = ReferentialNpArray()
        self.filtered_data = ReferentialNpArray()
        self.errors = ErrorBox(master=self, label_text="Errors")
        self.raw_data_updates = CanvasList(self.raw_data)
        self.filtered_data_updates = CanvasList(self.filtered_data)
        try:
            self.recall = RecallFile()
        except Exception as e:
            tk.messagebox.showerror('Save file error',str(e)) #type: ignore
            exit(-1)

        # call matplotlib inits
        self.set_mpl_params()

        # create tabs
        self.tabs = ctk.CTkTabview(self)
        self.tabs.add("Load")
        self.tabs.add("Filter")
        self.tabs.add("Analysis")
        self.left_align_tabs() # must be done after all tabs are defined
        self.tabs.set("Load")

        # create widgets in tabs and then place them
        self.loadtab = LoadTab(master=self.tabs.tab("Load"),\
            raw_data=self.raw_data, filtered_data=self.filtered_data,\
                raw_data_updates=self.raw_data_updates, \
                    filtered_data_updates=self.filtered_data_updates, \
                        errors=self.errors)
        self.loadtab.pack(padx=0,pady=0,anchor='center',expand=True,\
            fill='both')
        self.filtertab = FilterTab(master=self.tabs.tab("Filter"),\
            raw_data=self.raw_data, filtered_data=self.filtered_data,\
                raw_data_updates=self.raw_data_updates, \
                    filtered_data_updates=self.filtered_data_updates)
        self.filtertab.pack(padx=0,pady=0,anchor='center',expand=True,\
            fill='both')
        self.analysistab = AnalysisTab(master=self.tabs.tab("Analysis"), \
                filtered_data = self.filtered_data, \
                    filtered_data_updates=self.filtered_data_updates)
        self.analysistab.pack(padx=0,pady=0,anchor='center',expand=True,\
                              fill='both')

        # layout tabs
        self.tabs.pack(padx=10, pady=0, anchor='center', expand=True, \
            fill='both')
        
        self.recallDir()
        self.recallSettings()

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
                self.tabs._corner_radius, self.tabs._border_width)), \
                pady=self.tabs._apply_widget_scaling(max(\
                self.tabs._corner_radius, self.tabs._border_width)))
            
    def save_state(self,file_name:str=''):
        # settings saving should be handled by objects themselves, not root
        new_params = self.recall.parameters.copy()
        
        self.loadtab.save(new_params)
        self.loadtab.process.settings.save(new_params)
        self.filtertab.timetab.save(new_params)

        self.recall.write_file(new_params, file_name)

    def recallAll(self):
        # settings recall should be handled by the objects themselves, not root
        self.loadtab.recall(self.recall)
        self.loadtab.process.settings.recall(self.recall)
        self.filtertab.timetab.recall(self.recall)

    def recallSettings(self):
        self.loadtab.process.settings.recall(self.recall)

    def recallDir(self):
        self.loadtab.recallDir(self.recall)

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