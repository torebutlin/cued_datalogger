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

class RootWidget(BoxLayout):
    def __init__(self, rec = None, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.padding = 10
        self.orientation = 'vertical'

        self.rec = rec
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_ylim(-5e4,5e4)
        self.line = ax.plot(range(len(self.rec.signal_data)),
                            self.rec.signal_data)[0]
        self.canvas_widget = FigureCanvas(fig)
        self.add_widget(self.canvas_widget)
        
        btn = Button(text='Switch')
        self.add_widget(btn)
        btn.size_hint_y = 0.1

        event = Clock.schedule_interval(self.update_line, 1 / 60.)

    def update_line(self,dt):
        self.line.set_ydata(self.rec.signal_data)
        self.canvas_widget.draw()

        
class MyApp(App):

    def __init__(self):
        super().__init__()
        self.rec = rcd.Recorder(1,44100,1024,'Line (U24XL with SPDIF I/O)')
        self.rec.stream_init(playback = True)
        self.playing = True
        self.rootwidget = RootWidget(rec = self.rec);

    
    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        return self.rootwidget

    def on_request_close(self, *args,**kwargs):
        self.exit_popup(title='Exit', text='Are you sure?')
        return False
    
    # Unable to implement an exit confirmation
    def exit_popup(self,title,text):
        vbox = BoxLayout(orientation='vertical')
        vbox.add_widget(Label(text=text))
        mybutton = Button(text='OK', size_hint=(0.5,1))
        vbox.add_widget(mybutton)

        popup = Popup(title=title, content=vbox, size_hint=(None, None), size= (600, 300))
        mybutton.bind(on_release = self.stop)
        popup.open()
        
    def on_stop(self):
        self.rec.stream_stop()
        return False

if __name__ == '__main__':
    MyApp().run()
