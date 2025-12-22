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
import time

import click
import pathlib

from ..constants import DEFAULT_OUTPUT_PATH, BROWSER_PATHS, SELECTORS
from typing import Optional
from playwright.sync_api import sync_playwright

class GoogleAuthClient:
    def __init__(self):
        self.chrome_path = os.path.expandvars(BROWSER_PATHS["Windows"]["chrome"]["executable"])

    def get_oauth_token(self, email: str, password: str) -> Optional[str]:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=False,
                executable_path=self.chrome_path,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = browser.new_context()
            page = context.new_page()

            page.goto("https://accounts.google.com/EmbeddedSetup",
                      wait_until="networkidle",
                      timeout=60000)

            page.wait_for_load_state("networkidle")

            email_input = page.wait_for_selector(SELECTORS['email_input'])
            if email_input and email_input.is_enabled():
                email_input.fill(email)

            next_button = page.wait_for_selector(SELECTORS['email_next'])
            if next_button and next_button.is_enabled():
                next_button.click()

            page.wait_for_load_state("networkidle")

            password_input = page.wait_for_selector(SELECTORS['password_input'])
            if password_input and password_input.is_enabled():
                password_input.fill(password)

            password_next = page.wait_for_selector(SELECTORS['password_next'])
            if password_next and password_next.is_enabled():
                password_next.click()

            try:
                two_step = page.wait_for_selector(SELECTORS['two_step'], timeout=3000)
                two_step_code = page.wait_for_selector(SELECTORS['two_step_code'], timeout=3000)

                if two_step or two_step_code:
                    start_time = time.time()
                    timeout = 60

                    while time.time() - start_time < timeout:
                        if page.is_closed():
                            raise Exception("Browser closed, process aborted.")
                        try:
                            consent_next = page.wait_for_selector(SELECTORS['consent_next'], timeout=1000)
                            if consent_next and consent_next.is_visible():
                                break
                        except Exception:
                            time.sleep(1)
            except Exception:
                pass

            consent_next = page.wait_for_selector(SELECTORS['consent_next'])
            if consent_next and consent_next.is_enabled():
                consent_next.click()

            page.wait_for_timeout(3000)

            cookies = context.cookies()
            oauth_token = next((c["value"] for c in cookies if c["name"] == "oauth_token"), None)

            browser.close()
            return oauth_token


@click.command(name="cookie")
@click.argument("email")
@click.option('--password', '-p', help='Google account password', required=True)
@click.option('--output', '-o', help='Output file path', default=str(DEFAULT_OUTPUT_PATH))
def cookie(email: str, password: str, output: str):
    client = GoogleAuthClient()

    try:
        oauth_token = client.get_oauth_token(email, password)

        if oauth_token:
            output_path = pathlib.Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if os.path.exists(output_path):
                os.remove(output_path)

            with open(output_path, 'w') as f:
                f.write(oauth_token)
            click.echo(f"Token saved to: {output_path}, use it with wabdd token command.")

        else:
            click.echo("Failed to obtain oauth_token", err=True)
            exit(1)

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)