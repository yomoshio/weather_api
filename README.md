# Weather Forecast Application

Веб-приложение для получения прогноза погоды с использованием FastAPI, Tortoise ORM, Celery и Redis.

## Реализованные функции

### ✅ Основные требования
- ✅ Веб-приложение на FastAPI с современной архитектурой
- ✅ Ввод названия города и получение прогноза погоды
- ✅ Удобно читаемый формат вывода данных
- ✅ Использование OpenWeatherMap API для получения данных о погоде

### 🎯 Дополнительные возможности (бонусы)
- ✅ **Тесты** - pytest для тестирования API и сервисов
- ✅ **Docker контейнеры** - полная контейнеризация приложения
- ✅ **Автодополнение городов** - динамические подсказки при вводе
- ✅ **История поиска** - сохранение последних запросов пользователя
- ✅ **API статистики** - показывает количество поисков по городам
- ✅ **Celery + Redis** - асинхронная обработка запросов
- ✅ **PostgreSQL** - надежная реляционная база данных

### 🚀 Дополнительные улучшения
- ✅ Современный отзывчивый интерфейс
- ✅ Почасовой прогноз на 12 часов
- ✅ 5-дневный прогноз погоды
- ✅ Подробная информация (влажность, скорость ветра, ощущаемая температура)
- ✅ Эмодзи для разных типов погоды
- ✅ Сохранение истории поиска в PostgreSQL
- ✅ Чистая архитектура с разделением на слои
- ✅ Pydantic схемы для валидации данных

## Используемые технологии

- **Backend**: FastAPI, Tortoise ORM, PostgreSQL
- **Async Tasks**: Celery, Redis
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **HTTP Client**: aiohttp для асинхронных запросов
- **API**: OpenWeatherMap API
- **Containerization**: Docker, Docker Compose
- **Testing**: pytest, pytest-asyncio
- **Data Validation**: Pydantic
- **Database Migrations**: Aerich

## Архитектура проекта

```
├── app/
│   ├── core/
│   │   ├── config.py               # Настройки приложения
│   │   └── database.py             # Конфигурация БД
│   ├── api/v1/
│   │   ├── routes.py               # API эндпоинты
│   │   ├── schemas.py              # Pydantic схемы
│   │   └── services/
│   │       └── weather_service.py  # Сервис для работы с погодой
│   └── celery_dir/
│   |    ├── celery_app.py           # Конфигурация Celery
│   |   └── tasks.py                # Celery задачи
│   └──models/
│   |    └── models.py                   # Tortoise ORM модели
│   └──static/
│   |    ├── css/
│   |    │   └── style.css
│   |    └── js/
│   |        └── app.js
│   └──templates/
│   |    └── index.html
│   └──tests/
│       ├── test_main.py
│       ├── test_weather_service.py
│       └── test_models.py
        main.py   
├── docker-compose.yml              # Docker Compose конфигурация
├── Dockerfile                      # Docker образ
├── requirements.txt                # Python зависимости
└── .env.example                    # Пример конфигурации
```

## Как запустить

### 🐳 Запуск с Docker (рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yomoshio/weather_api
cd weather-app
```

2. Создайте `.env` файл:
```bash
cp .env.example .env
# Отредактируйте .env и добавьте ваш API ключ OpenWeatherMap
```

3. Запустите приложение:
```bash
docker-compose up --build
```

4. Откройте браузер и перейдите по адресу:
- **Приложение**: http://localhost:8000
- **База данных**: PostgreSQL на порту 5432
- **Redis**: Redis на порту 6379

### 🐍 Локальный запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения:
```bash
export DATABASE_USER="USER"
export DATABASE_PASSWORD="PASS"
export DATABASE_NAME="DB_NAME"
export REDIS_URL="redis://localhost:6379"
export WEATHER_API_KEY="your_openweathermap_api_key"
```

3. Запустите PostgreSQL и Redis:
```bash
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

4. Инициализируйте базу данных:
```bash
cd app/
aerich init -t core.database.TORTOISE_ORM
aerich init-db
```

5. Запустите Celery worker:
```bash
celery -A app.celery.celery_app worker --loglevel=info
```

6. Запустите приложение:
```bash
python -m app.main
```

### 🧪 Запуск тестов

```bash
# Установите тестовые зависимости
pip install pytest pytest-asyncio httpx

# Запустите тесты
pytest tests/ -v

# Запустите тесты с покрытием
pytest tests/ -v --cov=app --cov-report=html
```

## API Endpoints

### Основные эндпоинты
- `GET /` - Главная страница
- `GET /api/v1/cities/suggestions?q={query}` - Автодополнение городов
- `POST /api/v1/weather` - Получение прогноза погоды
- `GET /api/v1/weather/{city}` - Получение прогноза по названию города
- `GET /api/v1/stats` - Статистика поиска городов
- `GET /api/v1/user/history` - История поиска пользователя
- `GET /api/v1/health` - Проверка состояния приложения
- `GET /api/v1/task-status/{task_id}` - Проверка статуса celery задачи

### Примеры запросов

#### Получение прогноза погоды
```bash
curl -X POST "http://localhost:8000/api/v1/weather" \
     -H "Content-Type: application/json" \
     -d '{"city": "Moscow"}'
```

#### Автодополнение городов
```bash
curl "http://localhost:8000/api/v1/cities/suggestions?q=Mosc"
```

## Особенности реализации

### Современная архитектура
- **Clean Architecture**: Разделение на слои (API, Services, Models)
- **Dependency Injection**: Использование FastAPI Depends
- **Async/Await**: Полностью асинхронный код
- **Type Hints**: Строгая типизация Python

### Асинхронная обработка
Получение данных о погоде происходит через Celery задачи, что позволяет:
- Не блокировать основной поток приложения
- Обрабатывать множество запросов одновременно
- Масштабировать обработку задач независимо от веб-сервера

### База данных
- **Tortoise ORM**: Современная async ORM для Python
- **PostgreSQL**: Надежная реляционная СУБД
- **Aerich**: Миграции для Tortoise ORM
- **Connection Pooling**: Эффективное управление соединениями

### Валидация данных
- **Pydantic**: Схемы для валидации входных и выходных данных
- **Type Safety**: Автоматическая проверка типов
- **API Documentation**: Автогенерация OpenAPI схемы

### Безопасность
- Валидация входных данных через Pydantic
- Защита от SQL инъекций через Tortoise ORM
- Таймауты для внешних API запросов
- Безопасная обработка пользовательских данных

### Пользовательский опыт
- Автодополнение с задержкой для уменьшения количества запросов
- Сохранение предпочтений пользователя в cookies
- Отзывчивый дизайн для мобильных устройств
- Индикаторы загрузки и обработки ошибок

## Мониторинг и отладка

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Логи приложения
```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f web
docker-compose logs -f celery
```

### Мониторинг задач Celery
```bash
# Просмотр активных задач
celery -A app.celery_dir.celery_app inspect active

# Статистика воркеров
celery -A app.celery_dir.celery_app inspect stats
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgres://postgres:password@localhost:5432/weather_db` |
| `REDIS_URL` | URL подключения к Redis | `redis://localhost:6379` |
| `WEATHER_API_KEY` | API ключ OpenWeatherMap | Обязательный |

### Настройки Celery
- **Broker**: Redis
- **Backend**: Redis
- **Serialization**: JSON
- **Timezone**: UTC
- **Result Expiry**: 1 час

## Производительность

### Оптимизации
- Async I/O для всех внешних запросов
- Connection pooling для базы данных
- Эффективные SQL запросы с индексами
- Кэширование результатов Celery задач

### Масштабирование
- Горизонтальное масштабирование Celery воркеров
- Репликация PostgreSQL для чтения
- Load balancing для веб-серверов
- Кэширование с Redis

## Возможные улучшения

1. **Кэширование**: Кэширование результатов погоды в Redis
2. **WebSocket**: Реальное время обновления данных
3. **Геолокация**: Автоматическое определение местоположения
4. **Метрики**: Prometheus + Grafana для мониторинга
5. **Аутентификация**: JWT токены для пользователей
6. **Rate Limiting**: Ограничение количества запросов
7. **CDN**: Для статических файлов
8. **Backup**: Автоматическое резервное копирование БД

## Разработка

### Добавление новых эндпоинтов
1. Создайте Pydantic схему в `app/api/v1/schemas.py`
2. Добавьте эндпоинт в `app/api/v1/routes.py`
3. При необходимости создайте сервис в `app/api/v1/services/`
4. Напишите тесты в `tests/`

### Работа с базой данных
```bash
# Создание новой миграции
aerich migrate --name describe_changes

# Применение миграций
aerich upgrade

# Откат миграции
aerich downgrade
```

### Запуск в режиме разработки
```bash
# Автоперезагрузка при изменениях
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Отладочный режим Celery
celery -A app.celery_dir.celery_app worker --loglevel=debug
```

---

Разработано с ❤️ используя FastAPI, Tortoise ORM и современные веб-технологии.
