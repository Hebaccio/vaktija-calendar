import requests
from datetime import datetime, timedelta
from ics import Calendar, Event

LOCATION_ID = 77  # Sarajevo
YEARS_FORWARD = 2  # generate for next 2 years

def fetch_prayer_times():
    rows = []
    current_year = datetime.now().year
    years = list(range(current_year, current_year + YEARS_FORWARD + 1))

    for year in years:
        for month in range(1, 13):
            url = f"https://api.vaktija.ba/vaktija/v1/{LOCATION_ID}/{year}/{month}"
            print(f"Fetching: {url}")
            r = requests.get(url)

            try:
                data = r.json()
            except:
                print(f"❌ ERROR: Invalid JSON for {year}-{month}")
                continue

            # Skip if "vakat" is missing or empty
            if "vakat" not in data:
                print(f"⚠️ No vakat data for {year}-{month}, skipping...")
                continue

            if not data["vakat"]:
                print(f"⚠️ Empty vakat list for {year}-{month}, skipping...")
                continue

            prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

            for day, vakti in enumerate(data["vakat"], start=1):
                date = datetime(year, month, day)
                for name, time in zip(prayers, vakti):
                    dt = datetime.strptime(f"{date.date()} {time}", "%Y-%m-%d %H:%M")
                    rows.append((name, dt))

    return rows


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

    print("✔️ ICS file created: Vaktija_Sarajevo.ics")


if __name__ == "__main__":
    events = fetch_prayer_times()
    print(f"Total events: {len(events)}")
    build_ics(events)
