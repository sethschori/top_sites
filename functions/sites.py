import datetime
from decimal import Decimal
import json
from data_functions import (prune_empty_branches, setup_data_branch,
                            unpack_and_save_list)
from dynamodb import Dynamo
from error_handling import handle_error
from html_parse import scrape_newest
# from json_functions import json_to_object
from moz import moz_search
from s3 import S3
from twitter import twitter_search
from url_functions import generate_filename, tidy_url


class Site(object):
    """
    Site represents a website or blog.
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
    """
    # def __getitem__(self, items):
    #     print('{i}'.format(i=items))

    def __init__(self, site_dict):
        """
        Instantiate a Site object.
        :param site_dict: a dict with Site's existing config and data
        """
        time_start = datetime.datetime.utcnow()
        # Copy site_dict keys to Site keys.
        try:
            self.__dict__.update(site_dict)
        except Exception as e:
            handle_error(
                err=e,
                msg='could not copy JSON to Site keys -- invalid/missing JSON?'
            )
            raise ValueError('could not create Site with JSON: {j}'.format(
                j=site_dict
            ))
        self.test_mode = False  # test_mode caches HTML; False means no cache

        # Clean and establish default self.url values if not already present.
        self.url = tidy_url(self.url)

        # Create Site's filename to be used for local caching if test_mode=True
        if self.test_mode:
            self.url['filename'] = generate_filename(self.url)

        # Create data branch of Site if it doesn't already exist.
        try:
            len(self.data)
        except AttributeError:
            self.data = {}
        # Make sure all top-level keys within self.data are present
        self.data = setup_data_branch(
            data_dict=self.data,
            directives_dict=self.directives
        )

        # directives_map holds instructions of how to handle the different
        # types of directives: which function to call and which parameters
        # to pass to that function. This enables, below, to make a single loop
        # through self.directives without using any if statements.
        directives_map = {
            'moz': {
                'func': moz_search,
                'params_to_pass': {
                    'params': 'this will be replaced with params',
                }
            },
            'scrape_newest': {
                'func': scrape_newest,
                'params_to_pass': {
                    'url': self.url,
                    'params': 'this will be replaced with params',
                    'test_mode': self.test_mode
                }
            },
            'twitter': {
                'func': twitter_search,
                'params_to_pass': {
                    'params': 'this will be replaced with params',
                }
            }
        }

        # Follow all the directives (to scrape and ping apis) and save all
        # the collected data into the proper locations within self.data
        # TODO: handle errors here in case of incomplete/incorrect directives
        for directive in self.directives:
            start_time = datetime.datetime.utcnow()
            params = self.directives[directive]["parameters"]
            # d_type points to the top-level key within directives_map (e.g.
            # 'moz', 'twitter', 'scrape_newest')
            d_type = self.directives[directive]['type']
            # Save the relevant value from the "parameters" key in
            # self.directives to the relevant 'params' key in directives_map.
            directives_map[d_type]['params_to_pass']['params'] = params
            # func is the function to be called
            func = directives_map[d_type]['func']
            # params_to_pass are the parameters to pass to func
            params_to_pass = directives_map[d_type]['params_to_pass']
            # Call func, passing in params_to_pass and start_time, which is
            # used to calculate how long func took to run. response will be
            # a list of dict(s).
            response = func(**params_to_pass, start_time=start_time)
            # Unpack the list of dicts(s) returned in response and save them
            # to the relevant lists within self.data.
            self.data = unpack_and_save_list(
                list_of_dicts=response,
                data_dict=self.data,
                location=directive
            )

        # Remove any empty dict key/value pairs from self.data if they
        # exist. This is needed because DynamoDB can't save empty strings
        # as dict values.
        self.data = prune_empty_branches(self.data)
        time_end = datetime.datetime.utcnow()
        self.elapsed_seconds = Decimal(
            str((time_end - time_start).total_seconds())
        )


def load_sites(dynamo_session):
    """
    Load Dynamo data and instantiate site objects (with scraping & api calls).
    :param site_items: sites as a list of dicts
    :param dynamo_session: a session (connection) to DynamoDB
    :return: a list of site objects.
    """
    site_objects = []
    items = dynamo_session.get_all_rows(
        table_name='sites'
    )
    # Turn the DynamoDB rows about the sites into a list of Site objects.
    for item in items:
        try:
            site_obj = Site(item)
        except ValueError as err:
            handle_error(err=err)
        site_objects.append(site_obj)
    return site_objects

# TODO: Move the lines below (for '__main__') to 1 or 2 functions.
if __name__ == '__main__':
    dynamo = Dynamo(
        profile_name='top-sites'
    )
    sites = load_sites(dynamo)

    # Format one copy of table_row.html per each Site object in sites and
    # concatenate all of the table rows into table_rows_html.
    with open('../templates/table_row.html', 'r') as fo:
        site_template = fo.read()
    table_rows_html = ''
    for position, site in enumerate(sites):
        table_rows_html += site_template.format(site=site, rank=position + 1)

    # Then format sites.html by inserting all of the table rows into the
    # appropriate place within sites.html.
    with open('../templates/sites.html', 'r') as fo:
        html_page = fo.read()
    now = datetime.datetime.utcnow().strftime(
        '%A %B %-d, %Y at %-I:%M %p GMT (UTC)'
    )
    html_page = html_page.format(table_rows=table_rows_html, last_updated=now)

    # Finally, save html_page as index.html. Later, instead of saving this
    # file locally, it will instead be uploaded to an S3 bucket/folder.
    with open('../output/index.html', 'w') as fo:
        fo.write(html_page)

    # Upload file to S3
    s3 = S3()
    result = s3.upload_file_public_read(file='foo')
    print(result)

    # Write the site objects back to DynamoDB
    result = dynamo.batch_update_rows(
        table_name='sites',
        items=sites
    )
