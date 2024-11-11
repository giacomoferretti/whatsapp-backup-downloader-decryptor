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

from urllib.parse import quote

import requests

from .constants import USER_AGENT


class WaBackup:
    def __init__(self, auth):
        self.auth = auth

    def _get(self, path, params=None, **kwargs):
        path = quote(path)
        r = requests.get(
            f"https://backup.googleapis.com/v1/{path}",
            headers={
                "Authorization": f"Bearer {self.auth}",
                "User-Agent": USER_AGENT,
            },
            params=params,
            **kwargs,
        )
        r.raise_for_status()
        return r

    def _get_page(self, path, page_token=None):
        return self._get(
            path,
            None if page_token is None else {"pageToken": page_token},
        ).json()

    def download(self, path):
        return self._get(
            path,
            params={"alt": "media"},
            stream=True,
        )

    def _list_path(self, path):
        last_component = path.split("/")[-1]
        page_token = None
        while True:
            page = self._get_page(path, page_token)

            # Early exit if no key is found (e.g. no backups)
            if last_component not in page:
                break

            # Yield each item in the page
            for item in page[last_component]:
                yield item

            # If there is no nextPageToken, we are done
            if "nextPageToken" not in page:
                break

            page_token = page["nextPageToken"]

    def get_backups(self):
        return self._list_path("clients/wa/backups")

    def backup_files(self, backup):
        return self._list_path("{}/files".format(backup["name"]))
