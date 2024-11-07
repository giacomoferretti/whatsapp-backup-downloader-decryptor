import hashlib
import pathlib
import random


# https://stackoverflow.com/questions/1094841/
def sizeof_fmt(num: int, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def generate_android_uid():
    return f"{random.getrandbits(64):016x}"


def get_hash_from_file(file: pathlib.Path):
    with open(file, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.digest()


def crop_string(s: str, N: int, ellipsis="…"):
    # Check if the string needs to be cropped
    if len(s) > N - len(ellipsis):
        return ellipsis + s[(-(N - len(ellipsis))) :]
    else:
        return s
