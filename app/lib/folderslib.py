import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from os import scandir
from typing import Tuple

from app import instances
from app.models import Folder
from app.models import Track
from ..settings import SUPPORTED_FILES, SUPPORTED_IMAGES


@dataclass
class Dir:
    path: str
    is_sym: bool


def get_folder_track_count(path: str) -> int:
    """
    Returns the number of files associated with a folder.
    """
    tracks = instances.tracks_instance.get_dir_t_count(path)
    return len(tracks)


def create_folder(dir: Dir) -> Folder:
    """Create a single Folder object"""
    folder = {
        "name": dir.path.split("/")[-1],
        "path": dir.path,
        "is_sym": dir.is_sym,
        "trackcount": instances.tracks_instance.get_dir_t_count(dir.path),
    }

    return Folder(folder)


class getFnF:
    """
    Get files and folders from a directory.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self) -> Tuple[Track, Folder]:
        try:
            all = scandir(self.path)
        except FileNotFoundError:
            return ([], [])

        dirs, files = [], []

        for entry in all:
            ext = os.path.splitext(entry.name)[1].lower()

            if entry.is_dir() and not entry.name.startswith("."):
                dir = {
                    "path": entry.path,
                    "is_sym": entry.is_symlink(),
                }
                dirs.append(Dir(**dir))
            elif entry.is_file() and ext in SUPPORTED_FILES:
                files.append(entry.path)

        tracks = instances.tracks_instance.find_songs_by_filenames(files)
        tracks = [Track(**track) for track in tracks]

        with ThreadPoolExecutor() as pool:
            iter = pool.map(create_folder, dirs)
            folders = [i for i in iter if i is not None]

        folders = filter(lambda f: f.trackcount > 0, folders)

        return tracks, folders


class FolderLib:
    def get_dir_images(fullpath: str):
        files = scandir(fullpath)

        for entry in files:
            if entry.is_file() and entry.name.endswith(SUPPORTED_IMAGES):
                print(entry.name)


def test_dir_images():
    FolderLib.get_dir_images(
        "/home/cwilvx/Downloads/Telegram Desktop/Mac Miller - Self Care"
    )
