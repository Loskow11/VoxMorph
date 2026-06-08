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


def normalize(image: Image.Image, size: int = 512, padding: float = 0.10) -> Image.Image:
    # crops tightly to the subject bounding box, adds padding, then resizes to size x size
    # this ensures the object fills the frame — critical for triposr reconstruction quality
    import numpy as np
    arr = np.array(image.convert("RGBA"))
    alpha = arr[:, :, 3]

    rows = np.any(alpha > 10, axis=1)
    cols = np.any(alpha > 10, axis=0)

    if not rows.any() or not cols.any():
        # fallback: no subject found, just resize as-is
        image.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset = ((size - image.width) // 2, (size - image.height) // 2)
        canvas.paste(image, offset)
        return canvas

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    # add padding around the bounding box
    h, w = arr.shape[:2]
    pad_y = int((rmax - rmin) * padding)
    pad_x = int((cmax - cmin) * padding)
    rmin = max(0, rmin - pad_y)
    rmax = min(h - 1, rmax + pad_y)
    cmin = max(0, cmin - pad_x)
    cmax = min(w - 1, cmax + pad_x)

    # crop to subject
    cropped = image.crop((cmin, rmin, cmax + 1, rmax + 1))

    # resize to square canvas while preserving ratio
    cropped.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - cropped.width) // 2, (size - cropped.height) // 2)
    canvas.paste(cropped, offset)
    return canvas
