"""Тесты точки входа приложения."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
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


@mock.patch("main.save_svg")
class TestModeTest(unittest.TestCase):
    """Работа с тестовым репозиторием."""

    def test_mermaid_and_svg(self, save_svg):
        code, out, _ = run_main(GRAPHS / "simple.xml")
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("graph TD", out)
        self.assertIn("n0 --> n1", out)
        self.assertIn("Изображение сохранено", out)
        save_svg.assert_called_once()
        self.assertTrue(save_svg.call_args.args[1].endswith("simple.svg"))

    def test_ascii_tree(self, _):
        _, out, _ = run_main(GRAPHS / "simple.xml")
        self.assertIn("A\n|-- B\n|   `-- D\n`-- C\n    `-- D\n", out)

    def test_ascii_tree_disabled(self, _):
        text = (ROOT / "config_test.xml").read_text(encoding="utf-8")
        text = text.replace("<ascii_tree>true", "<ascii_tree>false")
        text = text.replace("repos/", str(ROOT / "repos") + "/")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.xml"
            path.write_text(text, encoding="utf-8")
            _, out, _ = run_main(path)
        self.assertIn("graph TD", out)
        self.assertNotIn("|--", out)

    def test_cycle_reported(self, _):
        _, out, _ = run_main(GRAPHS / "cycle.xml")
        self.assertIn("Циклические зависимости", out)
        self.assertIn("A -> B -> C -> A", out)
        self.assertIn("-.->", out)

    def test_filter(self, _):
        _, out, _ = run_main(GRAPHS / "filter_b.xml")
        self.assertNotIn('["B"]', out)

    def test_root_filtered(self, _):
        code, _, err = run_main(GRAPHS / "filter_root.xml")
        self.assertEqual(code, main.EXIT_GRAPH_ERROR)
        self.assertIn("исключён", err)

    def test_missing_package(self, _):
        code, _, err = run_main(GRAPHS / "missing_package.xml")
        self.assertEqual(code, main.EXIT_REPOSITORY_ERROR)
        self.assertIn("не описан", err)

    def test_bad_repository_file(self, _):
        code, _, err = run_main(GRAPHS / "bad_name.xml")
        self.assertEqual(code, main.EXIT_REPOSITORY_ERROR)
        self.assertIn("строка 2", err)

    def test_save_error(self, save_svg):
        save_svg.side_effect = PermissionError("нет доступа")
        code, _, err = run_main(GRAPHS / "simple.xml")
        self.assertEqual(code, main.EXIT_OUTPUT_ERROR)
        self.assertIn("Ошибка сохранения", err)


@mock.patch("main.save_svg")
class PypiModeTest(unittest.TestCase):
    """Работа с PyPI (сеть заменена заглушкой)."""

    @mock.patch("main.get_dependencies")
    def test_graph_from_pypi(self, get_dependencies, _):
        repo = {"requests": ["idna", "certifi"], "idna": [], "certifi": []}
        get_dependencies.side_effect = lambda url, name: repo[name]
        code, out, _ = run_main(ROOT / "config.xml")
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn('n0["requests"]', out)
        self.assertIn("requests\n|-- idna\n`-- certifi", out)
        self.assertEqual(get_dependencies.call_count, len(repo))

    @mock.patch("main.get_dependencies")
    def test_repository_error(self, get_dependencies, _):
        get_dependencies.side_effect = RepositoryError("пакет не найден")
        code, _, err = run_main(ROOT / "config.xml")
        self.assertEqual(code, main.EXIT_REPOSITORY_ERROR)
        self.assertIn("Ошибка репозитория", err)

    def test_config_error(self, _):
        code, out, err = run_main(ROOT / "scripts/errors/bad_test_mode.xml")
        self.assertEqual(code, main.EXIT_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка конфигурации", err)


if __name__ == "__main__":
    unittest.main()
