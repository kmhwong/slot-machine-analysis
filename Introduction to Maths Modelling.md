# Mathematical Framework: Slot Machine Probability Space & Random Variables

To establish a rigorous mathematical framework for a $3 \times 5$ slot machine, we must define the probability space starting from the mechanical reels up to the final payout evaluations. 
Here is the formal definition of the sample space and the random variables governing the game.

## 1. The Fundamental Random Variables (The Reel Stops)
The entire state of the slot machine is determined by exactly one mechanical event: the stopping position of each of the 5 reels. Let $L_c$ be the ordered list of 12 symbols on reel $c$, where $c \in \{0, 1, 2, 3, 4\}$. Let $Y_c$ be the random variable representing the index of the symbol on reel $c$ that lands on the top row of the grid. Since each reel stops randomly and independently, $Y_c$ follows a Discrete Uniform Distribution: 

$$Y_c \sim \text{Uniform}(0, 11)$$

$$P(Y_c = y) = \frac{1}{12} \quad \text{for } y \in \{0, 1, \dots, 11\}$$

## 2. The Sample Space ($\Omega$)
The sample space $\Omega$ consists of every possible combination of the 5 reel stops. An individual outcome $\omega \in \Omega$ is a 5-tuple representing the stops of the 5 reels: 

$$\omega = (y_0, y_1, y_2, y_3, y_4)$$

Because the reels are independent, the size of the sample space is the product of their lengths: 

$$|\Omega| = 12 \times 12 \times 12 \times 12 \times 12 = 12^5 = \mathbf{248,832}$$

Under a fair RNG, every outcome is equally likely. Thus, the probability measure for any specific stop combination $\omega$ is: 

$$P(\omega) = \frac{1}{248,832}$$

## 3. The Grid (Derived Matrix State)
Once the reels stop, they populate a $3 \times 5$ visible grid. We define this grid as a random matrix $M(\omega)$ with rows $r \in \{0, 1, 2\}$ and columns $c \in \{0, 1, 2, 3, 4\}$. 

The symbol in any specific cell of the grid is determined by adding the row index to the reel's stopping position (wrapping around modulo 12): 

$$M_{r,c} = L_c[\ (Y_c + r) \pmod{12} \]$$

## 4. The Payline Random Variables
A payline is a predetermined geometric path across the matrix $M$. Let $\pi_k$ be the $k$-th payline, defined as a vector of row indices for each column: $\pi_k = [r_0, r_1, r_2, r_3, r_4]$.

For example, a "V-shape" payline is defined as $\pi_4 = [0, 1, 2, 1, 0]$. 

We define $V_k$ as the random vector of 5 symbols that land on payline $k$: 

$$V_k = \Big( M_{\pi_k[0], 0},\; M_{\pi_k[1], 1},\; M_{\pi_k[2], 2},\; M_{\pi_k[3], 3},\; M_{\pi_k[4], 4} \Big)$$

## 5. The Reward Random Variables
Let the function $f(V_k)$ represent the paytable evaluation logic (checking for 3, 4, or 5 consecutive matching symbols from left to right, factoring in 'W' wilds).

We define $X_k$ as the **Random Variable for the Payout of Payline $k$**: 

$$X_k = f(V_k)$$ 

The **Total Base Win Random Variable ($W_{base}$)** is the sum of the payouts across all 5 active paylines: 

$$W_{base} = \sum_{k=1}^{5} X_k$$ 

*(Note: By the Linearity of Expectation, the expected value of the base spin is simply $E[W_{base}] = \sum E[X_k]$, which is why analytical scripts calculate the expected win by summing individual line averages.)*

## 6. The Scatter Random Variable
Scatters do not follow paylines; they are counted across the entire matrix $M$. We define an indicator variable $I$ that equals $1$ if a cell contains a scatter ('S') and $0$ otherwise.

The **Total Scatter Count Random Variable ($C_S$)** is:

$$C_S = \sum_{c=0}^{4} \sum_{r=0}^{2} I(M_{r,c} == \text{'S'})$$ 

The payout for scatters (both cash $S_{cash}$ and awarded free spins $S_{spins}$) is mapped as a piecewise function of this variable $C_S$.
