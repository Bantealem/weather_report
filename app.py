"""Streamlit app: how has the weather changed in Milan, Rome and Palermo?

Run it with:  streamlit run app.py
(first run prepare_data.py once, to create the processed data)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src import plots
from src.analysis import (BASELINE_END, BASELINE_START, HEAVY_RAIN_LIMIT,
                          HOT_DAY_LIMIT, RECENT_END, RECENT_START,
                          city_correlation, count_days, period_average,
                          temperature_anomalies, temperature_change_table)
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


def show_two_periods(table, column, label, unit, decimals):
    """Show the average of the old and the recent period side by side."""
    old = period_average(table, column, BASELINE_START, BASELINE_END)
    new = period_average(table, column, RECENT_START, RECENT_END)

    col1, col2 = st.columns(2)
    col1.metric(f"{label} {BASELINE_START}-{BASELINE_END}",
                f"{old:.{decimals}f} {unit}")
    col2.metric(f"{label} {RECENT_START}-{RECENT_END}",
                f"{new:.{decimals}f} {unit}",
                delta=f"{new - old:+.{decimals}f} {unit}",
                delta_color="inverse")


# ---------- load the data ----------

try:
    data_by_city = load_all_cities()
except FileNotFoundError:
    st.error("Processed data not found. Please run: python prepare_data.py")
    st.stop()

# ---------- sidebar ----------

st.sidebar.header("Settings")
city = st.sidebar.selectbox("City", CITIES)

# ---------- data of the selected city ----------

df = data_by_city[city]
yearly = yearly_table(df)

# ---------- page ----------

st.title("Weather Report: Milan, Rome and Palermo")
st.write("Is the climate really changing where we live? "
         "This app uses daily weather data from 1940 to 2025 "
         "(Open-Meteo, ERA5) to compare the weather of three Italian cities.")

tab_temp, tab_anomaly, tab_seasons, tab_extremes, tab_compare = st.tabs(
    ["Temperature", "Anomalies", "Seasons and months", "Extremes",
     "Compare cities"])

with tab_temp:
    st.subheader(f"Temperature in {city}")
    show_two_periods(yearly, "temp_mean", "Average temperature", "°C", 2)

    show(plots.plot_temperature(yearly, city))
    st.write("The red line is the 10-year moving average: for each year it "
             "shows the average of that year and the 9 years before it. "
             "It hides the ups and downs from year to year, so the "
             "long-term change is easier to see.")

with tab_anomaly:
    st.subheader(f"Temperature anomalies in {city}")

    anomalies, baseline = temperature_anomalies(yearly)
    show(plots.plot_anomalies(anomalies, baseline, city))
    st.write(f"An anomaly is the difference between one year and the average "
             f"of {BASELINE_START}-{BASELINE_END}. Red bars are warmer than "
             f"that period, blue bars are colder.")

with tab_seasons:
    st.subheader(f"Monthly mean temperature in {city}")
    show(plots.plot_heatmap(df, city))

    st.subheader("Average temperature and rain in each month")
    monthly_by_city = {}
    for name, data in data_by_city.items():
        monthly_by_city[name] = monthly_table(data)

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
    hot_days = count_days(df, "temperature_2m_max", HOT_DAY_LIMIT)
    st.write(f"Hot day = maximum temperature of at least {HOT_DAY_LIMIT} °C")
    show_two_periods(hot_days, "days", "Hot days per year", "days", 1)
    show(plots.plot_extreme_days(
        hot_days, "Days per year",
        f"Hot days per year in {city}"))

    # heavy rain days
    rain_days = count_days(df, "precipitation_sum", HEAVY_RAIN_LIMIT)
    st.write(f"Heavy rain day = at least {HEAVY_RAIN_LIMIT} mm of rain")
    show_two_periods(rain_days, "days", "Heavy rain days per year", "days", 2)
    show(plots.plot_extreme_days(
        rain_days, "Days per year",
        f"Heavy rain days per year in {city}"))

with tab_compare:
    st.subheader("Average temperature: old period and recent period")
    st.dataframe(temperature_change_table(data_by_city), hide_index=True)

    yearly_by_city = {}
    for name, data in data_by_city.items():
        yearly_by_city[name] = yearly_table(data)

    show(plots.plot_annual_compare(
        yearly_by_city, "temp_mean", "Temperature (°C)",
        "Annual mean temperature"))
    show(plots.plot_annual_compare(
        yearly_by_city, "rain_total", "Rain (mm)",
        "Total rain per year"))

    st.subheader("Do the cities warm in the same years?")
    st.write("Correlation of the annual temperatures: 1 means the cities "
             "go up and down together, 0 means there is no connection.")
    st.dataframe(city_correlation(data_by_city))

st.caption("Data: Open-Meteo Historical Weather API (ERA5 model).")