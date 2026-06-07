"""
Weather + Irrigation ETL Pipeline
--------------------------------------------------------------------
This script:
    - Extracts daily + hourly weather data from Open-Meteo API
    - DROPS and CREATES all tables on every execution
    - Transforms API data into clean DataFrames
    - Computes irrigation logic (yesterday rain + next 6 hours)
  
"""

import os
import logging
from datetime import datetime, timedelta

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# ============================================================
# 1. CONFIGURATION & LOGGING
# ============================================================

def load_config():
    load_dotenv()

    return {
        "DB_SERVER": os.getenv("DB_SERVER"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_DRIVER": os.getenv("DB_DRIVER"),
        "LATITUDE": float(os.getenv("LATITUDE")),
        "LONGITUDE": float(os.getenv("LONGITUDE")),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO").upper(),
    }


def setup_logging(level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def build_connection_string(config):
    driver = config["DB_DRIVER"].replace(" ", "+")
    return (
        f"mssql+pyodbc://{config['DB_SERVER']}/{config['DB_NAME']}"
        f"?driver={driver}&TrustServerCertificate=yes"
    )


# ============================================================
# 2. EXTRACTION
# ============================================================

def extract_weather_data(lat, lon, days=7):
    logging.info("Extracting weather data from Open-Meteo API")

    from datetime import timezone
    end_date = datetime.now(timezone.utc).date()

    start_date = end_date - timedelta(days=days - 1)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "hourly": [
            "temperature_2m",
            "relativehumidity_2m",
            "precipitation_probability",
            "rain",
            "showers",
            "weathercode",
        ],
        "daily": [
            "rain_sum",
            "et0_fao_evapotranspiration",
            "weathercode",
        ],
        "timezone": "UTC",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    hourly_df = pd.DataFrame(data["hourly"])
    daily_df = pd.DataFrame(data["daily"])

    logging.info(f"Extracted {len(hourly_df)} hourly rows and {len(daily_df)} daily rows")

    return daily_df, hourly_df


# ============================================================
# 3. TRANSFORMATION
# ============================================================

def transform_weather_data(daily_df, hourly_df):
    logging.info("Transforming weather data")

    # ---------------- Hourly ----------------
    hourly = hourly_df.copy()
    hourly["timestamp"] = pd.to_datetime(hourly["time"], utc=True)
    hourly["date_id"] = hourly["timestamp"].dt.date

    hourly.rename(
        columns={
            "relativehumidity_2m": "humidity",
            "weathercode": "weather_code",
        },
        inplace=True,
    )

     # ---------------------------------------------------------
    # Data Quality Check: Validate weather codes
    # ---------------------------------------------------------
    valid_weather_codes = {
        0, 1, 2, 3, 45, 48,
        51, 53, 55, 56, 57,
        61, 63, 65, 66, 67,
        71, 73, 75, 77,
        80, 81, 82,
        85, 86,
        95, 96, 99
    }

    invalid_hourly = hourly_df[~hourly_df["weathercode"].isin(valid_weather_codes)]
    if not invalid_hourly.empty:
        logging.error(f"Invalid weather codes in hourly data: {invalid_hourly['weathercode'].unique()}")
        raise ValueError("Invalid weather codes detected in hourly API response.")
        
    hourly = hourly[
        [
            "timestamp",
            "date_id",
            "weather_code",
            "temperature_2m",
            "humidity",
            "precipitation_probability",
            "rain",
            "showers",
        ]
    ]

    # ---------------- Daily ----------------
    daily = daily_df.copy()
    daily["date_id"] = pd.to_datetime(daily["time"]).dt.date

    daily.rename(
        columns={
            "rain_sum": "rain_sum",
            "et0_fao_evapotranspiration": "et0",
            "weathercode": "weather_code",
        },
        inplace=True,
    )

     # ---------------------------------------------------------
    # Data Quality Check: Validate weather codes
    # ---------------------------------------------------------
    valid_weather_codes = {
        0, 1, 2, 3, 45, 48,
        51, 53, 55, 56, 57,
        61, 63, 65, 66, 67,
        71, 73, 75, 77,
        80, 81, 82,
        85, 86,
        95, 96, 99
    }

    invalid_daily = daily_df[~daily_df["weathercode"].isin(valid_weather_codes)]
    if not invalid_daily.empty:
        logging.error(f"Invalid weather codes in daily data: {invalid_daily['weathercode'].unique()}")
        raise ValueError("Invalid weather codes detected in hourly API response.")
        
    daily = daily[["date_id", "weather_code", "rain_sum", "et0"]]

    # ---------------- Derived: daily humidity ----------------
    daily_humidity = (
        hourly.groupby("date_id", as_index=False)["humidity"]
        .mean()
        .rename(columns={"humidity": "avg_humidity"})
    )

    daily = daily.merge(daily_humidity, on="date_id", how="left")

    # ---------------- Derived: next_6hr_rain ----------------
    hourly["hour"] = hourly["timestamp"].dt.hour
    next_6hr = (
        hourly[hourly["hour"].between(0, 5)]
        .groupby("date_id", as_index=False)["rain"]
        .sum()
        .rename(columns={"rain": "next_6hr_rain"})
    )

    irrigation = daily.merge(next_6hr, on="date_id", how="left")

    # ---------------- Derived: yesterday_rain ----------------
    irrigation = irrigation.sort_values("date_id")
    irrigation["yesterday_rain"] = irrigation["rain_sum"].shift(1).fillna(0)

    # ---------------- Decision Logic ----------------
    def decide(row):
        if row["rain_sum"] >= 5 or row["yesterday_rain"] >= 5 or row["next_6hr_rain"] >= 5:
            return "SKIP", "Rain threshold exceeded"
        return "WATER", "Insufficient rain"

    decisions = irrigation.apply(lambda r: decide(r), axis=1, result_type="expand")
    irrigation["decision"] = decisions[0]
    irrigation["reason"] = decisions[1]

    irrigation.rename(columns={"rain_sum": "today_rain"}, inplace=True)

    return daily, hourly, irrigation


# ============================================================
# 4. DROP + CREATE TABLES
# ============================================================

CREATE_SCHEMA_SQL = """
IF OBJECT_ID('FactIrrigationDecision', 'U') IS NOT NULL DROP TABLE FactIrrigationDecision;
IF OBJECT_ID('FactHourlyWeather', 'U') IS NOT NULL DROP TABLE FactHourlyWeather;
IF OBJECT_ID('FactDailyWeather', 'U') IS NOT NULL DROP TABLE FactDailyWeather;
IF OBJECT_ID('DimDate', 'U') IS NOT NULL DROP TABLE DimDate;

CREATE TABLE DimDate (
    date_id DATE NOT NULL PRIMARY KEY,
    year INT,
    month INT,
    day INT,
    weekday_name VARCHAR(20)
);

CREATE TABLE FactDailyWeather (
    date_id DATE NOT NULL PRIMARY KEY,
    weather_code INT,
    rain_sum FLOAT,
    et0 FLOAT,
    avg_humidity FLOAT,
    FOREIGN KEY (date_id) REFERENCES DimDate(date_id)
);

CREATE TABLE FactHourlyWeather (
    timestamp DATETIME NOT NULL PRIMARY KEY,
    date_id DATE NOT NULL,
    temperature_2m FLOAT,
    humidity FLOAT,
    precipitation_probability INT,
    rain FLOAT,
    showers FLOAT,
    weather_code INT,
    FOREIGN KEY (date_id) REFERENCES DimDate(date_id)
);

CREATE TABLE FactIrrigationDecision (
    date_id DATE NOT NULL PRIMARY KEY,
    decision VARCHAR(20),
    reason VARCHAR(255),
    yesterday_rain FLOAT,
    today_rain FLOAT,
    next_6hr_rain FLOAT,
    avg_humidity FLOAT,
    et0 FLOAT,
    weather_code INT,
    FOREIGN KEY (date_id) REFERENCES DimDate(date_id)
);
"""

# Incremental loading is not required for this irrigation project because the
# Open‑Meteo API always returns a complete 7‑day snapshot of weather data on
# every request. The dataset is small, fully refreshed each run, and not meant
# to accumulate historical records. Since each execution replaces the entire
# 7‑day window, a full DROP + CREATE reload is the correct and simplest
# approach for this project.


def recreate_tables(engine):
    with engine.begin() as conn:
        conn.execute(text(CREATE_SCHEMA_SQL))


# ============================================================
# 5. LOAD FUNCTION
# ============================================================

def load_tables(engine, dim_df, daily_df, hourly_df, irrigation_df):
    """
    Loads ALL tables using explicit INSERT statements (Week‑2 style).
    """

    with engine.begin() as conn:

        # ---------------------------------------------------------
        # 1. Load DimDate
        # ---------------------------------------------------------
        for _, row in dim_df.iterrows():
            conn.execute(text("""
                INSERT INTO DimDate (date_id, year, month, day, weekday_name)
                VALUES (:date_id, :year, :month, :day, :weekday_name)
            """), row.to_dict())

        # ---------------------------------------------------------
        # 2. Load FactDailyWeather
        # ---------------------------------------------------------
        for _, row in daily_df.iterrows():
            conn.execute(text("""
                INSERT INTO FactDailyWeather
                (date_id, weather_code, rain_sum, et0, avg_humidity)
                VALUES
                (:date_id, :weather_code, :rain_sum, :et0, :avg_humidity)
            """), row.to_dict())

        # ---------------------------------------------------------
        # 3. Load FactHourlyWeather
        # ---------------------------------------------------------
        for _, row in hourly_df.iterrows():
            conn.execute(text("""
                INSERT INTO FactHourlyWeather
                (timestamp, date_id, temperature_2m, humidity,
                 precipitation_probability, rain, showers, weather_code)
                VALUES
                (:timestamp, :date_id, :temperature_2m, :humidity,
                 :precipitation_probability, :rain, :showers, :weather_code)
            """), row.to_dict())

        # ---------------------------------------------------------
        # 4. Load FactIrrigationDecision
        # ---------------------------------------------------------
        for _, row in irrigation_df.iterrows():
            conn.execute(text("""
                INSERT INTO FactIrrigationDecision
                (date_id, decision, reason, yesterday_rain, today_rain,
                 next_6hr_rain, avg_humidity, et0, weather_code)
                VALUES
                (:date_id, :decision, :reason, :yesterday_rain, :today_rain,
                 :next_6hr_rain, :avg_humidity, :et0, :weather_code)
            """), row.to_dict())


# ============================================================
# 6. Main execution
# ============================================================

def run_pipeline():
    config = load_config()
    setup_logging(config["LOG_LEVEL"])

    logging.info("Starting ETL pipeline")

    engine = create_engine(build_connection_string(config))

    # DROP + CREATE TABLES
    recreate_tables(engine)

    # Extract
    daily_raw, hourly_raw = extract_weather_data(
        config["LATITUDE"], config["LONGITUDE"]
    )

    # Transform
    daily, hourly, irrigation = transform_weather_data(daily_raw, hourly_raw)

    # Build DimDate
    dim = pd.DataFrame({"date_id": daily["date_id"].unique()})
    dim["year"] = pd.to_datetime(dim["date_id"]).dt.year
    dim["month"] = pd.to_datetime(dim["date_id"]).dt.month
    dim["day"] = pd.to_datetime(dim["date_id"]).dt.day
    dim["weekday_name"] = pd.to_datetime(dim["date_id"]).dt.day_name()

    # ONE CALL loads all tables
    load_tables(engine, dim, daily, hourly, irrigation)

    logging.info("ETL pipeline completed successfully")


if __name__ == "__main__":
    run_pipeline()
