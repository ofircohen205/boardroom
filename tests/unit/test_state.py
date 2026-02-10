from backend.ai.state.enums import (
    Market,
    Trend,
    Action,
    SentimentSource,
    AgentType,
    WSMessageType,
)


def test_market_enum():
    assert Market.US.value == "US"
    assert Market.TASE.value == "TASE"


def test_action_enum():
    assert Action.BUY.value == "BUY"
    assert Action.SELL.value == "SELL"
    assert Action.HOLD.value == "HOLD"


def test_agent_type_enum():
    assert len(AgentType) == 5
    assert AgentType.CHAIRPERSON.value == "chairperson"
