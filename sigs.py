import subprocess as sp
from pathlib import Path
import re
import random


PAT = re.compile(r"(?P<stem>.*)_Page(?P<pg_num>\d+)")
cmd = ["convert", "-density", "200", "{input}", "-attenuate", "0.4", "-rotate", "{rotation}", "+noise", "Gaussian", "{output}"]
fold = Path(r"D:\Downloads") / "intern"
for img in fold.iterdir():
    if img.suffix != ".png":
        continue
    if m:= PAT.search(img.stem):
        print(m['stem'], m['pg_num'])
        cmd[3] = str(img)
        rot = random.random() * 0.5 * (1, -1)[random.random() > 0.5]
        cmd[7] = f"{rot:.2f}"
        cmd[10] = str(img.with_name(f"{m['stem']}_{m['pg_num']}_out.pdf"))
        print(cmd)
        sp.check_call(" ".join(cmd), shell=True)
