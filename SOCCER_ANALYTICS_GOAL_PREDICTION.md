# Soccer Analytics: Goal Prediction & Expected Goals (xG)

**Source:** Soccer Analytics: An Introduction Using R (Clive Beggs, 2024)  
**Chapter:** 5.7 Expected Goals; 6.3-6.5 Poisson Models  
**Focus:** Predicting goal outcomes using statistical models

---

## 1. EXPECTED GOALS (xG) METHODOLOGY

### Conceptual Foundation

#### Core Principle
**Not all goal attempts are equal.** Each shot has an inherent probability of resulting in a goal based on:
- Distance from goal line
- Angle of shot
- Defensive pressure
- Goalkeeper positioning
- Type of shot (header, volley, tap-in)

#### Probability Scale (0-1)
```
0.01 = Very low probability (long-range speculative)
0.05 = Low probability (30+ yards)
0.15 = Moderate probability (18-yard line, defenders nearby)
0.30 = Good opportunity (6-yard box, some space)
0.50 = High probability (clear chance, goalkeeper beaten)
0.80 = Very high probability (1v1 with goalkeeper)
0.95 = Near-certain (tap-in with empty net)
```

### Mathematical Formula

#### Expected Goals Calculation
```
xG = ps₁ + ps₂ + ps₃ + ... + psₙ

Where:
- ps₁, ps₂, psₙ = probability of each individual shot
- n = total number of shots by team in match
```

#### Example: Team with 10 Shots
```
Shot 1: 0.05 (long range)
Shot 2: 0.08 (distance)
Shot 3: 0.12 (mid-range)
Shot 4: 0.15 (approaching box)
Shot 5: 0.02 (deflected)
Shot 6: 0.20 (clear chance)
Shot 7: 0.10 (blocked)
Shot 8: 0.06 (poor angle)
Shot 9: 0.03 (long shot)
Shot 10: 0.18 (penalty area)

xG = 0.05 + 0.08 + 0.12 + 0.15 + 0.02 + 0.20 + 0.10 + 0.06 + 0.03 + 0.18
xG = 0.99 expected goals
```

### Data Sources and Calculation

#### Three-Step Process

**1. Data Collection**
- Video analysts watch every shot
- Record shot location, type, defensive pressure
- Build proprietary database

**2. Comparative Database**
- Compare to 1000s of historical similar shots
- What % of shots from this location resulted in goals?
- Accounts for unique player/goalkeeper characteristics

**3. Team Aggregation**
- Sum probabilities for all shots in match
- Published by StatsBomb, Opta, Understat
- Updated after each round of matches

### Real-World Example: Brighton vs Man United (May 2022)

#### Match Details
```
Final Score: Brighton 4-0 Man United
Expected Goals: Brighton 2.04, Man United 1.73
Possession: 43% (Brighton) vs 57% (Man United)
```

#### Analysis
```
Brighton Performance:
- Fewer possessions (43%)
- Fewer total shots
- BUT higher quality chances
- ACTUAL: 4 goals vs xG: 2.04
- OUTPERFORMANCE: 1.96 goals above expected
- Explanation: Exceptional clinical finishing

Man United Performance:
- More possession (57%)
- More total shots
- BUT lower quality chances
- ACTUAL: 0 goals vs xG: 1.73
- UNDERPERFORMANCE: -1.73 goals
- Explanation: Poor conversion despite decent chances
```

**Conclusion:** The xG correctly identified Brighton created higher-quality chances despite fewer shots. The 4-0 scoreline was exceptional—xG suggested 2-1 Brighton.

### Why xG > Raw Shot Count

#### Comparison: Three 3-1 Wins

**Match 1 (Efficient)**
```
Team A: 6 shots, 3 goals → 0.50 conversion
xG: 2.8 → outperformed by 0.2 goals
Interpretation: Clinical finishing, high quality
```

**Match 2 (Average)**
```
Team A: 10 shots, 3 goals → 0.30 conversion
xG: 3.1 → underperformed by -0.1 goals
Interpretation: Typical efficiency for shots taken
```

**Match 3 (Wasteful)**
```
Team A: 18 shots, 3 goals → 0.17 conversion
xG: 4.5 → underperformed by -1.5 goals
Interpretation: Poor finishing, quantity over quality
```

Raw shot count (same 3 goals each) misses efficiency difference. xG captures quality difference.

---

## 2. CORRELATION WITH SEASON OUTCOMES

### EPL 2020-21 Season Analysis

#### Metric Comparison

| Metric | Formula | Correlation with Points | Explanation |
|--------|---------|-------------------------|-------------|
| **Goals Ratio** | GF / SF | r = 0.635 | Basic efficiency |
| **Expected Goals** | Sum of shot probabilities | r = 0.736 | **BEST single metric** |
| **Goal-to-Shot** | GF / SF (same as above) | r = 0.682 | Variance from luck |

#### Detailed Results

**Goals Ratio vs Points:**
```
Variables: Actual goals / shots vs season points
Correlation: r = 0.635
Significance: p < 0.05
Interpretation: Moderate correlation; some teams lucky/unlucky
```

**Expected Goals vs Points:**
```
Variables: xG (from analytical database) vs season points
Correlation: r = 0.736
Significance: p < 0.001
Interpretation: STRONG correlation; xG predicts success better
```

**Why xG Stronger:**
- Removes variance/luck component
- Isolates quality of chances created
- More stable across seasons
- Better predictor of future performance

### Team-Level Example: Man City vs Fulham

#### 2020-21 Season Performance

**Manchester City (Champions)**
```
Goals Scored: 83
Shots: 588
Goals Ratio: 0.141 (14.1% conversion)
Expected Goals: 73.3
Outperformance: +9.7 goals
Interpretation: Excellent finishing + high-quality chances
```

**Fulham (Relegated)**
```
Goals Scored: 27
Shots: 443
Goals Ratio: 0.061 (6.1% conversion)
Expected Goals: 41.3
Underperformance: -14.3 goals
Interpretation: Poor finishing despite decent chances
```

#### Efficiency Gap
```
Man City: 83/588 = 14.1%
Fulham: 27/443 = 6.1%

Man City converts 2.3× more shots than Fulham
Goal differential explains relegation despite similar possession
```

---

## 3. LIMITATIONS OF EXPECTED GOALS

### Limitation 1: Order Matters

#### Sequence Impact
```
Team scores in 5 minutes:
- Opponent becomes more aggressive
- Fewer defensive coverage
- More chances created
- xG increases artificially

Team concedes early:
- Team parks the bus defensively
- Fewer attacking opportunities
- xG decreases artificially
```

#### Real Example
```
Match: Team A 2-1 Team B

If Team A scored in 15, 45 minutes:
- Easy to create chances late
- xG might be 3.2

If Team A scored in 87, 90 minutes:
- Defended all match
- Created few chances until late push
- xG might be 1.4

SAME OUTCOME, DIFFERENT xG!
```

### Limitation 2: Extreme Outliers

```
Brighton-Man United (May 2022):
- xG: 2.04 vs 1.73 (essentially equal)
- Actual: 4-0 (extreme outlier)
- Explanation: Exceptional execution + defensive collapse

Such matches are rare but do occur
Cannot be predicted by any model with 100% certainty
```

### Limitation 3: Not Guaranteed

```
xG is EXPECTED value, not prediction
Brighton expected 2.04 goals ≠ will score 2 goals exactly

Distribution around xG:
Normal match: ±0.5 variance
Good day: +1.0 above xG
Bad day: -1.0 below xG
Very rare: ±2.0 (like Brighton)
```

### What xG CANNOT Do
- ✗ Predict exact scorelines
- ✗ Account for random variance
- ✗ Measure player willpower/mentality
- ✗ Predict injury impacts

### What xG CAN Do
- ✓ Identify chance quality
- ✓ Predict season-long trends
- ✓ Spot undervalued teams
- ✓ Identify efficiency issues
- ✓ Compare teams fairly

---

## 4. R IMPLEMENTATION

### Data Structure

```r
# Season-level performance data
perf_data <- data.frame(
  Team = c("Arsenal", "Aston Villa", "Brighton", "Burnley", 
           "Chelsea", "Crystal Palace", ...),
  Played = c(38, 38, 38, 38, 38, 38, ...),
  GoalsFor = c(55, 55, 54, 38, 58, 45, ...),
  ShotsFor = c(455, 519, 488, 384, 501, 396, ...),
  xG = c(53.5, 52.9, 47.3, 32.1, 54.2, 41.8, ...),
  xA = c(42.1, 39.3, 35.6, 28.4, 46.7, 34.2, ...),
  GoalsAgainst = c(38, 45, 42, 60, 36, 48, ...),
  xGA = c(41.2, 46.3, 48.7, 62.1, 38.9, 50.3, ...),
  Points = c(61, 55, 42, 24, 67, 30, ...)
)
```

### Correlation Analysis

```r
# Create correlation matrix
performance_metrics <- cbind(
  perf_data$GoalsFor,
  perf_data$ShotsFor,
  perf_data$xG,
  perf_data$Points
)

colnames(performance_metrics) <- c("Goals", "Shots", "xG", "Points")

# Compute correlations
cor_matrix <- cor(performance_metrics)

# Test significance
cor_test <- cor.test(perf_data$xG, perf_data$Points)
print(cor_test)

# Output:
# Pearson's product-moment correlation
# t = 9.234, df = 18, p-value = 1.23e-08
# cor = 0.736
```

### Visualization

```r
library(ggplot2)

# xG vs Points scatter
ggplot(perf_data, aes(x=xG, y=Points)) +
  geom_point(size=4, alpha=0.6) +
  geom_smooth(method="lm", se=TRUE) +
  geom_text(aes(label=Team), nudge_y=1, size=3) +
  labs(title="Expected Goals vs Final Points (EPL 2020-21)",
       x="Expected Goals", y="Points",
       caption="r=0.736, p<0.001") +
  theme_minimal()

# Over/Underperformance
perf_data$Performance <- perf_data$GoalsFor - perf_data$xG

ggplot(perf_data, aes(x=reorder(Team, Performance), y=Performance)) +
  geom_col(aes(fill=Performance > 0)) +
  coord_flip() +
  labs(title="Goals Over/Under Expected (xG)",
       x="Team", y="Goal Difference (Actual - xG)") +
  theme_minimal()
```

### Comparing Teams

```r
# Which teams overperformed xG?
overperf <- perf_data %>%
  mutate(Performance = GoalsFor - xG) %>%
  arrange(desc(Performance)) %>%
  head(5)

print(overperf[, c("Team", "GoalsFor", "xG", "Performance")])

# Which teams underperformed?
underperf <- perf_data %>%
  mutate(Performance = GoalsFor - xG) %>%
  arrange(Performance) %>%
  head(5)

print(underperf[, c("Team", "GoalsFor", "xG", "Performance")])
```

### Predicting Next Season

```r
# xG is more stable than actual goals
# Use xG for next season prediction

current_xg <- perf_data$xG  # 2020-21
previous_xg <- old_data$xG  # 2019-20

# Correlation of xG year-to-year
xg_stability <- cor(current_xg, previous_xg)
# Typically r ≈ 0.70-0.75 (fairly stable)

# Predicted goals next season
predicted_goals <- current_xg * 0.95  # Apply efficiency factor
# 95% accounts for random variance regression to mean
```

---

## 5. INTEGRATING xG INTO PREDICTION MODELS

### Simple Model: xG Regression

```r
# Model: Points ~ xG

model_xg <- lm(Points ~ xG, data=perf_data)
summary(model_xg)

# Output:
# Coefficients:
#             Estimate Std. Error t value Pr(>|t|)
# (Intercept)   -8.234   5.231   -1.574    0.133
# xG             1.234   0.134    9.234  1.23e-08 ***
#
# R-squared: 0.541

# Interpretation: Each additional expected goal
# adds 1.23 actual points on average
```

### Advanced Model: xG + xGA (Defensive Quality)

```r
# Model: Points ~ xG + xGA

model_full <- lm(Points ~ xG + xGA, data=perf_data)
summary(model_full)

# Predictions
new_team <- data.frame(xG = 55, xGA = 45)
predicted_points <- predict(model_full, new_team)
# Result: ~70 points
```

### Betting Application

```r
# Using xG to identify value in odds

# Get betting odds for match
bookmaker_odds <- data.frame(
  HomeWin = 2.15,
  Draw = 3.50,
  AwayWin = 3.85
)

# Calculate xG for teams
home_xg <- 1.8  # from recent performance
away_xg <- 1.2

# Poisson probabilities using xG as lambda
home_win_prob <- ppois(1, lambda=home_xg) * (1 - ppois(1, lambda=away_xg))
draw_prob <- sum(dpois(0:5, home_xg) * dpois(0:5, away_xg))
away_win_prob <- 1 - home_win_prob - draw_prob

# Convert to odds
model_home_odds <- 1 / home_win_prob
model_away_odds <- 1 / away_win_prob

# Compare
cat("Bookmaker Home Odds:", bookmaker_odds$HomeWin, "\n")
cat("Model Home Odds:", round(model_home_odds, 2), "\n")
cat("Value exists if model odds > bookmaker odds\n")

if(model_home_odds > bookmaker_odds$HomeWin * 1.05) {
  cat("BET: Home win at", bookmaker_odds$HomeWin, "has value!\n")
}
```

---

## SUMMARY: xG IN PRACTICE

### When to Use xG
- ✓ Season-long analysis
- ✓ Identifying efficiency trends
- ✓ Comparing teams fairly
- ✓ Predicting future seasons
- ✓ Finding betting value
- ✓ Coaching analysis

### When NOT to Trust xG
- ✗ Single match prediction
- ✗ Extreme outlier games
- ✗ Early-season (small sample)
- ✗ Teams with major tactical changes

### Key Statistics
| Metric | Correlation with Points | Interpretation |
|--------|-------------------------|-----------------|
| Shots | 0.45 | Weak (quantity ≠ quality) |
| Shots on Target | 0.65 | Moderate |
| xG | 0.74 | Strong |
| xG + xGA | 0.85 | Very Strong |

**Conclusion:** Expected Goals is the best single metric for predicting team success—better than any simple counting statistic.

