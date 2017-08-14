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
    """
    def __init__(self, *args):
        super().__init__(*args)
    """
    def __getitem__(self, index):
        output = []
        # Allow tuples eg. (1,2)
        if isinstance(index, tuple):
            # Iterate through the tuple
            for i in index:
                # If the item is a slice, indexing with it will give
                # a list so it must be concatenated to the output
                if isinstance(i, slice):
                    output += self[i]
                # If it's an integer, we indexing with it will give one item
                # so it must be appended to the output
                elif isinstance(i, int):
                    output.append(self[i])
            # Remove any multiple occurrences using set
            #return list(set(sorted(output)))
            return list(set(output))
        else:
            return super().__getitem__(index)

