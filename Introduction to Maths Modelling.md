# Mathematical Framework: Slot Machine Probability Space & Random Variables

To establish a rigorous mathematical framework for a $3 \times 5$ slot machine, we must define the probability space starting from the mechanical reels up to the final payout evaluations. 
Here is the formal definition of the sample space and the random variables governing the game.

## 1. The Fundamental Random Variables (The Reel Stops)
The entire state of the slot machine is determined by exactly one mechanical event: the stopping position of each of the 5 reels. Let $L_c$ be the ordered list of 12 symbols on reel $c$, where $c \in \{0, 1, 2, 3, 4\}$. Let $Y_c$ be the random variable representing the index of the symbol on reel $c$ that lands on the top row of the grid. Since each reel stops randomly and independently, $Y_c$ follows a Discrete Uniform Distribution: 

$$Y_c \sim \text{Uniform}(0, 11)$$

$$P(Y_c = y) = \frac{1}{12} \quad \text{for } y \in \{0, 1, \dots, 11\}$$

### Python Implementation:
```
# The deterministic lists representing L_c

reels = [
    ['A', 'K', 'Q', 'J', 'W', 'S', 'A', 'K', 'Q', 'J', 'A', 'K'],
    ['K', 'Q', 'J', 'A', 'W', 'S', 'K', 'Q', 'J', 'A', 'K', 'Q'],
    ['Q', 'J', 'A', 'K', 'W', 'S', 'Q', 'J', 'A', 'K', 'Q', 'J'],
    ['J', 'A', 'K', 'Q', 'W', 'S', 'J', 'A', 'K', 'Q', 'J', 'A'],
    ['A', 'K', 'Q', 'J', 'W', 'S', 'A', 'K', 'Q', 'J', 'A', 'K']
]
```

## 2. The Sample Space ($\Omega$)
The sample space $\Omega$ consists of every possible combination of the 5 reel stops. An individual outcome $\omega \in \Omega$ is a 5-tuple representing the stops of the 5 reels: 

$$\omega = (y_0, y_1, y_2, y_3, y_4)$$

Because the reels are independent, the size of the sample space is the product of their lengths: 

$$|\Omega| = 12 \times 12 \times 12 \times 12 \times 12 = 12^5 = \mathbf{248,832}$$

Under a fair RNG, every outcome is equally likely. Thus, the probability measure for any specific stop combination $\omega$ is: 

$$P(\omega) = \frac{1}{248,832}$$

### Python Implementation:

```
total_combinations = 12 ** 5  # 248,832

# Exhaustive evaluation of the sample space
for st0 in reel_stops[0]:
    for st1 in reel_stops[1]:
        for st2 in reel_stops[2]:
            for st3 in reel_stops[3]:
                for st4 in reel_stops[4]:
                    # Each nested iteration represents one unique outcome ω in Ω
                    pass
```

## 3. The Grid (Derived Matrix State)
Once the reels stop, they populate a $3 \times 5$ visible grid. We define this grid as a random matrix $M(\omega)$ with rows $r \in \{0, 1, 2\}$ and columns $c \in \{0, 1, 2, 3, 4\}$. 

The symbol in any specific cell of the grid is determined by adding the row index to the reel's stopping position (wrapping around modulo 12): 

$$M_{r,c} = L_c[\ (Y_c + r) \pmod{12} \]$$

### Python Implementation:
```
reel_stops = []
for c in range(5):
    strip = reels[c]
    stops = []
    for idx in range(len(strip)):
        # M_{r,c} mapping using modulo arithmetic to wrap around the 12-symbol strip
        visible = [strip[(idx + r) % len(strip)] for r in range(3)]
        
        # Pre-computing line symbols and scatter counts for speed
        s_count = visible.count('S')
        line_syms = tuple(visible[paylines[l][c]] for l in range(active_lines))
        stops.append((s_count, line_syms))
        
    reel_stops.append(stops)
```

## 4. The Payline Random Variables
A payline is a predetermined geometric path across the matrix $M$. Let $\pi_k$ be the $k$-th payline, defined as a vector of row indices for each column: $\pi_k = [r_0, r_1, r_2, r_3, r_4]$.

For example, a "V-shape" payline is defined as $\pi_4 = [0, 1, 2, 1, 0]$. 

We define $V_k$ as the random vector of 5 symbols that land on payline $k$: 

$$V_k = \Big( M_{\pi_k[0], 0},\; M_{\pi_k[1], 1},\; M_{\pi_k[2], 2},\; M_{\pi_k[3], 3},\; M_{\pi_k[4], 4} \Big)$$

### Python Implementation:
```
# Geometric definitions of π_k
paylines = [
    [1, 1, 1, 1, 1], # Line 1
    [0, 0, 0, 0, 0], # Line 2
    [2, 2, 2, 2, 2], # Line 3
    [0, 1, 2, 1, 0], # Line 4 (V-Shape)
    [2, 1, 0, 1, 2]  # Line 5 (Inverted V)
]

# Extracting the random vector V_k for a specific payline during evaluation
for l_idx in range(active_lines):
    syms = (st0[1][l_idx], st1[1][l_idx], st2[1][l_idx], st3[1][l_idx], st4[1][l_idx])
```

## 5. The Reward Random Variables
Let the function $f(V_k)$ represent the paytable evaluation logic (checking for 3, 4, or 5 consecutive matching symbols from left to right, factoring in 'W' wilds).

We define $X_k$ as the **Random Variable for the Payout of Payline $k$**: 

$$X_k = f(V_k)$$ 

The **Total Base Win Random Variable ($W_{base}$)** is the sum of the payouts across all 5 active paylines: 

$$W_{base} = \sum_{k=1}^{5} X_k$$ 

*(Note: By the Linearity of Expectation, the expected value of the base spin is simply $E[W_{base}] = \sum E[X_k]$, which is why analytical scripts calculate the expected win by summing individual line averages.)*

### Python Implementation:
```
def evaluate_line_consec(line_symbols, paytable):
    """ Evaluates f(V_k) for left-to-right consecutive symbols """
    max_payout = 0.0
    for target in ['A', 'K', 'Q', 'J']:
        count = 0
        for sym in line_symbols:
            if sym == target or sym == 'W':
                count += 1
            else:
                break
        if count >= 3:
            payout = paytable.get(target, {}).get(count, 0.0)
            if payout > max_payout:
                max_payout = payout
    return max_payout

# Calculating W_base across all active paylines
base_win = 0.0
for l_idx in range(active_lines):
    syms = (st0[1][l_idx], st1[1][l_idx], st2[1][l_idx], st3[1][l_idx], st4[1][l_idx])
    
    # Memoization applied to speed up f(V_k)
    if syms not in PAYOUT_CACHE:
        PAYOUT_CACHE[syms] = evaluate_line_consec(syms, paytable_line)
    base_win += PAYOUT_CACHE[syms]
```

## 6. The Scatter Random Variable
Scatters do not follow paylines; they are counted across the entire matrix $M$. We define an indicator variable $I$ that equals $1$ if a cell contains a scatter ('S') and $0$ otherwise.

The **Total Scatter Count Random Variable ($C_S$)** is:

$$C_S = \sum_{c=0}^{4} \sum_{r=0}^{2} I(M_{r,c} == \text{'S'})$$ 

The payout for scatters (both cash $S_{cash}$ and awarded free spins $S_{spins}$) is mapped as a piecewise function of this variable $C_S$.

### Python Implementation:
```
# Summing the pre-computed indicator variable I across all 5 reels (C_S)
scatters = st0[0] + st1[0] + st2[0] + st3[0] + st4[0]

# Piecewise mapping function for scatter payouts
scatter_pays = {
    3: {'cash': 10,  'spins': 8},
    4: {'cash': 50,  'spins': 12}, 
    5: {'cash': 250, 'spins': 20}
}

# Resolving S_cash and S_spins
sc_info = scatter_pays.get(scatters, {})
trigger_cash = float(sc_info.get('cash', 0.0))
spins_awarded = int(sc_info.get('spins', 0))
```
