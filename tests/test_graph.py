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


class LoadOrderTest(unittest.TestCase):
    """Порядок загрузки зависимостей."""

    def assert_before(self, order, first, second):
        """Проверить, что пакет first загружается раньше second."""
        self.assertLess(order.index(first), order.index(second))

    def test_chain(self):
        graph = build_graph("A", source("A: B\nB: C\nC:"))
        self.assertEqual(graph.load_order(), ["C", "B", "A"])

    def test_diamond(self):
        graph = build_graph("A", source("A: B C\nB: D\nC: D\nD:"))
        order = graph.load_order()
        self.assertEqual(order, ["D", "B", "C", "A"])

    def test_dependencies_first(self):
        text = "A: B C\nB: D E\nC: E F\nD: F\nE:\nF:"
        graph = build_graph("A", source(text))
        order = graph.load_order()
        self.assertEqual(sorted(order), ["A", "B", "C", "D", "E", "F"])
        for name in order:
            for dep in graph.dependencies(name):
                self.assert_before(order, dep, name)

    def test_cycle_each_package_once(self):
        graph = build_graph("A", source("A: B\nB: C\nC: A D\nD:"))
        self.assertEqual(graph.load_order(), ["D", "C", "B", "A"])

    def test_single_package(self):
        graph = build_graph("A", source("A:"))
        self.assertEqual(graph.load_order(), ["A"])

    def test_filtered_not_loaded(self):
        graph = build_graph("A", source("A: B C\nB:\nC:"), "C")
        self.assertEqual(graph.load_order(), ["B", "A"])


if __name__ == "__main__":
    unittest.main()
