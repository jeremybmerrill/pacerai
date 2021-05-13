import pandas as pd
from os.path import dirname, join
data = pd.read_csv(join(dirname(__file__), "classifier", "predicted_search_warrants.csv"))


search_warrants = data[data["predicted_search_warrant"] == 1.0]
print(search_warrants.shape[0])
search_warrants["text"] = search_warrants["description"]
search_warrants[["absolute_url", "text", "id"]].to_json(join(dirname(__file__), "ner", "predicted_search_warrants_for_ner.jsonl"), orient="records", lines=True)