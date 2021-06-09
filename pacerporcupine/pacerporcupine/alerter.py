from os import environ
import requests
import json


def alert_to_slack(category_cases, intro=None):
    if environ.get("SLACKWH"):
        if intro:
            requests.post(
                environ.get("SLACKWH"),
                data=json.dumps({"text": intro}),
                headers={"Content-Type": "application/json"},
            )
        for i, category in enumerate(category_cases.keys()):
            cases = category_cases[
                category
            ]  # a dict of case names to case names + URLs
            msg = [f"*{category}*"]
            for case in cases.values():
                msg.append(case)
            requests.post(
                environ.get("SLACKWH"),
                data=json.dumps({"text": "\n".join(msg)}),
                headers={"Content-Type": "application/json"},
            )


def alert_to_log(category_cases, intro=None):
    if intro:
        print(intro)
    for i, category in enumerate(category_cases.keys()):
        cases = category_cases[category]  # a dict of case names to case names + URLs
        print(category)
        for case in cases.values():
            print(case)
        print("")
        if i + 1 != len(category_cases.keys()):
            print("----------------------")
            print("")
