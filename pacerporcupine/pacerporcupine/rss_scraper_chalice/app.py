from datetime import datetime
from os import environ
from urllib.parse import urlparse, parse_qs
from time import mktime
from html import unescape

import feedparser
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from bs4 import BeautifulSoup
from chalice import Chalice

engine = create_engine(environ.get("DATABASE_URL"))
app = Chalice(app_name="rss_scraper_chalice")

courts = [
    "almd",
    "alsd",
    "akd",
    "azd",
    "ared",
    "arwd",
    "cacd",
    "cand",
    "casd",
    "cod",
    "ctd",
    "ded",
    "dcd",
    "flmd",
    "flsd",
    "gamd",
    "gud",
    "idd",
    "ilcd",
    "ilnd",
    "innd",
    "insd",
    "iand",
    "iasd",
    "ksd",
    "kywd",
    "laed",
    "lamd",
    "lawd",
    "med",
    "mad",
    "mied",
    "miwd",
    "mnd",
    "mssd",
    "moed",
    "mowd",
    "mtd",
    "ned",
    "nvd",
    "nhd",
    "njd",
    "nmd",
    "nyed",
    "nynd",
    "nysd",
    "nced",
    "ncmd",
    "ncwd",
    "nmid",
    "ohnd",
    "ohsd",
    "okwd",
    "ord",
    "paed",
    "pawd",
    "prd",
    "rid",
    # "sdd",
    "tned",
    "tnmd",
    "txed",
    "txsd",
    "txwd",
    "utd",
    "vtd",
    "vid",
    "vawd",
    "waed",
    "wawd",
    "wvnd",
    "wvsd",
    "wied",
    "wiwd",
    "wyd",
]

bankruptcy_courts = [
    "almb",
    "alnb",
    "alsb",
    "akb",
    "azb",
    "areb",
    "cacb",
    "caeb",
    "canb",
    "casb",
    "cob",
    "ctb",
    "deb",
    "dcb",
    "flmb",
    "flnb",
    "flsb",
    "gamb",
    "ganb",
    "gasb",
    "hib",
    "ilcb",
    "ilnb",
    "ilsb",
    "innb",
    "insb",
    "ianb",
    "iasb",
    "ksb",
    "kyeb",
    "kywb",
    "laeb",
    "lamb",
    "lawb",
    "meb",
    "mdb",
    "mab",
    "mieb",
    "miwb",
    "mnb",
    "msnb",
    "mssb",
    "moeb",
    "mtb",
    "neb",
    "nvb",
    "nhb",
    "njb",
    "nmb",
    "nyeb",
    "nynb",
    "nysb",
    "nywb",
    "nceb",
    "ncmb",
    "ncwb",
    "ndb",
    "ohnb",
    "ohsb",
    "okeb",
    "oknb",
    "okwb",
    "orb",
    "paeb",
    "pamb",
    "pawb",
    "prb",
    "rib",
    "scb",
    "sdb",
    "tneb",
    "tnmb",
    "tnwb",
    "txeb",
    "txnb",
    "txwb",
    "utb",
    "vtb",
    "vaeb",
    "vawb",
    "waeb",
    "wawb",
    "wvnb",
    "wvsb",
    "wieb",
    "wiwb",
    "wyb"
]

# TODO: import from pacerporcupine.db
Base = declarative_base()
Session = sessionmaker(bind=engine)


class RSSDocketEntry(Base):
    __tablename__ = "rss_docket_entries"
    __table_args__ = (
        # this can be db.PrimaryKeyConstraint if you want it to be a primary key
        UniqueConstraint("case_number", "pub_date"),
    )

    title = Column(String)
    case_number = Column(String, primary_key=True)
    case_name = Column(String)
    docket_id = Column(Integer)
    description = Column(String)
    document_type = Column(String)
    guid = Column(String)
    pub_date = Column(DateTime, primary_key=True)
    court = Column(String)
    scrape_date = Column(DateTime)
    docket_entry_seq_num = Column(Integer)
    docket_entry_num = Column(Integer)


def scrape_court(court):
    session = Session()
    try:
        feed = feedparser.parse(
            f"https://ecf.{court}.uscourts.gov/cgi-bin/rss_outside.pl"
        )
    except ConnectionRefusedError:
        return
    for entry in feed.entries:
        description = unescape(
            entry["description"]
        )  # [~Util - Modify Hearings/Deadlines (Full List)] (<a href="https://ecf.txnd.uscourts.gov/doc1/177114116288?caseid=339097&de_seq_num=155" >46</a>)
        document_type = description.split("(", 1)[0].strip().lstrip("[").rstrip("]")
        title = unescape(entry["title"])
        if "(<a" in description:
            document_link = description.split("(", 1)[1][:-1]  # maybe None
            document_link_soup = BeautifulSoup(document_link, "html.parser").find_all(
                "a"
            )[0]
            parsed_query_string = parse_qs(urlparse(document_link_soup["href"]).query)
            docket_entry_seq_num = (
                parsed_query_string["de_seq_num"][0]
                if "de_seq_num" in parsed_query_string
                else None
            )
            try: 
                docket_entry_num = int(document_link_soup.get_text())
            except ValueError:
                print(f"couldn't parse docket_entry_num int from {document_link_soup}")
                docket_entry_num = None
        else:
            document_link = None
            document_link_soup = None
            docket_entry_seq_num = None
            docket_entry_num = None

        entry_obj = RSSDocketEntry(
            title=title,
            case_number=title.split(" ", 1)[0],
            case_name=title.split(" ", 1)[1] if " " in title else None,
            docket_id=entry["link"].split("?")[-1],
            document_type=document_type,
            description=description,
            docket_entry_seq_num=docket_entry_seq_num,
            docket_entry_num=docket_entry_num,
            guid=entry["guid"],
            pub_date=datetime.fromtimestamp(mktime(entry.published_parsed)),
            scrape_date=datetime.now(),
            court=court,
        )
        session.merge(entry_obj)
    session.commit()


# Automatically runs every two hours minutes
# @app.schedule("cron(0 8-22/2 ? * MON-FRI *)")
def scrape_all_courts(event, ctx=None):
    # visit each one's RSS feed
    Base.metadata.create_all(engine)

    for court in courts + bankruptcy_courts:
        scrape_court(court)


for i, court in enumerate(courts + bankruptcy_courts):
    exec(
        """
@app.schedule("cron({} 8-22/1 ? * MON-FRI *)")
def scrape_{}(event):
    scrape_court("{}")

    """.format(
            int(i / 2), court, court
        )
    )

if __name__ == "__main__":
    for court in bankruptcy_courts:
#        locals()[f"scrape_{court}"](
        scrape_all_courts(
            {
                "version": "0",
                "id": "53dc4d37-cffa-4f76-80c9-8b7d4a4d2eaa",
                "detail-type": "Scheduled Event",
                "source": "aws.events",
                "account": "123456789012",
                "time": "2015-10-08T16:53:06Z",
                "region": "us-east-1",
                "resources": [
                    "arn:aws:events:us-east-1:123456789012:rule/my-scheduled-rule"
                ],
                "detail": {},
            },
            {},
        )

    #
