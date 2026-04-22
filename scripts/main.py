import csv
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
MAP_FILENAME = str(ROOT / 'remainder_map.csv')

REMAINDER_MAP = [
    'g','k','a','m','z','t','l','b','d','q','i','y','f','u','c','x','b','h','s','j',
    'o','p','r','n','w','e','y','g','t','j','m','e','v','c','h','d','x','s','a','n',
    'q','o','l','k','r','v','w','i','y','p','j','z','q','u','h','e'
]


def ensure_map_csv():
    if os.path.exists(MAP_FILENAME):
        return
    with open(MAP_FILENAME, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['remainder', 'letter'])
        for i, letter in enumerate(REMAINDER_MAP):
            writer.writerow([i, letter])


def cipher_key(word):
    return ''.join(REMAINDER_MAP[ord(c) % 56] for c in word)


if __name__ == '__main__':
    ensure_map_csv()
    print(f'[√] {MAP_FILENAME} ready.')
