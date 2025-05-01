from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional, Dict
import logging
import re
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import json
import os # <-- Добавляем импорт os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ELK Configuration ---
# Читаем конфигурацию из переменных окружения
ELK_URL = os.getenv("ELK_URL")
ELK_USER = os.getenv("ELK_USER")
ELK_PASSWORD = os.getenv("ELK_PASSWORD")
ELK_TIMEOUT = int(os.getenv("ELK_TIMEOUT", "15")) # Таймаут тоже можно сделать переменной

# Проверка наличия необходимых переменных для ELK
if not all([ELK_URL, ELK_USER, ELK_PASSWORD]):
    logger.warning("ELK credentials (ELK_URL, ELK_USER, ELK_PASSWORD) are not fully configured in environment variables. 'With Samples' logic will likely fail.")
    # В зависимости от требований, можно выбросить исключение при старте
    # raise ValueError("Missing required ELK environment variables")

app = FastAPI(title="iTest text filter", version="1.0.0")

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="templates")

# --- Вспомогательные функции ---

def extract_numeric_lines(text: str) -> List[str]:
    """Извлекает числовые строки, следующие за строками, начинающимися с '42123'."""
    if not text:
        return []
    
    # Возвращаем старый метод итерации по строкам
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    results = []
    for i, line in enumerate(lines):
        if line.startswith("42123") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Проверяем, является ли следующая строка числом (возможно, со знаком '+')
            if next_line.isdigit() or (next_line.startswith("+") and next_line[1:].isdigit()):
                results.append(next_line)

    return results

def extract_cli_pairs(text: str) -> List[Dict[str, str]]:
    """Извлекает пары (CLI Sent, CLI Received), включая случаи с 'No CLI presented'."""
    if not text:
        return []

    lines = [line.strip() for line in text.splitlines() if line.strip()] # Убираем пустые строки
    pairs = []
    i = 0
    while i < len(lines):
        current_line = lines[i]
        # Проверяем, начинается ли текущая строка с 42123 и есть ли следующая строка
        if current_line.startswith("42123") and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Проверяем, является ли следующая строка валидным номером
            if next_line.isdigit() or (next_line.startswith("+") and next_line[1:].isdigit()):
                # Нашли валидную пару с номером!
                pairs.append({"sent": current_line, "received": next_line})
                # Перескакиваем через найденную пару
                i += 2
                continue # Переходим к следующей итерации внешнего цикла
            # --- Новая проверка: если следующая строка "No CLI presented" ---
            elif next_line == "No CLI presented":
                 # Нашли пару с "No CLI presented", сохраняем как "anonymous"
                 pairs.append({"sent": current_line, "received": "anonymous"})
                 # Перескакиваем через найденную пару
                 i += 2
                 continue # Переходим к следующей итерации внешнего цикла
            # --- Конец новой проверки ---

        # Если пара (валидная или "No CLI") не найдена на текущей строке,
        # просто переходим к следующей
        i += 1

    if not pairs:
         # Updated warning message
         logger.warning("No lines starting with '42123' followed by a number or 'No CLI presented' were found.")
         logger.debug("Text snippet where search failed (first 1000 chars): %s", text[:1000])
    else:
         # Updated info message
        logger.info(f"Extracted {len(pairs)} CLI pairs (including 'anonymous').")

    return pairs

def query_elk(cli_sent: str) -> Optional[Dict]:
    """Выполняет запрос к Elasticsearch для поиска записей по cli_sent за последние 3 дня."""
    # Дополнительная проверка перед запросом
    if not all([ELK_URL, ELK_USER, ELK_PASSWORD]):
        logger.error("Cannot query ELK: Credentials are not configured.")
        return None
        
    now = datetime.utcnow()
    three_days_ago = now - timedelta(days=3)
    
    # Форматируем даты для ELK range query
    # Используем 'strict_date_optional_time_nanos' совместимый формат
    gte_date = three_days_ago.strftime('%Y-%m-%dT%H:%M:%S.%fZ') 
    lt_date = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    query_payload = {
      "query": {
        "bool": {
          "must": [
            { "match": { "message": cli_sent }} 
          ],
          "filter": [
            {
              "range": {
                "@timestamp": {
                  "gte": gte_date, 
                  "lt": lt_date,
                  "format": "strict_date_optional_time_nanos||epoch_millis" # Добавляем формат
                }
              }
            }
          ]
        }
      },
      "size": 100, # Достаточно для поиска нужных записей
      "sort": [ { "@timestamp": "asc" } ] # Сортируем по времени
    }

    try:
        response = requests.post(
            ELK_URL,
            auth=HTTPBasicAuth(ELK_USER, ELK_PASSWORD),
            headers={'Content-Type': 'application/json'},
            json=query_payload, # Используем json параметр для авто-сериализации
            timeout=ELK_TIMEOUT
        )
        response.raise_for_status() # Вызовет исключение для кодов 4xx/5xx
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"ELK query timed out for {cli_sent}.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"ELK query failed for {cli_sent}: {e}")
         # Логируем тело ответа, если есть, для диагностики
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"ELK response status: {e.response.status_code}")
             logger.error(f"ELK response body: {e.response.text[:500]}...") # Ограничиваем длину
        return None
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response from ELK for {cli_sent}.")
        return None


def process_elk_hits(hits: List[Dict], cli_sent: str, delivered_cli: str) -> Optional[str]:
    """Обрабатывает результаты ELK: находит timestamp из message, BYE и INVITE, извлекает данные и форматирует строку."""
    if not hits:
        logger.warning(f"No ELK hits provided for processing {cli_sent}.")
        return None

    # Ищем timestamp в первом сообщении
    first_message = hits[0]["_source"].get("message", "")
    time_match = re.search(r"^\w+\s+\d+\s+(\d{2}:\d{2}:\d{2})", first_message) # Ищем ЧЧ:ММ:СС
    formatted_timestamp = None
    if time_match:
        extracted_time = time_match.group(1)
        # Если нужно добавить дату, можно взять ее из @timestamp, если он есть
        timestamp_field = hits[0]["_source"].get("@timestamp")
        if timestamp_field:
            try:
                # Use datetime.fromisoformat for potentially timezone-aware strings
                # Handle both 'Z' and '+HH:MM' offsets if present
                if timestamp_field.endswith('Z'):
                    timestamp_field = timestamp_field[:-1] + '+00:00'
                dt_object = datetime.fromisoformat(timestamp_field)
                date_part = dt_object.strftime('%Y-%m-%d')
                formatted_timestamp = f"{date_part} {extracted_time}"
                logger.debug(f"Extracted time '{extracted_time}' from message, combined with date '{date_part}' from @timestamp for {cli_sent}")
            except ValueError:
                 logger.warning(f"Could not parse date from '@timestamp': {timestamp_field} for {cli_sent}. Using time only.")
                 formatted_timestamp = extracted_time # Используем только время, если дата не парсится
        else:
            logger.debug(f"Extracted time '{extracted_time}' from message for {cli_sent}, @timestamp field missing.")
            formatted_timestamp = extracted_time # Используем только время, если @timestamp нет
    else:
        logger.warning(f"Could not extract HH:MM:SS time from the beginning of the first message for {cli_sent}. Message: '{first_message[:100]}...' Attempting fallback to @timestamp.")
        # Можно добавить fallback на @timestamp, если он есть и время не найдено
        timestamp_field = hits[0]["_source"].get("@timestamp")
        if timestamp_field:
             try:
                 # Use datetime.fromisoformat for potentially timezone-aware strings
                 if timestamp_field.endswith('Z'):
                    timestamp_field = timestamp_field[:-1] + '+00:00'
                 dt_object = datetime.fromisoformat(timestamp_field)
                 formatted_timestamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')
                 logger.info(f"Using fallback timestamp from '@timestamp' field for {cli_sent}: {formatted_timestamp}")
             except ValueError:
                 logger.error(f"Could not parse fallback timestamp '@timestamp': {timestamp_field} for {cli_sent}.")
                 return None # Не можем получить время
        else:
             logger.error(f"Could not extract time from message and '@timestamp' field is missing for {cli_sent}.")
             return None # Не можем получить время

    bye_message_source = None
    invite_message_source = None
    call_id = None

    # Сначала найдем BYE и извлечем call_id
    for hit in hits:
        message = hit.get("_source", {}).get("message", "")
        if "method=BYE;" in message:
            bye_message_source = hit.get("_source")
            call_id_match = re.search(r'call_id=([^;@]+)', message) # Извлекаем call_id
            if call_id_match:
                call_id = call_id_match.group(1)
            logger.debug(f"Found BYE message for {cli_sent}. Call ID: {call_id}")
            break

    if not bye_message_source or not call_id:
        logger.warning(f"Could not find BYE message or Call ID for {cli_sent}. Cannot process.")
        return None

    # Теперь найдем соответствующий INVITE по call_id
    for hit in hits:
        message = hit.get("_source", {}).get("message", "")
        if f"method=INVITE;" in message and f"call_id={call_id}" in message:
            invite_message_source = hit.get("_source")
            logger.debug(f"Found matching INVITE message for {cli_sent} with Call ID: {call_id}")
            break

    if not invite_message_source:
        logger.warning(f"Could not find matching INVITE message for Call ID {call_id} ({cli_sent}). Cannot determine 'To' number.")
        # В зависимости от требований, можно либо вернуть None, либо продолжить без 'To'?
        # Пока возвращаем None, так как 'To' нужен для результата.
        return None

    # --- Извлечение данных ---
    bye_message_content = bye_message_source.get("message", "")
    invite_message_content = invite_message_source.get("message", "")

    # Из BYE
    src_user_bye_match = re.search(r'src_user=(\d+)', bye_message_content)
    dst_user_bye_match = re.search(r'dst_user=(\d+)', bye_message_content)
    dst_ouser_bye_match = re.search(r'dst_ouser=(\+?\d+)', bye_message_content)

    # Из INVITE (нужен только dst_user)
    dst_user_invite_match = re.search(r'dst_user=(\d+)', invite_message_content)

    # Проверка наличия всех нужных полей
    if not (src_user_bye_match and dst_user_bye_match and dst_ouser_bye_match and dst_user_invite_match):
        logger.warning(f"Could not extract all required fields from BYE/INVITE messages for {cli_sent} (Call ID: {call_id}).")
        logger.debug(f"BYE Fields: src_user={src_user_bye_match}, dst_user={dst_user_bye_match}, dst_ouser={dst_ouser_bye_match}")
        logger.debug(f"INVITE Fields: dst_user={dst_user_invite_match}")
        return None

    src_user_in_bye = src_user_bye_match.group(1)
    dst_user_in_bye = dst_user_bye_match.group(1)
    dst_ouser = dst_ouser_bye_match.group(1)
    dst_user_in_invite = dst_user_invite_match.group(1) # Это номер "to"

    # --- Верификация ---
    # Проверяем, что cli_sent совпадает ЛИБО с src_user из BYE, ЛИБО с dst_user из BYE
    if cli_sent != src_user_in_bye and cli_sent != dst_user_in_bye:
        logger.warning(f"Verification failed for {cli_sent}: Neither src_user ({src_user_in_bye}) nor dst_user ({dst_user_in_bye}) in BYE message match original CLI Sent.")
        return None
    logger.debug(f"Verification passed for {cli_sent}: Found in BYE src_user or dst_user.")
    # --- Конец Верификации ---

    # --- Формируем итоговую строку ---

    # Определяем номер "from" на основе dst_ouser из BYE и префикса
    dst_ouser_prefix = "699954"
    default_from_number = "441224607102" # Номер по умолчанию, если префикс не совпадает

    from_number = default_from_number # По умолчанию
    if dst_ouser.startswith(dst_ouser_prefix):
        from_number_suffix = dst_ouser[len(dst_ouser_prefix):] # Берем часть после префикса
        # Формируем полный номер "from" (например, "421" + остаток)
        # !!! УТОЧНЕНИЕ: Здесь используется жестко заданный префикс "421". Убедитесь, что это правильно.
        potential_from = "421" + from_number_suffix # Пример, нужно уточнить правило
        # Здесь можно добавить проверку на длину или формат potential_from, если нужно
        from_number = potential_from
        logger.debug(f"Constructed 'from' number: {from_number} from dst_ouser: {dst_ouser}")
    else:
        logger.debug(f"dst_ouser ({dst_ouser}) does not start with prefix {dst_ouser_prefix}. Using default 'from' number: {default_from_number}")


    # Номер "to" - это dst_user из INVITE
    to_number = dst_user_in_invite

    # Собираем результат, используя 'formatted_timestamp', полученный ранее
    # Возвращаем формат: "YYYY-MM-DD HH:MM:SS UTC from [num] to [num] | CLI displayed [num]"
    result_string = f"{formatted_timestamp} UTC from {from_number} to {to_number} | CLI displayed {delivered_cli}"
    logger.info(f"Successfully processed ELK results for {cli_sent}. Result: {result_string}")
    return result_string


# --- Эндпоинты ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Отображает главную страницу с формой."""
    return templates.TemplateResponse("index.html", {"request": request, "results": None, "error": None})


@app.post("/process", response_class=JSONResponse)
async def process_text_api(
    text: str = Form(...), 
    logic_choice: str = Form(...) 
):
    """Обрабатывает текст и возвращает результат в формате JSON."""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Please provide non-empty text.")

        # Логируем начало обработки и часть входного текста
        logger.info(f"Processing request with logic: {logic_choice}")
        logger.debug(f"Received text (first 500 chars): {text[:500]}...") 
        
        final_results = [] 
        
        if logic_choice == "only_cli":
            logger.info("Using 'Only CLI' logic")
            final_results = extract_numeric_lines(text) 
            logger.info(f"'Only CLI' logic found {len(final_results)} results.")
        
        elif logic_choice == "with_samples":
            logger.info("Starting 'With Samples (ELK)' logic")
            cli_pairs = extract_cli_pairs(text)
            logger.info(f"Extracted {len(cli_pairs)} CLI pairs.")
            if cli_pairs:
                logger.debug(f"First extracted pair (if any): {cli_pairs[0]}")
            else:
                logger.warning("No CLI pairs were extracted. Check input text format and regex in `extract_cli_pairs`.")
                # Возвращаем пустой результат, если пар нет
                return JSONResponse(content={"results": []}) 
            
            for i, pair in enumerate(cli_pairs):
                cli_sent = pair['sent']
                delivered_cli = pair['received']
                logger.info(f"--- Processing pair {i+1}/{len(cli_pairs)}: sent={cli_sent}, received={delivered_cli} ---")
                
                # Шаг 2a: Запрос к ELK
                logger.debug(f"Querying ELK for: {cli_sent}")
                elk_response = query_elk(cli_sent)
                
                if elk_response:
                     # Логируем часть ответа для проверки
                    logger.debug(f"ELK response received for {cli_sent}. Keys: {list(elk_response.keys())}")
                    if 'hits' in elk_response and isinstance(elk_response['hits'], dict):
                        total_hits_value = elk_response['hits'].get('total', {}).get('value', 'N/A')
                        hits_list = elk_response['hits'].get('hits', [])
                        logger.info(f"ELK reported {total_hits_value} total hits for {cli_sent}. Received {len(hits_list)} hits in response.")
                        logger.debug(f"First hit (if any): {str(hits_list[0])[:300]}..." if hits_list else "No hits in list.")
                        
                        # Шаг 2b, 2c, 2d: Обработка результатов ELK
                        if hits_list:
                             logger.debug(f"Processing {len(hits_list)} ELK hits for {cli_sent}...")
                             processed_result = process_elk_hits(hits_list, cli_sent, delivered_cli)
                             if processed_result:
                                 logger.info(f"Successfully processed ELK data for {cli_sent}. Result: {processed_result}")
                                 final_results.append(processed_result)
                             else:
                                 logger.warning(f"Processing ELK hits for {cli_sent} did not yield a result (check logs for process_elk_hits warnings).")
                        else:
                             logger.info(f"No hits returned in the list for {cli_sent}, cannot process.")
                    else:
                         logger.error(f"Unexpected ELK response format for {cli_sent}. 'hits' key missing or not a dictionary. Response snippet: {str(elk_response)[:500]}...")
                else:
                     # Логируем, что запрос к ELK не удался
                    logger.warning(f"ELK query failed or returned no response for {cli_sent} (check previous logs for request errors).")
            
            logger.info(f"Finished processing all {len(cli_pairs)} pairs for 'With Samples'. Generated {len(final_results)} final results.")

        else:
            logger.warning(f"Unknown logic choice received: {logic_choice}")
            raise HTTPException(status_code=400, detail=f"Invalid logic choice: {logic_choice}")

        logger.info(f"Generated {len(final_results)} results for logic '{logic_choice}'")

        return JSONResponse(content={"results": final_results}) # Возвращаем final_results
        
    except HTTPException as http_exc:
        logger.warning(f"HTTP Exception: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc 
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}", exc_info=True) 
        # Используем стандартный ответ FastAPI для 500 ошибки, он вернет JSON
        raise HTTPException(status_code=500, detail="An internal server error occurred during processing.")

# --- Код ниже удален, так как HTML/CSS/JS перенесены ---
# HTML_TEMPLATE = ...
# @app.post("/process", response_class=HTMLResponse) ... (старая версия эндпоинта)
# Старый GET "/" также заменен на использование Jinja
