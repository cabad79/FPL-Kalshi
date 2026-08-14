# Soccer Analytics: R Code Implementations

**Source:** Soccer Analytics: An Introduction Using R (Clive Beggs, 2024)  
**Chapters:** 2-3, 6-9  
**Focus:** Complete, runnable R code examples

---

## 1. DATA STRUCTURES AND MANIPULATION

### Vectors
```r
# Creating vectors
goals <- c(1, 2, 0, 3, 1, 2)
teams <- c("Man United", "Chelsea", "Liverpool", "Arsenal", "Man City", "Tottenham")

# Vector operations
goals + 1                    # Add 1 to each element
goals * 2                    # Multiply each element
max(goals)                   # Maximum value
mean(goals)                  # Mean
sum(goals)                   # Sum

# Vector indexing
goals[1]                     # First element (1-indexed in R)
goals[2:4]                   # Elements 2, 3, 4
goals[-1]                    # All except first
goals[goals > 1]             # Elements > 1
```

### Data Frames
```r
# Creating data frame
match_data <- data.frame(
  HomeTeam = c("Man United", "Chelsea", "Liverpool"),
  AwayTeam = c("Arsenal", "Man City", "Tottenham"),
  HomeGoals = c(2, 3, 2),
  AwayGoals = c(1, 1, 0),
  Date = as.Date(c("2021-08-13", "2021-08-14", "2021-08-15"))
)

# Exploring structure
head(match_data)             # First 6 rows
tail(match_data)             # Last 6 rows
str(match_data)              # Data structure
names(match_data)            # Column names
nrow(match_data)             # 3 rows
ncol(match_data)             # 5 columns
dim(match_data)              # Dimensions: 3 x 5

# Accessing columns
match_data$HomeTeam          # Column as vector
match_data[, "HomeGoals"]    # Alternative syntax
match_data[1, ]              # First row
match_data[1, 2]             # Cell: row 1, column 2
```

### Matrix Operations
```r
# Creating matrices
m <- matrix(0, nrow=4, ncol=4)
m <- matrix(1:16, nrow=4, ncol=4)

# Assigning row/column names
rownames(m) <- c("A", "B", "C", "D")
colnames(m) <- c("A", "B", "C", "D")

# Matrix operations
m[1, 2]                      # Access cell
m[1, ] <- 5                  # Set row to 5
m[, 3] <- 2:5                # Set column
t(m)                         # Transpose
det(m)                       # Determinant
solve(m)                     # Matrix inverse
m %*% m                      # Matrix multiplication
```

---

## 2. DATA IMPORT/EXPORT

### Reading CSV Files
```r
# From local file
local_data <- read.csv("matches.csv")

# From internet URL
epl_2018_19 <- read.csv('https://www.football-data.co.uk/mmz4281/1819/E0.csv')

# Inspect imported data
head(epl_2018_19, 10)        # First 10 rows
tail(epl_2018_19)
summary(epl_2018_19)         # Statistical summary
```

### Writing Results
```r
# Save data frame to CSV
write.csv(results, "predictions.csv", row.names=FALSE)

# Save R objects
save(model_obj, file="model.RData")
load("model.RData")
```

---

## 3. SUBSETTING AND FILTERING

### Base R Methods
```r
# Filter rows by condition
epl_2018 <- data[data$Season == 2018, ]
home_wins <- data[data$Result == "H", ]
draws <- data[data$Result == "D", ]

# Select specific columns
subset_cols <- data[, c("Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG")]

# Multiple conditions
man_utd_home <- data[data$HomeTeam == "Man United" & data$FTHG > 2, ]
```

### dplyr Methods (Tidyverse)
```r
library(dplyr)

# Filter rows
filtered <- data %>%
  filter(Season == 2018, Result == "H")

# Select columns
selected <- data %>%
  select(Date, HomeTeam, AwayTeam, FTHG, FTAG)

# Create new variables
with_diff <- data %>%
  mutate(GoalDiff = FTHG - FTAG,
         TotalShots = HS + AS)

# Arrange (sort)
sorted <- data %>%
  arrange(desc(FTHG))  # Descending

# Combine operations
result <- data %>%
  filter(Season == 2018) %>%
  mutate(HomeAdvantage = ifelse(FTHG > FTAG, 1, 0)) %>%
  select(HomeTeam, AwayTeam, HomeAdvantage) %>%
  arrange(HomeTeam)
```

---

## 4. CREATING DERIVED VARIABLES

```r
# Goal difference
data$GoalDiff <- data$FTHG - data$FTAG

# Match result (if not provided)
data$Result <- ifelse(data$FTHG > data$FTAG, "H",
                 ifelse(data$FTHG < data$FTAG, "A", "D"))

# Points awarded
data$Points <- ifelse(data$Result == "H", 3,
                 ifelse(data$Result == "D", 1, 0))

# Total shots ratio
data$TSR <- data$HS / (data$HS + data$AS)

# Pass completion percentage
data$PassComplPct <- data$PassCompleted / data$PassAttempted * 100

# Shot on target ratio
data$SoTRatio <- data$SoT / data$Shots
```

---

## 5. HANDLING MISSING DATA

```r
# Check for missing values
summary(data)
colSums(is.na(data))
na.exclude(data)

# Remove rows with missing values
clean_data <- na.omit(data)
clean_data <- data[complete.cases(data), ]

# Impute with mean
data$Shots[is.na(data$Shots)] <- mean(data$Shots, na.rm=TRUE)

# Impute with group mean
library(dplyr)
data <- data %>%
  group_by(Team) %>%
  mutate(Shots = ifelse(is.na(Shots), mean(Shots, na.rm=TRUE), Shots))
```

---

## 6. LOOPS AND CONDITIONALS

### For Loops
```r
# Simple loop
for(i in 1:10) {
  print(i^2)
}

# Loop through data frame
for(i in 1:nrow(data)) {
  team <- data$HomeTeam[i]
  goals <- data$FTHG[i]
  print(paste(team, "scored", goals))
}

# Nested loops
results <- matrix(0, nrow=20, ncol=20)
for(i in 1:20) {
  for(j in 1:20) {
    results[i, j] <- i * j
  }
}
```

### If Statements
```r
# Simple conditional
if(team_rating > 1600) {
  print("Strong team")
} else {
  print("Developing team")
}

# Else-if chains
if(points >= 90) {
  rating <- "Excellent"
} else if(points >= 70) {
  rating <- "Good"
} else if(points >= 50) {
  rating <- "Average"
} else {
  rating <- "Poor"
}

# Vectorized conditional (ifelse)
data$Category <- ifelse(data$Points >= 70, "Top",
                   ifelse(data$Points >= 50, "Mid", "Bottom"))
```

---

## 7. APPLY FAMILY FUNCTIONS

```r
# Apply function to rows
row_means <- apply(matrix_data, MARGIN=1, FUN=mean)

# Apply to columns
col_sums <- apply(data[, 3:8], MARGIN=2, FUN=sum)

# lapply: returns list
team_stats <- lapply(unique(data$Team), function(x) {
  team_data <- data[data$Team == x, ]
  return(list(
    team = x,
    matches = nrow(team_data),
    avg_goals = mean(team_data$Goals)
  ))
})

# sapply: returns vector/matrix (simplified)
goal_totals <- sapply(unique(data$Team), function(x) {
  sum(data$Goals[data$Team == x])
})

# mapply: multiple arguments
distances <- mapply(function(x, y) {
  sqrt(x^2 + y^2)  # Euclidean distance
}, c(3, 4, 5), c(4, 3, 12))
```

---

## 8. VISUALIZATION

### Base R Plotting
```r
# Scatter plot
plot(data$ShotsOnTarget, data$Points,
     main="Shots on Target vs Points",
     xlab="Shots on Target", 
     ylab="Points",
     col="blue", pch=16)
abline(lm(Points ~ ShotsOnTarget, data=data), col="red")

# Line plot
plot(1:38, cumulative_points, type="l",
     main="Cumulative Points Over Season",
     xlab="Match Day", 
     ylab="Points")

# Histogram
hist(data$Goals, breaks=15,
     main="Distribution of Goals Scored",
     xlab="Goals", col="steelblue")

# Boxplot
boxplot(Points ~ Team, data=data,
        main="Points Distribution by Team",
        las=2)

# Bar chart
barplot(table(data$Result),
        main="Match Outcomes",
        names.arg=c("Away Win", "Draw", "Home Win"),
        col=c("red", "gray", "green"))
```

### ggplot2 (Modern Graphics)
```r
library(ggplot2)

# Scatter with regression line
ggplot(data, aes(x=ShotsOnTarget, y=Points)) +
  geom_point(size=3, alpha=0.6) +
  geom_smooth(method="lm", se=TRUE, color="red") +
  labs(title="SoT vs Points",
       x="Shots on Target",
       y="Points",
       subtitle="EPL 2020-21") +
  theme_minimal()

# Boxplot by team
ggplot(data, aes(x=Team, y=Goals)) +
  geom_boxplot(fill="steelblue") +
  geom_point(alpha=0.3) +
  coord_flip() +
  labs(title="Goals Distribution by Team")

# Faceted plot (multiple subplots)
ggplot(data, aes(x=MatchDay, y=Points)) +
  geom_line() +
  facet_wrap(~Team) +
  labs(title="Points Over Season by Team")
```

---

## 9. STATISTICAL TESTS

### Correlation
```r
# Pearson correlation
cor(data$ShotsOnTarget, data$Points)  # r value only
cor.test(data$ShotsOnTarget, data$Points)  # With p-value

# Correlation matrix
cor_matrix <- cor(data[, c("Goals", "ShotsOnTarget", "PassCompletion")])
print(cor_matrix)

# Visualize correlations
library(corrplot)
corrplot(cor_matrix, method="circle")
```

### T-Tests
```r
# Independent samples t-test
t.test(season1$Points, season2$Points, 
       paired=FALSE, var.equal=TRUE)

# Paired t-test
t.test(before$Performance, after$Performance, 
       paired=TRUE)

# One-sample t-test
t.test(data$Points, mu=52.5)  # Test if mean = 52.5
```

### Chi-Square Test
```r
# Test of independence
contingency <- table(data$Result, data$Team)
chisq.test(contingency)
```

---

## 10. REGRESSION MODELS

### Simple Linear Regression
```r
# Fit model
model1 <- lm(Points ~ ShotsOnTarget, data=data)

# View results
summary(model1)
coef(model1)           # Coefficients only
confint(model1)        # Confidence intervals
```

### Multiple Linear Regression
```r
model2 <- lm(Points ~ SoT + PassCompletion + Tackles + 
                     Interceptions + AerialWons,
             data=data)
summary(model2)

# Model comparison
anova(model1, model2)  # ANOVA comparison
AIC(model1, model2)    # AIC comparison
```

### Poisson Regression (GLM)
```r
# Convert to long format
long_data <- rbind(
  data.frame(Home=1, Team=data$HomeTeam, 
             Opponent=data$AwayTeam, Goals=data$FTHG),
  data.frame(Home=0, Team=data$AwayTeam, 
             Opponent=data$HomeTeam, Goals=data$AWHG)
)

# Fit Poisson model
pois_model <- glm(Goals ~ Home + Team + Opponent,
                  family=poisson(link=log),
                  data=long_data)

summary(pois_model)

# Make predictions
pred <- predict(pois_model, 
                data.frame(Home=1, Team="Liverpool", 
                          Opponent="Arsenal"),
                type='response')
```

---

## 11. NETWORK ANALYSIS

### Adjacency Matrix Operations
```r
# Create adjacency matrix from pass data
pass_matrix <- read.csv("passes.csv", row.names=1)
pass_matrix <- as.matrix(pass_matrix)

# Analyze network
library(igraph)
graph <- graph_from_adjacency_matrix(pass_matrix, 
                                    weighted=TRUE,
                                    directed=TRUE)

# Centrality measures
degree_centrality <- degree(graph)
weighted_degree <- strength(graph)
betweenness <- betweenness(graph)
closeness <- closeness(graph)

# Create summary
network_stats <- data.frame(
  Player = names(degree_centrality),
  Degree = as.numeric(degree_centrality),
  WeightedDegree = as.numeric(weighted_degree),
  Betweenness = as.numeric(betweenness),
  Closeness = as.numeric(closeness)
)

print(network_stats[order(-network_stats$WeightedDegree), ])
```

### Network Visualization
```r
library(qgraph)

qgraph(pass_matrix,
       labels = rownames(pass_matrix),
       directed = TRUE,
       edge.width = 0.5,
       label.cex = 1.5,
       color = "lightblue",
       edge.color = "gray")
```

---

## 12. MACHINE LEARNING

### Random Forest
```r
library(randomForest)

# Prepare data
train_data <- data[1:300, ]
test_data <- data[301:380, ]

# Fit model
rf_model <- randomForest(Result ~ PSH + PSD + PSA + B365H + ...,
                         data = train_data,
                         ntree = 500,
                         mtry = sqrt(ncol(train_data)-1),
                         importance = TRUE)

# Predictions
predictions <- predict(rf_model, test_data)
prob_predictions <- predict(rf_model, test_data, type="prob")

# Feature importance
importance_vals <- importance(rf_model)
print(importance_vals[order(-importance_vals[,1]), ])
```

### Conditional Inference Trees
```r
library(party)

# Fit model
ct_model <- ctree(Result ~ PSH + PSD + PSA,
                  data = train_data,
                  controls = ctree_control(mincriterion = 0.95,
                                          minsplit = 20))

# Visualize tree
plot(ct_model, main="Match Prediction Decision Tree")

# Make predictions
ct_predictions <- predict(ct_model, test_data)
```

---

## 13. ELO RATING UPDATES

```r
# Initial ratings
teams <- c("Arsenal", "Chelsea", "Liverpool", "Man City")
ratings <- data.frame(Team = teams, Rating = rep(1500, 4))

# Update function
elo_update <- function(R_team, R_opp, result, K, home_advantage=0) {
  R_adj_opp <- R_opp + home_advantage
  E <- 1 / (1 + 10^((R_adj_opp - R_team) / 400))
  R_new <- R_team + K * (result - E)
  return(R_new)
}

# Apply to matches
matches <- data.frame(
  Home = c("Arsenal", "Chelsea", "Liverpool"),
  Away = c("Chelsea", "Arsenal", "Man City"),
  Result_Home = c(1, 0, 0.5)  # 1=home win, 0.5=draw, 0=away win
)

for(i in 1:nrow(matches)) {
  home_team <- matches$Home[i]
  away_team <- matches$Away[i]
  result <- matches$Result_Home[i]
  
  idx_home <- which(ratings$Team == home_team)
  idx_away <- which(ratings$Team == away_team)
  
  R_home <- ratings$Rating[idx_home]
  R_away <- ratings$Rating[idx_away]
  
  R_home_new <- elo_update(R_home, R_away, result, K=24, home_advantage=40)
  R_away_new <- elo_update(R_away, R_home, 1-result, K=24, home_advantage=40)
  
  ratings$Rating[idx_home] <- R_home_new
  ratings$Rating[idx_away] <- R_away_new
}

print(ratings[order(-ratings$Rating), ])
```

---

## 14. SUMMARY: COMPLETE WORKFLOW

```r
# 1. Load and explore
data <- read.csv('https://www.football-data.co.uk/mmz4281/1819/E0.csv')
head(data)
summary(data)

# 2. Clean and prepare
data <- na.omit(data)
data$GoalDiff <- data$FTHG - data$FTAG
data$TSR <- data$HS / (data$HS + data$AS)

# 3. Exploratory analysis
library(ggplot2)
ggplot(data, aes(x=HS, y=FTHG)) + geom_point() + geom_smooth(method="lm")

# 4. Statistical tests
cor.test(data$HS, data$FTHG)

# 5. Fit model
model <- lm(FTHG ~ HS + AS, data=data)
summary(model)

# 6. Predict
new_match <- data.frame(HS=15, AS=10)
predict(model, new_match, interval="prediction")

# 7. Visualize results
plot(model)
```

---

**All code examples are from "Soccer Analytics: An Introduction Using R" by Clive Beggs (2024)**
