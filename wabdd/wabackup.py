import requests

from .constants import USER_AGENT


class WaBackup:
    def __init__(self, auth):
        self.auth = auth

    def _get(self, path, params=None, **kwargs):
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
        return requests.get(
            f"https://backup.googleapis.com/v1/{path}?alt=media",
            headers={
                "Authorization": f"Bearer {self.auth}",
                "User-Agent": USER_AGENT,
            },
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
