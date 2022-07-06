from fastapi.routing import APIRouter, HTTPException

from .schemas import ParsedPrice
from .controllers import parse_prices_by_host

router = APIRouter(
    prefix="/prices",
    tags=["prices"]
)


@router.get(
    path="",
    response_model=list[ParsedPrice],
    name="Parse Prices",
    description="Спарсить цены с указанного хоста.\t"
                "Поддерживаемые хосты: plata57.ru, vekolom.ru, uralvtordrag.ru.\t"
                "Значение price возвращается в рублях за кг",
    responses={400: {"description": "Bad Request - Был передан неподдерживаемый хост"}}
)
async def read_prices_by_host(host: str) -> list[ParsedPrice]:
    try:
        prices = parse_prices_by_host(host=host)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Хост {host} - не поддерживается!")
    return prices

