from pydantic import BaseModel


class PortfolioPositionSchema(BaseModel):
    id: str
    ticker: str
    quantity: float
    avg_entry_price: float
    sector: str


class PortfolioSchema(BaseModel):
    id: str
    name: str
    positions: list[PortfolioPositionSchema]