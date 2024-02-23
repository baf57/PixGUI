import os
import csv
import numpy as np
from threading import Thread

import tpx3_toolkit as t3
from CustomTKWidgets import *

class ReferentialNpArray:
    def __init__(self, array:np.ndarray=np.array([])):
        self.array = array

    def set(self,array:np.ndarray):
        self.array = array
    
    def get(self):
        return self.array

class ReturnThread(Thread):
    def __init__(self, target, args:tuple):
        Thread.__init__(self)
        self.target = target
        self.args = args
        self.ret = None

    def run(self):
        self.ret = self.target(*self.args)
        self.angle = None
    def get(self):
        return self.ret

class CanvasList:
    def __init__(self, data:ReferentialNpArray, \
                 update_functions:list[Callable]=[], args:list=[]):
        self.data = data
        self.update_functions = update_functions

        if len(self.update_functions) != len(args):
            self.args = [{} for i in range(len(self.update_functions))]
        else:
            self.args = args

    def append(self, update_functions:list[Callable], args:list=[]):
        self.update_functions.extend(update_functions)

        if len(update_functions) != len(args):
            self.args.extend([{} for i in range(len(update_functions))])
        else:
            self.args.extend(args)

    def update_all(self):
        for (update_function,kwargs) in \
            zip(self.update_functions,self.args):
            update_function(data=self.data, **kwargs)

class RecallFile:
    def __init__(self):
        self.file_path = os.path.join(os.path.curdir, 'recall.t3w')
        self.parameters = {'version': 3,
                           'dir': '',
                           'file':'',
                           'calib_file':'',
                           'spaceWindow':20,
                           'timeWindow':250,
                           'coincWindow':1000,
                           'clusterRange':30,
                           'numScans':20,
                           'beamI':t3.Beam(0,0,0,0).toString(),
                           'beamS':t3.Beam(0,0,0,0).toString(),
                           'fmin':-200,
                           'fmax':200,
                           'ref_file': '',
                           'ref_scale':1.085,
                           'ref_angle':-3.5,
                           'ref_thresh':0.4,
                           'ref_lower':25,
                           'ref_upper':150,
                           'ref_binning':3}

        # check if the recall file exists. If it doesn't then make it
        if not(os.path.exists(self.file_path)):
            self.create_file()

        self.read_file()

    def create_file(self):
        '''
        File will be a csv where each entry is done as a dict. I will make the 
        format of the base dict below. Whenever I want to extend this I cam just
        add a new key-value pair to the dict.
        '''
        # BUG: only first pair of ilder and signal beam locations are recalled
        # this can be fixed, but it is more work than I need right now
        with open(self.file_path, 'w') as f:
            w = csv.DictWriter(f, self.parameters.keys())
            w.writeheader()
            w.writerow(self.parameters)

    def read_file(self):
        try:   
            with open(self.file_path, 'r') as f:
                prelim = csv.reader(f) # check version
                fields = prelim.__next__()
                assert fields[0] == 'version'
                values = prelim.__next__()
                if len(values) == 0:
                    values = prelim.__next__()
                assert values[0] == str(self.parameters['version'])
                
            with open(self.file_path, 'r') as f:
                r = csv.DictReader(f, self.parameters.keys())
                for line in r: # sets twice, but needs to skip header
                    self.parameters = line
        except:
            raise Exception('Save file is wrong version!\n'+\
                            'Please note any needed settings from "recall.t3w" and then delte it!')


    def write_file(self, new_parameters:dict, file_name:str=''):
        # BUG: same beamI and beamS bug as above
        if len(file_name) == 0:
            file_name = self.file_path

        with open(file_name, 'w') as f:
            w = csv.DictWriter(f, fieldnames=new_parameters.keys())
            w.writeheader()
            w.writerow(new_parameters)