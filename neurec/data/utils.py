"""
@author: Zhongchuan Sun
"""
import pandas as pd
import math
import os
from neurec.util.properties import Properties

def get_dataset_names():
    """Returns dict with training and testing filename for the dataset."""
    dataset_name = Properties().get_property("data.input.dataset")

    os.makedirs(dataset_name, exist_ok=True)

    file_prefix = "%s_%s_u%d_i%d" % (dataset_name,
                                     Properties().get_property("data.splitter"),
                                     Properties().get_property("user_min"),
                                     Properties().get_property("item_min"))
    file_path = os.path.join('./', dataset_name, file_prefix)

    paths = ({'train': file_path + '.train',
             'test': file_path + '.test',
             'neg': file_path + '.neg',
             'user2id': file_path + '.user2id',
             'item2id': file_path + '.item2id'})
    print(paths)
    return paths

def load_data(filename, sep, columns):
    data = pd.read_csv(filename, sep=sep, header=None, names=columns)
    return data


def filter_data(data, user_min=None, item_min=None):
    data.dropna(how="any", inplace=True)
    if item_min is not None and item_min > 0:
        item_count = data["item"].value_counts(sort=False)
        filtered_idx = data["item"].map(lambda x: item_count[x] >= item_min)
        data = data[filtered_idx]

    if user_min is not None and user_min > 0:
        user_count = data["user"].value_counts(sort=False)
        filtered_idx = data["user"].map(lambda x: user_count[x] >= user_min)
        data = data[filtered_idx]
    return data


def remap_id(data):
    unique_user = data["user"].unique()
    user2id = pd.Series(data=range(len(unique_user)), index=unique_user)
    data["user"] = data["user"].map(user2id)

    unique_item = data["item"].unique()
    item2id = pd.Series(data=range(len(unique_item)), index=unique_item)
    data["item"] = data["item"].map(item2id)

    return data, user2id, item2id


def split_by_ratio(data, ratio=0.8, by_time=True):
    if by_time:
        data.sort_values(by=["user", "time"], inplace=True)
    else:
        data.sort_values(by=["user", "item"], inplace=True)

    first_section = []
    second_section = []
    user_grouped = data.groupby(by=["user"])
    for user, u_data in user_grouped:
        u_data_len = len(u_data)
        if not by_time:
            u_data = u_data.sample(frac=1)
        data_amount = ratio * u_data_len
        idx = math.ceil(data_amount)
        first_section.append(u_data.iloc[:idx])
        second_section.append(u_data.iloc[idx:])

    first_section = pd.concat(first_section, ignore_index=True)
    second_section = pd.concat(second_section, ignore_index=True)

    return first_section, second_section


def split_by_loo(data, by_time=True):
    if by_time:
        data.sort_values(by=["user", "time"], inplace=True)
    else:
        data.sort_values(by=["user", "item"], inplace=True)

    first_section = []
    second_section = []
    user_grouped = data.groupby(by=["user"])
    for user, u_data in user_grouped:
        u_data_len = len(u_data)
        if u_data_len <= 3:
            first_section.append(u_data)
        else:
            if not by_time:
                u_data = u_data.sample(frac=1)
            first_section.append(u_data.iloc[:-1])
            second_section.append(u_data.iloc[-1:])

    first_section = pd.concat(first_section, ignore_index=True)
    second_section = pd.concat(second_section, ignore_index=True)

    return first_section, second_section
