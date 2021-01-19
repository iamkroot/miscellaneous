import requests
from bs4 import BeautifulSoup


def parse_second(data: str) -> str:
    if '.' not in data:
        data += ".0"
    sec, milli = map(int, data.split('.'))
    h, ms = divmod(sec, 3600)
    m, s = divmod(ms, 60)
    return f"{h}:{m}:{s},{milli}"


def get_lines(soup):
    for span in soup.find_all('span', {'class': 'transcription-time-part'}):
        start = span.get('data-time-start')
        end = span.get('data-time-end')
        yield (parse_second(start), parse_second(end), span.text.strip())


def dump_srt(lines, file):
    for i, line in enumerate(lines, 1):
        start, end, line = line
        print(i, file=file)
        print(start, end, sep=" --> ", file=file)
        print(line, end="\n\n", file=file)


def get_videos(course_url):
    resp = requests.get(course_url)
    soup = BeautifulSoup(resp.text)
    return [a.get('href') for a in soup.find_all('a', {'class': 'icon video'})]


def main():
    urls = get_videos("https://www.cs.cornell.edu/courses/cs6120/2020fa/self-guided/")
    for url in urls:
        resp = requests.get(url)
        with open('dump.html', 'w') as f:
            f.write(resp.text)
        break
        soup = BeautifulSoup(resp.text)
        title = soup.find('h3', {'class': 'entryTitle'}).text.strip()
        print(title)
        lines = get_lines(soup)
        with open(f"{title}.srt", 'w') as f:
            dump_srt(lines, f)
        break


if __name__ == '__main__':
    # main()
    with open('div.html') as f:
        text = f.read()
    soup = BeautifulSoup(text)
    lines = get_lines(soup)
    title = "02"
    with open(f"{title}.srt", 'w') as f:
        dump_srt(lines, f)
