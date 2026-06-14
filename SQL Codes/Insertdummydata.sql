--Inserting dummy data

--dbo.DimDate
INSERT INTO DimDate (date_id, year, month, day, weekday_name, IsActive)
VALUES 
('2024-05-24', 2024, 5, 24, 'Friday', 0),
('2024-05-25', 2024, 5, 25, 'Saturday', 0);

select * from dbo.DimDate

-- DimWeatherCode

INSERT INTO DimWeatherCode (weather_code, description, IsActive)
VALUES
(1, 'Mainly clear', 0),
(2, 'Partly cloudy', 0),
(61, 'Slight rain', 0);

select * from DimWeatherCode

--Fact Daily Weather

INSERT INTO FactDailyWeather (date_id, weather_code, rain_sum, IsActive)
VALUES
('2024-05-24', 1, 0.12, 0),
('2024-05-25', 61, 0.50, 0);

select * from FactDailyWeather

-- Fact Hourly Weather

INSERT INTO FactHourlyWeather (
    timestamp, date_id, temperature_2m, precipitation_probability,
    rain, weather_code, precipitation, showers, IsActive
)
VALUES
('2024-05-24T08:00:00-04:00', '2024-05-24', 72.5, 10, 0.0, 1, 0.0, 0.0, 0),
('2024-05-24T09:00:00-04:00', '2024-05-24', 74.0, 20, 0.1, 61, 0.1, 0.0, 0);

select * from FactHourlyWeather

-- FactIrrigationDecision

INSERT INTO FactIrrigationDecision (
    date_id, decision, reason, yesterday_rain, today_rain, next_6hr_rain, IsActive
)
VALUES
('2024-05-24', 'SKIP', 'Dummy test row', 0.10, 0.00, 0.25, 0),
('2024-05-25', 'WATER', 'Dummy test row', 0.00, 0.00, 0.00, 0);

select * from FactIrrigationDecision



------------------------------------------------------------
-- Step 2: Drop fact tables first, then dimensions
------------------------------------------------------------
IF OBJECT_ID('dbo.FactIrrigationDecision', 'U') IS NOT NULL
    DROP TABLE dbo.FactIrrigationDecision;

IF OBJECT_ID('dbo.FactHourlyWeather', 'U') IS NOT NULL
    DROP TABLE dbo.FactHourlyWeather;

IF OBJECT_ID('dbo.FactDailyWeather', 'U') IS NOT NULL
    DROP TABLE dbo.FactDailyWeather;

IF OBJECT_ID('dbo.DimWeatherCode', 'U') IS NOT NULL
    DROP TABLE dbo.DimWeatherCode;

IF OBJECT_ID('dbo.DimDate', 'U') IS NOT NULL
    DROP TABLE dbo.DimDate;
GO





