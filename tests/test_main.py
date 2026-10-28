"""Тесты точки входа приложения."""

import contextlib
import io
import unittest
from unittest import mock

from tests import ROOT
import main
from pypi import RepositoryError

GRAPHS = ROOT / "scripts" / "graphs"


def run_main(*args):
    """Запустить main() и вернуть код завершения, stdout и stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main.main([str(arg) for arg in args])
    return code, out.getvalue(), err.getvalue()


class TestModeTest(unittest.TestCase):
    """Работа с тестовым репозиторием."""

    def test_simple_graph(self):
        code, out, _ = run_main(GRAPHS / "simple.xml")
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("A -> B, C", out)
        self.assertIn("D -> (нет)", out)

    def test_cycle_reported(self):
        _, out, _ = run_main(GRAPHS / "cycle.xml")
        self.assertIn("Циклические зависимости", out)
        self.assertIn("A -> B -> C -> A", out)

    def test_filter(self):
        _, out, _ = run_main(GRAPHS / "filter_b.xml")
        self.assertNotIn("B", out.replace("пакета", ""))

    def test_root_filtered(self):
        code, _, err = run_main(GRAPHS / "filter_root.xml")
        self.assertEqual(code, main.EXIT_GRAPH_ERROR)
        self.assertIn("исключён", err)

    def test_missing_package(self):
        code, _, err = run_main(GRAPHS / "missing_package.xml")
        self.assertEqual(code, main.EXIT_REPOSITORY_ERROR)
        self.assertIn("не описан", err)

    def test_bad_repository_file(self):
        code, _, err = run_main(GRAPHS / "bad_name.xml")
        self.assertEqual(code, main.EXIT_REPOSITORY_ERROR)
        self.assertIn("строка 2", err)


class PypiModeTest(unittest.TestCase):
    """Работа с PyPI (сеть заменена заглушкой)."""

    @mock.patch("main.get_dependencies")
    def test_graph_from_pypi(self, get_dependencies):
        repo = {"requests": ["idna", "certifi"], "idna": [], "certifi": []}
        get_dependencies.side_effect = lambda url, name: repo[name]
        code, out, _ = run_main(ROOT / "config.xml")
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("requests -> idna, certifi", out)
        self.assertEqual(get_dependencies.call_count, len(repo))

    @mock.patch("main.get_dependencies")
    def test_repository_error(self, get_dependencies):
        get_dependencies.side_effect = RepositoryError("пакет не найден")
        code, _, err = run_main(ROOT / "config.xml")
        self.assertEqual(code, main.EXIT_REPOSITORY_ERROR)
        self.assertIn("Ошибка репозитория", err)

    def test_config_error(self):
        code, out, err = run_main(ROOT / "scripts/errors/bad_test_mode.xml")
        self.assertEqual(code, main.EXIT_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка конфигурации", err)


if __name__ == "__main__":
    unittest.main()
