from transformers import BertTokenizer
from transformers import BertForSequenceClassification, AdamW, BertConfig
from torch.nn.utils.rnn import pad_sequence
from torch import tensor, device, no_grad
from torch import long as torch_long
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from scipy.special import softmax
import numpy as np

from pacerporcupine.models import fetch

my_device = device("cpu")
MAX_DESCRIPTION_LENGTH = 64


def pad_sequences(myseries):
    """
    padding and truncating,

    equiv of the below, but minus Keras dependency.

    # from keras.preprocessing.sequence import pad_sequences
    # dataframe_of_texts.input_ids = pad_sequences( # for the Keras version
    #     dataframe_of_texts.input_ids,
    #     maxlen=MAX_DESCRIPTION_LENGTH,
    #     dtype="long",
    #     value=0,
    #     truncating="post",
    #     padding="post",
    # ).tolist()
    """

    myseries = [
        list_of_input_ids[0:MAX_DESCRIPTION_LENGTH] for list_of_input_ids in myseries
    ]
    return [
        tensor(
            list_of_input_ids
            + [0.0] * (MAX_DESCRIPTION_LENGTH - len(list_of_input_ids)),
            dtype=torch_long,
        )
        for list_of_input_ids in myseries
    ]


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
            )
        )
        dataframe_of_texts["input_ids"] = pad_sequences(dataframe_of_texts.input_ids)

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
