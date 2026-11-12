"""Charts made with matplotlib and seaborn. Every function returns a figure."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.analysis import trend_line
from src.cleaning import SEASON_ORDER

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def plot_trend(yearly, trend, city):
    """Annual mean temperature of one city, with its trend line."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(yearly["year"], yearly["temp_mean"], marker="o", markersize=3,
            label="Annual mean")
    ax.plot(yearly["year"], trend_line(yearly["year"], trend), color="red",
            linestyle="--", label="Trend line")

    ax.set_title(f"Annual mean temperature in {city}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Temperature (°C)")
    ax.legend()
    ax.grid(alpha=0.3)
    return fig


def plot_anomalies(anomalies, baseline, city):
    """Bars showing how much each year differs from the baseline period."""
    fig, ax = plt.subplots(figsize=(10, 5))

    # red bars for warmer years, blue bars for colder years
    colors = ["red" if value > 0 else "blue" for value in anomalies["anomaly"]]
    ax.bar(anomalies["year"], anomalies["anomaly"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)

    ax.set_title(f"Temperature anomaly in {city} "
                 f"(baseline mean: {baseline:.1f} °C)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Difference from baseline (°C)")
    ax.grid(alpha=0.3)
    return fig


def plot_heatmap(df, city):
    """Heatmap of the mean temperature for every month of every year."""
    table = df.pivot_table(index="year", columns="month",
                           values="temperature_2m_mean")

    fig, ax = plt.subplots(figsize=(8, 10))
    sns.heatmap(table, cmap="coolwarm", ax=ax, yticklabels=10,
                xticklabels=MONTH_NAMES,
                cbar_kws={"label": "Temperature (°C)"})

    ax.set_title(f"Monthly mean temperature in {city}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")
    ax.tick_params(axis="y", rotation=0)  # write the years horizontally
    return fig


def plot_monthly_cycle(monthly_by_city, column, ylabel, title):
    """Average value of each calendar month, one line per city."""
    fig, ax = plt.subplots(figsize=(10, 5))

    for city, table in monthly_by_city.items():
        ax.plot(table["month"], table[column], marker="o", label=city)

    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_NAMES)
    ax.legend(title="City")
    ax.grid(alpha=0.3)
    return fig


def plot_seasons(data_by_city):
    """Average temperature of each season, one group of bars per season."""
    table = pd.DataFrame({
        city: df.groupby("season")["temperature_2m_mean"].mean()
        for city, df in data_by_city.items()
    })
    table = table.reindex(SEASON_ORDER)

    fig, ax = plt.subplots(figsize=(10, 5))
    table.plot(kind="bar", ax=ax)

    ax.set_title("Average temperature in each season")
    ax.set_xlabel("Season")
    ax.set_ylabel("Temperature (°C)")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="City")
    ax.grid(axis="y", alpha=0.3)
    return fig


def plot_annual_compare(yearly_by_city, column, ylabel, title):
    """One value per year, one line per city."""
    fig, ax = plt.subplots(figsize=(10, 5))

    for city, table in yearly_by_city.items():
        ax.plot(table["year"], table[column], label=city)

    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.legend(title="City")
    ax.grid(alpha=0.3)
    return fig


def plot_extreme_days(counts, trend, ylabel, title):
    """Bars with the number of extreme days per year, plus a trend line."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(counts["year"], counts["days"], label="Days per year")
    ax.plot(counts["year"], trend_line(counts["year"], trend), color="red",
            linestyle="--", label="Trend line")

    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(alpha=0.3)
    return fig
