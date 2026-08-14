"""
ML Model utilities for SAEROS yield prediction.
Loads the trained Random Forest model and provides prediction interface.
"""
import os
import joblib
import numpy as np
from flask import current_app


_model = None
_model_loaded = False


def load_model():
    """Load the trained ML model from disk."""
    global _model, _model_loaded
    try:
        model_path = current_app.config.get('MODEL_PATH', 'models/yield_model.pkl')
        if os.path.exists(model_path):
            _model = joblib.load(model_path)
            _model_loaded = True
            return True
        else:
            _model_loaded = False
            return False
    except Exception as e:
        current_app.logger.error(f"Error loading ML model: {e}")
        _model_loaded = False
        return False


def get_model():
    """Get the loaded model, loading it if necessary."""
    global _model, _model_loaded
    if not _model_loaded or _model is None:
        load_model()
    return _model


def predict_yield(silica_percent, iron_oxide_percent, alumina_percent, moisture_content):
    """
    Predict aluminum yield percentage based on raw material composition.
    
    Args:
        silica_percent: SiO2 percentage
        iron_oxide_percent: Fe2O3 percentage
        alumina_percent: Al2O3 percentage
        moisture_content: Moisture percentage
    
    Returns:
        dict: {
            'predicted_yield': float,
            'confidence_score': float,
            'efficiency_rating': str,
            'model_used': str
        }
    """
    model = get_model()

    features = np.array([[
        float(silica_percent),
        float(iron_oxide_percent),
        float(alumina_percent),
        float(moisture_content)
    ]])

    if model is not None:
        try:
            predicted_yield = float(model.predict(features)[0])
            predicted_yield = max(0, min(100, predicted_yield))

            # Calculate confidence from tree variance if Random Forest
            if hasattr(model, 'estimators_'):
                tree_predictions = np.array([
                    tree.predict(features)[0] for tree in model.estimators_
                ])
                std_dev = np.std(tree_predictions)
                confidence = max(0, min(100, 100 - (std_dev * 5)))
            else:
                confidence = 75.0

            model_used = 'random_forest'
        except Exception as e:
            # Fallback to formula-based prediction
            predicted_yield, confidence = _formula_prediction(
                silica_percent, iron_oxide_percent, alumina_percent, moisture_content
            )
            model_used = 'formula_fallback'
    else:
        # Use formula-based prediction when model not available
        predicted_yield, confidence = _formula_prediction(
            silica_percent, iron_oxide_percent, alumina_percent, moisture_content
        )
        model_used = 'formula_fallback'

    efficiency_rating = _get_efficiency_rating(predicted_yield)

    return {
        'predicted_yield': round(predicted_yield, 2),
        'confidence_score': round(confidence, 1),
        'efficiency_rating': efficiency_rating,
        'model_used': model_used
    }


def _formula_prediction(silica_percent, iron_oxide_percent, alumina_percent, moisture_content):
    """
    Formula-based yield prediction as fallback.
    Based on Bayer process chemistry principles.
    """
    silica_percent = float(silica_percent)
    iron_oxide_percent = float(iron_oxide_percent)
    alumina_percent = float(alumina_percent)
    moisture_content = float(moisture_content)

    # Base yield from alumina content
    base_yield = alumina_percent * 0.85

    # Silica penalty (silica reacts with caustic soda, reducing efficiency)
    silica_penalty = silica_percent * 1.2

    # Iron oxide minor penalty
    iron_penalty = iron_oxide_percent * 0.3

    # Moisture penalty
    moisture_penalty = moisture_content * 0.4

    predicted_yield = base_yield - silica_penalty - iron_penalty - moisture_penalty
    predicted_yield = max(5.0, min(95.0, predicted_yield))

    # Confidence based on how typical the values are
    confidence = 65.0
    if 20 <= alumina_percent <= 60 and silica_percent < 20:
        confidence = 72.0

    return predicted_yield, confidence


def _get_efficiency_rating(yield_percent):
    """Get efficiency rating based on yield percentage."""
    if yield_percent >= 75:
        return 'Excellent'
    elif yield_percent >= 60:
        return 'Good'
    elif yield_percent >= 45:
        return 'Average'
    elif yield_percent >= 30:
        return 'Below Average'
    else:
        return 'Poor'
