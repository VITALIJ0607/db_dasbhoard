"""Simple app for checking train arrival and departure times."""

from argparse import ArgumentParser
from datetime import date
import json
import requests

from flask import (
    Flask,
    render_template,
    request,
    url_for,
)


CACHE_SIZE = 100

app = Flask(__name__)
app.config.from_object("config.Config")


def get_timetable_information(location, time, track, date, _cache={}):
    """Gets timetable information by DB REST API
            Arguments:
            location -- The destinated station
        time -- Arrival and departure time
        track -- The railway track
        date -- The date
    """
    api_url = app.config["DB_API_URL"]
    client_id = app.config["DB_CLIENT_ID"]
    client_secret = app.config["DB_CLIENT_SECRET"]
    headers = {
        "Accept": "application/json",
        "DB-Client-id": client_id,
        "DB-Api-Key": client_secret,
    }
    url = f"{api_url}/{location}?date={date}"
    if url not in _cache:
        response = requests.get(url, headers=headers)
        if response.ok:
            data = json.loads(response.text)
            if len(_cache) == CACHE_SIZE:
                _cache.popitem()
            _cache[url] = data
    data = _cache.get(url, [])
    result = []
    date_time = f"{date}T{time}" if time else None
    for entry in data:
        if date_time and (date_time >= entry["dateTime"]):
            continue
        if track and track != entry["track"]:
            continue
        result.append(entry)
    return result


@app.route("/")
def get_index():
    """Returns rendered input form."""
    return render_template("index.html")


@app.route("/timetable", methods=["POST"])
def get_timetable():
    """Return rendered timetable."""
    location = request.form["location"].strip()
    time = request.form["time"].strip()
    track = request.form["track"].strip()
    today = date.today().strftime("%Y-%m-%d")
    result = get_timetable_information(location, time, track, today)
    return render_template("timetable.html", data=result)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app.run(args.host, args.port, debug=args.debug)
