# Soccer Analytics: Statistical Tests & Significance

**Source:** Soccer Analytics: An Introduction Using R (Clive Beggs, 2024)  
**Chapter:** 11. Successful Data Analytics  
**Focus:** Statistical rigor in soccer prediction

---

## 1. CORRELATION ANALYSIS

### Pearson's Product-Moment Correlation

#### Mathematical Formula
```
r = Σ[(xᵢ - x̄)(yᵢ - ȳ)] / √[Σ(xᵢ - x̄)² × Σ(yᵢ - ȳ)²]
```

**Range:** -1.0 to +1.0

#### Interpretation Guide

| r Value | Strength | Direction | Example |
|---------|----------|-----------|---------|
| 0.90-1.00 | Very strong | Positive | xG & actual goals |
| 0.70-0.89 | Strong | Positive | Shots on target & points |
| 0.40-0.69 | Moderate | Positive | Pass completion & points |
| 0.10-0.39 | Weak | Positive | Aerial wins & goals |
| -0.10-0.10 | None | None | Random noise |
| -0.40 to -0.10 | Weak | Negative | Losses & confidence |

### Significance Testing

#### Hypothesis Test for Correlation
```
H₀: ρ = 0 (no correlation in population)
H₁: ρ ≠ 0 (correlation exists)

Test Statistic:
t = r√(n-2) / √(1-r²)

Degrees of Freedom: df = n - 2
```

### R Implementation

```r
# Simple correlation
r <- cor(data$ShotsOnTarget, data$Points)
# Result: e.g., r = 0.652

# With significance test
cor_test <- cor.test(data$ShotsOnTarget, data$Points,
                     method="pearson")

# Output interpretation
# Pearson's product-moment correlation
# 
# data:  data$ShotsOnTarget and data$Points
# t = 4.810, df = 38, p-value = 1.22e-05
# alternative hypothesis: true correlation is not equal to 0
# 95% confidence interval: [0.4201 0.7967]
# sample estimates:
#    cor 
#   0.652 

print(cor_test)
```

### Example: Pythagorean Points Correlation (EPL 2020-21)

**Data:**
- Correlation: r = 0.972 (very strong)
- t-statistic: t = 17.608
- Degrees of freedom: df = 18
- p-value: p < 0.001
- 95% CI: [0.9296, 0.9892]

**Interpretation:**
```
"There is an extremely strong positive correlation 
between Pythagorean expected points and actual 
end-of-season points (r=0.972, p<0.001). 
The correlation is statistically significant at 
p<0.001 level, and we are 95% confident the true 
population correlation lies between 0.93 and 0.99."
```

---

## 2. T-TESTS: COMPARING MEANS

### Independent Samples T-Test

#### Formula
```
t = (x̄₁ - x̄₂) / √[s²ₚ(1/n₁ + 1/n₂)]

Pooled variance:
s²ₚ = [(n₁-1)s₁² + (n₂-1)s₂²] / (n₁ + n₂ - 2)

Degrees of freedom: df = n₁ + n₂ - 2
```

### EPL Season Comparison Example

#### Question: Did defensive activity increase between seasons?

**Variable: Intercepts (defensive actions)**

```
Season 1 (2020-21): M = 416.2, SD = 43.7, n = 20
Season 2 (2021-22): M = 574.6, SD = 58.3, n = 20

Null Hypothesis: μ₁ = μ₂ (no difference)
Alternative: μ₁ ≠ μ₂ (seasons differ)
```

#### Calculation
```
Pooled variance:
s²ₚ = [(19×43.7²) + (19×58.3²)] / 38
s²ₚ = [36,412 + 64,687] / 38
s²ₚ = 2,659

Standard error:
SE = √[2,659 × (1/20 + 1/20)]
SE = √[265.9]
SE = 16.31

t-statistic:
t = (416.2 - 574.6) / 16.31
t = -158.4 / 16.31
t = -9.71

df = 38
p-value < 0.001 (highly significant)
```

### R Implementation

```r
# Load season data
season1 <- read.csv("EPL_2020_21.csv")
season2 <- read.csv("EPL_2021_22.csv")

# Perform t-test
t_test <- t.test(season1$Intercepts, season2$Intercepts,
                 paired=FALSE,
                 var.equal=TRUE)

# Display results
print(t_test)

# Extract specific values
t_value <- t_test$statistic
p_value <- t_test$p.value
ci_lower <- t_test$conf.int[1]
ci_upper <- t_test$conf.int[2]

# Report results
cat("t-statistic:", round(t_value, 2), "\n")
cat("p-value:", format.pval(p_value), "\n")
cat("95% CI: [", round(ci_lower, 2), ", ", round(ci_upper, 2), "]\n")
```

### Paired T-Test Example

```r
# Same team before and after coaching change
before <- c(30, 28, 35, 25, 32, 29, 31, 27)  # Goals/season
after <- c(35, 32, 38, 28, 36, 33, 35, 31)

t_test_paired <- t.test(before, after,
                        paired=TRUE)

print(t_test_paired)
# Positive t = before > after (coaching worked)
```

---

## 3. CONFIDENCE INTERVALS

### 95% Confidence Interval for Mean

#### Formula
```
CI = x̄ ± (t_critical × SE)

Where:
SE = s / √n
t_critical = t₀.₀₂₅ from t-distribution with df=n-1
```

### Example: Shots on Target (EPL 2020-21)

```
Data:
Mean = 155.1
SD = 34.0
n = 20 teams

Standard Error:
SE = 34.0 / √20 = 34.0 / 4.47 = 7.61

t-critical (df=19, α=0.05):
t₀.₀₂₅ = 2.093

95% CI:
CI = 155.1 ± (2.093 × 7.61)
CI = 155.1 ± 15.93
CI = [139.2, 171.0]
```

### Interpretation
```
"We are 95% confident that the true population 
mean of shots on target per team per season 
lies between 139.2 and 171.0."
```

### R Implementation

```r
# Calculate confidence interval
data <- c(120, 145, 160, 155, 170, 140, 155, 165, 150, 160,
          145, 135, 170, 155, 165, 150, 140, 145, 160, 155)

n <- length(data)
mean_val <- mean(data)
sd_val <- sd(data)
se <- sd_val / sqrt(n)
t_crit <- qt(0.975, df=n-1)  # 0.975 for two-tailed 95%

ci_lower <- mean_val - (t_crit * se)
ci_upper <- mean_val + (t_crit * se)

cat("Mean:", round(mean_val, 1), "\n")
cat("95% CI: [", round(ci_lower, 1), ", ", round(ci_upper, 1), "]\n")
```

---

## 4. EFFECT SIZES

### Cohen's d (Standardized Difference)

#### Formula
```
d = (x̄₁ - x̄₂) / σₚₒₒₗₑᵈ

Where:
σₚₒₒₗₑᵈ = √[((n₁-1)s₁² + (n₂-1)s₂²) / (n₁ + n₂ - 2)]
```

#### Interpretation
```
d < 0.2:  Small effect (negligible)
d = 0.2-0.5: Small effect
d = 0.5-0.8: Medium effect
d > 0.8:  Large effect
d > 1.2:  Very large effect
```

### Example: Intercepts Between Seasons

```
Season 1: M = 416.2, SD = 43.7, n = 20
Season 2: M = 574.6, SD = 58.3, n = 20

Pooled SD:
σₚ = √[((19×43.7²) + (19×58.3²)) / 38]
σₚ = √[2,659]
σₚ = 51.56

Cohen's d:
d = (574.6 - 416.2) / 51.56
d = 158.4 / 51.56
d = 3.07 (Very large effect)
```

### Interpretation
```
"The difference between seasons is not just 
statistically significant (p<0.001), but also 
practically meaningful with a very large effect 
size (d=3.07). Defensive activity more than 
tripled between seasons—a substantial change."
```

### R Implementation

```r
# Calculate Cohen's d
cohens_d <- function(x1, x2) {
  n1 <- length(x1)
  n2 <- length(x2)
  
  s_pooled <- sqrt(((n1-1)*sd(x1)^2 + (n2-1)*sd(x2)^2) / (n1 + n2 - 2))
  
  d <- (mean(x1) - mean(x2)) / s_pooled
  return(d)
}

d <- cohens_d(season1$Intercepts, season2$Intercepts)
print(d)  # 3.07
```

---

## 5. MULTIPLE COMPARISONS PROBLEM

### The Problem: Inflated Type I Error

```
Scenario: Testing 11 performance variables at α=0.05

Expected false positives:
= 11 tests × 0.05 α-level
= 0.55 false positives expected

Actual family-wise error rate:
P(at least one Type I error) = 1 - (0.95)¹¹
                               ≈ 0.44 (44%)

PROBLEM: True error rate 44%, not 5%!
```

### Solution 1: Bonferroni Correction

#### Formula
```
αₐⱼᵤₛₜₑᵈ = α / m

Where m = number of comparisons
```

#### Example
```
11 variables tested
α_original = 0.05
α_adjusted = 0.05 / 11 = 0.0045

Only p < 0.0045 considered significant
```

#### Criticism
```
Very conservative—loses statistical power
May miss real effects (Type II error)
```

### Solution 2: Benjamini-Hochberg FDR

#### Method
```
1. Rank p-values: p₁ ≤ p₂ ≤ ... ≤ pₘ
2. For largest i where pᵢ ≤ (i/m)α:
   Reject H₀ for tests 1 to i
```

#### Advantage
```
Less conservative than Bonferroni
Better balance of Type I and Type II errors
Better control of false discovery rate
```

### R Implementation

```r
# Multiple t-tests (season comparison)
variables <- c("Shots", "SoT", "Passes", "Tackles", 
               "Dribbles", "Intercepts", "Crosses",
               "Aerial_Won", "Aerial_Lost", "Pass_Pct", "TSR")

p_values <- sapply(variables, function(var) {
  t_test <- t.test(season1[[var]], season2[[var]])
  return(t_test$p.value)
})

# Bonferroni correction
alpha <- 0.05
bonferroni_alpha <- alpha / length(variables)
significant_bonf <- p_values < bonferroni_alpha

# Benjamini-Hochberg FDR
p_adjusted <- p.adjust(p_values, method="BH")
significant_bh <- p_adjusted < 0.05

# Display results
results <- data.frame(
  Variable = variables,
  p_value = round(p_values, 4),
  Bonferroni_Sig = significant_bonf,
  BH_FDR_Adj = round(p_adjusted, 4),
  BH_Sig = significant_bh
)

print(results)
```

---

## 6. P-VALUES: MISINTERPRETATION WARNING

### Common Misunderstanding

```
❌ WRONG: "p=0.03 means there's only 3% probability 
          results occurred by random chance"

✓ CORRECT: "If null hypothesis true, there's 3% 
           probability of observing this result 
           (or more extreme)"
```

### Why This Matters

#### Example: Same p-value, Different Evidence

**Scenario 1: Small Sample**
```
Team A vs Team B performance
n = 10 teams per group
t-test: p = 0.05
Conclusion: Weak evidence of difference
```

**Scenario 2: Large Sample**
```
Team A vs Team B performance (100 seasons)
n = 100 seasons per group
t-test: p = 0.05
Conclusion: Strong evidence of difference
```

**Both have p=0.05, but very different strength of evidence!**

### P-value Alternatives

**1. Effect Sizes (always report)**
```r
cohen_d <- (mean1 - mean2) / pooled_sd
print(paste("Effect size (d):", round(cohen_d, 2)))
```

**2. Confidence Intervals**
```r
ci <- t.test(x, y)$conf.int
print(paste("95% CI: [", round(ci[1], 2), ", ", round(ci[2], 2), "]"))
```

**3. Sample Size Justification**
```r
# Power analysis
library(pwr)
effect_size <- 0.5  # Medium effect
pwr.t.test(d=effect_size, power=0.80, sig.level=0.05)
```

---

## 7. STATISTICAL SIGNIFICANCE vs PRACTICAL SIGNIFICANCE

### Key Distinction

| Aspect | Statistical | Practical |
|--------|-------------|-----------|
| **Definition** | p < 0.05 | Does effect matter? |
| **Question** | Is it real? | Is it important? |
| **Example** | p=0.002 | But d=0.1 (tiny effect) |
| **Sample Size** | Affects p-value | Doesn't affect magnitude |

### Example: Goal Scoring Rate

```
Team A average goals: 1.85 per match
Team B average goals: 1.81 per match
Difference: 0.04 goals (one goal per 25 matches)

With n=380 matches per season:
t-test p-value: p = 0.043 ✓ Statistically significant

Practical significance?
NO! - 0.04 goals per match is negligible difference
Effect size d = 0.08 (very small)
```

### Recommendation

```
Always report:
1. Test statistic and p-value
2. Effect size (Cohen's d or correlation r)
3. Confidence intervals
4. Sample size
5. Interpretation in practical terms
```

---

## SUMMARY: STATISTICAL TESTING FRAMEWORK

### Decision Tree

```
1. STATE HYPOTHESIS
   - H₀: No difference/relationship
   - H₁: Difference/relationship exists

2. CHOOSE TEST
   - Correlation: cor.test()
   - Compare means: t.test()
   - Multiple groups: ANOVA, Kruskal-Wallis
   - Categorical: chi-square

3. CHECK ASSUMPTIONS
   - Normality (Shapiro-Wilk)
   - Equal variances (Levene's test)
   - Independence (no clustering)

4. SET α LEVEL
   - Standard: α = 0.05
   - Conservative: α = 0.01
   - Multiple comparisons: Bonferroni/FDR

5. REPORT RESULTS
   - Test statistic
   - p-value
   - Effect size (d, r, η²)
   - Confidence intervals
   - Sample size
   - Practical interpretation

6. INTERPRET CAREFULLY
   - Statistical ≠ Practical significance
   - Small p-value ≠ large effect
   - Consider power and sample size
```

---

## KEY SOCCER ANALYTICS STATISTICS

| Analysis | Test | Key Result (EPL 2020-21) | Interpretation |
|----------|------|--------------------------|-----------------|
| Pythagorean vs Actual | Correlation | r=0.972, p<0.001 | Excellent predictor |
| Intercepts Season 1 vs 2 | Independent t-test | t=-9.71, p<0.001, d=3.07 | Massive increase |
| SoT and Points | Correlation | r=0.652, p<0.001 | Strong relationship |
| Home advantage goals | t-test | 1.568 vs 1.253 goals, p<0.001 | 25% home bonus |

