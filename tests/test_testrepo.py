"""Тесты чтения тестового репозитория."""

import unittest

from tests import ROOT
from testrepo import TestRepositoryError, load_repository, parse_repository


class ParseRepositoryTest(unittest.TestCase):
    """Разбор файла описания графа."""

    def test_simple(self):
        repo = load_repository(ROOT / "repos" / "simple.txt")
        self.assertEqual(repo, {
            "A": ["B", "C"], "B": ["D"], "C": ["D"], "D": [],
        })

    def test_blank_lines_and_duplicates(self):
        repo = parse_repository("A: B B C\n\nB:\n")
        self.assertEqual(repo, {"A": ["B", "C"], "B": []})

    def test_multi_letter_names(self):
        self.assertEqual(parse_repository("AB: CD"), {"AB": ["CD"]})

    def test_bad_name(self):
        with self.assertRaisesRegex(TestRepositoryError, "строка 2"):
            parse_repository("A: B\nB: c\n")

    def test_bad_format(self):
        with self.assertRaisesRegex(TestRepositoryError, "формат"):
            parse_repository("A B")

    def test_duplicate_package(self):
        with self.assertRaisesRegex(TestRepositoryError, "повторно"):
            parse_repository("A: B\nA: C")

    def test_missing_file(self):
        with self.assertRaises(TestRepositoryError):
            load_repository(ROOT / "repos" / "no_such.txt")


if __name__ == "__main__":
    unittest.main()
