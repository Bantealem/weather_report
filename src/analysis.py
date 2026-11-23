"""Calculations: averages, anomalies, extreme days and correlation (numpy)."""

import numpy as np
import pandas as pd

from src.cleaning import yearly_table

# the old period and the recent period that we compare
BASELINE_START = 1961
BASELINE_END = 1990
RECENT_START = 1996
RECENT_END = 2025

# limits for the extreme days
HOT_DAY_LIMIT = 30      # maximum temperature in °C
HEAVY_RAIN_LIMIT = 20   # rain in mm

MOVING_WINDOW = 10      # years used for the moving average


def period_average(table, column, start, end):
    """Calculate the average of a column between two years.

    Parameters:
        table (DataFrame): a table with a "year" column
        column (str): the column we want to average
        start (int): first year (included)
        end (int): last year (included)

    Returns:
        float: the average
    """
    years = table["year"]
    selected = table.loc[(years >= start) & (years <= end), column]
    return np.mean(selected)


def moving_average(values, window=MOVING_WINDOW):
    """Smooth a series with a moving average.

    Each value becomes the average of itself and the (window - 1)
    values before it. The first years do not have enough values,
    so they get NaN and are not drawn in the chart.

    Parameters:
        values (Series): the numbers to smooth
        window (int): how many values go in each average

    Returns:
        array: same length as values
    """
    values = np.array(values)
    weights = np.ones(window) / window
    averages = np.convolve(values, weights, mode="valid")
    empty = np.full(window - 1, np.nan)
    return np.concatenate([empty, averages])


def temperature_anomalies(yearly):
    """Compare each year with the average of the baseline period.

    Parameters:
        yearly (DataFrame): result of yearly_table

    Returns:
        tuple: (DataFrame with year and anomaly, baseline temperature)
    """
    baseline = period_average(yearly, "temp_mean",
                              BASELINE_START, BASELINE_END)

    anomalies = yearly[["year"]].copy()
    anomalies["anomaly"] = yearly["temp_mean"] - baseline

    return anomalies, baseline


def count_days(df, column, limit):
    """Count the days per year when a value is at least the limit.

    Parameters:
        df (DataFrame): prepared daily data of one city
        column (str): column to check, e.g. "temperature_2m_max"
        limit (float): the limit, e.g. 30 for hot days

    Returns:
        DataFrame: columns year and days
    """
    extreme = df[df[column] >= limit]
    counts = extreme.groupby("year").size()

    # years without any extreme day are missing, so we add them with 0
    all_years = sorted(df["year"].unique())
    counts = counts.reindex(all_years, fill_value=0)

    return pd.DataFrame({"year": all_years, "days": counts.values})


def temperature_change_table(data_by_city):
    """Compare the average temperature of the old and the recent period.

    Parameters:
        data_by_city (dict): city name -> prepared daily data

    Returns:
        DataFrame: one row per city
    """
    old_name = f"Average {BASELINE_START}-{BASELINE_END} (°C)"
    new_name = f"Average {RECENT_START}-{RECENT_END} (°C)"
    rows = []

    for city, df in data_by_city.items():
        yearly = yearly_table(df)
        old = period_average(yearly, "temp_mean",
                             BASELINE_START, BASELINE_END)
        new = period_average(yearly, "temp_mean",
                             RECENT_START, RECENT_END)

        rows.append({
            "City": city,
            old_name: round(old, 2),
            new_name: round(new, 2),
            "Change (°C)": round(new - old, 2),
        })

    return pd.DataFrame(rows)


def city_correlation(data_by_city):
    """Check if the cities warm and cool in the same years.

    Parameters:
        data_by_city (dict): city name -> prepared daily data

    Returns:
        DataFrame: correlation between the annual temperatures of the cities
    """
    names = list(data_by_city.keys())
    temperatures = []

    for city in names:
        yearly = yearly_table(data_by_city[city])
        temperatures.append(yearly["temp_mean"])

    correlation = np.corrcoef(temperatures)
    return pd.DataFrame(correlation, index=names, columns=names).round(2)