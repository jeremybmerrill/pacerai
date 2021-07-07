from os import environ
import requests
import json
from html import unescape
from itertools import groupby
from operator import itemgetter


def case_object_to_slarkdown(
    case_name=None, absolute_url=None, thing_searched=None, court_id=None, category=None, document_type=None
):
    case_name = unescape(case_name)
    if (
        not thing_searched
        or thing_searched.replace(" ", "").replace(",", "").lower()
        in case_name.replace(" ", "").replace(",", "").lower()
    ):
        thing_searched = ""
    if document_type:
        document_type = f"[{document_type}]"
    else:
        document_type = ""
    return f"<{absolute_url}|{case_name}> {thing_searched} {document_type}\n"


def case_object_to_text(
    case_name=None, absolute_url=None, thing_searched=None, court_id=None, category=None, document_type=None
):
    case_name = unescape(case_name)
    if (
        not thing_searched
        or thing_searched.replace(" ", "").replace(",", "").lower()
        in case_name.replace(" ", "").replace(",", "").lower()
    ):
        thing_searched = ""
    else:
        thing_searched = "\n  " + thing_searched
    if document_type:
        document_type = f"[{document_type}]"
    else:
        document_type = ""        
    return "- {}   {} {}".format(case_name, thing_searched, document_type)


def alert_to_slack(category_case_objects, intro=None):
    slack_blocks = []
    if environ.get("SLACKWH"):
        if intro:
            slack_blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{intro}:*"},
                }
            )
        for category, cases in category_case_objects.items():

            slack_blocks.append({"type": "divider"})
            slack_blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{category}:*"},
                }
            )
            cases_by_court = groupby(
                sorted(cases.values(), key=itemgetter("court_id")),
                key=itemgetter("court_id"),
            )
            for court, cases_of_court in cases_by_court:
                cases_of_court = "• " + "\n• ".join(
                    [case_object_to_slarkdown(**case) for case in cases_of_court]
                )
                slack_blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{court}:*\n\n{cases_of_court}",
                        },
                    }
                )
    send_to_slack(slack_blocks)


def alert_to_log(category_cases_objects, intro=None):
    if intro:
        print(intro)
    for i, category in enumerate(category_cases_objects.keys()):
        cases = category_cases_objects[
            category
        ]  # a dict of case names to case names + URLs
        print(category)
        cases_by_court = groupby(
            sorted(cases.values(), key=itemgetter("court_id")),
            key=itemgetter("court_id"),
        )
        for court, cases_of_court in cases_by_court:
            print(court)
            for case in cases_of_court:
                print(case_object_to_text(**case))
        print("")
        if i + 1 != len(category_cases_objects.keys()):
            print("----------------------")
            print("")


def send_to_slack(blocks, max_block_size=46):
    for subset_of_blocks in (
        blocks[pos : pos + max_block_size]
        for pos in range(0, len(blocks), max_block_size)
    ):
        print(subset_of_blocks)
        payload = {"blocks": subset_of_blocks}

        response = requests.post(environ["SLACKWH"], json=payload)

        if response.status_code != 200:
            raise ValueError(
                "Request to slack returned an error %s, the response is: %s"
                % (response.status_code, response.text)
            )
