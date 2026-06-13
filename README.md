# weather_irrigation_pipeline_2026
Pipeline Repository for Summer 2026 MSBA Project

## Project Structure

- **assets/**  
  Images, diagrams, and media used for documentation or the Power BI dashboard.

- **src/**   
  Python modules for ETL and utilities.

---

## Scripts

### Weather_Irrigation.py
**Purpose:**  
End‑to‑end ETL pipeline that extracts weather data, transforms it, loads it directly into SQL Server, and computes irrigation decisions for visualization in Power BI.

**Workflow:**
1. Loads environment variables and configuration  
2. Extracts hourly + daily weather data from Open‑Meteo API  
3. Transforms timestamps, units, and derived metrics  
4. Loads data **directly into SQL Server** using SQLAlchemy + pyodbc  
   - `DimDate`  
   - `FactDailyWeather`  
   - `FactHourlyWeather`  
   - `FactIrrigationDecision`  
5. Applies irrigation decision logic (rainfall, soil moisture, thresholds)  
6. Outputs results for Power BI dashboard consumption  

**Usage:**
```bash
python Weather_Irrigation.py
```
### Weather Code Preloading

The `DimWeatherCode` lookup table is **preloaded using a SQL script** stored in the `/scripts` folder.  
This table is **not populated by the Python ETL script**. Instead, it is loaded once during setup so that
all official Open‑Meteo weather codes and descriptions are available for joins during the ETL process.

Preloading this table ensures:
- Weather codes always match Open‑Meteo’s official definitions  
- No foreign‑key or lookup failures occur during ETL  
- Power BI visuals can display descriptive weather conditions instead of numeric codes  

The Python pipeline reads from `DimWeatherCode` but **never inserts or updates** its contents.

---

## Data Flow (Direct‑to‑SQL)

All data flows directly into SQL Server.

### SQL Server Tables
- **DimDate**
- **FactDailyWeather**
- **FactHourlyWeather**
- **FactIrrigationDecision**

---

## Irrigation Decision Logic

**Evaluates:**
- Rainfall in the last 24 hours  
- Forecasted precipitation  
- Soil moisture  
- Temperature thresholds  

**Example rule:**
```bash
If rainfall < 0.1 inches AND soil moisture < 30% → WATER
Else → DO NOT WATER
```
The final decision is stored in SQL and visualized in Power BI.

## Power BI Dashboards

The project includes two Power BI dashboards that visualize the final irrigation decision and the underlying weather patterns used to make that decision.

### **1. Irrigation Decision Overview**

This dashboard displays:
- **Today's irrigation decision** (WATER / DO NOT WATER)
- **Reason for the decision** (e.g., insufficient rain, adequate moisture)
- A combined **Daily ETₒ (water demand)** and **Rainfall** chart
- A date slicer for selecting the analysis window

This view helps quickly understand whether irrigation is needed based on recent weather conditions and evapotranspiration trends.

### **2. Rainfall Trend Dashboard**

This dashboard focuses on:
- **Daily rainfall amounts**
- A clear trend line showing declining or increasing rainfall
- The same date slicer for filtering the analysis period

This view supports the irrigation decision by showing whether recent rainfall has been sufficient.

Both dashboards are powered directly from SQL Server tables populated by the ETL pipeline:
- `FactDailyWeather`
- `FactHourlyWeather`
- `FactIrrigationDecision`
- `DimDate`
- `DimWeatherCode` (preloaded)

These dashboards provide a complete, data‑driven view of weather‑based irrigation needs.

## Requirements

Install all dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```
Key Libraries:
- `requests` — HTTP client for calling the Open‑Meteo API

- `pandas` — Data manipulation and transformation

- `sqlalchemy` — Engine/ORM for loading data into SQL Server

- `pyodbc` — ODBC driver for SQL Server connectivity

- `python-dotenv` — Loads environment variables from .env
---
## Setup and Run
1. Create and activate a Python virtual environment:
   - Windows:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - macOS / Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

2. Install dependencies:
     ```bash
      pip install -r requirements.txt
     ```
3. Configure database and API settings

   Create a .env file at the repository root:

   ```env
    DB_SERVER=localhost\SQLEXPRESS
    DB_NAME=WeatherDB
    DB_DRIVER=ODBC Driver 18 for SQL Server

    LATITUDE=38.2527
    LONGITUDE=-85.7585
   ```
4. Preload Weather Codes (Required Step)
   Before running the ETL pipeline, preload the weather code lookup table:

   The SQL script is located in:
   ```
    /scripts/preload_weather_codes.sql
   ```
   Run it once in SQL Server Management Studio (SSMS) to populate:

   ```
    DimWeatherCode  
   ```
   This table is NOT populated by Python — it must exist before ETL runs.
5. Run the ETL Pipeline
   This script extracts weather data, transforms it, loads it into SQL Server,
   and prepares the data for visualization in Power BI.

   ```bash
    python Weather_Irrigation.py
   ```
6. View Results in Power BI
   Open the Power BI dashboard connected to your SQL Server database to explore:

     - Daily & hourly weather trends

     - Irrigation decisions

      - Rainfall vs. soil moisture

      - Temperature patterns

      - Water conservation insights

