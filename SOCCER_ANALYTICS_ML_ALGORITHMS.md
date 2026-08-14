# Soccer Analytics: ML Algorithms

## Overview

This document provides comprehensive coverage of machine learning algorithms used in soccer analytics and prediction modeling, with emphasis on practical implementation and prediction accuracy for sports betting markets.

## 1. Regression Models

### 1.1 Linear Regression

**Purpose**: Predict continuous outcomes (e.g., player market value, expected goals)

**When to Use**:
- Predicting numeric outcomes with linear relationships
- Initial baseline models
- Interpretability is critical

**Key Concepts**:
- Line of best fit minimizing squared error
- Coefficient interpretation shows feature impact
- R² metric for goodness of fit

**Applications in Soccer**:
- Player market value prediction
- Goal prediction with linear assumptions
- Performance score estimation

**Python Implementation**:
```python
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# Evaluate
from sklearn.metrics import mean_squared_error, r2_score
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)
```

**Performance Metrics**:
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)
- R² Score (0-1, higher is better)
- Mean Absolute Error (MAE)

**Limitations**:
- Assumes linear relationships
- Sensitive to outliers
- Does not capture complex patterns
- Multicollinearity can distort coefficients

---

### 1.2 Poisson Regression

**Purpose**: Predict count outcomes (goals, shots, tackles)

**When to Use**:
- Predicting discrete events (goals, shots)
- Data with non-negative integer values
- Modeling low-frequency events

**Key Concepts**:
- Models event rates using Poisson distribution
- Log-linear relationship between features and outcome
- Variance equals mean (homogeneity assumption)

**Applications in Soccer**:
- Goals in a match (home team, away team)
- Shot predictions
- Card predictions
- Event frequency modeling

**Python Implementation**:
```python
from sklearn.linear_model import PoissonRegressor

model = PoissonRegressor(alpha=0.1)
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# Evaluate
from sklearn.metrics import mean_absolute_error, mean_poisson_deviance
mae = mean_absolute_error(y_test, predictions)
```

**Performance Metrics**:
- Mean Absolute Error
- Poisson Deviance
- Actual vs Predicted frequency distributions

**Limitations**:
- **Overdispersion**: Variance > mean
  - Solution: Negative Binomial Regression
  - Better handles variance in goal data
- **Zero-Inflation**: Too many zero outcomes
  - Solution: Hurdle Models or Zero-Inflated Poisson
- Assumes independence between events

---

### 1.3 Negative Binomial Regression

**Purpose**: Handle overdispersed count data (variance > mean)

**When to Use**:
- Goals data (often has high variance)
- When Poisson regression shows poor fit
- More flexible than Poisson for soccer data

**Key Concepts**:
- Generalization of Poisson
- Additional dispersion parameter allows variance != mean
- Better captures goal scoring variability

**Applications in Soccer**:
- Goal prediction (more accurate than Poisson)
- High-variance event modeling
- Team-specific scoring patterns

**Python Implementation**:
```python
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import NegativeBinomial
from statsmodels.genmod.cov_struct import Independence

# Simple implementation with statsmodels
model = NegativeBinomial()
# Use with fitting routine for count data
```

**Performance**: Typically 10-20% better than Poisson on soccer goal data

---

### 1.4 K-Nearest Neighbors (KNN) Regression

**Purpose**: Non-parametric prediction based on similarity

**When to Use**:
- Local patterns matter more than global trends
- Player value prediction from comparable players
- When you have rich neighbor data

**Key Concepts**:
- Predicts value based on K nearest neighbors
- Distance metric (Euclidean) determines similarity
- Non-parametric (no assumptions about distribution)

**Applications in Soccer**:
- Player valuation from comparables
- Performance prediction from similar situations
- Match outcome based on historical similar matches

**Python Implementation**:
```python
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

# Must scale features for KNN
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Try different K values
for k in [3, 5, 7, 10]:
    model = KNeighborsRegressor(n_neighbors=k)
    model.fit(X_train_scaled, y_train)
    score = model.score(X_test_scaled, y_test)
    print(f"K={k}: R² = {score:.3f}")

# Optimal K usually 5-7 for soccer data
model = KNeighborsRegressor(n_neighbors=5)
model.fit(X_train_scaled, y_train)
predictions = model.predict(X_test_scaled)
```

**Choosing K**:
- Small K (3-5): More flexible, higher variance
- Large K (10+): Smoother, higher bias
- Soccer data: Typically 5-7 optimal

**Limitations**:
- Computationally expensive for large datasets
- Sensitive to feature scaling
- All features weighted equally
- Poor performance in high dimensions

---

## 2. Classification Models

### 2.1 Logistic Regression

**Purpose**: Binary probability prediction

**When to Use**:
- Match outcome prediction (win/loss/draw)
- Expected Goals (xG) - probability a shot results in goal
- Binary event prediction (goal/no-goal)

**Key Concepts**:
- Sigmoid function maps linear combination to [0,1]
- Probability interpretation
- Threshold determines decision boundary (default 0.5)

**Applications in Soccer**:
- Expected Goals (xG) modeling
- Match outcome prediction
- Shot success probability
- Player performance likelihood

**Python Implementation**:
```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_score, recall_score, roc_auc_score, roc_curve

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Get probabilities
y_prob = model.predict_proba(X_test)[:, 1]  # Probability of positive class
y_pred = model.predict(X_test)

# Evaluate
cm = confusion_matrix(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)

# ROC Curve analysis
fpr, tpr, thresholds = roc_curve(y_test, y_prob)

# Find optimal threshold (not necessarily 0.5)
f1_scores = [2 * (p * r) / (p + r) for p, r in zip(precision_list, recall_list)]
optimal_threshold = thresholds[np.argmax(f1_scores)]
```

**Performance Metrics**:
- Confusion Matrix (TP, FP, TN, FN)
- Precision: TP / (TP + FP) - accuracy of positive predictions
- Recall: TP / (TP + FN) - coverage of actual positives
- F1-Score: Harmonic mean of precision and recall
- ROC AUC: Area under ROC curve (0.5-1.0, higher better)
- Log Loss: Probability calibration metric

**Threshold Optimization**:
```python
# For betting, may want higher precision (fewer false alarms)
# For scouting, may want higher recall (don't miss talent)
optimal_threshold = 0.45  # Example: slightly below 0.5
y_pred_custom = (y_prob >= optimal_threshold).astype(int)
```

**Typical Accuracy Ranges**:
- xG model: 65-75% accuracy (shots are inherently variable)
- Match outcome: 55-62% (soccer is unpredictable)
- Player performance: 60-70%

---

### 2.2 K-Nearest Neighbors Classification

**Purpose**: Classify based on neighbor voting

**When to Use**:
- Local neighborhood patterns matter
- Pass success prediction from similar situations
- Complex non-linear decision boundaries

**Key Concepts**:
- K nearest neighbors vote on classification
- Distance-weighted voting options
- Non-parametric, instance-based learning

**Applications in Soccer**:
- Shot success (goal/no-goal)
- Pass completion from situation
- Player position classification
- Tactical pattern recognition

**Python Implementation**:
```python
from sklearn.neighbors import KNeighborsClassifier

# Optimal K varies by problem
for k in [3, 5, 7, 9]:
    model = KNeighborsClassifier(n_neighbors=k, weights='distance')
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    print(f"K={k}: Accuracy = {accuracy:.3f}")

# Use distance weighting for better results
model = KNeighborsClassifier(n_neighbors=5, weights='distance')
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)
```

**Performance Range**: 58-72% depending on problem complexity

---

## 3. Tree-Based Models

### 3.1 Decision Trees

**Purpose**: Interpretable rules for classification/regression

**When to Use**:
- Feature importance needed
- Rules should be interpretable
- Mixed feature types (numeric + categorical)

**Key Concepts**:
- Recursive binary splits (Gini/Entropy)
- Each path = decision rule
- Prone to overfitting without limits

**Applications in Soccer**:
- Pass outcome prediction (with rule interpretation)
- Player position classification
- Tactic identification
- Injury risk assessment

**Python Implementation**:
```python
from sklearn.tree import DecisionTreeClassifier, plot_tree
import matplotlib.pyplot as plt

model = DecisionTreeClassifier(
    max_depth=5,  # Limit depth to prevent overfitting
    min_samples_split=20,
    min_samples_leaf=10,
    criterion='gini'  # or 'entropy'
)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# Visualize tree
plt.figure(figsize=(20, 10))
plot_tree(model, feature_names=feature_names, 
          class_names=['No', 'Yes'], filled=True)
plt.show()

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
```

**Hyperparameter Tuning**:
- `max_depth`: 3-6 optimal for soccer (too deep = overfitting)
- `min_samples_split`: 20-50 (avoid splits on noise)
- `min_samples_leaf`: 10-20 (ensure leaf nodes meaningful)

**Accuracy**: 55-70% depending on complexity

---

### 3.2 Random Forest

**Purpose**: Ensemble of trees for robust prediction

**When to Use**:
- Need high accuracy + some interpretability
- Feature importance required
- Reduce overfitting vs single tree
- Handles mixed feature types

**Key Concepts**:
- Ensemble of independent decision trees
- Bootstrap samples reduce variance
- Averaging predictions stabilizes output
- Feature importance from all trees

**Applications in Soccer**:
- Match outcome prediction (typical: 60-65% accuracy)
- xG alternative model
- Player performance ranking
- Team strength estimation

**Python Implementation**:
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

model = RandomForestClassifier(
    n_estimators=100,  # Number of trees
    max_depth=8,  # Deeper than single tree
    min_samples_split=20,
    min_samples_leaf=10,
    max_features='sqrt',  # Feature subsampling
    n_jobs=-1,  # Use all cores
    random_state=42
)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

# Feature importance
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

# Out-of-bag error (validation without holdout set)
oob_score = model.oob_score_  # Typical: 0.55-0.65

print(classification_report(y_test, y_pred))
```

**Feature Importance Interpretation**:
- Top features for match outcome: Home advantage, recent form, goal differential
- Top features for xG: Distance, angle, defender proximity

**Typical Accuracy**:
- Match outcome: 58-64%
- xG prediction: 68-75%
- Player performance: 62-70%

---

### 3.3 XGBoost (Extreme Gradient Boosting)

**Purpose**: State-of-the-art gradient boosting for maximum accuracy

**When to Use**:
- Maximum prediction accuracy critical
- Handling complex feature interactions
- Dealing with imbalanced data
- Can afford computational cost

**Key Concepts**:
- Sequential trees correcting previous errors
- Loss function optimization at each step
- Gradient-based learning
- Built-in regularization (L1/L2)

**Applications in Soccer**:
- Best-in-class xG models (74-80% accuracy)
- Match outcome prediction (64-69%)
- Injury prediction
- Player valuation models

**Python Implementation**:
```python
import xgboost as xgb
from sklearn.metrics import classification_report

# Classification
model = xgb.XGBClassifier(
    n_estimators=200,  # More boosting rounds
    max_depth=5,  # Moderate depth
    learning_rate=0.1,  # Step size
    subsample=0.8,  # Row subsampling
    colsample_bytree=0.8,  # Feature subsampling
    gamma=0,  # Min loss reduction
    reg_alpha=0.1,  # L1 regularization
    reg_lambda=1.0,  # L2 regularization
    random_state=42,
    n_jobs=-1
)

# Early stopping to prevent overfitting
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=20,
    verbose=False
)

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

# SHAP for model interpretation
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test, feature_names=feature_names)

# Feature importance
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
```

**Hyperparameter Tuning Strategy**:
```python
# Grid search for optimal parameters
from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.05, 0.1],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9]
}

grid = GridSearchCV(
    xgb.XGBClassifier(n_estimators=100),
    param_grid,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1
)

grid.fit(X_train, y_train)
best_model = grid.best_estimator_
```

**Typical Accuracy Ranges**:
- xG model: 74-80%
- Match outcome: 64-70%
- Player performance: 68-75%

---

## 4. Deep Learning Models

### 4.1 Neural Networks (Fully Connected)

**Purpose**: Learn complex non-linear patterns

**When to Use**:
- Large amounts of data available
- Complex feature interactions
- Need maximum flexibility
- Can tolerate longer training

**Key Concepts**:
- Multiple layers of neurons
- Non-linear activation functions
- Backpropagation for training
- Learning rate optimization

**Applications in Soccer**:
- Match outcome with many features
- Full game simulation
- Player performance prediction
- Tactical pattern recognition

**Python Implementation**:
```python
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.utils.data import DataLoader, TensorDataset

class SoccerNeuralNetwork(nn.Module):
    def __init__(self, input_size, hidden_sizes=[128, 64, 32]):
        super().__init__()
        layers = []
        
        # Build layers
        prev_size = input_size
        for hidden_size in hidden_sizes:
            layers.append(nn.Linear(prev_size, hidden_size))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.3))
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, 1))
        layers.append(nn.Sigmoid())  # For binary classification
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)

# Training
model = SoccerNeuralNetwork(input_size=X_train.shape[1])
optimizer = Adam(model.parameters(), lr=0.001)
criterion = nn.BCELoss()

train_dataset = TensorDataset(
    torch.FloatTensor(X_train.values),
    torch.FloatTensor(y_train.values)
)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

epochs = 100
for epoch in range(epochs):
    for X_batch, y_batch in train_loader:
        # Forward pass
        predictions = model(X_batch).squeeze()
        loss = criterion(predictions, y_batch)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")

# Prediction
model.eval()
with torch.no_grad():
    X_test_tensor = torch.FloatTensor(X_test.values)
    y_prob = model(X_test_tensor).numpy()
    y_pred = (y_prob >= 0.5).astype(int)
```

**TensorFlow Implementation**:
```python
from tensorflow import keras
from tensorflow.keras import layers

model = keras.Sequential([
    layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    layers.Dropout(0.3),
    layers.Dense(64, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(32, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC()]
)

history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=32,
    validation_split=0.2,
    early_stopping=keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10
    )
)

# Evaluate
y_prob = model.predict(X_test)
y_pred = (y_prob >= 0.5).astype(int)
```

**Typical Accuracy**: 60-70% for match outcomes (not necessarily better than XGBoost)

**Key Advantages**:
- Can learn from raw features with less engineering
- Handles large feature sets well
- Flexible architecture

**Key Disadvantages**:
- Requires more data than tree models
- Harder to interpret (black box)
- Longer training time
- Hyperparameter tuning complex

---

## 5. Ensemble Methods

### Combining Multiple Models

**Purpose**: Leverage strengths of different algorithms

**When to Use**:
- Need maximum accuracy
- Different models capture different patterns
- Can afford computational cost

**Strategies**:

1. **Voting Classifier**
```python
from sklearn.ensemble import VotingClassifier

ensemble = VotingClassifier(
    estimators=[
        ('logistic', LogisticRegression()),
        ('rf', RandomForestClassifier()),
        ('xgb', xgb.XGBClassifier())
    ],
    voting='soft'  # Use probability averaging
)
ensemble.fit(X_train, y_train)
y_prob = ensemble.predict_proba(X_test)[:, 1]
```

2. **Stacking**
```python
from sklearn.ensemble import StackingClassifier

level0 = [
    ('logistic', LogisticRegression()),
    ('rf', RandomForestClassifier()),
    ('xgb', xgb.XGBClassifier())
]
level1 = LogisticRegression()

stacking = StackingClassifier(
    estimators=level0,
    final_estimator=level1,
    cv=5
)
stacking.fit(X_train, y_train)
```

3. **Weighted Averaging**
```python
# Blend predictions with optimal weights
models = [model1, model2, model3]
weights = [0.3, 0.4, 0.3]  # Tune weights by validation

predictions = sum(w * m.predict_proba(X_test)[:, 1] 
                  for w, m in zip(weights, models))
```

**Typical Improvement**: 2-4% accuracy gain over best single model

---

## 6. Model Comparison Framework

| Model | Complexity | Interpretability | Training Time | Accuracy Range | Best For |
|-------|-----------|------------------|---------------|-----------------|----------|
| Logistic Regression | Low | High | Fast | 55-65% | Baseline, xG |
| KNN | Low | Medium | Fast | 58-68% | Local patterns |
| Decision Tree | Medium | Very High | Fast | 55-65% | Rules needed |
| Random Forest | High | Medium | Medium | 58-68% | Balanced accuracy |
| XGBoost | Very High | Low | Slow | 64-75% | Max accuracy |
| Neural Network | Very High | Low | Very Slow | 60-70% | Large datasets |

---

## Key Takeaways

1. **No universal best**: Algorithm choice depends on data, interpretability needs, and accuracy targets
2. **Start simple**: Baseline with logistic regression before complex models
3. **Feature engineering**: Often more important than algorithm choice (70% of work)
4. **Validation critical**: Always use holdout test set and cross-validation
5. **Ensemble methods**: Combine models for incremental gains
6. **Accuracy limits**: Even best models cap out ~70% on soccer due to inherent unpredictability

