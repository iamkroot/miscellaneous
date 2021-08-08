"""
Splits the given Manga Volume CBZ into the CBZs of the individual chapters 
"""

import re
import shutil
import zipfile
from collections import defaultdict
from operator import attrgetter
from pathlib import Path

root = Path("/path/to/volumes/")
output = root / "chapters"
CHAP_PAT = re.compile(r"c(?P<num>\d{3})")


def process_volume(archive: zipfile.ZipFile):
    chapters: dict[str, list[zipfile.ZipInfo]] = defaultdict(list)
    for page in archive.filelist:
        m = CHAP_PAT.search(page.filename)
        assert m is not None, page
        chapters[m['num']].append(page)

    for chapter, pages in chapters.items():
        chap_dir = output / chapter
        print(chap_dir)
        chap_dir.mkdir(exist_ok=True, parents=True)
        archive.extractall(chap_dir, map(attrgetter("filename"), pages))
        with zipfile.ZipFile(chap_dir.with_suffix(".cbz"), "w") as chap_zip:
            chap_zip.write(chap_dir, chapter)
            # for page in chap_dir.iterdir():
            #     chap_zip.write(page, page.name)
        shutil.rmtree(chap_dir)


for file in root.iterdir():
    if file.suffix != ".cbz":
        continue
    with zipfile.ZipFile(file) as archive:
        process_volume(archive)
