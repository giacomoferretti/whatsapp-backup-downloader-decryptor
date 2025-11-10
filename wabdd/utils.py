# Copyright 2024 Giacomo Ferretti
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import pathlib
import random
from typing import Union


# https://stackoverflow.com/questions/1094841/
def sizeof_fmt(num: float, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


def generate_android_uid():
    return f"{random.getrandbits(64):016x}"


def get_md5_hash_from_file(file: Union[str, pathlib.Path]):
    with open(file, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.digest()


def crop_string(s: str, N: int, ellipsis="…", include_ellipsis=True):
    ellipsis_length = len(ellipsis) if include_ellipsis else 0

    # Check if the string needs to be cropped
    if len(s) > N - ellipsis_length:
        return ellipsis + s[(-(N - ellipsis_length)) :]
    else:
        return s
