# get models from S3.
from os.path import exists, join, dirname, abspath
from os import makedirs
import boto3


s3 = boto3.client("s3")

S3_BUCKET = "pacerporcupine"

MODEL_FILES = [
    "models/classifier/casename_desc_model/config.json",
    "models/classifier/casename_desc_model/pytorch_model.bin",
    "models/classifier/casename_desc_model/special_tokens_map.json",
    "models/classifier/casename_desc_model/tokenizer_config.json",
    "models/classifier/casename_desc_model/vocab.txt",
    "models/classifier/casename_shortdesc_model/config.json",
    "models/classifier/casename_shortdesc_model/pytorch_model.bin",
    "models/classifier/casename_shortdesc_model/special_tokens_map.json",
    "models/classifier/casename_shortdesc_model/tokenizer_config.json",
    "models/classifier/casename_shortdesc_model/vocab.txt",
    "models/flairner/final-model-20210607.pt",
]


def ensure_model_exists(model_file_fragment):
    filepath = abspath(join("/tmp/pacerporcupine/", model_file_fragment))
    if not exists(filepath):
        print(
            "downloading {}/{} to {}".format(S3_BUCKET, model_file_fragment, filepath)
        )
        makedirs(dirname(filepath), exist_ok=True)
        s3.download_file(S3_BUCKET, model_file_fragment, filepath)


def ensure_models_exist(matching=None):
    print("ensure_models_exist", matching)
    for model_file_fragment in MODEL_FILES:
        if not matching or matching in model_file_fragment:
            ensure_model_exists(model_file_fragment)
