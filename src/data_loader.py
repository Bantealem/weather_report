"""Download daily weather data from the Open-Meteo API and save it as CSV."""

import time
from pathlib import Path

import pandas as pd
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
RAW_DIR = Path("data/raw")
MODEL = "era5"

# the daily values we ask the API for
VARIABLES = ("temperature_2m_max,temperature_2m_min,"
             "temperature_2m_mean,precipitation_sum")


def get_coordinates(city):
    """Find the latitude and longitude of an Italian city.

    Parameters:
        city (str): name of the city, e.g. "Milan"

    Returns:
        tuple: (latitude, longitude)
    """
    # countryCode makes sure we get the Italian city,
    # not another city with the same name
    params = {"name": city, "count": 10, "countryCode": "IT"}

    try:
        response = requests.get(GEOCODING_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"Could not look up {city}: {error}")

    results = response.json().get("results")
    if not results:
        raise ValueError(f"Could not find city: {city}")

    # use the result with exactly the same name, otherwise the first one
    best = results[0]
    for result in results:
        if result["name"].lower() == city.lower():
            best = result
            break

    return best["latitude"], best["longitude"]


def download_weather(lat, lon, start_year, end_year):
    """Download daily weather data, ten years at a time.

    Parameters:
        lat (float): latitude of the city
        lon (float): longitude of the city
        start_year (int): first year to download
        end_year (int): last year to download (included)

    Returns:
        DataFrame: one row per day
    """
    parts = []

    # small requests (10 years each) are safer than one huge request
    for year in range(start_year, end_year + 1, 10):
        last = min(year + 9, end_year)
        print(f"  downloading {year}-{last}...")

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": f"{last}-12-31",
            "daily": VARIABLES,
            "timezone": "auto",
            "models": MODEL,
        }

        # The free API sometimes answers 429 (too many requests).
        # In that case we wait one minute and try again, up to 5 times.
        for attempt in range(5):
            try:
                response = requests.get(ARCHIVE_URL, params=params, timeout=60)
                if response.status_code == 429:
                    print("  too many requests, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                response.raise_for_status()
                break
            except requests.RequestException as error:
                raise RuntimeError(
                    f"Could not download {year}-{last}: {error}")
        else:
            raise RuntimeError(
                f"Still rate limited after 5 attempts ({year}-{last})")

        df = pd.DataFrame(response.json()["daily"])
        df = df.rename(columns={"time": "date"})
        parts.append(df)

        time.sleep(3)  # short pause between requests

    return pd.concat(parts, ignore_index=True)


def load_city(city, start_year=1940, end_year=2025):
    """Load the daily weather of a city.

    The data is downloaded only if we don't have it on the disk yet.

    Parameters:
        city (str): name of the city, e.g. "Milan"
        start_year (int): first year of the period
        end_year (int): last year of the period (included)

    Returns:
        DataFrame: daily weather with a "date" column
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{city.lower()}_{MODEL}_{start_year}_{end_year}.csv"

    # already downloaded: read it from the disk, no API call needed
    if path.exists():
        print(f"Reading saved data for {city}")
        return pd.read_csv(path, parse_dates=["date"])

    print(f"Downloading data for {city}")
    lat, lon = get_coordinates(city)
    df = download_weather(lat, lon, start_year, end_year)
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(path, index=False)
    return df
