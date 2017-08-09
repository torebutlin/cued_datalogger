import numpy as np

def to_dB(x):
    """A simple function that converts x to dB"""
    return 20*np.log10(x)


def from_dB(x):
    """A simple function that converts x in dB to a ratio over 1"""
    return 10**(x/20)


class MatlabList(list):
    """A list that allows slicing like Matlab.

    eg. l[1, 2, 3:5, 10:20:2]
    """
    def __getitem__(self, index):
        output = []
        if isinstance(index, tuple) or isinstance(index, range):
            for i in index:
                if isinstance(i, range):
                    range_list = list(i)
                    for r in range_list:
                        if r not in index:
                            output.append(self[r])
                else:
                    output.append(self[i])
            return output
        else:
            return super().__getitem__(index)


def circle_fit(data):
    """Fit a circle to complex data"""
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
