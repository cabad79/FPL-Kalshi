# Comprehensive Statistical Soccer Analysis Guide

**Source:** Soccer Analytics: An Introduction Using R (Clive Beggs, 2024)  
**Purpose:** Complete methodology for predicting soccer outcomes using Poisson models and statistical methods  
**Audience:** FPL managers, sports bettors, data analysts

---

## EXECUTIVE SUMMARY

Soccer match outcomes can be predicted using statistical models with ~55-65% accuracy on head-to-head betting. This guide provides the complete methodology using proven techniques from academic research and professional soccer analytics.

### Key Findings
- **Poisson distribution** accurately models goal-scoring (r > 0.99)
- **Poisson regression** predicts expected goals (λ, μ) with high reliability
- **Expected Goals (xG)** correlates with season success (r = 0.74)
- **Pythagorean points** predict final league position (r = 0.97)
- **No single model** exceeds 65% prediction accuracy (inherent uncertainty)

---

## 1. COMPLETE PREDICTION PIPELINE

### Step 1: Data Collection

#### Required Data Points (Per Team, Per Season)
```
Home/Away Status
Goals Scored
Goals Conceded
Shots
Shots on Target
Pass Completion %
Tackles
Intercepts
Aerial Wins/Losses
Crosses
Dribbles
```

#### Data Sources
- **Primary:** Football-Data.co.uk (free EPL data)
- **Advanced:** StatsBomb, Opta Sports, Understat (xG)
- **Format:** CSV or database (must be normalized)

### Step 2: Exploratory Data Analysis

#### Check Distribution
```r
# Visualize goal distribution
hist(data$FTHG, breaks=10, main="Home Goals Distribution")
summary(data$FTHG)  # Mean, median, SD

# Test for normality
shapiro.test(data$FTHG)
```

#### Key Statistics to Calculate
```
Home goals: Mean = 1.568, SD = 1.236
Away goals: Mean = 1.253, SD = 1.087
Home advantage: 1.568 / 1.253 = 1.25 (25% boost)
```

### Step 3: Model Selection

#### Decision Tree
```
Question: What is your prediction goal?
├─ "Match odds" → Use Poisson Regression + Dixon-Coles
├─ "Season position" → Use Pythagorean Expected Points
├─ "Player performance" → Use Linear Regression
├─ "Goal probability" → Use Poisson Distribution directly
└─ "Team ranking" → Use Elo or Colley Algorithm
```

### Step 4: Model Fitting

#### Poisson Regression (for expected goals)

```r
# Convert wide to long format
long_data <- rbind(
  data.frame(Home=1, Team=data$Home, Opponent=data$Away, Goals=data$FTHG),
  data.frame(Home=0, Team=data$Away, Opponent=data$Home, Goals=data$AWHG)
)

# Fit model
pois_mod <- glm(Goals ~ Home + Team + Opponent,
                family=poisson(link=log),
                data=long_data)

# Extract expected goals for specific match
lambda <- predict(pois_mod, 
                  data.frame(Home=1, Team="Liverpool", Opponent="Arsenal"),
                  type='response')
# lambda ≈ 2.1 (Liverpool expected home goals)
```

### Step 5: Probability Calculation

#### From Expected Goals to Match Odds

```r
# Using Poisson probabilities
library(stats)

lambda <- 2.1  # Liverpool
mu <- 1.3      # Arsenal

# Calculate match outcome
home_win <- ppois(0, mu) * (1 - ppois(0, lambda))  +
            ppois(1, mu) * (1 - ppois(1, lambda))  + ... # continues for all scores

draw <- sum(dpois(0:6, lambda) * dpois(0:6, mu) * (diag(7)))

away_win <- 1 - home_win - draw

# Convert to odds
home_odds <- 1 / home_win      # e.g., 1 / 0.45 = 2.22
draw_odds <- 1 / draw          # e.g., 1 / 0.28 = 3.57
away_odds <- 1 / away_win      # e.g., 1 / 0.27 = 3.70
```

### Step 6: Model Validation

#### Out-of-Sample Testing
```r
# Split data
train_idx <- 1:300
test_idx <- 301:380

train_data <- data[train_idx, ]
test_data <- data[test_idx, ]

# Fit on training
model_train <- glm(Goals ~ Home + Team + Opponent,
                   family=poisson(link=log),
                   data=train_data)

# Predict on test
predictions <- predict(model_train, test_data, type='response')

# Calculate accuracy
correct <- sum((predictions > 1 & test_data$FTHG > 1.5) | 
               (predictions <= 1 & test_data$FTHG <= 1.5))
accuracy <- correct / nrow(test_data)
# Typical: 55-58%
```

---

## 2. POISSON REGRESSION FOR GOAL PREDICTION

### Theoretical Foundation

#### Why Poisson?
- Goals are **count data** (0, 1, 2, ...)
- Goals are **independent** events
- Goals are **rare** relative to match duration
- **Empirical evidence:** r = 0.994 correlation (EPL 2018-19)

#### GLM Framework
```
Log-linear model ensures positive predictions:
ln(y) = b₀ + b₁(Home) + b₂(Team) + b₃(Opponent)
y = e^(b₀ + b₁(Home) + b₂(Team) + b₃(Opponent))
```

### Model Interpretation

#### Coefficients Example
```
(Intercept):      0.49 → baseline ~1.6 goals
Home:             0.25 → home teams score e^0.25 = 1.28× more
TeamLiverpool:    0.18 → Liverpool +18% attacking power
OppArsenal:      -0.12 → Arsenal defense -12% effectiveness
```

### Limitations & Improvements

#### Poisson Limitations
- Underestimates 0-0, 1-0, 1-1 (low scores)
- Assumes independence (momentum exists)
- Doesn't model clustering (goals in runs)

#### Solution: Dixon-Coles Model
```
Apply tau function to adjust low-score probabilities:
τ(x, y, λ, μ, ρ) = {
  1 - λμρ    if x=0, y=0
  1 + λρ     if x=0, y=1
  1 + μρ     if x=1, y=0
  1 - ρ      if x=1, y=1
  1          otherwise
}

Optimize ρ to maximize likelihood using BFGS
Typical ρ ≈ -0.03
```

### Implementation Checklist

- [ ] Load data (CSV from football-data.co.uk)
- [ ] Check goal distribution (mean, SD)
- [ ] Validate Poisson fit (correlation test)
- [ ] Fit Poisson regression model
- [ ] Extract team coefficients
- [ ] Calculate expected goals (λ, μ) for new matches
- [ ] Generate probability matrices
- [ ] Apply Dixon-Coles adjustment (optional, for accuracy)
- [ ] Convert to decimal odds
- [ ] Compare vs bookmaker odds (value betting)

---

## 3. EXPECTED GOALS (xG) INTEGRATION

### Why xG Matters

#### Correlation with Points
```
Simple Metrics:
- Shots per match: r = 0.45
- Shots on target: r = 0.65

Advanced Metrics:
- Expected Goals (xG): r = 0.74 ← BEST SINGLE METRIC
- xG + xGA: r = 0.85
```

#### Real Example
```
Team A: 3 goals from 18 shots = 0.167 conversion
Team B: 3 goals from 6 shots = 0.500 conversion

Same scoreline (3-3), very different quality!

With xG:
Team A: xG = 2.2 (underperformed by 0.8)
Team B: xG = 2.8 (overperformed by 0.2)

Now we understand who played better.
```

### Incorporating xG Into Models

#### Three Approaches

**1. Replace Shots with xG in Models**
```r
model_xg <- glm(Points ~ xG + xGA, 
                family=poisson(link=log),
                data=season_data)
# Better prediction of points than raw shots
```

**2. Use xG as Predictor Variable**
```r
# Multi-metric model
model_multi <- lm(Points ~ xG + xGA + PassCompletion + Intercepts,
                  data=season_data)
# Explains ~80% of variance
```

**3. Combine with Poisson (Hybrid)**
```
1. Use xG as initial λ estimate
2. Apply Poisson regression adjustment
3. Fine-tune with team-specific coefficients
4. Calculate final probabilities
```

---

## 4. PYTHAGOREAN EXPECTED POINTS

### When to Use
- Season-long predictions (not individual matches)
- Mid-season forecasting
- Understanding lucky/unlucky teams

### Formula & Coefficients

```
ptsexp = 2.78 × [GF^1.24 / (GF^1.24 + GA^1.25)] × matches_played

Coefficient values (Beggs optimization, 1995-2017):
a = 2.78 (points multiplier)
b = 1.24, c = 1.24, d = 1.25 (goal exponents)

Validation: r = 0.972 with actual points (EPL 2020-21)
95% CI: [0.9296, 0.9892]
```

### Implementation

```r
pythag_points <- function(GF, GA, PLD, nGames=38) {
  a <- 2.78; b <- 1.24; c <- 1.24; d <- 1.25
  
  pythag_frac <- (GF^b) / ((GF^c) + (GA^d))
  exp_pts <- a * pythag_frac * PLD
  pred_remaining <- a * pythag_frac * (nGames - PLD)
  
  return(list(
    expected_so_far = exp_pts,
    predicted_total = exp_pts + pred_remaining
  ))
}

# Example: Liverpool at round 19
result <- pythag_points(38, 19, 19)
# Expected: 48 points so far
# Predicted total: ~87 points
```

### Reliability by Round

| Round | Matches | MAE | Confidence |
|-------|---------|-----|------------|
| 10 | 10 | ±9.2 | Low (early) |
| 19 | 19 | ±6.1 | Moderate |
| 29 | 29 | ±2.8 | High |
| 38 | 38 | 0.0 | Perfect |

---

## 5. COMBINING MULTIPLE MODELS

### Ensemble Approach

#### Why Combine?
- No single model >65% accuracy
- Different models capture different patterns
- Averaging reduces variance
- Provides confidence estimate

#### Model Weights
```
Final Prediction = w₁×Poisson + w₂×xG + w₃×Pythagorean + w₄×RandomForest

Weight Assignment (empirically optimized):
w₁ = 0.30 (Poisson Regression)
w₂ = 0.35 (Expected Goals)
w₃ = 0.20 (Pythagorean Points)
w₄ = 0.15 (Machine Learning)
```

#### R Implementation
```r
ensemble_prediction <- function(models_list, weights) {
  predictions <- sapply(models_list, function(m) predict(m))
  weighted_avg <- sum(predictions * weights)
  
  # Calculate confidence
  variance <- var(predictions)
  confidence <- 1 - (variance / sum(predictions)^2)
  
  return(list(
    prediction = weighted_avg,
    confidence = confidence
  ))
}
```

---

## 6. STATISTICAL SIGNIFICANCE IN CONTEXT

### Understanding P-Values

#### Correct Interpretation
```
p = 0.03 means:
"If null hypothesis true, 3% probability of 
observing this result (or more extreme)"

NOT: "3% probability results are due to chance"
NOT: "97% confidence in finding"
```

#### Practical Example
```
Team A vs Team B performance difference:
t-test p = 0.001 (highly significant)
Cohen's d = 0.2 (tiny effect)

Conclusion: Difference is REAL but NEGLIGIBLE
Statistical significance ≠ Practical significance
```

### Multiple Testing Correction

#### Problem
```
Testing 11 variables without correction:
Expected false positives = 11 × 0.05 = 0.55
Actual error rate ≈ 44%
```

#### Solutions

**Bonferroni:** α = 0.05 / 11 = 0.0045
- Conservative
- Loses power
- Suitable for confirmatory analysis

**Benjamini-Hochberg FDR:** p_adj = p × (m/rank)
- Better for exploratory work
- More power than Bonferroni
- Controls false discovery rate

---

## 7. BAYESIAN APPROACH (OPTIONAL)

### When Bayesian Helps
- Small sample size (early season)
- Prior knowledge available (historical data)
- Uncertainty quantification important

### Simple Bayesian Update
```
Prior: Team's historical performance
Data: Current season results
Posterior: Updated estimate

Team's win probability:
P(W|Data) ∝ P(Data|W) × P(W)

Where:
P(Data|W) = Likelihood from current matches
P(W) = Prior from historical data
```

### Implementation
```r
library(Rstan)  # or simpler: conjugate priors

# Beta-binomial model for win probability
prior_alpha <- 50  # From historical seasons
prior_beta <- 40   # Historical losses

matches_won <- 15
matches_total <- 25

posterior_alpha <- prior_alpha + matches_won
posterior_beta <- prior_beta + (matches_total - matches_won)

# Posterior expected probability
post_prob <- posterior_alpha / (posterior_alpha + posterior_beta)
```

---

## 8. PRACTICAL WORKFLOW FOR FPL PREDICTION

### Weekly Workflow

#### Tuesday (After Last Gameweek)
```
1. Download latest EPL data
2. Update Poisson regression model
3. Calculate λ, μ for all upcoming matches
4. Generate probability matrices
5. Extract expected points by player
```

#### Wednesday (Analysis)
```
1. Compare predicted vs actual results (validation)
2. Identify over/under performers
3. Update team strength estimates
4. Calculate expected points by position
5. Generate fixture difficulty ratings
```

#### Thursday (Decision)
```
1. Create predicted points rankings
2. Identify value (predicted points vs ownership)
3. Model differential gain (differential ownership)
4. Select transfer targets
5. Set lineup strategy
```

#### Sample Code
```r
# Load FPL data
fpl_data <- read.csv("fpl_players.csv")

# Predict points for upcoming gameweek
gameweek <- 15

predictions <- sapply(1:nrow(fpl_data), function(i) {
  player <- fpl_data[i, ]
  team_lambda <- predict(pois_mod,
    data.frame(Home=..., Team=..., Opponent=...),
    type='response')
  
  # Convert expected goals to points
  expected_pts <- ifelse(player$position == "GK", 
                         team_lambda * 0.5,
                         team_lambda * 0.4)
  return(expected_pts)
})

fpl_data$predicted_pts <- predictions
fpl_data$value <- fpl_data$predicted_pts / fpl_data$price

# Top value picks
top_value <- fpl_data[order(-fpl_data$value), ][1:20, ]
```

---

## 9. BETTING STRATEGY FRAMEWORK

### Expected Value (EV) Approach

#### Calculate EV
```
EV = (Win Probability × Odds) - Probability of Loss

Example:
Model says: 45% win probability
Bookmaker odds: 2.5
Implied probability: 1/2.5 = 40%

EV = (0.45 × 2.5) - (0.55 × 1)
EV = 1.125 - 0.55 = 0.575

For every £1 bet:
Expected return: £2.5 × probability = £1.125
Expected loss: -£1 × (1-probability) = -£0.55
Net: +£0.575 per bet (positive expectation)
```

#### Practical Rules
```
Only bet when:
- EV > 5% (0.05 positive expected value)
- Confidence in prediction > 70%
- Odds from efficient bookmaker (Pinnacle, Betfair)

Bet sizing:
- Kelly Criterion: f = (bp - q) / b
- Fractional Kelly: f/2 or f/4 for safety
- Minimum stake: %5-%10% of bankroll
```

---

## 10. RISK MANAGEMENT

### Avoiding Common Pitfalls

#### Overfitting
```
Problem: Model fits training data too well
- High R² in sample (0.90)
- Low accuracy out of sample (45%)

Solution:
- Use cross-validation (k-fold)
- Test on holdout data
- Regularize (ridge, lasso)
```

#### Survivorship Bias
```
Problem: Only tracking winners (not losers)
- Overestimate success rate
- Ignore failed predictions

Solution:
- Track ALL predictions
- Calculate actual accuracy
- Review losing picks for lessons
```

#### P-Hacking
```
Problem: Test until significant
- Multiple tests without correction
- Report only positive results

Solution:
- Decide analysis plan before looking at data
- Pre-register hypotheses
- Control for multiple comparisons
```

---

## FINAL CHECKLIST: COMPLETE ANALYSIS

- [ ] **Data Collection:** All required variables downloaded
- [ ] **Validation:** Distribution and assumptions checked
- [ ] **Model Selection:** Appropriate method chosen based on goal
- [ ] **Fitting:** Model trained on sufficient data (>300 matches)
- [ ] **Testing:** Out-of-sample validation accuracy ≥55%
- [ ] **Calibration:** Predicted probabilities align with outcomes
- [ ] **Sensitivity Analysis:** Model robust to small changes
- [ ] **Uncertainty:** Confidence intervals and error bounds calculated
- [ ] **Comparison:** Model performance vs benchmark
- [ ] **Documentation:** Method reproducible and transparent
- [ ] **Ethics:** No insider information or data manipulation

---

## REFERENCES & FURTHER READING

### Key Papers
- **Poisson Model:** Lee (1997) - "Modelling Scores in the Premier League"
- **Dixon-Coles:** Dixon & Coles (1997) - "Modelling Association Football Scores"
- **Pythagorean:** Beggs & Beggs (2017) - Empirical optimization
- **Bayesian:** Constantinou & Fenton (2012) - Fixed Soccer Odds

### Books
- Soccer Analytics: An Introduction Using R (Beggs, 2024)
- The Numbers Game (Swaab & Anderson, 2014)
- How to Find Hidden Jobs (LinkedIn Data Analysis)

### Online Resources
- Football-Data.co.uk (data)
- StatsBomb (open data + blog)
- Understat.com (xG analyses)
- Betfair API (market data)

---

**This guide integrates all statistical methods from "Soccer Analytics: An Introduction Using R" into a complete prediction framework. Accuracy expected: 55-65% on match odds, 85%+ on season predictions.**

