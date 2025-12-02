import requests
from datetime import datetime, timedelta
from ics import Calendar, Event
import pytz
import time
import os

LOCATION_ID = 77  # Sarajevo
sarajevo_tz = pytz.timezone("Europe/Sarajevo")

ICS_FILE = "Vaktija_Sarajevo.ics"


# --------------------------------------------------------
# LOAD EXISTING ICS (EVEN IF BROKEN)
# --------------------------------------------------------
def load_existing_ics():
    if not os.path.exists(ICS_FILE):
        print("[INFO] No ICS file found. Creating a new one.")
        return Calendar()

    with open(ICS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        cal = Calendar(content)
        print(f"[INFO] Loaded {len(list(cal.events))} existing events.")
        return cal

    except Exception:
        print("[WARNING] ICS file broken or has multiple calendars. Cleaning...")

        try:
            calendars = list(Calendar.parse_multiple(content))
            merged = Calendar()
            for c in calendars:
                for e in c.events:
                    merged.events.add(e)

            print(f"[INFO] Cleaned and merged {len(list(merged.events))} events.")
            return merged

        except Exception:
            print("[ERROR] Could not parse ICS. Creating fresh calendar.")
            return Calendar()


# --------------------------------------------------------
# SAVE CALENDAR TO FILE (WORKING VERSION)
# --------------------------------------------------------
def save_ics(calendar):
    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.write(str(calendar))
    print(f"[INFO] Saved {len(list(calendar.events))} total events to ICS.")


# --------------------------------------------------------
# GET THE LAST DATE IN ICS
# --------------------------------------------------------
def get_last_date(calendar):
    if not calendar.events:
        return None
    last_dt = max(e.begin.datetime for e in calendar.events)
    return last_dt.date()


# --------------------------------------------------------
# FETCH PRAYER DATA FOR NEXT DAY ONLY  (Your original logic)
# --------------------------------------------------------
def fetch_prayer_times():
    calendar = load_existing_ics()

    # Prevent duplicates: store (name, datetime)
    existing = {(e.name, e.begin.datetime) for e in calendar.events}

    last_date = get_last_date(calendar)
    if last_date:
        start_date = last_date + timedelta(days=1)
        end_date = start_date
        print(f"[INFO] Fetching prayers for next day after last ICS event: {start_date}")
    else:
        start_date = datetime.now().date()
        end_date = start_date
        print(f"[INFO] No existing events, starting from today: {start_date}")

    prayers = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

    current = start_date
    while current <= end_date:

        print(f"\n[FETCH] Fetching date: {current}")

        url = (
            f"https://api.vaktija.ba/vaktija/v1/"
            f"{LOCATION_ID}/{current.year}/{current.month}/{current.day}"
        )

        try:
            r = requests.get(url)
            data = r.json()
        except ValueError:
            print(f"[ERROR] Invalid JSON for {current}. Skipping.")
            break
        except Exception as e:
            print(f"[ERROR] Request failed for {current}: {e}")
            break

        vakat = data.get("vakat")

        if vakat:
            print(f"[SUCCESS] Received data for {current}")

            # --------------------------------------------------------
            # NEW LOGIC: BUILD FULL DATETIME LIST
            # --------------------------------------------------------
            dt_list = []
            for t in vakat:
                dt = datetime.strptime(f"{current} {t}", "%Y-%m-%d %H:%M")
                dt_list.append(sarajevo_tz.localize(dt))

            # --------------------------------------------------------
            # NEW LOGIC: DEFINE PRAYER TIME RANGES
            # --------------------------------------------------------
            ranges = {
                "Fajr": (
                    dt_list[0],
                    dt_list[1]
                ),
                "Dhuhr": (
                    dt_list[2],
                    dt_list[3] - timedelta(minutes=1)
                ),
                "Asr": (
                    dt_list[3],
                    dt_list[4] - timedelta(minutes=1)
                ),
                "Maghrib": (
                    dt_list[4],
                    dt_list[5] - timedelta(minutes=1)
                ),
                "Isha": (
                    dt_list[5],
                    sarajevo_tz.localize(datetime.combine(
                        current,
                        datetime.strptime("23:59", "%H:%M").time()
                    ))
                )
            }

            # --------------------------------------------------------
            # ADD EVENTS USING NEW RANGE LOGIC
            # --------------------------------------------------------
            new_events_added = False

            for name, (start_dt, end_dt) in ranges.items():

                if (name, start_dt) in existing:
                    continue

                event = Event(
                    name=name,
                    begin=start_dt,
                    end=end_dt
                )
                calendar.events.add(event)
                existing.add((name, start_dt))
                new_events_added = True

            if new_events_added:
                print("[INFO] New events added — saving to file...")
                save_ics(calendar)
            else:
                print("[INFO] No new events for this date (already exists).")

        else:
            print(f"[WARNING] No vakat data for {current}")

        current += timedelta(days=1)
        time.sleep(5)  # small delay to avoid server spam

    return calendar


# RUN SCRIPT
fetch_prayer_times()
