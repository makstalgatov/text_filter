from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="iTest text filter", version="1.0.0")

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="templates")

# --- Вспомогательная функция для обработки текста ---
def extract_numeric_lines(text: str) -> List[str]:
    """Извлекает числовые строки, следующие за строками, начинающимися с '42123'."""
    if not text:
        return []
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    results = []
    
    for i, line in enumerate(lines):
        if line.startswith("42123") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Проверяем, является ли следующая строка числом (возможно, со знаком '+')
            if next_line.isdigit() or (next_line.startswith("+") and next_line[1:].isdigit()):
                results.append(next_line)
    return results

# --- Эндпоинты ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Отображает главную страницу с формой."""
    return templates.TemplateResponse("index.html", {"request": request, "results": None, "error": None})

@app.post("/process", response_class=JSONResponse)
async def process_text_api(
    text: str = Form(...) # Используем Form(...) для обязательного поля
):
    """Обрабатывает текст и возвращает результат в формате JSON."""
    try:
        if not text.strip():
            # Дополнительная проверка на пустой ввод после пробелов
            raise HTTPException(status_code=400, detail="Please provide non-empty text.")

        logger.info("Processing text input via API")
        
        results = extract_numeric_lines(text)
        logger.info(f"Found {len(results)} matches")

        return JSONResponse(content={"results": results})
        
    except HTTPException as http_exc:
        # Перехватываем HTTPException, чтобы не логировать их как 500 ошибку
        logger.warning(f"HTTP Exception: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc # Повторно вызываем исключение для FastAPI
    except Exception as e:
        # Логируем другие неожиданные ошибки
        logger.error(f"Error processing text: {str(e)}", exc_info=True) # Добавляем exc_info для трассировки стека
        # Возвращаем общую ошибку 500 клиенту
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred."})

# --- Код ниже удален, так как HTML/CSS/JS перенесены ---
# HTML_TEMPLATE = ...
# @app.post("/process", response_class=HTMLResponse) ... (старая версия эндпоинта)
# Старый GET "/" также заменен на использование Jinja
