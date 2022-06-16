from pkg_resources import resource_filename
from pathlib import Path


AUTHOR = 'Firin Kinuo'
EMAIL = 'deals@fkinuo.ru'
TELEGRAM = "https://t.me/fkinuo"
NAME = 'drag_parser'
LICENSE = 'AGPL-3.0'
URL = 'https://git.fkinuo.ru/drag-parser'
DESCRIPTION = 'Parsing price lists from hosts and transferring them via RestAPI'
ROOT = Path(resource_filename(NAME, '')).parent


def _generate_modules(*modules: str) -> list[str]:
    return [f"drag_parser.{module}" for module in modules]


MODULES = [NAME, *_generate_modules('settings')]

with open(file=Path(ROOT, 'VERSION'), mode='r', encoding="UTF-8") as version_file:
    VERSION = version_file.read().replace("v", "")
