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

from .. import gpsoauth_helper
from ..constants import MASTER_TOKEN_SUFFIX, TOKEN_SUFFIX, TOKENS_FOLDER
from ..utils import generate_android_uid


@click.command(name="token")
@click.argument("email")
@click.option("--token-file", help="Token file", default=None)
@click.option("--master-token", help="Master token file", default=None)
@click.option("--android-id", help="Android ID", default=None)
def token(token_file: str, master_token: str, android_id: str, email: str):
    # Generate a random android_id if not provided
    if android_id is None:
        android_id = generate_android_uid()

    # Use the default token file if not provided
    if token_file is None:
        token_file = email.replace("@", "_").replace(".", "_") + TOKEN_SUFFIX

        # Create tokens folder if it doesn't exist
        tokens_folder = pathlib.Path.cwd() / TOKENS_FOLDER
        tokens_folder.mkdir(parents=True, exist_ok=True)
        token_filepath = tokens_folder / token_file
    else:
        token_filepath = pathlib.Path(token_file)

    # Use the default master token file if not provided
    if master_token is None:
        master_token_file = email.replace("@", "_").replace(".", "_") + MASTER_TOKEN_SUFFIX

        # Create tokens folder if it doesn't exist
        tokens_folder = pathlib.Path.cwd() / TOKENS_FOLDER
        tokens_folder.mkdir(parents=True, exist_ok=True)
        master_token_filepath = tokens_folder / master_token_file
    else:
        master_token_filepath = pathlib.Path(master_token)

    # Ask for the oauth_token cookie
    print("Please visit https://accounts.google.com/EmbeddedSetup, login and copy the oauth_token cookie.")
    oauth_token = input('Enter "oauth_token" code: ')

    # Exchange the token for a master token
    master_response = gpsoauth.exchange_token(email, oauth_token, android_id)
    if "Error" in master_response:
        print(master_response["Error"], file=sys.stderr)
        sys.exit(1)

    master_token = master_response["Token"]
    with open(master_token_filepath, "w") as f:
        f.write(master_token)
        print(f"Master Token saved to `{master_token_filepath}`")

    try:
        auth_token = gpsoauth_helper.get_auth_token(master_token, android_id)
    except gpsoauth_helper.AuthException as e:
        print(e, file=sys.stderr)
        print(e.get_extra(), file=sys.stderr)
        sys.exit(1)

    # Save the token to a file
    with open(token_filepath, "w") as f:
        f.write(auth_token)
        print(f"Token saved to `{token_filepath}`")

    print(f"You can now run `wabdd download --master-token {master_token_filepath}`")
