from flair.models import SequenceTagger
from flair.data import Sentence

from pacerporcupine.models import fetch


class NamedEntityRecognizer:
    def __init__(self, model_path):
        fetch.ensure_models_exist(
            model_path.replace("/tmp/pacerporcupine/", "").strip("/")
        )
        self.ner_model = SequenceTagger.load(model_path)

    def predict(self, sentence_str):
        sentence = Sentence(sentence_str)
        self.ner_model.predict(sentence)
        return sentence.get_spans("ner")


if __name__ == "__main__":
    ner = NamedEntityRecognizer("/tmp/pacerporcupine/models/flairner/best-model.pt")
    sentence_entities = ner.predict("USA v. Snapchat Account")

