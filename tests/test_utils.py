# Copyright 2025 Giacomo Ferretti
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

from unittest.mock import patch

from wabdd.utils import crop_string, generate_android_uid, sizeof_fmt


def test_bytes():
    assert sizeof_fmt(0) == "0.0B"
    assert sizeof_fmt(1) == "1.0B"
    assert sizeof_fmt(500) == "500.0B"
    assert sizeof_fmt(1023) == "1023.0B"


def test_kilobytes():
    assert sizeof_fmt(1024) == "1.0KiB"


def test_megabytes():
    assert sizeof_fmt(1024 * 1024) == "1.0MiB"


def test_gigabytes():
    assert sizeof_fmt(1024 * 1024 * 1024) == "1.0GiB"


def test_terabytes():
    assert sizeof_fmt(1024 * 1024 * 1024 * 1024) == "1.0TiB"


def test_petabytes():
    assert sizeof_fmt(1024 * 1024 * 1024 * 1024 * 1024) == "1.0PiB"


def test_exabytes():
    assert sizeof_fmt(1024 * 1024 * 1024 * 1024 * 1024 * 1024) == "1.0EiB"


def test_zettabytes():
    assert sizeof_fmt(1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024) == "1.0ZiB"


def test_yottabytes():
    assert sizeof_fmt(1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024) == "1.0YiB"


def test_crop_string():
    assert crop_string("Hello, World!", 5) == "…rld!"


def test_crop_string_no_crop():
    assert crop_string("Hello, World!", 20) == "Hello, World!"


def test_crop_string_empty():
    assert crop_string("", 5) == ""


def test_crop_string_ellipsis():
    assert crop_string("Hello, World!", 5, "...", False) == "...orld!"


def test_crop_string_no_ellipsis():
    assert crop_string("Hello, World!", 5, "") == "orld!"


def test_crop_string_long_ellipsis():
    assert crop_string("Hello, World!", 5, "....", False) == "....orld!"


def test_generate_android_uid():
    with patch("random.getrandbits", return_value=0x123456789ABCDEF0):
        uid = generate_android_uid()
        assert uid == "123456789abcdef0"
