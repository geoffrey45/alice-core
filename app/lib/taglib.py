import os
from io import BytesIO

from tinytag import TinyTag
from PIL import Image, UnidentifiedImageError

from app import settings
from app.utils import create_hash


def parse_album_art(filepath: str):
    """
    Returns the album art for a given audio file.
    """

    try:
        tags = TinyTag.get(filepath, image=True)
        return tags.get_image()
    except:
        return None


def extract_thumb(filepath: str, webp_path: str) -> bool:
    """
    Extracts the thumbnail from an audio file. Returns the path to the thumbnail.
    """
    img_path = os.path.join(settings.LG_THUMBS_PATH, webp_path)
    sm_img_path = os.path.join(settings.SM_THUMB_PATH, webp_path)

    tsize = settings.THUMB_SIZE
    sm_tsize = settings.SM_THUMB_SIZE

    def save_image(img: Image.Image, small: bool = False):
        if small:
            img.resize((sm_tsize, sm_tsize), Image.ANTIALIAS).save(sm_img_path, "webp")
        else:
            img.resize((tsize, tsize), Image.ANTIALIAS).save(img_path, "webp")

    if os.path.exists(img_path):
        img_size = os.path.getsize(filepath)

        if img_size > 0:
            return True

    album_art = parse_album_art(filepath)

    if album_art is not None:
        try:
            img = Image.open(BytesIO(album_art))
        except (UnidentifiedImageError, OSError):
            return False

        try:
            save_image(img)
            save_image(img, small=True)
        except OSError:
            try:
                png = img.convert("RGB")
                save_image(png)
                save_image(png, small=True)
            except:
                return False

        return True
    else:
        return False


def get_tags(filepath: str):
    filetype = filepath.split(".")[-1]
    filename = (filepath.split("/")[-1]).replace(f".{filetype}", "")

    try:
        tags = TinyTag.get(filepath)
    except:
        return None

    no_albumartist: bool = (tags.albumartist == "") or (tags.albumartist is None)
    no_artist: bool = (tags.artist == "") or (tags.artist is None)

    if no_albumartist and not no_artist:
        tags.albumartist = tags.artist

    if no_artist and not no_albumartist:
        tags.artist = tags.albumartist

    to_filename = ["title", "album"]
    for tag in to_filename:
        p = getattr(tags, tag)
        if p == "" or p is None:
            setattr(tags, tag, filename)

    to_check = ["album", "artist", "year", "albumartist"]
    for prop in to_check:
        p = getattr(tags, prop)
        if (p is None) or (p == ""):
            setattr(tags, prop, "Unknown")

    to_round = ["bitrate", "duration"]
    for prop in to_round:
        try:
            setattr(tags, prop, round(getattr(tags, prop)))
        except TypeError:
            setattr(tags, prop, 0)

    to_int = ["track", "disc"]
    for prop in to_int:
        try:
            setattr(tags, prop, int(getattr(tags, prop)))
        except (ValueError, TypeError):
            setattr(tags, prop, 1)

    try:
        tags.copyright = tags.extra["copyright"]
    except KeyError:
        tags.copyright = None

    tags.albumhash = create_hash(tags.album, tags.albumartist)
    tags.hash = create_hash(tags.artist, tags.album, tags.title)
    tags.image = f"{tags.albumhash}.webp"
    tags.folder = os.path.dirname(filepath)

    tags.date = tags.year
    tags.filepath = filepath
    tags.filetype = filetype

    tags = tags.__dict__

    # delete all tag properties that start with _ (tinytag internals)
    for tag in list(tags):
        if tag.startswith("_"):
            del tags[tag]

    to_delete = [
        "filesize",
        "audio_offset",
        "channels",
        "comment",
        "composer",
        "disc_total",
        "extra",
        "samplerate",
        "track_total",
        "year",
    ]

    for tag in to_delete:
        del tags[tag]

    return tags
