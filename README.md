# 🌦️ Weather Report

Weather Report compares 86 years of daily weather in Milan, Rome and Palermo
and asks a simple question: is the climate really changing where we live? The
results are explored in a web app.

![built with](https://img.shields.io/badge/built%20with-Streamlit-red)
![python](https://img.shields.io/badge/python-3.12%2B-blue)

## What the app does

Pick a city in the sidebar. The app has five tabs:

| Tab                    | What you can see                                                                                                                                |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Temperature**        | Annual mean temperature with a 10-year moving average, and the average of the old and the recent period side by side.                           |
| **Anomalies**          | How much each year differs from the 1961-1990 average, as red (warmer) and blue (colder) bars.                                                  |
| **Seasons and months** | A heatmap of the monthly mean temperature, the average temperature and rain of each month for the three cities, and the average of each season. |
| **Extremes**           | Hot days and heavy rain days per year, with the average of the old and the recent period.                                                       |
| **Compare cities**     | A table with the change in average temperature, charts of annual temperature and rain, and how strongly the cities follow each other.           |

## How the analysis works

The analysis compares an old period with a recent one. The settings below
are used everywhere in the project:

| Setting        | Value                             | Meaning                                 |
| -------------- | --------------------------------- | --------------------------------------- |
| Old period     | 1961-1990                         | The "normal" climate we compare against |
| Recent period  | 1996-2025                         | The last 30 years                       |
| Hot day        | max temperature of at least 30 °C | Counted for every year                  |
| Heavy rain day | at least 20 mm of rain            | Counted for every year                  |
| Moving average | 10 years                          | Smooths the ups and downs between years |

They are defined in one place, at the top of `src/analysis.py`, so they are
easy to change.

## Results

Average annual temperature in the two periods:

| City    | 1961-1990 | 1996-2025 | Change   |
| ------- | --------- | --------- | -------- |
| Milan   | 12.51 °C  | 14.31 °C  | +1.80 °C |
| Rome    | 15.27 °C  | 16.60 °C  | +1.34 °C |
| Palermo | 18.10 °C  | 19.49 °C  | +1.39 °C |

- Hot days became much more frequent: from about 20 to 43 days per year in
  Milan, from 36 to 66 in Rome and from 56 to 79 in Palermo.
- Heavy rain days changed only a little, and not in the same direction in
  all cities, so there is no clear change.
- The cities follow each other closely. The correlation between their annual
  temperatures is between 0.87 and 0.92.

Some limits to keep in mind:

- The data comes from a model (ERA5), so it is a very good estimate of the
  weather, but it is not the reading of a weather station.
- A hot day is a single day above 30 °C. The project does not look for
  heatwaves, which need several hot days in a row.
- The comparison shows how big the difference is, but it has no statistical
  test.
- There are only three cities, all in Italy, so the results say nothing about
  other regions.

## Data sources

- **[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)**:
  free and without an API key. For each city the project downloads four daily
  values from 1940 to 2025: maximum, minimum and mean temperature, and total
  precipitation.
- `data/raw/`: the downloaded files, one CSV per city. They are created by the
  program and are not on GitHub.
- `data/processed/`: the cleaned data, with year, month and season added. Also
  created by the program and not on GitHub.
- `outputs/temperature_change.csv`: the table with the old and the recent
  average temperature.

## Libraries

| Library      | Used for                                         |
| ------------ | ------------------------------------------------ |
| `requests`   | calling the Open-Meteo API                       |
| `pandas`     | cleaning the data, grouping it by year and month |
| `numpy`      | averages, moving average and correlation         |
| `matplotlib` | the charts                                       |
| `seaborn`    | the heatmap                                      |
| `streamlit`  | the web application                              |

Exact versions are listed in [`requirements.txt`](requirements.txt).

## Setup

1. Clone the repository and enter the folder:

   ```bash
   git clone https://github.com/<your-user>/<your-repo>.git
   cd <your-repo>
   ```

2. Create a virtual environment and install the dependencies (Python 3.12 or
   newer):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Download and prepare the data:

   ```bash
   python prepare_data.py
   ```

   No API key is needed. The first run downloads the data of the three cities,
   which can take several minutes because the free API limits the number of
   requests. When the API says "too many requests" the program waits and tries
   again. The files are saved in `data/raw/`, so the download happens only once.
   The script also checks the data, cleans it and prints the table with the old
   and the recent average temperature.

## Run

Start the web app:

```bash
streamlit run app.py
```

The browser opens at <http://localhost:8501>. Use the sidebar to choose the
city. If you start the app before step 3, it shows a message that asks you to
run `prepare_data.py` first.

The code in `src/` can also be used without Streamlit, like any library:

```python
from src.data_loader import load_city
from src.cleaning import prepare_city, yearly_table

df = prepare_city(load_city("Milan"), "Milan")
print(yearly_table(df).tail())
```

## Project structure

```
weather_report/
├── app.py                 # Streamlit app: the five tabs
├── prepare_data.py        # load, check, clean and save the data
├── src/
│   ├── __init__.py
│   ├── data_loader.py     # Open-Meteo API calls, retry on errors, CSV cache
│   ├── cleaning.py        # data checks, year/month/season, yearly and monthly tables
│   ├── analysis.py        # periods, anomalies, extreme days, moving average, correlation
│   └── plots.py           # charts with matplotlib and seaborn
├── data/
│   ├── raw/               # downloaded CSV files (created by the program, not on GitHub)
│   └── processed/         # cleaned CSV files (created by the program, not on GitHub)
├── outputs/
│   └── temperature_change.csv   # average temperature of the old and the recent period
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

Everything in `src/` is plain Python that can be reused in a script or a
notebook, while `app.py` only deals with showing things on screen.
