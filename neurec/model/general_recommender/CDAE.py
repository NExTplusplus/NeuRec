'''
Reference: Wu, Yao, et al. "Collaborative denoising auto-encoders for top-n recommender systems." in WSDM2016
@author: wubin
'''
from neurec.model.AbstractRecommender import AbstractRecommender

import tensorflow as tf
import numpy as np
from time import time
from neurec.util import learner, tool
from neurec.util.tool import timer
from neurec.util.tool import csr_to_user_dict
from neurec.util.tool import l2_loss
from neurec.util.DataIterator import DataIterator

class CDAE(AbstractRecommender):
    properties = [
        "hidden_neuron",
        "learning_rate",
        "learner",
        "reg",
        "epochs",
        "batch_size",
        "verbose",
        "h_act",
        "g_act",
        "corruption_level",
        "init_method",
        "stddev"
    ]

    def __init__(self, **kwds):  
        super().__init__(**kwds)
        
        self.hidden_neuron = self.conf["hidden_neuron"]
        self.learning_rate = self.conf["learning_rate"]
        self.learner = self.conf["learner"]
        self.reg = self.conf["reg"]
        self.num_epochs = self.conf["epochs"]
        self.batch_size = self.conf["batch_size"]
        self.verbose = self.conf["verbose"]
        self.h_act = self.conf["h_act"]
        self.g_act = self.conf["g_act"]
        self.corruption_level = self.conf["corruption_level"]
        self.init_method = self.conf["init_method"]
        self.stddev = self.conf["stddev"]
        self.num_users = self.dataset.num_users
        self.num_items = self.dataset.num_items 
        self.train_dict = csr_to_user_dict(self.dataset.train_matrix) 
        
        
    def _create_placeholders(self):
        with tf.name_scope("input_data"):
            self.user_input = tf.placeholder(tf.int32, shape=[None,],name = 'user_input')
            self.input_R = tf.placeholder(tf.float32, [None, self.num_items])
            self.mask_corruption = tf.placeholder(tf.float32, [None, self.num_items])
            
    def _create_variables(self):
        with tf.name_scope("embedding"):  # The embedding initialization is unknown now
            initializer = tool.get_initializer(self.init_method, self.stddev)
            self.V = tf.Variable(initializer([self.num_users, self.hidden_neuron]))
             
            self.weights = {'encoder': tf.Variable(initializer([self.num_items, self.hidden_neuron])),
                            'decoder': tf.Variable(initializer([self.hidden_neuron, self.num_items]))}
            self.biases = {'encoder': tf.Variable(initializer([self.hidden_neuron])),
                           'decoder': tf.Variable(initializer([self.num_items]))}
            
    def _create_inference(self):
        with tf.name_scope("inference"):
            
            self.user_latent = tf.nn.embedding_lookup(self.V, self.user_input)
            
            corrupted_input = tf.multiply(self.input_R, self.mask_corruption)
            encoder_op = tool.activation_function(self.h_act, \
            tf.matmul(corrupted_input, self.weights['encoder'])+self.biases['encoder']+self.user_latent)
              
            self.decoder_op = tf.matmul(encoder_op, self.weights['decoder'])+self.biases['decoder']
            self.output = tool.activation_function(self.g_act, self.decoder_op)
            
    def _create_loss(self):
        with tf.name_scope("loss"):
            
            self.loss = - tf.reduce_sum(self.input_R*tf.log(self.output) + (1 - self.input_R)*tf.log(1 - self.output))

            self.reg_loss = self.reg * l2_loss(self.weights['encoder'], self.weights['decoder'],
                                               self.biases['encoder'], self.biases['decoder'],
                                               self.user_latent)
            self.loss = self.loss + self.reg_loss
    
    def _create_optimizer(self):
        with tf.name_scope("learner"):
            self.optimizer = learner.optimizer(self.learner, self.loss, self.learning_rate) 
            
    def build_graph(self):
        self._create_placeholders()
        self._create_variables()
        self._create_inference()
        self._create_loss()
        self._create_optimizer()
                                               
    def train_model(self):
        self.logger.info(self.evaluator.metrics_info())
        for epoch in range(1, self.num_epochs+1):
            # Generate training instances
            mask_corruption_np = np.random.binomial(1, 1-self.corruption_level, (self.num_users, self.num_items))
            total_loss = 0.0
            training_start_time = time()
            all_users = np.arange(self.num_users)
            users_iter = DataIterator(all_users, batch_size=self.batch_size, shuffle=True, drop_last=False)
            for batch_set_idx in users_iter:
                batch_matrix = np.zeros((len(batch_set_idx), self.num_items))
                for idx, userid in enumerate(batch_set_idx):
                    items_by_userid = self.train_dict[userid]
                    batch_matrix[idx, items_by_userid] = 1

                feed_dict = {self.mask_corruption: mask_corruption_np[batch_set_idx, :],
                             self.input_R: batch_matrix,
                             self.user_input: batch_set_idx}
                _, loss = self.sess.run([self.optimizer, self.loss], feed_dict=feed_dict)
                total_loss += loss

            self.logger.info("[iter %d : loss : %f, time: %f]" % (epoch, total_loss/self.num_users,
                                                             time()-training_start_time))
            if epoch % self.verbose == 0:
                self.logger.info("epoch %d:\t%s" % (epoch, self.evaluate()))
    
    @timer
    def evaluate(self):
        return self.evaluator.evaluate(self)

    def predict(self, user_ids, candidate_items_userids):
        ratings = []
        mask = np.ones((1, self.num_items), dtype=np.int32)
        if candidate_items_userids is not None:
            rating_matrix = np.zeros((1,self.num_items), dtype=np.int32)
            for userid, candidate_items_userid in zip(user_ids, candidate_items_userids):
                items_by_userid = self.dataset.train_matrix[userid].indices
                for itemid in items_by_userid:
                    rating_matrix[0,itemid] = 1
                output = self.sess.run(self.output, 
                                       feed_dict={self.mask_corruption: mask,
                                                  self.input_R: rating_matrix,
                                                  self.user_input: [userid]})
                ratings.append(output[0, candidate_items_userid])
                
        else:
            rating_matrix = np.zeros((1,self.num_items), dtype=np.int32)
            allitems = np.arange(self.num_items)
            for userid in user_ids:
                items_by_userid = self.dataset.train_matrix[userid].indices
                for itemid in items_by_userid:
                    rating_matrix[0, itemid] = 1
                output = self.sess.run(self.output, 
                                       feed_dict={self.mask_corruption: mask,
                                                  self.input_R: rating_matrix,
                                                  self.user_input: [userid]})
                ratings.append(output[0, allitems])
        return ratings
