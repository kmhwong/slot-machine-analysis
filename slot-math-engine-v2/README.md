# Slot Math Engine

A config-driven Python slot math engine for RTP, variance/volatility, hit frequency, free-spin features, retriggers, and simulation-based game tuning.

## Project layout

```text
slot-math-engine/
├── config/
│   └── game_config.yaml
├── src/
│   ├── reels.py
│   ├── paylines.py
│   ├── paytable.py
│   ├── engine.py
│   ├── simulator.py
│   └── analytics.py
├── notebooks/
│   └── analysis.ipynb
├── results/
│   └── reports/
└── README.md
```

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run a simulation

```bash
python -m src.simulator --config config/game_config.yaml --spins 100000 --seed 123456
```

Save the report:

```bash
python -m src.simulator \
  --config config/game_config.yaml \
  --spins 100000 \
  --seed 123456 \
  --output results/reports/simulation_report.json
```

`--spins` means paid base rounds. Each paid round can include a base spin plus any awarded free spins and retriggers.

## Free-spin feature logic

A paid round works as follows:

1. Run one paid base spin.
2. Evaluate line wins and scatter wins.
3. If the configured trigger symbol count awards free spins, add them to the free-spin queue.
4. Run free spins with `charge_bet=False`, so they do not increase the RTP denominator.
5. Apply `features.free_spins.multiplier` to free-spin wins.
6. If `features.free_spins.retrigger` is true, free spins can award more free spins.
7. Stop when the queue is empty or `features.free_spins.max_free_spins` is reached.
8. Apply the round-level `game.max_win_multiplier` cap against the paid base-spin bet.

Example config:

```yaml
features:
  free_spins:
    trigger_symbol: S
    trigger_counts: {3: 8, 4: 0, 5: 0}
    multiplier: 2.0
    retrigger: true
    max_free_spins: 200
```

## Important report fields

The simulator now reports round-level metrics:

- `rtp`: total round win / paid base-spin bet
- `base_rtp`: base-spin win contribution / paid base-spin bet
- `feature_rtp`: free-spin win contribution / paid base-spin bet
- `hit_frequency`: rounds with total win > 0
- `feature_trigger_frequency`: paid rounds that triggered at least one free-spin award
- `average_free_spins_awarded`: initial awards plus retrigger awards per paid round
- `average_free_spins_played`: actually played free spins per paid round
- `retrigger_frequency`: paid rounds with at least one retrigger
- `average_retriggers_per_round`
- `variance`, `standard_deviation`, `coefficient_of_variation`, and win percentiles

## Tuning notes

To reduce RTP, lower line pays, reduce scatter frequency/pay, reduce free-spin multiplier, reduce free-spin awards, or disable retriggers.

To increase volatility, reduce hit frequency and move more EV into rarer, higher-paying outcomes or features.

To reduce volatility, increase small wins and reduce feature/top-pay concentration.
