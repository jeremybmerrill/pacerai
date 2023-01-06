from datetime import datetime, timedelta
import logging
from os.path import join, dirname
from os import environ

from tqdm import tqdm
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pacerporcupine import courtlistener
from pacerporcupine.models.classifier import Classifier
from pacerporcupine.models.named_entity_recognizer import NamedEntityRecognizer
from pacerporcupine.alerter import alert_to_log, alert_to_slack
from pacerporcupine.db import CourtListenerSwOrNotPrediction, Base, CourtListenerNerPrediction

load_dotenv()

DAYS_BACK = 800  # because these are DATEs not DATETIMEs, looking back a single day only gets us stuff filed TODAY which isn't necessarily what we want.
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

ENGINE = create_engine(environ.get("LIVE_DATABASE_URL"))
Session = sessionmaker(bind=ENGINE)

SEARCH_WARRANT_OR_NOT_PREDICTION_TYPE = "swornot_recap"
SEARCH_WARRANT_OBJECT_NER_PREDICTION_TYPE = "swobjectner_recap"


def get_search_warrant_metadata_from_courtlistener():
    pass

def record_swornot_prediction(record):
    if environ.get("SKIPDB"):
        return
    session = Session()
    pred = CourtListenerSwOrNotPrediction(
        absolute_url=record["absolute_url"],
        prediction_type=SEARCH_WARRANT_OR_NOT_PREDICTION_TYPE,
        prediction_value=record["predicted_class"],
    )

    session.add(pred)
    session.commit()


def record_ner_prediction(record, category, thing_searched):
    print(record)
    if environ.get("SKIPDB"):
        return
    session = Session()
    pred = CourtListenerNerPrediction(
        absolute_url=record["absolute_url"],
        prediction_type=SEARCH_WARRANT_OBJECT_NER_PREDICTION_TYPE,
        prediction_value=category,
        prediction_substring=thing_searched
    )

    session.add(pred)
    session.commit()

def url_exists_in_db(absolute_url, session):
    return session.query(CourtListenerSwOrNotPrediction).filter(CourtListenerSwOrNotPrediction.absolute_url==absolute_url).count() > 0


def alert_from_courtlistener_api(start_date=None):
    casename_desc_classifier = Classifier(
        join(
            dirname(__file__),
            "/tmp/pacerporcupine/models/classifier/casename_desc_model/",
        )
    )
    ner = NamedEntityRecognizer(
        join(
            dirname(__file__),
            "/tmp/pacerporcupine/models/flairner/best-model.pt",
        )
    )

    start_date = start_date or (datetime.today() - timedelta(days=DAYS_BACK)).strftime(
        "%m/%d/%Y"
    )

    docs = courtlistener.find_search_warrant_documents_by_description(
        n=500, filed_after=start_date, available_only=False
    )
    if len(docs) == 0:
        return {"okee": "dokee"}
    docs_df = pd.DataFrame(docs)
    docs_df[
        "absolute_url"
    ] = "https://www.courtlistener.com" + docs_df.absolute_url.astype("str")

    with Session() as session:
        docs_df["exists_in_db"] = docs_df.absolute_url.apply(lambda url: url_exists_in_db(url, session))
    docs_df = docs_df[~docs_df["exists_in_db"]].copy()

    log.info("found {} possible search warrants".format(docs_df.shape[0]))
    if len(docs_df) == 0:
        return {"okee": "dokee"}
    docs_df["to_classify"] = docs_df.caseName + " " + docs_df.description
    docs_df = casename_desc_classifier.predict(
        docs_df, "description"
    )  # TODO: why does "description" work better than "to_classify"???
    search_warrants = docs_df[docs_df["predicted_class"] == 1]
    log.info(
        "of which, {} are search warrants according to the model".format(
            search_warrants.shape[0]
        )
    )
    docs_df[["absolute_url", "predicted_class"]].apply(
        record_swornot_prediction, axis=1
    )

    category_case_objects = classify_cases_by_searched_object_category(
        ner, search_warrants
    )
    alert_to_log(category_case_objects, "search warrants from the CourtListener API")
    if not environ.get("SKIP_SLACK"):
        alert_to_slack(
            category_case_objects, "search warrants from the CourtListener API"
        )
    with open("category_case_objects_courtlistener.json", 'w') as f: 
        import json
        f.write(json.dumps(category_case_objects, indent=4, sort_keys=True))
    return {"okee": "dokee"}


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
                "description": doc["description"],
                "thing_searched": thing_searched,
                "court_id": doc["court_id"],
                "absolute_url": doc["absolute_url"],
                "category": category,
            }

            category_case_objects[category] = category_case_objects.get(category, {})
            if case_string not in category_case_objects[category]:
                category_case_objects[category][case_string] = case_object

    return category_case_objects


if __name__ == "__main__":
    Base.metadata.create_all(ENGINE)
    alert_from_courtlistener_api()
