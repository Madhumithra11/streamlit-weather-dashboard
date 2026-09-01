# Real-Time Weather App

A Streamlit app that shows current weather and a 5-day forecast for any city, using the OpenWeatherMap API.

## Features
- City search input
- Current temperature, "feels like", humidity, sunrise/sunset
- 5-day forecast with daily icons
- Line chart (temperature trend) and bar chart (humidity trend)
- Celsius / Fahrenheit toggle
- Cached API calls (10 min) so repeated searches don't hit rate limits
- Friendly error handling (bad city name, bad API key, network issues)

## 1. Get an API key
1. Go to https://openweathermap.org/api and create a free account.
2. Go to "My API Keys" and copy your default key.
3. New keys can take up to ~1 hour to activate — if you get a 401 error right away, just wait and retry.

## 2. Install dependencies
```bash
pip install -r requirements.txt
```

## 3. Set your API key (optional — you can also paste it in the sidebar)
```bash
export OWM_API_KEY="your_api_key_here"      # Mac/Linux
setx OWM_API_KEY "your_api_key_here"        # Windows (new terminal after)
```

## 4. Run the app
```bash
streamlit run app.py
```
This opens the app in your browser at http://localhost:8501

## 5. Sample queries to demo
- Chennai
- London
- New York
- Tokyo
- Paris

## How it works (for your project write-up)
- **`fetch_current_weather()`** calls OpenWeatherMap's `/weather` endpoint for current conditions.
- **`fetch_forecast()`** calls the `/forecast` endpoint, which returns data in 3-hour steps for 5 days (40 data points).
- **`build_forecast_dataframe()`** reduces those 40 points down to one representative reading per day (the 12:00 noon entry) using pandas, so the chart shows a clean 5-day trend instead of a noisy 3-hourly one.
- **`ICON_MAP`** maps OpenWeatherMap's weather "main" field (e.g. `"Rain"`, `"Clouds"`) to an emoji — a simple, dependency-free way to do dynamic icons.
- **`st.cache_data(ttl=600)`** avoids re-calling the API every time Streamlit reruns the script (Streamlit reruns the whole file on every interaction), and keeps you under the free-tier rate limit (60 calls/min).
- The C/F toggle just changes the `units` parameter sent to the API (`metric` vs `imperial`) — OpenWeatherMap does the conversion server-side.

## Possible extensions (nice for a "future work" slide)
- Add a map (via `st.map`) showing the city location using the `coord` field from the API response.
- Add hourly forecast (use all 40 entries instead of just noon).
- Add a "recent searches" dropdown using `st.session_state`.
- Deploy for free on Streamlit Community Cloud so you can share a live link.
