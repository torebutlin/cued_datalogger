'''
kivy requires some library installation
'''

import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')

import matplotlib.pyplot as plt
import kivy
kivy.require('1.10.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvas

import Recorder as rcd

#-------------- Root Widget (to be built) ----------------------
class RootWidget(BoxLayout):
    def __init__(self, rec = None, **kwargs):
        #--------------- UI Constuctions ---------------------
        super(RootWidget, self).__init__(**kwargs)
        # Set up the widgets orientations
        self.padding = 10
        self.orientation = 'vertical'
        
        # Play the recorder
        self.rec = rec
        self.rec.stream_init(playback = True)
        self.playing = True

        # Set up the plot canvas
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_ylim(-5e4,5e4)
        self.line = ax.plot(range(len(self.rec.signal_data)),
                            self.rec.signal_data)[0]
        self.canvas_widget = FigureCanvas(fig)
        self.add_widget(self.canvas_widget)

        # Set up the button
        btn = Button(text='Switch')
        btn.bind(on_press = self.toggle_rec)
        self.add_widget(btn)
        btn.size_hint_y = 0.1

        # Set up live update plot
        event = Clock.schedule_interval(self.update_line, 1 / 60.)
    #--------------- UI Callback Methods ---------------------
    def update_line(self,dt):
        self.line.set_ydata(self.rec.signal_data)
        self.canvas_widget.draw()
        
    def toggle_rec(self,*args):
        if self.playing:
            self.rec.stream_stop()
        else:
            self.rec.stream_start()
        self.playing = not self.playing
#-------------- MyApp Class ----------------------        
class MyApp(App):

    def __init__(self):
        super().__init__()
        # Set up recorder class
        self.rec = rcd.Recorder(device_name = 'Line (U24XL with SPDIF I/O)')
        # Set up window parameter
        Window.size = (500,500)
        # Initialise root widget passing recorder class
        self.rootwidget = RootWidget(rec = self.rec);

    # Build the root widget   
    def build(self):
        # Failed attempt at making a closing messagebox
        Window.bind(on_request_close=self.on_request_close)
        # Build the root widget
        return self.rootwidget

    # Function to be called when closing
    def on_request_close(self, *args,**kwargs):
        self.exit_popup(title='Exit', text='Are you sure?')
        return False
    
    # Exit popup confirmation
    def exit_popup(self,title,text):
        vbox = BoxLayout(orientation='vertical')
        vbox.add_widget(Label(text=text))
        mybutton = Button(text='OK', size_hint=(0.5,1))
        vbox.add_widget(mybutton)

        popup = Popup(title=title, content=vbox, size_hint=(None, None), size= (600, 300))
        mybutton.bind(on_release = self.stop)
        popup.open()

    # Exit events    
    def on_stop(self):
        self.rec.close()
        return False
# ----------------- Main Loop -------------------
if __name__ == '__main__':
    MyApp().run()
