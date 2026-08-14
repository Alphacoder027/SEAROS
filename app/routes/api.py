from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import csrf
from app.utils.ml_model import predict_yield
from app.utils.byproduct_algo import recommend_byproduct_use

api_bp = Blueprint('api', __name__)


@api_bp.route('/predict', methods=['POST'])
@csrf.exempt
@login_required
def predict():
    """
    Predict aluminum yield based on raw material composition.
    
    POST JSON:
    {
        "silica_percent": float,
        "iron_oxide_percent": float,
        "alumina_percent": float,
        "moisture_content": float
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['silica_percent', 'iron_oxide_percent', 'alumina_percent', 'moisture_content']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    try:
        silica = float(data['silica_percent'])
        iron_oxide = float(data['iron_oxide_percent'])
        alumina = float(data['alumina_percent'])
        moisture = float(data['moisture_content'])

        # Validate ranges
        for val, name in [(silica, 'silica'), (iron_oxide, 'iron_oxide'),
                          (alumina, 'alumina'), (moisture, 'moisture')]:
            if not (0 <= val <= 100):
                return jsonify({'error': f'{name} must be between 0 and 100'}), 400

        if silica + iron_oxide + alumina + moisture > 100:
            return jsonify({'error': 'Total composition cannot exceed 100%'}), 400

    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid numeric value: {str(e)}'}), 400

    result = predict_yield(silica, iron_oxide, alumina, moisture)
    return jsonify(result)


@api_bp.route('/recommend-byproduct', methods=['POST'])
@csrf.exempt
@login_required
def recommend_byproduct():
    """
    Get by-product use recommendation based on composition.
    
    POST JSON:
    {
        "byproduct_type": str,
        "iron_oxide_percent": float,
        "alumina_percent": float,
        "silica_percent": float,
        "manganese_percent": float (optional),
        "rare_earth_percent": float (optional)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    byproduct_type = data.get('byproduct_type', 'red_mud')

    result = recommend_byproduct_use(
        byproduct_type=byproduct_type,
        iron_oxide_percent=data.get('iron_oxide_percent', 0),
        alumina_percent=data.get('alumina_percent', 0),
        silica_percent=data.get('silica_percent', 0),
        manganese_percent=data.get('manganese_percent', 0),
        rare_earth_percent=data.get('rare_earth_percent', 0)
    )
    return jsonify(result)


@api_bp.route('/health', methods=['GET'])
@csrf.exempt
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'SAEROS API'})
