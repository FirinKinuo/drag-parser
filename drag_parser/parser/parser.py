import re
from typing import TypedDict
from urllib import parse
from abc import abstractmethod
from enum import Enum
from logging import getLogger

import requests

from bs4 import BeautifulSoup, Tag

log = getLogger("parser")

__all__ = [
    "Price", "Parser", "ParserVekolom", "ParserPlata57", "ParserUralvtordrag",
    "get_parser_for_host",
    "HOSTS_WITH_CATEGORIES"
]


class AvailableHosts(Enum):
    VEKOLOM = "vekolom.ru"
    PLATA57 = "plata57.ru"
    URALVTORDRAG = "uralvtordrag.ru"


HOSTS_WITH_CATEGORIES = (
    AvailableHosts.URALVTORDRAG.value,
)


class Price(TypedDict):
    title: str
    host: str
    price: float


class Parser:
    def __init__(self):
        self.url: str = ""

    def get_soup(self) -> BeautifulSoup:
        """
        Returns the html soup from the specified site

        :return: BeautifulSoup
        """
        return self.get_soup_for_url(self.url)

    @classmethod
    def get_soup_for_url(cls, url: str) -> BeautifulSoup:
        """
        Returns html soup for given host
        :param url: The path of the URL for which you want to get the soup
        :type url: str

        :return: BeautifulSoup
        """
        response = requests.get(url, timeout=5.0)
        return BeautifulSoup(response.text, 'lxml')

    @property
    def _host(self) -> str:
        parsed_url = parse.urlparse(self.url)
        return parsed_url.netloc

    @abstractmethod
    def parse_prices(self, soup: BeautifulSoup) -> list[Price]:
        """
        Parsing prices from the transferred site

        :param soup: Generated html soup from the site via BeautifulSoup
        :type soup: BeautifulSoup

        :return: list[Price]
        """
        ...


class ParserCategories(Parser):
    @abstractmethod
    def get_categories_urls(self, soup: BeautifulSoup) -> tuple[str]:
        """
        Get URL tuple with website categories

        :param soup: Generated html soup from the site via BeautifulSoup
        :type soup: BeautifulSoup

        :return: tuple[str] - Tuple with category URL strings
        """

    ...


def get_parser_for_host(host: str) -> Parser | ParserCategories:
    """
    Get parser for specified host

    :param host: Host, for which you need to get a parser
    :type host: str

    :return: If the specified host is supported by the parser, will return one of the Parser child classes

    :raise ValueError: If the specified host is not supported by the parser
    """
    match host:
        case AvailableHosts.VEKOLOM.value:
            return ParserVekolom()
        case AvailableHosts.PLATA57.value:
            return ParserPlata57()
        case AvailableHosts.URALVTORDRAG.value:
            return ParserUralvtordrag()
        case _:
            raise ValueError("The specified host is not supported by the parser")


class ParserVekolom(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://vekolom.ru/pricelist"

    @classmethod
    def _parse_title(cls, row: Tag) -> str:
        title = row.find(class_="positionname")
        if not title:
            log.error(f"Title was not found for the row {row.text}, an empty string will be returned")
            return ""
        return title.text if title else ""

    @classmethod
    def _match_price(cls, price_string: str) -> float:
        matched_price = re.search(r'(?P<price>\d+)', price_string)
        if not matched_price:
            log.error(f"The price was not found for the string {price_string}, 0.0 will be returned")
            return 0.0

        return float(matched_price.group('price'))

    @classmethod
    def _parse_price_at_flexbox(cls, row: Tag) -> list[float]:
        prices = row.find_all(class_="price_flex_value")

        return [cls._match_price(price.text) for price in prices]

    @classmethod
    def _parse_price(cls, row: Tag) -> float:
        price = row.find(class_="positionprice")

        if price is None:
            prices = cls._parse_price_at_flexbox(row=row)
            return prices[-1] if prices else 0.0

        return cls._match_price(price.text)

    def parse_prices(self, soup: BeautifulSoup) -> list[Price]:
        rows = soup.find_all(class_='price-table-item-wr')
        prices: list[Price] = []

        for row in rows:
            title = self._parse_title(row=row)
            if title == "":
                continue

            price = self._parse_price(row=row)

            prices.append(Price(
                title=title,
                price=price,
                host=self._host
            ))

        return prices


class ParserPlata57(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://plata57.ru"

    @classmethod
    def _parse_title(cls, row: Tag) -> str:
        title = row.find(attrs={"style": "color: #000000;"})
        if not title:
            log.error(f"Title was not found for the row {row.text}, an empty string will be returned")
            return ""

        return title.text if title else ""

    @classmethod
    def _match_price(cls, price_string: str) -> float:
        matched_price = 0.0
        price_regexps = [
            r'^(?P<price>\d+)$',
            r'^от\s(?P<price>\d+)',
            r'\d+\-(?P<price>\d+)',
            r'\d+\/(?P<price>\d+)'
        ]

        for regexp in price_regexps:
            if matched_price := re.search(regexp, price_string):
                matched_price = float(matched_price.group('price'))
                break

        return matched_price

    @classmethod
    def _parse_price(cls, row: Tag) -> float:
        price = [column
                 for column in row.find_all(attrs={"style": "text-align: center; vertical-align: middle;"})
                 if column.find("b") or column.find('strong')]

        if not price:
            return 0.0

        return cls._match_price(price[0].text)

    def parse_prices(self, soup: BeautifulSoup) -> list[Price]:
        rows = soup.find('table', class_='table table-bordered table-hover table-price').find('tbody').find_all("tr")

        prices = [Price(
            title=self._parse_title(row=row),
            price=self._parse_price(row=row),
            host=self._host
        ) for row in rows]

        return prices


class ParserUralvtordrag(ParserCategories):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://uralvtordrag.ru"

    @classmethod
    def _parse_title(cls, row: Tag) -> str:
        title = row.find(class_="item_caption")
        if not title:
            log.error(f"Title was not found for the row {row.text}, an empty string will be returned")
            return ""

        return title.text

    @classmethod
    def _match_price(cls, price_string: str) -> float:
        price_regexp = r"^(?P<price>\d+)"

        if matched_price := re.search(price_regexp, price_string):
            return float(matched_price.group('price'))

        log.error(f"The price was not found for the string {price_string}, 0.0 will be returned")
        return 0.0

    @classmethod
    def _parse_price(cls, row: Tag) -> float:
        price = row.find("span", class_="row5 td item_prise")

        if not price:
            log.error(f"Unable to parse price from {row=}, 0.0 will be returned")
            return 0.0

        return cls._match_price(price.text)

    def parse_prices(self, soup: BeautifulSoup) -> list[Price]:
        rows = soup.find_all("div", class_="catalogItem")

        prices = [Price(
            title=self._parse_title(row=row),
            price=self._parse_price(row=row),
            host=self._host
        ) for row in rows]

        return prices

    def get_categories_urls(self, soup: BeautifulSoup) -> tuple[str]:
        categories_list = soup.find_all("a", class_="catalog_part")
        return tuple(f"{self.url}{category.attrs.get('href')}" for category in categories_list)
