"""Handles building model classes"""
from abc import ABC, abstractmethod
import logging
from neurec.data.dataset import Dataset
from neurec.util.properties import Properties

class AbstractRecommender(ABC):
    """Abstract class for building a Recommender class."""
    @property
    @abstractmethod
    def properties(self):
        """List of properties used by the model"""

    def __init__(self, sess):
        """Sets up the model with properties, dataset, and session."""
        self.logger = logging.getLogger(__name__)
        self.conf = Properties().get_properties(self.properties)
        self.dataset = Dataset()
        self.sess = sess

        self.logger.info("Arguments: %s", self.conf)

    @abstractmethod
    def build_graph(self):
        """Sets up the model's network"""

    @abstractmethod
    def train_model(self):
        """Trains the model's network"""

    @abstractmethod
    def predict(self):
        """Performs a prediction task on the model"""

class SeqAbstractRecommender(AbstractRecommender):
    def __init__(self, **kwds):
        if Dataset().time_matrix is None:
            raise ValueError("Dataset does not contant time infomation!")
        super().__init__(**kwds)

class SocialAbstractRecommender(AbstractRecommender):
    def __init__(self, **kwds):
        super().__init__(**kwds)

        social_users = reader.load_social_file(self.conf["social_file"], Properties().getProperty('data.convert.separator'), header=None, names=['user', 'friend'])

        users_key = np.array(list(self.dataset.userids.keys()))
        index = np.in1d(social_users["user"], users_key)
        social_users = social_users[index]

        index = np.in1d(social_users["friend"], users_key)
        social_users = social_users[index]

        user = social_users["user"]
        user_id = [self.dataset.userids[u] for u in user]
        friend = social_users["friend"]
        friend_id = [self.dataset.userids[u] for u in friend]
        num_users, num_items = self.dataset.train_matrix.shape
        self.social_matrix = sp.csr_matrix(([1] * len(user_id), (user_id, friend_id)),
                                           shape=(num_users, num_users))
