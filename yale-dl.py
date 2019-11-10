import argparse
import shutil
import requests
from pathlib import Path
from multiprocessing.pool import Pool
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup


def download_file(url, path: Path):
    name = Path(url.split("/")[-1])
    file = path.with_name(path.name + name.suffix)
    with requests.get(url, stream=True) as r:
        with open(file, "wb") as f:        
            shutil.copyfileobj(r.raw, f)
    print("finished", file)


def get_lec_num(soup):
    num = soup.find("h2", {"class": "session-number"})
    try:
        return int(num.text.split()[1])
    except (AttributeError, ValueError, IndexError):
        pass


def get_lec_title(soup):
    title = soup.find("h2", {"class": "session-title"})
    try:
        return title.text[3:]
    except (AttributeError, IndexError):
        pass


def get_sess_deets(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html5lib")
    name = str(get_lec_num(soup)).zfill(2) + ". " + get_lec_title(soup)
    vid = soup.find("video")
    vid_src = vid.find("source")
    vid_sub = vid.find("track", {"kind": "subtitles", "label": "English"})
    return name, vid_src["src"], vid_sub["src"] 


def get_lec_urls(home):
    base = urlsplit(home)[:2]
    r = requests.get(home)
    soup = BeautifulSoup(r.text, "html5lib")
    div = soup.find("div", id="quicktabs-tabpage-course-2")
    for tr in div.find_all("tr"):
        num, title = tr.find_all("td")
        if 'lecture' not in num.text.lower():
            continue
        yield urlunsplit(base + (title.a['href'], None, None))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--course-url", required=True)
    parser.add_argument("-p", "--path", type=Path, default=Path("Lectures"))
    parser.add_argument("-s", "--subs", action="store_true")
    args = parser.parse_args()

    assert args.course_url.startswith("https://oyc.yale.edu"), "Unsupported url."
    parent: Path = args.path
    parent.mkdir(parents=True, exist_ok=True)

    urls = tuple(get_lec_urls(args.course_url))
    with Pool(4) as pool:
        for url in urls[:20]:
            name, vid_url, sub_url = get_sess_deets(url)
            file = parent / name
            pool.apply_async(download_file, [vid_url, file])
            if args.subs:
                download_file(sub_url, file)
        pool.close()
        pool.join()


if __name__ == '__main__':
    main()
