from __future__ import absolute_import, unicode_literals
from MasterProject.celery import app
from celery import chord, group
from django.core.cache import cache
from datetime import datetime
import time
from . import external_service_manager as serv_manager
from Helpers import db_helper, utilities as utils


def revoke_task(celery_task_id):
    app.control.revoke(celery_task_id, terminate=True)


def run_paper_service_in_parallel(search_query):
    """
    Run celery paper service in parallel
    :param search_query: search query for the external service
    :type search_query: str
    """
    background_task = group(
        [call_external_services.s(search_query, 'ARXIV'), call_external_services.s(search_query, 'PLOS'),
         call_external_services.s(search_query, 'SPRINGER'), call_external_services.s(search_query, 'IEEE')]).\
        apply_async(queue="PaperManagerQueue")

    # background_task = group(
    #     [call_external_services.s(search_query, 'IEEE')]). \
    #     apply_async(queue="PaperManagerQueue")

    return background_task


def save_papers_in_db(paper_dicts):
    """
    Saves the model in the database as a celery group task
    :param paper_dicts: List of parsed paper dictionaries from API
    :type paper_dicts: list
    """
    print("API Results:" + str(paper_dicts))
    background_task = group(
        [save_data_in_model.s(paper_dicts)]).apply_async(queue="PaperManagerQueue")


@app.task
def periodic_task():
    # This task is just to show how to set a periodic task. Donot use it. create your own task.
    # use it only if you need a periodic task. Check commented out part in MasterProject/celery.py

    timeout = 60 * 10
    lock_id = "Task_checker"
    # If key has already been added, this fails. This ensures mutual exclusion
    # if cache.add(lock_id, "", timeout):
    # Use this statement to call your celery task. Remember to assign task to specific queue or there will be chaos
    # background_task = chord([header_task.s(i, "abc") for i in range(3)],
    #                         callback_task.s("abcdef")).apply_async(queue="PaperManagerQueue")
    #
    # # you can use these celery task ids to revoke a task
    # celery_task_ids = []
    # celery_task_ids.append(str(background_task.task_id))
    # try:
    #     for b_task_id in background_task.parent:
    #         celery_task_ids.append(str(b_task_id))
    # except TypeError:
    #     # Not iterable if only one header task
    #     pass
    # cache.delete(lock_id)
    # else:
    #     print("*** Another Process has a lock at the moment ***")


@app.task
def callback_task(prev_returns, param1):
    # prev_returns are the values returned by the header tasks in a chord
    time.sleep(10)
    print("***************", prev_returns, "**********", param1, "*************")

@app.task
def save_data_in_model(external_paper_dicts):
    print("These are external papers: " + str(external_paper_dicts))

    # get max_doc_id
    max_doc_id = db_helper.get_max_doc_id_from_papers()

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


@app.task
def call_external_services(search_query, API_NAME):
    print('API Name:' + API_NAME)

    if API_NAME == 'ARXIV':
        return serv_manager.get_arxiv_data(search_query)
    if API_NAME == 'SPRINGER':
        return serv_manager.get_springer_data(search_query)
    if API_NAME == 'PLOS':
        return serv_manager.get_plos_data(search_query)
    if API_NAME == 'IEEE':
        return serv_manager.get_ieee_data(search_query)
