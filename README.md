Weather‑Based Irrigation Automation

Overview
This project automates weather‑based irrigation decisions using a fully orchestrated data engineering pipeline.
Every day, the system:

1. Extracts weather data from the Open‑Meteo API
2. Transforms and loads it into a SQL Server data warehouse
3. Generates a daily irrigation recommendation
4. Sends the decision via SMS notification
5. Powers a Power BI dashboard for monitoring trends

This project demonstrates end‑to‑end mastery of ETL, APIs, SQL modeling, automation, and real‑world data engineering practices.

Features: 

Automated ETL Pipeline
  * Extracts hourly and daily weather data
  * Cleans, transforms, and enriches the dataset
  * Loads into a SQL Server star schema

Irrigation Decision Engine
  * Uses rainfall, temperature, and soil‑moisture logic
  * Produces a daily WATER / DO NOT WATER recommendation
  * Stores decisions in FactIrrigationDecision

SMS Notifications (Twilio)
  * Sends a daily text message with:
    --Today’s irrigation decision
    --Reasoning
  * Runs automatically via Windows Task Scheduler

Power BI Dashboard
  * Visualizes weather trends
  * Shows irrigation decisions over time
  * Provides insights for water conservation

Data Pipeline Details
  1. Extract
     Weather data is pulled from the Open‑Meteo API:
      * Hourly: temperature, humidity, precipitation, soil moisture
      * Daily: rainfall totals, evapotranspiration, max/min temps
  2. Transform
    * Convert timestamps
    * Normalize units
    * Create derived metrics
    * Prepare fact/dimension tables
  3. Load
     Data is loaded into SQL Server:

     Dimension Tables
       * DimDate
       * DimLocation
       * DimWeatherCondition
     
     Fact Tables
       * FactHourlyWeather
       * FactDailyWeather
       * FactIrrigationDecision

Irrigation Decision Logic
  The decision engine evaluates:
    * Rainfall in last 24 hours
    * Forecasted precipitation
    * Soil moisture
    * Temperature thresholds

  Example rule: If rainfall < 0.1 inches AND soil moisture < 30% → WATER  Else → DO NOT WATER

SMS Notification

  After the ETL completes, the script queries SQL Server:

  SELECT TOP 1 decision, reason
  FROM FactIrrigationDecision
  ORDER BY Date_id DESC

  Then sends a text message using Twilio:
  Today's irrigation decision: WATER
  Reason: Soil moisture below threshold.

Installation
      
    1. Clone the repository
      git clone https://github.com/chitravk/weather-irrigation-dashboard.git
      cd weather-irrigation-dashboard

    2. Configure environment variables
       Create a .env file:

Running the Pipeline

  * Manual Run
    python Weather_Irrigation_notification.py
  * Automated Run (Daily)
    Use Windows Task Scheduler to run the script every morning.

Power BI Dashboard
  
  The dashboard includes:
    * Daily & hourly weather trends
    * Irrigation decisions over time
    * Rainfall vs. soil moisture
    * Water conservation insights

Technologies Used

    * Python (requests, pandas, SQLAlchemy, pyodbc)
    * SQL Server
    * Twilio SMS API
    * Power BI
    * Windows Task Scheduler
    * Open‑Meteo Weather API

Future Enhancements

    * Add soil moisture sensor integration
    * Build a mobile‑friendly dashboard
