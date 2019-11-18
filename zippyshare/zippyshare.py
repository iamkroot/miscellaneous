import shutil
import subprocess as sp

import requests
from bs4 import BeautifulSoup

IDM_PATH = r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"

JS_PRE = """
let obj = {};
let document = {getElementById: (id) => id === "dlbutton" ? obj : {}};

"""

JS_SUF = """
obj.href;
"""

run_js = False


class LinkNotFoundError(Exception):
    pass


def get_link(src, domain):
    try:
        soup = BeautifulSoup(src, "html5lib")
        div = soup.find("a", id="dlbutton").parent
        js = JS_PRE + div.script.text.strip() + JS_SUF
        global run_js
        if not run_js:
            choice = input("JS: " + js)
            if choice.lower() in ("y", "yes"):
                run_js = True
            else:
                return
        res = sp.run(["node", "-p", js], capture_output=True)
        link = res.stdout.decode()
        assert link
        return domain + link
    except Exception as e:
        print(e)
        raise LinkNotFoundError


def get_zippyshare_dl_link(url):
    r = requests.get(url)
    try:
        link = get_link(r.text, url[: url.find("/v")])
    except (IndexError, ValueError):
        raise LinkNotFoundError
    return link


def send_to_idm(link):
    cmd = [f'"{IDM_PATH}"', f'/d "{link}"', "/a"]
    sp.Popen(" ".join(cmd), shell=True)


def start_idm_queue():
    cmd = [f'"{IDM_PATH}"', "/s"]
    sp.Popen(" ".join(cmd), shell=True)


def download(link, title=None):
    r = requests.get(link, stream=True)
    if not title:
        cont = r.headers.get("Content-Disposition")
        if cont:
            ind = cont.rfind("'")
            title = cont[ind:]
        else:
            ind = link.find("/")
            title = link[ind:]
    with open(title, "wb") as f:
        shutil.copyfileobj(r.raw, f)


def add_to_file(link):
    with open("links.txt", "a") as f:
        f.write(link + "\n")


def read_urls():
    try:
        with open("urls.txt") as f:
            urls = [url for url in f.read().split() if url]
    except FileNotFoundError:
        return
    try:
        with open("indices.txt") as f:
            indices = set(map(int, f.read().split(",")))
    except (FileNotFoundError, ValueError):
        indices = None
    for ind, url in enumerate(urls, 1):
        if indices and ind not in indices:
            continue
        yield url


def main():
    for url in read_urls():
        try:
            link = get_zippyshare_dl_link(url)
        except (LinkNotFoundError, requests.excepions.ConnectionError):
            print("Failed to generate link for", url)
            continue
        print(link)
        # download(link)
        add_to_file(link)


if __name__ == "__main__":
    main()
