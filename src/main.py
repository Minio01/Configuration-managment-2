"""Точка входа CLI-приложения для анализа зависимостей pip-пакетов."""

import argparse
import sys

from config import ConfigError, load_config
from pypi import RepositoryError, get_dependencies

DEFAULT_CONFIG = "config.xml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 2
EXIT_REPOSITORY_ERROR = 3


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


def print_direct_dependencies(config):
    """Вывести прямые зависимости пакета, заданного в конфигурации."""
    dependencies = get_dependencies(config.repository, config.package)
    print(f"Прямые зависимости пакета {config.package}:")
    if not dependencies:
        print("  (нет зависимостей)")
    for name in dependencies:
        print(f"  {name}")


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Ошибка конфигурации: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    if config.test_mode:
        print("Тестовый режим пока не поддерживается", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    try:
        print_direct_dependencies(config)
    except RepositoryError as exc:
        print(f"Ошибка репозитория: {exc}", file=sys.stderr)
        return EXIT_REPOSITORY_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
