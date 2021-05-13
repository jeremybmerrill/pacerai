from datetime import datetime, timedelta
import csv
import logging
from os.path import join, dirname
from os import environ
import json

from tqdm import tqdm
import pandas as pd
import numpy as np
from scipy.special import softmax
from flair.models import SequenceTagger
from flair.data import Sentence
from torch import tensor, device, no_grad
from torch import long as torch_long
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from transformers import BertTokenizer
from transformers import BertForSequenceClassification, AdamW, BertConfig
import requests

# from keras.preprocessing.sequence import pad_sequences

from pacerporcupine import courtlistener
from pacerporcupine.models import fetch

MAX_DESCRIPTION_LENGTH = 64
my_device = device("cpu")

DAYS_BACK = 7
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NamedEntityRecognizer:
    def __init__(self, model_path):
        fetch.ensure_model_exists(
            model_path.replace("/tmp/pacerporcupine/", "").strip("/")
        )
        self.ner_model = SequenceTagger.load(model_path)


class Classifier:
    def __init__(self, model_path, tokenizer_path=None):
        fetch.ensure_models_exist(
            model_path.replace("/tmp/pacerporcupine/", "").strip("/")
        )
        self.tokenizer = BertTokenizer.from_pretrained(
            tokenizer_path if tokenizer_path else model_path
        )
        self.model = BertForSequenceClassification.from_pretrained(model_path)

    def predict(self, dataframe_of_texts, text_column_name, batch_size=32):
        dataframe_of_texts["input_ids"] = dataframe_of_texts[text_column_name].apply(
            lambda sent: self.tokenizer.encode(
                sent,  # Sentence to encode.
                add_special_tokens=True,  # Add '[CLS]' and '[SEP]'
                # This function also supports truncation and conversion
                # to pytorch tensors, but we need to do padding, so we
                # can't use these features :( .
                # max_length = 128,          # Truncate all sentences.
                # return_tensors = 'pt',     # Return pytorch tensors.
            )
        )
        # dataframe_of_texts.input_ids = pad_sequences( # for the Keras version
        #     dataframe_of_texts.input_ids,
        #     maxlen=MAX_DESCRIPTION_LENGTH,
        #     dtype="long",
        #     value=0,
        #     truncating="post",
        #     padding="post",
        # ).tolist()
        # padding and truncating. equivalent of above, but minus Keras dependency.
        dataframe_of_texts.input_ids = [
            list_of_input_ids[0:MAX_DESCRIPTION_LENGTH]
            for list_of_input_ids in dataframe_of_texts.input_ids
        ]
        dataframe_of_texts.input_ids = [
            tensor(
                list_of_input_ids
                + [0.0] * (MAX_DESCRIPTION_LENGTH - len(list_of_input_ids)),
                dtype=torch_long,
            )
            for list_of_input_ids in dataframe_of_texts.input_ids
        ]

        dataframe_of_texts["attention_masks"] = dataframe_of_texts.input_ids.apply(
            lambda sent: list([int(token_id > 0) for token_id in sent])
        )

        prediction_inputs = tensor(np.stack(dataframe_of_texts.input_ids, axis=0))
        prediction_labels = tensor(
            np.stack(np.zeros_like(dataframe_of_texts.index), axis=0)
        )  # these are just dummies
        prediction_masks = tensor(np.stack(dataframe_of_texts.attention_masks, axis=0))

        prediction_data = TensorDataset(
            prediction_inputs, prediction_masks, prediction_labels
        )
        prediction_sampler = SequentialSampler(prediction_data)
        prediction_dataloader = DataLoader(
            prediction_data, sampler=prediction_sampler, batch_size=batch_size
        )

        self.model.eval()
        predictions = []
        for batch in prediction_dataloader:
            # Add batch to GPU
            batch = tuple(t.to(my_device) for t in batch)

            # Unpack the inputs from our dataloader
            b_input_ids, b_input_mask, b_labels = batch

            # Telling the model not to compute or store gradients, saving memory and
            # speeding up prediction
            with no_grad():
                # Forward pass, calculate logit predictions
                outputs = self.model(
                    b_input_ids, token_type_ids=None, attention_mask=b_input_mask
                )

            logits = outputs[0]

            # Move logits and labels to CPU
            logits = logits.detach().cpu().numpy()
            label_ids = b_labels.to("cpu").numpy()

            # Store predictions and true labels
            predictions.append(logits)
            # true_labels.append(label_ids)
        predictions = np.concatenate(predictions)

        dataframe_of_texts["predicted_class"] = np.argmax(predictions, axis=1).tolist()
        dataframe_of_texts["likelihood"] = np.transpose(softmax(predictions, axis=1))[1]
        return dataframe_of_texts


def alert(start_date=None):
    casename_desc_classifier = Classifier(
        join(
            dirname(__file__),
            "/tmp/pacerporcupine/models/classifier/casename_desc_model/",
        )
    )
    ner = NamedEntityRecognizer(
        join(
            dirname(__file__),
            "/tmp/pacerporcupine/models/flairner/final-model-20210429.pt",
        )
    )

    start_date = start_date or (datetime.today() - timedelta(days=7)).strftime(
        "%m/%d/%Y"
    )

    docs = courtlistener.find_search_warrant_documents_by_description(
        n=500, filed_after=start_date, available_only=False
    )
    docs_df = pd.DataFrame(docs)

    log.info("found {} possible search warrants".format(docs_df.shape[0]))
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
    category_cases = classify_cases_by_searched_object_category(ner, search_warrants)
    alert_to_log(category_cases)
    alert_to_slack(category_cases)
    return {"okee": "dokee"}


def alert_to_slack(category_cases):
    if environ.get("SLACKWH"):
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


def alert_to_log(category_cases):
    for i, category in enumerate(category_cases.keys()):
        cases = category_cases[category]  # a dict of case names to case names + URLs
        print(category)
        for case in cases.values():
            print(case)
        print("")
        if i + 1 != len(category_cases.keys()):
            print("----------------------")
            print("")


def classify_cases_by_searched_object_category(ner, search_warrants):
    category_cases = {}

    for i, doc in tqdm(search_warrants.iterrows(), total=search_warrants.shape[0]):
        if len(doc["description"]) == 0:
            log.warn(
                "blank description: {}".format(
                    "https://www.courtlistener.org" + doc["absolute_url"]
                )
            )
        sentence = Sentence(doc["description"])
        ner.ner_model.predict(sentence)
        sentence_entities = sentence.get_spans("ner")
        if len(sentence_entities) > 0:
            for entity in sentence_entities:
                thing_searched = entity.text
                category = entity.tag
                if category[:2] == "L-":  # entity continuations
                    continue
                case_string = "- {}    {}".format(doc["caseName"], doc["court_id"])
                if (
                    thing_searched.replace(" ", "").replace(",", "").lower()
                    not in doc["caseName"].replace(" ", "").replace(",", "").lower()
                ):
                    case_string += "\n  " + thing_searched
                case_string_with_url = (
                    case_string
                    + "\n  "
                    + "https://www.courtlistener.com{}".format(doc["absolute_url"])
                )

                category_cases[category] = category_cases.get(category, {})
                if case_string not in category_cases[category]:
                    category_cases[category][case_string] = case_string_with_url
        else:
            case_string = "- {}    {}".format(doc["caseName"], doc["court_id"])
            case_string_with_url = (
                case_string
                + "\n  "
                + "https://www.courtlistener.com{}".format(doc["absolute_url"])
            )

            category = "no category detected"
            category_cases[category] = category_cases.get(category, {})
            if case_string not in category_cases[category]:
                category_cases[category][case_string] = case_string_with_url
    return category_cases


if __name__ == "__main__":
    alert()
