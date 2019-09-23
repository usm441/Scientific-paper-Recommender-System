import requests
from Helpers.http_request_helper import get_request_from_url
from xml.etree import ElementTree as ET
from Helpers import utilities as utils, paper_utilities as pap_utils
import json
from datetime import datetime

urls = dict(DBLP='http://dblp.org/search/publ/api',
                ARXIV='http://export.arxiv.org/api/query',
                SPRINGER='http://api.springer.com/metadata/json',
                PLOS='http://api.plos.org/search',
                IEEE='http://ieeexploreapi.ieee.org/api/v1/search/articles')


def is_response_a_error(response):
    """
    Checks if the response returned is a string or not
    :param response: The HTTP response returned
    """
    if isinstance(response, requests.exceptions.HTTPError):
        return True
    return False


def extract_data_from_api(api_name, params):
    """
    A generic method for extracting data from the APIS
    :param api_name: name of the API
    :type api_name: String
    :param params: Parameters to be appended with the request
    :type params: Dictionary
    :return: response from the HTTP request
    :rtype: String
    """
    request = get_request_from_url(urls[api_name], params)
    if is_response_a_error(request):
        # request is unsuccessfull
        print('olaaala')
        raise Exception(request)
    else:
        return request.text #request successful

#IEEE data methods
def get_ieee_data(query):
    """
    Gets XML repsonse from API name ARXIV
    :param query: the query string
    :type query: String
    """

    api_key = 'cpfx7n6mg4xc5zc3pd5983pc'
    format = 'json'
    max_records = '10'
    start_record = '1'
    sort_order = 'asc'
    sort_field = 'author'
    article_title = query

    params = dict(apikey=api_key,
                  format=format,
                  max_records=max_records,
                  start_record=start_record,
                  sort_order=sort_order,
                  sort_field=sort_field,
                  article_title=article_title)
    response = extract_data_from_api('IEEE', params)
    return (response, 'IEEE')

def parse_ieee_response(response):
    if not isinstance(response, str):
        response = response.decode('utf-8')
    json_response = json.loads(response)
    articles = json_response['articles']

    ieee_data_list = []

    for article in articles:
        url = utils.check_json_key_for_none(article, 'pdf_url')
        title = utils.check_json_key_for_none(article, 'title')
        abstract = utils.check_json_key_for_none(article, 'abstract')
        journal_name = utils.check_json_key_for_none(article, 'publisher')
        # published_date = utils.check_json_key_for_none(article, 'publication_date')
        #
        # if published_date:
        #     published_date = published_date
        #     datetime_object = datetime.strptime('Jun 1 2005  12:00AM', '%b %d %Y %I:%M%p')



        authors = [author['full_name'] for author in utils.check_json_key_for_none(article['authors'], 'authors')]

        authors = pap_utils.get_authors_from_list(authors)

        parsed_api_dict = pap_utils.get_serialized_dict(url=url, display_title=title, title=title, abstract=abstract, journal_name=journal_name,
                                              published_date=None, authors=authors, source='IEEE')
        ieee_data_list.append(parsed_api_dict)

    return ieee_data_list

# Arxiv API Data Methods
def get_arxiv_data(query):
    """
    Gets XML repsonse from API name ARXIV
    :param query: the query string
    :type query: String
    """
    query = 'ti:' + query
    params = dict(search_query=query)
    response = extract_data_from_api('ARXIV', params)
    return (response, 'ARXIV')


def parse_arxiv_response(response):
    def prepend_ns(tag):
        return '{http://www.w3.org/2005/Atom}' + tag

    tree = ET.ElementTree(ET.fromstring(response))  # For XML parsing
    root_node = tree.getroot()

    arxiv_data_list = []

    for entry in root_node.findall(prepend_ns('entry')):
        url = entry.find(prepend_ns('link')).attrib['href']
        title = utils.check_xml_key_for_none(entry.find(prepend_ns('title')))
        abstract = utils.check_xml_key_for_none(entry.find(prepend_ns('summary')))
        journal_name = utils.check_xml_key_for_none(entry.find(prepend_ns('arxiv:journal_ref')))
        published_date = utils.check_xml_key_for_none(entry.find(prepend_ns('published')))

        try:
            datetime_object = datetime.strptime(published_date, '%Y-%m-%dT%H:%M:%SZ')
            published_date = datetime_object.strftime('%Y-%m-%d')
        except:
            published_date = ''

        authors_xml = entry.findall(prepend_ns('author'))
        authours = [author.find(prepend_ns('name')).text for author in authors_xml]

        authors = pap_utils.get_authors_from_list(authours)

        parsed_api_dict = pap_utils.get_serialized_dict(url=url, display_title=title, title=title, abstract=abstract,
                                              journal_name=journal_name, published_date=published_date, authors=authors, source='arXiv')
        arxiv_data_list.append(parsed_api_dict)

    return arxiv_data_list


# Plos API Data Methods
def get_plos_data(query):
    """
    Gets the json response from API name PLOS
    :param query: the query string
    :type query: String
    """
    query = 'title:' + query
    params = dict(q=query, wt='json')
    response = extract_data_from_api('PLOS', params)
    return (response, 'PLOS')

def parse_plos_response(response):
    json_response = json.loads(response)['response']
    docs = utils.check_json_key_for_none(json_response, 'docs')

    plos_data_list = []

    for doc in docs:
        url = 'http://journals.plos.org/plosone/article?id=' + utils.check_json_key_for_none(doc, 'id')
        title = utils.check_json_key_for_none(doc, 'title_display')
        abstract = utils.check_json_key_for_none(doc, 'abstract')[0]
        journal_name = utils.check_json_key_for_none(doc, 'journal')

        published_date = utils.check_json_key_for_none(doc, 'publication_date')

        try:
            if published_date:
                datetime_object = datetime.strptime(published_date, '%Y-%m-%dT%H:%M:%SZ')
                published_date = datetime_object.strftime('%Y-%m-%d')
        except:
            published_date = ''


        authors = utils.check_json_key_for_none(doc, 'author_display')

        authors = pap_utils.get_authors_from_list(authors)

        parsed_api_dict = pap_utils.get_serialized_dict(url=url, display_title=title, title=title, abstract=abstract, journal_name=journal_name,
                                              published_date=published_date, authors=authors, source='Plos')
        plos_data_list.append(parsed_api_dict)

    return plos_data_list


# Springer API Data Methods
def get_springer_data(query):
    """
    Gets the paper meta data from API name PLOS
    :param query: the query string
    :type query: String
    """
    query = "(title:'" + query + "')"
    api_key = '1f45958ec8fae951de568ac2d191d000'
    params = dict(q=query, api_key=api_key)
    response = extract_data_from_api('SPRINGER', params)
    return (response, 'SPRINGER')


def parse_springer_data(response):
    # load the response as JSON
    json_response = json.loads(response)
    docs = utils.check_json_key_for_none(json_response, 'records')

    springer_data_list = []

    for doc in docs:
        url = [url['value'] for url in utils.check_json_key_for_none(doc, 'url')]
        title = utils.check_json_key_for_none(doc, 'title')
        abstract = utils.check_json_key_for_none(doc, 'abstract')
        published_date = utils.check_json_key_for_none(doc, 'publicationDate')
        authors = [creator['creator'] for creator in utils.check_json_key_for_none(doc, 'creators')]

        authors = pap_utils.get_authors_from_list(authors)

        parsed_api_dict = pap_utils.get_serialized_dict(url=url[0], display_title=title, title=title, abstract=abstract, journal_name='',
                                              published_date=published_date, authors=authors, source='Springer')
        springer_data_list.append(parsed_api_dict)

    return springer_data_list