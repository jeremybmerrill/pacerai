from random import random
test_proportion = 0.1
dev_proportion = 0.1
train_proportion = 1.0 - test_proportion - dev_proportion
test_proportion_inverse = 1.0 - test_proportion

with open(
    "rss-ner-at-2021-06-07-19-09-30217966.train.conll", "w"
) as ftrain:  # FLAIR input format
    with open(
        "rss-ner-at-2021-06-07-19-09-30217966.dev.conll", "w"
    ) as fdev:  # FLAIR input format
        with open(
            "rss-ner-at-2021-06-07-19-09-30217966.test.conll", "w"
        ) as ftest:  # FLAIR input format
            with open("rss-ner-at-2021-06-07-19-09-30217966.conll", 'r') as input_file:
                examples = input_file.read().split("\n\n")
                examples = [[tag.split(" ", 3) for tag in example.split("\n") if '-DOCSTART-' not in tag] for example in examples]


            for eg in examples:
                if eg == [[""]]:
                    continue
                r = random()
                f = ftrain if r < train_proportion else (fdev if r < test_proportion_inverse else ftest)
                for i, (tok, _, _, tag) in enumerate(eg):
                    if tag[0] == "L": # spacy produces BILUO tags. Flair supports BIOES tags. ugh.
                        tag = "E" + tag[1:]
                    if tag[0] == "U":
                        tag = "S" + tag[1:]
                    if tag[0] == "I" and (len(eg) == (i + 1) or eg[i+1][3] != tag): # LabelStudio doesn't produce End tags, just intermediates after the first.
                        tag = "E" + tag[1:]
                    f.write("{}\t{}\n".format(tok, tag.upper().replace(" ", "_")))
                f.write("\n")
