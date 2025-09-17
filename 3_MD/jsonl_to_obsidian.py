#!/usr/bin/env python3
"""
Скрипт для преобразования JSONL файла в markdown для Obsidian
"""

import json
import os
from datetime import datetime
from pathlib import Path


def format_date_for_obsidian(date_str):
    """Форматирует дату для Obsidian"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str


def format_text_for_obsidian(text):
    """Форматирует текст для Obsidian с учетом синтаксиса"""
    if not text:
        return ""
    
    # Заменяем переносы строк на двойные для markdown
    text = text.replace('\n', '\n\n')
    
    # Обрабатываем списки
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
            
        # Обрабатываем нумерованные списки
        if line.startswith(('1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)')):
            formatted_lines.append(f"- {line[2:].strip()}")
        # Обрабатываем маркированные списки
        elif line.startswith(('•', '-', '*')):
            formatted_lines.append(f"- {line[1:].strip()}")
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def create_obsidian_markdown(posts):
    """Создает markdown контент для Obsidian"""
    markdown_content = []
    
    # Заголовок
    markdown_content.append("# Все посты из Telegram каналов")
    markdown_content.append("")
    markdown_content.append(f"*Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    markdown_content.append("")
    
    # Статистика
    total_posts = len(posts)
    sources = {}
    for post in posts:
        source = post.get('_source_file', 'Неизвестно')
        sources[source] = sources.get(source, 0) + 1
    
    markdown_content.append("## Статистика")
    markdown_content.append(f"- **Всего постов:** {total_posts}")
    markdown_content.append(f"- **Источников:** {len(sources)}")
    markdown_content.append("")
    
    # Список источников
    markdown_content.append("### Источники:")
    for source, count in sorted(sources.items()):
        markdown_content.append(f"- {source}: {count} постов")
    markdown_content.append("")
    
    # Содержание
    markdown_content.append("## Содержание")
    markdown_content.append("")
    
    # Группируем по источникам
    posts_by_source = {}
    for post in posts:
        source = post.get('_source_file', 'Неизвестно')
        if source not in posts_by_source:
            posts_by_source[source] = []
        posts_by_source[source].append(post)
    
    # Создаем содержание
    for source, source_posts in sorted(posts_by_source.items()):
        markdown_content.append(f"### {source}")
        markdown_content.append("")
        
        for i, post in enumerate(source_posts, 1):
            title = post.get('ai_generated_title', 'Без заголовка')
            date = post.get('date', 'Неизвестная дата')
            formatted_date = format_date_for_obsidian(date)
            
            markdown_content.append(f"{i}. [[{title}]] - {formatted_date}")
        
        markdown_content.append("")
    
    # Разделитель
    markdown_content.append("---")
    markdown_content.append("")
    
    # Посты
    for source, source_posts in sorted(posts_by_source.items()):
        markdown_content.append(f"## {source}")
        markdown_content.append("")
        
        for post in source_posts:
            # Заголовок поста
            title = post.get('ai_generated_title', 'Без заголовка')
            markdown_content.append(f"### {title}")
            markdown_content.append("")
            
            # Метаданные
            date = post.get('date', 'Неизвестная дата')
            formatted_date = format_date_for_obsidian(date)
            markdown_content.append(f"**Дата:** {formatted_date}")
            markdown_content.append("")
            
            # Текст поста
            text = post.get('text', post.get('content', post.get('message', '')))
            if text:
                formatted_text = format_text_for_obsidian(text)
                markdown_content.append(formatted_text)
                markdown_content.append("")
            
            # Ссылки если есть
            if 'link' in post and post['link']:
                markdown_content.append(f"**Ссылка:** {post['link']}")
                markdown_content.append("")
            
            # Разделитель между постами
            markdown_content.append("---")
            markdown_content.append("")
    
    return '\n'.join(markdown_content)


def create_table_of_contents(posts):
    """Создает содержание для Obsidian"""
    toc_content = []
    
    # Группируем по источникам
    posts_by_source = {}
    for post in posts:
        source = post.get('_source_file', 'Неизвестно')
        if source not in posts_by_source:
            posts_by_source[source] = []
        posts_by_source[source].append(post)
    
    toc_content.append("# Содержание")
    toc_content.append("")
    
    for source, source_posts in sorted(posts_by_source.items()):
        toc_content.append(f"## {source}")
        toc_content.append("")
        
        for i, post in enumerate(source_posts, 1):
            title = post.get('ai_generated_title', 'Без заголовка')
            date = post.get('date', 'Неизвестная дата')
            formatted_date = format_date_for_obsidian(date)
            
            toc_content.append(f"{i}. [[{title}]] - {formatted_date}")
        
        toc_content.append("")
    
    return '\n'.join(toc_content)


def process_jsonl_to_obsidian(input_file, output_dir):
    """Основная функция обработки"""
    print("🚀 Запуск преобразования JSONL в Obsidian Markdown")
    print("=" * 50)
    
    # Создаем выходную директорию
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Читаем JSONL файл
    posts = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    post = json.loads(line)
                    posts.append(post)
                    title = post.get('ai_generated_title', 'Без заголовка')
                    print(f"✓ Загружен пост {len(posts)}: {title[:50]}...")
                except json.JSONDecodeError as e:
                    print(f"✗ Ошибка JSON в строке {line_num}: {e}")
                    continue
    except FileNotFoundError:
        print(f"❌ Файл не найден: {input_file}")
        return
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return
    
    if not posts:
        print("❌ Нет данных для обработки")
        return
    
    print(f"\n📋 Создаю содержание...")
    
    # Создаем содержание
    toc_content = create_table_of_contents(posts)
    toc_file = Path(output_dir) / "table_of_contents.md"
    with open(toc_file, 'w', encoding='utf-8') as f:
        f.write(toc_content)
    
    print(f"📝 Формирую общий файл...")
    
    # Создаем основной markdown файл
    markdown_content = create_obsidian_markdown(posts)
    output_file = Path(output_dir) / "all_posts.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"✓ Создан общий файл: {output_file}")
    
    # Статистика
    print(f"\n📊 Результат обработки:")
    print(f"✓ Успешно обработано: {len(posts)} постов")
    print(f"✗ Ошибок: 0")
    print(f"📁 Файл сохранен: {output_file}")
    print(f"\n🎉 Преобразование завершено успешно!")


def main():
    """Основная функция"""
    input_file = "/home/andrey/projects/Cursor/4_CSV_MD/2_JSONL_AI/output/analyzed_combined_posts.jsonl"
    output_dir = "/home/andrey/projects/Cursor/4_CSV_MD/3_MD/output"
    
    process_jsonl_to_obsidian(input_file, output_dir)


if __name__ == "__main__":
    main()