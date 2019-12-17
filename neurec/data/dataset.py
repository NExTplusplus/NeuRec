"""
Created on Aug 8, 2016
Processing datasets.
@author: Xiangnan He (xiangnanhe@gmail.com)
"""
import os
import pandas as pd
from scipy.sparse import csr_matrix
from neurec.data.DataSplitter import Splitter
from neurec.data.utils import get_dataset_names
from neurec.util.properties import Properties
from neurec.util.singleton import Singleton
import logging

class Dataset(metaclass=Singleton):
    def __init__(self):
        self.train_matrix = None
        self.test_matrix = None
        self.time_matrix = None
        self.negative_matrix = None
        self.userids = None
        self.itemids = None
        self.num_users = None
        self.num_items = None
        self.dataset_name = Properties().get_property('data.input.dataset')
        self.is_ready = False

    def _split_data(self):
        splitter = Splitter()
        splitter.split()

    def load_data(self):
        data_names = get_dataset_names()

        if (not os.path.isfile(data_names['train']) or not
           os.path.isfile(data_names['test'])):
            self._split_data()

        file_format = Properties().get_property("data.column.format")
        sep = Properties().get_property("data.convert.separator")

        if file_format == "UIRT":
            columns = ["user", "item", "rating", "time"]
        elif file_format == "UIR":
            columns = ["user", "item", "rating"]
        elif file_format == "UI":
            columns = ["user", "item"]
        else:
            raise ValueError("There is not data format '%s'" % file_format)

        train_data = pd.read_csv(data_names['train'], sep=sep, header=None, names=columns)
        test_data = pd.read_csv(data_names['test'], sep=sep, header=None, names=columns)

        all_data = pd.concat([train_data, test_data])

        self.num_users = len(all_data["user"].unique())
        self.num_items = len(all_data["item"].unique())
        self.num_ratings = len(all_data)

        user_map = pd.read_csv(data_names['user2id'], sep=sep, header=None, names=["user", "id"])
        item_map = pd.read_csv(data_names['item2id'], sep=sep, header=None, names=["item", "id"])
        self.userids = {user: uid for user, uid in zip(user_map["user"], user_map["id"])}
        self.itemids = {item: iid for item, iid in zip(item_map["item"], item_map["id"])}

        if file_format == "UI":
            self.train_matrix = csr_matrix(([1.0]*len(train_data["user"]), (train_data["user"], train_data["item"])),
                                           shape=(self.num_users, self.num_items))
            self.test_matrix = csr_matrix(([1.0]*test_data["user"], (test_data["user"], test_data["item"])),
                                          shape=(self.num_users, self.num_items))
        else:
            self.train_matrix = csr_matrix((train_data["rating"], (train_data["user"], train_data["item"])),
                                           shape=(self.num_users, self.num_items))
            self.test_matrix = csr_matrix((test_data["rating"], (test_data["user"], test_data["item"])),
                                          shape=(self.num_users, self.num_items))
        if file_format == "UIRT":
            self.time_matrix = csr_matrix((train_data["time"], (train_data["user"], train_data["item"])),
                                          shape=(self.num_users, self.num_items))

        if os.path.isfile(data_names['neg']) and Properties().get_property("rec.evaluate.neg") > 0:
            user_list, item_list = [], []
            neg_items = pd.read_csv(data_names['neg'], sep=sep, header=None)
            for line in neg_items.values:
                user_list.extend([line[0]]*(len(line)-1))
                item_list.extend(line[1:])
            self.negative_matrix = csr_matrix(([1]*len(user_list), (user_list, item_list)),
                                              shape=(self.num_users, self.num_items))

        self.is_ready = True

    def __str__(self):
        num_users, num_items = self.num_users, self.num_items
        num_ratings = self.train_matrix.nnz+self.test_matrix.nnz

        data_info = "\n\nDataset statistics:\nusers:\t%d\nitems:\t%d\nsparsity:%.4f%%" % \
                    (num_users, num_items, (1-num_ratings/(num_items*num_users))*100)
        return data_info

    def __repr__(self):
        return self.__str__()
