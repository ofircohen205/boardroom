from typing import TypedDict

from openai import AsyncOpenAI

from backend.core.cache import cached
from backend.core.settings import settings


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str
    published_at: str
    source: str


class OpenAISearchClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.openai_api_key
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def _search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        response = await self.client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=query,
        )

        results: list[SearchResult] = []
        seen_urls: set[str] = set()

        for item in response.output:
            if item.type == "message":
                for block in item.content:
                    text = getattr(block, "text", "") or ""
                    for ann in getattr(block, "annotations", None) or []:
                        url = getattr(ann, "url", None)
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        title = getattr(ann, "title", "") or ""

                        # Extract context around the citation for a snippet
                        snippet = title
                        start_idx = getattr(ann, "start_index", None)
                        if start_idx is not None and text:
                            context_start = max(0, start_idx - 300)
                            context_end = min(len(text), start_idx + 100)
                            snippet = text[context_start:context_end].strip()

                        results.append(
                            SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet[:500],
                                published_at="",
                                source="news",
                            )
                        )
                        if len(results) >= num_results:
                            break

        return results

    @cached(ttl=900, skip_self=True)
    async def search_news(
        self, ticker: str, market: str = "US", hours: int = 48, num_results: int = 15
    ) -> list[SearchResult]:
        context = ""
        if market == "TASE":
            context = " from Israeli financial news sources (Globes, Calcalist, TheMarker, Bizportal) and international coverage"

        query = f"Latest financial news and analysis for {ticker} stock{context} in the last {hours} hours"
        return await self._search(query, num_results)

    @cached(ttl=900, skip_self=True)
    async def search_social(
        self, ticker: str, market: str = "US", hours: int = 48, num_results: int = 15
    ) -> list[SearchResult]:
        context = ""
        if market == "TASE":
            context = " in Israel market context"

        query = f"Recent Reddit and Twitter/X discussions about {ticker} stock{context} sentiment"
        results = await self._search(query, num_results)
        for r in results:
            if "reddit" in r["url"].lower():
                r["source"] = "reddit"
            elif "twitter" in r["url"].lower() or "x.com" in r["url"].lower():
                r["source"] = "twitter"
        return results


def get_search_client() -> OpenAISearchClient:
    return OpenAISearchClient()
