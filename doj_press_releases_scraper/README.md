1. get a list of all press releases `pipenv run scrapy runspider doj/spiders/press_release_index.py  -o doj_press_releases/urls.csv -t csv`
2. get the contents of each press release `pipenv run scrapy runspider doj/spiders/documents.py  -o docs.csv -t csv`
3. get the documents linked from each press release `pipenv run python pdfs.py`