#!/usr/bin/env python3
"""
CSV to JSONL Converter
Простой и надежный скрипт для преобразования CSV файлов в JSONL формат
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def read_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Читает CSV файл с кодировкой windows-1251 и разделителем ';'
    
    Args:
        file_path: Путь к CSV файлу
        
    Returns:
        Список словарей с данными из CSV
    """
    data = []
    
    try:
        with open(file_path, 'r', encoding='windows-1251', newline='') as csvfile:
            # Определяем разделитель автоматически
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            # Пробуем разные разделители
            for delimiter in [';', ',', '\t']:
                if delimiter in sample:
                    csvfile.seek(0)
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                    data = list(reader)
                    logger.info(f"Использован разделитель '{delimiter}' для файла {file_path.name}")
                    break
            
            if not data:
                logger.warning(f"Не удалось определить разделитель для файла {file_path.name}")
                return []
                
    except UnicodeDecodeError:
        logger.error(f"Ошибка кодировки при чтении файла {file_path.name}")
        return []
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path.name}: {e}")
        return []
    
    logger.info(f"Прочитано {len(data)} записей из файла {file_path.name}")
    return data


def convert_to_jsonl(data: List[Dict[str, Any]], source_file: str) -> List[str]:
    """
    Преобразует данные CSV в JSONL формат
    
    Args:
        data: Данные из CSV файла
        source_file: Имя исходного файла
        
    Returns:
        Список JSONL строк
    """
    jsonl_lines = []
    
    for i, row in enumerate(data):
        try:
            # Добавляем информацию об источнике
            row['_source_file'] = source_file
            row['_row_number'] = i + 1
            
            # Очищаем значения от лишних пробелов и заменяем двойные переносы на одинарные
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, str):
                    cleaned_value = v.strip().replace('\n\n', '\n')
                    cleaned_row[k] = cleaned_value
                else:
                    cleaned_row[k] = v
            
            jsonl_line = json.dumps(cleaned_row, ensure_ascii=False, separators=(',', ':'))
            jsonl_lines.append(jsonl_line)
            
        except Exception as e:
            logger.error(f"Ошибка при преобразовании строки {i+1} из файла {source_file}: {e}")
            continue
    
    logger.info(f"Преобразовано {len(jsonl_lines)} записей в JSONL из файла {source_file}")
    return jsonl_lines


def process_csv_files(input_dir: Path, output_dir: Path) -> None:
    """
    Обрабатывает все CSV файлы в директории и объединяет в один JSONL файл
    
    Args:
        input_dir: Директория с CSV файлами
        output_dir: Директория для сохранения JSONL файла
    """
    if not input_dir.exists():
        logger.error(f"Директория {input_dir} не существует")
        return
    
    # Создаем выходную директорию если не существует
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Находим все CSV файлы
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"CSV файлы не найдены в директории {input_dir}")
        return
    
    logger.info(f"Найдено {len(csv_files)} CSV файлов для обработки")
    
    all_jsonl_lines = []
    processed_files = 0
    
    for csv_file in csv_files:
        logger.info(f"Обрабатываю файл: {csv_file.name}")
        
        # Читаем CSV файл
        csv_data = read_csv_file(csv_file)
        
        if not csv_data:
            logger.warning(f"Файл {csv_file.name} пуст или содержит ошибки")
            continue
        
        # Преобразуем в JSONL
        jsonl_lines = convert_to_jsonl(csv_data, csv_file.name)
        
        if jsonl_lines:
            all_jsonl_lines.extend(jsonl_lines)
            processed_files += 1
            logger.info(f"Файл {csv_file.name} успешно обработан")
        else:
            logger.warning(f"Не удалось преобразовать файл {csv_file.name}")
    
    # Сохраняем объединенный JSONL файл
    if all_jsonl_lines:
        output_file = output_dir / "combined_posts.jsonl"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for line in all_jsonl_lines:
                    f.write(line + '\n')
            
            logger.info(f"Сохранено {len(all_jsonl_lines)} записей в файл {output_file}")
            logger.info(f"Обработано {processed_files} из {len(csv_files)} файлов")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла {output_file}: {e}")
    else:
        logger.error("Нет данных для сохранения")


def main():
    """Основная функция"""
    # Пути к директориям (внутри 4_CSV_MD)
    input_dir = Path("/home/andrey/projects/Cursor/4_CSV_MD/1_CSV_1/output")
    output_dir = Path("/home/andrey/projects/Cursor/4_CSV_MD/1_CSV_1/input")
    
    logger.info("Начинаю обработку CSV файлов...")
    logger.info(f"Входная директория: {input_dir}")
    logger.info(f"Выходная директория: {output_dir}")
    
    process_csv_files(input_dir, output_dir)
    
    logger.info("Обработка завершена")


if __name__ == "__main__":
    main()