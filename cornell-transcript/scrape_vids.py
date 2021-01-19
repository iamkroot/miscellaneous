import re
from transcript import get_lines, dump_srt
from bs4 import BeautifulSoup
import subprocess as sp
from pathlib import Path
import requests
from seleniumwire.webdriver import Chrome
# from selenium.webdriver import

VID_PAT = re.compile(r"https://vod\.video\.cornell\.edu/media/(?P<vid_id>[^/]+)")
HLS_HOST = "https://cdnapisec.kaltura.com/"
SUFFIX_PAT = r"/a.m3u8.*uiConfId=\d+$"
M3U8_PAT = HLS_HOST + ".*" + SUFFIX_PAT

SRT_HOST = "https://cdnsecakmi.kaltura.com/"
SRT_SUFFIX_PAT = r"\.srt$"
SRT_PAT = SRT_HOST + ".*" + SRT_SUFFIX_PAT

driver = Chrome()
driver.scopes = [M3U8_PAT, SRT_PAT]
driver.implicitly_wait(20)


def get_master_pls(vid_id):
    driver.switch_to.frame("kplayer_ifp")
    driver.find_element_by_class_name('largePlayBtn').click()
    driver.wait_for_request(M3U8_PAT)
    driver.execute_script('document.getElementsByClassName("mwEmbedPlayer")[0].click()')
    # driver.find_element_by_class_name("mwEmbedPlayer").click()
    driver.switch_to.parent_frame()
    for req in driver.requests:
        if re.search(HLS_HOST + rf".*{vid_id}.*" + SUFFIX_PAT , req.url):
            return req.response.body


def get_transcript():
    driver.wait_for_request(SRT_PAT)
    # for req in driver.requests
    el = driver.find_element_by_class_name("transcript-body")
    soup = BeautifulSoup(el.get_property("outerHTML"), "html.parser")
    return get_lines(soup)


def download_lec_files(url, title, hls_file: Path, srt_file: Path):
    driver.get(url)
    match = VID_PAT.match(url)
    if not match:
        raise ValueError("Invalid url", url)
    body = get_master_pls(match['vid_id'])
    hls_file.write_bytes(body)

    lines = get_transcript()
    with open(srt_file, "w") as f:
        dump_srt(lines, f)


def select_resolution(hls_file: Path, required="best"):
    lines = iter(hls_file.read_text().splitlines())
    links = {}
    for line in lines:
        if line.startswith("#EXT-X-STREAM-INF"):
            ind = line.find("RESOLUTION=")
            res = line[ind + len("RESOLUTION="):].split("x")
            links[tuple(map(int, res))] = (line, next(lines))
    from operator import itemgetter
    if required == "best":
        selected = max(links, key=itemgetter(1), default=None)
    else:
        selected = links.get(required)
    if selected is None:
        print(f"Couldn't find {required=} for {hls_file}")
    else:
        hls_file.write_text("#EXTM3U\n{}\n{}".format(*links[selected]))


def get_course_vids(course_url):
    resp = requests.get(course_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    for article in soup.find_all('article', {}):
        lesson = article.h1.a.text.replace(":", "").strip()
        lesson_num = int(lesson.split(' ')[-1])
        for i, link in enumerate(article.find_all('a', {'class': 'icon video'}), 1):
            yield {
                "title": f"{lesson_num:02}.{i} - {link.text}",
                "url": link['href']
            }


def download_vid(output: Path, hls_file: Path, srt_file: Path = None):
    cmd = [
        "ffmpeg",
        "-protocol_whitelist",
        "file,http,https,tcp,tls,pipe,crypto",
        "-i", str(hls_file),
    ]
    if srt_file.is_file():
        cmd += ["-i", str(srt_file)]
    cmd += ["-map", "0", "-map", "-0:d?"]
    if srt_file.is_file():
        cmd += ["-map", "1"]
    cmd += ["-c", "copy"]
    cmd += [str(output)]
    sp.check_call(cmd)


def main():
    output_dir = Path("CS 6120")
    output_dir.mkdir(exist_ok=True)
    temp_dir = Path("files")
    temp_dir.mkdir(exist_ok=True)

    course_url = "https://www.cs.cornell.edu/courses/cs6120/2020fa/self-guided/"
    for vid in get_course_vids(course_url):
        vid_path = output_dir / f"{vid['title']}.mkv"
        hls_file = temp_dir / f"{vid['title']}.hls"
        srt_file = hls_file.with_suffix(".srt")

        if not hls_file.is_file() or not srt_file.is_file():
            download_lec_files(**vid, hls_file=hls_file, srt_file=srt_file)
            select_resolution(hls_file, "best")
        if not vid_path.is_file():
            download_vid(vid_path, hls_file, srt_file)
        del driver.requests


if __name__ == '__main__':
    main()
