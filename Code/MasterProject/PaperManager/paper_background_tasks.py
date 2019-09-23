from . import paper_data_manager as pd
from . import celery_tasks
from . import multiprocessor
import pdb



def fetch_external_papers_in_parallel(search_query):
    """
    Invokes the method to fetch papers from APIS in parallel
    as a background task
    :param search_query: query to be searched for
    :type search_query: str
    """
    # api_results_dict = multiprocessor.fetch_http_service_data(search_query)
    # result_list = api_results_dict.values()
    # result_list = list(filter(None, result_list))
    # return result_list

    # celery tasks
    background_task = celery_tasks.run_paper_service_in_parallel(search_query)
    while not background_task.ready():
        print('Waiting for result')

    print('Result received')
    return background_task.get()


def save_external_papers_in_db_in_bg(paper_dicts):
    """
    Invokes the celery task method to save the papers in background
    :param paper_dicts: List of parsed dictionaries from API
    :type paper_dicts: list
    """
    # multiprocessor.save_papers_in_db(paper_dicts)
    celery_tasks.save_papers_in_db(paper_dicts)