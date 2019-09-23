import requests
import pdb


def get_request_from_url(url, params):
    """
    Gets a request from url and raises exception if any exception occurs
    :param url: the request url
    :type url: String
    :param params: parameters to be added to url
    :type params: Dict
    :return: request object
    :rtype: Request or String
    """
    request = requests.get(url, params=params)
    try:
        request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print('Error in HTTP Request Custom')
        return err

    return request


