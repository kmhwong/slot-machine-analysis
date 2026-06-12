game:
  id: demo_5x3_slot
  version: 3.0.0
  rows: 3
  mode: paylines        # paylines or ways
  max_win_multiplier: 5000

bet:
  bet_per_line: 1.0
  active_lines: 5

symbols:
  A:
    type: regular
  K:
    type: regular
  Q:
    type: regular
  J:
    type: regular
  W:
    type: wild
    substitutes_for: all
  S:
    type: scatter

reels:
  - [A, K, Q, J, W, S, A, K, Q, J, A, K]
  - [K, Q, J, A, W, S, K, Q, J, A, K, Q]
  - [Q, J, A, K, W, S, Q, J, A, K, Q, J]
  - [J, A, K, Q, W, S, J, A, K, Q, J, A]
  - [A, K, Q, J, W, S, A, K, Q, J, A, K]

paylines:
  - [1, 1, 1, 1, 1]
  - [0, 0, 0, 0, 0]
  - [2, 2, 2, 2, 2]
  - [0, 1, 2, 1, 0]
  - [2, 1, 0, 1, 2]

paytable:
  line:
    A: {3: 5, 4: 25, 5: 100}
    K: {3: 4, 4: 15, 5: 60}
    Q: {3: 3, 4: 10, 5: 40}
    J: {3: 2, 4: 8, 5: 25}
  scatter:
    S: {3: 2, 4: 0, 5: 0}

features:
  free_spins:
    trigger_symbol: S
    trigger_counts: {3: 8, 4: 0, 5: 0}
    multiplier: 2.0
    retrigger: true
    max_free_spins: 20000

    # v3 accounting rule:
    # Line pays are always based on bet_per_line, even in free spins.
    # This avoids the old accidental x10 behavior: paytable x total_bet x fs_multiplier.
    line_win_bet_basis: line_bet        # allowed: line_bet, total_bet_for_bug_replay
    scatter_win_bet_basis: total_bet    # allowed: total_bet, line_bet
    multiplier_applies_to: all_wins     # allowed: all_wins, line_wins_only
    use_total_bet_multiplier_bug: false # true only to deliberately replay the old bug

simulation:
  seed: 123456
  spins: 100000
  report_path: results/reports/simulation_report.json
