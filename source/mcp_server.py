"""
Little MCP Agent is a simple yet powerful local AI assistant that runs entirely on your machine.
Built for learning and experimentation, it combines the power of open-source LLMs with advanced
retrieval-augmented generation (RAG) to create an intelligent chatbot that can work with your
personal documents and provide real-time information.
"""
VERSION="0.1.01"

import os
import requests
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file for the API key
load_dotenv()

# Initialize the FastAPI application
app = FastAPI(
    title="MCP Tool Server",
    description="Provides tools like weather and datetime as a service.",
    version="0.1"
)


# --- Tool Functions (Your Business Logic) ---

def get_date_time(city: str):
    """Gets the current date and time for a given city."""
    try:
        geolocator = Nominatim(user_agent="mcp_datetime_app")
        location = geolocator.geocode(city, timeout=10)
        if location is None:
            raise ValueError(f'City "{city}" not found.')

        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=location.latitude, lng=location.longitude)
        if timezone_str is None:
            raise ValueError(f'Could not determine timezone for {city}.')

        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        city_name = location.address.split(',')[0]

        return {
            'city': city_name,
            'timezone': timezone_str,
            'datetime': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'day_of_week': current_time.strftime('%A'),
        }
    except Exception as e:
        # Return a dictionary that can be converted to JSON, even for errors
        return {'error': str(e)}


def get_weather(city: str):
    """Gets the current weather for a given city."""
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'OpenWeather API key is not set.'}

    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Return a dictionary for errors
        return {'error': f'Failed to fetch weather: {e}'}


def get_Calc(l_operation: str):

    OPERATION, NUM_ONE, NUM_TWO = l_operation.split(", ")
    try:
        # Convert string inputs to floating-point numbers for calculation
        num1_float = float(NUM_ONE)
        num2_float = float(NUM_TWO)
    except ValueError:
        return "Error: NUM_ONE and NUM_TWO must be valid numbers."

    result = None
    if OPERATION == "ADD":
        result = num1_float + num2_float
    elif OPERATION == "SUB":
        result = num1_float - num2_float
    elif OPERATION == "MUL":
        result = num1_float * num2_float
    elif OPERATION == "DIV":
        if num2_float == 0:
            return "Error: Division by zero is not allowed."
        result = num1_float / num2_float
    else:
        return "Error: Invalid operation. Please use 'ADD', 'SUB', 'MUL', or 'DIV'."
    # Convert the numerical result back to a string
    return str(result)


# --- API Endpoints ---

@app.get("/")
def read_root():
    """A simple endpoint to check if the server is running."""
    return {"status": "MCP Server is running"}


@app.get("/get_datetime")
def api_get_datetime(
        myParam: str = Query(..., description="The city to get the date and time for, e.g., 'Paris, France'")):
    """API endpoint to get the current date and time."""
    result = get_date_time(myParam)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/get_weather")
def api_get_weather(myParam: str = Query(..., description="The city to get the weather for, e.g., 'London, UK'")):
    """API endpoint to get the current weather."""
    result = get_weather(myParam)
    if "error" in result:
        # Check for specific HTTP errors if possible from the original response
        if "cod" in result and result["cod"] != 200:
            raise HTTPException(status_code=int(result["cod"]), detail=result.get("message", "Weather API error"))
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/get_calc")
def api_get_calc(myParam: str = Query(..., description="The calc operation, e.g., 'ADD, 2, 3' 'SUB, 2, 3'")):
    """API endpoint to get the current weather."""

    result = get_Calc(myParam)
    if "error" in result:
        # Check for specific HTTP errors if possible from the original response
        if "cod" in result and result["cod"] != 200:
            raise HTTPException(status_code=int(result["cod"]), detail=result.get("message", "Calc API error"))
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# --- Main entry point to run the server ---
if __name__ == "__main__":
    print("Starting MCP Server ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
