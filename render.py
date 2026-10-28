#!/usr/bin/env python3
"""Render a 600x800 grayscale dashboard PNG for a Kobo Touch (N905).

Data sources:
  - Google Calendar via the private "secret address in iCal format" (env GCAL_ICS_URL)
  - Weather via Open-Meteo (no API key)

Usage:
  python render.py --out dist/dashboard.png
  python render.py --demo --out preview.png     # fake data, no network
"""
import argparse
import datetime as dt
import os
import sys
import urllib.request
import json
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

TZ = ZoneInfo("America/Toronto")
LAT, LON = 43.2557, -79.8711  # Hamilton, ON
W, H = 600, 800
MARGIN = 36

FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts/TTF",
    "/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
]


def font(size, bold=False):
    names = ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
             "Arial Bold.ttf" if bold else "Arial.ttf"]
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


WMO = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Rain showers", 81: "Rain showers", 82: "Heavy showers",
    85: "Snow showers", 86: "Snow showers", 95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&current=temperature_2m,weather_code"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        "&timezone=America%2FToronto&forecast_days=1"
    )
    with urllib.request.urlopen(url, timeout=20) as r:
        d = json.load(r)
    return {
        "now": round(d["current"]["temperature_2m"]),
        "hi": round(d["daily"]["temperature_2m_max"][0]),
        "lo": round(d["daily"]["temperature_2m_min"][0]),
        "pop": d["daily"]["precipitation_probability_max"][0],
        "text": WMO.get(d["daily"]["weather_code"][0], ""),
    }


def get_events(day_start, day_end):
    """Return list of (start, end, title, all_day) overlapping [day_start, day_end)."""
    import icalendar
    import recurring_ical_events

    url = os.environ["GCAL_ICS_URL"]
    with urllib.request.urlopen(url, timeout=30) as r:
        cal = icalendar.Calendar.from_ical(r.read())
    out = []
    for ev in recurring_ical_events.of(cal).between(day_start, day_end):
        s = ev.get("DTSTART").dt
        e = ev.get("DTEND").dt if ev.get("DTEND") else s
        title = str(ev.get("SUMMARY", "(no title)"))
        all_day = not isinstance(s, dt.datetime)
        if not all_day:
            s, e = s.astimezone(TZ), e.astimezone(TZ)
        out.append((s, e, title, all_day))
    out.sort(key=lambda x: (not x[3], x[0] if not x[3] else dt.datetime.min.replace(tzinfo=TZ)))
    return out


def demo_data(now):
    d = now.replace(hour=0, minute=0, second=0, microsecond=0)
    ev = [
        (d.date(), d.date(), "Focus day: no meetings", True),
        (d.replace(hour=9, minute=30), d.replace(hour=10, minute=0), "Client check-in", False),
        (d.replace(hour=11), d.replace(hour=12, minute=30), "Design work block", False),
        (d.replace(hour=14), d.replace(hour=15), "Stellae sync", False),
        (d.replace(hour=17, minute=30), d.replace(hour=18, minute=30), "Gym", False),
    ]
    wx = {"now": 6, "hi": 11, "lo": 3, "pop": 30, "text": "Partly cloudy"}
    return wx, ev


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fmt_time(t):
    s = t.strftime("%I:%M").lstrip("0")
    return s + t.strftime("%p").lower()


def render(now, wx, events, out_path, error=None):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)

    # Header: date
    d.text((MARGIN, 30), now.strftime("%A"), font=font(54, True), fill=0)
    d.text((MARGIN, 94), now.strftime("%B %-d"), font=font(32), fill=60)
    d.line((MARGIN, 150, W - MARGIN, 150), fill=0, width=3)

    # Weather block
    y = 168
    if wx:
        d.text((MARGIN, y), f"{wx['now']}°", font=font(76, True), fill=0)
        d.text((190, y + 10), wx["text"], font=font(30), fill=0)
        d.text((190, y + 52), f"High {wx['hi']}°  Low {wx['lo']}°  Rain {wx['pop']}%",
               font=font(22), fill=60)
    else:
        d.text((MARGIN, y + 20), "Weather unavailable", font=font(26), fill=90)
    d.line((MARGIN, 275, W - MARGIN, 275), fill=0, width=3)

    # Schedule
    d.text((MARGIN, 292), "TODAY", font=font(20, True), fill=90)
    y = 330
    body, small = font(30, True), font(22)
    max_w = W - 2 * MARGIN
    if error:
        for line in wrap(d, error, small, max_w):
            d.text((MARGIN, y), line, font=small, fill=0)
            y += 30
    elif not events:
        d.text((MARGIN, y), "Nothing scheduled.", font=font(30), fill=0)
        d.text((MARGIN, y + 44), "Enjoy the quiet.", font=small, fill=90)
    else:
        shown = 0
        for s, e, title, all_day in events:
            if y > H - 150:
                break
            if all_day:
                d.text((MARGIN, y), "ALL DAY", font=font(18, True), fill=90)
                y += 24
            else:
                d.text((MARGIN, y), f"{fmt_time(s)} to {fmt_time(e)}", font=font(20), fill=90)
                y += 26
            for line in wrap(d, title, body, max_w)[:2]:
                d.text((MARGIN, y), line, font=body, fill=0)
                y += 38
            y += 16
            shown += 1
        if shown < len(events):
            d.text((MARGIN, H - 92), f"+ {len(events) - shown} more", font=small, fill=90)

    # Footer
    d.line((MARGIN, H - 56, W - MARGIN, H - 56), fill=0, width=1)
    d.text((MARGIN, H - 44), f"Updated {fmt_time(now)}", font=font(18), fill=110)

    img = img.point(lambda p: 255 if p > 235 else p)
    img.save(out_path, "PNG", optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/dashboard.png")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()

    now = dt.datetime.now(TZ)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    if a.demo:
        wx, events = demo_data(now)
        events = [(s if isinstance(s, dt.datetime) else s, e, t, ad) for s, e, t, ad in events]
        render(now, wx, events, a.out)
        return

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + dt.timedelta(days=1)

    try:
        wx = get_weather()
    except Exception as ex:
        print("weather failed:", ex, file=sys.stderr)
        wx = None

    error, events = None, []
    try:
        events = get_events(day_start, day_end)
    except KeyError:
        error = "Calendar not set up yet. Add the GCAL_ICS_URL secret."
    except Exception as ex:
        print("calendar failed:", ex, file=sys.stderr)
        error = "Calendar unavailable right now."

    render(now, wx, events, a.out, error)


if __name__ == "__main__":
    main()
