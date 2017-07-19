import numpy as np

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
    wmin, wmax = p1.getAxis('bottom').range
    dmin, dmax = p1.getAxis('left').range
    
    lower_w = np.where(w>wmin)[0][0]
    upper_w = np.where(w<wmax)[0][-1]
    lower_d = np.where(d>dmin)[0][0]
    upper_d = np.where(d<dmax)[0][-1]
    
    if lower_w > lower_d:
        lower = lower_w
    else:
        lower = lower_d
    if upper_w < upper_d:
        upper = upper_w
    else:
        upper = upper_w
    
    d_ = d[lower:upper]
    
    p2.clear()
    p2.plot(d_.real, d_.imag)
    
    p3.clear()
    x0, y0, R0 = circle_fit(d_)
    #print(calculate_interesting_values(x0, y0, R0))
    x_c, y_c = circle_plot(x0, y0, R0)
    p3.plot(d_.real, d_.imag, pen=pg.mkPen(width=4))
    p3.plot(x_c, y_c, pen=pg.mkPen('r', width=2, style=QtCore.Qt.DashLine))


def calculate_interesting_values(x0, y0, R0):
    re, im = circle_plot(x0, y0, R0)
    cmplx = re + 1j*im
    
    # Resonant frequency and phase angle
    w0, t0 = 0, 0
    w1, t1 = 0, 0
    w2, t2 = 0, 0
    w3, t3 = 0, 0
    
    def tAtB(tA, tB, wA, wB):
        return (tA - tB) / (wA**2 - wB**2)
    
    def tAtBtC(tA, tB, tC, wA, wB, wC):
        return (tAtB(tA, tB, wA, wB) - tAtB(tB, tC, wB, wC)) / (wA**2 - wC**2)
    
    def tAtBtCtD(tA, tB, tC, tD, wA, wB, wC, wD):
        return (tAtBtC(tA, tB, tC, wA, wB, wC) - tAtBtC(tB, tC, tD, wB, wC, wD)) / (wA**2 - wD**2)
    
    t0t1 = tAtB(t0, t1, w0, w1)
    t0t1t2 = tAtBtC(t0, t1, t2, w0, w1, w2)
    t0t1t2t3 = tAtBtCtD(t0, t1, t2, t3, w0, w1, w2, w3)
    
    wr2 = (w0**2 + w1**2 + w2**2 - (t0t1t2 / t0t1t2t3)) / 3
    wr = np.sqrt(wr2)
    tr = t0 + (wr2 - w0**2)*t0t1 + (wr2 - w0**2)*(wr2 - w1**2)*t0t1t2 + (wr2 - w0**2)*(wr2 - w1**2)*(wr2 - w2**2)*t0t1t2t3
    
    # Damping factor
    def calc_nr(wr, tr, wa, wb, ta, tb):
        return (wa**2 - wb**2)/ (wr**2 * (np.tan(ta - tr) + np.tan(tr - tb)))
    
    w1, t1 = 0, 0
    w2, t2 = 0, 0
    w3, t3 = 0, 0
    w4, t4 = 0, 0
    w5, t5 = 0, 0
    w6, t6 = 0, 0
    
    # Take mean of points
    #3,4
    nr34 = calc_nr(wr, tr, w3, w4, t3, t4)
    
    #2,5
    nr25 = calc_nr(wr, tr, w2, w5, t2, t5)
    
    #1,6
    nr16 = calc_nr(wr, tr, w1, w6, t1, t6)
    
    nr = (nr34 + nr25 + nr16)/3
    
    # Modal Constant
    # Modulus:
    C = 2*R0*wr2*nr
    
    # Phase angle
    xD = 0
    yD = 0
    phi = np.atan((x0 - xD) / (y0 - yD))
    
    return wr, nr, C, phi

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

# Create a demo FRF
w = np.linspace(0, 25 ,1e5)
d = 20*np.log10(func(w, 10, 1e-2, 8e12+1e9j) + func(w, 5, 1e-1, 8e12+1e9j) + func(w, 20, 5e-2, 8e12+1e9j) + func(w, 12, 2e-2, 8e12+1e9j))


win = pg.GraphicsWindow(title="Circle Fit")

# Transfer fn
p1 = win.addPlot(title="Transfer function", x=w, y=np.abs(d))
p_select = win.addPlot(title="Region Selection", x=w, y=np.abs(d))

# Create ROI - NOTE THIS DOES NOT WORK WELL
# TODO: reimplement the ROI, really jerky updates
roi = pg.ROI([w[0], d.min()], [w.max(), d.max()-d.min()], pen='r')
# Horizontal scale handles
roi.addScaleHandle([1, 0.5], [0, 0.5])
roi.addScaleHandle([0, 0.5], [1, 0.5])
# Vertical scale handles
roi.addScaleHandle([0.5, 0], [0.5, 1])
roi.addScaleHandle([0.5, 1], [0.5, 0])
# Corner scale handles
roi.addScaleHandle([1, 1], [0, 0])
roi.addScaleHandle([0, 0], [1, 1])
p_select.addItem(roi)


def update_zoom():
    x_min, y_min = roi.pos()
    x_max, y_max = roi.pos() + roi.size()
    p1.setXRange(x_min, x_max, padding=0)
    p1.setYRange(y_min, y_max, padding=0)

def update_roi():
    region = np.asarray(p1.getViewBox().viewRange())
    roi.setPos(region[:, 0])
    roi.setSize(region[:, 1] - region[:, 0])
    

roi.sigRegionChanged.connect(update_zoom)
roi.sigRegionChanged.connect(update_plots)
p1.sigXRangeChanged.connect(update_roi)
p1.sigXRangeChanged.connect(update_plots)
update_zoom()

win.nextRow()
# Nyquist
p2 = win.addPlot(title="Nyquist plot")
# Circle
p3 = win.addPlot(title="Nyquist plot with circle fit")



update_plots()





