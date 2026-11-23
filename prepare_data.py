"""Download the weather data, clean it and save the results.

Run this once from the project folder:

    python prepare_data.py

It does four things for every city:
1. load the raw data (download it only if it is not on the disk yet)
2. check that the values make sense
3. clean the data and add year, month and season
4. save the result in data/processed/
"""

from pathlib import Path

from src.analysis import temperature_change_table
from src.cleaning import check_data, prepare_city
from src.data_loader import load_city

CITIES = ["Milan", "Rome", "Palermo"]
START_YEAR = 1940
END_YEAR = 2025

PROCESSED_DIR = Path("data/processed")
OUTPUT_DIR = Path("outputs")


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    data_by_city = {}

    for city in CITIES:
        raw = load_city(city, START_YEAR, END_YEAR)
        print(f"{city}: {len(raw)} days, from {raw['date'].min().date()} "
              f"to {raw['date'].max().date()}")

        # step 2: sanity checks
        print("  wrong rows:", check_data(raw))
        print("  missing values:", int(raw.isna().sum().sum()))

        # step 3 and 4: clean and save
        df = prepare_city(raw, city)
        df.to_csv(PROCESSED_DIR / f"{city.lower()}_processed.csv", index=False)
        data_by_city[city] = df

    # save a small table that compares the old and the recent period
    summary = temperature_change_table(data_by_city)
    summary.to_csv(OUTPUT_DIR / "temperature_change.csv", index=False)

    print("\nAverage temperature, old period and recent period:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()