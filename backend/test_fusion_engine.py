import pytest
from models.fusion_engine import FusionEngine

def test_fusion_initialization():
    engine = FusionEngine()
    assert engine.emotions == ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

def test_single_modality_fusion():
    engine = FusionEngine()
    visual_data = {'emotions': {'Happy': 0.8, 'Sad': 0.1, 'Neutral': 0.1}}
    result = engine.fuse(visual_data, None, None, ['visual'])
    
    assert 'Happy' in result
    assert result['Happy'] > 0.7 # Due to normalization, it might slightly shift, but should be dominant
    assert sum(result.values()) == pytest.approx(1.0)

def test_multi_modality_fusion():
    engine = FusionEngine()
    visual_data = {'emotions': {'Happy': 0.6, 'Sad': 0.2, 'Neutral': 0.2}}
    audio_data = {'emotions': {'Happy': 0.4, 'Sad': 0.1, 'Neutral': 0.5}}
    
    result = engine.fuse(visual_data, None, audio_data, ['visual', 'audio'])
    
    assert result['Happy'] > result['Sad']
    # The sum of average should be close to 1
    assert sum(result.values()) == pytest.approx(1.0)

def test_text_transformer_lexicon_fusion():
    engine = FusionEngine()
    text_data = {
        'lexicon': {'Angry': 0.5, 'Neutral': 0.5},
        'transformer': {'Angry': 0.9, 'Neutral': 0.1}
    }
    
    result = engine.fuse(None, text_data, None, ['text'])
    
    # Internal text fusion averages them out
    assert result['Angry'] > 0.6
    assert sum(result.values()) == pytest.approx(1.0)

def test_no_active_modalities():
    engine = FusionEngine()
    result = engine.fuse(None, None, None, [])
    
    # Should return all zeros
    for e in engine.emotions:
        assert result[e] == 0.0
