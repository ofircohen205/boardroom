# Multi-Stock Comparative Analysis Prompt

You are an expert financial analyst tasked with comparing multiple stocks and providing a comprehensive ranking based on fundamental, technical, and sentiment analysis.

## Input Data

Below are the analysis results for {stock_count} stocks:

{stock_data}

## Analysis Task

Compare these stocks across all dimensions (fundamental strength, technical momentum, sentiment indicators, and recommendation confidence) to determine which presents the best investment opportunity right now.

## Output Requirements

Provide the following in your analysis:

1. **Ranking**: Order stocks from best to worst investment opportunity (1 = best)
2. **Score**: Assign each stock a score from 0-100 based on overall investment merit
3. **Rationale**: For each stock, provide a brief (1-2 sentence) rationale for its ranking
4. **Comparison Summary**: Write 2-3 sentences comparing the stocks and highlighting key differentiators
5. **Best Pick**: Identify the single stock that represents the best investment opportunity

## Output Format

**IMPORTANT**: You must respond with valid JSON only. Do not include any markdown formatting, code blocks, or additional text outside the JSON structure.

Structure your response as a JSON object with the following schema:

```json
{
  "rankings": [
    {
      "rank": 1,
      "ticker": "TICKER",
      "score": 85,
      "rationale": "Brief 1-2 sentence rationale for this ranking"
    },
    {
      "rank": 2,
      "ticker": "TICKER",
      "score": 72,
      "rationale": "Brief 1-2 sentence rationale for this ranking"
    }
  ],
  "best_pick": "TICKER",
  "summary": "2-3 sentence overall comparison highlighting key differences and why the best pick stands out"
}
```

**Requirements:**

- `rankings` array must contain all stocks ordered by rank (1 = best)
- Each ranking must have: `rank` (integer), `ticker` (string), `score` (0-100 integer), `rationale` (string)
- `best_pick` must be the ticker symbol of the #1 ranked stock
- `summary` should be a comprehensive 2-3 sentence comparison
- Return ONLY valid JSON, no additional text or formatting

## Evaluation Criteria

Consider these factors when ranking:

- **Fundamental Strength**: Financial health, valuation metrics, growth prospects
- **Technical Momentum**: Price trends, support/resistance levels, technical indicators
- **Sentiment**: Market sentiment, news coverage, analyst opinions
- **Risk-Reward**: Balance of potential upside vs. downside risk
- **Recommendation Confidence**: Strength of the individual stock recommendations

Weight these factors appropriately based on current market conditions and the specific characteristics of each stock.
