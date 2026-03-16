"""ORM models package — import all models here to populate Base.metadata."""

from app.models.ai_analysis import AiAnalysis
from app.models.alert import Alert
from app.models.dev_activity import DevActivity
from app.models.historical_candle import HistoricalCandle
from app.models.historical_snapshot import HistoricalSnapshot
from app.models.market_data import MarketData
from app.models.narrative import NarrativeCluster
from app.models.score import TokenScore
from app.models.scoring_weight import ScoringWeight
from app.models.signal import Signal
from app.models.social_data import SocialData
from app.models.token import Token

__all__ = [
    "AiAnalysis",
    "Alert",
    "DevActivity",
    "HistoricalCandle",
    "HistoricalSnapshot",
    "MarketData",
    "NarrativeCluster",
    "TokenScore",
    "ScoringWeight",
    "Signal",
    "SocialData",
    "Token",
]
