import subprocess as sp
from pathlib import Path
import re
import random


# PAT = re.compile(r"(?P<stem>.*)_Page(?P<pg_num>\d+)")
PAT = re.compile(r"_(?P<pg_num>\d+)")
cmd = ["magick", "-quality", "50", "{input}", "-grayscale", "average", "-attenuate", "0.4", "-rotate", "{rotation}", "+noise", "Gaussian", "{output}"]
fold = Path(r"/home/kroot/Downloads/MSR_RF/")
out_fold = fold / "out"
out_fold.mkdir(exist_ok=True)
for img in fold.iterdir():
    if img.suffix != ".png":
        continue
    if m := PAT.search(img.stem):
        print(m['pg_num'])
        cmd[3] = str(img)
        rot = random.random() * 0.5 * (1, -1)[random.random() > 0.5]
        cmd[9] = f"{rot:.2f}"
        cmd[12] = str(out_fold / (f"page-{m['pg_num']}_out.jpg"))
        # cmd[12] = f'"{cmd[12]}"'
        print(cmd)
        # sp.check_call(" ".join(cmd), shell=True)
        sp.check_call(cmd)
