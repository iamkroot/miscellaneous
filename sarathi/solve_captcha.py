import urllib.request
import subprocess as sp
from string import ascii_lowercase, digits


def data_uri_to_img(data_uri: str) -> bytes:
    assert data_uri.startswith("data:image/"), "Invalid image uri"
    resp = urllib.request.urlopen(data_uri)
    return resp.file.read()


def tesseract(img_data: bytes) -> str:
    op = sp.check_output(
        [
            "tesseract",
            "stdin",
            "stdout",
            "--dpi",
            "72",
            "--psm",
            "8",
            "-c",
            f"tessedit_char_whitelist={ascii_lowercase}{digits}",
        ],
        input=img_data,
    )
    return op.decode().strip()


def solve_captcha(data_uri: str) -> str:
    return tesseract(data_uri_to_img(data_uri))
