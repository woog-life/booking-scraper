import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from typing import List, Dict, Iterable
from urllib.parse import urlencode

import pytz
import requests

from booking.configuration import configuration


@dataclass
class EventDetails:
    booking_link: str
    begin_time: datetime
    end_time: datetime
    sale_start: datetime
    is_available: bool

    def __repr__(self):
        return f"is_available={self.is_available} ({self.booking_link})"


def _get_events() -> List[Dict]:
    base_url = "https://api.ztix-technik.de/homepage/calendar/events/" \
               "?booking_office=129&filter{category}=erleben&"
    result = []
    for page in count(start=1):
        arg = urlencode([
            ("search", configuration.query),
            ("page", page),
        ])
        url = base_url + arg
        response = requests.get(url).json()
        events = response["events"]
        result.extend(events)

        meta = response["meta"]
        if page >= meta["total_pages"]:
            break

    return result


def _utc(input_time: datetime) -> datetime:
    naive_time = input_time.replace(tzinfo=None)
    input_tz = pytz.timezone("Europe/Berlin")
    local_time = input_tz.localize(naive_time)
    return local_time.astimezone(pytz.utc)


def _get_details(event: Dict) -> EventDetails:
    event_id = event["pf_id"]
    base_url = f"https://api.ztix-technik.de/sale/events/{event_id}/?booking_office=129"
    response = requests.get(base_url).json()

    begin_time = _utc(datetime.fromisoformat(response["begin_time"]))
    end_time = _utc(datetime.fromisoformat(response["end_time"]))

    sale_config = response["sale_configs"][0]
    sale_start = _utc(datetime.fromisoformat(sale_config["start_date"]))

    is_available = False

    products = response["products"]
    for product in products:
        if product["name"] == "Einzelkarte":
            is_available = product["is_available"]
            break

    booking_link: str = event["link"]
    booking_link = booking_link.replace("hp//", "hp/")

    return EventDetails(
        booking_link=booking_link,
        begin_time=begin_time,
        end_time=end_time,
        sale_start=sale_start,
        is_available=is_available,
    )


def _is_valid(details: EventDetails) -> bool:
    if details.end_time > datetime.utcnow().replace(tzinfo=timezone.utc):
        return False

    return True


def _publish_details(details: Iterable[EventDetails]):
    base_url = f"https://api.woog.life/lake/{configuration.lake_id}/booking"
    body = {
        "events": list(details)
    }
    try:
        requests.put(
            base_url,
            json=body,
            headers={"Authorization": f"Bearer {configuration.api_key}"}
        )
    except Exception as e:
        print(f"Could not publish events: {e}")
        sys.exit(1)


def main():
    events = _get_events()
    event_details = (_get_details(event) for event in events)
    valid_events = (details for details in event_details if _is_valid(details))
    _publish_details(valid_events)


if __name__ == '__main__':
    main()
