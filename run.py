import os
import sys
import json
import csv
import re
import time
import requests
from ranker import build_ranker, rerank, clean_punctuation, RankerConfig
from lm import build_lm_scorer

try:
    from decoder import decode_topn
    _HAS_TOPN = True
except ImportError:
    _HAS_TOPN = False

BASE = 'https://www.akedata.top'
MANIFESTS = [
    '/public/CH/character/manifest.json',
    '/public/CH/weapon/manifest.json',
    '/public/CH/item/manifest.json',
    '/public/CH/enemy/manifest.json',
]
REMAINDER_MAP = ['g','k','a','m','z','t','l','b','d','q','i','y','f','u','c','x','b','h','s','j',
                 'o','p','r','n','w','e','y','g','t','j','m','e','v','c','h','d','x','s','a','n',
                 'q','o','l','k','r','v','w','i','y','p','j','z','q','u','h','e']
ENDFIELD_FILE = 'endfield_dict.txt'
CIPHER_FILE = 'cipher_dict.json'

# ── Step 1: Scrape ────────────────────────────────────────────────────────────

def scrape():
    print('[1/3] 抓取 Endfield 词库...')
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0'
    terms = set()
    for path in MANIFESTS:
        try:
            r = session.get(BASE + path, timeout=10)
            r.raise_for_status()
            data = r.json()
            field = 'title' if 'weapon' in path else 'name'
            for entry in data:
                v = entry.get(field, '')
                if v:
                    terms.add(v)
        except Exception as e:
            print(f'    [!] {path}: {e}')
    with open(ENDFIELD_FILE, 'w', encoding='utf-8') as f:
        for t in sorted(terms):
            f.write(t + '\n')
    print(f'    → {len(terms)} 个词条已保存至 {ENDFIELD_FILE}')
    return terms

# ── Step 2: Build dict ────────────────────────────────────────────────────────

def get_common_chars():
    chars = []
    for q in range(16, 56):
        for w in range(1, 95):
            try:
                chars.append(bytes([q + 0xA0, w + 0xA0]).decode('gb2312'))
            except:
                pass
    return set(chars)

def cipher_key(word):
    return ''.join(REMAINDER_MAP[ord(c) % 56] for c in word)

def build_dict(endfield_terms):
    print('[2/3] 构建密码字典...')
    common = get_common_chars()
    d = {}

    def add(key, word, src):
        if key not in d:
            d[key] = {'endfield': [], 'common': []}
        if word not in d[key][src]:
            d[key][src].append(word)

    for t in endfield_terms:
        add(cipher_key(t), t, 'endfield')
    for c in common:
        add(cipher_key(c), c, 'common')

    with open(CIPHER_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print(f'    → {len(d)} 个密钥已保存至 {CIPHER_FILE}')
    return d

# ── Step 3: Decode ────────────────────────────────────────────────────────────

def decode(s, d):
    n = len(s)
    dp = [None] * (n + 1)
    dp[0] = (0, 0, None)
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] is None:
                continue
            key = s[j:i]
            if key not in d:
                continue
            entry = d[key]
            seg_len = i - j
            base = 3 if entry['endfield'] else (2 if seg_len > 1 else 1)
            score = base * seg_len
            total = dp[j][0] + score
            if dp[i] is None or total > dp[i][0]:
                dp[i] = (total, j, entry)
    if dp[n] is None:
        return None
    segs = []
    pos = n
    while pos > 0:
        _, prev, entry = dp[pos]
        words = entry.get('endfield') or entry.get('punct') or entry.get('common') or []
        segs.append((s[prev:pos], words))
        pos = prev
    segs.reverse()
    return segs

def refresh_dict():
    terms = scrape()
    return build_dict(terms)

def run_decoder(d, ranker, lm_scorer=None):
    print('解码器就绪。输入 "update dic" 更新词典，输入 q 退出。\n')
    while True:
        s = input('请输入密文字母串: ').strip()
        if s.lower() in ('q', 'quit', 'exit'):
            break
        if s.lower() == 'update dic':
            print()
            d = refresh_dict()
            print('  → 词典已更新。\n')
            continue
        if not s:
            continue
        segs = decode(s.lower(), d)
        if segs is None:
            print('  [!] 无法完整解码，逐字母查找:')
            for ch in s.lower():
                entry = d.get(ch, {})
                words = entry.get('endfield') or entry.get('punct') or entry.get('common') or []
                print(f'    {ch} → {", ".join(words[:5]) or "未知"}')
        else:
            best = []
            for key, words in segs:
                top = words[0]
                best.append(top)
                alts = ', '.join(words[1:9])
                print(f'  {key} → {top}' + (f'  (备选: {alts})' if alts else ''))
            print(f'\n  最佳解码: {clean_punctuation("".join(best))}')
            if _HAS_TOPN:
                topn = decode_topn(s.lower(), d, n=5)
                topn = rerank(topn, ranker, lm_scorer=lm_scorer)
                if len(topn) > 1:
                    print('\n  [候选分词]')
                    for rank, (sc, segments) in enumerate(topn, 1):
                        decoded = clean_punctuation(''.join(w[0] if w else f'[{k}]' for k, w in segments))
                        detail = ' + '.join(f'{k}({w[0] if w else "?"})' for k, w in segments)
                        print(f'    #{rank} (score={sc}): {decoded}  [{detail}]')
            print()

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if os.path.exists(CIPHER_FILE):
        with open(CIPHER_FILE, encoding='utf-8') as f:
            d = json.load(f)
        print(f'[✓] 使用缓存字典 ({len(d)} 密钥)。\n')
    else:
        terms = scrape()
        d = build_dict(terms)
        print()

    ranker = build_ranker(ENDFIELD_FILE)
    print(f'[✓] 排名器已就绪。\n')
    lm_scorer = build_lm_scorer()
    if lm_scorer is not None:
        print('[✓] LM 评分器已就绪 (uer/gpt2-chinese-cluecorpussmall)。\n')
    else:
        print('[!] transformers/torch 未安装，仅使用 TF-IDF 排名。\n')
    run_decoder(d, ranker, lm_scorer)
