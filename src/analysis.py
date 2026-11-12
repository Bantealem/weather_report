"""Statistics: trends, anomalies and extreme days (numpy and scipy)."""

import numpy as np
import pandas as pd
from scipy import stats

from src.cleaning import yearly_table

# years used as "normal climate" when we calculate anomalies
BASELINE_START = 1961
BASELINE_END = 1990


def linear_trend(years, values):
    """Fit a straight line through the points (year, value).

    Parameters:
        years (Series): the years (x values)
        values (Series): the measured values (y values)

    Returns:
        dict: slope (change per year), intercept, p_value and r_squared
    """
    result = stats.linregress(years, values)

    return {
        "slope": result.slope,
        "intercept": result.intercept,
        "p_value": result.pvalue,
        "r_squared": result.rvalue ** 2,
    }


def trend_line(years, trend):
    """Calculate the y values of the trend line, so we can draw it.

    Parameters:
        years (Series): the years (x values)
        trend (dict): result of linear_trend

    Returns:
        array: one y value for each year
    """
    years = np.array(years)
    return trend["intercept"] + trend["slope"] * years


def temperature_anomalies(yearly):
    """Compare each year with the average of the baseline period.

    Parameters:
        yearly (DataFrame): result of yearly_table

    Returns:
        tuple: (DataFrame with year and anomaly, baseline temperature)
    """
    years = yearly["year"]
    in_baseline = (years >= BASELINE_START) & (years <= BASELINE_END)
    baseline = yearly.loc[in_baseline, "temp_mean"].mean()

    anomalies = yearly[["year"]].copy()
    anomalies["anomaly"] = yearly["temp_mean"] - baseline

    return anomalies, baseline


def count_days(df, column, threshold):
    """Count the days per year when a value is at least the threshold.

    Parameters:
        df (DataFrame): prepared daily data of one city
        column (str): column to check, e.g. "temperature_2m_max"
        threshold (float): limit, e.g. 30 for hot days

    Returns:
        DataFrame: columns year and days
    """
    extreme = df[df[column] >= threshold]
    counts = extreme.groupby("year").size()

    # years without any extreme day are missing, so we add them with 0
    all_years = sorted(df["year"].unique())
    counts = counts.reindex(all_years, fill_value=0)

    return counts.rename_axis("year").reset_index(name="days")


def format_p_value(p_value):
    """Write a p-value as text, very small values as '< 0.001'."""
    if p_value < 0.001:
        return "< 0.001"
    return f"{p_value:.3f}"


def warming_summary(data_by_city):
    """Make a table with the warming trend of every city.

    Parameters:
        data_by_city (dict): city name -> prepared daily data

    Returns:
        DataFrame: one row per city
    """
    rows = []

    for city, df in data_by_city.items():
        yearly = yearly_table(df)
        trend = linear_trend(yearly["year"], yearly["temp_mean"])
        number_of_years = yearly["year"].max() - yearly["year"].min()

        rows.append({
            "City": city,
            "Warming per decade (°C)": round(trend["slope"] * 10, 2),
            "Total warming (°C)": round(trend["slope"] * number_of_years, 2),
            "p-value": format_p_value(trend["p_value"]),
            "R²": round(trend["r_squared"], 2),
        })

    return pd.DataFrame(rows)
