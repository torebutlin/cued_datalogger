from Recorder import *
#import matplotlib.pyplot as plt


rec = Recorder(1,44100,1024,pyaudio.paInt16)
rec.set_filename('test.wav')
rec.device_info_name()
#audio_data = rec.record(3)
rec.show_recording(30)
rec.close()

#plt.plot(np.array(range(len(audio_data)))/44100,audio_data)
#plt.show()


