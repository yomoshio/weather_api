import aiohttp
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings


class WeatherService:
    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geo_url = "http://api.openweathermap.org/geo/1.0"
    
    async def search_cities(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Поиск городов по названию"""
        url = f"{self.geo_url}/direct"
        params = {
            "q": query,
            "limit": limit,
            "appid": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        {
                            "name": item["name"],
                            "display_name": f"{item['name']}, {item.get('state', '')}, {item['country']}".replace(", ,", ",").strip(", "),
                            "country": item["country"],
                            "lat": item["lat"],
                            "lon": item["lon"]
                        }
                        for item in data
                    ]
                else:
                    raise Exception(f"API Error: {response.status}")
    
    def _map_weather_code(self, openweather_id: int) -> int:
        """Маппинг OpenWeatherMap ID в упрощенные коды для emoji"""
        # Группируем похожие условия
        if 200 <= openweather_id <= 299:  # Thunderstorm
            return 95
        elif 300 <= openweather_id <= 399:  # Drizzle
            return 51
        elif 500 <= openweather_id <= 599:  # Rain
            return 61
        elif 600 <= openweather_id <= 699:  # Snow
            return 71
        elif 700 <= openweather_id <= 799:  # Atmosphere (fog, mist, etc.)
            return 45
        elif openweather_id == 800:  # Clear sky
            return 0
        elif openweather_id == 801:  # Few clouds
            return 1
        elif openweather_id == 802:  # Scattered clouds
            return 2
        elif openweather_id in [803, 804]:  # Broken/overcast clouds
            return 3
        else:
            return 1  # Default to partly cloudy
    
    async def get_weather_by_city(self, city: str) -> Dict[str, Any]:
        """Получение погоды по названию города"""
        try:
            # Получаем текущую погоду
            current_weather = await self._get_current_weather(city)
            
            # Получаем прогноз
            forecast_data = await self._get_forecast(city)
            
            return {
                "city": current_weather["city"],
                "current": {
                    "temperature": round(current_weather["temperature"]),
                    "weather": current_weather["description"].title(),
                    "weather_code": self._map_weather_code(current_weather["weather_id"]),
                    "humidity": current_weather["humidity"],
                    "wind_speed": round(current_weather.get("wind_speed", 0)),
                },
                "daily_forecast": forecast_data.get("daily", []),
                "hourly_forecast": forecast_data.get("hourly", [])
            }
        except Exception as e:
            raise Exception(f"Ошибка получения данных о погоде: {str(e)}")
    

    async def _get_current_weather(self, city: str) -> Dict[str, Any]:
        """Получение текущей погоды с улучшенной обработкой ошибок"""
        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Добавляем отладочную информацию
                    print(f"OpenWeather API response for {city}: {data}")
                    
                    # Проверяем наличие всех необходимых ключей
                    if "main" not in data:
                        raise Exception(f"Missing 'main' section in API response for {city}")
                    if "temp" not in data["main"]:
                        raise Exception(f"Missing 'temp' in main section for {city}")
                    if "weather" not in data or len(data["weather"]) == 0:
                        raise Exception(f"Missing weather information for {city}")
                    
                    return {
                        "city": data.get("name", city),
                        "country": data.get("sys", {}).get("country", ""),
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"].get("feels_like", data["main"]["temp"]),
                        "humidity": data["main"].get("humidity", 0),
                        "description": data["weather"][0].get("description", ""),
                        "weather_id": data["weather"][0].get("id", 800),
                        "wind_speed": data.get("wind", {}).get("speed", 0) * 3.6,  # м/с в км/ч
                    }
                elif response.status == 404:
                    raise Exception("Город не найден")
                elif response.status == 401:
                    raise Exception("Неверный API ключ OpenWeather")
                elif response.status == 429:
                    raise Exception("Превышен лимит запросов к API")
                else:
                    error_text = await response.text()
                    raise Exception(f"Ошибка API OpenWeather ({response.status}): {error_text}")
    
    async def _get_forecast(self, city: str) -> Dict[str, Any]:
        """Получение прогноза погоды"""
        url = f"{self.base_url}/forecast"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Обрабатываем почасовой прогноз (первые 8 часов)
                    hourly_forecast = []
                    for i, item in enumerate(data["list"][:8]):
                        hourly_forecast.append({
                            "time": item["dt_txt"],
                            "temperature": round(item["main"]["temp"]),
                            "weather": item["weather"][0]["description"].title(),
                            "precipitation_probability": round(item.get("pop", 0) * 100)
                        })
                    
                    # Обрабатываем дневной прогноз (группируем по дням)
                    daily_forecast = []
                    daily_data = {}
                    
                    for item in data["list"]:
                        date_str = item["dt_txt"].split()[0]  # Получаем только дату
                        
                        if date_str not in daily_data:
                            daily_data[date_str] = {
                                "temps": [],
                                "weather": item["weather"][0]["description"],
                                "precipitation": 0
                            }
                        
                        daily_data[date_str]["temps"].append(item["main"]["temp"])
                        if "rain" in item:
                            daily_data[date_str]["precipitation"] += item["rain"].get("3h", 0)
                    
                    # Формируем итоговый дневной прогноз
                    for date_str, day_data in list(daily_data.items())[:5]:
                        daily_forecast.append({
                            "date": date_str,
                            "temp_max": round(max(day_data["temps"])),
                            "temp_min": round(min(day_data["temps"])),
                            "weather": day_data["weather"].title(),
                            "precipitation": round(day_data["precipitation"], 1)
                        })
                    
                    return {
                        "daily": daily_forecast,
                        "hourly": hourly_forecast
                    }
                elif response.status == 404:
                    raise Exception("Город не найден")
                else:
                    raise Exception(f"Ошибка API: {response.status}")
    
    async def get_weather_by_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """Получение погоды по координатам"""
        url = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "city": data["name"],
                        "country": data["sys"]["country"],
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "description": data["weather"][0]["description"],
                        "weather_id": data["weather"][0]["id"]
                    }
                else:
                    raise Exception(f"API Error: {response.status}")
    
    async def get_forecast(self, city: str, days: int = 5) -> Dict[str, Any]:
        """Получение прогноза на несколько дней (старый метод для совместимости)"""
        return await self._get_forecast(city)