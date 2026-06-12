# Slot Math Engine v3

Production-style Python slot math engine for RTP, volatility, hit frequency, free-spin retriggers, and tuning.

## v3 change

Version 3 fixes the free-spin line-win accounting issue discussed during analysis:

- **Line wins** use `bet_per_line`, including during free spins.
- **Scatter wins** can use `total_bet` and do so by default.
- **Free-spin multiplier** applies according to config. Default is `all_wins`.
- The old accidental behavior `line_win = paytable * total_bet * fs_multiplier` is disabled by default.

This means a 5OAK `A` with `A: {5: 100}`, `bet_per_line = 1`, and `free_spin multiplier = 2` pays:

```text
100 * 1 * 2 = 200
```

not:

```text
100 * 5 * 2 = 1000
```

## Project layout

```text
slot-math-engine-v3/
├── config/
│   └── game_config.yaml
├── src/
│   ├── reels.py
│   ├── paylines.py
│   ├── paytable.py
│   ├── engine.py
│   ├── simulator.py
│   └── analytics.py
├── tools/
│   └── exact_theory.py
├── notebooks/
│   └── analysis.ipynb
├── results/
│   └── reports/
└── README.md
```

## Install

```bash
pip install -r requirements.txt
```

## Run simulation

From the project root:

```bash
python -m src.simulator --config config/game_config.yaml --spins 100000 --seed 123456
```

Save a report:

```bash
python -m src.simulator \
  --config config/game_config.yaml \
  --spins 1000000 \
  --seed 123456 \
  --output results/reports/v3_1m.json
```

## Run exact theory helper

For the default demo strips/paylines/paytable:

```bash
python tools/exact_theory.py
```

For the default v3 config with `m = 2`, `n = 8`, `s = 10`, the theory helper reports approximately:

```text
line_ev                  ~= 4.986859
three_scatter_probability = 0.087890625
free_spin_state_ev_f     ~= 39.516732
round_ev_r               ~= 33.660654
rtp                      ~= 6.732131
```

The simulator's `mean_win_per_spin` should converge toward `round_ev_r` as spin count increases.

## Free-spin accounting config

```yaml
features:
  free_spins:
    multiplier: 2.0
    retrigger: true
    max_free_spins: 20000
    line_win_bet_basis: line_bet
    scatter_win_bet_basis: total_bet
    multiplier_applies_to: all_wins
    use_total_bet_multiplier_bug: false
```

### `line_win_bet_basis`

Use:

```yaml
line_win_bet_basis: line_bet
```

This is the normal production setting for payline games. Line wins are:

```text
paytable multiplier * bet_per_line * free_spin_multiplier
```

The alternative value:

```yaml
line_win_bet_basis: total_bet_for_bug_replay
use_total_bet_multiplier_bug: true
```

exists only to deliberately replay the old bug for comparison. Do not use it for normal math unless the game design intentionally defines line awards as total-bet awards.

### `scatter_win_bet_basis`

Default:

```yaml
scatter_win_bet_basis: total_bet
```

Scatter wins are:

```text
scatter multiplier * total_bet
```

### `multiplier_applies_to`

Default:

```yaml
multiplier_applies_to: all_wins
```

This means free-spin multiplier applies to both line wins and scatter wins.

Use this if scatter cash should not be multiplied:

```yaml
multiplier_applies_to: line_wins_only
```

## Metrics

The simulator reports round-level metrics. Each iteration is one paid base round, not one physical reel spin.

Important fields:

```text
mean_win_per_spin     # alias for mean_win_per_round
rtp
base_rtp
feature_rtp
hit_frequency
variance
standard_deviation
feature_trigger_frequency
average_free_spins_played
average_retriggers_per_round
```

Free spins do not increase `total_bet`. RTP denominator is paid base-spin bet only.
