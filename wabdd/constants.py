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
import platform
from . import __version__

BACKUP_FOLDER = "backups"
TOKENS_FOLDER = "tokens"
TOKEN_SUFFIX = "_token.txt"
MASTER_TOKEN_SUFFIX = "_mastertoken.txt"

DEFAULT_OUTPUT_PATH = pathlib.Path(f"{TOKENS_FOLDER}/oauth{TOKEN_SUFFIX}")

SYSTEM = platform.system()

BROWSER_PATHS = {
    "Windows": {
        "chrome": {
            "executable": "%USERPROFILE%\\AppData\\Local\\ms-playwright\\chrome-win\\chrome.exe",
        }
    }
}

SELECTORS = {
    'email_input': '[type="email"], #identifierId, [name="identifier"]',
    'email_next': '#identifierNext button, [name="identifier_next"]',
    'password_input': '[type="password"], [name="password"]',
    'password_next': '#passwordNext button, [name="password_next"]',
    'two_step': '[jsname="bN97Pc"], .aDGQwe[data-use-configureable-escape-action="true"]',
    'two_step_code': '.fD1Pid[jsname="feLNVc"]',
    'consent_next': '#signinconsentNext button, [name="consent_next"]'
}

USER_AGENT = f"wabdd/{__version__}"
