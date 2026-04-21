import re
import math
from collections import Counter

def clean_punctuation(text: str) -> str:
    text = text.replace('——', '\x00').replace('……', '\x01')
    text = re.sub(r'[，。！？、；：“”‘’（）【】《》「」『』…—~!?,.:;\'\"()\[\]{}<>]', '', text)
    return text.replace('\x00', '——').replace('\x01', '……')


def _ngrams(text, ns=(1, 2)):
    grams = []
    for n in ns:
        for i in range(len(text) - n + 1):
            grams.append(text[i:i+n])
    return grams

def _tf_vector(grams):
    counts = Counter(grams)
    total = len(grams)
    return {g: c / total for g, c in counts.items()} if total else {}

class Ranker:
    def __init__(self, idf, entries):
        self.idf = idf
        self.entries = entries

def build_ranker(dict_path: str) -> 'Ranker':
    try:
        with open(dict_path, encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(f'Dictionary not found: {dict_path}')
    if not lines:
        raise FileNotFoundError(f'Dictionary is empty: {dict_path}')

    N = len(lines)
    df: Counter = Counter()
    entry_grams = []
    for line in lines:
        grams = _ngrams(line)
        entry_grams.append(grams)
        for g in set(grams):
            df[g] += 1

    idf = {g: math.log((N + 1) / (cnt + 1)) for g, cnt in df.items()}

    entries = []
    for grams in entry_grams:
        tf = _tf_vector(grams)
        vec = {g: tf[g] * idf.get(g, 0.0) for g in tf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 0.0
        entries.append((vec, norm))

    return Ranker(idf, entries)


def _candidate_string(segments):
    return ''.join(words[0] if words else '' for _key, words in segments)

def _cosine(cand_vec, cand_norm, entry_vec, entry_norm):
    if cand_norm == 0.0 or entry_norm == 0.0:
        return 0.0
    dot = sum(cand_vec.get(g, 0.0) * w for g, w in entry_vec.items())
    return dot / (cand_norm * entry_norm)

def rerank(candidates, ranker: Ranker):
    if len(candidates) <= 1:
        return candidates

    def tfidf_score(candidate):
        dp_score, segments = candidate
        text = clean_punctuation(_candidate_string(segments))
        grams = _ngrams(text)
        tf = _tf_vector(grams)
        vec = {g: tf[g] * ranker.idf.get(g, 0.0) for g in tf}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 0.0
        best = max(
            (_cosine(vec, norm, ev, en) for ev, en in ranker.entries),
            default=0.0
        )
        return (best, dp_score)

    return sorted(candidates, key=tfidf_score, reverse=True)
