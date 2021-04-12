from datetime import datetime
from os import environ
from urllib.parse import urlparse, parse_qs
from time import mktime

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
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

engine = create_engine(environ.get("DATABASE_URL"))

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


def scrape_all_courts(event=None, lambda_context=None):
    # visit each one's RSS feed
    Base.metadata.create_all(engine)

    session = Session()
    for court in courts:
        try:
            feed = feedparser.parse(
                f"https://ecf.{court}.uscourts.gov/cgi-bin/rss_outside.pl"
            )
        except ConnectionRefusedError:
            continue
        for entry in feed.entries:
            description = entry[
                "description"
            ]  # [~Util - Modify Hearings/Deadlines (Full List)] (<a href="https://ecf.txnd.uscourts.gov/doc1/177114116288?caseid=339097&de_seq_num=155" >46</a>)
            document_type = description.split("(", 1)[0].strip().lstrip("[").rstrip("]")
            print(entry)
            if "(<a" in description:
                document_link = description.split("(", 1)[1][:-1]  # maybe None
                document_link_soup = BeautifulSoup(
                    document_link, "html.parser"
                ).find_all("a")[0]
                parsed_query_string = parse_qs(
                    urlparse(document_link_soup["href"]).query
                )
                docket_entry_seq_num = (
                    parsed_query_string["de_seq_num"][0]
                    if "de_seq_num" in parsed_query_string
                    else None
                )
                docket_entry_num = document_link_soup.get_text()
            else:
                document_link = None
                document_link_soup = None
                docket_entry_seq_num = None
                docket_entry_num = None

            entry_obj = RSSDocketEntry(
                title=entry["title"],
                case_number=entry["title"].split(" ", 1)[0],
                case_name=entry["title"].split(" ", 1)[1]
                if " " in entry["title"]
                else None,
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


if __name__ == "__main__":
    scrape_all_courts(None, None)
