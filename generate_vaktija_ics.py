import requests
from datetime import datetime, timedelta
from ics import Calendar, Event
import pytz

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
        r = requests.get(url)
        try:
            data = r.json()
        except:
            current += delta
            continue

        vakat = data.get("vakat")
        if vakat:
            for name, time in zip(prayers, vakat):
                dt = datetime.strptime(f"{current.date()} {time}", "%Y-%m-%d %H:%M")
                dt = sarajevo_tz.localize(dt)
                events.append((name, dt))

        current += delta

    return events

def build_ics(events):
    cal = Calendar()
    for name, dt in events:
        e = Event()
        e.name = name
        e.begin = dt
        e.end = dt + timedelta(minutes=1)
        cal.events.add(e)

    with open("Vaktija_Sarajevo.ics", "w", encoding="utf-8") as f:
        f.writelines(cal)
    print(f"✔️ ICS generated with {len(events)} events")

if __name__ == "__main__":
    events = fetch_prayer_times()
    build_ics(events)
