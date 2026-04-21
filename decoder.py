import json
import os
from ranker import clean_punctuation

CIPHER_DICT_FILE = 'cipher_dict.json'

# Priority scores for DP
SCORE = {'endfield': 3, 'common_multi': 2, 'common_single': 1}

def load_dict():
    if not os.path.exists(CIPHER_DICT_FILE):
        raise FileNotFoundError(f'{CIPHER_DICT_FILE} not found — run build_dict.py first.')
    with open(CIPHER_DICT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def best_words(entry):
    """Return candidate list: endfield > punct > common."""
    return entry.get('endfield') or entry.get('punct') or entry.get('common') or []

def score_entry(entry, word_len):
    if entry.get('endfield'):
        base = SCORE['endfield']
    elif word_len > 1:
        base = SCORE['common_multi']
    else:
        base = SCORE['common_single']
    return base * word_len

def decode(s, cipher_dict):
    n = len(s)
    # dp[i] = (score, prev_index, chosen_words)
    dp = [None] * (n + 1)
    dp[0] = (0, -1, [])

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] is None:
                continue
            key = s[j:i]
            if key not in cipher_dict:
                continue
            entry = cipher_dict[key]
            seg_score = score_entry(entry, i - j)
            total = dp[j][0] + seg_score
            if dp[i] is None or total > dp[i][0]:
                dp[i] = (total, j, entry)

    if dp[n] is None:
        return None  # no full segmentation found

    # Backtrack
    segments = []
    pos = n
    while pos > 0:
        _, prev, entry = dp[pos]
        key = s[prev:pos]
        # Pick best word from entry: prefer endfield, then punct, then common
        words = best_words(entry)
        segments.append((key, words))
        pos = prev
    segments.reverse()
    return segments

def all_words(entry):
    """Return all candidates: endfield first, then punct, then common."""
    ef = entry.get('endfield', [])
    pt = entry.get('punct', [])
    cm = entry.get('common', [])
    return ef + pt + cm or []

def decode_topn(s, cipher_dict, n=3, max_enum=200):
    results = []
    counter = [0]

    def dfs(pos, path, score):
        if counter[0] >= max_enum:
            return
        if pos == len(s):
            results.append((score, list(path)))
            counter[0] += 1
            return
        for end in range(pos + 1, len(s) + 1):
            key = s[pos:end]
            if key not in cipher_dict:
                continue
            entry = cipher_dict[key]
            seg_score = score_entry(entry, end - pos)
            words = all_words(entry)
            path.append((key, words))
            dfs(end, path, score + seg_score)
            path.pop()

    dfs(0, [], 0)
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:n]

if __name__ == '__main__':
    cipher_dict = load_dict()
    user_input = input('请输入密文字母串 (例如 gds): ').strip().lower()
    if not user_input:
        print('No input.')
    else:
        topn = decode_topn(user_input, cipher_dict, n=3)
        if not topn:
            print(f'[!] 无法完整解码 "{user_input}"，尝试逐字母查找...')
            for ch in user_input:
                entry = cipher_dict.get(ch, {})
                words = best_words(entry)
                print(f'  {ch} → {", ".join(words[:5]) or "未知"}')
        else:
            print('\n[解码结果]')
            for rank, (score, segments) in enumerate(topn, 1):
                decoded = clean_punctuation(''.join(w[0] if w else f'[{k}]' for k, w in segments))
                print(f'  #{rank} (score={score}): {decoded}')
                for k, w in segments:
                    alts = ', '.join(w[:6]) if w else '?'
                    print(f'    {k} → {alts}')
            best = clean_punctuation(''.join(w[0] if w else f'[{k}]' for k, w in topn[0][1]))
            print(f'\n最佳解码: {best}')
