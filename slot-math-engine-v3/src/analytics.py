from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import NormalDist
from typing import Iterable


@dataclass(frozen=True)
class AnalyticsReport:
    rounds: int
    total_bet: float
    total_win: float
    rtp: float
    expected_loss_rate: float
    hit_frequency: float
    miss_frequency: float
    mean_win_per_round: float
    mean_win_on_hit: float
    variance: float
    standard_deviation: float
    coefficient_of_variation: float
    max_win: float
    p50_win: float
    p90_win: float
    p95_win: float
    p99_win: float
    base_win: float
    feature_win: float
    base_rtp: float
    feature_rtp: float
    feature_trigger_frequency: float
    average_free_spins_awarded: float
    average_free_spins_played: float
    retrigger_frequency: float
    average_retriggers_per_round: float
    capped_round_frequency: float
    standard_error_rtp: float
    rtp_confidence_95_low: float
    rtp_confidence_95_high: float

    def to_dict(self) -> dict[str, float | int]:
        data = asdict(self)
        # Backward-compatible aliases for older notebooks/reports.
        data["spins"] = self.rounds
        data["mean_win_per_spin"] = self.mean_win_per_round
        return data


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if q <= 0:
        return sorted_values[0]
    if q >= 1:
        return sorted_values[-1]
    idx = q * (len(sorted_values) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_values) - 1)
    weight = idx - lo
    return sorted_values[lo] * (1 - weight) + sorted_values[hi] * weight


def build_report(
    wins: Iterable[float],
    bets: Iterable[float],
    feature_triggers: Iterable[bool],
    *,
    base_wins: Iterable[float] | None = None,
    feature_wins: Iterable[float] | None = None,
    free_spins_awarded: Iterable[int] | None = None,
    free_spins_played: Iterable[int] | None = None,
    retriggers: Iterable[int] | None = None,
    capped_rounds: Iterable[bool] | None = None,
) -> AnalyticsReport:
    win_values = list(wins)
    bet_values = list(bets)
    trigger_values = list(feature_triggers)
    rounds = len(win_values)
    if rounds == 0:
        raise ValueError("cannot analyse zero rounds")
    if len(bet_values) != rounds or len(trigger_values) != rounds:
        raise ValueError("wins, bets, and feature_triggers must have equal length")

    base_win_values = list(base_wins) if base_wins is not None else [0.0] * rounds
    feature_win_values = list(feature_wins) if feature_wins is not None else [0.0] * rounds
    awarded_values = list(free_spins_awarded) if free_spins_awarded is not None else [0] * rounds
    played_values = list(free_spins_played) if free_spins_played is not None else [0] * rounds
    retrigger_values = list(retriggers) if retriggers is not None else [0] * rounds
    capped_values = list(capped_rounds) if capped_rounds is not None else [False] * rounds

    for name, values in {
        "base_wins": base_win_values,
        "feature_wins": feature_win_values,
        "free_spins_awarded": awarded_values,
        "free_spins_played": played_values,
        "retriggers": retrigger_values,
        "capped_rounds": capped_values,
    }.items():
        if len(values) != rounds:
            raise ValueError(f"{name} must have the same length as wins")

    total_bet = sum(bet_values)
    total_win = sum(win_values)
    total_base_win = sum(base_win_values)
    total_feature_win = sum(feature_win_values)

    rtp = total_win / total_bet if total_bet else 0.0
    base_rtp = total_base_win / total_bet if total_bet else 0.0
    feature_rtp = total_feature_win / total_bet if total_bet else 0.0
    mean_win = total_win / rounds
    hits = sum(1 for w in win_values if w > 0)
    hit_frequency = hits / rounds
    variance = sum((w - mean_win) ** 2 for w in win_values) / rounds
    sd = sqrt(variance)
    avg_bet = total_bet / rounds
    se_rtp = (sd / sqrt(rounds)) / avg_bet if avg_bet else 0.0
    z = NormalDist().inv_cdf(0.975)
    sorted_wins = sorted(win_values)

    return AnalyticsReport(
        rounds=rounds,
        total_bet=total_bet,
        total_win=total_win,
        rtp=rtp,
        expected_loss_rate=1.0 - rtp,
        hit_frequency=hit_frequency,
        miss_frequency=1.0 - hit_frequency,
        mean_win_per_round=mean_win,
        mean_win_on_hit=total_win / hits if hits else 0.0,
        variance=variance,
        standard_deviation=sd,
        coefficient_of_variation=sd / mean_win if mean_win else 0.0,
        max_win=max(win_values),
        p50_win=percentile(sorted_wins, 0.50),
        p90_win=percentile(sorted_wins, 0.90),
        p95_win=percentile(sorted_wins, 0.95),
        p99_win=percentile(sorted_wins, 0.99),
        base_win=total_base_win,
        feature_win=total_feature_win,
        base_rtp=base_rtp,
        feature_rtp=feature_rtp,
        feature_trigger_frequency=sum(1 for t in trigger_values if t) / rounds,
        average_free_spins_awarded=sum(awarded_values) / rounds,
        average_free_spins_played=sum(played_values) / rounds,
        retrigger_frequency=sum(1 for r in retrigger_values if r > 0) / rounds,
        average_retriggers_per_round=sum(retrigger_values) / rounds,
        capped_round_frequency=sum(1 for c in capped_values if c) / rounds,
        standard_error_rtp=se_rtp,
        rtp_confidence_95_low=rtp - z * se_rtp,
        rtp_confidence_95_high=rtp + z * se_rtp,
    )
