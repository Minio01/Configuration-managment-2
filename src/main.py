"""Точка входа CLI-приложения для анализа зависимостей pip-пакетов."""

import argparse
import sys

from config import ConfigError, load_config
from graph import GraphError, build_graph
from pypi import RepositoryError, get_dependencies
from testrepo import TestRepositoryError, load_repository
from visualize import ascii_tree, save_svg, to_mermaid

DEFAULT_CONFIG = "config.xml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 2
EXIT_REPOSITORY_ERROR = 3
EXIT_GRAPH_ERROR = 4
EXIT_OUTPUT_ERROR = 5


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


def make_source(config):
    """Вернуть функцию, выдающую прямые зависимости пакета."""
    if config.test_mode:
        repository = load_repository(config.repository)
        if config.package not in repository:
            raise TestRepositoryError(
                f"пакет {config.package} не описан в тестовом репозитории"
            )
        return lambda name: repository.get(name, [])
    return lambda name: get_dependencies(config.repository, name)


def print_cycles(graph):
    """Вывести найденные циклические зависимости."""
    if graph.cycles:
        print("Циклические зависимости:")
        for cycle in graph.cycles:
            print("  " + " -> ".join(cycle))
        print()


def visualize(graph, config):
    """Вывести Mermaid, сохранить SVG и при необходимости ASCII-дерево."""
    print(f"Граф зависимостей пакета {graph.root} на языке Mermaid:")
    print(to_mermaid(graph))
    print()
    print_cycles(graph)
    save_svg(graph, config.output_image)
    print(f"Изображение сохранено в {config.output_image}")
    if config.ascii_tree:
        print()
        print(ascii_tree(graph))


def run(config):
    """Построить граф по конфигурации и вывести его визуализацию."""
    source = make_source(config)
    graph = build_graph(config.package, source, config.filter_substring)
    visualize(graph, config)


def main(argv=None):
    """Запустить приложение и вернуть код завершения."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Ошибка конфигурации: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    try:
        run(config)
    except (RepositoryError, TestRepositoryError) as exc:
        print(f"Ошибка репозитория: {exc}", file=sys.stderr)
        return EXIT_REPOSITORY_ERROR
    except GraphError as exc:
        print(f"Ошибка анализа: {exc}", file=sys.stderr)
        return EXIT_GRAPH_ERROR
    except OSError as exc:
        print(f"Ошибка сохранения изображения: {exc}", file=sys.stderr)
        return EXIT_OUTPUT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
