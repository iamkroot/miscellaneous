from urllib.parse import urljoin
from pathlib import Path
import os
import re

FILES_LIST = "./files_list.txt"
BASE_URL = "https://archive.org/download/academictorrents_e31e54905c7b2669c81fe164de2859be4697013a/"
DOWNLOAD_DIR = Path("~/Downloads/compilers").expanduser()


def read_file_paths():
    PATTERN = re.compile(r"(?P<path>.*?)\s+\d+\s+(?P=path)")
    with open(FILES_LIST) as f:
        for line in f:
            yield PATTERN.match(line)["path"]


def filter_paths(path):
    return ".thumbs" not in path and not path.endswith(".ogv")


with open("urls.txt", 'w') as f:
    for path in filter(filter_paths, read_file_paths()):
        url = urljoin(BASE_URL, path)
        dir_ = DOWNLOAD_DIR / os.path.dirname(path)
        print(f"{url}\n dir={dir_}\n", file=f)
