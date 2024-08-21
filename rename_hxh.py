"""
Try to recover file names from a torrent file.

I basically messed up my Hunter x Hunter rename via filebot, and ended up with
the files getting names from random episodes. So, episode 33 might have
name "120 - Fake × And × Real.mkv".

This script parses the original torrent file and uses the file size metadata
to match the files. Turns out, all 148 episodes in the torrent have distinct
file size (in bytes.)

Now I just have to match the file size in torrent to the file size on disk to
find the correct name. Has some extra logic to also handle directory names.
"""

from pathlib import Path
import torrent_parser as tp

TORRENT_FILE = "/path/to/hxh.torrent"
DRIVE_ROOT = Path.home() / "Videos"
ORIG_DIR = DRIVE_ROOT / "Hunter x Hunter"
assert ORIG_DIR.exists()
NEW_ROOT = DRIVE_ROOT / "Hunter x Hunter (copy)/"
NEW_ROOT.mkdir(exist_ok=True)

t = tp.parse_torrent_file()
files = list(ORIG_DIR.rglob("*.mkv"))
t_files = [f for f in t['info']['files'] if f['path'][0].endswith(".mkv")]
sizes = {f.stat().st_size: f for f in files}
t_sizes = {f['length']: f['path'][0] for f in t_files}
eps = {int(f.name[:3]): f for f in files}
t_eps = {f['path'][0]: int(f['path'][0][28:31]) for f in t_files}
dirs = {ep: f.parent for ep, f in eps.items()}

for size, path in sizes.items():
    t_file = t_sizes[size]
    ep = t_eps[t_file]
    new_name = eps[ep].name
    new_dir = dirs[ep]
    new_path = NEW_ROOT / new_dir.name / new_name
    new_path.parent.mkdir(exist_ok=True)
    path.rename(new_path)
    print(size, path, t_sizes[size], eps[t_eps[t_sizes[size]]].name)
    print(path, new_path)
