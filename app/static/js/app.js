class WeatherApp {
    constructor() {
        this.cityInput = document.getElementById('cityInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.suggestions = document.getElementById('suggestions');
        this.loading = document.getElementById('loading');
        this.weatherResult = document.getElementById('weatherResult');
        this.statsContainer = document.getElementById('statsContainer');
        
        this.initEventListeners();
        this.loadStats();
    }
    
    initEventListeners() {
        this.cityInput.addEventListener('input', this.handleCityInput.bind(this));
        this.cityInput.addEventListener('keypress', this.handleKeyPress.bind(this));
        this.searchBtn.addEventListener('click', this.handleSearch.bind(this));

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideSuggestions();
            }
        });
    }
    
    async handleCityInput(e) {
        const query = e.target.value.trim();
        
        if (query.length >= 2) {
            try {
                // Добавляем таймаут для запроса
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 секунд
                
                const response = await fetch(`/api/v1/cities/suggestions?q=${encodeURIComponent(query)}`, {
                    signal: controller.signal,
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                console.log('Suggestions response:', data); // Отладка
                
                this.showSuggestions(data.suggestions || []);
            } catch (error) {
                console.error('Error fetching suggestions:', error);
                if (error.name === 'AbortError') {
                    console.log('Suggestions request timed out');
                }
                this.hideSuggestions();
            }
        } else {
            this.hideSuggestions();
        }
    }
    
    showSuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        // Исправляем обработку объектов city
        this.suggestions.innerHTML = suggestions
            .map((city, index) => {
                // Безопасное извлечение данных
                const cityName = city.name || city.city || city;
                const displayName = city.display_name || city.name || city.city || city;
                
                // Экранируем данные для безопасности
                const safeCityName = this.escapeHtml(String(cityName));
                const safeDisplayName = this.escapeHtml(String(displayName));
                
                return `
                    <div class="suggestion-item" 
                         data-city-name="${safeCityName}"
                         onclick="weatherApp.selectCityFromSuggestion(this)">
                        ${safeDisplayName}
                    </div>
                `;
            }).join('');
        
        this.suggestions.style.display = 'block';
    }
    
    // Безопасное экранирование HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    hideSuggestions() {
        this.suggestions.style.display = 'none';
    }
    
    // Новый метод для выбора города из подсказок
    selectCityFromSuggestion(element) {
        const cityName = element.getAttribute('data-city-name');
        this.selectCity(cityName);
    }
    
    selectCity(cityName) {
        this.cityInput.value = cityName;
        this.hideSuggestions();
        this.searchWeather(cityName);
    }
    
    handleKeyPress(e) {
        if (e.key === 'Enter') {
            this.handleSearch();
        }
    }
    
    handleSearch() {
        const city = this.cityInput.value.trim();
        if (city) {
            this.searchWeather(city);
        }
    }
    
    async searchWeather(city) {
        this.showLoading();
        this.hideSuggestions();
        
        try {
            // Добавляем таймаут для запроса погоды
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 секунд
            
            const response = await fetch('/api/v1/weather', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ city }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Добавим отладочную информацию
            console.log('Weather response data:', data);
            
            if (data.error) {
                this.showError(data.error);
            } else {
                this.showWeatherData(data);
                this.loadStats(); 
            }
        } catch (error) {
            console.error('Error fetching weather:', error);
            
            if (error.name === 'AbortError') {
                this.showError('Запрос превысил время ожидания. Попробуйте еще раз.');
            } else if (error.message.includes('fetch')) {
                this.showError('Ошибка соединения. Проверьте подключение к интернету.');
            } else {
                this.showError('Произошла ошибка при получении данных о погоде');
            }
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading() {
        this.loading.classList.remove('hidden');
        this.weatherResult.classList.add('hidden');
    }
    
    hideLoading() {
        this.loading.classList.add('hidden');
    }
    
    showError(message) {
        this.weatherResult.innerHTML = `
            <div class="error-message" style="text-align: center; padding: 40px; color: #e74c3c;">
                <h3>❌ Ошибка</h3>
                <p>${message}</p>
            </div>
        `;
        this.weatherResult.classList.remove('hidden');
    }
    
    showWeatherData(data) {
        // Безопасное извлечение данных с проверками
        const currentWeather = data.current || {};
        const city = data.city || 'Неизвестный город';
        const dailyForecast = data.daily_forecast || [];
        const hourlyForecast = data.hourly_forecast || [];
        
        // Безопасное получение emoji с проверкой
        const weatherCode = currentWeather.weather_code;
        const weatherEmoji = weatherCode !== undefined ? this.getWeatherEmoji(weatherCode) : '🌤️';
        
        // Проверяем наличие необходимых данных
        const temperature = currentWeather.temperature !== undefined ? `${currentWeather.temperature}°C` : 'N/A';
        const weather = currentWeather.weather || 'Данные недоступны';
        const humidity = currentWeather.humidity !== undefined ? `${currentWeather.humidity}%` : 'N/A';
        const windSpeed = currentWeather.wind_speed !== undefined ? `${currentWeather.wind_speed} км/ч` : 'N/A';
        
        this.weatherResult.innerHTML = `
            <div class="current-weather">
                <h2>${weatherEmoji} ${city}</h2>
                <div class="temperature">${temperature}</div>
                <div class="weather-condition">${weather}</div>
                
                <div class="weather-details">
                    <div class="detail-item">
                        <div>💧 Влажность</div>
                        <div>${humidity}</div>
                    </div>
                    <div class="detail-item">
                        <div>💨 Ветер</div>
                        <div>${windSpeed}</div>
                    </div>
                </div>
            </div>
            
            ${dailyForecast.length > 0 ? `
            <div class="forecast-section">
                <h3>📅 Прогноз на 5 дней</h3>
                <div class="daily-forecast">
                    ${dailyForecast.map(day => {
                        const date = new Date(day.date);
                        const weekday = date.toLocaleDateString('ru-RU', { weekday: 'short' });
                        const dayMonth = date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
                        
                        return `
                            <div class="forecast-item">
                                <div class="forecast-day">${weekday}</div>
                                <div class="forecast-date">${dayMonth}</div>
                                <div class="forecast-weather">${day.weather || 'N/A'}</div>
                                <div class="forecast-temp">
                                    <span style="color: #e74c3c;">${day.temp_max || 'N/A'}°</span> / 
                                    <span style="color: #3498db;">${day.temp_min || 'N/A'}°</span>
                                </div>
                                ${(day.precipitation || 0) > 0 ? `<div class="precipitation">☔ ${day.precipitation}мм</div>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
            ` : ''}
            
            ${hourlyForecast.length > 0 ? `
            <div class="forecast-section">
                <h3>🕐 Почасовой прогноз</h3>
                <div class="hourly-forecast">
                    ${hourlyForecast.slice(0, 8).map(hour => {
                        const time = new Date(hour.time);
                        const timeStr = time.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                        
                        return `
                            <div class="forecast-item">
                                <div class="forecast-time">${timeStr}</div>
                                <div class="forecast-weather">${hour.weather || 'N/A'}</div>
                                <div class="forecast-temp">${hour.temperature || 'N/A'}°C</div>
                                ${(hour.precipitation_probability || 0) > 0 ? 
                                    `<div class="precipitation-prob">☔ ${hour.precipitation_probability}%</div>` : ''
                                }
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
            ` : ''}
        `;
        
        this.weatherResult.classList.remove('hidden');
    }
    
    getWeatherEmoji(weatherCode) {
        const emojiMap = {
            0: '☀️',   // Clear sky
            1: '🌤️',   // Mainly clear
            2: '⛅',   // Partly cloudy
            3: '☁️',   // Overcast
            45: '🌫️',  // Fog
            48: '🌫️',  // Depositing rime fog
            51: '🌦️',  // Light drizzle
            53: '🌦️',  // Moderate drizzle
            55: '🌧️',  // Dense drizzle
            61: '🌧️',  // Slight rain
            63: '🌧️',  // Moderate rain
            65: '🌧️',  // Heavy rain
            71: '❄️',  // Slight snow
            73: '❄️',  // Moderate snow
            75: '❄️',  // Heavy snow
            95: '⛈️',  // Thunderstorm
            96: '⛈️',  // Thunderstorm with hail
            99: '⛈️'   // Severe thunderstorm
        };
        
        return emojiMap[weatherCode] || '🌤️';
    }
    
    async loadStats() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            const response = await fetch('/api/v1/stats', {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.showStats(data.stats || []);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    showStats(stats) {
        if (stats.length === 0) {
            this.statsContainer.innerHTML = '<p style="text-align: center; color: #666;">Статистика пока пуста</p>';
            return;
        }
        
        this.statsContainer.innerHTML = stats.map(stat => `
            <div class="stat-item">
                <span>${stat.city}</span>
                <span class="stat-count">${stat.count}</span>
            </div>
        `).join('');
    }
}

// Глобальная функция для поиска города (если нужна)
function searchCity(city) {
    weatherApp.searchWeather(city);
}

// Инициализация приложения
const weatherApp = new WeatherApp();