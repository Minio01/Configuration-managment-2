"""Тесты точки входа приложения."""

import contextlib
import io
import unittest

from tests import ROOT
import main


def run_main(*args):
    """Запустить main() и вернуть код завершения, stdout и stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main.main([str(arg) for arg in args])
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    """Проверка вывода параметров и кодов завершения."""

    def test_prints_all_parameters(self):
        code, out, _ = run_main(ROOT / "config.xml")
        self.assertEqual(code, main.EXIT_OK)
        self.assertIn("package=requests", out)
        self.assertIn("repository=https://pypi.org/pypi", out)
        self.assertIn("test_mode=false", out)
        self.assertIn("ascii_tree=true", out)
        self.assertIn("filter_substring=", out)
        self.assertIn("output_image=", out)

    def test_config_error(self):
        code, out, err = run_main(ROOT / "scripts/errors/bad_test_mode.xml")
        self.assertEqual(code, main.EXIT_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Ошибка конфигурации", err)


if __name__ == "__main__":
    unittest.main()
