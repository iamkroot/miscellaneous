#!/usr/bin/env python
import difflib
import json
import os
import re
import sys
from pathlib import Path

script_dir = Path(__file__).parent


def load_config():
    try:
        with open(script_dir / 'config.json') as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print("Config not found.")
        exit(2)
    except json.JSONDecodeError:
        print("Invalid config")
        exit(128)
    paths = {}
    for name, path in cfg['paths'][sys.platform].items():
        path = Path(os.path.expandvars(path))
        if not path.is_absolute():
            path = script_dir / path
        paths[name] = path
    cfg['paths'] = paths
    return cfg


def find_appl_dir(viv_dir):
    if os.name != 'nt':
        return viv_dir
    for appl_dir in list(viv_dir.iterdir()):
        if appl_dir.is_dir() and re.match(r'(\d+\.){3}\d+', appl_dir.name):
            return appl_dir

    print("Couldn't determine app folder!")
    exit(1)


def patch(patch_dir, viv_dir, **kwargs):
    assert patch_dir.exists(), "Invalid patch folder"
    assert viv_dir.exists(), "Invalid vivaldi installation folder"

    appl_dir = find_appl_dir(viv_dir)
    dest_dir = appl_dir / 'resources' / 'vivaldi'
    assert dest_dir.exists(), "Invalid vivaldi installation folder"
    print('Destination folder:', dest_dir)
    PAIRS = (
        (patch_dir / 'browser.html', dest_dir / 'browser.html'),
        (patch_dir / 'custom.css', dest_dir / 'style' / 'custom.css'),
        # (patch_dir / 'custom.js', dest_dir / 'style' / 'custom.js')
    )
    for src, dest in PAIRS:
        if not src.exists():
            print(src, "not found. Skipping.")
            continue
        with open(src) as s, open(dest, 'w') as d:
            print('Writing', dest.name)
            d.write(s.read())


def print_changelog():
    try:
        import requests
    except ImportError:
        print("Need requests module to fetch changelog.")
        return
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Need bs4 module to fetch changelog.")
        return

    def get_changelog(url):
        resp = requests.get(snap_url)
        soup = BeautifulSoup(resp.text, "html5lib")
        content = soup.find('div', {'class': "entry-content"})
        return content.find_all('ul')[-1].text.strip()

    BASE_URL = "https://vivaldi.com/blog/snapshots/"
    resp = requests.get(BASE_URL)
    soup = BeautifulSoup(resp.text, "html5lib")
    for post in soup.select("header.article-header"):
        title = post.h1.text
        if "android" in title.lower():
            continue
        snap_url = post.a['href']
        print("Snapshot URL:", snap_url)
        print(title, post.p.text)
        return print(get_changelog(snap_url))
    print("Couldn't find proper snapshot to fetch changelog.")


def get_all_sites(parent):
    """Get info about bookmarks inside the current directory, recursively."""
    for child in parent['children']:
        if child['type'] == 'url':
            yield child
        elif child['type'] == 'folder':
            yield from get_all_sites(child)


def get_speeddial_items(bookmarks_file):
    with open(bookmarks_file) as f:
        bookmarks = json.load(f)
    for child in bookmarks["roots"]["bookmark_bar"]["children"]:
        if child.get('meta_info', {}).get('Speeddial') == 'true':
            yield from get_all_sites(child)


def get_thumbs(bookmarks_file, thumbs_dir: Path):
    thumb_files = list(thumbs_dir.glob('*.[jp][pn]g'))
    thumbs = {thumb.stem.lower(): thumb for thumb in thumb_files}
    for bookmark in get_speeddial_items(bookmarks_file):
        m = difflib.get_close_matches(bookmark['name'].lower(), thumbs, n=1)
        if not m:
            print("Could not find thumbnail for", bookmark['name'])
            continue
        yield bookmark['id'], thumbs[m[0]]


def update_thumbs(bookmarks_file, thumbs_dir, **kwargs):
    for bkmk, thumb_file in get_thumbs(bookmarks_file, thumbs_dir):
        pass


def main():
    cfg = load_config()
    patch(**cfg['paths'])
    print_changelog()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Error occurred", e)
        exit(1)
