from pacerporcupine.courtlistener_search_warrant_alerter.alert import alert


def handler(event, context):
    # TODO: extract start date?
    alert()


if __name__ == "__main__":
    handler(
        {},
        {},
    )
