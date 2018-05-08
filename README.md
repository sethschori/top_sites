# top_sites
**tldr; top_sites retrieves data about websites/blogs and publishes it to a static HTML file hosted on AWS S3.**

Here's how it works:

- You pick a set of blogs about a topic (e.g. entrepreneurship or coding) which you want to be tracked and ranked daily for their popularity.
- Every day the blogs are ranked according to metrics retreieved from the [Moz API](https://moz.com/products/api) and [Twitter Search API](https://developer.twitter.com/en/docs/tweets/search/api-reference).
  - If you keep the set of blogs at ~100, you can keep within the limits of the free versions of the Moz and Twitter APIs, and within an hour or two of runtime on an AWS EC2 instance, which should cost $1.50 - $3.00 per day. (I haven't tested the actual AWS costs yet, so YMMV.)
- A minimal set of metadata about the sites to be ranked is stored, as JSON, in DynamoDB. This includes:
  - **scraping metadata** about how to find the most recent blog post on the site
    - the example below finds the first `<a>` tag within the first occurrence of `class="public-article__title"`
  - **twitter metadata** about which tweets should be counted
    - the example below finds tweets referencing the [recurse.com](https://recurse.com) website, but not sent by [@recursecenter](http://www.twitter.com/recursecenter)
  - **moz metadata** about which url to query
    - the example below queries `recurse.com`
  - **URL metadata** which breaks the URL down into its components (these could be parsed programmatically, however since the delineation of subdomain and domain might not always be rule-based, I chose to have the entire URL be human-parsed, at least for now)
    - the example below uses `https://www.recurse.com/blog`
  ```json
  {
    "directives": {
      "scrape1": {
        "type": "scrape_newest",
        "parameters": [
          ["class", "public-article__title"],
          "a"
        ]
      },
      "twitter1": {
        "type": "twitter",
        "parameters": [
          "url:\"recurse com\"",
          "-from:recursecenter"
        ]
      },
      "moz1": {
        "type": "moz",
        "parameters": "recurse.com"
      }
    },
    "project": "test_blogs",
    "title": "Recurse Center",
    "url": {
      "protocol": "https://",
      "subdomain": "www",
      "domain": "recurse.com",
      "path": "/blog"
    }
  }
  ```
- The retrieved data is then parsed and saved to static HTML files (hosted on AWS S3), as a table of data which can be sorted by any of the table's columns. This screenshot shows an unstyled presentation of the data.
![index_html_screenshot](https://user-images.githubusercontent.com/20755795/39737500-79c887a6-5253-11e8-8c9c-feaebe9dd828.png)
- Finally, the data is saved as JSON back to DynamoDB.

## Technology Stack
top_sites is intended to be used with the following AWS technologies:
- **EC2 instance**: to perform data retrieval and publish to static HTML
- **DynamoDB**: database backend for the sites
- **S3**: to serve static HTML files

## Current Version
The current version of top_sites is a work in progress. Here are details of where things are at:

Feature | Status | Details
:-: | :-: | :--
web scraping | implemented | `scrape_newest` function scapes the newest blog post, as directed by metadata about the HTML tags and attributes which define how to find the most recent post
Twitter search | implemented | `twitter_search` function uses the Twitter API to search for whichever keywords are specified (e.g. find tweets mentioning the blog's URL) since yesterday
Moz | implemented | `moz_search` function uses the Moz 
DynamoDB | not (yet) implemented | currently using `sites.json` file as a simple, local storage substitute for DynamoDB
S3 | not (yet) implemented | currently outputting final HTML to `index.html` file

## How to Install
```sh
git clone https://github.com/sethschori/top_sites.git
cd top_sites
pip install .
```
