"""GLiNER client singleton for zero-shot PII entity detection.

Loads knowledgator/gliner-pii-small-v1.0 (with fallback to edge model if required)
and provides a unified detect() function used by name, company, and address detectors.
"""

from typing import List, Dict, Any
from gliner import GLiNER

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = GLiNER.from_pretrained("knowledgator/gliner-pii-edge-v1.0")
        except Exception as e:
            print(f"[gliner_client] Small model load failed: {e}. Falling back to edge model...")
            _model = GLiNER.from_pretrained("knowledgator/gliner-pii-edge-v1.0")
    return _model


def detect(text: str, labels: List[str], threshold: float = 0.3) -> List[Dict[str, Any]]:
    """Detect entity spans in *text* matching the given *labels* above *threshold*.

    Returns a list of dicts:
        [{'text': str, 'label': str, 'start': int, 'end': int, 'score': float}, ...]
    """
    if not text or not text.strip():
        return []
    model = get_model()
    entities = model.predict_entities(text, labels, threshold=threshold)
    return entities
