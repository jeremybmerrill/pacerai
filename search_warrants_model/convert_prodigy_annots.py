# https://support.prodi.gy/t/ner-format-to-conll/1153/2

from prodigy.components.db import connect
from spacy.gold import biluo_tags_from_offsets
from spacy.lang.en import English   # or whichever language tokenizer you need
from random import random
import csv
import json

nlp = English()

db = connect()  # uses settings from your prodigy.json
examples = db.get_dataset('ner_search_warrant_objects')  # load the annotations

with open("ner_search_warrant_objects.conll", 'w') as f:
    for eg in examples:
        if eg['answer'] != 'accept' or "spans" not in eg:
            continue
        f.write("# {}".format(eg["text"]))
        doc = nlp(eg['text'])
        entities = [(span['start'], span['end'], span['label'] if span["label"] != "OBJ" else "MISC")
                    for span in eg['spans']]
        tags = biluo_tags_from_offsets(doc, entities)
        # do something with the tags here
        for tok, tag in zip(eg['tokens'], tags):
            f.write("{}\t{}\n".format(tok['text'], tag))
        f.write("\n")


with open("ner_search_warrant_objects.train.conll", 'w') as ftrain: # FLAIR input format
    with open("ner_search_warrant_objects.dev.conll", 'w') as fdev: # FLAIR input format
        with open("ner_search_warrant_objects.test.conll", 'w') as ftest: # FLAIR input format
            for eg in examples:
                r = random()
                f = ftrain if r < 0.6 else (fdev if r < 0.8 else ftest)
                if eg['answer'] != 'accept' or "spans" not in eg:
                    continue
                doc = nlp(eg['text'])
                entities = [(span['start'], span['end'], span['label'] if span["label"] != "OBJ" else "MISC")
                            for span in eg['spans']]
                tags = biluo_tags_from_offsets(doc, entities)
                for tok, tag in zip(eg['tokens'], tags):
                    f.write("{}\t{}\n".format(tok['text'], tag))
                f.write("\n")


with open("ner_search_warrant_objects.train.csv", 'w') as ftrain: # not an output format anything can actually use
    with open("ner_search_warrant_objects.dev.csv", 'w') as fdev: # not an output format anything can actually use
        with open("ner_search_warrant_objects.test.csv", 'w') as ftest: # not an output format anything can actually use
            csvtrain = csv.writer(ftrain)
            csvdev = csv.writer(fdev)
            csvtest = csv.writer(ftest)
            csvtrain.writerow(["token","label"])
            csvdev.writerow(["token","label"])
            csvtest.writerow(["token","label"])

            for eg in examples:
                r = random()
                f = csvtrain if r < 0.6 else (csvdev if r < 0.8 else csvtest)
                if eg['answer'] != 'accept' or "spans" not in eg:
                    continue
                doc = nlp(eg['text'])
                entities = [(span['start'], span['end'], span['label'] if span["label"] != "OBJ" else "MISC")
                            for span in eg['spans']]
                tags = biluo_tags_from_offsets(doc, entities)
                for tok, tag in zip(eg['tokens'], tags):
                    f.writerow([tok['text'], tag])
                f.writerow([])

with open("ner_search_warrant_objects.train.json", 'w') as ftrain: # huggingface transformers bert input format
    with open("ner_search_warrant_objects.dev.json", 'w') as fdev: # huggingface transformers bert input format
        with open("ner_search_warrant_objects.test.json", 'w') as ftest: # huggingface transformers bert input format

            for eg in examples:
                r = random()
                f = ftrain if r < 0.8 else (fdev if r < 1 else ftest)
                if eg['answer'] != 'accept' or "spans" not in eg:
                    continue
                doc = nlp(eg['text'])
                entities = [(span['start'], span['end'], span['label'] if span["label"] != "OBJ" else "MISC")
                            for span in eg['spans']]
                tags = biluo_tags_from_offsets(doc, entities)
                f.write(json.dumps({"tokens": [tok["text"] for tok in eg["tokens"]], "tags": tags}) + "\n")