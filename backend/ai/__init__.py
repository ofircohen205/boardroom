# backend/ai/__init__.py
"""AI analysis system: agents, workflow, state management, and tools."""
from .workflow import create_boardroom_graph, BoardroomGraph
from .agents.base import (
    BaseLLMClient,
    AnthropicClient,
    OpenAIClient,
    GeminiClient,
    get_llm_client,
)
from .agents.fundamental import FundamentalAgent
from .agents.sentiment import SentimentAgent
from .agents.technical import TechnicalAgent
from .agents.risk_manager import RiskManagerAgent
from .agents.chairperson import ChairpersonAgent
from .state.enums import Market, Action, AgentType, Trend, SentimentSource, WSMessageType, AnalysisMode
from .state.agent_state import (
    AgentState,
    FundamentalReport,
    SentimentReport,
    TechnicalReport,
    RiskAssessment,
    Decision,
)

__all__ = [
    # Workflow
    "create_boardroom_graph",
    "BoardroomGraph",
    # LLM Clients
    "BaseLLMClient",
    "AnthropicClient",
    "OpenAIClient",
    "GeminiClient",
    "get_llm_client",
    # Agents
    "FundamentalAgent",
    "SentimentAgent",
    "TechnicalAgent",
    "RiskManagerAgent",
    "ChairpersonAgent",
    # Enums
    "Market",
    "Action",
    "AgentType",
    "Trend",
    "SentimentSource",
    "WSMessageType",
    "AnalysisMode",
    # State
    "AgentState",
    "FundamentalReport",
    "SentimentReport",
    "TechnicalReport",
    "RiskAssessment",
    "Decision",
]
