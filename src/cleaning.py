"""Clean the raw weather data and add year, month and season columns."""

import pandas as pd

WEATHER_COLUMNS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
]

# meteorological seasons: month number -> season name
SEASONS = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}

SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]


def check_data(df):
    """Count the rows that contain impossible values.

    Parameters:
        df (DataFrame): raw daily weather data

    Returns:
        dict: number of wrong rows for each check
    """
    max_below_min = (df["temperature_2m_max"] < df["temperature_2m_min"]).sum()

    mean_outside = (
        (df["temperature_2m_mean"] < df["temperature_2m_min"])
        | (df["temperature_2m_mean"] > df["temperature_2m_max"])
    ).sum()

    negative_rain = (df["precipitation_sum"] < 0).sum()

    return {
        "max below min": int(max_below_min),
        "mean outside min/max": int(mean_outside),
        "negative rain": int(negative_rain),
    }


def clean_data(df):
    """Fix the date column, remove duplicate days and sort by date.

    Parameters:
        df (DataFrame): raw daily weather data

    Returns:
        DataFrame: cleaned data
    """
    # check that all the columns we need are there
    for column in ["date"] + WEATHER_COLUMNS:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date")
    df = df.reset_index(drop=True)

    # A few days can have a missing value (NaN). We keep them:
    # pandas ignores NaN when it calculates means and sums.
    return df


def add_time_columns(df):
    """Add year, month and season columns, taken from the date.

    Parameters:
        df (DataFrame): cleaned data with a "date" column

    Returns:
        DataFrame: same data with three new columns
    """
    df = df.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["season"] = df["month"].map(SEASONS)
    return df


def prepare_city(df, city):
    """Clean the data of one city and add the extra columns.

    Parameters:
        df (DataFrame): raw daily weather data
        city (str): name of the city

    Returns:
        DataFrame: data ready for the analysis
    """
    df = clean_data(df)
    df = add_time_columns(df)
    df["city"] = city
    return df


def yearly_table(df):
    """Summarise the daily data into one row per year.

    Parameters:
        df (DataFrame): prepared data of one city

    Returns:
        DataFrame: columns year, temp_mean and rain_total
    """
    table = df.groupby("year").agg(
        temp_mean=("temperature_2m_mean", "mean"),
        rain_total=("precipitation_sum", "sum"),
    )
    return table.reset_index()


def monthly_table(df):
    """Average temperature and rain for each calendar month (Jan to Dec).

    Parameters:
        df (DataFrame): prepared data of one city

    Returns:
        DataFrame: columns month, temp_mean and rain_total
    """
    # rain: first add up each month of each year, then average over the years
    rain = df.groupby(["year", "month"])["precipitation_sum"].sum()
    rain = rain.groupby("month").mean()

    temperature = df.groupby("month")["temperature_2m_mean"].mean()

    table = pd.DataFrame({"temp_mean": temperature, "rain_total": rain})
    return table.reset_index()
