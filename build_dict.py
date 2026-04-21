import csv
import json
import os

REMAINDER_MAP = ['g','k','a','m','z','t','l','b','d','q','i','y','f','u','c','x','b','h','s','j',
                 'o','p','r','n','w','e','y','g','t','j','m','e','v','c','h','d','x','s','a','n',
                 'q','o','l','k','r','v','w','i','y','p','j','z','q','u','h','e']

MAP_FILENAME = 'remainder_map.csv'
ENDFIELD_FILE = 'endfield_dict.txt'
OUTPUT_FILE = 'cipher_dict.json'

def get_gb2312_chars():
    """Returns (punct_set, common_set) from GB2312 zones 1-9 and 16-55."""
    punct, common = set(), set()
    for q in range(1, 10):   # zones 1-9: symbols and punctuation
        for w in range(1, 95):
            try:
                c = bytes([q + 0xA0, w + 0xA0]).decode('gb2312')
                punct.add(c)
            except:
                pass
    for q in range(16, 56):  # zones 16-55: GB2312 Level 1 Chinese characters
        for w in range(1, 95):
            try:
                c = bytes([q + 0xA0, w + 0xA0]).decode('gb2312')
                common.add(c)
            except:
                pass
    return punct, common

# Common Chinese punctuation sorted by priority (most common first)
_PUNCT_PRIORITY = list('，。？！：；、…""''《》【】（）—～·')
_CORE_PUNCT = set(_PUNCT_PRIORITY)

def _punct_sort_key(ch):
    try:
        return _PUNCT_PRIORITY.index(ch)
    except ValueError:
        return len(_PUNCT_PRIORITY)


def cipher_key(word):
    return ''.join(REMAINDER_MAP[ord(c) % 56] for c in word)

def load_endfield_terms():
    if not os.path.exists(ENDFIELD_FILE):
        print(f'[!] {ENDFIELD_FILE} not found — run scraper.py first. Skipping Endfield terms.')
        return []
    with open(ENDFIELD_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def build():
    print('[*] Loading GB2312 characters...')
    punct_chars, common_chars = get_gb2312_chars()

    print('[*] Loading Endfield terms...')
    endfield_terms = load_endfield_terms()

    # cipher_dict[key] = {"endfield": [...], "punct": [...], "common": [...]}
    cipher_dict = {}

    def add(key, word, source):
        if key not in cipher_dict:
            cipher_dict[key] = {'endfield': [], 'punct': [], 'common': []}
        if word not in cipher_dict[key][source]:
            cipher_dict[key][source].append(word)

    for term in endfield_terms:
        key = cipher_key(term)
        add(key, term, 'endfield')

    for char in sorted(punct_chars & _CORE_PUNCT, key=_punct_sort_key):
        key = cipher_key(char)
        add(key, char, 'punct')

    for char in common_chars:
        key = cipher_key(char)
        add(key, char, 'common')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cipher_dict, f, ensure_ascii=False, indent=2)

    print(f'[√] Built {len(cipher_dict)} cipher keys → {OUTPUT_FILE}')

if __name__ == '__main__':
    build()
