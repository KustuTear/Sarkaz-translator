import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ranker import clean_punctuation

def test_preserves_em_dash():
    assert clean_punctuation('萨卡兹——终焉') == '萨卡兹——终焉'

def test_preserves_ellipsis():
    assert clean_punctuation('等待……归来') == '等待……归来'

def test_strips_common_punct():
    assert clean_punctuation('你好，世界。') == '你好世界'

def test_noop_on_plain():
    assert clean_punctuation('陈千语') == '陈千语'

def test_noop_on_empty():
    assert clean_punctuation('') == ''


import tempfile
from ranker import build_ranker

def _make_dict(lines):
    f = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False)
    f.write('\n'.join(lines))
    f.close()
    return f.name

def test_build_ranker_missing_file():
    import pytest
    with pytest.raises(FileNotFoundError):
        build_ranker('/nonexistent/path.txt')

def test_build_ranker_empty_file():
    import pytest
    path = _make_dict([])
    with pytest.raises(FileNotFoundError):
        build_ranker(path)

def test_build_ranker_returns_ranker():
    path = _make_dict(['陈千语', '萨卡兹', '终焉'])
    r = build_ranker(path)
    assert r is not None

def test_ranker_has_idf_for_known_ngram():
    path = _make_dict(['陈千语', '萨卡兹'])
    r = build_ranker(path)
    assert r.idf.get('陈', 0) > 0

def test_ranker_entry_count():
    path = _make_dict(['陈千语', '萨卡兹', '终焉'])
    r = build_ranker(path)
    assert len(r.entries) == 3


from ranker import rerank

def test_rerank_single_candidate():
    path = _make_dict(['陈千语'])
    r = build_ranker(path)
    candidates = [(10, [('gds', ['陈千语'])])]
    result = rerank(candidates, r)
    assert result == candidates

def test_rerank_orders_by_similarity():
    path = _make_dict(['陈千语', '萨卡兹'])
    r = build_ranker(path)
    cand_a = (5, [('gds', ['陈千语'])])
    cand_b = (8, [('xyz', ['无关词'])])
    result = rerank([cand_b, cand_a], r)
    assert result[0][1] == cand_a[1]

def test_rerank_tiebreak_by_dp_score():
    path = _make_dict(['测试'])
    r = build_ranker(path)
    cand_hi = (10, [('abc', ['测试'])])
    cand_lo = (3,  [('abc', ['测试'])])
    result = rerank([cand_lo, cand_hi], r)
    assert result[0][0] == 10

def test_rerank_no_overlap_scores_zero():
    path = _make_dict(['陈千语'])
    r = build_ranker(path)
    cand = (5, [('zzz', ['ωωω'])])
    result = rerank([cand], r)
    assert result[0] == cand

def test_rerank_preserves_tuple_structure():
    path = _make_dict(['陈千语'])
    r = build_ranker(path)
    candidates = [(7, [('gds', ['陈千语'])]), (3, [('ab', ['萨卡'])])]
    result = rerank(candidates, r)
    for orig_score, orig_segs in candidates:
        assert any(score == orig_score and segs == orig_segs for score, segs in result)


from ranker import RankerConfig

def test_rerank_config_defaults():
    cfg = RankerConfig()
    assert cfg.w1 == 0.6
    assert cfg.w2 == 0.4
    assert cfg.top_n_for_lm == 10

def test_rerank_no_lm_backward_compatible():
    path = _make_dict(['陈千语', '萨卡兹'])
    r = build_ranker(path)
    cand_a = (5, [('gds', ['陈千语'])])
    cand_b = (8, [('xyz', ['无关词'])])
    result_old = rerank([cand_b, cand_a], r)
    result_new = rerank([cand_b, cand_a], r, lm_scorer=None)
    assert result_old == result_new

def test_rerank_with_mock_lm(monkeypatch):
    import lm as lm_module
    path = _make_dict(['陈千语', '萨卡兹'])
    r = build_ranker(path)
    # cand_a has low TF-IDF but high LM score; cand_b has high TF-IDF but low LM score
    cand_a = (5, [('gds', ['陈千语'])])
    cand_b = (8, [('xyz', ['无关词'])])

    scores = {'陈千语': -1.0, '无关词': -10.0}
    monkeypatch.setattr(lm_module, 'lm_score', lambda text, scorer: scores.get(text, -5.0))

    class FakeScorer:
        pass

    result = rerank([cand_b, cand_a], r, lm_scorer=FakeScorer(), config=RankerConfig(w1=0.0, w2=1.0))
    # With w1=0, only LM matters — 陈千语 (-1.0) should beat 无关词 (-10.0)
    assert result[0][1] == cand_a[1]
