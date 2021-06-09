from datetime import datetime, timedelta
import logging
from os.path import join, dirname
from os import environ

from dotenv import load_dotenv
from tqdm import tqdm
import pandas as pd
from sqlalchemy import create_engine

from pacerporcupine.models.classifier import Classifier
from pacerporcupine.models.named_entity_recognizer import NamedEntityRecognizer
from pacerporcupine.alerter import alert_to_log, alert_to_slack

load_dotenv()

DAYS_BACK = 3
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

ENGINE = create_engine(environ.get("LIVE_DATABASE_URL"))


def get_search_warrant_metadata_from_pacer_rss(start_date="2021-05-10"):
    return pd.read_sql(
        """
        select * from rss_docket_entries where document_type ilike '%%warrant%%' and pub_date > %(start_date)s;
        """,
        ENGINE,
        params={"start_date": start_date},
    )


def alert_based_on_pacer_rss(start_date=None):
    start_date = start_date or (datetime.today() - timedelta(days=7)).strftime(
        "%m/%d/%Y"
    )

    docs_df = get_search_warrant_metadata_from_pacer_rss(start_date)

    print("found {} possible search warrants".format(docs_df.shape[0]))
    docs_df["to_classify"] = docs_df.case_name + " " + docs_df.document_type

    # predict
    casename_shortdesc_classifier = Classifier(
        "/tmp/pacerporcupine/models/classifier/casename_shortdesc_model/"
    )
    docs_df = casename_shortdesc_classifier.predict(docs_df, "to_classify")
    search_warrants = docs_df[docs_df["predicted_class"] == 1].copy()
    print(
        "of which, {} are search warrants according to the model".format(
            search_warrants.shape[0]
        )
    )

    # categorize
    ner = NamedEntityRecognizer(
        "/tmp/pacerporcupine/models/flairner/final-model-20210607.pt"
    )
    # TODO: clean this up...
    search_warrants["caseName"] = search_warrants.case_name
    search_warrants["court_id"] = search_warrants.court  # rename this in main DB?
    search_warrants["absolute_url"] = search_warrants.guid  # rename this in main DB?
    search_warrants["description"] = search_warrants.case_name.replace(
        "USA v.", "Search/Seizure Warrant Returned Executed on 8/5/2020 for"
    )
    category_cases = classify_cases_by_searched_object_category(ner, search_warrants)
    alert_to_log(category_cases, "search warrants from PACER RSS")
    alert_to_slack(category_cases, "search warrants from PACER RSS")


def classify_cases_by_searched_object_category(ner, search_warrants_df):
    """
    depends on the following columns in sthe search_warrants_df dataframe:
        - description (for classification)
        - caseName, only for printing
        - court_id, only for printing
        - absolute_url, only for printing
    """
    category_cases = {}

    for i, doc in tqdm(
        search_warrants_df.iterrows(), total=search_warrants_df.shape[0]
    ):
        if len(doc["description"]) == 0:
            log.warn("blank description: {}".format(doc["absolute_url"]))

        sentence_entities = ner.predict(doc["description"])
        if len(sentence_entities) > 0:
            for entity in sentence_entities:
                thing_searched = entity.text
                category = entity.tag
                if category[:2] == "L-":  # entity continuations
                    continue
                case_string = "- {}    *{}*".format(doc["caseName"], doc["court_id"])
                if (
                    thing_searched.replace(" ", "").replace(",", "").lower()
                    not in doc["caseName"].replace(" ", "").replace(",", "").lower()
                ):
                    case_string += "\n  " + thing_searched
                case_string_with_url = case_string + "\n  " + doc["absolute_url"]

                category_cases[category] = category_cases.get(category, {})
                if case_string not in category_cases[category]:
                    category_cases[category][case_string] = case_string_with_url
        else:
            case_string = "- {}    *{}*".format(doc["caseName"], doc["court_id"])
            case_string_with_url = case_string + "\n  " + doc["absolute_url"]

            category = "no category detected"
            category_cases[category] = category_cases.get(category, {})
            if case_string not in category_cases[category]:
                category_cases[category][case_string] = case_string_with_url
    return category_cases


if __name__ == "__main__":
    alert_based_on_pacer_rss()