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
    plt.plot(x, y, '--')
    plt.axis('equal')


w = np.linspace(0, 25 ,1e5)
d = func(w, 5, 1, 1j)
plt.figure()
plt.plot(w, np.abs(d))

# Nyquist
plt.figure()
plt.plot(d.real, d.imag)

# Circle
x0, y0, R0 = circle_fit(d)
circle_plot(x0, y0, R0)





