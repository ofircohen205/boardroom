from datetime import datetime, timedelta
from typing import TypedDict

from exa_py import Exa

from backend.config import settings


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str
    published_at: str
    source: str


class ExaSearchClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.exa_api_key
        self._client: Exa | None = None

    @property
    def client(self) -> Exa:
        if self._client is None:
            self._client = Exa(api_key=self.api_key)
        return self._client

    async def _search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        response = self.client.search_and_contents(
            query,
            num_results=num_results,
            text=True,
            use_autoprompt=True,
        )
        return [
            SearchResult(
                title=r.title or "",
                url=r.url,
                snippet=r.text[:500] if r.text else "",
                published_at=r.published_date or "",
                source="news",
            )
            for r in response.results
        ]

    async def search_news(
        self, ticker: str, hours: int = 48, num_results: int = 10
    ) -> list[SearchResult]:
        query = f"{ticker} stock news financial analysis"
        results = await self._search(query, num_results)
        return results

    async def search_social(
        self, ticker: str, hours: int = 48, num_results: int = 10
    ) -> list[SearchResult]:
        query = f"{ticker} stock reddit twitter sentiment"
        results = await self._search(query, num_results)
        for r in results:
            if "reddit" in r["url"].lower():
                r["source"] = "reddit"
            elif "twitter" in r["url"].lower() or "x.com" in r["url"].lower():
                r["source"] = "twitter"
        return results


def get_search_client() -> ExaSearchClient:
    return ExaSearchClient()
