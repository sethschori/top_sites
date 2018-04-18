"""
Functions to handle JSON.

This is currently unused. But might use it later.
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
