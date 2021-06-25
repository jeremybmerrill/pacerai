from pacerporcupine.courtlistener_search_warrant_alerter.alert import (
    alert_from_courtlistener_api,
)


def handler(event, context):
    # TODO: extract start date?
    alert_from_courtlistener_api()


if __name__ == "__main__":
    handler(
        {},
        {},
    )
