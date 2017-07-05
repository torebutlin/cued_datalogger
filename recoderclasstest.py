from Recorder import *
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
    rec = Recorder(1,44100,1024,'Line (U24XL with SPDIF I/O)')
    rec.stream_init(playback = True)
except:
    quit()
rec.current_device_info()


line = ax.plot(range(len(rec.signal_data)),rec.signal_data)[0]
data_array= np.append(data_array,rec.signal_data)

line2 = ax2.plot(range(5),range(5))[0]

samples = 0                       
try:
    #while True:
    while samples<10:
    #for _ in range(DURATION * 100):
        data_array= np.append(data_array,rec.signal_data)
        #print(data_array)
        ax2.cla()
        ax2.plot(range(len(data_array)),data_array)
        line.set_ydata(rec.signal_data)
        fig.canvas.draw()
        fig.canvas.flush_events()
        samples+=1
except:
    print('Some error happened!')
finally:
    rec.stream_stop()
    rec.close()
    #plt.close(fig)
    