"""Тесты точки входа приложения."""

import contextlib
import io
import unittest
from unittest import mock

from tests import ROOT
import main
from pypi import RepositoryError


def run_main(*args):
    """Запустить main() и вернуть код завершения, stdout и stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main.main([str(arg) for arg in args])
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка вывода прямых зависимостей и кодов завершения."""

    @mock.patch("main.get_dependencies")
    def test_prints_direct_dependencies(self, get_dependencies):
        get_dependencies.return_value = ["idna", "certifi"]
        code, out, _ = run_main(ROOT / "config.xml")
        self.assertEqual(code, main.EXIT_OK)
        get_dependencies.assert_called_once_with(
            "https://pypi.org/pypi", "requests"
        )
        self.assertIn("Прямые зависимости пакета requests", out)
        self.assertIn("  idna\n  certifi\n", out)

    @mock.patch("main.get_dependencies")
    def test_no_dependencies(self, get_dependencies):
        get_dependencies.return_value = []
        _, out, _ = run_main(ROOT / "config.xml")
        self.assertIn("нет зависимостей", out)

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
