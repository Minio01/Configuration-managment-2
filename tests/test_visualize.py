"""Тесты визуализации графа."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from graph import build_graph
from testrepo import parse_repository
from visualize import (
    ascii_tree, assign_levels, back_edges, save_svg, to_mermaid, to_svg,
)

SVG_NS = "{http://www.w3.org/2000/svg}"


def make_graph(text, root="A", filter_substring=""):
    """Построить граф по описанию тестового репозитория."""
    repo = parse_repository(text)
    return build_graph(root, lambda name: repo.get(name, []),
                       filter_substring)


class MermaidTest(unittest.TestCase):
    """Текстовое представление на языке Mermaid."""

    def test_simple(self):
        text = to_mermaid(make_graph("A: B C\nB: C\nC:"))
        self.assertEqual(text.splitlines(), [
            "graph TD",
            '    n0["A"]',
            '    n1["B"]',
            '    n2["C"]',
            "    n0 --> n1",
            "    n0 --> n2",
            "    n1 --> n2",
        ])

    def test_cycle_edge_dotted(self):
        text = to_mermaid(make_graph("A: B\nB: A"))
        self.assertIn("n0 --> n1", text)
        self.assertIn("n1 -.-> n0", text)

    def test_single_node(self):
        self.assertEqual(to_mermaid(make_graph("A:")),
                         'graph TD\n    n0["A"]')


class AsciiTreeTest(unittest.TestCase):
    """Вывод зависимостей в виде ASCII-дерева."""

    def test_tree(self):
        tree = ascii_tree(make_graph("A: B C\nB: D\nC:\nD:"))
        self.assertEqual(tree.splitlines(), [
            "A",
            "|-- B",
            "|   `-- D",
            "`-- C",
        ])

    def test_shared_dependency_repeated(self):
        tree = ascii_tree(make_graph("A: B C\nB: D\nC: D\nD:"))
        self.assertEqual(tree.count("D"), len(["B", "C"]))

    def test_cycle_marked(self):
        tree = ascii_tree(make_graph("A: B\nB: A"))
        self.assertTrue(tree.isascii())
        self.assertEqual(tree.splitlines(), [
            "A", "`-- B", "    `-- A (cycle)",
        ])

    def test_filtered(self):
        tree = ascii_tree(make_graph("A: B C\nB:\nC:", filter_substring="B"))
        self.assertEqual(tree.splitlines(), ["A", "`-- C"])


class SvgTest(unittest.TestCase):
    """Изображение графа в формате SVG."""

    def test_levels(self):
        graph = make_graph("A: B C\nB: C\nC:")
        self.assertEqual(assign_levels(graph), [["A"], ["B"], ["C"]])

    def test_levels_with_cycle(self):
        graph = make_graph("A: B\nB: C\nC: A")
        self.assertEqual(assign_levels(graph), [["A"], ["B"], ["C"]])
        self.assertEqual(back_edges(graph), {("C", "A")})

    def test_svg_is_valid_xml(self):
        graph = make_graph("A: B C\nB: D\nC: D\nD: B")
        root = ET.fromstring(to_svg(graph))
        self.assertEqual(root.tag, SVG_NS + "svg")
        labels = [node.text for node in root.iter(SVG_NS + "text")]
        self.assertEqual(sorted(labels), ["A", "B", "C", "D"])
        self.assertEqual(len(list(root.iter(SVG_NS + "path"))),
                         len(["arrow", "arrow-cycle", "D->B"]))

    def test_save_svg(self):
        graph = make_graph("A: B\nB:")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "graph.svg"
            save_svg(graph, path)
            self.assertTrue(path.read_text(encoding="utf-8")
                            .startswith("<svg"))

    def test_names_escaped(self):
        repo = {"a<b": []}
        graph = build_graph("a<b", lambda name: repo[name])
        self.assertIn("a&lt;b", to_svg(graph))


if __name__ == "__main__":
    unittest.main()
