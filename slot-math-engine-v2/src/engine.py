from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from random import Random
from typing import Any

try:
    from .paylines import PaylineSet
    from .paytable import Paytable
    from .reels import Grid, ReelSet, ReelStop
except ImportError:  # Allows python src/engine.py-style execution during local experiments.
    from paylines import PaylineSet
    from paytable import Paytable
    from reels import Grid, ReelSet, ReelStop


@dataclass(frozen=True)
class WinEvent:
    type: str
    symbol: str
    count: int
    multiplier: float
    win: float
    line_index: int | None = None
    positions: list[tuple[int, int]] | None = None


@dataclass(frozen=True)
class FeatureEvent:
    type: str
    symbol: str
    count: int
    value: int | float


@dataclass(frozen=True)
class SpinResult:
    """One visible grid evaluation.

    total_bet is the amount charged for this spin. Base spins charge the player;
    free spins normally have total_bet = 0 but still evaluate wins using the
    original bet_per_line and active line count.
    """

    mode: str
    total_bet: float
    total_win: float
    grid: Grid
    stops: list[ReelStop]
    wins: list[WinEvent]
    features: list[FeatureEvent]
    capped: bool
    win_multiplier: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "total_bet": self.total_bet,
            "total_win": self.total_win,
            "grid": self.grid,
            "stops": [asdict(stop) for stop in self.stops],
            "wins": [asdict(win) for win in self.wins],
            "features": [asdict(feature) for feature in self.features],
            "capped": self.capped,
            "win_multiplier": self.win_multiplier,
        }


@dataclass(frozen=True)
class RoundResult:
    """One paid round: one base spin plus any awarded free spins."""

    total_bet: float
    total_win: float
    base_win: float
    feature_win: float
    base_spin: SpinResult
    free_spins: list[SpinResult]
    free_spins_awarded: int
    free_spins_played: int
    retriggers: int
    feature_triggered: bool
    capped: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_bet": self.total_bet,
            "total_win": self.total_win,
            "base_win": self.base_win,
            "feature_win": self.feature_win,
            "base_spin": self.base_spin.to_dict(),
            "free_spins": [spin.to_dict() for spin in self.free_spins],
            "free_spins_awarded": self.free_spins_awarded,
            "free_spins_played": self.free_spins_played,
            "retriggers": self.retriggers,
            "feature_triggered": self.feature_triggered,
            "capped": self.capped,
        }


class SlotMathEngine:
    def __init__(self, config: dict[str, Any], rng: Random | None = None) -> None:
        self.config = config
        game = config["game"]
        self.rows = int(game["rows"])
        self.mode = game.get("mode", "paylines")
        self.max_win_multiplier = float(game.get("max_win_multiplier", "inf"))

        self.symbols = Paytable.build_symbols(config["symbols"])
        self.reels = ReelSet(config["reels"], self.rows)
        self.paytable = Paytable(config["paytable"], self.symbols)
        self.paylines = None
        if self.mode == "paylines":
            self.paylines = PaylineSet(config["paylines"], self.rows, self.reels.reel_count)
        elif self.mode != "ways":
            raise ValueError("game.mode must be 'paylines' or 'ways'")
        self.rng = rng or Random()

    def spin(
        self,
        bet_per_line: float,
        active_lines: int | None = None,
        *,
        mode: str = "base",
        charge_bet: bool = True,
        win_multiplier: float = 1.0,
        evaluate_features: bool = True,
        apply_cap: bool = True,
    ) -> SpinResult:
        """Evaluate one spin.

        charge_bet controls the accounting denominator. Free spins should set
        charge_bet=False, but wins are still evaluated using the same bet_per_line
        and active line count as the triggering base spin.
        """

        if bet_per_line <= 0:
            raise ValueError("bet_per_line must be positive")

        if self.mode == "paylines":
            assert self.paylines is not None
            active_paylines = self.paylines.active(active_lines)
            wagering_total_bet = bet_per_line * len(active_paylines)
        else:
            active_paylines = []
            wagering_total_bet = bet_per_line

        charged_bet = wagering_total_bet if charge_bet else 0.0

        stops, grid = self.reels.spin(self.rng)
        wins: list[WinEvent] = []

        if self.mode == "paylines":
            wins.extend(self._evaluate_lines(grid, active_paylines, bet_per_line))
        else:
            wins.extend(self._evaluate_ways(grid, bet_per_line))

        wins.extend(self._evaluate_scatters(grid, wagering_total_bet))
        features = self._evaluate_features(grid) if evaluate_features else []

        raw_win_before_multiplier = sum(w.win for w in wins)
        raw_win = raw_win_before_multiplier * win_multiplier
        if win_multiplier != 1.0:
            wins = [replace(w, win=w.win * win_multiplier, multiplier=w.multiplier * win_multiplier) for w in wins]

        if apply_cap:
            max_win = wagering_total_bet * self.max_win_multiplier
            total_win = min(raw_win, max_win)
            capped = total_win < raw_win
        else:
            total_win = raw_win
            capped = False

        return SpinResult(
            mode=mode,
            total_bet=charged_bet,
            total_win=total_win,
            grid=grid,
            stops=stops,
            wins=wins,
            features=features,
            capped=capped,
            win_multiplier=win_multiplier,
        )

    def play_round(self, bet_per_line: float, active_lines: int | None = None) -> RoundResult:
        """Play one paid round with free spins and retriggers.

        A round charges only the base spin bet. Free spins are not added to
        total_bet. Free spins can retrigger when the config sets retrigger: true.
        The round-level max win cap is applied after base and feature wins.
        """

        free_cfg = self.config.get("features", {}).get("free_spins", {}) or {}
        free_multiplier = float(free_cfg.get("multiplier", 1.0))
        retrigger_enabled = bool(free_cfg.get("retrigger", True))
        max_free_spins = int(free_cfg.get("max_free_spins", 200))

        base_spin = self.spin(
            bet_per_line=bet_per_line,
            active_lines=active_lines,
            mode="base",
            charge_bet=True,
            win_multiplier=1.0,
            evaluate_features=True,
            apply_cap=False,
        )

        total_bet = base_spin.total_bet
        total_win_uncapped = base_spin.total_win
        free_spins_remaining = self._free_spins_awarded(base_spin.features)
        free_spins_awarded = free_spins_remaining
        retriggers = 0
        free_spins: list[SpinResult] = []

        while free_spins_remaining > 0 and len(free_spins) < max_free_spins:
            free_spins_remaining -= 1
            free_spin = self.spin(
                bet_per_line=bet_per_line,
                active_lines=active_lines,
                mode="free",
                charge_bet=False,
                win_multiplier=free_multiplier,
                evaluate_features=True,
                apply_cap=False,
            )
            free_spins.append(free_spin)
            total_win_uncapped += free_spin.total_win

            if retrigger_enabled:
                awarded = self._free_spins_awarded(free_spin.features)
                if awarded > 0:
                    retriggers += 1
                    free_spins_remaining += awarded
                    free_spins_awarded += awarded

        max_round_win = total_bet * self.max_win_multiplier
        total_win = min(total_win_uncapped, max_round_win)
        capped = total_win < total_win_uncapped

        # If a cap is hit, keep the accounting simple: feature_win is the residual
        # after base_win up to the capped total.
        base_win = min(base_spin.total_win, total_win)
        feature_win = max(0.0, total_win - base_win)

        return RoundResult(
            total_bet=total_bet,
            total_win=total_win,
            base_win=base_win,
            feature_win=feature_win,
            base_spin=base_spin,
            free_spins=free_spins,
            free_spins_awarded=free_spins_awarded,
            free_spins_played=len(free_spins),
            retriggers=retriggers,
            feature_triggered=free_spins_awarded > 0,
            capped=capped,
        )

    @staticmethod
    def _free_spins_awarded(features: list[FeatureEvent]) -> int:
        total = 0
        for feature in features:
            if feature.type == "free_spins_awarded":
                total += int(feature.value)
        return total

    def _evaluate_lines(self, grid: Grid, paylines: list[list[int]], bet_per_line: float) -> list[WinEvent]:
        wins: list[WinEvent] = []
        for line_index, line in enumerate(paylines):
            line_symbols = [grid[reel][row] for reel, row in enumerate(line)]
            best = self._best_line_win(line_symbols)
            if best:
                symbol, count, multiplier = best
                wins.append(
                    WinEvent(
                        type="line",
                        symbol=symbol,
                        count=count,
                        multiplier=multiplier,
                        win=multiplier * bet_per_line,
                        line_index=line_index,
                        positions=[(reel, line[reel]) for reel in range(count)],
                    )
                )
        return wins

    def _best_line_win(self, line_symbols: list[str]) -> tuple[str, int, float] | None:
        best: tuple[str, int, float] | None = None
        for symbol in self.paytable.line.keys():
            count = 0
            for actual in line_symbols:
                if not self.paytable.matches(actual, symbol):
                    break
                count += 1
            multiplier = self.paytable.line_multiplier(symbol, count)
            if multiplier > 0 and (best is None or multiplier > best[2]):
                best = (symbol, count, multiplier)
        return best

    def _evaluate_ways(self, grid: Grid, bet_unit: float) -> list[WinEvent]:
        wins: list[WinEvent] = []
        for symbol, pays in self.paytable.line.items():
            matching_rows_by_reel: list[list[int]] = []
            for reel, visible in enumerate(grid):
                rows = [row for row, actual in enumerate(visible) if self.paytable.matches(actual, symbol)]
                if not rows:
                    break
                matching_rows_by_reel.append(rows)
            count = len(matching_rows_by_reel)
            multiplier = pays.get(count, 0.0)
            if multiplier > 0:
                ways = 1
                positions: list[tuple[int, int]] = []
                for reel, rows in enumerate(matching_rows_by_reel):
                    ways *= len(rows)
                    positions.extend((reel, row) for row in rows)
                wins.append(
                    WinEvent(
                        type="ways",
                        symbol=symbol,
                        count=count,
                        multiplier=multiplier,
                        win=multiplier * ways * bet_unit,
                        positions=positions,
                    )
                )
        return wins

    def _evaluate_scatters(self, grid: Grid, total_bet: float) -> list[WinEvent]:
        wins: list[WinEvent] = []
        for symbol, pays in self.paytable.scatter.items():
            positions = [
                (reel, row)
                for reel, visible in enumerate(grid)
                for row, actual in enumerate(visible)
                if actual == symbol
            ]
            count = len(positions)
            multiplier = pays.get(count, 0.0)
            if multiplier > 0:
                wins.append(
                    WinEvent(
                        type="scatter",
                        symbol=symbol,
                        count=count,
                        multiplier=multiplier,
                        win=multiplier * total_bet,
                        positions=positions,
                    )
                )
        return wins

    def _evaluate_features(self, grid: Grid) -> list[FeatureEvent]:
        free_spins = self.config.get("features", {}).get("free_spins")
        if not free_spins:
            return []
        symbol = free_spins["trigger_symbol"]
        count = sum(1 for visible in grid for actual in visible if actual == symbol)
        awarded = {int(k): int(v) for k, v in free_spins.get("trigger_counts", {}).items()}.get(count, 0)
        if awarded <= 0:
            return []
        return [FeatureEvent(type="free_spins_awarded", symbol=symbol, count=count, value=awarded)]
