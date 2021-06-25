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
from sqlalchemy.orm import declarative_base, relationship


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
    predictions = relationship(
        "Prediction",
        back_populates="rss_docket_entry",
    )


class Prediction(Base):
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
        back_populates="predictions",
    )


if __name__ == "__main__":
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine

    engine = create_engine(environ.get("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
