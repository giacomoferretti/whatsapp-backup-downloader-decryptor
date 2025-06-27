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


import gpsoauth


class AuthException(Exception):
    def __init__(self, message: str, extra: object):
        super().__init__(message)
        self.extra = extra

    def get_extra(self):
        return self.extra


def get_auth_token(master_token: str, android_id: str):
    oauth_data = {
        "accountType": "HOSTED_OR_GOOGLE",
        "has_permission": 1,
        "Token": master_token,
        "service": "oauth2:https://www.googleapis.com/auth/drive.appdata",
        "source": "android",
        "androidId": android_id,
        "app": "com.whatsapp",
        "client_sig": "38a0f7d505fe18fec64fbf343ecaaaf310dbd799",
        "device_country": "us",
        "operatorCountry": "us",
        "lang": "en",
        "sdk_version": 17,
        "google_play_services_version": 240913000,
    }
    auth_response = gpsoauth._perform_auth_request(oauth_data, None)

    # Check if the login was successful
    if "Auth" not in auth_response:
        raise AuthException("Login failed", auth_response)

    return auth_response["Auth"]
