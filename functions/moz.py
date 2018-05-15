"""
Functions for querying the moz api.
"""
import base64
from decimal import Decimal
import hashlib
import hmac
import requests
import time
from credentials import moz_secrets as moz
from data_functions import make_dict


def moz_search(params, start_time):
    """
    Retrieve and return authority and mozrank from Moz api.
    Authority is a logarithmically-scaled ranking of 1-100 and MozRank
    (similar to Google's PageRank) is a logarithmically-scaled ranking of 1-10.
    :param params: The url for which authority and mozrank are being 
    requested (str), e.g. 'google.com' or 'en.wikipedia.org'.
    :param start_time: 
    :return: Returns two dicts in a list:
    - mozrank (the larger value of mozrank_url or mozrank_subdomain)
    - authority (the larger value of authority_domain or authority_page)
    """
    print('starting moz')
    error = 'ok'
    # url is the base url for the Moz api
    url = 'https://lsapi-beta.seomoz.com/linkscape'
    # endpoint gets appended to url. There are multiple endpoints, but this
    # module currently just supports url-metrics.
    endpoint = '/url-metrics/'

    # TODO could make a batched POST request see:
    # https://moz.com/help/guides/moz-api/mozscape/getting-started-with-mozscape/best-practices

    unix_now = int(time.time())
    # expires is the time, 5 minutes from now, which is used for sending a
    # signed hash of moz.ACCESS_ID and expiration time, and is hashed using
    # moz.SECRET_KEY
    expires = unix_now + 300  # 300 seconds

    # moz_fields is the subset of fields from the url-metrics endpoint which
    # don't require a paid plan. Free access is limited to one call every
    # ten seconds, with a limit of 20,000 rows per month. For the
    # url-metrics endpoint, a row is a response about a single target url
    # (e.g. yourdomain.com), regardless of how many moz_fields are returned
    # during that response.
    moz_fields = {
        "title": {
            "bit_flag": 1,
            "response_fields": {
                "ut": "Title: The title of the page, if available"
            },
        },
        "canonical": {
            "bit_flag": 4,
            "response_fields": {
                "uu": "Canonical URL: The canonical form of the URL"
            },
        },
        "links_ee": {
            "bit_flag": 32,
            "response_fields": {
                "ueid": "External Equity Links: The number of external equity "
                        "links to the URL"
            },
        },
        "links": {
            "bit_flag": 2048,
            "response_fields": {
                "uid": "Links: The number of links (equity or nonequity or not"
                       ", internal or external) to the URL"
            },
        },
        "mozrank_url": {
            "bit_flag": 16384,
            "response_fields": {
                "umrp": "MozRank: The normalized 10-point score MozRank of the"
                        " URL",
                "ignored": {
                    "umrr": "MozRank: The raw score MozRank of the URL"
                }
            },
        },
        "mozrank_subdomain": {
            "bit_flag": 32768,
            "response_fields": {
                "fmrp": "MozRank: The normalized 10-point score MozRank of the"
                        " URL's subdomain",
                "ignored": {
                    "fmrr": "MozRank: The raw score MozRank of the URL's "
                            "subdomain"
                }
            },
        },
        "http_status": {
            "bit_flag": 536870912,
            "response_fields": {
                "us": "HTTP Status Code: The HTTP status code recorded by "
                      "Mozscape for this URL, if available"
            },
        },
        "authority_page": {
            "bit_flag": 34359738368,
            "response_fields": {
                "upa": "Page Authority: A normalized 100-point score "
                       "representing the likelihood of a page to rank well in "
                       "search engine results"
            },
        },
        "authority_domain": {
            "bit_flag": 68719476736,
            "response_fields": {
                "pda": "Domain Authority: A normalized 100-point score "
                       "representing the likelihood of a domain to rank well "
                       "in search engine results"
            },
        }
    }

    # Which fields from moz_fields should be requested?
    fields_to_get = [
        "authority_domain",
        "mozrank_url",
        "mozrank_subdomain",
        "canonical",
        "authority_page",
        "title",
        "http_status",
        "links",
        "links_ee"
    ]

    # If there are any fields which shouldn't be retrieved, move them from
    # fields_to_get to fields_not_to_get.
    fields_not_to_get = [
    ]

    # Each of Moz's fields in moz_fields has a bit_flag value. To request a
    # single field from the api, its bit_flag value is sent as the Cols=
    # parameter in the api call. To request more than one field from the
    # api, the sum of all the bit_flag values is sent as the Cols= parameter.
    bit_flags_sum = 0
    for field_to_get in fields_to_get:
        if field_to_get in moz_fields:
            bit_flags_sum += moz_fields[field_to_get]["bit_flag"]

    # The code for generating signature is from Moz's seomoz Python package:
    # https://github.com/seomoz/SEOmozAPISamples/blob/master/python/mozscape.py
    str_to_sign = moz.ACCESS_ID + '\n' + str(expires)
    signature = base64.b64encode(
        hmac.new(
            moz.SECRET_KEY.encode('utf-8'),
            str_to_sign.encode('utf-8'),
            hashlib.sha1).digest()
        )

    # Assemble request_url and request_params and use these to make a GET
    # request to the moz api.
    request_url = url + endpoint + params
    request_params = {
        "Cols": bit_flags_sum,
        "Limit": 1,
        "AccessID": moz.ACCESS_ID,
        "Expires": expires,
        "Signature": signature
    }
    response = requests.get(
        request_url,
        params=request_params
    ).json()

    # Moz's json response contains cryptically-named keys. Rename the
    # cryptic keys to the more sensible names used in moz_fields, and stick
    # the new keys and associated values in response_rekeyed.
    response_rekeyed = {}
    for cryptic_key in response:
        for sensible_key in moz_fields:
            if cryptic_key in moz_fields[sensible_key]["response_fields"]:
                response_rekeyed[sensible_key] = response[cryptic_key]

    # Take the larger value of authority_domain or authority_page and of
    # mozrank_url or mozrank_subdomain.
    authority = Decimal(
        str(
            max(
        response_rekeyed['authority_domain'],
        response_rekeyed['authority_page']
    )))
    mozrank = Decimal(
        str(
            max(
        response_rekeyed['mozrank_url'],
        response_rekeyed['mozrank_subdomain']
    )))

    mozrank = make_dict(
        value=mozrank,
        data_name='mozrank',
        start_time=start_time,
        status=error
    )

    authority = make_dict(
        value=authority,
        data_name='authority',
        start_time=start_time,
        status=error
    )

    return [mozrank, authority]
