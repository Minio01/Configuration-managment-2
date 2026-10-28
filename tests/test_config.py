"""Тесты чтения и проверки XML-конфигурации."""

import tempfile
import unittest
from pathlib import Path

from tests import ROOT
from config import ConfigError, load_config

ERRORS = ROOT / "scripts" / "errors"


def write_config(directory, body):
    """Записать во временный каталог config.xml с заданным содержимым."""
    path = Path(directory) / "config.xml"
    path.write_text(f"<config>{body}</config>", encoding="utf-8")
    return path


class LoadConfigTest(unittest.TestCase):
    """Проверка корректных конфигураций."""

    def test_pypi_config(self):
        config = load_config(ROOT / "config.xml")
        self.assertEqual(config.package, "requests")
        self.assertEqual(config.repository, "https://pypi.org/pypi")
        self.assertFalse(config.test_mode)
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.filter_substring, "")
        self.assertTrue(config.output_image.endswith("graph.svg"))

    def test_test_mode_config(self):
        config = load_config(ROOT / "config_test.xml")
        self.assertTrue(config.test_mode)
        self.assertEqual(config.package, "A")
        self.assertTrue(Path(config.repository).is_file())

    def test_optional_defaults(self):
        body = (
            "<package>flask</package>"
            "<repository>https://pypi.org/pypi/</repository>"
            "<test_mode>no</test_mode>"
            "<output_image>out.svg</output_image>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(write_config(tmp, body))
        self.assertFalse(config.ascii_tree)
        self.assertEqual(config.filter_substring, "")
        self.assertEqual(config.repository, "https://pypi.org/pypi")

    def test_items_order(self):
        config = load_config(ROOT / "config.xml")
        keys = [key for key, _ in config.items()]
        self.assertEqual(keys[0], "package")
        self.assertEqual(keys[-1], "filter_substring")


class ConfigErrorTest(unittest.TestCase):
    """Проверка обработки ошибок для всех параметров."""

    def check_error(self, name, fragment):
        """Убедиться, что файл из scripts/errors вызывает ошибку."""
        with self.assertRaises(ConfigError) as ctx:
            load_config(ERRORS / f"{name}.xml")
        self.assertIn(fragment, str(ctx.exception))

    def test_missing_file(self):
        with self.assertRaises(ConfigError):
            load_config(ROOT / "no_such_config.xml")

    def test_xml_structure(self):
        self.check_error("bad_xml", "некорректный XML")
        self.check_error("wrong_root", "корневой элемент")
        self.check_error("unknown_param", "неизвестный параметр")
        self.check_error("duplicate_param", "указан дважды")
        self.check_error("nested_param", "вложенные элементы")

    def test_package(self):
        self.check_error("missing_package", "<package>")
        self.check_error("empty_package", "не может быть пустым")
        self.check_error("bad_package", "недопустимое имя")
        self.check_error("bad_test_package", "латинских букв")

    def test_repository(self):
        self.check_error("missing_repository", "<repository>")
        self.check_error("bad_repository_url", "http://")
        self.check_error("missing_test_repo", "не найден")

    def test_flags(self):
        self.check_error("bad_test_mode", "<test_mode>")
        self.check_error("bad_ascii_tree", "<ascii_tree>")

    def test_output_image(self):
        self.check_error("missing_output_image", "<output_image>")
        self.check_error("bad_output_image", ".svg")
        self.check_error("missing_image_dir", "не существует")


if __name__ == "__main__":
    unittest.main()
