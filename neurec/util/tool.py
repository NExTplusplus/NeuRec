"""Functions to handle model requirements"""
import tensorflow as tf

def activation_function(act, act_input):
    """Returns an activation function"""
    act_func = None
    if act == "sigmoid":
        act_func = tf.nn.sigmoid(act_input)
    elif act == "tanh":
        act_func = tf.nn.tanh(act_input)

    elif act == "relu":
        act_func = tf.nn.relu(act_input)
    elif act == "elu":
        act_func = tf.nn.elu(act_input)
    elif act == "identity":
        act_func = tf.identity(act_input)
    else:
        raise NotImplementedError("ERROR")
    return act_func
