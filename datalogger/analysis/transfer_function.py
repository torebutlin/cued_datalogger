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

def compute_transfer_function(in_fft_data,out_fft_data):
    autospec_in = in_fft_data * np.conjugate(in_fft_data)
    autospec_out = out_fft_data * np.conjugate(out_fft_data)
    #crossspec = in_fft_data * np.conjugate(out_fft_data)
    crossspec = out_fft_data * np.conjugate(in_fft_data)
    
    transfer_func = autospec_out/crossspec
    coherence = (crossspec * np.conjugate(crossspec))/(autospec_in*autospec_out)
    
    #print(transfer_func,coherence)
    return(transfer_func,coherence)