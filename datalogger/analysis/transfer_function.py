# -*- coding: utf-8 -*-
"""
Created on Mon Aug 21 14:53:09 2017

@author: eyt21
"""
import numpy as np
from datalogger.api.pyqtgraph_extensions import InteractivePlotWidget


class TransferFunctionWidget(InteractivePlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

def compute_autospec(fft_data):
    return(fft_data * np.conjugate(fft_data))

def compute_crossspec(in_fft_data,out_fft_data):
    #crossspecs = []
    #for fft_data in out_fft_datas:
    #    crossspecs.append(in_fft_data * np.conjugate(fft_data))
    return(in_fft_data * np.conjugate(out_fft_data))

def compute_transfer_function(autospec_in,autospec_out,crossspec):
   
    transfer_func = (autospec_out/crossspec)
    coherence = ((crossspec * np.conjugate(crossspec))/(autospec_in*autospec_out))
    
    return(transfer_func,coherence)