from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
    PrimaryKeyConstraint,
    ForeignKeyConstraint,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import declarative_base, relation, relationship


Base = declarative_base()


class RSSDocketEntry(Base):
    __tablename__ = "rss_docket_entries"
    __table_args__ = (
        # this can be db.PrimaryKeyConstraint if you want it to be a primary key
        PrimaryKeyConstraint("case_number", "pub_date"),
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
    sw_or_not_predictions = relationship(
        "RssSwOrNotPrediction",
        back_populates="rss_docket_entry",
    )
    ner_predictions = relationship(
        "RssNerPrediction",
        back_populates="rss_docket_entry"
    )

class RssNerPrediction(Base):
    __tablename__ = "ner_predictions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["case_number", "pub_date"],
            ["rss_docket_entries.case_number", "rss_docket_entries.pub_date"],
        ),
    )
    id = Column(Integer, primary_key=True)
    case_number = Column(String)
    pub_date = Column(DateTime)
    prediction_type = Column(String)
    prediction_value = Column(String) # category, e.g. "Phone"
    rss_docket_entry = relationship(
        "RSSDocketEntry",
        back_populates="ner_predictions",
    )
    prediction_substring = Column(String) # e.g. "rose gold i-Phone"


class RssSwOrNotPrediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["case_number", "pub_date"],
            ["rss_docket_entries.case_number", "rss_docket_entries.pub_date"],
        ),
    )

    id = Column(Integer, primary_key=True)
    case_number = Column(String)
    pub_date = Column(DateTime)
    prediction_type = Column(String)
    prediction_value = Column(Boolean)
    rss_docket_entry = relationship(
        "RSSDocketEntry",
        back_populates="sw_or_not_predictions",
    )


class CourtListenerNerPrediction(Base):
    __tablename__ = "courtlistener_ner_predictions"
    id = Column(Integer, primary_key=True)
    absolute_url=Column(String)
    prediction_type = Column(String)
    prediction_value = Column(String) # category, e.g. "Phone"
    prediction_substring = Column(String) # e.g. "rose gold i-Phone"

    

class CourtListenerSwOrNotPrediction(Base):
    __tablename__ = "courtlistener_predictions"
    id = Column(Integer, primary_key=True)
    absolute_url=Column(String)
    prediction_type = Column(String)
    prediction_value = Column(Boolean)


if __name__ == "__main__":
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from os.path import environ

    engine = create_engine(environ.get("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
