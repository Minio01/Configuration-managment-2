"""Тесты построения графа зависимостей."""

import unittest

from graph import GraphError, build_graph, is_excluded
from testrepo import parse_repository


def source(text):
    """Вернуть функцию зависимостей для описания репозитория text."""
    repo = parse_repository(text)
    return lambda name: repo.get(name, [])


class BuildGraphTest(unittest.TestCase):
    """Обход DFS, циклы и фильтрация."""

    def test_dfs_order(self):
        graph = build_graph("A", source("A: B C\nB: D\nC: D\nD:"))
        self.assertEqual(graph.nodes(), ["A", "B", "D", "C"])
        self.assertEqual(graph.dependencies("C"), ["D"])
        self.assertEqual(graph.cycles, [])

    def test_transitive(self):
        graph = build_graph("A", source("A: B\nB: C\nC: D\nD:"))
        self.assertEqual(set(graph.nodes()), {"A", "B", "C", "D"})

    def test_cycle(self):
        graph = build_graph("A", source("A: B\nB: C\nC: A D\nD:"))
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(graph.dependencies("C"), ["A", "D"])

    def test_self_loop(self):
        graph = build_graph("A", source("A: A B\nB:"))
        self.assertEqual(graph.cycles, [["A", "A"]])

    def test_inner_cycle(self):
        graph = build_graph("A", source("A: B\nB: C\nC: B"))
        self.assertEqual(graph.cycles, [["B", "C", "B"]])

    def test_each_package_fetched_once(self):
        calls = []
        repo = parse_repository("A: B C\nB: D\nC: D\nD: B")

        def get_deps(name):
            """Запомнить запрос и вернуть зависимости."""
            calls.append(name)
            return repo.get(name, [])

        build_graph("A", get_deps)
        self.assertEqual(sorted(calls), ["A", "B", "C", "D"])

    def test_filter(self):
        text = "A: B C\nB: D\nC: E\nD:\nE:"
        graph = build_graph("A", source(text), "B")
        self.assertEqual(graph.nodes(), ["A", "C", "E"])
        self.assertEqual(graph.dependencies("A"), ["C"])

    def test_filter_case_insensitive(self):
        self.assertTrue(is_excluded("pytest-cov", "TEST"))
        self.assertFalse(is_excluded("requests", ""))

    def test_root_excluded(self):
        with self.assertRaises(GraphError):
            build_graph("A", source("A: B"), "A")


if __name__ == "__main__":
    unittest.main()
