import json
import requests

BASE = 'https://www.akedata.top'
OUTPUT_FILE = 'endfield_dict.txt'

MANIFESTS = [
    '/public/CH/character/manifest.json',  # name field
    '/public/CH/weapon/manifest.json',     # title field
    '/public/CH/item/manifest.json',       # name field
    '/public/CH/enemy/manifest.json',      # name field
]

def fetch_json(path, session):
    r = session.get(BASE + path, timeout=10)
    r.raise_for_status()
    return r.json()

def extract_names(data, path):
    names = set()
    field = 'title' if 'weapon' in path else 'name'
    for entry in data:
        val = entry.get(field, '')
        if val:
            names.add(val)
    return names

def scrape():
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (compatible; SarkazBot/1.0)'

    all_terms = set()
    for path in MANIFESTS:
        print(f'[*] Fetching {path}...')
        try:
            data = fetch_json(path, session)
            names = extract_names(data, path)
            all_terms.update(names)
            print(f'    +{len(names)} terms')
        except Exception as e:
            print(f'[!] Failed {path}: {e}')

    return all_terms

if __name__ == '__main__':
    terms = scrape()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for term in sorted(terms):
            f.write(term + '\n')
    print(f'\n[√] Saved {len(terms)} terms to {OUTPUT_FILE}')
