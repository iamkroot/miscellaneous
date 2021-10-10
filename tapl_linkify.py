import fitz
from typing import NamedTuple
from packaging.version import Version, InvalidVersion
from pathlib import Path
import re

path = Path("~/Books/Types and Programming Languages.bak.pdf").expanduser()
mupdf = fitz.open(path)
SEC_REF_PAT = re.compile(r"§(?P<sec_num>\d+(\.\d+)*)")


class FoundTextBox(NamedTuple):
    string: str
    rect: fitz.Rect


class VersionedEntity(NamedTuple):
    """Anything that is stringified as a version (eg: 2.3.4)

    A hack to get comparison operators between section numbers for free.

    FIXME: We don't really need comparison operators now that we're doing hashjoin.
        Better to replace with regex matching. Would be cheaper.
    """
    version: Version
    rect: fitz.Rect
    pagenum: int


def find_before_target(page: fitz.Page, target: str, margin=200):
    """Find the text _before_ the target word only if text.x0 < margin"""
    prev = None
    for data in page.get_text("words"):
        string = data[4]
        if prev and string == target and prev[0] < margin:
            yield FoundTextBox(prev[4], fitz.Rect(prev[:4]))
        prev = data


def get_all_entities(search_str: str, page_start: int, page_end: int):
    """Search for versioned entities between given pages"""
    for page in mupdf.pages(page_start, page_end):
        for found_box in find_before_target(page, search_str):
            try:
                ver = Version(found_box.string)
            except InvalidVersion:
                print("Weird entity:", found_box)
            else:
                yield VersionedEntity(ver, found_box.rect, page.number)


def add_link(source: VersionedEntity, target: VersionedEntity):
    src_page = mupdf[source.pagenum]
    target_point = target.rect.top_left
    src_page.insert_link({
        'kind': fitz.LINK_GOTO,
        'from': source.rect,
        'page': target.pagenum,
        'to': target_point,
        'zoom': 0.0
    })


def link_exercises_and_solutions():
    all_exercises = get_all_entities("Exercise", 0, 512)
    all_solutions = get_all_entities("Solution:", 514, 587)

    # do a hashjoin of exercises and solutions
    solutions_dict = {sol.version: sol for sol in all_solutions}
    found = set()

    for exercise in all_exercises:
        if solution := solutions_dict.get(exercise.version):
            found.add(solution.version)
            # print("MATCH!", solution, exercise)
            add_link(exercise, solution)
            add_link(solution, exercise)

    for solution in set(solutions_dict.keys()).difference(found):
        print("Warning: No corresponding exercise found for", solution)


def get_sections():
    for entry in mupdf.get_toc():
        level, name, page_num = entry
        page_num: int
        try:
            section_str, _ = name.split(" ", maxsplit=1)
            yield str(Version(section_str)), page_num - 1
        except (ValueError, IndexError, TypeError, InvalidVersion):
            continue


def get_section_refs(page: fitz.Page):
    for data in page.get_text("words"):
        word: str = data[4]
        if "§" in word:
            if ver_str := SEC_REF_PAT.search(word):
                yield fitz.Rect(data[:4]), ver_str["sec_num"]
            else:
                print("Weird section num", word)


def link_section_refs():
    section_index = dict(get_sections())

    for page in mupdf.pages():
        for rect, sec_ref in get_section_refs(page):
            try:
                target_page_num = section_index[sec_ref]
            except KeyError:
                print("Warning: Could not find page number for section", sec_ref)
            else:
                page.insert_link({
                    'kind': fitz.LINK_GOTO,
                    'from': rect,
                    'page': target_page_num,
                })


def main():
    link_exercises_and_solutions()
    link_section_refs()
    mupdf.save(path.with_name("temp.pdf"))


if __name__ == '__main__':
    main()
