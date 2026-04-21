import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import lm as lm_module
from lm import build_lm_scorer, lm_score

def test_build_lm_scorer_returns_none_without_transformers(monkeypatch):
    monkeypatch.setattr(lm_module, '_LM_AVAILABLE', False)
    monkeypatch.setattr(lm_module, '_cached_scorer', None)
    result = build_lm_scorer()
    assert result is None

def test_lm_score_returns_zero_for_none():
    assert lm_score('你好', None) == 0.0

def test_lm_score_returns_zero_for_empty():
    assert lm_score('', None) == 0.0

def test_lm_score_returns_float_when_available():
    transformers = pytest.importorskip('transformers')
    scorer = build_lm_scorer()
    if scorer is None:
        pytest.skip('transformers/torch not installed')
    score = lm_score('你好世界', scorer)
    assert isinstance(score, float)
    assert score < 0.0

import pytest
