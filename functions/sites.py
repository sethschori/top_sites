from bs4 import BeautifulSoup
# import html  # might need to use unescape()
import json
import requests
import requests.exceptions as req_exc
from error_handling import handle_error
from json_functions import json_to_object


class Site(object):
    """
    Site class represents a website or blog.
    When instantiating a Site object, the dict provided must contain following:

    1. directives: a list specifying the target element that is sought within
    the HTML retrieved from url (see below). The list is processed 
    iteratively, successively narrowing down the scope. The list can contain
    a combination of str elements and two-item list elements. 
    If str, (eg "a", "article", or "h1"), find the first occurrence of 
    that str within the url -- or in the previously-narrowed scope of the url.
    If list (eg "id": "foo" or "class": "bar"), the list must have 
    exactly two items in the order of list[0]=key and list[1]=value. 
    This method then finds the first occurrence of that key/value pair
    within url -- or in the previously-narrowed scope of the url.

    2. url: the url from which to retrieve HTML and parse it with the
    directives (see above).
    
    3. filename: if self.test_mode = True, then a filename must be specified of
    where to locally save the retrieved HTML
    """
    def __init__(self, site_dict):
        """
        Instantiate a Site object.
        :param site_dict: a dict with Site's config details
        """
        try:
            self.__dict__.update(site_dict)  # copy site_dict keys to Site keys
        except Exception as e:
            handle_error(
                err=e,
                msg='could not copy JSON to Site keys -- invalid/missing JSON?'
            )
            raise ValueError('could not create Site with JSON: {j}'.format(
                j=site_dict
            ))
        self.test_mode = True  # set testing mode; comment out to turn off

        self.raw_html = self.get_site()  # get the raw HTML for site's url
        soup = self.parse_site()  # parse raw HTML to find target <a> element
        self.html_pair = soup['href'], soup.text  # save <a> as html_pair tuple

    def get_site(self):
        """
        Retrieves a site webpage (specified in self.url) in HTML format.
        :return: returns None if error; otherwise returns the raw HTML
        """
        def request_site(url):
            """
            Uses requests package to get HTML from url.
            :param url: the url to request
            :return: None if error; raw HTML as a byte string if no error.
            """
            try:
                response = requests.get(url)
            except req_exc.BaseHTTPError as e:
                handle_error(
                    exc=req_exc.BaseHTTPError,
                    err=e
                )
                return None
            if response.status_code != 200:
                handle_error(
                    msg='HTTP status code: {s}'.format(s=response.status_code)
                )
                return None
            return response

        def read_site_from_file(filename):
            """
            Helper function to return (HTML) contents stored in a file.
            : param filename: file name to read from
            :return: returns the file as a str
            """
            with open(filename, 'r') as f:
                return f.read()

        def save_site_to_file(filename, url):
            """
            Helper function to save retrieved HTML to a file.
            :param filename: file name to save to
            :param url: url to retrieve HTML from
            :return: doesn't return anything
            """
            response = request_site(url)
            with open(filename, 'wb') as f:
                f.write(response.content)

        # When not in testing mode, get the HTML of self.url and return it.
        if not self.test_mode:
            return request_site(self.url)

        # When in testing mode, avoid repeated requests to self.url.
        # Instead, get the HTML str from locally cached file if it exists.
        # If it doesn't exist, save the HTML to local file and return it.
        try:
            return read_site_from_file(self.filename)
        except:
            save_site_to_file(self.filename, self.url)
            return read_site_from_file(self.filename)

    def parse_site(self):
        """
        Parses HTML str to find target element specified in self.directives.
        :return: a BeautifulSoup object of the target element.
        """
        soup = BeautifulSoup(self.raw_html, 'html.parser')

        for directive in self.directives:
            if isinstance(directive, list):
                soup = soup.find(attrs={directive[0]: directive[1]})
            else:
                soup = soup.find(directive)

        return soup


with open('sites.json', 'r') as fo:
    sites_json = json.loads(fo.read())

for site_json in sites_json:
    try:
        site = Site(site_json)
        print(site.html_pair)
    except ValueError as err:
        handle_error(err=err)


"""
dynamo.py
\ functions to interact with dynamo, using boto
postgresql.py
\ functions to interact with postgresql, using sqlalchemy
publishing.py
\ pelican functions to generate html, make & rsync to build and upload
apis.py
\ functions to interact with apis
"""
