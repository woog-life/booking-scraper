import sys
from dataclasses import dataclass
from datetime import datetime
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

    def json(self) -> Dict:
        return {
            "booking_link": self.booking_link,
            "is_available": self.is_available,
            "begin_time": f"{self.begin_time.isoformat()}Z",
            "end_time": f"{self.end_time.isoformat()}Z",
            "sale_start": f"{self.sale_start.isoformat()}Z",
        }


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
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        events = data["events"]
        result.extend(events)

        meta = data["meta"]
        if page >= meta["total_pages"]:
            break

    return result


def _utc(input_time: datetime) -> datetime:
    naive_time = input_time.replace(tzinfo=None)
    input_tz = pytz.timezone("Europe/Berlin")
    local_time = input_tz.localize(naive_time)
    utc_time = local_time.astimezone(pytz.utc)
    return utc_time.replace(tzinfo=None)


def _get_details(event: Dict) -> EventDetails:
    event_id = event["pf_id"]
    base_url = f"https://api.ztix-technik.de/sale/events/{event_id}/?booking_office=129"
    response = requests.get(base_url)
    response.raise_for_status()
    data = response.json()

    begin_time = _utc(datetime.fromisoformat(data["begin_time"]))
    end_time = _utc(datetime.fromisoformat(data["end_time"]))

    sale_config = data["sale_configs"][0]
    sale_start = _utc(datetime.fromisoformat(sale_config["start_date"]))

    is_available = False

    products = data["products"]
    for product in products:
        if product["name"] in ["Einzelkarte", "Schwimmbadticket"]:
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


def _publish_details(details: Iterable[EventDetails]):
    base_url = f"https://api.woog.life/lake/{configuration.lake_id}/booking"
    body = {
        "variation": configuration.variation,
        "events": [event.json() for event in details],
    }
    response = requests.put(
        base_url,
        json=body,
        headers={"Authorization": f"Bearer {configuration.api_key}"}
    )
    response.raise_for_status()


def main():
    try:
        events = _get_events()
        print(f"Got a list of {len(events)} events, proceeding to request details...")
        event_details = (_get_details(event) for event in events)
        _publish_details(event_details)
    except Exception as e:
        print(f"Fuck me sideways: {e}")
        sys.exit(1)
    else:
        print("Success.")


if __name__ == '__main__':
    main()
