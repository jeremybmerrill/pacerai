from datetime import datetime, timedelta
import logging
from os.path import join, dirname
from os import environ

from dotenv import load_dotenv
from tqdm import tqdm
import pandas as pd
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from pacerporcupine.models.classifier import Classifier
from pacerporcupine.models.named_entity_recognizer import NamedEntityRecognizer
from pacerporcupine.alerter import alert_to_log, alert_to_slack
from pacerporcupine.db import RSSDocketEntry, RssSwOrNotPrediction, Base, RssNerPrediction

load_dotenv()

DAYS_BACK = 1
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

ENGINE = create_engine(environ.get("LIVE_DATABASE_URL"))
Session = sessionmaker(bind=ENGINE)


SEARCH_WARRANT_OR_NOT_PREDICTION_TYPE = "swornot"
SEARCH_WARRANT_OBJECT_NER_PREDICTION_TYPE = "swobjectner"
def get_search_warrant_metadata_from_pacer_rss(start_date="2021-06-10"):
    session = Session()

    search_warrant_predictions = (
        session.query(RssSwOrNotPrediction)
        .filter(RssSwOrNotPrediction.prediction_type == SEARCH_WARRANT_OR_NOT_PREDICTION_TYPE)
        .subquery()
    )
    query = (
        session.query(RSSDocketEntry)
        .filter(or_(RSSDocketEntry.document_type.ilike("%warrant%"), RSSDocketEntry.document_type.ilike("%unseal%")))
        .filter(RSSDocketEntry.pub_date > start_date)
        .outerjoin(search_warrant_predictions)
        .filter(search_warrant_predictions.c.id == None)
    )
    print(query.statement)
    return pd.read_sql(query.statement, query.session.bind)


def record_swornot_prediction(record):
    if environ.get("SKIPDB"):
        return
    session = Session()
    pred = RssSwOrNotPrediction(
        case_number=record["case_number"],
        pub_date=record["pub_date"],
        prediction_type=SEARCH_WARRANT_OR_NOT_PREDICTION_TYPE,
        prediction_value=record["predicted_class"],
    )

    session.add(pred)
    session.commit()


def record_ner_prediction(record, category, thing_searched):
    if environ.get("SKIPDB"):
        return
    session = Session()
    pred = RssNerPrediction(
        case_number=record["case_number"],
        pub_date=record["pub_date"],
        prediction_type=SEARCH_WARRANT_OBJECT_NER_PREDICTION_TYPE,
        prediction_value=category,
        prediction_substring=thing_searched
    )

    session.add(pred)
    session.commit()



def alert_based_on_pacer_rss(start_date=None):
    start_date = start_date or (datetime.today() - timedelta(days=DAYS_BACK)).strftime(
        "%Y-%m-%d"
    )

    docs_df = get_search_warrant_metadata_from_pacer_rss(start_date)

    print("found {} possible search warrants".format(docs_df.shape[0]))
    if docs_df.shape[0] == 0:
        return
    docs_df["to_classify"] = docs_df.case_name + " | " + docs_df.document_type
    docs_df.dropna(subset=["to_classify"], inplace=True)
    # predict
    casename_shortdesc_classifier = Classifier(
        "/tmp/pacerporcupine/models/classifier/casename_shortdesc_model/"
    )
    docs_df = casename_shortdesc_classifier.predict(docs_df, "to_classify")
    docs_df[["case_number", "pub_date", "predicted_class"]].apply(
        record_swornot_prediction, axis=1
    )

    search_warrants = docs_df[docs_df["predicted_class"] == 1].copy()
    print(
        "of which, {} are search warrants according to the model".format(
            search_warrants.shape[0]
        )
    )

    # categorize
    ner = NamedEntityRecognizer("/tmp/pacerporcupine/models/flairner/best-model.pt")
    # TODO: clean this up...
    search_warrants["caseName"] = search_warrants.case_name
    search_warrants["court_id"] = search_warrants.court  # rename this in main DB?
    search_warrants["absolute_url"] = search_warrants.guid.str.split("&").str[
        0
    ]  # rename this in main DB?
    search_warrants["description"] = search_warrants.case_name.replace(
        "USA v.", "Search/Seizure Warrant Returned Executed on 8/5/2020 for"
    )
    category_case_objects = classify_cases_by_searched_object_category(
        ner, search_warrants
    )
    if "no category detected" in category_case_objects:
        del category_case_objects["no category detected"]
    alert_to_log(category_case_objects, "search warrants from PACER RSS")
    if not environ.get("SKIP_SLACK"):
        alert_to_slack(category_case_objects, "search warrants from PACER RSS")

    delete_non_sw_rss_docket_entries()

def delete_non_sw_rss_docket_entries():
    """
    the DB had gotten huge, with 13+ GB of random PACER RSS entries 
    that weren't search warrants or otherwise useful. this deletes them.
    """
    if environ.get("SKIPDB"):
        return
    session = Session()
    session.execute("""
                    delete from rss_docket_entries using (
                        select case_number, pub_date 
                        from rss_docket_entries 
                        
                        except 
                    
                        select case_number, pub_date 
                        from rss_docket_entries 
                        join predictions using (case_number, pub_date)
                    ) sw where 
                    rss_docket_entries.pub_date = sw.pub_date and 
                    rss_docket_entries.case_number = sw.case_number;""")
    session.commit()

def classify_cases_by_searched_object_category(ner, search_warrants_df):
    """
    depends on the following columns in sthe search_warrants_df dataframe:
        - description (for classification)
        - caseName, only for printing
        - court_id, only for printing
        - absolute_url, only for printing
    """
    category_case_objects = {}  # {"caseName", "court_id", "absolute_url"}

    for i, doc in tqdm(
        search_warrants_df.iterrows(), total=search_warrants_df.shape[0]
    ):
        if len(doc["description"]) == 0:
            log.warn("blank description: {}".format(doc["absolute_url"]))

        sentence_entities = ner.predict(doc["description"])
        if len(sentence_entities) == 0:
            sentence_entities = [(None, "no category detected")]
        else:
            sentence_entities = [
                (entity.text, entity.tag)
                for entity in sentence_entities
                if entity.tag[:2] != "L-"
            ]

        for thing_searched, category in sentence_entities:
            record_ner_prediction(doc, category, thing_searched)
            case_string = "- {}    *{}*".format(doc["caseName"], doc["court_id"])
            if (
                thing_searched
                and thing_searched.replace(" ", "").replace(",", "").lower()
                not in doc["caseName"].replace(" ", "").replace(",", "").lower()
            ):
                case_string += "\n  " + thing_searched
            case_string_with_url = case_string + "\n  " + doc["absolute_url"]

            case_object = {
                "case_name": doc["caseName"],
                "thing_searched": thing_searched,
                "court_id": doc["court_id"],
                "absolute_url": doc["absolute_url"],
                "category": category,
                "document_type": doc["document_type"]
            }

            category_case_objects[category] = category_case_objects.get(category, {})
            if case_string not in category_case_objects[category]:
                category_case_objects[category][case_string] = case_object

    return category_case_objects


if __name__ == "__main__":
    Base.metadata.create_all(ENGINE)

    alert_based_on_pacer_rss()
