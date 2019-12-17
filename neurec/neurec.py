"""Sets up NeuRec and runs the models"""
import logging
import numpy as np
import tensorflow as tf
from neurec.data.dataset import Dataset
from neurec.data.models import MODELS
from neurec.data.properties import TYPES
from neurec.util import tool
from neurec.util.properties import Properties

def setup(properties_path, properties_section="DEFAULT", numpy_seed=2018, tensorflow_seed=2017):
    """Setups initial values for neurec.

    properties_path -- path to properties file
    properties_section -- section inside the properties files to read (default "DEFAULT")
    numpy_seed -- seed value for numpy random (default 2018)
    tensorflow_seed -- seed value for tensorflow random (default 2017)
    """
    np.random.seed(numpy_seed)
    tf.set_random_seed(tensorflow_seed)

    Properties().set_section(properties_section)
    Properties().set_properties(properties_path)

    gpu = Properties().get_property("gpu_id")

    if tool.get_available_gpus(gpu):
        os.environ["CUDA_VISIBLE_DEVICES"] = gpu

    Dataset().load_data()

def setup_logging():
    """Sets up logging and handlers"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler('neurec.log', mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def run():
    """Trains and evaluates a model."""
    logger = logging.getLogger(__name__)

    recommender = Properties().get_property("recommender")

    if not recommender in MODELS:
        raise KeyError("Recommender " + str(recommender) \
                + " not recognised. Add recommender to neurec.util.models")

    gpu_memory = Properties().get_property("gpu_mem")
    gpu_options = tf.GPUOptions(allow_growth=True,
                                per_process_gpu_memory_fraction=gpu_memory)
    config = tf.ConfigProto(gpu_options=gpu_options)

    with tf.Session(config=config) as sess:
        model = MODELS[recommender](sess=sess)
        model.build_graph()
        sess.run(tf.global_variables_initializer())
        model.train_model()

def list_models():
    """Returns a list of available models."""
    return MODELS

def list_properties(model):
    """Returns a list of properties used by the model.

    name -- name of a model
    """
    model_properties = MODELS[model].properties
    properties_list = []

    for model_property in model_properties:
        properties_list.append({
            "name": model_property,
            "type": TYPES[model_property].__name__
        })

    return properties_list

setup_logging()
