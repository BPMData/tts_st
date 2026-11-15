"""Prepare a photo the way the app will before upload: turn it upright using the
camera's rotation tag, shrink it, and save a JPEG with NO metadata (no GPS, no
camera details). Usage: python3 -I shrink.py <in> <out> <max_side>"""
import sys
from PIL import Image, ImageOps

src, dst, max_side = sys.argv[1], sys.argv[2], int(sys.argv[3])
im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
im.thumbnail((max_side, max_side), Image.LANCZOS)
clean = Image.new("RGB", im.size)
clean.paste(im)  # copy pixels only, leaving every metadata block behind
clean.save(dst, "JPEG", quality=82)
