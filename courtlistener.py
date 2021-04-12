"""

convenience functions for interacting with the courtlistener API

"""

from os import environ, makedirs
from os.path import join, exists, dirname
import requests
from urllib.parse import urlencode
import logging
import csv
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = environ.get("API_KEY")


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
    return requests.get(
        url,
        headers={
            "content-type": "application/json",
            "Authorization": f"Token {API_KEY}",
        },
    ).json()


def search_recap(q=None, description=None, available_only=None, suit_nature=None):
    urlparams = {
        "type": "r",  # Document-oriented results from the RECAP Archive
        "available_only": "on" if available_only else "off",
        "order_by": "entry_date_filed desc",
    }
    if suit_nature:
        urlparams["suitNature"] = suit_nature
    if description:
        urlparams["description"] = description
    if q:
        urlparams["q"] = q  # wwg1wga
    return search_recap_with_url(
        "https://www.courtlistener.com/api/rest/v3/search/?{}".format(
            urlencode(urlparams)
        )
    )


def find_search_warrant_documents(n=1000):
    #     for each case and document, make a record (in memory or in a DB), so we don\'t duplicate
    #     download the documents locally
    #    ?q=&type=r&order_by=entry_date_filed%20desc&available_only=on&description=search%20warrant
    next_url = None
    records = []
    while len(records) <= n:
        if len(records) == 0:
            search_result = search_recap(
                description="search warrant", available_only=True
            )
            records += search_result["results"]
            next_url = search_result["next"]
        elif next_url:
            search_result = search_recap_with_url(next_url)
            records += search_result["results"]
            next_url = search_result["next"]
        else:  # next_url is not None (and it's not the first go)
            break
    return records
