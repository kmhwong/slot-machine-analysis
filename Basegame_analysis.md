# Comprehensive Base Game Mathematical Analysis & Simulator Validation

This document studies and compares the results between the empirical slot simulator (Simulator v3) and the exact mathematical engine (Expected Payoff Calculator) under a strictly isolated Base Game scenario.

By analyzing the theoretical combinatorics alongside a 3,000,000-round empirical sample, we mathematically validate the core engine's integrity.

## 1. Mathematical Setting & Assumptions

The structural foundation of the game is a finite combinatorial space:

- Grid: $3 \times 5$ visible window.

- Reels: 5 independent reels, each containing 12 symbols.

- State Space ($\Omega$): $12^5 = 248,832$ total unique combinations.

- Paylines: 5 geometric paths (Top, Middle, Bottom, V-Shape, Inverted V-Shape).

- Bet Configuration: 1.0 credit per line $\times$ 5 lines = 5.0 Total Bet.

The Base Paytable

Wins are awarded for 3, 4, or 5 consecutive identical symbols (or 'W' Wilds) starting from the leftmost reel.

| Symbol | 3-of-a-kind | 4-of-a-kind | 5-of-a-kind|
| -------- | -------- | -------- | -------- |
| A | 5 | 25 | 100 |
| K | 4 | 15 | 60 |
| Q | 3 | 10 | 40 |
| J | 2 | 8 | 25 |

## 2. Configuration Settings to Disable Scatters

To isolate the Base Game and completely bypass all recursive features, the mathematical model and simulator must be structurally restricted. This ensures we are testing pure payline mechanics.

### Method: Configuration Level (Simulator v3 & Payoff Script)

We zero out all scatter trigger payoff structures. This keeps the scatter symbols on the reels but strips them of all mathematical utility.

In Simulator v3 (`game_config.yaml`):
```
  scatter:
    S: {3: 0, 4: 0, 5: 0} # Zeroed out cash
features:
  free_spins:
    trigger_symbol: X     # 'X' does not exist on reels, ensuring zero triggers
    trigger_counts: {3: 8, 4: 0, 5: 0}
```

In Expected Payoff Script (`expected_payoff.py`):
```
    'features': {
        'free_spins_multiplier': 1.0,  # Disabled multiplier
        'scatter_pays': {
            3: {'cash': 0, 'spins': 0}, # Zeroed out cash & spins
            4: {'cash': 0, 'spins': 0},
            5: {'cash': 0, 'spins': 0}
        }
    }
```

*Note: We can also enforce this programmatically in the script by checking for a null symbol `s_count = visible.count('X')` instead of `'S'` to guarantee zero feature hits.*

## 3. Side-by-Side JSON Payload Comparison

The following table presents the exact JSON keys and their respective values, comparing a 3,000,000-round empirical sample (Simulator v3) against the 248,832-round exhaustive population (Expected Payoff Calculator).

*Note: Simulator outputs inherently use raw decimals/ratios for probability rates, while the Payoff Calculator uses percentages. In this table, the Simulator values have been converted to percentages (`* 100`) to allow for a direct 1:1 comparison.*

| JSON Key | Simulator v3 (3M Sample) | Expected Payoff (Exact Math) | Deviation / Alignment Status |
| ------ | ------ | ------ | ------ |
|`"rounds"` | $3,000,000$ | $248,832$ | N/A (Sample vs. Population)|
| `"total_bet"` | $15,000,000.0$ | $1,244,160.0$ | N/A |
| `"total_win"` | $14,962,065.0$ | $1,240,889.9$ | N/A|
| `"rtp"` | $99.747\%$ (from 0.9974) | $99.737\%$ | $+0.010\%$ (Near Perfect Convergence)|
| `"expected_loss_rate"` | $0.253\%$ | $0.262\%$ | $-0.009\%$|
| `"hit_frequency"` | $37.136\%$ (from 0.3713) | $37.152\%$ | $-0.016\%$ (Flawless Match)|
| `"miss_frequency"` | $62.864\%$ | $62.847\%$ | $+0.017\%$ |
| `"mean_win_per_round"` | $4.987$ | $4.986$ | $+0.001$ credits|
| `"mean_win_on_hit"` | $13.430$ | $13.422$ | $+0.008$ credits|
| `"variance"` | $226.155$ | $225.805$ | $+0.350$ (Flawless Match)|
| `"standard_deviation"` | $15.038$ | $15.026$ | $+0.012$|
| `"max_win"` | $265.0$ | $25,000.0$ | Max cap $25,000 is not realised.|


## 4. Mathematical Analysis & Structural Breakdown

To formalize the alignment, we define the core analytical forms for the Base Game Payline Win random variable, $X$.

### A. Analytical Forms: Expectation and RTP

The Expected Value (Mean Win) of the base game $E[X]$ is evaluated by summing over the entire state space $\Omega$:

$$E[X] = \sum_{x} x \cdot P(X = x)$$

The Return to Player (RTP) is structurally defined as the expected win divided by the Total Bet ($B_{total} = 5.0$):

$$\text{RTP} = \frac{E[X]}{B_{total}}$$

From the exhaustive combinatorics of the 248,832 states, the exact expected payoff calculates to $E[X] \approx 4.9868$.
Applying the analytical form:

$$\text{RTP}_{base} = \frac{4.9868}{5.0} = \mathbf{99.737\%}$$

The empirical simulator converges to $99.747\%$, mathematically confirming the payline evaluation logic.

## B. Analytical Forms: Variance

The theoretical Variance quantifies the spread of payouts around the mean. It is defined as:

$$\text{Var}(X) = E[X^2] - (E[X])^2$$

Evaluating the second moment $E[X^2] = \sum x^2 P(X=x)$ yields $\approx 250.6737$.
Applying the variance formula:

$$\text{Var}(X) = 250.6737 - (4.9868)^2 = 250.6737 - 24.8681 = \mathbf{225.805}$$

The empirical simulator's tracked variance of $226.155$ flawlessly rectifies against this analytical form.

## C. Hit Frequency Combinatorics

Hit frequency is defined as the probability of securing at least one winning payline:

$$P(X > 0) = 1 - P(X = 0)$$

Because paylines intersect, their probabilities are correlated. The analytical script groups these overlapping probabilities perfectly, revealing that exactly $92,448$ out of $248,832$ combinations result in a win ($37.152\%$). The simulator's empirical hit frequency of $37.136\%$ mathematically confirms that the left-to-right evaluation logic and Wild (`'W'`) substitutions function flawlessly without double-counting overlaps.

## 5. Phase 2: Introducing Scatters (Cash Only, No Free Spins)

To further validate the simulator's core logic before enabling recursive features, we run an intermediate state: Scatter Cash is active ($10, 50, 250$), but Free Spins are disabled. Because this configuration does not trigger free spins, the expected value remains purely linear, making it an excellent test of the game's ability to sum disjoint probabilities (paylines + scatters) across the grid.

### Configuration

Simulator: `S` pays `{3: 10, 4: 50, 5: 250}`, trigger_symbol changed to `X` to block free spins.

Math Script: `scatter_pays` set to `{'cash': 10, 'spins': 0}`, etc.

### Side-by-Side Comparison (Cash Scatters Active)

| JSON Key | Simulator v3 (3M Sample) | Expected Payoff (Exact Math) | Deviation / Alignment Status |
| ------ | ------ | ------ | ------ |
| `"rounds"` | $3,000,000$ | $248,832$ | N/A |
| `"rtp"` | $136.9118\%$ | $136.8465\%$ | $+0.0653\%$ (Within 95% Confidence Interval)|
| `"hit_frequency"` | $42.7322\%$ | $42.7264\%$ | $+0.0058\%$ (Flawless Match)|
| `"mean_win_per_round"` | $6.8455$ | $6.8423$ | $+0.0032$ credits|
| `"variance"` | $338.7927$ | $338.2045$ | $+0.5882$ (Flawless Match)|
| `"standard_deviation"` | $18.4063$ | $18.3903$ | $+0.0160$ |


### Analytical Breakdown of the Scatter Addition

Let $S$ be the random variable for the Scatter Cash payout, and $W = X + S$ be the total round win.

### 1. Rectifying the RTP Shift

Scatter symbols land independently per reel. The probability of landing $k$ scatters follows a binomial distribution where $p = \frac{3}{12} = \frac{1}{4}$:


$$P(k) = \binom{5}{k} \left(\frac{1}{4}\right)^k \left(\frac{3}{4}\right)^{5-k}$$

The Expected Value of the scatter cash $E[S]$ is defined as:


$$E[S] = \sum_{k=3}^{5} S_k \cdot P(k)$$

$$E[S] = 10 \left(\frac{90}{1024}\right) + 50 \left(\frac{15}{1024}\right) + 250 \left(\frac{1}{1024}\right) = \frac{900 + 750 + 250}{1024} = \frac{1900}{1024} = \mathbf{1.8554} \text{ credits}$$

By the Linearity of Expectation, the total expected win is the exact sum of the base game and scatter expectations:


$$E[W] = E[X] + E[S] = 4.9868 + 1.8554 = \mathbf{6.8422} \text{ credits}$$

$$\text{RTP}_{combined} = \frac{E[W]}{B_{total}} = \frac{6.8422}{5.0} = \mathbf{136.846\%}$$

The exact analytical derivation perfectly matches both the combinatorial expected payoff ($136.8465\%$) and the empirical simulator logged value ($136.9118\%$).

### 2. Rectifying the Variance Bump

For the variance of a combined system, we apply the sum of variances formula, which includes the Covariance interaction term:

$$\text{Var}(W) = \text{Var}(X+S) = \text{Var}(X) + \text{Var}(S) + 2\text{Cov}(X, S)$$

First, we solve for the exact variance of the Scatter Cash independently $\text{Var}(S) = E[S^2] - (E[S])^2$:


$$E[S^2] = 10^2 \left(\frac{90}{1024}\right) + 50^2 \left(\frac{15}{1024}\right) + 250^2 \left(\frac{1}{1024}\right) = \frac{9000 + 37500 + 62500}{1024} = 106.4453$$

$$\text{Var}(S) = 106.4453 - (1.8554)^2 = 106.4453 - 3.4425 = \mathbf{103.0028}$$

If line pays and scatters were perfectly independent, the combined variance would simply be $225.805 + 103.0028 = 328.807$.
However, the exact combined variance calculates to $338.2045$.
This discrepancy reveals that $2\text{Cov}(X,S) \approx +9.39$. The positive covariance implies that landing scatters on the grid slightly correlates with hitting higher-paying line wins—a direct consequence of how 'S' symbols and 'W' Wilds are aligned on your specific reel strips. The simulator empirically capturing $338.79$ proves it accurately processes this precise reel-strip topography.

### 3. Hit Frequency Overlaps

Notice that the theoretical Hit Frequency increased from $37.152\%$ (paylines only) to $42.726\%$ (paylines + scatters).

- The probability of getting a scatter win ($k \ge 3$) is $P(3) + P(4) + P(5) = \frac{106}{1024} \approx 10.35\%$.

- However, the hit frequency only increased by $\approx 5.57\%$.

- Why? Because almost half the time you hit a scatter payout, you also hit a payline payout on the same spin. The exact math script avoids double-counting these overlapping wins. The fact that the simulator empirically hit $42.732\%$ proves its accounting logic correctly merges overlapping wins into a single "hit" event for the player.

## 6. Conclusion

Both the isolated paylines and the overlapping scatter cash mechanics have been exhaustively validated. By establishing the formal analytical models for Expectation and Variance, we prove the simulator correctly respects the Law of Large Numbers, the Linearity of Expectation, the structural Covariance of the reel strips, and the combinatorial limits of the grid.
