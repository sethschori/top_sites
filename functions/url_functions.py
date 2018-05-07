"""
Simple functions to operate on Site.url dict.
"""
import re


def tidy_url(url):
    """
    Clean and establish default Site.url values if not already present.
    :param url: a dict describing the url of a Site.
    :return: cleaned and defaulted url dict
    """
    # Make sure that url protocol, subdomain, and path values are set to
    # appropriate defaults in case they were omitted when initially added to
    # database. This is to avoid having to do subsequent error catching when
    # referring to non-existent key(s) in url (and non-existent attributes
    # in the Site class).
    component_defaults = {
        'protocol': 'http://',
        'subdomain': '',
        'path': '/'
    }
    for component in component_defaults:
        try:
            len(url[component])
        except AttributeError:
            url[component] = component_defaults[component]

    # Remove trailing '.' in url data if it was accidentally added
    # during data entry.
    if len(url['subdomain']) > 0 and url['subdomain'][-1] == '.':
        url['subdomain'] = url['subdomain'][0:-1]

    # Assemble full_url for later usage.
    url['full_url'] = url['protocol'] + url['subdomain']
    if len(url['subdomain']) > 0:
        url['full_url'] += '.'
    url['full_url'] += url['domain'] + url['path']

    return url


def generate_filename(url):
    """
    Generate the filename to be used for local caching if test_mode = True.
    :return: filename of type str, and ending in ".html"
    """
    # Replace '.' in subdomain with '_'
    subdomain = url['subdomain']
    if len(subdomain) > 0:
        subdomain = '_'.join(subdomain.split('.'))
        subdomain += '_'

    # Replace '/' in path with '-' and remove anything from path that's
    # not a letter, digit, or '-'.
    path = url['path']
    if len(path) > 1:
        path = '-'.join(path.split('/'))
        path = re.sub(r'[^a-zA-Z\d-]', '', path)
    else:
        path = ''

    # Concatenate filename.
    domain = '_'.join(url['domain'].split('.'))
    filename = '../html_cached_files/' + subdomain + domain + path + '.html'

    return filename
