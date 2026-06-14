-- preloading the weather codes

INSERT INTO DimWeatherCode (weather_code, description, IsActive) VALUES
(0,  'Clear sky', 1),
(1,  'Mainly clear', 1),
(2,  'Partly cloudy', 1),
(3,  'Overcast', 1),

(45, 'Fog', 1),
(48, 'Depositing rime fog', 1),

(51, 'Light drizzle', 1),
(53, 'Moderate drizzle', 1),
(55, 'Dense drizzle', 1),
(56, 'Light freezing drizzle', 1),
(57, 'Dense freezing drizzle', 1),

(61, 'Slight rain', 1),
(63, 'Moderate rain', 1),
(65, 'Heavy rain', 1),
(66, 'Light freezing rain', 1),
(67, 'Heavy freezing rain', 1),

(71, 'Slight snow', 1),
(73, 'Moderate snow', 1),
(75, 'Heavy snow', 1),
(77, 'Snow grains', 1),

(80, 'Slight rain showers', 1),
(81, 'Moderate rain showers', 1),
(82, 'Violent rain showers', 1),

(85, 'Slight snow showers', 1),
(86, 'Heavy snow showers', 1),

(95, 'Thunderstorm', 1),
(96, 'Thunderstorm with slight hail', 1),
(99, 'Thunderstorm with heavy hail', 1);


-- select * from [dbo].[DimWeatherCode]
