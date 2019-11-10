import requests
import re
import subprocess as sp
import shutil


IDM_PATH = r"C:\Program Files (x86)\Internet Download Manager\IDMan.exe"
pat = re.compile(
    r'.*?a = (?P<a>\d*);\n.*b = (?P<b>\d*);.*?href = "(?P<u1>.*?)".*?"(?P<u2>.*?)";',
    re.DOTALL,
)


class LinkNotFoundError(Exception):
    pass


def get_link(src, domain):
    ind = src.find('<script type="text/javascript">\n    var')
    src = src[ind : ind + src[ind:].find("/script")]
    m = pat.match(src)
    if not m:
        raise LinkNotFoundError
    s = m.groupdict()
    a, b = int(s["a"]), int(s["b"])
    num = (a // 3) + (a % b)
    return domain + s["u1"] + str(num) + s["u2"]


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
            indices = list(map(int, f.read().split(",")))
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
        except (LinkNotFoundError, requests.exceptions.ConnectionError):
            print("Failed to generate link for", url)
            continue
        print(link)
        # download(link)
        add_to_file(link)


if __name__ == "__main__":
    main()
