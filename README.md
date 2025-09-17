# 4_CSV_MD

TG каналы. Обработка информации из CSV в MarkDown

## Описание

Проект для автоматической обработки постов из Telegram каналов, экспортированных в CSV формат, с последующим преобразованием в структурированный Markdown для Obsidian.

## Структура проекта

```
4_CSV_MD/
├── 1_CSV_1/                    # Шаг 1: CSV → JSONL
│   ├── csv_to_jsonl_converter.py
│   ├── input/                  # Выходной JSONL файл
│   └── output/                 # Входные CSV файлы
├── 2_JSONL_AI/                 # Шаг 2: Анализ JSONL с AI
│   ├── jsonl_analyzer.py
│   ├── requirements.txt
│   ├── .env                    # API ключ OpenRouter
│   └── output/                 # Обработанный JSONL с заголовками
├── 3_MD/                       # Шаг 3: JSONL → Markdown
│   ├── jsonl_to_obsidian.py
│   └── output/                 # Итоговый Markdown файл
└── run_pipeline.py             # Оркестратор всего пайплайна
```

## Возможности

- **CSV → JSONL**: Автоматическое преобразование CSV файлов в JSONL формат
- **AI-анализ**: Генерация заголовков для постов с помощью OpenRouter API
- **Markdown**: Создание структурированного Markdown для Obsidian
- **Автоматизация**: Полный пайплайн в одном скрипте
- **Кроссплатформенность**: Работает в Windows (через WSL) и Linux

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Andrey0125/4_CSV_MD.git
cd 4_CSV_MD
```

2. Настройте API ключ OpenRouter:
```bash
cd 2_JSONL_AI
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
```

3. Поместите CSV файлы в папку `1_CSV_1/output/`

## Использование

### Запуск полного пайплайна:
```bash
python3 run_pipeline.py
```

### Пошаговый запуск:

1. **CSV → JSONL**:
```bash
python3 1_CSV_1/csv_to_jsonl_converter.py
```

2. **Анализ JSONL с AI**:
```bash
cd 2_JSONL_AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 jsonl_analyzer.py
```

3. **JSONL → Markdown**:
```bash
python3 3_MD/jsonl_to_obsidian.py
```

## Требования

- Python 3.8+
- OpenRouter API ключ
- CSV файлы с постами из Telegram каналов

## Формат входных данных

CSV файлы должны содержать колонки:
- `text` или `content` - текст поста
- `date` - дата поста
- `link` - ссылка на пост (опционально)

## Результат

После обработки в папке `3_MD/output/` будет создан файл `all_posts.md` с:
- Статистикой по источникам
- Содержанием с ссылками на посты
- Структурированными постами с AI-заголовками
- Форматированием для Obsidian

## Особенности

- Автоматическое определение разделителей CSV
- Обработка кодировки windows-1251
- Переключение между AI-моделями при ошибках
- Логирование всех операций
- Поддержка WSL для Windows

## Лицензия

MIT License