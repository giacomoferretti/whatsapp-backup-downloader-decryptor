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

from . import gpsoauth_helper, utils
from .constants import USER_AGENT


class WaBackup:
    def __init__(self, auth_token, master_token):
        self.auth_token = auth_token
        self.master_token = master_token

        # Check if at least one token is provided
        if not (auth_token or master_token):
            raise ValueError("At least one token must be provided")

    def _get(self, path, params=None, **kwargs):
        path = quote(path)
        r = requests.get(
            f"https://backup.googleapis.com/v1/{path}",
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "User-Agent": USER_AGENT,
            },
            params=params,
            **kwargs,
        )

        # If the request is unauthorized, try to refresh the auth token
        if r.status_code == 401:
            if self.master_token is None:
                raise ValueError(
                    "Auth token is expired and no master token is provided. "
                    "You need to provide a master token to refresh the auth token."
                )

            try:
                android_id = utils.generate_android_uid()
                self.auth_token = gpsoauth_helper.get_auth_token(self.master_token, android_id)
            except gpsoauth_helper.AuthException:
                raise ValueError("Something went wrong while refreshing the auth token")

            r = requests.get(
                f"https://backup.googleapis.com/v1/{path}",
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "User-Agent": USER_AGENT,
                },
                params=params,
                **kwargs,
            )

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
