from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
from collections import defaultdict
from dataclasses import dataclass, field
p = Path("/home/kroot/files.txt").read_text()


@dataclass
class Node:
    children: dict[str, "Node"] = field(default_factory=lambda: defaultdict(Node))
    size: None | int = None


root = Node()


units = {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30, "TB": 2**40}
def parse_size(size):
    number, unit = [string.strip() for string in size.split()]
    return int(float(number)*units[unit])


def append(path: Path, size: int, root: Node):
    node = root
    pars = []
    print(path.parts)
    for part in path.parts:
        pars.append(node)
        node = node.children[part]
    node.size = size
    print(root)


ids, labels, parents, values = [], [], [], []
folders = set()


for line in p.splitlines():
    if line.startswith(" -"):
        idx = line.rfind('-')
        path, size = line.rsplit(' - ', maxsplit=1)
        # if not path.startswith()
        path = Path.home() / path[3:]
        ids.append(str(path))
        labels.append(path.name)
        parents.append(str(path.parent))
        folders.update(path.parents)
        try:
            values.append(parse_size(size))
        except ValueError:
            print(line)
            raise
        append(Path(path), parse_size(size), root)


def rec(node: Node, output: )

folders.difference_update(Path.home().parents)
folders.remove(Path.home())
for path in folders:
    ids.append(str(path))
    labels.append(path.name)
    parents.append(str(path.parent))
    values.append(0)



# fig = go.Figure(go.Sunburst(ids=ids, labels=labels, parents=parents, values=values))
# fig.write_html(Path("/home/kroot/data.html"))

