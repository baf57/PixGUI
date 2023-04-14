import customtkinter as ctk

class ImagingTab(ctk.CTkFrame):
    '''
    The tab where all of the loading stuff occurs
    '''
    def __init__(self, *args, filtered_data, **kwargs):
        super().__init__(*args, **kwargs)