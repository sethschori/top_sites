"""
Functions to handle JSON
"""
import json
import types


def json_to_object(json_st):
    """
    Convert JSON to an object.
    :param json_st: A JSON string.
    :return: object
    """
    obj = json.loads(json_st, object_hook=lambda d: types.SimpleNamespace(**d))
    return obj
