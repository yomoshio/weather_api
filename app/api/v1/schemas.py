from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class WeatherRequest(BaseModel):
    city: str


class WeatherResponse(BaseModel):
    city: str
    country: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    icon: str
    timestamp: datetime


class CityResponse(BaseModel):
    name: str
    country: str
    lat: float
    lon: float


class CitySuggestionsResponse(BaseModel):
    suggestions: List[CityResponse]


class SearchHistoryItem(BaseModel):
    city: str
    temperature: float
    timestamp: datetime


class UserHistoryResponse(BaseModel):
    history: List[SearchHistoryItem]


class SearchStatsItem(BaseModel):
    city: str
    count: int


class SearchStatsResponse(BaseModel):
    stats: List[SearchStatsItem]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime