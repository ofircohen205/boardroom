from pathlib import Path

# Load prompt templates
_PROMPTS_DIR = Path(__file__).parent
with open(_PROMPTS_DIR / "comparison.md", "r") as f:
    COMPARISON_PROMPT_TEMPLATE = f.read()


# JSON schema for comparison structured output
COMPARISON_SCHEMA = {
    "type": "object",
    "properties": {
        "rankings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer", "minimum": 1},
                    "ticker": {"type": "string"},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "string"},
                },
                "required": ["rank", "ticker", "score", "rationale"],
            },
        },
        "best_pick": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["rankings", "best_pick", "summary"],
}


def format_comparison_prompt(tickers: list[str], comparison_data: list[dict]) -> str:
    """Format the comparison prompt with actual stock data.

    Args:
        tickers: List of stock tickers being compared
        comparison_data: List of dicts containing ticker, action, confidence, and summaries

    Returns:
        Formatted prompt string ready for LLM
    """
    # Format stock data section
    stock_data_str = ""
    for i, data in enumerate(comparison_data, 1):
        stock_data_str += f"""
{i}. {data["ticker"]}
   Recommendation: {data["action"]} (confidence: {data["confidence"]:.0%})
   Fundamental: {data["fundamental_summary"]}
   Sentiment: {data["sentiment_summary"]}
   Technical: {data["technical_summary"]}
"""

    # Replace placeholders in template
    return COMPARISON_PROMPT_TEMPLATE.format(
        stock_count=len(tickers), stock_data=stock_data_str
    )


__all__ = [
    "COMPARISON_PROMPT_TEMPLATE",
    "COMPARISON_SCHEMA",
    "format_comparison_prompt",
]
