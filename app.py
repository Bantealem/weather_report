"""Streamlit app: how has the weather changed in Milan, Rome and Palermo?

Run it with:  streamlit run app.py
(first run prepare_data.py once, to create the processed data)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src import plots
from src.analysis import (count_days, format_p_value, linear_trend,
                          temperature_anomalies, warming_summary)
from src.cleaning import monthly_table, yearly_table

CITIES = ["Milan", "Rome", "Palermo"]
PROCESSED_DIR = Path("data/processed")

st.set_page_config(page_title="Weather Report", layout="wide")


@st.cache_data
def load_all_cities():
    """Read the processed CSV file of every city (only once, then cached)."""
    data = {}
    for city in CITIES:
        path = PROCESSED_DIR / f"{city.lower()}_processed.csv"
        data[city] = pd.read_csv(path, parse_dates=["date"])
    return data


def show(fig):
    """Show a matplotlib figure in the app, then close it to free memory."""
    st.pyplot(fig)
    plt.close(fig)


# ---------- load the data ----------

try:
    data_by_city = load_all_cities()
except FileNotFoundError:
    st.error("Processed data not found. Please run: python prepare_data.py")
    st.stop()

# ---------- sidebar: the user's choices ----------

st.sidebar.header("Settings")
city = st.sidebar.selectbox("City", CITIES)
hot_limit = st.sidebar.slider(
    "Hot day: maximum temperature of at least (°C)", 25, 40, 30)
rain_limit = st.sidebar.slider(
    "Heavy rain day: at least (mm)", 10, 50, 20)

# ---------- calculations for the selected city ----------

df = data_by_city[city]
yearly = yearly_table(df)
trend = linear_trend(yearly["year"], yearly["temp_mean"])

# ---------- page ----------

st.title("Weather Report: Milan, Rome and Palermo")
st.write("Is the climate really changing where we live? "
         "This app uses daily weather data from 1940 to 2025 "
         "(Open-Meteo, ERA5) to look for long-term trends.")

tab_trend, tab_anomaly, tab_seasons, tab_extremes, tab_compare = st.tabs(
    ["Temperature trend", "Anomalies", "Seasons and months", "Extremes",
     "Compare cities"])

with tab_trend:
    st.subheader(f"Temperature trend in {city}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Warming per decade", f"{trend['slope'] * 10:+.2f} °C")
    col2.metric("R²", f"{trend['r_squared']:.2f}")
    col3.metric("p-value", format_p_value(trend["p_value"]))

    show(plots.plot_trend(yearly, trend, city))
    st.write("The red line is the best straight line through the yearly "
             "averages (linear regression). R² shows how well the line fits "
             "the data. A p-value below 0.05 means the trend is very "
             "unlikely to be just random.")

with tab_anomaly:
    st.subheader(f"Temperature anomalies in {city}")

    anomalies, baseline = temperature_anomalies(yearly)
    show(plots.plot_anomalies(anomalies, baseline, city))
    st.write("An anomaly is the difference between one year and the average "
             "of 1961-1990. Red bars are warmer than that period, "
             "blue bars are colder.")

with tab_seasons:
    st.subheader(f"Monthly mean temperature in {city}")
    show(plots.plot_heatmap(df, city))

    st.subheader("Average temperature and rain in each month")
    monthly_by_city = {name: monthly_table(data)
                       for name, data in data_by_city.items()}
    show(plots.plot_monthly_cycle(
        monthly_by_city, "temp_mean", "Temperature (°C)",
        "Average temperature in each month"))
    show(plots.plot_monthly_cycle(
        monthly_by_city, "rain_total", "Rain (mm)",
        "Average rain in each month"))

    st.subheader("Seasons")
    show(plots.plot_seasons(data_by_city))

with tab_extremes:
    st.subheader(f"Extreme days in {city}")

    # hot days
    hot_days = count_days(df, "temperature_2m_max", hot_limit)
    hot_trend = linear_trend(hot_days["year"], hot_days["days"])
    st.metric(f"Change in hot days (at least {hot_limit} °C)",
              f"{hot_trend['slope'] * 10:+.1f} days per decade")
    show(plots.plot_extreme_days(
        hot_days, hot_trend, "Days per year",
        f"Hot days per year in {city} (at least {hot_limit} °C)"))

    # heavy rain days
    rain_days = count_days(df, "precipitation_sum", rain_limit)
    rain_trend = linear_trend(rain_days["year"], rain_days["days"])
    st.metric(f"Change in heavy rain days (at least {rain_limit} mm)",
              f"{rain_trend['slope'] * 10:+.2f} days per decade")
    show(plots.plot_extreme_days(
        rain_days, rain_trend, "Days per year",
        f"Heavy rain days per year in {city} (at least {rain_limit} mm)"))

with tab_compare:
    st.subheader("Warming trend of the three cities")
    st.dataframe(warming_summary(data_by_city), hide_index=True)

    yearly_by_city = {name: yearly_table(data)
                      for name, data in data_by_city.items()}
    show(plots.plot_annual_compare(
        yearly_by_city, "temp_mean", "Temperature (°C)",
        "Annual mean temperature"))
    show(plots.plot_annual_compare(
        yearly_by_city, "rain_total", "Rain (mm)",
        "Total rain per year"))

st.caption("Data: Open-Meteo Historical Weather API (ERA5 model).")
