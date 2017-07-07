import Recorder as rcd
import matplotlib.pyplot as plt
import numpy as np
DURATION = 30

fig = plt.figure()
ax = fig.add_subplot(211)
ax.set_ylim(-5e4,5e4)
ax2 = fig.add_subplot(212)
fig.show()
data_array = []

try:
    rec = rcd.Recorder(channels = 1,
                       rate = 44100,
                       frames_per_buffer = 1024,
                       device_name = 'Line (U24XL with SPDIF I/O)')
    rec.stream_init(playback = True)
except Exception as e:
    print(e)
    quit()
#rec.current_device_info()


line = ax.plot(range(len(rec.signal_data)),rec.signal_data)[0]
data_array= np.append(data_array,rec.signal_data)

line2 = ax2.plot(range(5),range(5))[0]

samples = 15
                       
try:
    #while True:
    for _ in range(samples):
        data_array= np.append(data_array,rec.signal_data)
        #print(data_array)
        ax2.cla()
        ax2.plot(range(len(data_array)),data_array)
        line.set_ydata(rec.signal_data)
        fig.canvas.draw()
        fig.canvas.flush_events()
        
except Exception as e:
    print('Some error happened!')
    print(e)
finally:
    rec.stream_stop()
    rec.close()
    #plt.close(fig)
    