from . import external_service_manager as serv_manager
from multiprocessing import Process, Manager
from threading import Thread
from Helpers import db_helper, utilities as utils, LDA_methods as lda
import pdb


def fetch_http_service_data(search_query):
    # ssh connection has to be started in child process otherwise it doesn't work
    # TODO: Perform checks for correct arguments
    jobs = []
    manager = Manager()
    return_dict = manager.dict()
    API_NAMES = ['ARXIV', 'PLOS', 'SPRINGER', 'IEEE']
    for api in API_NAMES:
        p = Process(target=call_external_services, args=(search_query, api, return_dict))
        p.start()
        jobs.append(p)
    for p in jobs:
        p.join()

    print("Multithread outputing now  " + str(return_dict.values()))
    return return_dict


def call_external_services(search_query, API_NAME, return_dict):
    print('API Name:' + API_NAME)
    return_dict['results'] = ''

    if API_NAME == 'ARXIV':
        return_dict['ARXIV'] = serv_manager.get_arxiv_data(search_query)
    if API_NAME == 'SPRINGER':
        return_dict['SPRINGER'] =serv_manager.get_springer_data(search_query)
    if API_NAME == 'PLOS':
        return_dict['PLOS']= serv_manager.get_plos_data(search_query)
    if API_NAME == 'IEEE':
        return_dict['IEEE'] =  serv_manager.get_ieee_data(search_query)


def save_papers_in_db(external_paper_dicts):
    proc = []
    input_dict = {}
    input_dict['data'] = external_paper_dicts
    p = Thread(target=save_data_in_model, args=(external_paper_dicts,))
    p.start()
    proc.append(p)
    # for p in proc:
    #     p.join()



def save_data_in_model(external_paper_dicts):
    print("These are external papers: " + str(external_paper_dicts))


    # get max_doc_id
    max_doc_id = db_helper.get_max_doc_id_from_papers()
    print("Max doc_id: " + str(max_doc_id))

    # external_paper_dicts = input_dict['data']

    # for manually managing the doc id
    paper_add_count = 0

    # save the results in database
    for i, paper_dict in enumerate(external_paper_dicts):
        # check if paper does not exist in the database
        paper_model = db_helper.get_model_paper_object(paper_dict)
        if paper_model:
            # if paper does not exist
            print('Entering in db')
            doc_id = utils.get_incremented_id(max_id=max_doc_id, iteration_count=paper_add_count)
            paper_model.doc_id = doc_id
            paper_model.save()
            lda.insert_paper_to_LDA(paper_model)

            # save author data
            # transform author back to list
            author_list = paper_dict['authors'].split(',')
            author_list[0] = author_list[0][3:]

            for author in author_list:
                print('Author list: ' + str(author_list))
                author_set = db_helper.get_all_authors()

                # check if author already exists in the database
                if author_set.filter(author_name=author).exists():
                    author_model = author_set.filter(author_name=author).get()
                else:
                    author_model = db_helper.get_model_author_object(author)
                    print('Unique Etry')

                author_model.save()
                paper_model.authors.add(author_model)

            paper_add_count += 1

        else:
            print('paper exists: ' + paper_dict['paper_url'])