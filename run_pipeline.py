#!/usr/bin/env python3
"""
Простой и надежный оркестратор для последовательного запуска пайплайна:
1) CSV -> JSONL
2) Анализ JSONL (OpenRouter) c автосозданием venv и установкой зависимостей
3) JSONL -> Markdown (Obsidian)

Рассчитан на запуск из Spyder/Anaconda (stdout/stderr в консоль Spyder).
"""

import os
import sys
import subprocess
import logging
import shlex
from pathlib import Path


# Логирование в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Абсолютные пути
BASE = Path('/home/andrey/projects/Cursor/4_CSV_MD')
STEP1_DIR = BASE / '1_CSV_1'
STEP2_DIR = BASE / '2_JSONL_AI'
STEP3_DIR = BASE / '3_MD'

STEP1_SCRIPT = STEP1_DIR / 'csv_to_jsonl_converter.py'
STEP2_SCRIPT = STEP2_DIR / 'jsonl_analyzer.py'
STEP3_SCRIPT = STEP3_DIR / 'jsonl_to_obsidian.py'

# Артефакты
COMBINED_JSONL = Path('/home/andrey/projects/Cursor/4_CSV_MD/1_CSV_1/input/combined_posts.jsonl')
ANALYZED_JSONL = Path('/home/andrey/projects/Cursor/4_CSV_MD/2_JSONL_AI/output/analyzed_combined_posts.jsonl')
OBSIDIAN_MD = Path('/home/andrey/projects/Cursor/4_CSV_MD/3_MD/output/all_posts.md')

# Venv для шага 2
STEP2_VENV = STEP2_DIR / 'venv'
STEP2_PIP_REQ = STEP2_DIR / 'requirements.txt'

# Запуск из Spyder/Windows требует проксировать команды в WSL
NEED_WSL = os.name == 'nt'


def _stream_process(proc: subprocess.Popen) -> int:
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
    proc.wait()
    return proc.returncode


def run_cmd(cmd, cwd=None, env=None) -> int:
    """Запустить команду, потоково выводя stdout/stderr в консоль.
    Если запущено из Windows/Spyder, проксируем через WSL.
    """
    if NEED_WSL:
        # Собираем bash-команду (важно: использовать POSIX-пути и корректное shell-экранирование)
        def to_wsl_str(value: str) -> str:
            return value.replace('\\', '/')

        wsl_cwd = to_wsl_str(str(cwd)) if cwd else None
        bash_cmd = ' '.join(shlex.quote(to_wsl_str(str(x))) for x in cmd)
        if wsl_cwd:
            bash_cmd = f"cd {shlex.quote(wsl_cwd)} && {bash_cmd}"
        wrapped = ['wsl', 'bash', '-lc', bash_cmd]
        logger.info('lzk: (WSL) запускаю команду: %s', ' '.join(cmd))
        try:
            proc = subprocess.Popen(
                wrapped,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )
            return _stream_process(proc)
        except FileNotFoundError as e:
            logger.error('WSL не доступен или команда не найдена: %s', e)
            return 127
        except Exception as e:
            logger.error('Неожиданная ошибка запуска (WSL): %s', e)
            return 1
    else:
        logger.info('lzk: запускаю команду: %s', ' '.join(cmd))
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )
            return _stream_process(proc)
        except FileNotFoundError as e:
            logger.error('Команда не найдена: %s', e)
            return 127
        except Exception as e:
            logger.error('Неожиданная ошибка запуска: %s', e)
            return 1


def ensure_step2_venv_with_requirements() -> Path:
    """Создать venv для шага 2 при отсутствии и установить зависимости."""
    python_exe = STEP2_VENV / 'bin' / 'python'
    pip_exe = STEP2_VENV / 'bin' / 'pip'

    if not STEP2_VENV.exists():
        logger.info('lzk: создаю venv для шага 2: %s', STEP2_VENV)
        # Создаем venv внутри WSL при необходимости
        py_cmd = ['python3', '-m', 'venv', str(STEP2_VENV)] if NEED_WSL else [sys.executable, '-m', 'venv', str(STEP2_VENV)]
        rc = run_cmd(py_cmd)
        if rc != 0:
            raise RuntimeError('Не удалось создать venv для шага 2')

    # Проверка pip внутри venv (в Linux-дереве)
    if not pip_exe.exists():
        raise RuntimeError('pip не найден в venv шага 2')

    if STEP2_PIP_REQ.exists():
        logger.info('lzk: устанавливаю зависимости для шага 2 из %s', STEP2_PIP_REQ)
        rc = run_cmd([str(pip_exe), 'install', '-r', str(STEP2_PIP_REQ)])
        if rc != 0:
            raise RuntimeError('Не удалось установить зависимости для шага 2')
    else:
        logger.warning('requirements.txt не найден: %s (пропускаю установку)', STEP2_PIP_REQ)

    return python_exe


def check_file_nonempty(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f'Файл не найден: {path}')
    if path.is_file() and path.stat().st_size == 0:
        raise ValueError(f'Файл пустой: {path}')


def step1_csv_to_jsonl() -> None:
    logger.info('=== Шаг 1: CSV -> JSONL ===')
    if not STEP1_SCRIPT.exists():
        raise FileNotFoundError(f'Скрипт не найден: {STEP1_SCRIPT}')
    # На Windows/Spyder используем WSL python3
    cmd = ['python3', str(STEP1_SCRIPT)] if NEED_WSL else [sys.executable, str(STEP1_SCRIPT)]
    rc = run_cmd(cmd)
    if rc != 0:
        raise RuntimeError('Шаг 1 завершился с ошибкой')
    check_file_nonempty(COMBINED_JSONL)
    logger.info('lzk: Шаг 1 OK, создан файл: %s', COMBINED_JSONL)


def step2_analyze_jsonl(limit: int | None = None) -> None:
    logger.info('=== Шаг 2: Анализ JSONL (OpenRouter) ===')
    if not STEP2_SCRIPT.exists():
        raise FileNotFoundError(f'Скрипт не найден: {STEP2_SCRIPT}')

    venv_python = ensure_step2_venv_with_requirements()
    # Запуск анализатора, опционально с лимитом
    cmd = [str(venv_python), str(STEP2_SCRIPT)]
    if limit is not None:
        cmd += ['--limit', str(limit)]
    rc = run_cmd(cmd, cwd=STEP2_DIR)
    if rc != 0:
        raise RuntimeError('Шаг 2 завершился с ошибкой')
    check_file_nonempty(ANALYZED_JSONL)
    logger.info('lzk: Шаг 2 OK, создан файл: %s', ANALYZED_JSONL)


def step3_jsonl_to_md() -> None:
    logger.info('=== Шаг 3: JSONL -> Markdown (Obsidian) ===')
    if not STEP3_SCRIPT.exists():
        raise FileNotFoundError(f'Скрипт не найден: {STEP3_SCRIPT}')
    cmd = ['python3', str(STEP3_SCRIPT)] if NEED_WSL else [sys.executable, str(STEP3_SCRIPT)]
    rc = run_cmd(cmd)
    if rc != 0:
        raise RuntimeError('Шаг 3 завершился с ошибкой')
    check_file_nonempty(OBSIDIAN_MD)
    logger.info('lzk: Шаг 3 OK, создан файл: %s', OBSIDIAN_MD)


def main() -> None:
    logger.info('Старт пайплайна 4_CSV_MD')
    # Быстрые проверки директорий/скриптов
    for p in [STEP1_DIR, STEP2_DIR, STEP3_DIR, STEP1_SCRIPT, STEP2_SCRIPT, STEP3_SCRIPT]:
        if not p.exists():
            raise FileNotFoundError(f'Не найден путь: {p}')

    step1_csv_to_jsonl()
    step2_analyze_jsonl(limit=None)
    step3_jsonl_to_md()

    logger.info('Пайплайн успешно завершен')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error('Пайплайн завершился с ошибкой: %s', e)
        sys.exit(1)