"""Match featurettes (deleted scenes) with their episodes and add episode num"""

from pathlib import Path
from difflib import SequenceMatcher
import re

root = Path("/path/to/30 Rock/")
featurettes_root = root / "Featurettes"
EP_NAME_PAT = re.compile(r"(?P<num>S\d{2}E\d{2}(-E\d{2})?) - (?P<name>.*)")
# EP_NAME_PAT = re.compile(r"(?P<num>S(?P<s>\d{2})E(?P<e>\d{2})(-E(?P<e2>\d{2}))?) - (?P<name>.*)")


def match_files(season: Path, featurettes: Path):
    matches = []
    for ep in season.iterdir():
        match = EP_NAME_PAT.match(ep.stem)
        assert(match), ep.stem
        seq1 = match['name']
        matcher = SequenceMatcher(None, seq1)
        for featurette in featurettes.rglob("*.mkv"):
            matcher.set_seq2(featurette.stem)
            if (ratio := matcher.ratio()) > 0.8:
                new_name = featurette.with_stem(f"{match['num']} - {featurette.stem}")
                print(ratio, seq1, featurette.stem, match['num'], new_name, sep=" | ")
                matches.append((ep, featurette, new_name))
                break
    return matches


matches = []
for entry in root.iterdir():
    if entry.is_dir() and "Season " in entry.stem:
        name = re.sub(r"0(\d)", r"\1", entry.stem)
        featurettes = featurettes_root / name
        assert featurettes.exists(), featurettes
        matches += match_files(entry, featurettes)


for ep, orig, new in matches:
    print(ep, orig, new)
    orig.rename(new)
