# -*- coding: utf-8 -*-
"""
Created on Thu Jul  6 09:41:11 2017

@author: eyt21
"""
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import Recorder as rcd
import tkinter as tk
from tkinter import messagebox

class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Set window parameter
        self.title('LiveStreamPlot')
        self.w = 500
        self.h = 500
        
        # Set recorder object
        self.rec = rcd.Recorder(device_name = 'Line (U24XL with SPDIF I/O)')
        self.rec.stream_init(playback = True)
        self.playing = True
        
        # Construct UI 
        self.initUI()
        
        # Center and set up closing window protocol
        self.center()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
 #------------- App construction methods--------------------------------        
    def initUI(self):
        # Set up Frame to put widget in
        self.frame = tk.Frame(self)
        self.frame.pack(fill = 'both', expand = True)
        
        # Set up the plot canvas
        self.plot_canvas()
        
        # Set up the button
        button = tk.Button(self.frame, text = 'Switch', command = self.toggle_rec)
        button.pack(side = 'top', fill = 'both',padx = 10, pady = 10)
        
    def plot_canvas(self):
        f = Figure(figsize=(5, 4), dpi=100)
        ax = f.add_subplot(111)
        ax.set_ylim(-5e4,5e4)
        self.line = ax.plot(range(len(self.rec.signal_data)),self.rec.signal_data)[0]
        
        self.canvas = FigureCanvasTkAgg(f, master=self.frame)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side = 'top', fill = 'both', 
                                 padx = 10, pady = 10, expand = True)
        
        # Set up live update of plot
        self.after_id = self.after(0, self.update_line)
    
    def center(self):
        # width of the screen
        ws = self.winfo_screenwidth()
        # height of the screen
        hs = self.winfo_screenheight() 
         # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (self.w/2)
        y = (hs/2) - (self.h/2)                            
        
        self.geometry('%dx%d+%d+%d' % (self.w, self.h, x, y))

    #------------- UI callback methods--------------------------------    
    def update_line(self):
        self.line.set_ydata(self.rec.signal_data)
        self.canvas.draw()
        self.after_id = self.after(1, self.update_line)
                            
    def toggle_rec(self):
        if self.playing:
            self.rec.stream_stop()
        else:
            self.rec.stream_start()
            
        self.playing = not self.playing
            
    def on_closing(self):
        if messagebox.askokcancel('Quit','Do you want to quit?'):
            self.rec.close()
            self.after_cancel(self.after_id)
            self.destroy()

#----------------Main loop------------------------------------   
if __name__ == '__main__':    
    root = MyApp()
    root.mainloop()