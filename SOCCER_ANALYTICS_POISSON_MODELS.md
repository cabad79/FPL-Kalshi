# Soccer Analytics: Poisson Models & Goal Prediction

**Source:** Soccer Analytics: An Introduction Using R (Clive Beggs, 2024)  
**Chapters:** 6.3-6.5, 5.7  
**Focus:** Statistical modeling of soccer match outcomes

---

## 1. POISSON DISTRIBUTION FOR GOALS

### Mathematical Foundation

#### Probability Mass Function
```
P(X = k) = (e^(-λ) × λ^k) / k!
```

Where:
- **X** = number of goals scored
- **k** = specific goal count (0, 1, 2, 3, ...)
- **λ (lambda)** = expected value (mean goals per match)
- **e** = Euler's number (2.71828...)
- **k!** = factorial (k × (k-1) × ... × 1)

#### Key Assumptions
1. **Independence:** Each goal is independent; scoring one goal doesn't change probability of next
2. **Constant rate:** Goal-scoring rate constant throughout match
3. **No simultaneity:** Goals occur one at a time (not simultaneously)
4. **Stationarity:** Environmental factors don't change during match

### Why Poisson Fits Soccer

#### Empirical Validation (EPL 2018-19)

**Home Goals Distribution (n=380 matches):**
```
Goals    0     1     2     3     4     5     6
Actual  88    116    95    48    22     8     3
Model   89    140    110   57    22     7     2
```

**Statistical Correlation:** r = 0.9946 (extremely strong fit)

**Away Goals Distribution:**
```
Goals    0     1     2     3     4    5     6
Actual  119   122    87    36     9    6     1
Model   95    119    75    31    10    2     1
```

**Statistical Correlation:** r = 0.9913

#### Home Advantage Effect
- **Home team mean:** 1.568 goals/match
- **Away team mean:** 1.253 goals/match
- **Home advantage ratio:** 1.568 / 1.253 = 1.25 (25% more goals)

### R Implementation: Poisson Analysis

#### Computing Probabilities
```r
# Mean goals for home and away teams (2018-19 EPL)
hgoals.mean <- 1.568  # Home teams
agoals.mean <- 1.253  # Away teams

# Poisson probability for 0-6 goals
goal_scale <- 0:6

# Home team Poisson distribution
home_probs <- dpois(x=goal_scale, lambda=hgoals.mean)
# Result: [0.208, 0.327, 0.257, 0.135, 0.053, 0.017, 0.004]

# Away team Poisson distribution
away_probs <- dpois(x=goal_scale, lambda=agoals.mean)
# Result: [0.286, 0.359, 0.225, 0.094, 0.030, 0.007, 0.002]
```

#### Complete R Workflow
```r
# 1. Load EPL data
mydata <- read.csv('https://www.football-data.co.uk/mmz4281/1819/E0.csv')
n <- nrow(mydata)

# 2. Calculate mean goals
hgoals.mean <- mean(mydata$FTHG)  # 1.568
agoals.mean <- mean(mydata$FTAG)  # 1.253

# 3. Create observed frequency distributions
hg.freq <- table(mydata$FTHG)
hgoals.frac <- hg.freq / n

ag.freq <- table(mydata$FTAG)
agoals.frac <- ag.freq / n

# 4. Create Poisson probability matrix
scale <- 0:6
home_poisson <- dpois(x=scale, lambda=hgoals.mean)
away_poisson <- dpois(x=scale, lambda=agoals.mean)

# 5. Compare observed vs theoretical
plot(scale, hgoals.frac, type="b", pch=20, lty=1, 
     main="Home Goals: Observed vs Poisson",
     xlab="Goals", ylab="Proportion")
lines(scale, home_poisson, type="b", pch=21, lty=2, col="red")
legend("topright", c("Observed", "Poisson"), pch=c(20,21), lty=c(1,2))

# 6. Correlation test
cor_home <- cor(hgoals.frac, home_poisson)
cor_away <- cor(agoals.frac, away_poisson)
print(paste("Home correlation:", round(cor_home, 4)))
print(paste("Away correlation:", round(cor_away, 4)))
```

#### Match Outcome Probabilities from Poisson

**Given λ (home goals) and μ (away goals), calculate outcome probabilities:**

```r
# Example: Manchester United home vs Liverpool away
lambda <- 1.8  # Man Utd expected home goals
mu <- 1.2      # Liverpool expected away goals

# Create 7x7 probability matrix
outcomes <- matrix(0, nrow=7, ncol=7)
goal_range <- 0:6

for(i in 1:7) {
  for(j in 1:7) {
    outcomes[i,j] <- dpois(goal_range[i], lambda) * dpois(goal_range[j], mu)
  }
}

# Calculate win/draw/loss probabilities
home_win <- sum(outcomes[lower.tri(outcomes)])  # Home goals > Away goals
draws <- sum(diag(outcomes))                     # Equal goals
away_win <- sum(outcomes[upper.tri(outcomes)])  # Away goals > Home goals

print(paste("Home Win:", round(home_win, 3)))
print(paste("Draw:", round(draws, 3)))
print(paste("Away Win:", round(away_win, 3)))
```

---

## 2. POISSON REGRESSION PREDICTION MODEL

### Mathematical Framework

#### Generalized Linear Model (GLM)

**Log-Linear Form:**
```
ln(y) = b₀ + b₁x₁ + b₂x₂ + ... + bₖxₖ
```

**Exponential (Response) Form:**
```
y = e^(b₀ + b₁x₁ + b₂x₂ + ...)
  = e^b₀ × e^(b₁x₁) × e^(b₂x₂) × ...
```

Where:
- **y** = predicted goals scored
- **b₀** = intercept
- **b₁, b₂, ...** = regression coefficients
- **x₁, x₂, ...** = predictor variables
- **e** = exponential ensures positive predictions

#### Why Log-Link Function?
- Goals are count data (non-negative)
- Linear regression can predict negative values (impossible)
- Log-link guarantees all predictions > 0
- Natural for exponential relationships

### Model Specification

#### Predictor Variables

```
Goals ~ Home + Team + Opponent
```

**Home:** Indicator variable (1=home, 0=away)  
**Team:** Team attacking strength  
**Opponent:** Opponent defensive weakness

#### R Model Fitting

```r
# Convert from wide to long format
long_data <- rbind(
  # Home team records
  data.frame(
    Home=1, 
    Team=dat$Home, 
    Opponent=dat$Away, 
    Goals=dat$Hgoals
  ),
  # Away team records
  data.frame(
    Home=0, 
    Team=dat$Away, 
    Opponent=dat$Home, 
    Goals=dat$Agoals
  )
)

# Fit Poisson GLM
pois_model <- glm(Goals ~ Home + Team + Opponent,
                  family=poisson(link=log),
                  data=long_data)

summary(pois_model)
```

### Example Output (2018-19 EPL, 370 Matches)

#### Sample Coefficients
```
                Estimate  Std. Error  z value  Pr(>|z|)
(Intercept)      0.4926    0.1915     2.572    0.0101 *
Home             0.2527    0.0627     4.031  5.56e-05 ***
TeamBrighton    -0.7334    0.2094    -3.503    0.0005 ***
TeamBurnley     -0.4493    0.1925    -2.334    0.0196 *
TeamChelsea     -0.1249    0.1740    -0.718    0.4730
TeamLiverpool    0.1849    0.1609     1.149    0.2505
TeamMan City     0.2291    0.1593     1.438    0.1505
...
```

#### Interpreting Coefficients

**Home Coefficient = 0.2527:**
```
e^0.2527 = 1.288
Interpretation: Home teams score 1.288× more goals (28.8% advantage)
```

**Team-specific Example (Liverpool):**
```
Coefficient = 0.1849 (positive)
e^0.1849 = 1.203
Interpretation: Liverpool scores 20.3% more goals than baseline
```

### Making Predictions

#### Predicting Expected Goals (λ and μ)

```r
# Burnley home vs Arsenal away
burnley_home_lambda <- predict(pois_model,
  data.frame(Home=1, Team="Burnley", Opponent="Arsenal"),
  type='response')
# λ ≈ 1.344 (Burnley expected home goals)

arsenal_away_mu <- predict(pois_model,
  data.frame(Home=0, Team="Arsenal", Opponent="Burnley"),
  type='response')
# μ ≈ 2.083 (Arsenal expected away goals)

# Calculate match outcome probabilities
outcomes <- matrix(0, nrow=7, ncol=7)
for(i in 0:6) {
  for(j in 0:6) {
    outcomes[i+1, j+1] <- dpois(i, burnley_home_lambda) * 
                          dpois(j, arsenal_away_mu)
  }
}

home_win <- sum(outcomes[lower.tri(outcomes)])
draw <- sum(diag(outcomes))
away_win <- sum(outcomes[upper.tri(outcomes)])

print(paste("Burnley Win:", round(home_win, 3)))
print(paste("Draw:", round(draw, 3)))
print(paste("Arsenal Win:", round(away_win, 3)))
```

### Model Performance

#### Limitations

1. **Underestimates low-scoring results:**
   - 0-0 draws
   - 1-0 home/away wins
   - 1-1 draws

2. **Prediction accuracy:** ~55% on match favorites (better than coin flip, not perfect)

3. **Assumes independence:** Doesn't account for psychological factors
   - Momentum from recent wins
   - Pressure in decisive matches
   - Injury surprises

#### Best Uses

✓ Calculating expected goals for betting odds  
✓ Tournament simulations  
✓ Season point predictions (aggregate)  
✗ Individual match certainty (inherent unpredictability)  

---

## 3. DIXON-COLES MODEL: IMPROVING POISSON

### The Problem: Low-Score Bias

#### Poisson Underestimates
```
Score    Poisson  Actual   Difference
0-0      0.0325   0.0350   -0.0025 (too low)
1-0      0.0676   0.0651   +0.0025 (too high)
0-1      0.0436   0.0411   +0.0025 (too high)
1-1      0.0909   0.0934   -0.0025 (too low)
```

### Mathematical Solution

#### Tau Adjustment Function

```
τ(x, y, λ, μ, ρ) = {
  1 - (λ×μ×ρ)         if x=0, y=0   (less common)
  1 + (λ×ρ)           if x=0, y=1   (more common)
  1 + (μ×ρ)           if x=1, y=0   (more common)
  1 - ρ               if x=1, y=1   (less common)
  1                   otherwise      (no adjustment)
}
```

Where:
- **ρ (rho):** Adjustment parameter (typically negative, -0.05 to 0)
- **λ, μ:** Expected goals (from Poisson regression)
- **x, y:** Goals scored (home, away)

#### Adjusted Probability
```
P(X=x, Y=y|Dixon-Coles) = τ(x,y,λ,μ,ρ) × P(X=x|λ) × P(Y=y|μ)
```

### R Implementation

#### User-Defined Functions

**1. Tau Function (Vectorized):**
```r
tau <- Vectorize(function(x, y, lambda, mu, rho){
  if(x == 0 & y == 0) return(1 - (lambda * mu * rho))
  else if(x == 0 & y == 1) return(1 + (lambda * rho))
  else if(x == 1 & y == 0) return(1 + (mu * rho))
  else if(x == 1 & y == 1) return(1 - rho)
  else return(1)
})
```

**2. Log-Likelihood Function:**
```r
logLike <- function(y1, y2, lambda, mu, rho=0){
  taus <- tau(y1, y2, lambda, mu, rho)
  log_likelihood <- sum(
    log(taus) + 
    log(dpois(y1, lambda)) + 
    log(dpois(y2, mu))
  )
  return(log_likelihood)
}
```

**3. Optimization Function:**
```r
optRho <- function(par, y1, y2, lambda, mu){
  rho <- par[1]
  return(logLike(y1, y2, lambda, mu, rho))
}
```

#### Finding Optimal ρ

```r
# Use BFGS optimization
result <- optim(
  par=c(-0.05),
  fn=function(par) optRho(par, build_dat$Hgoals, build_dat$Agoals, 
                          home.exp, away.exp),
  control=list(fnscale=-1),  # Maximize (not minimize)
  method='BFGS'
)

rho_optimal <- result$par
print(paste("Optimized rho:", round(rho_optimal, 4)))
# Example: rho ≈ -0.0276
```

### Worked Example: Burnley vs Arsenal

#### Expected Goals (Poisson Model)
```
λ (Burnley home) = 1.344
μ (Arsenal away) = 2.083
```

#### Step 1: Create Poisson Probability Matrix

```r
lambda <- 1.344
mu <- 2.083

# Create 9×9 matrix
prob_matrix <- matrix(0, nrow=9, ncol=9)
for(i in 0:8) {
  for(j in 0:8) {
    prob_matrix[i+1, j+1] <- dpois(i, lambda) * dpois(j, mu)
  }
}
```

**Top-left corner (0-3 goals each team):**
```
       0     1     2     3
0  0.0325 0.0676 0.0704 0.0489
1  0.0436 0.0909 0.0947 0.0658
2  0.0293 0.0611 0.0637 0.0442
3  0.0131 0.0274 0.0285 0.0198
```

#### Step 2: Apply Dixon-Coles Adjustment

```r
rho <- -0.0276

# Adjust only low-scoring matches
adj_matrix <- prob_matrix

for(i in 0:1) {
  for(j in 0:1) {
    tau_val <- tau(i, j, lambda, mu, rho)
    adj_matrix[i+1, j+1] <- prob_matrix[i+1, j+1] * tau_val
  }
}

# Adjusted 2×2 corner:
adjusted_corner <- matrix(0, nrow=2, ncol=2)
adjusted_corner[1,1] <- 0.0325 * (1 - (1.344 * 2.083 * -0.0276)) = 0.0350
adjusted_corner[1,2] <- 0.0676 * (1 + (1.344 * -0.0276)) = 0.0651
adjusted_corner[2,1] <- 0.0436 * (1 + (2.083 * -0.0276)) = 0.0411
adjusted_corner[2,2] <- 0.0909 * (1 - (-0.0276)) = 0.0934
```

#### Match Outcome Probabilities

**Raw Poisson:**
```
Home win: 0.253
Draw: 0.233
Away win: 0.514
```

**Dixon-Coles Adjusted:**
```
Home win: 0.242 (↓ 1.1%)
Draw: 0.216 (↓ 1.7%)
Away win: 0.542 (↑ 2.8%)
```

**Actual Result:** Arsenal won 1-0 (Away win ✓)

### Model Comparison

#### Performance on 10 EPL Matches (Last games, 2018-19)

| Metric | Poisson | Dixon-Coles | Pinnacle Odds |
|--------|---------|-------------|---------------|
| Correct predictions | 5/10 | 5/10 | 4/10 |
| Accuracy | 50% | 50% | 40% |
| Avg prediction error | 0.089 | 0.067 | 0.052 |
| Handles low-scores | Poor | Better | Good |

#### When to Use

**Dixon-Coles preferred when:**
- Modeling defensive/cautious leagues (lower scores)
- Many draws expected
- Draw-heavy competitions (e.g., European qualifiers)
- Account needed for score-specific patterns

**Simple Poisson acceptable when:**
- Need quick calculation
- High-scoring league
- Tournament simulations (volume over precision)

---

## 4. INTEGRATING POISSON & DIXON-COLES

### Full Prediction Pipeline

```r
# 1. Fit Poisson regression
model <- glm(Goals ~ Home + Team + Opponent,
             family=poisson(link=log),
             data=long_data)

# 2. Get expected goals for new match
lambda <- predict(model, 
                  data.frame(Home=1, Team=team1, Opponent=team2),
                  type='response')
mu <- predict(model,
              data.frame(Home=0, Team=team2, Opponent=team1),
              type='response')

# 3. Calculate Poisson probabilities
poisson_probs <- matrix(0, 7, 7)
for(i in 0:6) {
  for(j in 0:6) {
    poisson_probs[i+1, j+1] <- dpois(i, lambda) * dpois(j, mu)
  }
}

# 4. Optimize rho (one-time per dataset)
result <- optim(par=-0.05, 
                fn=function(par) optRho(par, data$goals1, 
                                        data$goals2, lambda, mu),
                control=list(fnscale=-1),
                method='BFGS')
rho <- result$par

# 5. Apply Dixon-Coles adjustment
adjusted_probs <- poisson_probs
for(i in 0:1) {
  for(j in 0:1) {
    adjusted_probs[i+1, j+1] <- poisson_probs[i+1, j+1] * 
                                tau(i, j, lambda, mu, rho)
  }
}

# 6. Calculate outcome probabilities
home_win <- sum(adjusted_probs[lower.tri(adjusted_probs)])
draw <- sum(diag(adjusted_probs))
away_win <- sum(adjusted_probs[upper.tri(adjusted_probs)])

# 7. Convert to decimal odds
home_odds <- 1 / home_win
draw_odds <- 1 / draw
away_odds <- 1 / away_win
```

---

## Summary: When to Use Each Model

| Model | Use Case | Accuracy | Speed | Code Complexity |
|-------|----------|----------|-------|-----------------|
| **Poisson** | Quick estimates, tournaments | 50-55% | Very fast | Simple |
| **Poisson GLM** | Season predictions | 55-60% | Fast | Moderate |
| **Dixon-Coles** | Precise odds, draws | 52-58% | Moderate | Complex |
| **Random Forest** | ML approach | 60-65% | Slow | High |

**Key Insight:** No single model achieves >65% accuracy on individual matches—soccer inherently unpredictable even to professionals (Pinnacle ~55%).
