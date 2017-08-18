import numpy as np


def to_dB(x):
    """A simple function that converts x to dB"""
    return 20*np.log10(x)


def from_dB(x):
    """A simple function that converts x in dB to a ratio over 1"""
    return 10**(x/20)


class MatlabList(list):
    """A list that allows slicing like Matlab.

    eg. l[1, 2, slice(3, 5), slice(10, 20, 2)]
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

