import re
from typing import TypedDict
from urllib import parse
from abc import abstractmethod
from enum import Enum

import requests

from bs4 import BeautifulSoup, Tag

__all__ = [
    "Price", "Parser", "ParserVekolom", "ParserPlata57",
    "get_parser_for_host"
]


class AvailableHosts(Enum):
    VEKOLOM = "vekolom.ru"
    PLATA57 = "plata57.ru"


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
        response = requests.get(self.url, timeout=2.0)
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


def get_parser_for_host(host: str) -> Parser:
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
        case _:
            raise ValueError("The specified host is not supported by the parser")


class ParserVekolom(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://vekolom.ru/pricelist"

    @classmethod
    def _parse_title(cls, row: Tag) -> str:
        title = row.find(class_="positionname")
        return title.text if title else ""

    @classmethod
    def _match_price(cls, price_string: str) -> float:
        matched_price = re.search(r'(?P<price>\d+)', price_string)
        return float(matched_price.group('price')) if matched_price else 0.0

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
