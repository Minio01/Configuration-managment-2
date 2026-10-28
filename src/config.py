"""Чтение и проверка XML-конфигурации приложения."""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

FIELDS = (
    "package",
    "repository",
    "test_mode",
    "output_image",
    "ascii_tree",
    "filter_substring",
)
REQUIRED_FIELDS = ("package", "repository", "test_mode", "output_image")
DEFAULTS = {"ascii_tree": "false", "filter_substring": ""}
ROOT_TAG = "config"
TRUE_VALUES = ("true", "1", "yes")
FALSE_VALUES = ("false", "0", "no")
URL_SCHEMES = ("http", "https")
IMAGE_SUFFIX = ".svg"
PACKAGE_RE = re.compile(r"[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?")
TEST_PACKAGE_RE = re.compile(r"[A-Z]+")


class ConfigError(Exception):
    """Ошибка в конфигурационном файле."""


@dataclass(frozen=True)
class Config:
    """Параметры, настраиваемые пользователем."""

    package: str
    repository: str
    test_mode: bool
    output_image: str
    ascii_tree: bool
    filter_substring: str

    def items(self):
        """Вернуть параметры в виде пар (ключ, значение)."""
        return [(name, getattr(self, name)) for name in FIELDS]


def load_config(path):
    """Прочитать XML-файл конфигурации и проверить все параметры."""
    path = Path(path)
    values = read_values(parse_xml(path))
    base_dir = path.resolve().parent
    test_mode = parse_bool(values["test_mode"], "test_mode")
    return Config(
        package=check_package(values["package"], test_mode),
        repository=check_repository(
            values["repository"], test_mode, base_dir
        ),
        test_mode=test_mode,
        output_image=check_output_image(values["output_image"], base_dir),
        ascii_tree=parse_bool(values["ascii_tree"], "ascii_tree"),
        filter_substring=values["filter_substring"],
    )


def parse_xml(path):
    """Разобрать XML-файл и вернуть корневой элемент <config>."""
    if not path.is_file():
        raise ConfigError(f"файл конфигурации не найден: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ConfigError(f"некорректный XML: {exc}") from exc
    if root.tag != ROOT_TAG:
        raise ConfigError(
            f"корневой элемент должен быть <{ROOT_TAG}>, "
            f"а найден <{root.tag}>"
        )
    return root


def read_values(root):
    """Собрать значения параметров из дочерних элементов <config>."""
    values = {}
    for child in root:
        if child.tag not in FIELDS:
            raise ConfigError(f"неизвестный параметр <{child.tag}>")
        if child.tag in values:
            raise ConfigError(f"параметр <{child.tag}> указан дважды")
        if len(child):
            raise ConfigError(
                f"параметр <{child.tag}> не может содержать "
                "вложенные элементы"
            )
        values[child.tag] = (child.text or "").strip()
    for name in REQUIRED_FIELDS:
        if name not in values:
            raise ConfigError(f"отсутствует обязательный параметр <{name}>")
        if not values[name]:
            raise ConfigError(f"параметр <{name}> не может быть пустым")
    for name, default in DEFAULTS.items():
        values.setdefault(name, default)
    return values


def parse_bool(text, name):
    """Преобразовать строку в логическое значение."""
    value = text.lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise ConfigError(
        f"параметр <{name}> должен быть true или false, получено {text!r}"
    )


def check_package(name, test_mode):
    """Проверить имя анализируемого пакета."""
    if test_mode:
        if not TEST_PACKAGE_RE.fullmatch(name):
            raise ConfigError(
                "в тестовом режиме имя пакета состоит из больших "
                f"латинских букв, получено {name!r}"
            )
    elif not PACKAGE_RE.fullmatch(name):
        raise ConfigError(f"недопустимое имя пакета: {name!r}")
    return name


def check_repository(value, test_mode, base_dir):
    """Проверить URL репозитория или путь к тестовому репозиторию."""
    if test_mode:
        path = Path(value)
        if not path.is_absolute():
            path = base_dir / path
        if not path.is_file():
            raise ConfigError(f"файл тестового репозитория не найден: {value}")
        return str(path.resolve())
    url = urlparse(value)
    if url.scheme not in URL_SCHEMES or not url.netloc:
        raise ConfigError(
            f"URL репозитория должен начинаться с http:// или https://, "
            f"получено {value!r}"
        )
    return value.rstrip("/")


def check_output_image(value, base_dir):
    """Проверить имя файла, в который будет сохранено изображение."""
    path = Path(value)
    if path.suffix.lower() != IMAGE_SUFFIX:
        raise ConfigError(
            f"файл изображения должен иметь расширение {IMAGE_SUFFIX}, "
            f"получено {value!r}"
        )
    if not path.is_absolute():
        path = base_dir / path
    if not path.parent.is_dir():
        raise ConfigError(f"каталог для изображения не существует: {value}")
    return str(path.resolve())
