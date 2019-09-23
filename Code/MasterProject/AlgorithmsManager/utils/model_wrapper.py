from scipy.sparse import csr_matrix
import Helpers.db_helper as dbh
from GUIManager.models import PaperLDATheta
import GUIManager.models as m
from django.core.cache import cache
import numpy as np
import pickle
import os

def get_rating_matrix():
    rating_matrix_file_path = "rating_matrix"
    renew_rating_matrix = True
    if os.path.exists(rating_matrix_file_path):
        with open(rating_matrix_file_path, "rb") as pickle_fle:
            rating_matrix = pickle.load(pickle_fle)
            renew_rating_matrix = not rating_matrix.shape[0] == m.UserMapping.objects.count() or \
                                  not rating_matrix.shape[1] == m.Paper.objects.count()
            if not renew_rating_matrix:
                return rating_matrix
            else:
                os.remove(rating_matrix_file_path)
    if renew_rating_matrix:
        rm = m.RatingMatrix.objects.all().order_by('external_user_id', 'doc_id')
        mat = csr_matrix((m.UserMapping.objects.count(), m.Paper.objects.count())).tolil()
        for i in rm:
            # because matrix indexing start from 0
            mat[i.external_user_id, i.doc_id] = i.rating
        with open(rating_matrix_file_path, "wb") as pickle_file:
            pickle.dump(mat, pickle_file)
        return mat

def get_topics_matrix():
    """
    Returns Topics matric (LDA theta) as a numpy array
    :return: topics matrix (numpy array)
    """
    topics_matrix_file_path = "topics_matrix"
    if not os.path.exists(topics_matrix_file_path):
        rm = m.PaperLDATheta.objects.all()
        mat = np.zeros((m.Paper.objects.count(), 150))
        for i in rm:
            mat[i.doc_id, i.topic_id] = i.value
        with open(topics_matrix_file_path, "wb") as pickle_file:
            pickle.dump(mat, pickle_file)
        return mat
    else:
        with open(topics_matrix_file_path, "rb") as pickle_fle:
            topics_matrix = pickle.load(pickle_fle)
            current_docs_num = topics_matrix.shape[0]
            additional_docs_num = m.Paper.objects.count() - current_docs_num
            additional_docs = m.PaperLDATheta.objects.filter(doc_id__gte=current_docs_num)
            mat = np.zeros((additional_docs_num, 150))
            topics_matrix = np.append(topics_matrix, mat, axis=0)
            for i in additional_docs:
                topics_matrix[i.doc_id, i.topic_id] = i.value
        return topics_matrix


def get_user_docs(user_map_id):
    return dbh.get_ratings(user_map_id)