from __future__ import annotations

import argparse
import json
from pathlib import Path
from random import Random
from typing import Any

import yaml

try:
    from .analytics import build_report
    from .engine import SlotMathEngine
except ImportError:
    from analytics import build_report
    from engine import SlotMathEngine


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_simulation(config: dict[str, Any], spins: int | None = None, seed: int | None = None) -> dict[str, Any]:
    """Run paid rounds.

    The input name is still 'spins' for compatibility with the YAML and CLI, but
    each iteration is now one paid round: one base spin plus any free spins and
    retriggers. RTP denominator is paid base-spin bet only.
    """

    sim_cfg = config.get("simulation", {})
    rounds = int(spins if spins is not None else sim_cfg.get("spins", 100_000))
    seed = int(seed if seed is not None else sim_cfg.get("seed", 1))

    bet_cfg = config.get("bet", {})
    bet_per_line = float(bet_cfg.get("bet_per_line", 1.0))
    active_lines = bet_cfg.get("active_lines")
    active_lines = int(active_lines) if active_lines is not None else None

    engine = SlotMathEngine(config, Random(seed))

    wins: list[float] = []
    bets: list[float] = []
    base_wins: list[float] = []
    feature_wins: list[float] = []
    feature_triggers: list[bool] = []
    free_spins_awarded: list[int] = []
    free_spins_played: list[int] = []
    retriggers: list[int] = []
    capped_rounds: list[bool] = []

    for _ in range(rounds):
        result = engine.play_round(bet_per_line=bet_per_line, active_lines=active_lines)
        wins.append(result.total_win)
        bets.append(result.total_bet)
        base_wins.append(result.base_win)
        feature_wins.append(result.feature_win)
        feature_triggers.append(result.feature_triggered)
        free_spins_awarded.append(result.free_spins_awarded)
        free_spins_played.append(result.free_spins_played)
        retriggers.append(result.retriggers)
        capped_rounds.append(result.capped)

    report = build_report(
        wins=wins,
        bets=bets,
        feature_triggers=feature_triggers,
        base_wins=base_wins,
        feature_wins=feature_wins,
        free_spins_awarded=free_spins_awarded,
        free_spins_played=free_spins_played,
        retriggers=retriggers,
        capped_rounds=capped_rounds,
    ).to_dict()

    report["seed"] = seed
    report["game_id"] = config["game"]["id"]
    report["game_version"] = config["game"]["version"]
    report["free_spins_retrigger_enabled"] = bool(
        config.get("features", {}).get("free_spins", {}).get("retrigger", True)
    )
    report["max_free_spins_per_round"] = int(
        config.get("features", {}).get("free_spins", {}).get("max_free_spins", 200)
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run slot math round simulation")
    parser.add_argument("--config", default="config/game_config.yaml")
    parser.add_argument("--spins", type=int, default=None, help="Paid base rounds to simulate")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    report = run_simulation(config, spins=args.spins, seed=args.seed)

    output = args.output or config.get("simulation", {}).get("report_path")
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
