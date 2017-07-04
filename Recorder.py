# Add codes to install pyaudio if pyaudio is not installed
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import wave

"""
Recorder class:
- Allow recording and configurations of recording device
- Return recording as numpy array
"""

class Recorder():
    def __init__(self,channels,rate,frames_per_buffer,audio_format):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.format = audio_format
        self.p = pyaudio.PyAudio()
        self.device_index = 0;
        self.filename = None
    

    # TODO: Define function to initialise a PyAudio object
    def open(self):
        if self.p == None:
            self.p = pyaudio.PyAudio()
    
    # Originally setting file name for the wave file    
    def set_filename(self,filename):
        self.filename = filename
        
    # Play back a recording    
    def play_recording(self,filename = None):
        if filename == None:
            filename = self.filename
        
        if filename != None:
            wf = wave.open(filename,'rb')

            output_stream = self.p.open(format = self.p.get_format_from_width(wf.getsampwidth()),
                            channels = wf.getnchannels(),
                            rate = wf.getframerate(),
                            output = True)
            
            data = wf.readframes(self.frames_per_buffer)
            print('PLAYBACK...')
            while len(data)>0:
                output_stream.write(data)
                data = wf.readframes(self.frames_per_buffer)
            print('PLAYBACK STOP')
            
            wf.close()
            output_stream.stop_stream()
            output_stream.close()
                               
    def set_device_index(self,index):
       # TODO: Add check for invalid index input
        self.device_index = index;
        print("Selected device: %s" % (self.p.get_device_info_by_index(index)['name']))
        
    def current_device_info(self):
        print(self.p.get_device_info_by_index(self.device_index))
        
    # Get recording device info 
    def available_devices(self):
        for i in range(self.p.get_device_count()):
            print("%i) %s" % (i,self.p.get_device_info_by_index(i)['name']))
            
    #TODO: Add function(s) to configure recording device
            # Like changing recording device
            
    # May want to change to a callback method for responsive recording
    # Currently it is using blocking method
    def record(self,duration):
        rc = wave.open(self.filename,'wb')
        rc.setnchannels(self.channels)
        rc.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        rc.setframerate(self.rate)
        data_array = []
        input_stream = self.p.open(channels = self.channels,
                         rate = self.rate,
                         format = self.format,
                         input = True,
                         frames_per_buffer = self.frames_per_buffer,
                         input_device_index = self.device_index)

        print('RECORDING...')
        for _ in range(int(self.rate/self.frames_per_buffer * duration)):
            data = input_stream.read(self.frames_per_buffer)
            rc.writeframes(data)
            data_array.append(np.fromstring(data,dtype = np.int16))

        print('RECORDING END')
        rc.close()
        input_stream.stop_stream()
        input_stream.close()

        return np.hstack(data_array)

    #TODO: Complete callback function for non-blocking method
    def record_callback(self,in_data,frame_count,time_info,status_flag):
        #TODO: insert code to record data
        return(data,pyaudio.paContinue)
    
    #TODO: Live oscilloscope here?
    def show_recording(self, duration):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
        input_stream = self.p.open(channels = self.channels,
                         rate = self.rate,
                         format = self.format,
                         input = True,
                         frames_per_buffer = self.frames_per_buffer)
        print('LISTENING...')
        data = np.array(np.fromstring( input_stream.read(self.frames_per_buffer),
                              dtype = np.int16))
        
        line = ax.plot(np.array(range(len(data)))/self.rate,data)[0]
        ax.set_ylim(-10000,10000)
        fig.show()
        for _ in range(int(self.rate/self.frames_per_buffer * duration)):
            data = np.array(np.fromstring( input_stream.read(self.frames_per_buffer),
                              dtype = np.int16))
            line.set_ydata(data)
            fig.canvas.draw()

        print('LISTENING END')
        plt.close(fig)
        input_stream.stop_stream()
        input_stream.close()

        
    def close(self):
        self.p.terminate()
        self.p = None

