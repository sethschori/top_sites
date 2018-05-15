"""
Functions that operate on data structures used within this package.
"""
import datetime
from decimal import Decimal


def make_dict(value, data_name, start_time, status='ok'):
    """
    Takes value and formats it in a standard way as a dict.
    :param value: a str, int, None, etc. that will be standard-formatted as 
    a dict under the 'payload' key of the dict
    :param data_name: the "parent" key under which this dict will be stored 
    in the database
    :param start_time: the UTC time (as a datetime object) at which the 
    calling function began retrieving this value, to calculate duration.
    :param status: the error message returned if the calling function hit an
    exception when attempting to retrieve this value
    :return: a standard-formatted dict used within this package
    """
    duration = Decimal(
        str((datetime.datetime.utcnow() - start_time).total_seconds())
    )
    formatted_dict = {
        'accessed': datetime.datetime.utcnow().strftime(
            '%Y-%m-%dT%H:%M:%S%z'
            ),
        'data_name': data_name,
        'duration': duration,
        'payload': value,
        'status': status
    }
    return formatted_dict


def unpack_and_save_list(list_of_dicts, data_dict, location):
    """
    Puts each dict from list_of_dicts in appropriate place in data_structure.
    Also stores a maximum of max_to_keep dicts (e.g. 30 days' worth).
    data_structure is assumed to look like this:
        {
          '<location/data_subbranch (eg scrape1/twitter1/moz1)>': {
            '<data_name (eg a_link_text/tweets)>': [
              {<target_dict from list_of_dicts goes here>},
              {<up to (max_to_keep dicts - 1) dicts will follow>}
            ]
          }
        }
    :param list_of_dicts: a list of dicts to be saved to database
    :param data_dict: the full (JSON) data structure from database
    :param location: the top-level key within data_structure where each dict
    within list_of_dicts will be stored
    :return: returns revised data_structure
    """
    max_to_keep = 5  # (int >= 1) number dicts to store in data_dict lists
    data_subbranch = data_dict[location]
    for target_dict in list_of_dicts:
        data_name = target_dict['data_name']  # key where target_list lives
        try:  # see whether the key already exists
            # target_list is which list to save target_dict to
            target_list = data_subbranch[data_name]
        except KeyError:
            data_subbranch[data_name] = []
            target_list = data_subbranch[data_name]
        if len(target_list) > max_to_keep - 1:
            sliced_dict = target_list[max_to_keep - 1:]
            target_list = target_list[:max_to_keep - 1]
            print('sliced_dict:', sliced_dict)
        target_list = [target_dict] + target_list
        data_dict[location][data_name] = target_list
    return data_dict


def prune_empty_branches(data_dict):
    """
    Deletes key/value pairs from dict in which value is empty dict.
    The use case for this function in this package is that AWS's DynamoDB
    doesn't permit storage of key/value pairs where the value is empty.
    :param data_dict: a data structure dict from database
    :return: "pruned" data_structure as a dict
    """
    branches_to_prune = []  # list of keys to del post-iterate data_dict
    for branch in data_dict:
        if not data_dict[branch]:  # empty dicts evaluate to False
            branches_to_prune.append(str(branch))
    for branch_to_prune in branches_to_prune:
        del data_dict[branch_to_prune]  # delete the key/value pair
    return data_dict


def setup_data_branch(data_dict, directives_dict):
    """
    Sets up needed keys in 'data' branch of data_dict if don't already exist
    :param data_dict: a data structure dict from database
    :param directives_dict: a dict from database with the site's directives
    :return: data_dict w/ full set of needed keys (and associated empty dicts)
    """
    for key in directives_dict:
        if key not in data_dict:
            data_dict[key] = {}
    return data_dict
