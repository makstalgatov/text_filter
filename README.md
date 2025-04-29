# iTest text filter

Простое веб-приложение для фильтрации текста, построенное с использованием FastAPI.

Приложение предоставляет веб-интерфейс, где пользователь может ввести многострочный текст. Бэкенд обрабатывает этот текст, находит строки, начинающиеся с "42123", и извлекает следующую за ними строку, если она является числом (возможно, с префиксом "+"). Результаты отображаются на веб-странице.

## ✨ Особенности

*   Веб-интерфейс на базе HTML, CSS, JavaScript.
*   Бэкенд на FastAPI.
*   Обработка многострочного текста.
*   Отображение отфильтрованных результатов.
*   Редактирование результатов прямо на странице.
*   Кнопка "Copy" для копирования результатов в буфер обмена.
*   Кнопка "Clear" для очистки поля ввода.
*   Счетчик найденных результатов.
*   Favicon.
*   Конфигурация для развертывания с помощью Docker и Docker Compose.
*   Настройка Nginx в Docker для работы в качестве обратного прокси с HTTPS (используя самоподписанный сертификат).

## 🚀 Технологический стек

*   **Бэкенд:** Python, FastAPI, Uvicorn
*   **Фронтенд:** HTML, CSS, JavaScript
*   **Шаблонизатор:** Jinja2
*   **Контейнеризация:** Docker, Docker Compose
*   **Веб-сервер/Прокси:** Nginx (в Docker)

## 🛠️ Установка и запуск

### Локально (для разработки)

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/makstalgatov/text_filter.git
    cd text_filter
    ```

2.  **Создайте и активируйте виртуальное окружение:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    # Для Windows: .venv\Scripts\activate
    ```

3.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Запустите приложение с Uvicorn:**
    ```bash
    uvicorn main:app --reload
    ```

5.  Откройте браузер и перейдите по адресу `http://127.0.0.1:8000`.

### С помощью Docker Compose (для развертывания/продакшена)

Этот способ запускает приложение и Nginx в Docker-контейнерах.

1.  **Установите Docker и Docker Compose:** Следуйте официальным инструкциям для вашей ОС.

2.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/makstalgatov/text_filter.git
    cd text_filter
    ```

3.  **Создайте самоподписанный SSL-сертификат:**
    *   Nginx настроен на использование HTTPS. Для этого требуются SSL-сертификат и ключ. Создайте их и поместите в папку `nginx/ssl/`. **Замените `<your-ip-or-domain>` на IP-адрес или доменное имя вашего сервера.**
        ```bash
        mkdir -p nginx/ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
             -keyout nginx/ssl/nginx-selfsigned.key \
             -out nginx/ssl/nginx-selfsigned.crt \
             -subj "/CN=<your-ip-or-domain>"
        ```
    *   ***Важно:*** Если вы уже добавили сертификаты в Git, этот шаг можно пропустить.

4.  **Запустите с помощью Docker Compose:**
    ```bash
    docker compose up --build -d
    ```
    *   `--build` пересобирает образ приложения, если нужно.
    *   `-d` запускает контейнеры в фоновом режиме.

5.  Откройте браузер и перейдите по адресу `https://<your-ip-or-domain>`.
    *   Вам нужно будет принять предупреждение браузера о безопасности, так как сертификат самоподписанный.

## ⚙️ Управление Docker-контейнерами

*   **Посмотреть статус:** `docker compose ps`
*   **Посмотреть логи:** `docker compose logs app` или `docker compose logs nginx` (добавьте `-f` для слежения в реальном времени).
*   **Остановить:** `docker compose down`
*   **Перезапустить после обновления кода:** `git pull origin main && docker compose up --build -d`

## 📂 Структура проекта

```
. 
├── .git/                # Директория Git 
├── nginx/               # Конфигурация и SSL для Nginx 
│   ├── nginx.conf 
│   └── ssl/ 
│       ├── nginx-selfsigned.crt 
│       └── nginx-selfsigned.key 
├── static/              # Статические файлы (CSS, JS, Favicon) 
│   ├── css/style.css 
│   ├── js/script.js 
│   └── favicon.ico 
├── templates/           # HTML шаблоны (Jinja2) 
│   └── index.html 
├── .gitignore           # Файлы, игнорируемые Git 
├── Dockerfile           # Инструкции для сборки Docker-образа приложения 
├── docker-compose.yml   # Конфигурация для запуска сервисов (app, nginx) 
├── main.py              # Основной код FastAPI приложения 
├── requirements.txt     # Зависимости Python 
└── README.md            # Этот файл 
``` 

## Configuration

To enable the "With Samples (ELK Lookup)" feature, you need to configure the following environment variables before running the application:

*   `ELK_URL`: The full URL to your Elasticsearch search endpoint (e.g., `http://elk.example.com:9200/filebeat-*/_search`).
*   `ELK_USER`: The username for Elasticsearch authentication.
*   `ELK_PASSWORD`: The password for Elasticsearch authentication.
*   `ELK_TIMEOUT` (Optional): The timeout in seconds for Elasticsearch queries (defaults to 15).

**Example (Linux/macOS):**

```bash
export ELK_URL="http://your-elk-url/.../_search"
export ELK_USER="your_elk_user"
export ELK_PASSWORD="your_elk_password"
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Example (Docker Compose):**

You can add these variables to the `environment` section of the `web` service in your `docker-compose.yml` file:

```yaml
services:
  web:
    # ... other settings ...
    environment:
      - ELK_URL=http://your-elk-url/.../_search
      - ELK_USER=your_elk_user
      - ELK_PASSWORD=your_elk_password
      - ELK_TIMEOUT=20 # Optional
    # ...
```

If these variables are not set, the application will still run, but the "With Samples (ELK Lookup)" logic will log a warning and will not be able to fetch data from Elasticsearch.

## Running the Application

# ... (rest of README) ... 