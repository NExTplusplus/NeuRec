"""
@author: Zhongchuan Sun
"""
try:
    from .apt_evaluate_loo import apt_evaluate_loo
except:
    raise ImportError("Import apt_evaluate_loo error!")
from util import typeassert
import numpy as np
import os


@typeassert(score_matrix=np.ndarray, test_items=(list, np.ndarray), top_k=int)
def eval_score_matrix_loo(score_matrix, test_items, top_k=50, thread_num=None):
    if len(score_matrix) != len(test_items):
        raise ValueError("The lengths of score_matrix and test_items are not equal.")
    thread_num = (thread_num or (os.cpu_count() or 1) * 5)
    results = apt_evaluate_loo(score_matrix, test_items, top_k, thread_num)
    return results
