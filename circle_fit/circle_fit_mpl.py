import numpy as np

import matplotlib.pyplot as plt

def func(w, wr, nr, c):
    return c / (wr**2 - w**2 + 1j * nr * wr**2)

def circle_fit(data):
    # Take the real and imaginary parts
    x = data.real
    y = data.imag
    
    # Use the method from "Theoretical and Experimental Modal Analysis" p221
    # Set up the matrices
    xs = np.sum(x)
    ys = np.sum(y)
    xx = np.square(x).sum()
    yy = np.square(y).sum()
    xy = np.sum(x*y)
    L = data.size
    xxx = np.sum(x*np.square(x))
    yyy = np.sum(y*np.square(y))
    xyy = np.sum(x*np.square(y))
    yxx = np.sum(y*np.square(x))
    
    A = np.asarray([[xx, xy, -xs],
                    [xy, yy, -ys],
                    [-xs, -ys, L]])
    
    B = np.asarray([[-(xxx + xyy)],
                     [-(yyy + yxx)],
                     [xx + yy]])
    
    # Solve the equation
    v = np.linalg.solve(A, B)
    
    # Find the circle parameters
    x0 = v[0]/-2
    y0 = v[1]/-2
    R0 = np.sqrt(v[2] + x0**2 + y0**2)
    return x0, y0, R0

def circle_plot(x0, y0, R0):
    theta = np.linspace(-np.pi, np.pi, 180)
    x = x0[0] + R0[0]*np.cos(theta)
    y = y0[0] + R0[0]*np.sin(theta)
    return x, y

def update_plots():
    print("Getting axes limits...")
    wmin, wmax = ax1.get_xlim()
    
    lower = np.where(w>wmin)[0][0]
    upper = np.where(w<wmax)[0][-1]
    print(lower, upper)
    
    d_ = d[lower:upper]
    
    ax2.clear()
    ax2.plot(d_.real, d_.imag)

    ax3.clear()
    x0, y0, R0 = circle_fit(d_)
    x_c, y_c = circle_plot(x0, y0, R0)
    ax3.plot(d_.real, d_.imag)
    ax3.plot(x_c, y_c, '--')
    
fig = plt.figure()

w = np.linspace(0, 25 ,1e5)
d = func(w, 10, 1e-2, 500j) #+ func(w, 5, 1e-2, 200j) 

ax1 = fig.add_subplot(211)
ax1.set_title("Transfer function")
ax1.plot(w, np.abs(d))
# Add event handling:
#ax1.callbacks.connect('xlim_changed', update_plots)


# Nyquist
ax2 = fig.add_subplot(223)
ax2.set_title("Nyquist plot")
plt.gca().set_aspect('equal', adjustable='box')

# Circle
ax3 = fig.add_subplot(224)
ax3.set_title("Nyquist plot with circle fit")
plt.gca().set_aspect('equal', adjustable='box')
   
update_plots()
plt.show()




