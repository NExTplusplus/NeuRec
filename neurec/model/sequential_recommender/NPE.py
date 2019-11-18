'''
Reference: ThaiBinh Nguyen, et al. "NPE: Neural Personalized Embedding for Collaborative Filtering" in ijcai2018
@author: wubin
'''
from neurec.model.AbstractRecommender import SeqAbstractRecommender
import tensorflow as tf
import numpy as np
from time import time
from neurec.util import learner, DataGenerator, tool

from neurec.util.DataIterator import DataIterator
from neurec.util.tool import csr_to_user_dict_bytime
from neurec.util.tool import timer
from neurec.util.tool import l2_loss


class NPE(SeqAbstractRecommender):
    properties = [
        "learning_rate",
        "embedding_size",
        "learner",
        "loss_function",
        "epochs",
        "reg",
        "batch_size",
        "high_order",
        "verbose",
        "num_neg",
        "init_method",
        "stddev"
    ]

    def __init__(self, **kwds):  
        super().__init__(**kwds)
        
        self.learning_rate = self.conf["learning_rate"]
        self.embedding_size = self.conf["embedding_size"]
        self.learner = self.conf["learner"]
        self.loss_function = self.conf["loss_function"]
        self.num_epochs = self.conf["epochs"]
        self.reg = self.conf["reg"]
        self.batch_size = self.conf["batch_size"]
        self.high_order = self.conf["high_order"]
        self.verbose = self.conf["verbose"]
        self.num_negatives = self.conf["num_neg"]
        self.init_method = self.conf["init_method"]
        self.stddev = self.conf["stddev"]
        self.num_users = self.dataset.num_users
        self.num_items = self.dataset.num_items
        
        self.train_dict = csr_to_user_dict_bytime(self.dataset.time_matrix, self.dataset.train_matrix)
        

    def _create_placeholders(self):
        with tf.name_scope("input_data"):
            self.user_input = tf.placeholder(tf.int32, shape = [None,], name = "user_input")
            self.item_input = tf.placeholder(tf.int32, shape = [None,], name = "item_input")
            self.item_input_recent = tf.placeholder(tf.int32, shape = [None,None], name = "item_input_recent")
            self.labels = tf.placeholder(tf.float32, shape=[None,],name="labels")

    def _create_variables(self):
        with tf.name_scope("embedding"):
            initializer = tool.get_initializer(self.init_method, self.stddev)
            self.embeddings_UI = tf.Variable(initializer([self.num_users, self.embedding_size]),
                name='embeddings_UI', dtype=tf.float32)  #(users, embedding_size)
            self.embeddings_IU = tf.Variable(initializer([self.num_items, self.embedding_size]),
                name='embeddings_IU', dtype=tf.float32)  #(items, embedding_size)
            self.embeddings_IL = tf.Variable(initializer([self.num_items, self.embedding_size]),
                name='embeddings_IL', dtype=tf.float32) 

    def _create_inference(self):
        with tf.name_scope("inference"):
            # embedding look up
            embeddings_UI_u = tf.nn.embedding_lookup(self.embeddings_UI, self.user_input)
            embeddings_IU_i = tf.nn.embedding_lookup(self.embeddings_IU,self.item_input)
            embeddings_LI_l = tf.nn.embedding_lookup(self.embeddings_IL, self.item_input_recent)
            
            context_embedding = tf.reduce_sum(embeddings_LI_l,1)
            predict_vector = tf.multiply(tf.nn.relu(embeddings_UI_u), tf.nn.relu(embeddings_IU_i))\
               +tf.multiply(tf.nn.relu(embeddings_IU_i),tf.nn.relu(context_embedding))
            predict = tf.reduce_sum(predict_vector,1)
            return embeddings_UI_u,embeddings_IU_i,embeddings_LI_l, predict

    def _create_loss(self):
        with tf.name_scope("loss"):
            UI_u,IU_i,LI_l,self.output = self._create_inference()
            self.loss = learner.pointwise_loss(self.loss_function,self.labels,self.output) + \
                        self.reg * l2_loss(UI_u, IU_i, LI_l)

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
        for epoch in range(1, self.num_epochs+1):
            user_input, item_input, item_input_recents, labels = \
                DataGenerator._get_pointwise_all_highorder_data(self.dataset, self.high_order, self.num_negatives, self.train_dict)
            
            data_iter = DataIterator(user_input, item_input, item_input_recents, labels,
                                     batch_size=self.batch_size, shuffle=True)
           
            num_training_instances = len(user_input)
            total_loss = 0.0
            training_start_time = time()

            for bat_users, bat_items, bat_items_recent, bat_labels in data_iter:
                    
                    feed_dict = {self.user_input: bat_users,
                                 self.item_input: bat_items,
                                 self.item_input_recent: bat_items_recent,
                                 self.labels: bat_labels}
    
                    loss,_ = self.sess.run((self.loss,self.optimizer),feed_dict=feed_dict)
                    total_loss+=loss
                
            self.logger.info("[iter %d : loss : %f, time: %f]" % (epoch, total_loss/num_training_instances,
                                                             time()-training_start_time))
            
            if epoch % self.verbose == 0:
                self.logger.info("epoch %d:\t%s" % (epoch, self.evaluate()))

    @timer
    def evaluate(self):
        return self.evaluator.evaluate(self)
                
    def predict(self, user_ids, candidate_items_userids):
        ratings = []
        if candidate_items_userids is None:
            allitems = np.arange(self.num_items)
            for userid in user_ids:
                cand_items = self.train_dict[userid]
                item_recent = []
    
                for _ in range(self.num_items):
                    item_recent.append(cand_items[len(cand_items)-self.high_order:])
                users = np.full(self.num_items, userid, dtype=np.int32)
                feed_dict = {self.user_input: users,
                             self.item_input_recent: item_recent,
                             self.item_input: allitems}
                ratings.append(self.sess.run(self.output, feed_dict=feed_dict))  
        
        else:
            for userid, items_by_userid in zip(user_ids, candidate_items_userids):
                cand_items = self.train_dict[userid]
                item_recent = []
    
                for _ in range(len(items_by_userid)):
                    item_recent.append(cand_items[len(cand_items)-self.high_order:])
                users = np.full(len(items_by_userid), userid, dtype=np.int32)
                feed_dict = {self.user_input: users,
                             self.item_input_recent: item_recent,
                             self.item_input: items_by_userid}
                ratings.append(self.sess.run(self.output, feed_dict=feed_dict))
        return ratings
