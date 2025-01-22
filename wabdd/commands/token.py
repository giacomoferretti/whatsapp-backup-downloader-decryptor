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

import pathlib
import sys

import click
import gpsoauth

from ..constants import TOKEN_SUFFIX, TOKENS_FOLDER
from ..utils import generate_android_uid


@click.command(name="token")
@click.argument("email")
@click.option("--token-file", help="Token file", default=None)
@click.option("--android-id", help="Android ID", default=None)
def token(token_file, android_id, email):
    # Generate a random android_id if not provided
    if android_id is None:
        android_id = generate_android_uid()

    # Use the default token file if not provided
    if token_file is None:
        token_file = email.replace("@", "_").replace(".", "_") + TOKEN_SUFFIX

        # Create tokens folder if it doesn't exist
        tokens_folder = pathlib.Path.cwd() / TOKENS_FOLDER
        tokens_folder.mkdir(parents=True, exist_ok=True)
        token_file = tokens_folder / token_file

    # Ask for the oauth_token cookie
    print(
        "Please visit https://accounts.google.com/EmbeddedSetup, "
        "login and copy the oauth_token cookie."
    )
    token = input('Enter "oauth_token" code: ')

    # Exchange the token for a master token
    master_response = gpsoauth.exchange_token(email, token, android_id)
    if "Error" in master_response:
        print(master_response["Error"], file=sys.stderr)
        sys.exit(1)

    master_token = master_response["Token"]

    # Perform the oauth login for com.whatsapp
    # auth_response = gpsoauth.perform_oauth(
    #     email,
    #     master_token,
    #     android_id,
    #     service="oauth2:https://www.googleapis.com/auth/drive.appdata",
    #     app="com.whatsapp",
    #     client_sig="38a0f7d505fe18fec64fbf343ecaaaf310dbd799",
    # )

    # FIXME: Remove this when fixed upstream
    # https://github.com/B16f00t/whapa/issues/228#issuecomment-2608062669
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
        print(auth_response, file=sys.stderr)
        sys.exit(1)

    token = auth_response["Auth"]
    print(f"Your token is: {token}")

    # Save the token to a file
    with open(token_file, "w") as f:
        f.write(token)
        print(f"Token saved to `{token_file}`")

    print(f"You can now run `wabdd download --token-file {token_file}`")
