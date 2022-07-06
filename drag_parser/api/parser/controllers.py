from hashlib import md5
from drag_parser import parser
from .schemas import ParsedPrice


def parse_prices_from_categories_by_host(host: str) -> list[ParsedPrice]:
    host_parser = parser.get_parser_for_host(host=host)

    soup = host_parser.get_soup()
    categories = host_parser.get_categories_urls(soup)
    prices = []

    for category in categories:
        category_soup = host_parser.get_soup_for_url(category)
        prices.extend(host_parser.parse_prices(soup=category_soup))

    return [ParsedPrice(
        id=md5(f"{price.get('host')}{price.get('title')}".encode()).hexdigest(),
        host=price.get('host'),
        title=price.get('title'),
        price=price.get('price'),
    ) for price in prices]


def parse_prices_by_host(host: str) -> list[ParsedPrice]:
    if host in parser.HOSTS_WITH_CATEGORIES:
        return parse_prices_from_categories_by_host(host=host)

    host_parser = parser.get_parser_for_host(host=host)
    host_soup = host_parser.get_soup()
    prices = host_parser.parse_prices(soup=host_soup)

    return [ParsedPrice(
        id=md5(f"{price.get('host')}{price.get('title')}".encode()).hexdigest(),
        host=price.get('host'),
        title=price.get('title'),
        price=price.get('price'),
    ) for price in prices]
