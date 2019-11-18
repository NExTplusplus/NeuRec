"""
Reference: Steffen Rendle et al., "BPR: Bayesian Personalized Ranking from Implicit Feedback." in UAI 2009.
    GMF: Xiangnan He et al., "Neural Collaborative Filtering." in WWW 2017.
@author: wubin
"""
import tensorflow as tf
import numpy as np
from time import time
from neurec.util import learner, DataGenerator, tool
from neurec.model.AbstractRecommender import AbstractRecommender
from neurec.util.DataIterator import DataIterator
from neurec.util.tool import timer
from neurec.util.tool import l2_loss

class MF(AbstractRecommender):
    properties = [
        "learning_rate",
        "embedding_size",
        "learner",
        "loss_function",
        "is_pairwise",
        "topk",
        "epochs",
        "reg_mf",
        "batch_size",
        "verbose",
        "num_negatives",
        "init_method",
        "stddev"
    ]

    def __init__(self, **kwds):
        super().__init__(**kwds)
        
        self.learning_rate = self.conf["learning_rate"]
        self.embedding_size = self.conf["embedding_size"]
        self.learner = self.conf["learner"]
        self.loss_function = self.conf["loss_function"]
        self.is_pairwise = self.conf["is_pairwise"]
        self.topK = self.conf["topk"]
        self.num_epochs = self.conf["epochs"]
        self.reg_mf = self.conf["reg_mf"]
        self.batch_size = self.conf["batch_size"]
        self.verbose = self.conf["verbose"]
        self.num_negatives = self.conf["num_negatives"]
        self.init_method = self.conf["init_method"]
        self.stddev = self.conf["stddev"]
        
        self.num_users = self.dataset.num_users
        self.num_items = self.dataset.num_items
        
    
    def _create_placeholders(self):
        with tf.name_scope("input_data"):
            self.user_input = tf.placeholder(tf.int32, shape=[None], name="user_input")
            self.item_input = tf.placeholder(tf.int32, shape=[None], name="item_input")
            if self.is_pairwise == True:
                self.item_input_neg = tf.placeholder(tf.int32, shape=[None], name="item_input_neg")
            else:
                self.labels = tf.placeholder(tf.float32, shape=[None], name="labels")

    def _create_variables(self):
        with tf.name_scope("embedding"):
            initializer = tool.get_initializer(self.init_method, self.stddev)
            
            self.user_embeddings = tf.Variable(initializer([self.num_users, self.embedding_size]), 
                                               name='user_embeddings', dtype=tf.float32)  # (users, embedding_size)
            self.item_embeddings = tf.Variable(initializer([self.num_items, self.embedding_size]),
                                               name='item_embeddings', dtype=tf.float32)  # (items, embedding_size)

    def _create_inference(self, item_input):
        with tf.name_scope("inference"):
            # embedding look up
            user_embedding = tf.nn.embedding_lookup(self.user_embeddings, self.user_input)
            item_embedding = tf.nn.embedding_lookup(self.item_embeddings, item_input)
            predict = tf.reduce_sum(tf.multiply(user_embedding, item_embedding),1)
            return user_embedding, item_embedding, predict

    def _create_loss(self):
        with tf.name_scope("loss"):
            # loss for L(Theta)
            p1, q1,self.output = self._create_inference(self.item_input)
            if self.is_pairwise == True:
                _, q2, self.output_neg = self._create_inference(self.item_input_neg)
                result = self.output - self.output_neg
                self.loss = learner.pairwise_loss(self.loss_function, result) + self.reg_mf*l2_loss(p1, q2, q1)
            else:
                self.loss = learner.pointwise_loss(self.loss_function, self.labels,self.output) + \
                            self.reg_mf * l2_loss(p1, q1)

    def _create_optimizer(self):
        with tf.name_scope("learner"):
            self.optimizer = learner.optimizer(self.learner, self.loss, self.learning_rate)
    
    def build_graph(self):
        self._create_placeholders()
        self._create_variables()
        self._create_loss()
        self._create_optimizer()
        
    # ---------- training process -------
    def train_model(self):
        self.logger.info(self.evaluator.metrics_info())
        for epoch in range(1,self.num_epochs+1):
            # Generate training instances
            if self.is_pairwise == True:
                user_input, item_input_pos, item_input_neg = DataGenerator._get_pairwise_all_data(self.dataset)
                data_iter = DataIterator(user_input, item_input_pos, item_input_neg,
                                         batch_size=self.batch_size, shuffle=True)
            else:
                user_input, item_input, labels = DataGenerator._get_pointwise_all_data(self.dataset, self.num_negatives)
                data_iter = DataIterator(user_input, item_input, labels,
                                         batch_size=self.batch_size, shuffle=True)
            
            total_loss = 0.0
            training_start_time = time()

            if self.is_pairwise == True:
                for bat_users, bat_items_pos, bat_items_neg in data_iter:
                    feed_dict = {self.user_input: bat_users,
                                 self.item_input: bat_items_pos,
                                 self.item_input_neg: bat_items_neg}
                    loss, _ = self.sess.run((self.loss, self.optimizer), feed_dict=feed_dict)
                    total_loss += loss
            else:
                for bat_users, bat_items, bat_labels in data_iter:
                    feed_dict = {self.user_input: bat_users,
                                 self.item_input: bat_items,
                                 self.labels: bat_labels}
                    loss, _ = self.sess.run((self.loss, self.optimizer), feed_dict=feed_dict)
                    total_loss += loss
            self.logger.info("[iter %d : loss : %f, time: %f]" % (epoch, total_loss/len(user_input),
                                                             time()-training_start_time))
            if epoch % self.verbose == 0:
                self.logger.info("epoch %d:\t%s" % (epoch, self.evaluate()))
        
        # params = self.sess.run([self.user_embeddings, self.item_embeddings])
        # with open("pretrained/%s_epochs=%d_embedding=%d_MF.pkl" % (self.dataset.dataset_name, self.num_epochs,self.embedding_size), "wb") as fout:
        #         pickle.dump(params, fout)
    
    @timer
    def evaluate(self):
        self._cur_user_embeddings, self._cur_item_embeddings = self.sess.run([self.user_embeddings, self.item_embeddings])
        return self.evaluator.evaluate(self)

    def predict(self, user_ids, candidate_items_userids):
        if candidate_items_userids is None:
            user_embed = self._cur_user_embeddings[user_ids]
            ratings = np.matmul(user_embed, self._cur_item_embeddings.T)
        else:
            ratings = []
            for userid, items_by_userid in zip(user_ids, candidate_items_userids):
                user_embed = self._cur_user_embeddings[userid]
                items_embed = self._cur_item_embeddings[items_by_userid]
                ratings.append(np.squeeze(np.matmul(user_embed, items_embed.T)))
            
        return ratings
