#!/usr/bin/env python3
"""
Анализатор JSONL файлов с помощью OpenRouter API
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from dotenv import load_dotenv
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jsonl_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
# Исправляем проблему с путями для WSL/Windows
try:
    # Сначала пробуем найти .env в текущей директории
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Загружен .env файл из: {env_path}")
    else:
        # Если не найден, пробуем стандартный поиск
        load_dotenv()
        logger.info("Загружен .env файл через стандартный поиск")
except Exception as e:
    logger.warning(f"Не удалось загрузить .env файл: {e}")
    # Продолжаем работу, переменные окружения могут быть установлены системно

class OpenRouterClient:
    """Клиент для работы с OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        logger.info(f"API ключ из переменных окружения: {'найден' if self.api_key else 'не найден'}")
        
        if not self.api_key:
            # Пробуем загрузить из .env файла напрямую
            try:
                # Пробуем разные пути к .env файлу
                possible_paths = [
                    Path(__file__).parent / '.env',
                    Path('.env'),
                    Path('/home/andrey/projects/Cursor/4_CSV_MD/2_JSONL_AI/.env'),
                    Path('//wsl.localhost/Ubuntu-24.04/home/andrey/projects/Cursor/4_CSV_MD/2_JSONL_AI/.env')
                ]
                
                for env_path in possible_paths:
                    logger.info(f"Проверяем путь: {env_path}")
                    if env_path.exists():
                        logger.info(f"Найден .env файл: {env_path}")
                        load_dotenv(env_path)
                        self.api_key = os.getenv('OPENROUTER_API_KEY')
                        if self.api_key:
                            logger.info("API ключ успешно загружен из .env файла")
                            break
                
                if not self.api_key:
                    logger.error("API ключ не найден в .env файлах")
                    raise ValueError("OPENROUTER_API_KEY не найден")
                    
            except Exception as e:
                logger.error(f"Ошибка при загрузке .env файла: {e}")
                raise ValueError("Не удалось загрузить API ключ")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Andrey0125/4_CSV_MD",
            "X-Title": "TG каналы обработка CSV в MarkDown"
        }
        
        # Список моделей (исключаем бесплатные, которые дают 404)
        self.models = [
            "meta-llama/llama-3.1-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "microsoft/phi-3-mini-128k-instruct",
            "google/gemini-flash-1.5",
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o-mini",
            "openai/gpt-4o"
        ]
        
        self.current_model_index = 0
        self.retry_count = 0
        self.max_retries = 3
    
    def generate_title(self, text: str) -> Optional[str]:
        """Генерирует заголовок для текста поста"""
        if not text or len(text.strip()) < 10:
            return "Короткий пост"
        
        # Обрезаем текст до 2000 символов для экономии токенов
        truncated_text = text[:2000] + "..." if len(text) > 2000 else text
        
        prompt = f"""Создай краткий и информативный заголовок для этого поста из Telegram канала. 
Заголовок должен быть на русском языке, отражать суть поста и быть не более 60 символов.

Текст поста:
{truncated_text}

Заголовок:"""
        
        payload = {
            "model": self.models[self.current_model_index],
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                title = data['choices'][0]['message']['content'].strip()
                # Убираем кавычки если есть
                title = title.strip('"\'')
                return title
            elif response.status_code == 404:
                logger.warning(f"Модель {self.models[self.current_model_index]} недоступна (404)")
                return self._try_next_model(text)
            else:
                logger.warning(f"Ошибка API: {response.status_code} - {response.text}")
                return self._try_next_model(text)
                
        except requests.exceptions.Timeout:
            logger.warning("Таймаут запроса к OpenRouter API")
            return self._try_next_model(text)
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenRouter API: {e}")
            return self._try_next_model(text)
    
    def _try_next_model(self, text: str) -> Optional[str]:
        """Пробует следующую модель в списке"""
        self.current_model_index += 1
        self.retry_count += 1
        
        if self.current_model_index >= len(self.models):
            self.current_model_index = 0
            logger.warning("Все модели исчерпаны, возвращаемся к первой")
        
        if self.retry_count >= self.max_retries:
            logger.error("Превышено максимальное количество попыток")
            return "Ошибка генерации заголовка"
        
        logger.info(f"Попытка {self.retry_count} с моделью {self.models[self.current_model_index]}")
        return self.generate_title(text)


class JSONLAnalyzer:
    """Анализатор JSONL файлов"""
    
    def __init__(self):
        self.client = OpenRouterClient()
        self.input_dir = "/home/andrey/projects/Cursor/4_CSV_MD/1_CSV_1/input"  # внутри 4_CSV_MD
        self.output_dir = "/home/andrey/projects/Cursor/4_CSV_MD/2_JSONL_AI/output"
        
        # Создаем выходную директорию
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def process_jsonl_file(self, file_path: Path, max_lines: Optional[int] = None) -> None:
        """Обрабатывает JSONL файл и добавляет заголовки"""
        logger.info(f"Обработка файла: {file_path}")
        
        processed_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as infile, \
             open(Path(self.output_dir) / "analyzed_combined_posts.jsonl", 'w', encoding='utf-8') as outfile:
            
            for line_num, line in enumerate(infile, 1):
                if max_lines and line_num > max_lines:
                    logger.info(f"Достигнут лимит {max_lines} строк, останавливаем обработку")
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # Ищем поле с текстом поста
                    text_content = ""
                    for field in ['text', 'content', 'message', 'post']:
                        if field in data and data[field]:
                            text_content = str(data[field])
                            break
                    
                    if not text_content:
                        logger.warning(f"Строка {line_num}: не найден текст поста")
                        outfile.write(line + '\n')
                        continue
                    
                    # Генерируем заголовок
                    logger.info(f"Попытка {self.client.retry_count + 1} с моделью {self.client.models[self.client.current_model_index]}")
                    title = self.client.generate_title(text_content)
                    
                    if title and title != "Ошибка генерации заголовка":
                        data['ai_generated_title'] = title
                        logger.info(f"Заголовок сгенерирован: {title[:50]}...")
                    else:
                        data['ai_generated_title'] = "Не удалось сгенерировать заголовок"
                        logger.warning(f"Строка {line_num}: не удалось сгенерировать заголовок")
                    
                    # Сбрасываем счетчик попыток при успехе
                    self.client.retry_count = 0
                    self.client.current_model_index = 0
                    
                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
                    processed_count += 1
                    logger.info(f"Строка {line_num}: обработана успешно")
                    
                    # Небольшая пауза между запросами
                    time.sleep(0.5)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Строка {line_num}: ошибка JSON - {e}")
                    error_count += 1
                except Exception as e:
                    logger.error(f"Строка {line_num}: неожиданная ошибка - {e}")
                    error_count += 1
        
        logger.info(f"Анализ завершен:")
        logger.info(f"  Обработано успешно: {processed_count}")
        logger.info(f"  Не удалось обработать: {error_count}")
        logger.info(f"  Результаты сохранены в: {self.output_dir}")
    
    def run(self, max_lines: Optional[int] = None) -> None:
        """Запускает анализ всех JSONL файлов"""
        input_path = Path(self.input_dir)
        
        if not input_path.exists():
            logger.error(f"Входная директория не найдена: {self.input_dir}")
            return
        
        jsonl_files = list(input_path.glob("*.jsonl"))
        
        if not jsonl_files:
            logger.error(f"JSONL файлы не найдены в {self.input_dir}")
            return
        
        logger.info(f"Найдено {len(jsonl_files)} JSONL файлов")
        
        for file_path in jsonl_files:
            self.process_jsonl_file(file_path, max_lines)


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Анализ JSONL файлов с помощью OpenRouter API')
    parser.add_argument('--limit', type=int, help='Максимальное количество строк для обработки')
    
    args = parser.parse_args()
    
    logger.info("Запуск анализа JSONL файлов")
    
    analyzer = JSONLAnalyzer()
    analyzer.run(max_lines=args.limit)


if __name__ == "__main__":
    main()