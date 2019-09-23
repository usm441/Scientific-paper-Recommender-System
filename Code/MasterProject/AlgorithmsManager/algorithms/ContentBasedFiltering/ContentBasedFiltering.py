import model_wrapper
from ialgorithms import IAlgorithmInterface
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class Script(IAlgorithmInterface):
    val = None

    def __init__(self):
        pass

    def fit(self):
        pass

    def get_masking_dict(self, total_docs_without_user_docs, user_docs):
        masking_dict = dict()
        actual_index = total_docs_without_user_docs + len(user_docs) - 1
        for i in reversed(range(total_docs_without_user_docs)):
            while actual_index in user_docs:
                actual_index -= 1
            masking_dict[i] = actual_index
            actual_index -= 1
        return masking_dict

    def create_user_profile(self, user_docs, topics_matrix):
        user_profile = np.zeros([1,topics_matrix.shape[1]])
        for doc_id in user_docs:
            user_profile = user_profile + topics_matrix[doc_id]
        user_profile = user_profile / len(user_docs)
        topics_matrix_without_user_rows = np.delete(topics_matrix, user_docs, axis=0)
        return user_profile, topics_matrix_without_user_rows

    def get_recommendations(self, uid):
        topics_matrix = model_wrapper.get_topics_matrix()
        user_docs = model_wrapper.get_user_docs(uid)
        user_profile, rest_docs = self.create_user_profile(user_docs, topics_matrix)
        similarity_array = cosine_similarity(user_profile, rest_docs)
        [sorted_indices] = np.argsort(similarity_array).tolist()
        masking_dict = self.get_masking_dict(similarity_array.shape[1], user_docs)
        [similarity_array] = similarity_array.tolist()
        id_score_list =  [(masking_dict[i], similarity_array[i]) for i in sorted_indices]
        return id_score_list[::-1][:50]
