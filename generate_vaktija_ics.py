import requests
from datetime import datetime, timedelta
from ics import Calendar, Event
import pytz
import time  # <-- new import

LOCATION_ID = 77  # Sarajevo
sarajevo_tz = pytz.timezone("Europe/Sarajevo")

def fetch_prayer_times():
    events = []
    start_date = datetime.now()
    end_date = datetime(start_date.year + 2, 12, 31)

    delta = timedelta(days=1)
    current = start_date

    prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

    while current <= end_date:
        url = f"https://api.vaktija.ba/vaktija/v1/{LOCATION_ID}/{current.year}/{current.month}/{current.day}"
        try:
            r = requests.get(url)
            data = r.json()
        except Exception as e:
            print(f"Skipping {current.date()} due to error: {e}")
            current += delta
            time.sleep(1)  # wait 1 second before next request
            continue

        vakat = data.get("vakat")
        if vakat:
            for name, time_str in zip(prayers, vakat):
                dt = datetime.strptime(f"{current.date()} {time_str}", "%Y-%m-%d %H:%M")
                dt = sarajevo_tz.localize(dt)
                events.append((name, dt))

        current += delta
        time.sleep(1)  # wait 1 second before next request

    return events
