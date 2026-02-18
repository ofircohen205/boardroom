from pydantic import BaseModel


class WatchlistItemSchema(BaseModel):
    id: str
    ticker: str
    market: str


class WatchlistSchema(BaseModel):
    id: str
    name: str
    items: list[WatchlistItemSchema]
