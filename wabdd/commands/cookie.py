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

import os
import click
import pathlib
from typing import Optional
from playwright.sync_api import sync_playwright
from wabdd.constants import SYSTEM, BROWSER_PATHS, DEFAULT_OUTPUT_PATH

class GoogleAuthClient:
    def __init__(self, browser_name: str = "chrome"):
        browser_config = BROWSER_PATHS.get(SYSTEM, {}).get(browser_name.lower())
        if not browser_config:
            raise ValueError(f"Unsupported browser: {browser_name} on {SYSTEM}")

        self.user_data_dir = os.path.expandvars(browser_config["user_data"])
        self.executable_path = os.path.expandvars(browser_config["executable"])

    def get_oauth_token(self, email: str, password: str) -> Optional[str]:
        with sync_playwright() as playwright:
            browser_context = playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=self.executable_path,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            page = browser_context.new_page()
            page.goto("https://accounts.google.com/EmbeddedSetup",
                      wait_until="networkidle",
                      timeout=60000)

            page.wait_for_load_state("networkidle")

            email_input = page.wait_for_selector("#identifierId")
            if email_input and email_input.is_enabled():
                email_input.fill(email)


            next_button = page.wait_for_selector("#identifierNext > div > button > div.VfPpkd-RLmnJb")
            if next_button and next_button.is_enabled():
                next_button.click()

            page.wait_for_load_state("networkidle")

            password_input = page.wait_for_selector("#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input")
            if password_input and password_input.is_enabled():
                password_input.fill(password)

            password_next = page.wait_for_selector("#passwordNext > div > button > div.VfPpkd-RLmnJb")
            if password_next and password_next.is_enabled():
                password_next.click()

            page.wait_for_load_state("networkidle")

            consent_next = page.wait_for_selector("#signinconsentNext > div > button > span")
            if consent_next and consent_next.is_enabled():
                consent_next.click()

            page.wait_for_timeout(3000)

            cookies = browser_context.cookies()
            oauth_token = next((c["value"] for c in cookies if c["name"] == "oauth_token"), None)

            browser_context.close()
            return oauth_token


@click.command(name="cookie")
@click.argument("email")
@click.option('--password', '-p', help='Google account password', required=True)
@click.option('--output', '-o', help='Output file path', default=str(DEFAULT_OUTPUT_PATH))
@click.option('--browser', '-b', help='Browser to use (chrome/brave/edge)', default="chrome")
def cookie(email: str, password: str, output: str, browser: str):
    client = GoogleAuthClient(browser)

    try:
        oauth_token = client.get_oauth_token(email, password)

        if oauth_token:
            output_path = pathlib.Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if os.path.exists(output_path):
                os.remove(output_path)

            with open(output_path, 'w') as f:
                f.write(oauth_token)
            click.echo(f"Token saved to: {output_path}")

        else:
            click.echo("Failed to obtain oauth_token", err=True)
            exit(1)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)
