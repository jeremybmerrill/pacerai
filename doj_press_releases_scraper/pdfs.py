import csv
import requests
from os import makedirs
from os.path import exists, dirname
from time import sleep

with open("docs.csv") as csvfile:
    with open("docs_with_pdfs.csv", "w") as outcsv:
        outwriter = csv.writer(outcsv)
        outwriter.writerow(["date", "title", "doc_url", "host_url", "pdf"])
        for i, row in enumerate(csv.DictReader(csvfile)):
            try:
                id = row["doc_url"].split("/")[-2]
            except IndexError:
                print('can\'t find ID (split("/")[-2]): {}'.format(row["doc_url"]))
                continue
            press_release_slug = row["host_url"].split("/")[-1]
            filename = "pdfs/{}/{}.pdf".format(press_release_slug, id)
            makedirs(dirname(filename), exist_ok=True)
            if not exists(filename):
                resp = requests.get(row["doc_url"])

                with open(filename, "wb") as f:
                    f.write(resp.content)
                sleep(5)
            outwriter.writerow(
                [row[k] for k in ["date", "title", "doc_url", "host_url"]] + [filename]
            )
