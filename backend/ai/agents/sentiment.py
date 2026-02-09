import re
from datetime import datetime

from backend.ai.agents.base import get_llm_client
from backend.ai.state.agent_state import NewsItem, SentimentReport, SocialMention
from backend.ai.state.enums import Market, SentimentSource
from backend.ai.tools.search import get_search_client


class SentimentAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.search = get_search_client()

    async def analyze(self, ticker: str, market: Market) -> SentimentReport:
        # Search with market context
        market_str = "TASE" if market == Market.TASE else "US"
        news_results = await self.search.search_news(ticker, market=market_str, hours=48, num_results=15)
        social_results = await self.search.search_social(ticker, market=market_str, hours=48, num_results=15)

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

        # Build richer context for LLM
        news_text = "\n".join([f"- [NEWS] {n['title']} ({n['published_at']}): {n['snippet']}" for n in news_items])
        social_text = "\n".join([f"- [SOCIAL] {s['content'][:300]}" for s in social_mentions])
        
        content_summary = f"""RECENT NEWS:
{news_text if news_text else "No specific news found."}

SOCIAL MEDIA DISCUSSIONS:
{social_text if social_text else "No significant social chatter found."}
"""

        prompt = f"""Analyze sentiment for {ticker} ({market_str} Market) based on the following data:

{content_summary}

Respond with:
1. Overall sentiment score from -1.0 (very negative) to 1.0 (very positive)
2. Brief summary (2-3 sentences) highlighting key drivers.

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
