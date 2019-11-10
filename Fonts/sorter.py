from pathlib import Path
from fontTools.ttLib import TTFont
from ttfquery import describe

fold = Path('/Fonts/GothamFont/')


def process(font: TTFont):
    print(describe.shortName(font))
    weight, is_ita = describe.modifiers(font)
    print(weight, is_ita)
    print(describe.weightName(weight), 'italic' if is_ita else '')


for file in fold.rglob('*.[ot]tf'):
    file: Path
    # if file.suffix not in ('.ttf', '.otf'):
    #     continue
    # try:
    process(TTFont(file))
    # except Exception as e:
        # print(e)
# file = fold
# print(file)
# font = TTFont(file)

# # print(font['name'].names[1].string)
# print(describe.shortName(font))
