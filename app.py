"""
Real-Time Weather App
----------------------
A Streamlit app that shows current weather + 5-day forecast for any city,
using the OpenWeatherMap API.

Run with:
    streamlit run app.py

Before running, set your API key as an environment variable:
    export OWM_API_KEY="your_api_key_here"      (Mac/Linux)
    setx OWM_API_KEY "your_api_key_here"         (Windows)

Or paste it directly into the sidebar input box when the app runs.
"""

import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Real-Time Weather App", page_icon="⛅", layout="centered")

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Map OpenWeatherMap "main" condition -> emoji icon
ICON_MAP = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
    "Smoke": "🌫️",
}


def get_icon(condition: str) -> str:
    return ICON_MAP.get(condition, "🌡️")


# ----------------------------
# API HELPERS
# ----------------------------
@st.cache_data(ttl=600, show_spinner=False)
def fetch_current_weather(city: str, api_key: str, units: str):
    params = {"q": city, "appid": api_key, "units": units}
    resp = requests.get(CURRENT_WEATHER_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_forecast(city: str, api_key: str, units: str):
    params = {"q": city, "appid": api_key, "units": units}
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def unix_to_time(unix_ts: int, tz_offset: int = 0) -> str:
    return datetime.utcfromtimestamp(unix_ts + tz_offset).strftime("%H:%M")


def build_forecast_dataframe(forecast_json: dict) -> pd.DataFrame:
    """
    OpenWeatherMap's free forecast endpoint returns data in 3-hour steps
    for 5 days (40 entries). We reduce this to one row per day by taking
    the midday (12:00) reading, which best represents that day's weather.
    """
    rows = []
    for entry in forecast_json["list"]:
        dt_txt = entry["dt_txt"]  # e.g. "2026-08-24 12:00:00"
        date_str, time_str = dt_txt.split(" ")
        rows.append({
            "date": date_str,
            "time": time_str,
            "temp": entry["main"]["temp"],
            "humidity": entry["main"]["humidity"],
            "condition": entry["weather"][0]["main"],
        })
    df = pd.DataFrame(rows)
    # Prefer the 12:00:00 reading for each day; fall back to first reading if missing
    daily = df[df["time"] == "12:00:00"]
    if daily.empty:
        daily = df.groupby("date").first().reset_index()
    return daily.reset_index(drop=True)


# ----------------------------
# SIDEBAR — SETTINGS
# ----------------------------
st.sidebar.header("Settings")

default_key = os.environ.get("OWM_API_KEY", "")
api_key = st.sidebar.text_input("OpenWeatherMap API Key", value=default_key, type="password")

unit_choice = st.sidebar.radio("Units", ["Celsius (°C)", "Fahrenheit (°F)"])
units = "metric" if unit_choice.startswith("Celsius") else "imperial"
unit_symbol = "°C" if units == "metric" else "°F"

st.sidebar.markdown("---")
st.sidebar.caption(
    "Get a free API key at https://openweathermap.org/api. "
    "New keys can take up to ~1 hour to activate."
)

# ----------------------------
# MAIN UI
# ----------------------------
st.title("⛅ Real-Time Weather App")
st.write("Enter a city name to see current conditions and a 5-day forecast.")

city = st.text_input("City name", placeholder="e.g. Chennai, London, Tokyo")
search = st.button("Get Weather", type="primary")

if search:
    if not api_key:
        st.error("Please enter your OpenWeatherMap API key in the sidebar.")
    elif not city:
        st.warning("Please enter a city name.")
    else:
        try:
            with st.spinner("Fetching current weather..."):
                current = fetch_current_weather(city, api_key, units)

            # ---- CURRENT WEATHER ----
            condition = current["weather"][0]["main"]
            description = current["weather"][0]["description"].title()
            temp = current["main"]["temp"]
            feels_like = current["main"]["feels_like"]
            humidity = current["main"]["humidity"]
            tz_offset = current.get("timezone", 0)
            sunrise = unix_to_time(current["sys"]["sunrise"], tz_offset)
            sunset = unix_to_time(current["sys"]["sunset"], tz_offset)
            city_display = f'{current["name"]}, {current["sys"].get("country", "")}'

            st.subheader(f"{get_icon(condition)} {city_display}")
            st.caption(description)

            col1, col2, col3 = st.columns(3)
            col1.metric("Temperature", f"{temp:.1f}{unit_symbol}")
            col2.metric("Feels Like", f"{feels_like:.1f}{unit_symbol}")
            col3.metric("Humidity", f"{humidity}%")

            col4, col5 = st.columns(2)
            col4.metric("🌅 Sunrise", sunrise)
            col5.metric("🌇 Sunset", sunset)

            # ---- 5-DAY FORECAST ----
            with st.spinner("Fetching 5-day forecast..."):
                forecast_json = fetch_forecast(city, api_key, units)

            daily_df = build_forecast_dataframe(forecast_json)

            st.markdown("### 5-Day Forecast")

            # Icon row
            icon_cols = st.columns(len(daily_df))
            for i, row in daily_df.iterrows():
                with icon_cols[i]:
                    day_label = datetime.strptime(row["date"], "%Y-%m-%d").strftime("%a")
                    st.markdown(f"**{day_label}**")
                    st.markdown(f"## {get_icon(row['condition'])}")
                    st.write(f"{row['temp']:.0f}{unit_symbol}")

            # Chart
            chart_df = daily_df.set_index("date")[["temp"]].rename(
                columns={"temp": f"Temperature ({unit_symbol})"}
            )
            st.line_chart(chart_df)

            humidity_df = daily_df.set_index("date")[["humidity"]].rename(
                columns={"humidity": "Humidity (%)"}
            )
            st.bar_chart(humidity_df)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                st.error("Invalid API key, or your key hasn't activated yet (can take up to 1 hour).")
            elif e.response.status_code == 404:
                st.error(f'City "{city}" not found. Check the spelling and try again.')
            else:
                st.error(f"API error: {e}")
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {e}")

st.markdown("---")
st.caption("Sample queries to try: Chennai, London, New York, Tokyo, Paris")
