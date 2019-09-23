from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import  LatentDirichletAllocation
import scipy
from time import time
import GUIManager.models as model
from django.db.models.functions import Concat
MAX_DF=.95
MIN_DF=.01
VOCAB_SIZE=200
LDA_TOPICS=50


def get_document():
    list=model.Paper.objects.annotate(words=Concat('title', 'abstract'))\
                            .all().values_list('id', 'words')
    return [doc[1] for doc in sorted(list,key=lambda x:x[0])]


def get_tf_matrix(document_list):
    tf_vectorizer = CountVectorizer(max_df=MAX_DF, min_df=MIN_DF,
                                    max_features=VOCAB_SIZE,
                                    token_pattern= r"(?u)\b\w\w\w+\b",
                                    analyzer='word',
                                    stop_words='english')
    tf = tf_vectorizer.fit_transform(document_list)
    return tf

def build_lda_model():
    tf_matrix=get_tf_matrix(get_document())
    lda = LatentDirichletAllocation(n_components=LDA_TOPICS, max_iter=5,
                                    learning_method='online',
                                    learning_offset=50.,
                                    random_state=0)
    return lda.fit(tf_matrix)
