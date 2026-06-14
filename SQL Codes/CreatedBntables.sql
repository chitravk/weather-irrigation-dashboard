------------------------------------------------------------
-- 1. Create Database if not exists
------------------------------------------------------------
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'IrrigationDB')
BEGIN
    CREATE DATABASE IrrigationDB;
END
GO

USE IrrigationDB;
GO


------------------------------------------------------------
-- 2. CREATE DimDate
------------------------------------------------------------
CREATE TABLE dbo.DimDate (
    date_id DATE PRIMARY KEY,
    year INT,
    month INT,
    day INT,
    weekday_name VARCHAR(20),
    IsActive BIT DEFAULT 1
);
GO

------------------------------------------------------------
-- 3. CREATE DimWeatherCode
------------------------------------------------------------
CREATE TABLE dbo.DimWeatherCode (
    weather_code INT PRIMARY KEY,
    description VARCHAR(100),
    IsActive BIT DEFAULT 1
);
GO

------------------------------------------------------------
-- 4. CREATE FactDailyWeather
------------------------------------------------------------
CREATE TABLE dbo.FactDailyWeather (
    id INT IDENTITY(1,1) PRIMARY KEY,
    date_id DATE NOT NULL,
    weather_code INT NULL,
    rain_sum FLOAT NULL,
    IsActive BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_daily_date FOREIGN KEY (date_id)
        REFERENCES dbo.DimDate(date_id),
    CONSTRAINT FK_daily_weathercode FOREIGN KEY (weather_code)
        REFERENCES dbo.DimWeatherCode(weather_code)
);
GO

------------------------------------------------------------
-- 5. CREATE FactHourlyWeather
------------------------------------------------------------
CREATE TABLE dbo.FactHourlyWeather (
    id INT IDENTITY(1,1) PRIMARY KEY,
    timestamp DATETIMEOFFSET NOT NULL,
    date_id DATE NOT NULL,
    temperature_2m FLOAT NULL,
    precipitation_probability FLOAT NULL,
    rain FLOAT NULL,
    weather_code INT NULL,
    precipitation FLOAT NULL,
    showers FLOAT NULL,
    IsActive BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_hourly_date FOREIGN KEY (date_id)
        REFERENCES dbo.DimDate(date_id),
    CONSTRAINT FK_hourly_weathercode FOREIGN KEY (weather_code)
        REFERENCES dbo.DimWeatherCode(weather_code)
);
GO

------------------------------------------------------------
-- 6. CREATE FactIrrigationDecision
------------------------------------------------------------
CREATE TABLE dbo.FactIrrigationDecision (
    id INT IDENTITY(1,1) PRIMARY KEY,
    date_id DATE NOT NULL,
    decision VARCHAR(10) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    yesterday_rain FLOAT NULL,
    today_rain FLOAT NULL,
    next_6hr_rain FLOAT NULL,
    IsActive BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_irrigation_date FOREIGN KEY (date_id)
        REFERENCES dbo.DimDate(date_id)
);
GO


---test query to check load

SELECT TOP 20 * FROM FactDailyWeather ORDER BY id DESC;
SELECT TOP 20 * FROM FactHourlyWeather ORDER BY id DESC;
SELECT TOP 20 * FROM FactIrrigationDecision ORDER BY id DESC;
SELECT * FROM DimDate;
SELECT * FROM DimWeatherCode;