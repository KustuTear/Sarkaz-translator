# Design: ranker.py — TF-IDF Re-ranker for Sarkaz Cipher Decoder

**Date:** 2026-04-21  
**Status:** Approved

---

## 1. Purpose

The decoder's `decode_topn` returns multiple candidate segmentations ranked by a DP score that favours longer Endfield matches. This score does not account for how "Endfield-like" the full decoded string reads. OCR-style noise (e.g. `陈前语` vs `陈千语`) can slip through because individual segment scores look identical.

`ranker.py` adds a second-pass re-ranker: it scores each full candidate string by its maximum cosine similarity to any single entry in `endfield_dict.txt`, using pure-Python TF-IDF over character n-grams. The candidate list is re-sorted by this score; the original DP scores and segment data are never modified.

---

## 2. Public API

```python
# ranker.py

def clean_punctuation(text: str) -> str: ...
def build_ranker(dict_path: str) -> Ranker: ...
def rerank(candidates: list[tuple], ranker: Ranker) -> list[tuple]: ...
```

### `clean_punctuation(text)`
Normalises punctuation in a decoded Chinese string before scoring or display.
- Preserves `——` (em-dash) and `……` (ellipsis) as-is.
- Strips or normalises other punctuation as needed.
- Pure string transformation; safe on any input; no-op if no matching patterns.
- **Shared utility** — imported by `run.py` and `decoder.py` for UI/display cleanup.

### `build_ranker(dict_path)`
Loads `endfield_dict.txt` and builds the TF-IDF index.
- Raises `FileNotFoundError` if `dict_path` is missing or the file is empty.
- Returns a `Ranker` object (opaque to callers) holding the IDF table and per-entry vectors.
- Called **once at startup** in `run.py`.

### `rerank(candidates, ranker)`
Re-ranks the `decode_topn` output.
- `candidates`: list of `(dp_score, segments)` tuples as returned by `decode_topn`.
- Returns the **same list**, sorted descending by TF-IDF similarity score.
- Ties in TF-IDF score are broken by the original `dp_score` (descending).
- The `dp_score` and `segments` values inside each tuple are never mutated.

---

## 3. Algorithm

### 3.1 Setup — `build_ranker`

1. Read every non-empty line of `endfield_dict.txt`; each line is one corpus entry.
2. Extract character n-grams (n=1 and n=2) from each entry as a term-frequency map:
   `tf(t, entry) = count(t in entry) / total_ngrams(entry)`
3. Build IDF over the corpus (N = total entries):
   `idf(t) = log((N + 1) / (df(t) + 1))`
   where `df(t)` = number of entries containing term `t`. Smoothing prevents zero division.
4. Compute each entry's TF-IDF weight vector:
   `w(t, entry) = tf(t, entry) * idf(t)`
5. Pre-compute each entry's L2 norm:
   `norm(entry) = sqrt(sum(w(t, entry)^2 for t in entry))`
6. Store all `(weight_vector, norm)` pairs in the `Ranker`.

### 3.2 Scoring a Candidate — `rerank`

For each `(dp_score, segments)` tuple:

1. Join all segment words to form the full decoded string.
2. Pass through `clean_punctuation`.
3. Extract character n-grams (n=1,2) and compute the candidate's TF-IDF weight vector using the **same IDF table** built in setup. Compute the candidate's L2 norm.
4. For each dictionary entry vector, compute cosine similarity:
   ```
   sim = sum(w_cand(t) * w_entry(t) for t in intersection)
         / (norm_cand * norm_entry)
   ```
   If either norm is zero, similarity = 0.0.
5. Candidate's final score = **max** similarity across all entry vectors.

### 3.3 Sorting

Sort candidates descending by `(tfidf_score, dp_score)`. The original tuple structure is preserved; only list order changes.

---

## 4. Edge Cases

| Situation | Behaviour |
|---|---|
| `endfield_dict.txt` missing or empty | `build_ranker` raises `FileNotFoundError` |
| Candidate has no n-gram overlap with any entry | similarity = 0.0; ranked by dp_score tiebreak |
| Zero-length decoded string | similarity = 0.0 |
| Single candidate in list | returned immediately, no sorting needed |
| `clean_punctuation` on non-Chinese input | no-op, safe |

---

## 5. Integration

```python
# run.py (startup)
from ranker import build_ranker, rerank, clean_punctuation

ranker = build_ranker('endfield_dict.txt')

# run.py (per decode)
candidates = decode_topn(s.lower(), cipher_dict, n=5)
candidates = rerank(candidates, ranker)
```

`decoder.py` imports `clean_punctuation` for display formatting only; it does not call `rerank`.

---

## 6. Constraints

- Zero external dependencies (stdlib only: `math`, `collections`, `re`).
- No modifications to `decode_topn` output structure.
- `build_ranker` is called once; `rerank` is called per user query.
