from random import random

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
                f = ftrain if r < 0.6 else (fdev if r < 0.8 else ftest)
                print(eg)
                for tok, _, _, tag in eg:
                    if tag[0] == "L": # spacy produces BILUO tags. Flair supports BIOES tags. ugh.
                        tag = "E" + tag[1:]
                    if tag[0] == "U":
                        tag = "S" + tag[1:]                    
                    f.write("{}\t{}\n".format(tok, tag))
                f.write("\n")
