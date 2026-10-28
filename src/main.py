"""Точка входа CLI-приложения для анализа зависимостей pip-пакетов."""

import argparse
import sys

from config import ConfigError, load_config

DEFAULT_CONFIG = "config.xml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 2


def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей pip-пакетов"
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=DEFAULT_CONFIG,
        help=f"путь к XML-файлу конфигурации (по умолчанию {DEFAULT_CONFIG})",
    )
    return parser.parse_args(argv)


def format_value(value):
    """Представить значение параметра в виде строки для вывода."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Ошибка конфигурации: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    for key, value in config.items():
        print(f"{key}={format_value(value)}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
