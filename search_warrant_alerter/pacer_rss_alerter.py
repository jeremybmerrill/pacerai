from pacerporcupine.pacer_rss_search_warrant_alerter.alert import (
    alert_based_on_pacer_rss,
)
from pacerporcupine.db import Base


def handler(event, context):

    # TODO: extract start date?
    Base.metadata.create_all(ENGINE)

    alert_based_on_pacer_rss()


if __name__ == "__main__":
    handler(
        {},
        {},
    )
