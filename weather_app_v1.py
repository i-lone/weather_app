import datetime as dt
import json

import requests
from flask import Flask, jsonify, request
from datetime import datetime

# create your API token, and set it up in Postman collection as part of the Body section
API_TOKEN = ""
# you can get API keys for free here - https://api-ninjas.com/api/jokes
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def generate_forecast(date1: str, date2: str, location: str):
    url_base = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services"
    url_api = "timeline"

    if date2 == "":
        url = f"{url_base}/{url_api}/{location}/{date1}?key={RSA_KEY}&include=days&unitGroup=metric"
    else:
        url = f"{url_base}/{url_api}/{location}/{date1}/{date2}?key={RSA_KEY}&include=days&unitGroup=metric"

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA HT: We are getting weather.</h2></p>"


@app.route("/content/api/v1/integration/generate", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    if json_data.get("location") is None:
        raise InvalidUsage("location is required", status_code=400)

    location = json_data.get("location")

    if json_data.get("requester_name") is None:
        raise InvalidUsage("requester's name is required", status_code=400)

    requester_name = json_data.get("requester_name")

    if json_data.get("date") is None:
        raise InvalidUsage("date is required", status_code=400)

    date1 = json_data.get("date")

    date2 = ""
    if json_data.get("date2"):
        date2 = json_data.get("date2")

    forecast = generate_forecast(date1, date2, location)
    forecast_all_days = forecast.get("days")
    all_weather = {}
    
    for weather in forecast_all_days:
        temperature = weather.get("temp")
        windspeed = weather.get("windspeed")
        pressure  = weather.get("pressure")
        humidity = weather.get("humidity")
        sunrise = weather.get("sunrise")
        sunset = weather.get("sunset")
        light_time = str(datetime.strptime(sunset, "%H:%M:%S")- datetime.strptime(sunrise, "%H:%M:%S"))
        solar_energy = weather.get("solarenergy")
        description = weather.get("description")
        
        this_date = weather.get("datetime")
        
        weather_json = {
            "temp_c": temperature,
            "wind_kph": windspeed,
            "pressure_mb": pressure,
            "humidity": humidity,
            "sunrise": sunrise,
            "sunset": sunset,
            "sun_light_time": light_time,
            "solar_energy": solar_energy,
            "description": description
        }
        all_weather[f"{this_date}"] = weather_json

    end_dt = dt.datetime.now()

    if date2=="":
        result = {
           "requester_name": requester_name,
           "timestamp": end_dt.isoformat(),
           "location": location,
           "date": date1,
           "weather": all_weather,
        }
    else:
        result = {
           "requester_name": requester_name,
           "timestamp": end_dt.isoformat(),
           "location": location,
           "date": date1,
           "date_end": date2,
           "weather": all_weather,
        }

    return result
