"""HeuristicSubScorer — derives all sub-scores from CoinGecko market data.

Phase 9: Until external data sources (GitHub, social, LLM) are wired in,
this module computes reasonable heuristic sub-scores using only the market
data already collected by CoinGecko + MarketProcessor.

Each heuristic has a clear rationale documented inline. Scores will become
more accurate as richer data sources are added in Phases 10-12.

.. note:: **Known limitation — volume-driven memecoins rank too high**

   With real CoinGecko data (Phase 9), tokens with abnormally high
   volume/market-cap ratios (e.g. memecoins during hype events) score
   disproportionately well in growth, adoption, narrative and cycle-leader
   because all four pillar heuristics use ``volume_mcap_ratio`` as a
   positive signal.  In practice, high speculative volume ≠ real adoption.

   Real adoption is better measured by on-chain active addresses, TVL
   (DeFiLlama), developer activity (GitHub), and institutional/government
   adoption signals (news, Twitter/X) — none of which are available yet.

   This is **expected and intentional** in Phase 9.  Future phases will
   address it:

   - Phase 10: DeFiLlama TVL + GitHub commits → real adoption & dev scores
   - Phase 11: ML CycleLeaderModel replaces the heuristic cycle_leader
   - Phase 12: Backtesting will validate and tune pillar weights

   Additionally, the 5-pillar weight distribution (risk at only 10%) may
   need rebalancing once richer data sources are integrated.  Keep risk
   weight adjustment as a tuning parameter for Phase 12 backtesting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.processors.normalizer import clamp, min_max_normalize


@dataclass(frozen=True, slots=True)
class SubScoreResult:
    """Immutable container for the 9 sub-scores derived from market data."""

    technology_score: float
    tokenomics_score: float
    adoption_score: float
    dev_activity_score: float
    narrative_score: float
    growth_score: float
    risk_score: float
    listing_probability: float
    cycle_leader_prob: float

    def to_dict(self) -> dict[str, float]:
        """Return all 9 sub-scores as a plain dict for easy merging."""
        return {
            "technology_score": self.technology_score,
            "tokenomics_score": self.tokenomics_score,
            "adoption_score": self.adoption_score,
            "dev_activity_score": self.dev_activity_score,
            "narrative_score": self.narrative_score,
            "growth_score": self.growth_score,
            "risk_score": self.risk_score,
            "listing_probability": self.listing_probability,
            "cycle_leader_prob": self.cycle_leader_prob,
        }


# ---------------------------------------------------------------------------
# Heuristic upper bounds & constants
# ---------------------------------------------------------------------------
_RANK_MAX = 1000  # CoinGecko returns top ~10 000; we cap at 1000 for scoring
_MCAP_LOG_MIN = 4.0  # log10($10k) ≈ 4
_MCAP_LOG_MAX = 12.0  # log10($1T) = 12
_VOLUME_RATIO_MAX = 0.5  # vol/mcap ratio ceiling
_VELOCITY_MAX = 100.0  # price change ±100 %
_ATH_DIST_MAX = 99.0  # distance from ATH ceiling


class HeuristicSubScorer:
    """Computes all 9 sub-scores from CoinGecko + MarketProcessor data.

    Each score is in [0, 1]. Higher = better, except risk_score where
    higher = lower risk (i.e. safer).
    """

    @classmethod
    def score(cls, data: dict[str, Any]) -> SubScoreResult:
        """Compute all sub-scores from a processed market-data dict.

        Args:
            data: Must contain the standard CoinGecko fields plus
                  MarketProcessor-derived fields (volume_mcap_ratio,
                  price_velocity, ath_distance_pct).

        Returns:
            SubScoreResult with all 9 sub-scores in [0, 1].
        """
        rank = data.get("rank")
        mcap = float(data.get("market_cap_usd", 0.0))
        vol_ratio = float(data.get("volume_mcap_ratio", 0.0))
        velocity = float(data.get("price_velocity", 0.0))
        ath_dist = float(data.get("ath_distance_pct", 0.0))
        supply = data.get("circulating_supply")

        # Derived values used across heuristics
        rank_norm = cls._rank_to_score(rank)
        mcap_norm = cls._mcap_to_score(mcap)
        vol_norm = min_max_normalize(vol_ratio, 0.0, _VOLUME_RATIO_MAX)

        return SubScoreResult(
            technology_score=cls._technology(mcap_norm, rank_norm),
            tokenomics_score=cls._tokenomics(mcap, supply, mcap_norm),
            adoption_score=cls._adoption(rank_norm, vol_norm),
            dev_activity_score=cls._dev_activity(mcap_norm, rank_norm),
            narrative_score=cls._narrative(vol_norm, velocity, ath_dist),
            growth_score=cls._growth(velocity, vol_norm),
            risk_score=cls._risk(rank_norm, mcap_norm, ath_dist, vol_ratio),
            listing_probability=cls._listing(rank_norm, mcap_norm),
            cycle_leader_prob=cls._cycle_leader(rank_norm, vol_norm, velocity),
        )

    # ------------------------------------------------------------------
    # Individual heuristic functions
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_to_score(rank: int | None) -> float:
        """Convert CoinGecko rank to [0, 1]. Rank 1 → 1.0, rank >= 1000 → 0.0."""
        if rank is None or rank <= 0:
            return 0.2  # unknown rank → conservative default
        return clamp(1.0 - (rank - 1) / (_RANK_MAX - 1), 0.0, 1.0)

    @staticmethod
    def _mcap_to_score(mcap: float) -> float:
        """Convert market cap to [0, 1] via log10 scaling."""
        if mcap <= 0:
            return 0.0
        log_mcap = math.log10(max(mcap, 1.0))
        return min_max_normalize(log_mcap, _MCAP_LOG_MIN, _MCAP_LOG_MAX)

    @staticmethod
    def _technology(mcap_norm: float, rank_norm: float) -> float:
        """Heuristic: top-ranked, high-mcap projects tend to have stronger tech.

        Rationale: Without GitHub data, market cap and rank are reasonable
        proxies — projects with real technology sustain high valuations.
        Phases 10+ will replace this with actual dev/GitHub metrics.
        """
        return clamp(0.5 * mcap_norm + 0.5 * rank_norm, 0.0, 1.0)

    @staticmethod
    def _tokenomics(mcap: float, supply: float | None, mcap_norm: float) -> float:
        """Heuristic: reasonable supply + high market cap → decent tokenomics.

        Uses supply-to-mcap ratio as a proxy for token valuation efficiency.
        """
        supply_factor = 0.5  # neutral default
        if supply is not None and supply > 0 and mcap > 0:
            # Price per token as a sanity check; very high or very low is a signal
            price_per_token = mcap / supply
            # Tokens in a "healthy" price range (0.01 to 100k) score higher
            if price_per_token > 0:
                log_price = math.log10(max(price_per_token, 0.001))
                # Map -3..5 range to 0..1 (sweet spot: $0.10 to $10k)
                supply_factor = min_max_normalize(log_price, -3.0, 5.0)

        return clamp(0.5 * mcap_norm + 0.5 * supply_factor, 0.0, 1.0)

    @staticmethod
    def _adoption(rank_norm: float, vol_norm: float) -> float:
        """Heuristic: high rank + high trading activity = strong adoption.

        Rank is the strongest signal (60%) since CoinGecko rank correlates
        with real user adoption; volume ratio (40%) adds trading depth signal.
        """
        return clamp(0.6 * rank_norm + 0.4 * vol_norm, 0.0, 1.0)

    @staticmethod
    def _dev_activity(mcap_norm: float, rank_norm: float) -> float:
        """Heuristic: placeholder until GitHub data is available (Phase 10).

        High-mcap projects tend to have more active dev teams.
        Intentionally conservative — applies a 0.8× discount to avoid
        overstating dev activity without real commit data.
        """
        return clamp(0.8 * (0.5 * mcap_norm + 0.5 * rank_norm), 0.0, 1.0)

    @staticmethod
    def _narrative(vol_norm: float, velocity: float, ath_dist: float) -> float:
        """Heuristic: trending tokens have strong narrative momentum.

        Combines volume surge (hot topic), positive velocity (bullish story),
        and ATH proximity (FOMO narrative).
        """
        vel_norm = min_max_normalize(
            clamp(velocity, -_VELOCITY_MAX, _VELOCITY_MAX),
            -_VELOCITY_MAX,
            _VELOCITY_MAX,
        )
        ath_proximity = 1.0 - min_max_normalize(ath_dist, 0.0, _ATH_DIST_MAX)
        return clamp(0.35 * vol_norm + 0.35 * vel_norm + 0.30 * ath_proximity, 0.0, 1.0)

    @staticmethod
    def _growth(velocity: float, vol_norm: float) -> float:
        """Heuristic: positive momentum + high volume = growth signal.

        Velocity contributes 60% (primary momentum indicator) and
        volume ratio 40% (confirms the move has real volume behind it).
        """
        vel_norm = min_max_normalize(
            clamp(velocity, -_VELOCITY_MAX, _VELOCITY_MAX),
            -_VELOCITY_MAX,
            _VELOCITY_MAX,
        )
        return clamp(0.6 * vel_norm + 0.4 * vol_norm, 0.0, 1.0)

    @staticmethod
    def _risk(
        rank_norm: float,
        mcap_norm: float,
        ath_dist: float,
        vol_ratio: float,
    ) -> float:
        """Heuristic: risk score (higher = safer).

        Large-cap, top-rank, close-to-ATH tokens are less risky.
        Extremely high volume/mcap ratio can indicate manipulation → penalty.
        """
        ath_proximity = 1.0 - min_max_normalize(ath_dist, 0.0, _ATH_DIST_MAX)
        vol_penalty = min_max_normalize(vol_ratio, 0.0, 1.0) * 0.3  # over 100% vol/mcap → risky

        safety = 0.35 * rank_norm + 0.30 * mcap_norm + 0.20 * ath_proximity - vol_penalty
        return clamp(safety + 0.15, 0.0, 1.0)  # +0.15 baseline so most coins aren't 0

    @staticmethod
    def _listing(rank_norm: float, mcap_norm: float) -> float:
        """Heuristic: top-ranked high-mcap tokens already listed everywhere.

        This score represents the probability of being listed on major exchanges.
        Top-10 coins get near 1.0; micro-caps get low scores.
        """
        return clamp(0.6 * rank_norm + 0.4 * mcap_norm, 0.0, 1.0)

    @staticmethod
    def _cycle_leader(rank_norm: float, vol_norm: float, velocity: float) -> float:
        """Heuristic: tokens leading the current market cycle.

        Combines rank prominence, volume activity, and upward momentum.
        Will be replaced by the ML CycleLeaderModel in Phase 11.
        """
        vel_norm = min_max_normalize(
            clamp(velocity, -_VELOCITY_MAX, _VELOCITY_MAX),
            -_VELOCITY_MAX,
            _VELOCITY_MAX,
        )
        return clamp(0.40 * rank_norm + 0.30 * vol_norm + 0.30 * vel_norm, 0.0, 1.0)
