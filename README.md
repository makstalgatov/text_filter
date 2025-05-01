# iTest Text Filter

Веб-приложение для обработки текстовых данных из интерфейса iTest с использованием двух логик:
1.  **Only CLI:** Извлекает номера телефонов, следующие за строками, начинающимися с `42123...`.
2.  **With Samples (ELK):** Извлекает пары `CLI Sent` (начинающиеся с `42123...`) и `CLI Received`. Для каждой пары выполняет запрос к Elasticsearch (ELK), находит соответствующие логи звонков (INVITE и BYE), извлекает данные (`from`, `to`, `timestamp`) и форматирует результат. Обрабатывает отсутствующие `CLI Received` как "anonymous".

## Технологии

*   **Backend:** Python, FastAPI, Uvicorn
*   **Frontend:** HTML, CSS (Bootstrap 5), JavaScript
*   **База данных (логи):** Elasticsearch (ELK)
*   **Веб-сервер/Прокси:** Nginx
*   **Контейнеризация:** Docker, Docker Compose

## Предварительные требования

*   **Docker:** Установленный и запущенный Docker Engine. [Инструкция по установке Docker](https://docs.docker.com/engine/install/)
*   **Docker Compose:** Плагин Docker Compose (обычно устанавливается вместе с Docker Engine). [Инструкция по установке Docker Compose](https://docs.docker.com/compose/install/)
*   **Git:** (Опционально, для клонирования репозитория)
*   **Доступ к ELK:** URL, имя пользователя и пароль для доступа к вашему экземпляру Elasticsearch.

## Установка и Настройка

1.  **Клонировать репозиторий** (если необходимо):
    ```bash
    git clone <URL_вашего_репозитория>
    cd text_filter
    ```
    Или просто скопируйте файлы проекта на ваш сервер.

2.  **Создать файл `.env`:**
    В корневой директории проекта (`text_filter`) создайте файл с именем `.env` и добавьте в него учетные данные для доступа к Elasticsearch:
    ```dotenv
    ELK_URL=http://ss.ff.com:9200/filebeat-7.14.0*/_search # Замените на ваш URL ELK
    ELK_USER=admin                                        # Замените на вашего пользователя ELK
    ELK_PASSWORD=admin                                    # Замените на ваш пароль ELK
    ELK_TIMEOUT=15                                        # Таймаут запроса к ELK в секундах (опционально)
    ```
    **Важно:** Не добавляйте файл `.env` в систему контроля версий (Git). Ограничьте права доступа к этому файлу на сервере (`chmod 600 .env`).

3.  **(Опционально) Настроить IP Whitelisting в Nginx:**
    Отредактируйте файл `nginx/nginx.conf`. В секции `server` для порта `443 ssl` найдите блок `allow/deny` и укажите IP-адреса, с которых разрешен доступ к приложению.
    ```nginx
    # --- Ограничение доступа по IP ---
    allow   # Пример IP 1
    allow    # Пример IP 2
    # Добавьте или удалите нужные IP
    deny all; # Запретить все остальные
    # --- Конец ограничения ---
    ```

4.  **(Опционально, но рекомендуется) Настроить HTTPS с Let's Encrypt:**
    Текущая конфигурация Nginx использует самоподписанные сертификаты (`nginx/ssl/nginx-selfsigned.*`). Для безопасной работы в продуктивной среде настоятельно рекомендуется настроить получение и автоматическое обновление сертификатов от Let's Encrypt. Это можно сделать с помощью Certbot, интегрировав его в `docker-compose.yml` или запустив на хост-машине. Для этого потребуется доменное имя, указывающее на IP-адрес вашего сервера.

## Запуск приложения

1.  **Перейдите в директорию проекта:**
    ```bash
    cd text_filter
    ```

2.  **Собрать образы и запустить контейнеры:**
    ```bash
    docker compose up -d --build
    ```
    *   `up`: Создает и запускает контейнеры.
    *   `-d`: Запускает контейнеры в фоновом режиме (detached).
    *   `--build`: Пересобирает образы, если исходный код или Dockerfile изменились.

3.  **Проверить статус контейнеров:**
    ```bash
    docker compose ps
    ```
    Вы должны увидеть два запущенных контейнера: `itestfilter_app` и `itestfilter_nginx`.

## Доступ к приложению

*   Откройте веб-браузер и перейдите по адресу вашего сервера, используя **HTTPS**: `https://<IP-адрес_или_домен_сервера>/`
*   Если вы используете самоподписанные сертификаты, браузер покажет предупреждение безопасности, которое нужно будет принять.
*   Доступ может быть ограничен IP-адресами, настроенными в `nginx/nginx.conf`.

## Остановка приложения

Чтобы остановить и удалить контейнеры:
```bash
cd text_filter
docker compose down
```

## Логирование

*   Логи FastAPI приложения: `docker compose logs itestfilter_app`
*   Логи Nginx: `docker compose logs itestfilter_nginx`

## Безопасность

*   Используйте HTTPS с доверенными сертификатами (Let's Encrypt).
*   Настройте IP Whitelisting.
*   Обеспечьте безопасность файла `.env`.
*   Рассмотрите возможность запуска контейнера приложения от пользователя без root-прав.
*   Регулярно обновляйте зависимости и сканируйте образы на уязвимости.

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