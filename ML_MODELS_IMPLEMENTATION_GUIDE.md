# Soccer Analytics: ML Models Implementation Guide

## Overview

This guide provides step-by-step instructions for building production-ready predictive models for soccer analytics and betting markets.

---

## Part 1: Project Setup

### 1.1 Environment Setup

```bash
# Create virtual environment
python -m venv soccer_ml
source soccer_ml/bin/activate  # or soccer_ml\Scripts\activate on Windows

# Install dependencies
pip install pandas numpy scikit-learn xgboost lightgbm
pip install tensorflow torch  # For deep learning
pip install matplotlib seaborn  # Visualization
pip install jupyter notebook  # Development
pip install sqlalchemy psycopg2-binary  # Database
pip install python-dotenv  # Environment variables
pip install requests  # API calls
```

### 1.2 Project Structure

```
soccer_ml_project/
├── data/
│   ├── raw/                 # Original data
│   ├── processed/           # Cleaned data
│   └── features/            # Feature matrices
├── models/
│   ├── trained/             # Saved models
│   ├── predictions/         # Predictions
│   └── evaluation/          # Metrics
├── src/
│   ├── data_pipeline.py     # Data loading/cleaning
│   ├── feature_engineering.py
│   ├── model_training.py
│   ├── model_evaluation.py
│   └── prediction.py
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
├── config/
│   ├── config.yaml          # Configuration
│   └── secrets.yaml         # API keys (gitignore)
├── tests/
│   ├── test_features.py
│   ├── test_models.py
│   └── test_predictions.py
└── requirements.txt
```

### 1.3 Configuration Management

```python
# config.yaml
database:
  host: localhost
  port: 5432
  name: soccer_ml
  
data:
  train_date_start: "2020-01-01"
  train_date_end: "2023-12-31"
  test_date_start: "2024-01-01"
  test_date_end: "2024-12-31"
  
models:
  xgboost:
    n_estimators: 200
    max_depth: 5
    learning_rate: 0.1
    subsample: 0.8
    colsample_bytree: 0.8
  
validation:
  use_time_series_split: true
  n_splits: 5
  min_train_samples: 500
```

---

## Part 2: Data Pipeline

### 2.1 Data Loading

```python
# src/data_pipeline.py
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import yaml

class DataPipeline:
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.engine = create_engine(
            f"postgresql://{self.config['database']['user']}:"
            f"{self.config['database']['password']}@"
            f"{self.config['database']['host']}/"
            f"{self.config['database']['name']}"
        )
    
    def load_matches(self, date_start, date_end):
        """Load match data from database"""
        query = f"""
        SELECT 
            match_id, match_date, home_team, away_team,
            home_goals, away_goals, result,
            home_xg, away_xg, possession_home,
            league, season
        FROM matches
        WHERE match_date BETWEEN '{date_start}' AND '{date_end}'
        ORDER BY match_date
        """
        return pd.read_sql(query, self.engine)
    
    def load_players(self):
        """Load player data"""
        query = """
        SELECT player_id, player_name, team, position,
               age, market_value, nationality
        FROM players
        """
        return pd.read_sql(query, self.engine)
    
    def load_shots(self, match_ids):
        """Load shot-level data for xG calculation"""
        placeholders = ','.join(map(str, match_ids))
        query = f"""
        SELECT shot_id, match_id, player_id, team,
               distance, angle, defenders_nearby,
               shot_type, assist_type, under_pressure,
               goal
        FROM shots
        WHERE match_id IN ({placeholders})
        """
        return pd.read_sql(query, self.engine)

# Usage
pipeline = DataPipeline()
matches = pipeline.load_matches('2024-01-01', '2024-12-31')
shots = pipeline.load_shots(matches['match_id'].tolist())
```

### 2.2 Data Cleaning & Validation

```python
class DataCleaner:
    @staticmethod
    def clean_matches(df):
        """Clean match data"""
        df = df.copy()
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['match_id'])
        
        # Handle missing values
        df['home_xg'] = df['home_xg'].fillna(df['home_xg'].median())
        df['away_xg'] = df['away_xg'].fillna(df['away_xg'].median())
        
        # Ensure consistent team names
        df['home_team'] = df['home_team'].str.strip().str.title()
        df['away_team'] = df['away_team'].str.strip().str.title()
        
        # Sort by date
        df['match_date'] = pd.to_datetime(df['match_date'])
        df = df.sort_values('match_date')
        
        # Validate goals (should be non-negative)
        assert (df['home_goals'] >= 0).all()
        assert (df['away_goals'] >= 0).all()
        
        return df
    
    @staticmethod
    def validate_data(df):
        """Validation checks"""
        issues = []
        
        # Check for nulls
        nulls = df.isnull().sum()
        if nulls.any():
            issues.append(f"Null values found: {nulls[nulls > 0]}")
        
        # Check date range
        date_range = df['match_date'].max() - df['match_date'].min()
        if date_range < pd.Timedelta(days=365):
            issues.append("Less than 1 year of data")
        
        # Check team counts
        unique_teams = len(pd.concat([df['home_team'], df['away_team']]).unique())
        if unique_teams < 10:
            issues.append(f"Only {unique_teams} unique teams")
        
        return issues

# Usage
cleaner = DataCleaner()
matches = cleaner.clean_matches(matches)
issues = cleaner.validate_data(matches)
if issues:
    print("Data quality issues:", issues)
```

---

## Part 3: Feature Engineering Pipeline

### 3.1 Feature Generator

```python
# src/feature_engineering.py
class FeatureEngineer:
    def __init__(self, matches_df):
        self.matches = matches_df.sort_values('match_date')
        self.team_stats = {}
    
    def rolling_team_stats(self, team, window=5, metric='goals_scored'):
        """Calculate rolling averages for team"""
        team_matches = self.matches[
            (self.matches['home_team'] == team) |
            (self.matches['away_team'] == team)
        ].copy()
        
        team_matches['is_home'] = team_matches['home_team'] == team
        
        # Get metric for this team
        team_matches['metric_value'] = team_matches.apply(
            lambda row: row['home_goals'] if row['is_home'] else row['away_goals']
            if metric == 'goals_scored' else
            row['away_goals'] if row['is_home'] else row['home_goals'],
            axis=1
        )
        
        return team_matches['metric_value'].rolling(window).mean()
    
    def engineer_match_features(self, match):
        """Generate features for single match"""
        features = {}
        home_team = match['home_team']
        away_team = match['away_team']
        match_date = match['match_date']
        
        # Filter historical data before this match
        history = self.matches[self.matches['match_date'] < match_date]
        
        # Performance features
        home_matches = history[
            (history['home_team'] == home_team) |
            (history['away_team'] == home_team)
        ].tail(5)
        
        away_matches = history[
            (history['home_team'] == away_team) |
            (history['away_team'] == away_team)
        ].tail(5)
        
        if len(home_matches) >= 3:
            # Home team goals scored in last 5
            home_gf = sum(
                m['home_goals'] if m['home_team'] == home_team 
                else m['away_goals']
                for _, m in home_matches.iterrows()
            )
            features['home_gf_l5'] = home_gf / len(home_matches)
            
            # Home team goals against in last 5
            home_ga = sum(
                m['away_goals'] if m['home_team'] == home_team
                else m['home_goals']
                for _, m in home_matches.iterrows()
            )
            features['home_ga_l5'] = home_ga / len(home_matches)
        else:
            features['home_gf_l5'] = 1.3
            features['home_ga_l5'] = 1.3
        
        if len(away_matches) >= 3:
            away_gf = sum(
                m['away_goals'] if m['away_team'] == away_team
                else m['home_goals']
                for _, m in away_matches.iterrows()
            )
            features['away_gf_l5'] = away_gf / len(away_matches)
            
            away_ga = sum(
                m['home_goals'] if m['away_team'] == away_team
                else m['away_goals']
                for _, m in away_matches.iterrows()
            )
            features['away_ga_l5'] = away_ga / len(away_matches)
        else:
            features['away_gf_l5'] = 1.3
            features['away_ga_l5'] = 1.3
        
        # Rest days
        home_last_match = history[
            (history['home_team'] == home_team) |
            (history['away_team'] == home_team)
        ].iloc[-1] if len(history) > 0 else None
        
        features['home_rest_days'] = (
            (match_date - home_last_match['match_date']).days
            if home_last_match is not None else 7
        )
        
        # Home advantage constant
        features['home_advantage'] = 0.35
        
        return features
    
    def generate_all_features(self, matches_df):
        """Generate features for all matches"""
        features_list = []
        
        for idx, (_, match) in enumerate(matches_df.iterrows()):
            if idx % 100 == 0:
                print(f"Processing match {idx+1}/{len(matches_df)}")
            
            features = self.engineer_match_features(match)
            features['match_id'] = match['match_id']
            features_list.append(features)
        
        return pd.DataFrame(features_list)

# Usage
engineer = FeatureEngineer(matches)
X = engineer.generate_all_features(matches)

# Scale features
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = pd.DataFrame(
    scaler.fit_transform(X),
    columns=X.columns,
    index=X.index
)
```

### 3.2 Feature Storage

```python
class FeatureStore:
    def __init__(self, db_path='data/features'):
        self.db_path = db_path
        import os
        os.makedirs(db_path, exist_ok=True)
    
    def save_features(self, X, feature_set_name, metadata=None):
        """Save feature matrix with metadata"""
        X.to_parquet(f'{self.db_path}/{feature_set_name}.parquet')
        
        # Save metadata
        metadata = metadata or {}
        metadata['n_samples'] = len(X)
        metadata['n_features'] = X.shape[1]
        metadata['features'] = list(X.columns)
        
        import json
        with open(f'{self.db_path}/{feature_set_name}_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def load_features(self, feature_set_name):
        """Load feature matrix"""
        return pd.read_parquet(f'{self.db_path}/{feature_set_name}.parquet')

# Usage
store = FeatureStore()
store.save_features(
    X_scaled,
    'match_features_2024',
    metadata={'date_range': '2024-01-01 to 2024-12-31'}
)
```

---

## Part 4: Model Training

### 4.1 Model Training Pipeline

```python
# src/model_training.py
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, roc_auc_score
import pickle

class ModelTrainer:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.scaler = None
    
    def split_data_time_series(self, X, y):
        """Time-series aware train/test split"""
        cutoff_idx = int(len(X) * 0.8)
        
        X_train, X_test = X.iloc[:cutoff_idx], X.iloc[cutoff_idx:]
        y_train, y_test = y.iloc[:cutoff_idx], y.iloc[cutoff_idx:]
        
        # Validation set (last 20% of training)
        val_cutoff = int(len(X_train) * 0.8)
        X_val, X_train_final = X_train.iloc[val_cutoff:], X_train.iloc[:val_cutoff]
        y_val, y_train_final = y_train.iloc[val_cutoff:], y_train.iloc[:val_cutoff]
        
        return X_train_final, X_val, X_test, y_train_final, y_val, y_test
    
    def train_match_outcome_model(self, X, y):
        """Train multiclass match outcome model"""
        from sklearn.preprocessing import LabelEncoder
        
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data_time_series(X, y)
        
        # Encode target
        le = LabelEncoder()
        y_train_enc = le.fit_transform(y_train)
        y_val_enc = le.transform(y_val)
        y_test_enc = le.transform(y_test)
        
        # Train model
        model = xgb.XGBClassifier(
            n_estimators=self.config['models']['xgboost']['n_estimators'],
            max_depth=self.config['models']['xgboost']['max_depth'],
            learning_rate=self.config['models']['xgboost']['learning_rate'],
            subsample=self.config['models']['xgboost']['subsample'],
            colsample_bytree=self.config['models']['xgboost']['colsample_bytree'],
            objective='multi:softprob',
            num_class=3,  # W, D, L
            random_state=42,
            n_jobs=-1
        )
        
        print("Training XGBoost model...")
        model.fit(
            X_train, y_train_enc,
            eval_set=[(X_val, y_val_enc)],
            early_stopping_rounds=20,
            verbose=100
        )
        
        self.model = model
        self.label_encoder = le
        
        return self.evaluate_model(X_test, y_test_enc, y_test, le)
    
    def evaluate_model(self, X_test, y_test_enc, y_test_labels, label_encoder):
        """Evaluate model performance"""
        y_pred_enc = self.model.predict(X_test)
        y_pred = label_encoder.inverse_transform(y_pred_enc)
        y_prob = self.model.predict_proba(X_test)
        
        print("\nClassification Report:")
        print(classification_report(y_test_labels, y_pred, 
                                   target_names=['W', 'D', 'L']))
        
        # Multi-class AUC
        from sklearn.preprocessing import label_binarize
        y_test_bin = label_binarize(y_test_enc, classes=[0, 1, 2])
        auc = roc_auc_score(y_test_bin, y_prob, multi_class='ovr')
        print(f"\nMulti-class AUC: {auc:.3f}")
        
        accuracy = (y_pred == y_test_labels).mean()
        print(f"Accuracy: {accuracy:.1%}")
        
        return {
            'accuracy': accuracy,
            'auc': auc,
            'y_pred': y_pred,
            'y_prob': y_prob
        }
    
    def save_model(self, model_name):
        """Save trained model"""
        import os
        os.makedirs('models/trained', exist_ok=True)
        
        self.model.save_model(f'models/trained/{model_name}.json')
        
        # Save label encoder
        with open(f'models/trained/{model_name}_encoder.pkl', 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        print(f"Model saved: models/trained/{model_name}.json")
    
    def load_model(self, model_name):
        """Load trained model"""
        self.model = xgb.XGBClassifier()
        self.model.load_model(f'models/trained/{model_name}.json')
        
        with open(f'models/trained/{model_name}_encoder.pkl', 'rb') as f:
            self.label_encoder = pickle.load(f)
        
        print(f"Model loaded: {model_name}")

# Usage
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

trainer = ModelTrainer(config)
results = trainer.train_match_outcome_model(X_train, y_train)
trainer.save_model('match_outcome_xgboost_v1')
```

---

## Part 5: Model Evaluation & Monitoring

### 5.1 Evaluation Metrics

```python
class ModelEvaluator:
    @staticmethod
    def detailed_evaluation(y_true, y_pred_prob, model_name="Model"):
        """Comprehensive evaluation"""
        from sklearn.metrics import (
            confusion_matrix, precision_score, recall_score,
            f1_score, roc_auc_score, roc_curve, auc
        )
        import matplotlib.pyplot as plt
        
        # Get binary predictions
        y_pred = (y_pred_prob > 0.5).astype(int)
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        # Metrics
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        auc_score = roc_auc_score(y_true, y_pred_prob)
        
        print(f"\n{model_name} Evaluation:")
        print(f"Accuracy:  {accuracy:.1%}")
        print(f"Precision: {precision:.1%}")
        print(f"Recall:    {recall:.1%}")
        print(f"F1-Score:  {f1:.1%}")
        print(f"AUC:       {auc_score:.3f}")
        
        # ROC Curve
        fpr, tpr, _ = roc_curve(y_true, y_pred_prob)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'ROC (AUC={auc_score:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'{model_name} ROC Curve')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'models/evaluation/roc_{model_name}.png', dpi=100)
        plt.close()
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'auc': auc_score
        }
    
    @staticmethod
    def plot_feature_importance(model, feature_names, top_n=20):
        """Visualize feature importance"""
        import matplotlib.pyplot as plt
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False).head(top_n)
        
        plt.figure(figsize=(10, 6))
        plt.barh(importance_df['feature'], importance_df['importance'])
        plt.xlabel('Importance')
        plt.title(f'Top {top_n} Features')
        plt.tight_layout()
        plt.savefig('models/evaluation/feature_importance.png', dpi=100)
        plt.close()
        
        return importance_df

# Usage
evaluator = ModelEvaluator()
metrics = evaluator.detailed_evaluation(y_test, y_prob, "Match Outcome")
importance = evaluator.plot_feature_importance(model, X.columns)
```

### 5.2 Continuous Monitoring

```python
class ModelMonitor:
    def __init__(self, model, baseline_accuracy=0.62):
        self.model = model
        self.baseline_accuracy = baseline_accuracy
        self.performance_history = []
    
    def monitor_predictions(self, X_new, y_new, period):
        """Track model performance over time"""
        y_pred = self.model.predict(X_new)
        accuracy = (y_pred == y_new).mean()
        
        self.performance_history.append({
            'period': period,
            'accuracy': accuracy,
            'drift': accuracy - self.baseline_accuracy
        })
        
        # Alert if accuracy drops significantly
        if accuracy < self.baseline_accuracy - 0.05:
            print(f"⚠️  WARNING: Accuracy dropped to {accuracy:.1%}")
            return False
        
        return True
    
    def plot_performance_trend(self):
        """Visualize performance over time"""
        import matplotlib.pyplot as plt
        
        df = pd.DataFrame(self.performance_history)
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['period'], df['accuracy'], marker='o', label='Current')
        plt.axhline(y=self.baseline_accuracy, color='r', linestyle='--', label='Baseline')
        plt.fill_between(range(len(df)), 
                        self.baseline_accuracy - 0.05,
                        self.baseline_accuracy + 0.05,
                        alpha=0.2, color='green', label='Acceptable Range')
        plt.xlabel('Time Period')
        plt.ylabel('Accuracy')
        plt.title('Model Performance Monitoring')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('models/evaluation/performance_trend.png')
        plt.close()

# Usage
monitor = ModelMonitor(model, baseline_accuracy=0.62)
monitor.monitor_predictions(X_new, y_new, period='2024-Q3')
monitor.plot_performance_trend()
```

---

## Part 6: Production Deployment

### 6.1 Model API Service

```python
# src/prediction.py
from flask import Flask, request, jsonify
import xgboost as xgb
import pickle
import pandas as pd

app = Flask(__name__)

# Load model
model = xgb.XGBClassifier()
model.load_model('models/trained/match_outcome_xgboost_v1.json')

with open('models/trained/match_outcome_xgboost_v1_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

# Load feature scaler
with open('models/trained/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

@app.route('/predict', methods=['POST'])
def predict():
    """Predict match outcome"""
    try:
        # Get input data
        data = request.json
        
        # Convert to DataFrame
        X = pd.DataFrame([data])
        
        # Scale features
        X_scaled = pd.DataFrame(
            scaler.transform(X),
            columns=X.columns
        )
        
        # Make prediction
        y_pred = model.predict(X_scaled)[0]
        y_prob = model.predict_proba(X_scaled)[0]
        
        # Decode prediction
        prediction = label_encoder.inverse_transform([y_pred])[0]
        
        return jsonify({
            'prediction': prediction,
            'probabilities': {
                'home_win': float(y_prob[0]),
                'draw': float(y_prob[1]),
                'away_win': float(y_prob[2])
            },
            'confidence': float(max(y_prob))
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 6.2 Batch Prediction

```python
class BatchPredictor:
    def __init__(self, model, scaler, label_encoder):
        self.model = model
        self.scaler = scaler
        self.label_encoder = label_encoder
    
    def predict_batch(self, X_batch):
        """Make predictions on batch of matches"""
        X_scaled = pd.DataFrame(
            self.scaler.transform(X_batch),
            columns=X_batch.columns
        )
        
        y_pred = self.model.predict(X_scaled)
        y_prob = self.model.predict_proba(X_scaled)
        
        predictions = self.label_encoder.inverse_transform(y_pred)
        
        results = pd.DataFrame({
            'prediction': predictions,
            'p_home_win': y_prob[:, 0],
            'p_draw': y_prob[:, 1],
            'p_away_win': y_prob[:, 2],
            'confidence': y_prob.max(axis=1)
        })
        
        return results
    
    def save_predictions(self, predictions, output_path):
        """Save predictions to file"""
        predictions.to_csv(output_path, index=False)
        print(f"Predictions saved to {output_path}")

# Usage
predictor = BatchPredictor(model, scaler, label_encoder)
predictions = predictor.predict_batch(X_upcoming_matches)
predictor.save_predictions(predictions, 'predictions/upcoming_matches.csv')
```

---

## Part 7: Advanced Topics

### 7.1 Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV
import xgboost as xgb

def tune_hyperparameters(X_train, y_train):
    """Grid search for optimal parameters"""
    param_grid = {
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9],
        'n_estimators': [100, 200, 300]
    }
    
    grid = GridSearchCV(
        xgb.XGBClassifier(objective='multi:softprob', num_class=3),
        param_grid,
        cv=5,
        scoring='accuracy',
        n_jobs=-1,
        verbose=2
    )
    
    grid.fit(X_train, y_train)
    
    print(f"Best parameters: {grid.best_params_}")
    print(f"Best score: {grid.best_score_:.3f}")
    
    return grid.best_estimator_
```

### 7.2 Model Interpretability with SHAP

```python
import shap

def explain_predictions(model, X_test, feature_names):
    """Generate SHAP explanations"""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # Summary plot
    shap.summary_plot(shap_values, X_test, feature_names=feature_names)
    plt.savefig('models/evaluation/shap_summary.png')
    plt.close()
    
    # Force plot for individual prediction
    shap.force_plot(explainer.expected_value, 
                   shap_values[0], 
                   X_test.iloc[0],
                   matplotlib=True)
    plt.savefig('models/evaluation/shap_force.png')
    plt.close()
```

### 7.3 Ensemble Methods

```python
from sklearn.ensemble import VotingClassifier
import lightgbm as lgb

def create_ensemble(X_train, y_train, X_test):
    """Combine multiple models"""
    models = [
        ('xgb', xgb.XGBClassifier(n_estimators=200, max_depth=5)),
        ('lgb', lgb.LGBMClassifier(n_estimators=200, max_depth=5)),
        ('logistic', LogisticRegression(max_iter=1000))
    ]
    
    ensemble = VotingClassifier(
        estimators=models,
        voting='soft'
    )
    
    ensemble.fit(X_train, y_train)
    
    # Predictions
    y_pred = ensemble.predict(X_test)
    y_prob = ensemble.predict_proba(X_test)
    
    return ensemble, y_pred, y_prob
```

---

## Part 8: Testing & Quality Assurance

### 8.1 Unit Tests

```python
# tests/test_models.py
import unittest
import numpy as np
import pandas as pd

class TestModelTrainer(unittest.TestCase):
    def setUp(self):
        self.trainer = ModelTrainer(config)
        self.X_test = pd.DataFrame(np.random.rand(100, 10))
        self.y_test = np.random.choice([0, 1, 2], 100)
    
    def test_model_training(self):
        """Test model training completes"""
        model = self.trainer.train_match_outcome_model(
            self.X_test,
            self.y_test
        )
        self.assertIsNotNone(model)
    
    def test_prediction_shape(self):
        """Test prediction output shape"""
        y_pred = self.trainer.model.predict(self.X_test)
        self.assertEqual(len(y_pred), len(self.X_test))
    
    def test_probability_sum(self):
        """Test probabilities sum to 1"""
        y_prob = self.trainer.model.predict_proba(self.X_test)
        sums = y_prob.sum(axis=1)
        np.testing.assert_array_almost_equal(sums, np.ones(len(self.X_test)))
    
    def test_accuracy_above_baseline(self):
        """Test accuracy exceeds baseline"""
        y_pred = self.trainer.model.predict(self.X_test)
        accuracy = (y_pred == self.y_test).mean()
        self.assertGreater(accuracy, 0.33)  # Above random

if __name__ == '__main__':
    unittest.main()
```

---

## Part 9: Production Checklist

- [ ] Data pipeline working end-to-end
- [ ] Feature engineering reproducible
- [ ] Model training converges
- [ ] Evaluation metrics meet requirements
- [ ] Cross-validation shows stable performance
- [ ] Hyperparameters tuned
- [ ] Model saved and versioned
- [ ] API deployed and tested
- [ ] Batch prediction working
- [ ] Monitoring in place
- [ ] Documentation complete
- [ ] CI/CD pipeline configured

---

## Quick Start

```bash
# 1. Setup
python -m venv soccer_ml
pip install -r requirements.txt

# 2. Prepare data
python src/data_pipeline.py

# 3. Engineer features
python src/feature_engineering.py

# 4. Train model
python src/model_training.py

# 5. Evaluate
python src/model_evaluation.py

# 6. Deploy
python src/prediction.py

# 7. Monitor
python src/model_monitoring.py
```

