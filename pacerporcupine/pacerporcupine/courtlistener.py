"""

convenience functions for interacting with the courtlistener API

"""

from os import environ, makedirs
from os.path import join, exists, dirname
import logging
import csv

import requests
from urllib.parse import urlencode
import pandas as pd


log = logging.getLogger(__name__)


def get_pdf(recap_filepath_local, type_of_file="other"):
    logging.basicConfig(level=logging.DEBUG)

    fn = recap_filepath_local.split("/")[-1]
    fp = join(STORAGE_PATH, type_of_file, fn)
    makedirs(dirname(fp), exist_ok=True)
    if exists(fp):
        return fp
    url = recap_filepath_local.replace(
        "/storage", "https://www.courtlistener.com"
    ).replace("/sata", "https://www.courtlistener.com")
    with open(fp, "wb") as f:
        logging.debug(f"actually getting PDF from the web {url}")
        f.write(requests.get(url).content)
    return fp


def get_search_warrant_pdf(recap_filepath_local):
    return get_pdf(recap_filepath_local, "search_warrant")


# def get_docket_entries():
#     "https://www.courtlistener.com/api/rest/v3/docket-entries/?docket__id=XXX"
def search_recap_with_url(url):
    API_KEY = environ.get("API_KEY")

    log.debug(url)
    return requests.get(
        url,
        headers={
            "content-type": "application/json",
            "Authorization": f"Token {API_KEY}",
        },
    ).json()


def search_recap(
    q=None, description=None, available_only=None, suit_nature=None, filed_after=None
):
    # sadly we can't easily upgrade to Courtlistener v4
    # type "r" is missing documents (i.e. absolute_url)
    # the new type "rd" is missing case-level data like caseName
    # I'll have to make two queries, one search, then fetch the docket per document
    # cf. https://www.courtlistener.com/help/api/rest/v4/migration-guide/



    urlparams = {
        "type": "r",  # Document-oriented results from the RECAP Archive
        "order_by": "entry_date_filed desc",
    }
    if available_only:
        urlparams["available_only"] = "on"
    if filed_after:
        urlparams["filed_after"] = filed_after
    if suit_nature:
        urlparams["suitNature"] = suit_nature
    if description:
        urlparams["description"] = description
    if q:
        urlparams["q"] = q  # wwg1wga
    print(urlparams)
    return search_recap_with_url(
        "https://www.courtlistener.com/api/rest/v3/search/?{}".format(
            urlencode(urlparams)
        )
    )


def find_search_warrant_documents_by_description(
    n=1000, filed_after=None, available_only=True
):
    return search_for_docs(
        description="search warrant",
        n=n,
        filed_after=filed_after,
        available_only=available_only,
    )
    #     for each case and document, make a record (in memory or in a DB), so we don\'t duplicate
    #     download the documents locally
    #    ?q=&type=r&order_by=entry_date_filed%20desc&available_only=on&description=search%20warrant


def find_search_warrant_documents_by_keyword(
    n=1000, filed_after=None, available_only=True
):
    return search_for_docs(
        q="search warrant",
        n=n,
        filed_after=filed_after,
        available_only=available_only,
    ) + search_for_docs(
        q="seizure warrant",
        n=n,
        filed_after=filed_after,
        available_only=available_only,
    )


def search_for_docs(n=1000, **kwargs):
    """
    kwargs passed through to search_recap:  q=None, description=None, available_only=None, suit_nature=None, filed_after=None

    """
    next_url = None
    records = []
    first_run = True
    while len(records) <= n:
        if first_run:
            first_run = False
            search_result = search_recap(**kwargs)
            if "results" not in search_result:
                print("no results in search_result", search_result)
                break
            records += search_result["results"]
            next_url = search_result["next"]
        elif next_url:
            search_result = search_recap_with_url(next_url)
            records += search_result["results"]
            next_url = search_result["next"]
        else:  # next_url is not None (and it's not the first go)
            break
    return records
