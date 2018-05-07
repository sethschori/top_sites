"""
Functions to retrieve and parse the HTML from a url.
"""
from bs4 import BeautifulSoup
from html import escape
import requests
import requests.exceptions as requests_exc
from traceback import format_exception
from data_functions import make_dict


def scrape_newest(url, params, test_mode, start_time):
    """
    Scrape the newest blog post (as specified by params) from url.
    :param url: 
    :param params:
    :param test_mode: 
    :param start_time:
    :return: 
    """
    print('starting scrape_newest')
    error = 'ok'
    if not test_mode:
        # When not in testing mode, get the HTML of url.
        try:
            raw_html = request_site(url)
        except ValueError as e:
            error = e
            raw_html = None
    else:
        # When in testing mode, avoid repeated requests to url.
        # Instead, get the HTML str from locally cached file if it exists.
        # If it doesn't exist, first save the HTML to local cache file.
        try:
            raw_html = read_site_from_file(url['filename'])
        except FileNotFoundError:
            try:
                site_html = save_site_to_file(
                    url['filename'],
                    url['full_url']
                )
                if site_html:
                    raw_html = read_site_from_file(url['filename'])
            except ValueError as e:
                error = e
                raw_html = None

    if raw_html is not None:
        # parse HTML find target element
        try:
            soup = parse_site(raw_html, params)
        except ValueError as e:
            error = e
            a_link_text = None
            a_link_url = None

        a_link_text = soup.text
        a_link_url = soup['href']
        a_link_url = make_absolute(
            url_to_check=a_link_url,
            site_url=url
        )
    else:
        a_link_text = None
        a_link_url = None

    if isinstance(error, Exception):
        error = format_exception(ValueError, error, error.__traceback__)

    a_link_text = make_dict(
        value=escape(a_link_text, True),
        data_name='a_link_text',
        start_time=start_time,
        status=error
    )

    a_link_url = make_dict(
        value=a_link_url,
        data_name='a_link_url',
        start_time=start_time,
        status=error
    )

    return [a_link_text, a_link_url]


def request_site(url):
    """
    Uses requests package to get HTML from url.
    :param url: the url to request
    :return: None if error; raw HTML as a byte string if no error.
    """
    try:
        response = requests.get(url)
    except (requests_exc.BaseHTTPError, requests_exc.ConnectionError) as e:
        raise ValueError('requests package raised an exception when trying '
                         'to get {u}. Message received: {e}'.format(
                            u=url,
                            e=e
                            )
                        )
    if response.status_code != 200:
        raise ValueError('requests package received status code {s} when '
                         'trying to get {u}.'.format(
                            s=response.status_code,
                            u=url
                            )
                        )
    return response


def read_site_from_file(filename):
    """
    Helper function to return (HTML) contents stored in a file.
    :param filename: file name to read from
    :return: returns the file as a str
    """
    with open(filename, 'r') as f:
        return f.read()


def save_site_to_file(filename, url):
    """
    Helper function to save retrieved HTML to a file.
    :param filename: file name to save to
    :param url: url to retrieve HTML from
    :return: returns True if succeeded, raises exception if failed
    """
    try:
        response = request_site(url)
    except ValueError as e:
        raise ValueError(e)
    with open(filename, 'wb') as f:
        f.write(response.content)
        return True


def parse_site(raw_html, params):
    """
    Parses HTML str to find target element specified in self.directives.
    :return: a BeautifulSoup object of the target element.
    """
    soup = BeautifulSoup(raw_html, 'html.parser')

    for param in params:
        if isinstance(param, list):
            soup = soup.find(attrs={param[0]: param[1]})
        else:
            soup = soup.find(param)
    if soup is None:
        raise ValueError("BeautifulSoup couldn't find params {p}".format(
                            p=params
        ))

    return soup


def make_absolute(url_to_check, site_url):
    """
    Checks whether a url is relative and, if so, makes it absolute.
    :param url_to_check: the url to check and make absolute
    :param site_url: the url dict which has the Site's url components
    :return: an absolute url
    """
    # If '://' is anywhere in url_to_check, it's an absolute url, so return it.
    if '://' in url_to_check:
        return url_to_check

    # Since '://' is not in url_to_check, we can assume it does not start with
    # 'http[s][://]' and either starts with '/' or alphanumeric characters.
    absolute_url = site_url['protocol']
    if len(site_url['subdomain']) > 0:
        absolute_url += site_url['subdomain'] + '.'
    absolute_url += site_url['domain']
    if url_to_check[0] != '/':
        absolute_url += '/'
    absolute_url += url_to_check

    return absolute_url
