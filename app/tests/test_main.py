import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import uuid

from app.main import app
from app.models.models import SearchHistory


class TestMainApp:
    """Тесты основного приложения"""
    
    @pytest.fixture
    def client(self):
        """Синхронный клиент для тестирования"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Асинхронный клиент для тестирования"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    def test_home_page_without_cookies(self, client):
        """Тест главной страницы без cookies"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @patch('app.models.models.SearchHistory.filter')
    def test_home_page_with_user_history(self, mock_filter, client):
        """Тест главной страницы с историей пользователя"""
        # Мокаем историю поиска
        mock_search = Mock()
        mock_search.city = "Moscow"
        mock_filter.return_value.order_by.return_value.limit.return_value = AsyncMock(return_value=[mock_search])
        
        response = client.get("/", cookies={"user_id": "test-user-id"})
        assert response.status_code == 200
    
    def test_health_check(self, client):
        """Тест endpoint'а проверки здоровья"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @patch('app.api.v1.services.weather_service.WeatherService.search_cities')
    async def test_city_suggestions_success(self, mock_search_cities, async_client):
        """Тест успешного получения подсказок городов"""
        # Мокаем ответ сервиса
        mock_search_cities.return_value = [
            {
                "name": "Moscow",
                "display_name": "Moscow, Russia",
                "country": "RU",
                "lat": 55.7558,
                "lon": 37.6176
            }
        ]
        
        response = await async_client.get("/api/v1/cities/suggestions?q=Moscow")
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 1
        assert data["suggestions"][0]["name"] == "Moscow"
    
    @patch('app.api.v1.services.weather_service.WeatherService.search_cities')
    async def test_city_suggestions_error(self, mock_search_cities, async_client):
        """Тест ошибки при получении подсказок городов"""
        mock_search_cities.side_effect = Exception("API Error")
        
        response = await async_client.get("/api/v1/cities/suggestions?q=InvalidCity")
        assert response.status_code == 500
    
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    @patch('app.api.v1.routes.wait_for_celery_task')
    async def test_get_weather_success(self, mock_wait_task, mock_celery_task, async_client):
        """Тест успешного получения погоды"""
        # Мокаем Celery задачу
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        # Мокаем результат задачи
        weather_result = {
            "city": "Moscow",
            "current": {
                "temperature": 25,
                "weather": "Clear",
                "weather_code": 0,
                "humidity": 60,
                "wind_speed": 10
            },
            "daily_forecast": [],
            "hourly_forecast": []
        }
        mock_wait_task.return_value = weather_result
        
        response = await async_client.post(
            "/api/v1/weather",
            json={"city": "Moscow"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Moscow"
        assert data["current"]["temperature"] == 25
    
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    @patch('app.api.v1.routes.wait_for_celery_task')
    async def test_get_weather_city_not_found(self, mock_wait_task, mock_celery_task, async_client):
        """Тест обработки ошибки 'город не найден'"""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        mock_wait_task.return_value = {"error": "Город не найден"}
        
        response = await async_client.post(
            "/api/v1/weather",
            json={"city": "NonExistentCity"}
        )
        
        assert response.status_code == 404
    
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    @patch('app.api.v1.routes.wait_for_celery_task')
    async def test_get_weather_timeout(self, mock_wait_task, mock_celery_task, async_client):
        """Тест таймаута при получении погоды"""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        mock_wait_task.side_effect = asyncio.TimeoutError()
        
        response = await async_client.post(
            "/api/v1/weather",
            json={"city": "Moscow"}
        )
        
        assert response.status_code == 408
    
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    async def test_start_weather_task(self, mock_celery_task, async_client):
        """Тест запуска задачи получения погоды"""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        response = await async_client.post(
            "/api/v1/weather/start",
            json={"city": "Moscow"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
    
    @patch('celery.result.AsyncResult')
    def test_get_task_status_success(self, mock_async_result, client):
        """Тест получения статуса задачи - успех"""
        mock_result = Mock()
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"city": "Moscow", "temperature": 25}
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/task-status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert "result" in data
    
    @patch('celery.result.AsyncResult')
    def test_get_task_status_pending(self, mock_async_result, client):
        """Тест получения статуса задачи - в процессе"""
        mock_result = Mock()
        mock_result.ready.return_value = False
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/task-status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "PENDING"
    
    @patch('celery.result.AsyncResult')
    def test_get_task_status_failure(self, mock_async_result, client):
        """Тест получения статуса задачи - ошибка"""
        mock_result = Mock()
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.info = "Task failed"
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/task-status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "FAILURE"
        assert data["error"] == "Task failed"
    
    @patch('tortoise.connections.get')
    async def test_get_search_stats(self, mock_get_connection, async_client):
        """Тест получения статистики поиска"""
        # Мокаем соединение с БД
        mock_conn = Mock()
        mock_conn.execute_query_dict = AsyncMock(return_value=[
            {"city": "Moscow", "count": 10},
            {"city": "London", "count": 5}
        ])
        mock_get_connection.return_value = mock_conn
        
        response = await async_client.get("/api/v1/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "stats" in data
        assert len(data["stats"]) == 2
        assert data["stats"][0]["city"] == "Moscow"
        assert data["stats"][0]["count"] == 10
    
    @patch('app.models.models.SearchHistory.filter')
    async def test_get_user_history_with_user(self, mock_filter, async_client):
        """Тест получения истории пользователя"""
        # Мокаем историю
        mock_history = [
            Mock(city="Moscow", timestamp=datetime.now(), temperature=25),
            Mock(city="London", timestamp=datetime.now(), temperature=15)
        ]
        mock_filter.return_value.order_by.return_value.limit.return_value = AsyncMock(return_value=mock_history)
        
        response = await async_client.get(
            "/api/v1/user/history",
            cookies={"user_id": "test-user-id"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 2
    
    async def test_get_user_history_without_user(self, async_client):
        """Тест получения истории без user_id"""
        response = await async_client.get("/api/v1/user/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data["history"] == []
    
    def test_invalid_json_request(self, client):
        """Тест обработки некорректного JSON"""
        response = client.post(
            "/api/v1/weather",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_city_in_request(self, client):
        """Тест обработки запроса без города"""
        response = client.post(
            "/api/v1/weather",
            json={}
        )
        assert response.status_code == 422
    
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    @patch('app.api.v1.routes.wait_for_celery_task')
    async def test_get_weather_by_city_get_method(self, mock_wait_task, mock_celery_task, async_client):
        """Тест GET метода получения погоды по названию города"""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        weather_result = {
            "city": "Moscow",
            "current": {
                "temperature": 25,
                "weather": "Clear",
                "weather_code": 0,
                "humidity": 60,
                "wind_speed": 10
            }
        }
        mock_wait_task.return_value = weather_result
        
        response = await async_client.get("/api/v1/weather/Moscow")
        
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == "Moscow"


class TestUtilityFunctions:
    """Тесты вспомогательных функций"""
    
    @pytest.mark.asyncio
    async def test_wait_for_celery_task_success(self):
        """Тест успешного ожидания Celery задачи"""
        from app.api.v1.routes import wait_for_celery_task
        
        mock_task = Mock()
        mock_task.ready.return_value = True
        mock_task.successful.return_value = True
        mock_task.result = {"test": "data"}
        
        result = await wait_for_celery_task(mock_task, timeout=1)
        assert result == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_wait_for_celery_task_timeout(self):
        """Тест таймаута при ожидании Celery задачи"""
        from app.api.v1.routes import wait_for_celery_task
        
        mock_task = Mock()
        mock_task.ready.return_value = False
        
        with pytest.raises(Exception, match="Task timeout exceeded"):
            await wait_for_celery_task(mock_task, timeout=0.1)
    
    @pytest.mark.asyncio
    async def test_wait_for_celery_task_failure(self):
        """Тест неудачного выполнения Celery задачи"""
        from app.api.v1.routes import wait_for_celery_task
        
        mock_task = Mock()
        mock_task.ready.return_value = True
        mock_task.successful.return_value = False
        mock_task.info = "Task failed"
        
        with pytest.raises(Exception, match="Task failed"):
            await wait_for_celery_task(mock_task, timeout=1)


class TestCookieHandling:
    """Тесты обработки cookies"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    @patch('app.api.v1.routes.wait_for_celery_task')
    def test_cookie_creation_on_weather_request(self, mock_wait_task, mock_celery_task, client):
        """Тест создания cookie при запросе погоды"""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        mock_wait_task.return_value = {
            "city": "Moscow",
            "current": {"temperature": 25}
        }
        
        response = client.post("/api/v1/weather", json={"city": "Moscow"})
        

        assert "user_id" in response.cookies
        assert response.cookies["user_id"] is not None
        
    @patch('app.celery_dir.tasks.get_weather_async.delay')
    @patch('app.api.v1.routes.wait_for_celery_task')
    def test_existing_cookie_preserved(self, mock_wait_task, mock_celery_task, client):
        """Тест сохранения существующего cookie"""
        existing_user_id = str(uuid.uuid4())
        
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery_task.return_value = mock_task
        
        mock_wait_task.return_value = {
            "city": "Moscow",
            "current": {"temperature": 25}
        }
        
        response = client.post(
            "/api/v1/weather",
            json={"city": "Moscow"},
            cookies={"user_id": existing_user_id}
        )
        

        mock_celery_task.assert_called_once()
        args = mock_celery_task.call_args[0]
        assert args[1] == existing_user_id 