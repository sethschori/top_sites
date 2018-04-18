"""
Error handling.
"""
import inspect


def handle_error(exc=Exception, err='UNKNOWN', msg='none'):
    """
    Function to handle errors by printing them.
    Will eventually expand to local and/or console and/or Dynamo logging.
    :param exc: the exception type
    :param err: the error returned
    :param msg: an optional additional message to help with debugging
    :return: doesn't return anything
    """
    call_stack = inspect.stack()
    calling_function = call_stack[1][3]
    stack_str = ''
    for item in reversed(call_stack[1:]):
        stack_str += '{f}:{l}/'.format(f=item[3], l=item[2])
    print('caller: ', calling_function)
    print('stack trace:', stack_str)
    print('exception:', exc, 'error:', err, 'msg:', msg)
