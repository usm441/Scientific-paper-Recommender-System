from sklearn.decomposition import LatentDirichletAllocation
import sklearn,re
import multiprocessing,os,time
import numpy as np
from scipy.sparse import *
from sklearn.feature_extraction.text import CountVectorizer
import GUIManager.models as model
import pickle
from django.core.cache import cache
import nltk
from nltk.stem import PorterStemmer
THRESHOLD=.08

def readMult(doc_vocab_file, with_header = False, lda_c_format = True, delimiter = ' '):
    """
    Code from Anas
    Read mult.dat and return a document-termid matrix
    """
    start = 0
    # lda-c format: first value of each row is the #vocab
    if lda_c_format:
        start = 1
    doc_vocab = []
    vocabs = set()
    with open(doc_vocab_file, 'r') as f:
        line_num = 0
        if with_header:
            next(f)
        for line in f:
            doc_vector = []
            line_split = line.strip().split(delimiter)
            for e in line_split[start:]:
                vocab, freq = e.split(":")
                try:
                    vocab = int(vocab)
                    doc_vector.append((vocab, int(freq)))
                    vocabs.add(vocab)
                except ValueError:
                    print("Error in doc_vocab file {} : line {}, value {} is not int.".format(doc_vocab_file, line_num,
                                                                                              e))
                    raise
            doc_vocab.append(doc_vector)
            line_num += 1
    if (len(vocabs) != max(vocabs) + 1):
        print("Error in doc_vocab file {}: # Vocabs = {}, max vocab = {}".format(doc_vocab_file, len(vocabs),
                                                                                 max(vocabs)))
        raise ValueError

    mat = csr_matrix((len(doc_vocab), len(vocabs))).tolil()
    doc_idx = 0
    for d in doc_vocab:
        for e in d:
            mat[doc_idx, e[0]] = e[1]
            if e[1] <= 0:
                print(e[1])
        doc_idx += 1
    return mat

def fit_lda():
    """
    Code to fit the LDA model.
    This function was executed in another server and the model file transferred to Django
    :return:
    """
    print('file reading started at ', time.ctime())

    doc_matrix = readMult('Helpers/mult.dat')
    print('file reading completed at', time.ctime())

    lda = LatentDirichletAllocation(n_components=150,
                                    max_iter=5,
                                    learning_method='online',
                                    learning_offset=50.,
                                    random_state=0,
                                    n_jobs=multiprocessing.cpu_count() - 1
                                    )
    theta_matrix = lda.fit_transform(doc_matrix)
    print('model fitted succesfully at', time.ctime())
    save_model_to_file(lda)

    return theta_matrix

def save_model_to_file(model):
    """
    saves the fitted model as a file and inserts it into the django/system cache

    :param model:
    :return:
    """
    filename='model'+time.ctime().replace(':','').replace(' ','')+'.dat'
    try:
        pickle.dump(model, open(filename, "wb"))

    except:
        print('pickling error')
    # also save the model in memory cache for easier retrieval
    cache.set('lda_model', model)
    # insert into LDATopics table


def load_model_from_file(file):
    """
    load the file from hardrive and return the corresponding fitted LDA model.
    It also resets the model saved in Djano/system cache
    :param file:
    :return:
    """
    try:
       model=pickle.load(open(file, "rb"))
       cache.set('lda_model', model)
       return model
    except:
        print('MOdel file does not exist yet')
        raise ValueError
    # also save the model in memory cache for easier retrieval



def get_paper_vocabulary(paper_obj):
    """
    extracts the terms and returns a 1x20k row
    :param paper_obj:

    :return: np.array
    """

    def my_tokenizer(input_str):
        ps = PorterStemmer()
        l = [ps.stem(s).strip() for s in re.split("[^a-zA-Z]+", input_str) ]
        return l #[s for s in l if len(s)>2 and s not in stopWords]
    content=[paper_obj.title + paper_obj.abstract]
    # get terms from memcache to pass into model

    # if cache doesnt exist
    if cache.get('terms') is None:
        # get from DB
        term_array=model.Vocabulary.objects.values_list('term',flat=True)
        # and set the cache
        cache.set('terms',term_array)
    cv=CountVectorizer(vocabulary=cache.get('terms'),tokenizer=my_tokenizer)
    vocab=cv.fit_transform(content)
    # insert into mult.dat

    return vocab

def get_LDA_topics(paper_obj):

    # load lda model if not available in cache
    if cache.get('lda_model') is None:
        model=load_model_from_file("Helpers/model.dat")
        topic_array=model.transform(get_paper_vocabulary(paper_obj))
    else:
        topic_array=cache.get('lda_model').transform(get_paper_vocabulary(paper_obj))
    # return a dictionary of topic_id and those values greater than .08
    return {i:v for i,v in enumerate(topic_array[0].tolist()) if v>THRESHOLD}


def insert_paper_to_LDA(paper_obj):
    # get the last inserted object to get doc_id
    #todo paper object will have a field called doc_id
    # todo remove if and else code
    #TODO NOte: Paper_object will have a new column doc_id
    # todo so remove doc_id from PAPERLDATHETA

    #topic_array=get_LDA_topics(paper_obj)
    for index,value in get_LDA_topics(paper_obj).items():
        model.PaperLDATheta.objects.create(paper=paper_obj,
                                           topic_id=index,
                                           value=value,
                                           doc_id=paper_obj.doc_id)

def upload_ldatopics(theta_file):
    a=[]
    index=0
    print('starting insertion')
    with open(theta_file) as f:
        for line in f:
            #paper_obj=model.PaperMapping.objects.get(doc_id=index)
            paper_dis = [float(x) for x in line.replace("\n", "").split(' ') if x != ""]
            for i, value in enumerate(paper_dis):
                model.PaperLDATheta.objects.create(paper_id=index+1,
                                                   doc_id=index,
                                                   topic_id=i,
                                                   value=value)
            index=index+1
            print('paper id {}, doc id {} inserted'.format(index+1, index))
    print('insertion completed')
    return

def get_LDA_from_db(paper_obj):
    """

    :param paper_obj:model.Paper
    :return: list
    """

    # load lda model if not available in cache
    result=paper_obj.paperldatheta_set
    topics=np.zeros(150)
    for i in result:
        topics[i.topic_id]=i.value
    return topics
