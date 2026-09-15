"""Bounded JPEG evidence kept atomically with its observation in SQLite."""
import base64
import binascii
from io import BytesIO
from PIL import Image, UnidentifiedImageError

MAX_BYTES = 192 * 1024
MAX_SIDE = 640


def decode_jpeg(encoded):
    try:
        content = base64.b64decode(encoded, validate=True)
        if not 0 < len(content) <= MAX_BYTES:
            raise ValueError("Evidence JPEG must be at most 192 KiB")
        with Image.open(BytesIO(content)) as image:
            if image.format != "JPEG" or not (1 <= image.width <= MAX_SIDE and 1 <= image.height <= MAX_SIDE):
                raise ValueError("Evidence must be a JPEG no larger than 640 by 640 pixels")
            image.load()
            return content, image.width, image.height
    except (binascii.Error, OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("Evidence must contain a valid base64 JPEG") from exc
