"""
@author: Zhongchuan Sun
"""
from neurec.data.utils import filter_data, remap_id, get_dataset_names
from neurec.data.utils import split_by_ratio, split_by_loo, load_data
from neurec.util import reader
from neurec.util.tool import randint_choice
import pandas as pd
import numpy as np
import os
from neurec.util.properties import Properties
import logging
from importlib import util
import logging

class Splitter():
    def __init__(self):
        dataset_path = Properties().get_property('data.input.path')
        dataset_name = Properties().get_property('data.input.dataset')
        self.filename = os.path.join(dataset_path, dataset_name)

        if (dataset_path == 'neurec'):
            neurec_path = util.find_spec('neurec', package='neurec').submodule_search_locations[0]
            self.filename = os.path.join(neurec_path, 'dataset', dataset_name)

        self.ratio = Properties().get_property("data.splitterratio")
        self.file_format = Properties().get_property("data.column.format")
        self.sep = Properties().get_property("data.convert.separator")
        self.user_min = Properties().get_property("user_min")
        self.item_min = Properties().get_property("item_min")
        self.by_time = Properties().get_property("by_time")
        self.spliter = Properties().get_property("data.splitter")
        self.test_neg = Properties().get_property("rec.evaluate.neg")
        self.logger = logging.getLogger()

    def split(self):
        if self.file_format.lower() == "uirt":
            columns = ["user", "item", "rating", "time"]
            if self.by_time is False:
                by_time = False
            else:
                by_time = True
        elif self.file_format.lower() == "uir":
            columns = ["user", "item", "rating"]
            by_time = False
        else:
            raise ValueError("There is not data format '%s'" % self.file_format)

        print("load data...")
        all_data = load_data(self.filename, self.sep, columns)
        print("filter data...")
        filtered_data = filter_data(all_data, user_min=self.user_min, item_min=self.item_min)
        print("remap id...")
        remapped_data, user2id, item2id = remap_id(filtered_data)

        user_num = len(remapped_data["user"].unique())
        item_num = len(remapped_data["item"].unique())
        rating_num = len(remapped_data["item"])
        sparsity = 1 - 1.0 * rating_num / (user_num * item_num)
        # sampling negative item for test
        if self.test_neg > 0:
            neg_items = []
            grouped_user = remapped_data.groupby(["user"])
            for user, u_data in grouped_user:
                line = [user]
                line.extend(randint_choice(item_num, size=self.test_neg, replace=False, exclusion=u_data["item"]))
                neg_items.append(line)

            neg_items = pd.DataFrame(neg_items)
        else:
            neg_items = None

        print("split data...")
        if self.spliter == "ratio":
            train_data, test_data = split_by_ratio(remapped_data, ratio=self.ratio, by_time=by_time)
        elif self.spliter == "loo":
            train_data, test_data = split_by_loo(remapped_data, by_time=by_time)
        else:
            raise ValueError("Splitter not recognised: '%s'" % self.spliter)

        print("save to file...")
        data_names = get_dataset_names()
        np.savetxt(data_names['train'], train_data, fmt='%d', delimiter=self.sep)
        np.savetxt(data_names['test'], test_data, fmt='%d', delimiter=self.sep)

        if neg_items is not None:
            np.savetxt(data_names['neg'], neg_items, fmt='%d', delimiter=self.sep)

        user2id = [[user, id] for user, id in user2id.to_dict().items()]
        item2id = [[item, id] for item, id in item2id.to_dict().items()]
        np.savetxt(data_names['user2id'], user2id, fmt='%s', delimiter=self.sep)
        np.savetxt(data_names['item2id'], item2id, fmt='%s', delimiter=self.sep)

        self.logger.info(self.filename)
        self.logger.info("The number of users: %d" % user_num)
        self.logger.info("The number of items: %d" % item_num)
        self.logger.info("The number of ratings: %d" % rating_num)
        self.logger.info("Average actions of users: %.2f" % (1.0*rating_num/user_num))
        self.logger.info("Average actions of items: %.2f" % (1.0*rating_num/item_num))
        self.logger.info("The sparsity of the dataset: %f%%" % (sparsity*100))

