import fitz
from typing import NamedTuple
from packaging.version import Version, InvalidVersion
from pathlib import Path

path = Path("~/Books/Types and Programming Languages.pdf").expanduser()
mupdf = fitz.open(path)


class FoundTextBox(NamedTuple):
    string: str
    rect: fitz.Rect


class VersionedEntity(NamedTuple):
    """Anything that is stringified as a version (eg: 2.3.4)

    A hack to get comparison operators between section numbers for free.
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


mupdf.save(path.with_name("temp.pdf"))
