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

    def create_user_profile(self, user_docs, topics_matrix):
        user_profile = np.zeros([1,topics_matrix.shape[1]])
        for doc_id in user_docs:
            user_profile = user_profile + topics_matrix[doc_id]
        user_profile = user_profile / len(user_docs)
        return user_profile

    def get_recommendations(self, uid):
        rating_matrix = model_wrapper.get_rating_matrix()
        topics_matrix = model_wrapper.get_topics_matrix()
        users_topics_matrix = rating_matrix.dot(topics_matrix)
        user_docs = model_wrapper.get_user_docs(uid)
        user_profile = self.create_user_profile(user_docs, topics_matrix)
        similarity_array = cosine_similarity(user_profile, users_topics_matrix)
        [sorted_indices] = np.argsort(similarity_array).tolist()
        sorted_indices = sorted_indices[::-1]
        [similarity_array] = similarity_array.tolist()
        recommendations = []
        for index in sorted_indices:
            docs = model_wrapper.get_user_docs(index)
            for doc in docs:
                if doc not in user_docs:
                    recommendations.append((doc, similarity_array[index]))
            if len(recommendations) >= 50:
                    break
        return recommendations[:50]
