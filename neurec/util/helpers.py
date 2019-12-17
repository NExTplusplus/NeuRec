"""Helper functions to correctly cast values"""
import numpy

def to_list(string):
    """Returns a list from a string.

    string -- string in format [0.5,0.5]|type
    """
    pipe_split = string.split('|')

    try:
        cast = pipe_split[1]
        array = pipe_split[0]
        array_values = array[1:-1].split(',')
    except IndexError:
        raise IndexError('list index out of range for ' + str(string)
                         + '. Make sure the list is the form [0,0]|type')

    return numpy.array(array_values, dtype=cast)

def to_bool(input_value):
    """Returns a boolean from a string.

    input_value -- string in format yes|no|true|false|y|n|1|0
    """
    true_options = ['yes', 'y', 'true', '1']
    false_options = ['no', 'n', 'false', '0']
    input_value = input_value.lower()

    if (input_value not in true_options
            and input_value not in false_options):
        raise ValueError(str(input_value) +
                         'not in ' + str(true_options) + ' or'
                         + str(false_options))

    if input_value in true_options:
        return True

    return False
