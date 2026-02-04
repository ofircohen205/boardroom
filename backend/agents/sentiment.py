import re
from datetime import datetime

from backend.agents.base import get_llm_client
from backend.state.agent_state import NewsItem, SentimentReport, SocialMention
from backend.state.enums import Market, SentimentSource
from backend.tools.search import get_search_client


class SentimentAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.search = get_search_client()

    async def analyze(self, ticker: str, market: Market) -> SentimentReport:
        news_results = await self.search.search_news(ticker, hours=48)
        social_results = await self.search.search_social(ticker, hours=48)

        news_items: list[NewsItem] = []
        for r in news_results:
            news_items.append(
                NewsItem(
                    source=SentimentSource.NEWS,
                    title=r["title"],
                    url=r["url"],
                    published_at=datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) if r["published_at"] else datetime.now(),
                    sentiment=0.0,
                    snippet=r["snippet"],
                )
            )

        social_mentions: list[SocialMention] = []
        for r in social_results:
            source = SentimentSource.REDDIT if "reddit" in r.get("source", "") else SentimentSource.TWITTER
            social_mentions.append(
                SocialMention(
                    source=source,
                    content=r["snippet"],
                    author="",
                    url=r["url"],
                    timestamp=datetime.now(),
                    engagement=0,
                )
            )

        # Get LLM to analyze sentiment
        content_summary = "\n".join([f"- {n['title']}: {n['snippet'][:100]}" for n in news_items[:5]])
        prompt = f"""Analyze sentiment for {ticker} based on recent news:
{content_summary}

Respond with:
1. Overall sentiment score from -1.0 (very negative) to 1.0 (very positive)
2. Brief summary (2-3 sentences)

Format: SENTIMENT: <score>
SUMMARY: <text>"""

        response = await self.llm.complete([{"role": "user", "content": prompt}])

        # Parse response
        sentiment_match = re.search(r"SENTIMENT:\s*([-\d.]+)", response)
        summary_match = re.search(r"SUMMARY:\s*(.+)", response, re.DOTALL)

        overall_sentiment = float(sentiment_match.group(1)) if sentiment_match else 0.0
        summary = summary_match.group(1).strip() if summary_match else response

        return SentimentReport(
            overall_sentiment=max(-1.0, min(1.0, overall_sentiment)),
            news_items=news_items,
            social_mentions=social_mentions,
            summary=summary,
        )
