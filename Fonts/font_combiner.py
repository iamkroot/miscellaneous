from pathlib import Path
from fuzzywuzzy import fuzz

folds = Path(r"D:\Fonts\Fonts")

for fold in folds.iterdir():
    current = "-1"
    if not fold.is_dir():
        continue
    for font in fold.iterdir():
        if font.is_dir():
            continue
        nm = font.stem
        print(current, nm, fuzz.token_set_ratio(nm, current))
        if fuzz.token_set_ratio(nm, current) < 60:
            current = nm.strip()
            new_fold = font.parent / current
            # print("NN", new_fold)
            new_fold.mkdir(exist_ok=True)
        print(font.parent / current / font.name)
        try:
            font.rename(font.parent / current / font.name)
        except FileNotFoundError as e:
            print("ERR", e)
    # current = nm
