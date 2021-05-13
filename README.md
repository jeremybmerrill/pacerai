# pacer experimentation

Subprojects:

## Search warrants

1. downloaded 1000 RECAP documents that matched the phrase 'search warrant' in courtlistener recap data experimentation.ipynb, to search_warrants.csv
2. hand-coded 299 of those as to whether they're search warrants or not, in https://docs.google.com/spreadsheets/d/1gyYAlYdL9o45pPIC0POXzKwvO5Ji7SZ9uwP46uXfMqA/edit#gid=807616356
3. trained a BERT classifier model that seems to work well using the `description` field at https://colab.research.google.com/drive/16l_Fr9d9oLrGPz7cQwtD5Z3sJGsHQagD#scrollTo=2QR9UdtmiGbs. the model is in this directory, and the results are too.
4. glue script search_warrants_csv_to_jsonl.py to turn the document `description` and IDs into the prodigy input format.
6. hand-code for NER with prodigy...: 
   a. `prodigy ner.manual ner_search_warrant_objects en_core_web_md ./ner/predicted_search_warrants_for_ner.jsonl --label OBJ` 
   b. `prodigy ner.batch-train ner_search_warrant_objects search_warrant_ner_model -n 30 -es 0.5 -o search_warrant_ner_model` 
   c. `prodigy ner.teach ner_search_warrant_objects search_warrant_ner_model ./ner/predicted_search_warrants_for_ner.jsonl --label OBJ`
   d. the model itself did poorly. (tops out at 0.288), so I'm going to export the annotations and try to train it in BERT.
7. prodigy db-out ner_search_warrant_objects > ner_search_warrant_objects.jsonlner_search_warrant_objects.jsonl
6. train a NER model maybe with BERT, maybe with prodigy/spacy.
    - https://huggingface.co/transformers/v2.2.0/examples.html#named-entity-recognition
    - https://www.depends-on-the-definition.com/named-entity-recognition-with-bert/ (old)
    - https://gab41.lab41.org/how-to-fine-tune-bert-for-named-entity-recognition-2257b5e5ce7e
    - https://github.com/flairNLP/flair/blob/master/resources/docs/TUTORIAL_7_TRAINING_A_MODEL.md (alternative framewokr)
8. python convert_prodigy_annots.py
9. manually put some of teh annots in ner_search_warrant_objects.dev.conll and some in ner_search_warrant_objects.train.conll (copy-pasted 15k lines into .train.conll, remaining 5k in .dev.conll)
10. BERT: https://colab.research.google.com/drive/1AsvDvSuGx-N3XoDLGuqG7MnszVuBNKyv#scrollTo=uhvt_y-4gKjP (depends on custom run_ner.py in this directory here)
    FLAIR: https://colab.research.google.com/drive/1bK5lsugjEX6X4QdGFmeA4KglUPQaRuPh#scrollTo=79q5hRTtHNRq
11. FLAIR downloaded to `search_warrants_model/*.pt` (final-model-20210429.pt et seq. have multiple types of objects to get.)


### here's an example RECAP page w/o any downloaded docs.
https://www.courtlistener.com/docket/14901901/search-warrant/