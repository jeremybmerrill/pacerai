# https://support.prodi.gy/t/ner-format-to-conll/1153/2

from prodigy.components.db import connect
from spacy.gold import biluo_tags_from_offsets
from spacy.lang.en import English  # or whichever language tokenizer you need
from random import random
import csv
import json

print("you'll erase manually-edited conlls, be careful")
return 

nlp = English()

db = connect()  # uses settings from your prodigy.json
examples = db.get_dataset("ner_search_warrant_objects")  # load the annotations

with open('searched-object-classifications.csv', 'r') as f:
    object_classifications = {row["token"]: row["label"].upper().replace(" ", "_") for row in csv.DictReader(f)}


test_proportion = 0.1
dev_proportion = 0.1
train_proportion = 1.0 - test_proportion - dev_proportion
test_proportion_inverse = 1.0 - test_proportion

def eg_to_tags(eg):
    doc = nlp(eg["text"])
    entities = [
        (
            span["start"],
            span["end"],
            span["label"] if span["label"] != "OBJ" else object_classifications.get(eg["text"][span["start"]:span["end"]], "MISC"),
        )
        for span in eg["spans"]
    ]
    tags = biluo_tags_from_offsets(doc, entities)
    return tags

# generating a CSV 
with open('ner_training_data_tokens_to_classify.csv', 'w') as csvfile:
    entity_writer = csv.writer(csvfile)
    entity_writer.writerow(["token", "label"])
    for eg in examples:
        if eg["answer"] != "accept" or "spans" not in eg:
            continue
        for span in eg["spans"]:
            entity_text = eg["text"][span["start"]:span["end"]]
            entity_writer.writerow([entity_text, ''])
            
# with open("ner_search_warrant_objects.conll", "w") as f:
#     for eg in examples:
#         if eg["answer"] != "accept" or "spans" not in eg:
#             continue
#         f.write("# {}\n".format(eg["text"]))
#         tags = eg_to_tags(eg)
#         # do something with the tags here
#         for tok, tag in zip(eg["tokens"], tags):
#             if tag[0] == "L": # spacy produces BILUO tags. Flair supports BIOES tags. ugh.
#                 tag = "E" + tag[1:] # Flair might not care about End/Last though. So let's try with I-
#             if tag[0] == "U":
#                 tag = "S" + tag[1:]
#             f.write("{}\t{}\n".format(tok["text"], tag))
#         f.write("\n")

with open(
    "ner_search_warrant_objects.train.conll", "w"
) as ftrain:  # FLAIR input format
    with open(
        "ner_search_warrant_objects.dev.conll", "w"
    ) as fdev:  # FLAIR input format
        with open(
            "ner_search_warrant_objects.test.conll", "w"
        ) as ftest:  # FLAIR input format
            for eg in examples:
                r = random()
                f = ftrain if r < train_proportion else (fdev if r < test_proportion_inverse else ftest)
                if eg["answer"] != "accept" or "spans" not in eg:
                    continue

                # data augmentation, so to speak
                if "as to" in ' '.join([t["text"] for t in eg["tokens"]]):
                    tags = eg_to_tags(eg)
                    prev_token_text = None
                    have_seen_as_to = False
                    for tok, tag in zip(eg["tokens"], tags):
                        if (not have_seen_as_to) and not (prev_token_text == "as" and tok["text"] == "to"):
                            prev_token_text = tok["text"]
                            continue
                        elif (prev_token_text == "as" and tok["text"] == "to"):
                            have_seen_as_to = True
                            f.write("{}\t{}\n".format("USA", "O"))
                            f.write("{}\t{}\n".format("v.", "O"))
                        else:
                            if tag[0] == "L": # spacy produces BILUO tags. Flair supports BIOES tags. ugh.
                                tag = "E" + tag[1:]
                            if tag[0] == "U":
                                tag = "S" + tag[1:]
                            prev_token_text = tok["text"]
                            f.write("{}\t{}\n".format(tok["text"], tag))
                    f.write("\n")


                tags = eg_to_tags(eg)
                for tok, tag in zip(eg["tokens"], tags):
                    if tag[0] == "L": # spacy produces BILUO tags. Flair supports BIOES tags. ugh.
                        tag = "E" + tag[1:]
                    if tag[0] == "U":
                        tag = "S" + tag[1:]                    
                    f.write("{}\t{}\n".format(tok["text"], tag))
                f.write("\n")


# with open(
#     "ner_search_warrant_objects.train.csv", "w"
# ) as ftrain:  # not an output format anything can actually use
#     with open(
#         "ner_search_warrant_objects.dev.csv", "w"
#     ) as fdev:  # not an output format anything can actually use
#         with open(
#             "ner_search_warrant_objects.test.csv", "w"
#         ) as ftest:  # not an output format anything can actually use
#             csvtrain = csv.writer(ftrain)
#             csvdev = csv.writer(fdev)
#             csvtest = csv.writer(ftest)
#             csvtrain.writerow(["token", "label"])
#             csvdev.writerow(["token", "label"])
#             csvtest.writerow(["token", "label"])

#             for eg in examples:
#                 r = random()
#                 f = csvtrain if r < train_proportion else (csvdev if r < test_proportion_inverse else csvtest)
#                 if eg["answer"] != "accept" or "spans" not in eg:
#                     continue
#                 tags = eg_to_tags(eg)
#                 for tok, tag in zip(eg["tokens"], tags):
#                     f.writerow([tok["text"], tag])
#                 f.writerow([])

# with open(
#     "ner_search_warrant_objects.train.json", "w"
# ) as ftrain:  # huggingface transformers bert input format
#     with open(
#         "ner_search_warrant_objects.dev.json", "w"
#     ) as fdev:  # huggingface transformers bert input format
#         with open(
#             "ner_search_warrant_objects.test.json", "w"
#         ) as ftest:  # huggingface transformers bert input format

#             for eg in examples:
#                 r = random()
#                 f = ftrain if r < test_proportion_inverse else (fdev if r < 1 else ftest)
#                 if eg["answer"] != "accept" or "spans" not in eg:
#                     continue
#                 tags = eg_to_tags(eg)
#                 f.write(
#                     json.dumps(
#                         {"tokens": [tok["text"] for tok in eg["tokens"]], "tags": tags}
#                     )
#                     + "\n"
#                 )
