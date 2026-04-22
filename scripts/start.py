import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from main import ensure_map_csv, cipher_key, REMAINDER_MAP
from scraper import scrape

ROOT = Path(__file__).parent.parent
ENDFIELD_FILE = str(ROOT / 'endfield_dict.txt')
CIPHER_FILE = str(ROOT / 'cipher_dict.json')


def build_cipher_dict():
    print('[*] 构建密码字典...')
    terms = []
    if os.path.exists(ENDFIELD_FILE):
        with open(ENDFIELD_FILE, encoding='utf-8') as f:
            terms = [l.strip() for l in f if l.strip()]

    d = {}
    for t in terms:
        key = cipher_key(t)
        if key not in d:
            d[key] = []
        if t not in d[key]:
            d[key].append(t)

    with open(CIPHER_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    print(f'    → {len(d)} 个密钥已保存至 {CIPHER_FILE}')
    return d


def load_cipher_dict():
    if os.path.exists(CIPHER_FILE):
        with open(CIPHER_FILE, encoding='utf-8') as f:
            d = json.load(f)
        if d and isinstance(next(iter(d.values())), list):
            return d
    return build_cipher_dict()


_FULLWIDTH_PUNCT = set('，。？！：；、…""''《》【】（）—～·')


def encode(text):
    result = []
    for ch in text:
        if ch in _FULLWIDTH_PUNCT or '一' <= ch <= '鿿':
            result.append(REMAINDER_MAP[ord(ch) % 56])
        elif ch.isascii() and ch.isalpha():
            result.append(ch)
        else:
            result.append('[?]')
    return ''.join(result)


def decode(s, d):
    s = s.lower()
    result = []
    i = 0
    max_word_len = max((len(k) for k in d), default=1)

    while i < len(s):
        best_len = 0
        best_text = None

        for length in range(min(max_word_len, len(s) - i), 0, -1):
            key = s[i:i+length]
            entry = d.get(key)
            if entry:
                best_len = length
                best_text = entry[0]
                break

        if best_text:
            result.append(best_text)
            i += best_len
        else:
            result.append('[?]')
            i += 1

    return ''.join(result)


def run_lookup(d):
    print('\n请选择模式: decode (解密) / encode (加密)', end='  ')
    while True:
        mode = input().strip().lower()
        if mode in ('decode', 'encode'):
            break
        print('  请输入 decode 或 encode: ', end='')

    prompt = '密文: ' if mode == 'decode' else '明文: '
    print(f'\n已进入{"解密" if mode == "decode" else "加密"}模式。输入 q 退出，输入 "update" 更新词典。\n')

    while True:
        s = input(prompt).strip()
        if not s:
            continue
        if s.lower() in ('q', 'quit', 'exit'):
            break
        if s.lower() == 'update':
            print()
            terms = scrape()
            with open(ENDFIELD_FILE, 'w', encoding='utf-8') as f:
                for t in sorted(terms):
                    f.write(t + '\n')
            d.clear()
            d.update(build_cipher_dict())
            print('  → 词典已更新。\n')
            continue

        if mode == 'decode':
            print(f'  → {decode(s, d)}\n')
        else:
            print(f'  → {encode(s)}\n')


def main():
    ensure_map_csv()

    if not os.path.exists(ENDFIELD_FILE):
        print('[1/2] 未找到词库，正在抓取...')
        terms = scrape()
        with open(ENDFIELD_FILE, 'w', encoding='utf-8') as f:
            for t in sorted(terms):
                f.write(t + '\n')
        print(f'    → {len(terms)} 个词条已保存。\n')

    d = load_cipher_dict()
    run_lookup(d)


if __name__ == '__main__':
    main()
