"""
SAEROS - ML Model Training Script
Trains a Random Forest Regression model for aluminum yield prediction.
"""
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import joblib

# Paths
DATA_PATH = 'data/training_data.csv'
MODEL_PATH = 'models/yield_model.pkl'


def train_model():
    print("=" * 60)
    print("SAEROS - Yield Prediction Model Training")
    print("=" * 60)

    # Load data
    print(f"\n[1] Loading training data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    print(f"    Loaded {len(df)} samples")
    print(f"    Columns: {list(df.columns)}")
    print(f"\n    Data summary:")
    print(df.describe().to_string())

    # Features and target
    feature_cols = ['silica_percent', 'iron_oxide_percent', 'alumina_percent', 'moisture_content']
    target_col = 'yield_percent'

    X = df[feature_cols].values
    y = df[target_col].values

    print(f"\n[2] Feature matrix shape: {X.shape}")
    print(f"    Target range: {y.min():.2f}% - {y.max():.2f}%")
    print(f"    Target mean: {y.mean():.2f}%")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\n[3] Train/Test split: {len(X_train)}/{len(X_test)} samples")

    # Train Random Forest
    print("\n[4] Training Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("    Training complete!")

    # Evaluate
    print("\n[5] Model Evaluation:")
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)

    print(f"    R² Score:  {r2:.4f}")
    print(f"    RMSE:      {rmse:.4f}%")
    print(f"    MAE:       {mae:.4f}%")

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    print(f"\n    5-Fold CV R² Scores: {cv_scores}")
    print(f"    Mean CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    # Feature importance
    print("\n[6] Feature Importances:")
    for feat, imp in zip(feature_cols, model.feature_importances_):
        bar = '█' * int(imp * 40)
        print(f"    {feat:<25} {imp:.4f}  {bar}")

    # Save model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\n[7] Model saved to: {MODEL_PATH}")

    # Test prediction
    print("\n[8] Sample Predictions:")
    test_samples = [
        [5.2, 12.3, 48.5, 8.1],   # Expected ~72%
        [15.3, 22.1, 35.4, 14.5], # Expected ~52%
        [2.8, 8.5, 54.1, 5.9],    # Expected ~81%
    ]
    for sample in test_samples:
        pred = model.predict([sample])[0]
        print(f"    SiO2={sample[0]}%, Fe2O3={sample[1]}%, Al2O3={sample[2]}%, "
              f"Moisture={sample[3]}% → Predicted Yield: {pred:.2f}%")

    print("\n" + "=" * 60)
    print("Training complete! Model ready for use.")
    print("=" * 60)

    return model


if __name__ == '__main__':
    train_model()
