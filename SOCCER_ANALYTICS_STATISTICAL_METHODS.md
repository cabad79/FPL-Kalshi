# Soccer Analytics: Statistical Methods & Techniques

**Source:** Soccer Analytics: An Introduction Using R (Clive Beggs, 2024)  
**Chapters:** 5, 6, 10, 11  
**Focus:** Advanced statistical approaches for soccer prediction and analysis

---

## 1. LINEAR REGRESSION FOR MATCH PERFORMANCE

### Mathematical Foundation

#### General Linear Model
```
y = b₀ + b₁x₁ + b₂x₂ + ... + bₖxₖ + ε
```

Where:
- **y** = response variable (Points earned)
- **b₀** = intercept
- **b₁, b₂, ..., bₖ** = regression coefficients
- **x₁, x₂, ..., xₖ** = predictor variables
- **ε** = error term (residual)

#### Ordinary Least Squares (OLS)
```
Minimize: SSE = Σ(yᵢ - ŷᵢ)²
```

**Coefficient of Determination (R²):**
```
R² = 1 - (SSE / SST)
   = Σ(ŷᵢ - ȳ)² / Σ(yᵢ - ȳ)²
```

**Interpretation:**
- R² = 0.85 → Model explains 85% of variance
- R² = 0.50 → Model explains 50% of variance
- R² = 0.10 → Model explains 10% of variance

### Application: EPL Match Performance

#### Predictor Variables (2020-21, 2021-22)

| Variable | Description | Typical Range |
|----------|-------------|----------------|
| Shots | Total shots attempted | 300-550/season |
| SoT | Shots on target | 100-200/season |
| Shot Distance | Average distance (yards) | 16-18 |
| Pass Completion | Total passes completed | 14,000-16,000 |
| Dribbles | Successful dribbles | 300-400 |
| Tackles | Defensive tackles | 600-700 |
| Crosses | Cross attempts | 400-500 |
| Intercepts | Interceptions made | 400-600 |
| Aerial Won | Aerial duels won | 650-700 |

#### Descriptive Statistics Comparison

**2020-21 vs 2021-22 EPL:**

| Metric | S1 Mean | S2 Mean | p-value | Significant? |
|--------|---------|---------|---------|--------------|
| Intercepts | 416.2 | 574.6 | <0.001 | **Yes** |
| Dribbles | 370.7 | 320.5 | 0.012 | **Yes** |
| Tackles | 645.4 | 674.7 | 0.257 | No |
| Shot Distance | 16.9 | 16.8 | 0.777 | No |
| Pass Completion | 15355.9 | 14717.9 | 0.606 | No |

**Key Finding:** Teams increased interceptions dramatically in season 2 (38% increase).

### R Implementation

#### Data Loading and Exploration
```r
# Load EPL performance data
regdata <- read.csv("EPL_regression_2020_2021.csv")

# Split by season
season1 <- regdata[regdata$Season == 2020,]
season2 <- regdata[regdata$Season == 2021,]

# Dimension check
dim(season1)  # Should be 20 teams × 11 variables
dim(season2)

# Select performance metrics
perf_cols <- c("Points", "Shots", "SoT", "ShotDist", 
               "PassComp", "Dribbles", "Tackles", "Crosses",
               "Intercepts", "AerialWon", "AerialLost")

s1_perf <- season1[, perf_cols]
s2_perf <- season2[, perf_cols]
```

#### Descriptive Statistics
```r
library(psych)

# Generate summaries
summary_s1 <- describe(s1_perf)
summary_s2 <- describe(s2_perf)

# Compare means with t-tests
t_results <- sapply(2:11, function(i) {
  test <- t.test(s1_perf[,i], s2_perf[,i], paired=FALSE)
  return(c(mean1=mean(s1_perf[,i]),
           mean2=mean(s2_perf[,i]),
           t_value=test$statistic,
           p_value=test$p.value,
           sig=ifelse(test$p.value < 0.05, "***", "")))
})

print(t_results)
```

#### Simple Linear Regression
```r
# Points ~ Shots on Target
model1 <- lm(Points ~ SoT, data=regdata)
summary(model1)

# Output:
# Coefficients:
#             Estimate Std. Error t value Pr(>|t|)
# (Intercept)  -5.234    10.123   -0.516    0.608
# SoT           0.327     0.068    4.810   1.22e-05 ***
#
# R-squared: 0.424
# Adjusted R-squared: 0.420
# F-statistic: 23.14 on 1 and 38 DF, p-value: 1.22e-05
```

**Interpretation:**
- Each additional shot-on-target adds **0.327 points**
- Model explains **42.4%** of points variance
- Relationship highly significant (p < 0.001)

#### Multiple Linear Regression
```r
# Multiple predictors
model2 <- lm(Points ~ SoT + PassComp + Tackles + Dribbles + Intercepts, 
             data=regdata)
summary(model2)

# Extract coefficients with confidence intervals
coef_table <- data.frame(
  Coefficient = names(coef(model2)),
  Estimate = coef(model2),
  CI_Lower = coef(model2) - 1.96*summary(model2)$coefficients[,2],
  CI_Upper = coef(model2) + 1.96*summary(model2)$coefficients[,2]
)

print(coef_table)
```

### Variable Importance Analysis

#### Method 1: Standardized Coefficients
```r
# Standardize all variables
model_std <- lm(scale(Points) ~ scale(SoT) + scale(PassComp) + 
                               scale(Tackles) + scale(Intercepts),
                data=regdata)

# Coefficients now directly comparable
std_coefs <- coef(model_std)[-1]  # Remove intercept
std_coefs_ordered <- std_coefs[order(abs(std_coefs), decreasing=TRUE)]

barplot(std_coefs_ordered, 
        main="Standardized Coefficient Importance",
        horiz=TRUE, las=1)
```

#### Method 2: Correlation with Response
```r
# Simple correlation
correlations <- cor(regdata[, c("Points", "SoT", "PassComp", 
                               "Tackles", "Intercepts")])
points_cor <- correlations["Points", -1]
points_cor_ordered <- sort(abs(points_cor), decreasing=TRUE)

print(points_cor_ordered)
# Typical result:
# SoT: 0.65, PassComp: 0.58, Intercepts: 0.42, Tackles: 0.35
```

#### Method 3: Random Forest Feature Importance
```r
library(randomForest)

# Fit random forest
rf_model <- randomForest(Points ~ SoT + PassComp + Tackles + 
                                  Dribbles + Intercepts,
                         data=regdata,
                         ntree=500,
                         importance=TRUE)

# Get importance
importance_vals <- importance(rf_model)
importance_vals <- importance_vals[order(-importance_vals[,1]),]

print(importance_vals)
# Higher %IncMSE = more important variable
```

### Model Diagnostics

#### Checking Assumptions
```r
# Create diagnostic plots
par(mfrow=c(2,2))
plot(model1)

# Individual plots:

# 1. Linearity: Residuals vs Fitted
plot(fitted(model1), residuals(model1),
     main="Linearity Check",
     xlab="Fitted Values", ylab="Residuals")
abline(h=0, col="red", lty=2)
# Should show random scatter (no pattern)

# 2. Normality: Q-Q Plot
qqnorm(residuals(model1))
qqline(residuals(model1), col="red")
# Points should follow diagonal line

# 3. Homoscedasticity: Scale-Location
plot(fitted(model1), sqrt(abs(residuals(model1))),
     main="Homoscedasticity Check")
# Should show constant variance (no funnel shape)

# 4. Influence: Residuals vs Leverage
plot(hatvalues(model1), residuals(model1),
     main="Influence Check")
# Identify outliers and influential points
```

#### Formal Tests
```r
# Normality test (Shapiro-Wilk)
shapiro.test(residuals(model1))

# Homoscedasticity test (Breusch-Pagan)
library(lmtest)
bptest(model1)

# Check for multicollinearity (VIF)
library(car)
vif(model2)
# VIF > 10 indicates problematic multicollinearity
```

### Prediction with Regression

#### Point Estimation
```r
# New team performance data
newdata <- data.frame(
  SoT = 155,
  PassComp = 15000,
  Tackles = 650,
  Dribbles = 350,
  Intercepts = 500
)

# Predict points
pred_points <- predict(model2, newdata, type="response")
# Result: e.g., 57.3 points
```

#### Interval Predictions
```r
# Confidence Interval (for mean prediction)
ci_pred <- predict(model2, newdata, 
                   interval="confidence", 
                   level=0.95)
# 95% CI: [53.2, 61.4]

# Prediction Interval (for individual prediction)
pi_pred <- predict(model2, newdata,
                   interval="prediction",
                   level=0.95)
# 95% PI: [48.1, 66.5] (wider, accounts for individual variation)

# Combine in data frame
predictions <- data.frame(
  Fit = pred_points,
  Lower_CI = ci_pred[1,2],
  Upper_CI = ci_pred[1,3],
  Lower_PI = pi_pred[1,2],
  Upper_PI = pi_pred[1,3]
)

print(predictions)
```

---

## 2. PYTHAGOREAN EXPECTED POINTS

### Mathematical Foundation

#### Formula
```
ptsexp = a × [GF^b / (GF^c + GA^d)] × m
```

Where:
- **ptsexp** = expected points
- **GF** = goals for (scored)
- **GA** = goals against (conceded)
- **m** = matches played
- **a, b, c, d** = empirical coefficients
- **Beggs coefficients:** a=2.78, b=1.24, c=1.24, d=1.25

#### Pythagorean Goal Ratio
```
PythagFrac = GF^b / (GF^c + GA^d)
```

**Interpretation:**
- > 0.5 = Winning team
- ≈ 0.5 = Break-even
- < 0.5 = Losing team

### Application Example

#### 2020-21 EPL Season Validation

| Rank | Club | GF | GA | Actual Pts | Pythag Frac | Pythag Pts | Error |
|------|------|----|----|------------|------------|-----------|-------|
| 1 | Man City | 83 | 32 | 86 | 0.759 | 80.2 | +5.8 |
| 2 | Man United | 73 | 44 | 74 | 0.643 | 68.0 | +6.0 |
| 3 | Liverpool | 68 | 42 | 69 | 0.636 | 67.2 | +1.8 |
| 4 | Chelsea | 58 | 36 | 67 | 0.635 | 67.1 | -0.1 |
| 5 | Leicester | 68 | 50 | 66 | 0.585 | 61.8 | +4.2 |

**Statistical Validation:**
```
Correlation: r = 0.972
t-test: t = 17.608, df = 18, p < 0.001
95% CI: [0.9296, 0.9892]
```

### R Implementation

#### User-Defined Function
```r
pythag_pred <- function(PLD, GF, GA, PTS, nGames=38){
  # Coefficients
  a = 2.78
  b = 1.24
  c = 1.24
  d = 1.25
  
  # Pythagorean fraction
  pythag_frac <- (GF^b) / ((GF^c) + (GA^d))
  
  # Points after PLD matches
  pythag_pts <- a * pythag_frac * PLD
  
  # Over/under-performance
  pythag_diff <- PTS - pythag_pts
  
  # Available points
  points_avail <- (nGames - PLD) * 3
  
  # Predicted points from remaining
  pred_pts <- pythag_frac * a * (nGames - PLD)
  
  # Final predictions
  pred_total <- PTS + pred_pts
  pythag_total <- pythag_pts + pred_pts
  
  return(list(
    PLD = PLD,
    GF = GF,
    GA = GA,
    PTS = PTS,
    PythagFrac = pythag_frac,
    PythagPts = pythag_pts,
    PythagDiff = pythag_diff,
    PointsAvail = points_avail,
    PredPts = pred_pts,
    PredTotal = pred_total,
    PythagTotal = pythag_total
  ))
}
```

#### In-Season Prediction Example
```r
# Liverpool after 10 matches (2020-21)
# Actual: 10 played, 22 GF, 17 GA, 21 points

result <- pythag_pred(PLD=10, GF=22, GA=17, PTS=21, nGames=38)

# Step 1: Pythagorean fraction
pythag_frac <- result$PythagFrac  # 22^1.24 / (22^1.24 + 17^1.25) = 0.555

# Step 2: Expected pts after 10
pythag_pts_10 <- result$PythagPts  # 2.78 × 0.555 × 10 = 15.4

# Step 3: Over-performance
pythag_diff <- result$PythagDiff  # 21 - 15.4 = +5.6 points

# Step 4: Points from remaining 28 matches
remaining_pts <- result$PredPts  # 2.78 × 0.555 × 28 = 43.0

# Step 5: End-of-season predictions
pred_total <- result$PredTotal     # 21 + 43.0 = 64.0
pythag_total <- result$PythagTotal # 15.4 + 43.0 = 58.4

# Display results
results_df <- data.frame(
  Metric = names(result),
  Value = unlist(result)
)
print(results_df)
```

### Prediction Accuracy Over Season

#### Accuracy by Round (2020-21 EPL)

| Round | Matches Played | MAE | Best Case | Worst Case |
|-------|---------------|----|-----------|------------|
| 10 | 10 | 9.2 | ±6 | ±15 |
| 19 | 19 | 6.1 | ±4 | ±10 |
| 29 | 29 | 2.8 | ±2 | ±5 |
| 38 | 38 | 0.0 | Actual | - |

**Pattern:** Early predictions unreliable; mid-season becomes reasonable; late season very reliable

---

## 3. ADVANCED RANKING SYSTEMS

### Colley Algorithm

#### Win-Loss Vector
```
vᵢ = 1 + 0.5(wᵢ - lᵢ)
```

#### Colley Matrix
```
Cᵢⱼ = { 2 + pᵢ    if i = j
      { -pᵢⱼ     if i ≠ j
```

#### Solution
```
rc = C⁻¹v  (matrix inverse × vector)
```

### Massey Algorithm

#### Point Differential
```
dᵢⱼ = (goals_i - goals_j)
```

#### Massey Matrix
```
Mᵢⱼ = { matches_i       if i = j
      { -matches_ij    if i ≠ j
```

### Elo Rating System

#### Rating Update
```
Rₙₑw = Rₒₗᵈ + K(W - E)
```

#### Expected Probability
```
E = 1 / (1 + 10^((Rₒₚₚ - Rₜₑₐₘ)/400))
```

#### Home Advantage Adjustment
```
E_home = 1 / (1 + 10^((Rₒₚₚ + 40 - Rₜₑₐₘ)/400))
```

#### K-Factor Strategy
```
K = { 8   if R ≥ 2400 (super-elite)
    { 12  if R ≥ 2000
    { 16  if R ≥ 1600
    { 24  if R < 1600
    { 32  if new player
```

---

## Summary Table

| Method | Complexity | Speed | Accuracy | Use Case |
|--------|-----------|-------|----------|----------|
| Linear Regression | Low | Fast | 55-60% | Performance explanation |
| Pythagorean | Medium | Fast | 60-70% | Season prediction |
| Colley | High | Slow | 65% | Ranking systems |
| Massey | High | Slow | 65% | Goal differential |
| Elo | Medium | Fast | 58-62% | Rating updates |

