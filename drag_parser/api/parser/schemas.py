from pydantic import BaseModel


class ParsedPrice(BaseModel):
    id: str
    host: str
    title: str
    price: float
