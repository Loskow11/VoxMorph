from pathlib import Path
from PIL import Image
from rembg import remove, new_session


# rembg session loaded once to avoid reloading the model on each call
_session = None


def _get_session():
    global _session
    if _session is None:
        _session = new_session("u2net")
    return _session


def remove_background(image_path: str | Path) -> Image.Image:
    # removes the background and returns an RGBA image
    with open(image_path, "rb") as f:
        raw = f.read()
    result = remove(raw, session=_get_session())
    from io import BytesIO
    return Image.open(BytesIO(result)).convert("RGBA")


def normalize(image: Image.Image, size: int = 512) -> Image.Image:
    # resizes while preserving aspect ratio, centered on a size x size canvas
    image.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - image.width) // 2, (size - image.height) // 2)
    canvas.paste(image, offset)
    return canvas
