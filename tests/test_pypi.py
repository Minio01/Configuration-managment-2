"""Тесты получения зависимостей из PyPI (без обращения к сети)."""

import io
import json
import unittest
import urllib.error
from unittest import mock

import pypi

REQUESTS_META = {
    "info": {
        "requires_dist": [
            "charset_normalizer<4,>=2",
            "idna<4,>=2.5",
            "urllib3<3,>=1.26",
            "certifi>=2023.5.7",
            'PySocks!=1.5.7,>=1.5.6; extra == "socks"',
            'chardet<8,>=3.0.2; extra == "use-chardet-on-py3"',
        ]
    }
}


def fake_response(payload):
    """Создать объект, имитирующий ответ urlopen."""
    body = payload if isinstance(payload, bytes) else json.dumps(payload)
    if isinstance(body, str):
        body = body.encode("utf-8")
    return io.BytesIO(body)


class ParseTest(unittest.TestCase):
    """Разбор строк Requires-Dist."""

    def test_normalize_name(self):
        self.assertEqual(pypi.normalize_name("Charset_Normalizer"),
                         "charset-normalizer")
        self.assertEqual(pypi.normalize_name("zope.interface"),
                         "zope-interface")

    def test_parse_requirement(self):
        self.assertEqual(pypi.parse_requirement("idna<4,>=2.5"), "idna")
        self.assertEqual(pypi.parse_requirement("foo[bar] (>=1.0)"), "foo")
        self.assertEqual(
            pypi.parse_requirement('tomli>=1.1; python_version < "3.11"'),
            "tomli",
        )
        self.assertIsNone(
            pypi.parse_requirement('pytest; extra == "test"')
        )

    def test_parse_bad_requirement(self):
        with self.assertRaises(pypi.RepositoryError):
            pypi.parse_requirement("!!!")

    def test_parse_dependencies(self):
        self.assertEqual(
            pypi.parse_dependencies(REQUESTS_META),
            ["charset-normalizer", "idna", "urllib3", "certifi"],
        )

    def test_no_dependencies(self):
        self.assertEqual(pypi.parse_dependencies({"info": {}}), [])
        meta = {"info": {"requires_dist": None}}
        self.assertEqual(pypi.parse_dependencies(meta), [])

    def test_duplicates_removed(self):
        meta = {"info": {"requires_dist": [
            'numpy>=1.22; python_version < "3.11"',
            'numpy>=1.23; python_version >= "3.11"',
        ]}}
        self.assertEqual(pypi.parse_dependencies(meta), ["numpy"])


class FetchTest(unittest.TestCase):
    """Загрузка описания пакета по URL."""

    @mock.patch("urllib.request.urlopen")
    def test_get_dependencies(self, urlopen):
        urlopen.return_value = fake_response(REQUESTS_META)
        deps = pypi.get_dependencies("https://pypi.org/pypi", "requests")
        self.assertEqual(len(deps), len(REQUESTS_META["info"]
                                        ["requires_dist"]) - 2)
        url = urlopen.call_args.args[0]
        self.assertEqual(url, "https://pypi.org/pypi/requests/json")

    @mock.patch("urllib.request.urlopen")
    def test_not_found(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            "url", pypi.HTTP_NOT_FOUND, "Not Found", None, None
        )
        with self.assertRaisesRegex(pypi.RepositoryError, "не найден"):
            pypi.fetch_metadata("https://pypi.org/pypi", "nope")

    @mock.patch("urllib.request.urlopen")
    def test_connection_error(self, urlopen):
        urlopen.side_effect = urllib.error.URLError("no route")
        with self.assertRaisesRegex(pypi.RepositoryError, "подключиться"):
            pypi.fetch_metadata("https://pypi.invalid/pypi", "requests")

    @mock.patch("urllib.request.urlopen")
    def test_bad_json(self, urlopen):
        urlopen.return_value = fake_response(b"<html>")
        with self.assertRaisesRegex(pypi.RepositoryError, "JSON"):
            pypi.fetch_metadata("https://pypi.org/pypi", "requests")


if __name__ == "__main__":
    unittest.main()
