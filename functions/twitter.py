"""
Functions to interact with the Twitter search API.
"""
import datetime
import time
from html import escape
from traceback import format_exception
from TwitterSearch import (TwitterSearch, TwitterSearchOrder,
                           TwitterSearchException)
from credentials import twitter_secrets as tw
from data_functions import make_dict


def twitter_search(params, start_time):
    """
    Retrieves most recent tweets since yesterday based on keywords.
    Retrieves as many tweets as api gives, up to the maximum set by max_tweets.
    :param params: The keywords to search for, formatted as list of 
    strings. To search for a url, use this syntax:
        "url:\"gizmodo com\""
    in which the domain is separated by spaces instead of dots and the 
    internal quotes are escaped with backspaces.
    :return: 
    """
    print('starting twitter_search')
    # Set up flow control variables.
    max_tweets = 10000  # maximum number of tweets to retrieve from api
    more_tweets = True  # are there more tweets to retrieve?
    need_to_sleep = False  # tells to sleep (if approaching api rate limit)

    error = 'ok'

    try:
        # create TwitterSearch object using this app's tokens.
        ts = TwitterSearch(
            consumer_key=tw.CONSUMER_KEY,
            consumer_secret=tw.CONSUMER_SECRET,
            access_token=tw.ACCESS_TOKEN,
            access_token_secret=tw.ACCESS_TOKEN_SECRET
        )

        # Create a TwitterSearchOrder object and add keywords to it.
        tso = TwitterSearchOrder()
        for param in params:
            tso.add_keyword(param)
        # Only search for tweets since yesterday (in UTC).
        yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(1)
        tso.set_since(yesterday)

        # Set up counter variables.
        tweets = 0  # count of tweets about keywords, since yesterday
        unique_tweeters = {}  # dict of unique tweeters about keywords
        tweets_followers = 0  # count of followers of unique_tweeters
        min_id = 0  # next tweet for paginated results, when multiple api calls
        max_followers = (0, 'null')  # the tweeter with the most followers

        # Keep calling the api (for paginated results) until there are no
        # more tweets to retrieve, or until max_tweets limit has been reached.
        while more_tweets and tweets < max_tweets:
            # Sleep for 60 seconds, if needed, to avoid hitting api limit.
            if need_to_sleep:
                print("rate limit:", rate_limit)
                time.sleep(60)
            # Call the search api.
            response = ts.search_tweets(tso)
            # Are there no more tweets to retrieve?
            if len(response["content"]["statuses"]) == 0:
                more_tweets = False
            else:  # there are more tweets to retrieve
                # Iterate through the batch of tweets retrieved from this
                # api call. Count the tweet and track all the unique tweeters.
                for tweet in response["content"]["statuses"]:
                    if tweets > max_tweets:
                        break  # stop counting/tracking if reached max_tweets
                    tweets += 1
                    if (min_id == 0) or (tweet["id"] < min_id):
                        # Set min_id to the id of this tweet. The api returns
                        # tweets in reverse chronological order (most recent is
                        # first), so min_id is a lowering "ceiling" of which
                        # tweet id to start from during subsequent api call.
                        min_id = tweet["id"]
                    # Can uncomment the following lines to see who is tweeting.
                    # print(str(tweets) + "\t" + str(tweet["id"])
                    #       + "\t" + tweet["user"]["screen_name"]
                    #       + "\t" + str(tweet["user"]["followers_count"]))
                    if tweet["user"]["screen_name"] not in unique_tweeters:
                        tweeter = tweet["user"]["screen_name"]
                        tweeters_followers = tweet["user"]["followers_count"]
                        # Add tweet's screen_name and followers_count to
                        # unique_tweeters, iff this is first time seeing
                        # this screen_name.
                        unique_tweeters[tweeter] = tweeters_followers
                # Set the next paginated result's start point (subtract one
                # to avoid retrieving the last tweet from this batch twice).
                tso.set_max_id(min_id - 1)
            # If less than 15 api calls remaining then sleep during next loop.
            # (Search api free tier allows 180 calls per 15 minute period.)
            rate_limit = int(ts.get_metadata()["x-rate-limit-remaining"])
            if rate_limit < 15:
                need_to_sleep = True
            else:
                need_to_sleep = False
        # After all tweets have been retrieved (up to max_tweets), calculate
        # metrics on the followers of the tweeters in unique_tweeters.
        for tweeter in unique_tweeters:
            # Count how many followers there are in all the unique_tweeters.
            tweets_followers += unique_tweeters[tweeter]
            # Determine which tweeter from unique_tweeters has most followers.
            if unique_tweeters[tweeter] > max_followers[0]:
                max_followers = (unique_tweeters[tweeter], tweeter)

    except TwitterSearchException as e:
        tweets = None
        tweets_followers = None
        error = format_exception(ValueError, e, e.__traceback__)

    tweets = make_dict(
        value=tweets,
        data_name='tweets',
        start_time=start_time,
        status=error
    )

    tweets_followers = make_dict(
        value=tweets_followers,
        data_name='tweets_followers',
        start_time=start_time,
        status=error
    )

    most_followed_name = make_dict(
        value=escape(max_followers[1], True),
        data_name='most_followed_name',
        start_time=start_time,
        status=error
    )

    most_followed_count = make_dict(
        value=max_followers[0],
        data_name='most_followed_count',
        start_time=start_time,
        status=error
    )

    return [tweets, tweets_followers, most_followed_name, most_followed_count]
