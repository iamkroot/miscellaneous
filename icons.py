from pathlib import Path, PureWindowsPath, PurePosixPath
from configparser import ConfigParser, NoOptionError

DRIVE_ROOT = Path("/path/to/drive/")


class KDEConfig:
    """Wraps .directory file, handling icon files."""

    def __init__(self, file: Path):
        assert file.name == '.directory'
        self.config = ConfigParser(default_section="Desktop Entry")
        self.config.optionxform = lambda option: option
        self.file = file
        if self.file.exists():
            self.config.read(self.file)

    @property
    def icon_path(self) -> PurePosixPath:
        try:
            icon_path = self.config.get('Desktop Entry', 'Icon')
        except NoOptionError:
            return None
        else:
            return PurePosixPath(icon_path) if icon_path else None

    @icon_path.setter
    def icon_path(self, icon_path):
        icon_path = str(icon_path)
        self.config.set('Desktop Entry', 'Icon', icon_path)
        self.save()

    def save(self):
        with open(self.file, 'w') as f:
            self.config.write(f, space_around_delimiters=False)


class WindowsConfig():
    """Wraps desktop.ini, handling icon files"""

    def __init__(self, file: Path):
        assert file.name == 'desktop.ini'
        self.config = ConfigParser(allow_no_value=True, dict_type=dict,
                                   default_section='.ShellClassInfo')
        self.config.optionxform = lambda option: option
        self.file = file
        if self.file.exists():
            self.config.read(self.file)
        else:
            self._populate_default()
        self.is_relative = False
        self.trailing = ''

    def _populate_default(self):
        self.config.add_section("ViewState")
        self.config["ViewState"]["FolderType"] = "Generic"

    @property
    def icon_path(self) -> PureWindowsPath:
        try:
            icon_res = self.config.get('.ShellClassInfo', 'IconResource')
        except NoOptionError:
            return None
        if not icon_res:
            return None
        self.is_relative = icon_res.startswith('\\')
        end = icon_res.find(',')
        self.trailing = icon_res[end:]
        return PureWindowsPath(icon_res[int(self.is_relative):end])

    @icon_path.setter
    def icon_path(self, icon_path: PureWindowsPath):
        icon_path = str(icon_path)
        icon_res = icon_path + self.trailing
        self.config.set('.ShellClassInfo', 'IconResource', icon_res)

    def save(self):
        with open(self.file, 'w') as f:
            self.config.write(f, space_around_delimiters=False)


def ico_to_directory(ico: Path, overwrite=True):
    directory_file = ico.with_name('.directory')
    if not overwrite and directory_file.exists():
        return
    kde_config = KDEConfig(directory_file)
    kde_config.icon_path = "./" + ico.name
    kde_config.save()


def ini_to_directory(ini_file: Path, move_to_parent=True):
    win_config = WindowsConfig(ini_file)
    win_icon_path = win_config.icon_path
    posix_icon_path = DRIVE_ROOT / win_icon_path.as_posix()
    if not posix_icon_path.exists():
        print(f"Icon file at {posix_icon_path} in desktop.ini doesn't exist.")
        return
    fold = ini_file.parent
    if move_to_parent and posix_icon_path.parent != fold:
        # move icon file to folder with desktop.ini
        new_path = fold / posix_icon_path.name
        posix_icon_path.rename(new_path)
        posix_icon_path = new_path
    ico_to_directory(posix_icon_path)


def directory_to_ini(directory_file: Path, update=False):
    ini_file = directory_file.parent / "desktop.ini"
    if not update and ini_file.exists():
        return
    print("Converting", directory_file.parent.name)
    kde_config = KDEConfig(directory_file)
    if not kde_config.icon_path.is_absolute():
        posix_icon_path = directory_file.parent / kde_config.icon_path
    win_config = WindowsConfig(ini_file)
    rel_path = posix_icon_path.relative_to(DRIVE_ROOT)
    win_icon_path = PureWindowsPath("\\" + "\\".join(rel_path.parts))
    print(win_icon_path)
    win_config.icon_path = win_icon_path
    win_config.save()


def temp():
    fold = DRIVE_ROOT
    for config in fold.glob("**/.directory"):
        conf = KDEConfig(config)
        path = conf.icon_path
        if not path or not path.is_absolute():
            continue
        rel_path = "./" + path.name
        conf.icon_path = rel_path
        print(rel_path)


def populate_missing_ini(directory: Path):
    for directory_file in directory.rglob(".directory"):
        directory_to_ini(directory_file)


if __name__ == '__main__':
    populate_missing_ini(DRIVE_ROOT)
