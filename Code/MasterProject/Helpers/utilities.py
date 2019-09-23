import math
import pandas as pd

month_dict = {
        'jan':1,
        'feb':2,
        'mar':3,
        'apr':4,
        'may':5,
        'jun':6,
        'jul':7,
        'aug':8,
        'sep':9,
        'oct':10,
        'nov':11,
        'dec':12
    }

def check_string_for_none(variable):
    if variable is None:
        return ''
    return variable

def check_list_for_none(list):
    if list is None:
        return []
    return list

def check_xml_key_for_none(key):
    if key is None:
        return ''
    return key.text

def check_json_key_for_none(dict, key):
    if key in dict:
        return dict.get(key)
    return ''

def check_for_nan(value):
    if not isinstance(value, float):
        return value

    if not math.isnan(value):
        return value
    return ''


def get_incremented_id(max_id, iteration_count):
    if max_id is None:
        max_id = 0
    if max_id == 0:
        incremented_id = max_id + iteration_count
    else:
        incremented_id = max_id + iteration_count + 1

    return incremented_id

def is_valid_year(year):
  if not pd.isnull(year) and year.isdigit():
    if int(year) >=1900 and int(year) <=2020:
      return year
    else:
        return 0


def is_month_valid(month):
    if not pd.isnull(month) and len(month)>=3 and month in month_dict.keys():
        return True
    return False


def get_month_num(month):


    month = month.lower()
    month = month[:3]
    return month_dict[month]
