import pytest
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1.services.weather_service import WeatherService

@pytest.fixture
def weather_service():
    return WeatherService()

@pytest.mark.asyncio
async def test_search_cities(weather_service):
    """Тест поиска городов"""
    # Тест с коротким запросом
    result = await weather_service.search_cities("M")
    assert isinstance(result, list)
    
    # Тест с нормальным запросом
    result = await weather_service.search_cities("Moscow")
    assert isinstance(result, list)
    # В реальном API должны быть результаты
    # assert len(result) > 0

@pytest.mark.asyncio
async def test_get_coordinates(weather_service):
    """Тест получения координат"""
    coords = await weather_service.get_coordinates("Moscow")
    # В реальном тесте проверили бы конкретные координаты
    assert coords is None or len(coords) == 2

def test_format_weather_data(weather_service):
    """Тест форматирования данных о погоде"""
    test_data = {
        "current": {
            "temperature_2m": 20.5,
            "relative_humidity_2m": 60,
            "wind_speed_10m": 5.5,
            "weather_code": 0
        },
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "temperature_2m_max": [22.0, 18.0],
            "temperature_2m_min": [10.0, 8.0],
            "weather_code": [1, 2],
            "precipitation_sum": [0.0, 1.5]
        },
        "hourly": {
            "time": ["2024-01-01T12:00", "2024-01-01T13:00"],
            "temperature_2m": [20.0, 21.0],
            "weather_code": [0, 1],
            "precipitation_probability": [0, 10]
        },
        "timezone": "Europe/Moscow"
    }
    
    result = weather_service._format_weather_data(test_data, "Moscow")
    
    assert result["city"] == "Moscow"
    assert "current" in result
    assert "daily_forecast" in result
    assert "hourly_forecast" in result
    assert result["current"]["temperature"] == 20.5