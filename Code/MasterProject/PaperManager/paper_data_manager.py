from fuzzywuzzy import process
from . import paper_background_tasks as bg_task
from . import external_service_manager as serv_man
from Helpers import db_helper, paper_utilities as pap_utils
from UserManager.user_manager import UserManager
from django.core.cache import cache
import pdb
import re

class PaperDataManager:

    def __init__(self):
        pass

    @staticmethod
    def get_instance():
        #
        return PaperDataManager()

    # def serialize_api_response(self, response_dict):



    def serialize_db_paper_into_dict(self, db_paper, in_catalog):
        """
        Serializes the paper retrieved from database in to Dictionary object
        :param db_paper: Paper object of model
        :type db_paper:
        :return: paper meta data object
        :rtype: PaperMetaData
        """

        authors = pap_utils.get_authors_from_queryset(list(db_paper.authors.all()))

        display_title = re.sub("\d+", "", db_paper.title)

        serialized_paper = pap_utils.get_serialized_dict(url=db_paper.url, display_title=display_title, title=db_paper.title, abstract=db_paper.abstract,
                                                            journal_name=db_paper.journal_name,
                                                            published_date=db_paper.published_date,
                                                            authors=authors, in_catalog=in_catalog)
        return serialized_paper


    def get_paper_dicts_for_query(self, search_query,
                                  response_dicts):
        """
        Gets the paper dictionary for the searched query, from list of dictionaries
        :param search_query: query to be searched
        :type search_query:
        :param response_dicts:
        :type response_dicts:
        :return:
        :rtype:
        """

        def get_paper_dict_from_title(title):
            for paper_dict in response_dicts:
                if paper_dict['title'] == title:
                    return paper_dict

        # get titles from parsed dictionaries
        titles_list = [paper['title'] for paper in response_dicts]

        # gets the mathced title with search query from fuzzywuzzy
        titles_matches = self.get_title_matches(search_query, titles_list)

        # gets dictionary objects for matched titles
        serialized_papers = [get_paper_dict_from_title(title) for title in titles_matches]
        return serialized_papers


    def get_papers_for_query_from_db(self, user_id, search_query):
        """
        Searches paper for the search query returns the result set
        :param search_query: query on the title
        :type search_query: String
        """
        def get_paper_dict_from_title(title):
            db_paper = db_helper.get_paper_with_title(title)
            user_manager = UserManager()
            in_user_catalog = user_manager.does_paper_exist_in_user_catalog(paper=db_paper, user_id=user_id)
            paper_dict = self.serialize_db_paper_into_dict(db_paper, in_user_catalog)
            return paper_dict

        # paper_titles = db_helper.get_field_from_paper('title')
        paper_titles = db_helper.get_title_like(search_query)
        title_matches = self.get_title_matches(search_query, paper_titles)
        paper_dicts = [get_paper_dict_from_title(title) for title in title_matches]

        # cache the search dictionaries
        cache.set('searched_paper_dicts', paper_dicts)

        return paper_dicts

    def get_title_matches(self, query, titles):
        """
        Gets title matches from fuzzywuzzy for the given list
        :param query: search query
        :type query: str
        :param titles: list of titlles on which to search
        :type titles: list
        :return: partial or exact match
        :rtype: list
        """
        exact_title_matches = []
        partial_title_matches = []
        results = process.extractBests(query, titles, limit=10)

        for result in results:
            if result[1] == 100:
                exact_title_matches.append(result[0])
            elif result[1] > 80:
                partial_title_matches.append(result[0])

        if len(exact_title_matches):
            # if there is exact match, return that result
            return exact_title_matches

        # else return partial matches
        return partial_title_matches

    def parse_api_responses(self, api_results):
        """
        Parses API response retrieved from hitting different API services
        and returns list of parsed paper meta data objects
        :param api_results: list of all API results
        :type api_results: list
        :return: list of parsed objects
        :rtype: list
        """
        external_papers = []
        for api_result in api_results:
            if api_result[1] == 'ARXIV':
                external_papers += serv_man.parse_arxiv_response(api_result[0])
            if api_result[1] == 'SPRINGER':
                external_papers += serv_man.parse_springer_data(api_result[0])
            if api_result[1] == 'PLOS':
                external_papers += serv_man.parse_plos_response(api_result[0])
            if api_result[1] == 'IEEE':
                external_papers += serv_man.parse_ieee_response(api_result[0])

        return external_papers

    def remove_common_list_elements(self, filtered_api_responses, cached_responses):
        if not cached_responses:
            return filtered_api_responses
        for api_response in filtered_api_responses[:]:
            for cached_response in cached_responses:
                if api_response['title'] == cached_response['title']:
                    filtered_api_responses.remove(api_response)

        return filtered_api_responses

    def get_papers_from_external_sources(self, search_query):
        """
        Fetches paper from external sources and filters the result based on the query
        :param search_query: the query to be search papers on
        :type search_query: basestring
        :return: list of filtered papers
        :rtype: list
        """

        # fetch papers from service calls in parallel
        api_results = bg_task.fetch_external_papers_in_parallel(search_query)

        # parse API response for the search
        external_paper_dicts = self.parse_api_responses(api_results)

        # save API response in database in background
        bg_task.save_external_papers_in_db_in_bg(external_paper_dicts)



        # get papers for the search query in
        filtered_papers = self.get_paper_dicts_for_query(search_query, external_paper_dicts)

        local_searched_papers = cache.get('searched_paper_dicts')

        # remove papers already stored in cache
        filtered_papers = self.remove_common_list_elements(filtered_papers, local_searched_papers)

        return filtered_papers