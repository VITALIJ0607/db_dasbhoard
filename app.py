"""Simple app for checking train arrival and departure times."""

from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import date
from functools import lru_cache
from os import environ
import json
import requests

from flask import (
    Flask,
    render_template,
    request,
    url_for,
)


CONFIG_PATH = "app.conf"


app = Flask(__name__)


@lru_cache(maxsize=100)
def get_timetable_information(location, time, track, date):
    """Gets timetable information by DB REST API
            Arguments:
	        location -- The destinated station
		time -- Arrival and departure time
		track -- The railway track
    """
    api_url = environ.get("API_URL")
    client_id = environ.get("CLIENT_ID")
    client_secret = environ.get("CLIENT_SECRET")
    headers = {
        "Accept": "application/json",
        "DB-Client-id": client_id,
        "DB-Api-Key": client_secret,
    }
    url = f"{api_url}/{location}?date={date}"
    response = requests.get(url, headers=headers)
    result = []
    if response.ok:
        data = json.loads(response.text)
        date_time = f"{date}T{time}" if time else None
        for entry in data:
            if date_time and date_time != entry["dateTime"]:
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
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    config = ConfigParser()
    config.sections()
    config.read(CONFIG_PATH)
    environ["API_URL"] = config["App"]["db_api_url"]
    environ["CLIENT_ID"] = config["App"]["db_client_id"]
    environ["CLIENT_SECRET"] = config["App"]["db_client_secret"]
    host = config["App"]["host"]
    port = int(config["App"]["port"])
    app.run(host, port, debug=args.debug)
