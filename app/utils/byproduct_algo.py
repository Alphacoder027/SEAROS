"""
By-product recommendation algorithm for SAEROS.
Uses rule-based logic combined with composition analysis to recommend
optimal secondary uses for red mud and other by-products.
"""


def recommend_byproduct_use(byproduct_type, iron_oxide_percent=0, alumina_percent=0,
                             silica_percent=0, manganese_percent=0, rare_earth_percent=0):
    """
    Recommend secondary use for a by-product based on its composition.
    
    Returns:
        dict: {
            'recommendation': str,
            'confidence': float (0-100),
            'reasoning': str,
            'alternative_uses': list
        }
    """
    iron_oxide_percent = float(iron_oxide_percent or 0)
    alumina_percent = float(alumina_percent or 0)
    silica_percent = float(silica_percent or 0)
    manganese_percent = float(manganese_percent or 0)
    rare_earth_percent = float(rare_earth_percent or 0)

    if byproduct_type == 'manganese_alloy':
        return _recommend_manganese(manganese_percent, iron_oxide_percent)
    elif byproduct_type == 'silica_residue':
        return _recommend_silica(silica_percent, alumina_percent)
    else:
        # Red mud or other
        return _recommend_red_mud(iron_oxide_percent, alumina_percent,
                                  silica_percent, rare_earth_percent)


def _recommend_red_mud(iron_oxide_percent, alumina_percent, silica_percent, rare_earth_percent):
    """Recommend use for red mud based on composition."""
    scores = {}
    reasoning_parts = []

    # Iron recovery pathway
    if iron_oxide_percent > 30:
        score = min(95, 60 + (iron_oxide_percent - 30) * 1.5)
        scores['iron_recovery'] = score
        reasoning_parts.append(f'High Fe₂O₃ content ({iron_oxide_percent:.1f}%) suitable for iron recovery')

    # Rare earth extraction
    if rare_earth_percent > 0.5:
        score = min(90, 50 + rare_earth_percent * 20)
        scores['rare_earth_extraction'] = score
        reasoning_parts.append(f'Rare earth content ({rare_earth_percent:.2f}%) viable for extraction')

    # Cement additive
    if silica_percent > 15 and alumina_percent > 10:
        score = min(85, 40 + silica_percent * 0.8 + alumina_percent * 0.5)
        scores['cement_additive'] = score
        reasoning_parts.append(f'SiO₂ ({silica_percent:.1f}%) and Al₂O₃ ({alumina_percent:.1f}%) suitable for cement')
    elif silica_percent > 10:
        scores['cement_additive'] = 55
        reasoning_parts.append(f'Moderate SiO₂ ({silica_percent:.1f}%) for cement additive')

    # Road construction
    if iron_oxide_percent > 15 and silica_percent > 10:
        scores['road_construction'] = 60
        reasoning_parts.append('Composition suitable for road construction aggregate')

    # Soil amendment (low iron, moderate alumina)
    if iron_oxide_percent < 20 and alumina_percent > 5:
        scores['soil_amendment'] = 45
        reasoning_parts.append('Low iron content allows soil amendment application')

    # Default to further processing if no clear winner
    if not scores:
        return {
            'recommendation': 'further_processing',
            'confidence': 40.0,
            'reasoning': 'Composition requires further analysis before secondary use determination',
            'alternative_uses': ['disposal']
        }

    # Pick best recommendation
    best = max(scores, key=scores.get)
    confidence = scores[best]
    alternatives = [k for k in scores if k != best and scores[k] > 40]

    return {
        'recommendation': best,
        'confidence': round(confidence, 1),
        'reasoning': '; '.join(reasoning_parts) if reasoning_parts else 'Based on composition analysis',
        'alternative_uses': alternatives
    }


def _recommend_manganese(manganese_percent, iron_oxide_percent):
    """Recommend use for manganese alloy by-product."""
    if manganese_percent > 40:
        return {
            'recommendation': 'further_processing',
            'confidence': 88.0,
            'reasoning': f'High Mn content ({manganese_percent:.1f}%) suitable for manganese alloy production',
            'alternative_uses': ['iron_recovery']
        }
    elif manganese_percent > 20:
        return {
            'recommendation': 'further_processing',
            'confidence': 72.0,
            'reasoning': f'Moderate Mn content ({manganese_percent:.1f}%) for alloy processing',
            'alternative_uses': ['cement_additive']
        }
    else:
        return {
            'recommendation': 'cement_additive',
            'confidence': 60.0,
            'reasoning': f'Low Mn content ({manganese_percent:.1f}%) better suited for cement additive',
            'alternative_uses': ['road_construction']
        }


def _recommend_silica(silica_percent, alumina_percent):
    """Recommend use for silica residue."""
    if silica_percent > 60:
        return {
            'recommendation': 'cement_additive',
            'confidence': 85.0,
            'reasoning': f'High SiO₂ content ({silica_percent:.1f}%) excellent for cement production',
            'alternative_uses': ['road_construction']
        }
    elif silica_percent > 30:
        return {
            'recommendation': 'road_construction',
            'confidence': 70.0,
            'reasoning': f'SiO₂ ({silica_percent:.1f}%) suitable for road construction aggregate',
            'alternative_uses': ['cement_additive']
        }
    else:
        return {
            'recommendation': 'soil_amendment',
            'confidence': 55.0,
            'reasoning': f'Low silica content ({silica_percent:.1f}%) suitable for soil amendment',
            'alternative_uses': ['disposal']
        }


def get_recommendation_display(recommendation_key):
    """Get human-readable display name for recommendation."""
    displays = {
        'cement_additive': 'Cement Additive',
        'iron_recovery': 'Iron Recovery',
        'rare_earth_extraction': 'Rare Earth Extraction',
        'road_construction': 'Road Construction',
        'soil_amendment': 'Soil Amendment',
        'further_processing': 'Further Processing',
        'disposal': 'Safe Disposal'
    }
    return displays.get(recommendation_key, recommendation_key)


def get_recommendation_icon(recommendation_key):
    """Get Bootstrap icon for recommendation type."""
    icons = {
        'cement_additive': 'bi-building',
        'iron_recovery': 'bi-gear-fill',
        'rare_earth_extraction': 'bi-gem',
        'road_construction': 'bi-truck',
        'soil_amendment': 'bi-tree',
        'further_processing': 'bi-arrow-repeat',
        'disposal': 'bi-trash'
    }
    return icons.get(recommendation_key, 'bi-question-circle')
