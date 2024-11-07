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

import base64
import json
import pathlib
import sys
from datetime import datetime
from queue import Queue
from threading import Event, Thread
from time import time

import click
import inquirer
import requests
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.text import Text

from ..constants import BACKUP_FOLDER
from ..utils import crop_string, get_hash_from_file, sizeof_fmt
from ..wabackup import WaBackup


class ItemSpeedColumn(ProgressColumn):
    """Custom column to show speed in items per second."""

    def __init__(self):
        super().__init__()
        self.previous_completed = {}
        self.previous_time = {}

    def render(self, task):
        # Get the current time and completed items for the task
        current_time = time()
        completed = task.completed

        # Calculate time elapsed since the last update
        last_completed = self.previous_completed.get(task.id, 0)
        last_time = self.previous_time.get(task.id, current_time)

        elapsed_time = (
            current_time - last_time if last_time != current_time else 1e-10
        )  # avoid division by zero

        # Calculate speed in items per second
        speed = (completed - last_completed) / elapsed_time if elapsed_time > 0 else 0

        # Update the previous values for next calculation
        self.previous_completed[task.id] = completed
        self.previous_time[task.id] = current_time

        return Text(f"{speed:.0f} it/s", style="progress.percentage")


_sentinel = object()
_stop_event = Event()


class DownloaderWorker(Thread):
    def __init__(
        self,
        queue: Queue,
        output: pathlib.Path,
        progress: Progress,
        overall_progress: tuple[Progress, TaskID],
        client: WaBackup,
    ):
        super().__init__()
        self.queue = queue
        self.output = output
        self.progress = progress
        self.overall_progress = overall_progress[0]
        self.overall_task = overall_progress[1]
        self.client = client

    def run(self):
        while True:
            self.task_id = None

            if _stop_event.is_set():
                return

            try:
                # Get a file from the queue
                file = self.queue.get()

                # Check if we're done
                if file is _sentinel:
                    # self.queue.task_done()
                    return

                file_path = file["path"]
                file_name = file_path.split("/")[-1]
                file_hash = file["hash"]
                file_size = file["size"]
                metadata = file["metadata"]

                # Strip first 5 components of the path
                # (e.g. clients/wa/backups/00000/files)
                stripped_filepath = pathlib.Path(*file_path.split("/")[5:])

                # Check if file is already downloaded
                local_file = self.output / stripped_filepath
                if local_file.exists():
                    if get_hash_from_file(local_file) == file_hash:
                        # self.progress.console.print(f"Skipping {file_name}")
                        continue

                # Create task
                self.task_id = self.progress.add_task(
                    "",
                    start=False,
                    filename=crop_string(file_name, 20),
                    total=file_size,
                )

                # Download the file
                with self.client.download(file_path) as r:
                    if r.status_code == 401:
                        self.progress.console.print(
                            "Token expired, stopping download",
                        )
                        _stop_event.set()
                        raise Exception("Unauthorized (401) - Stopping all workers")

                    if r.status_code == 404:
                        self.progress.console.print(
                            f"Error: File {file_name} not found",
                        )
                        continue

                    r.raise_for_status()
                    with open(local_file, "wb") as f:
                        self.progress.start_task(self.task_id)
                        for chunk in r.iter_content(chunk_size=8192):
                            if _stop_event.is_set():  # Exit early if stop event is set
                                return

                            self.progress.update(self.task_id, advance=len(chunk))
                            f.write(chunk)

                # Write metadata if available
                if metadata:
                    with open(str(local_file) + "-metadata", "w") as f:
                        f.write(metadata)

            except Exception as e:
                self.progress.console.print(f"Error: {e}")
            finally:
                # Stop the download progress task
                if hasattr(self, "task_id") and self.task_id is not None:
                    self.progress.remove_task(self.task_id)

                # Update overall progress
                self.overall_progress.update(
                    self.overall_task,
                    advance=1,
                )

                # Indicate task completion
                self.queue.task_done()


@click.command(name="download")
@click.option("--token-file", help="Token file", default=None)
@click.option("--output", help="Output directory")
@click.option("--threads", help="Number of threads to use", default=8)
@click.option(
    "--save-files-list",
    help="Save list of files to files.json",
    is_flag=True,
    default=False,
)
def download(token_file, output, threads, save_files_list):
    # Check for token
    if not pathlib.Path(token_file).exists():
        print(f"Token file {token_file} not found", file=sys.stderr)
        print(f"Run `wabdd token` to generate a token", file=sys.stderr)
        sys.exit(1)

    # Load token
    with open(token_file) as f:
        token = f.read().strip()

    # Initialize client
    wa = WaBackup(token)

    # Get backups
    try:
        backups = list(wa.get_backups())
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e}")
        print("Run `wabdd token` to generate a new token", file=sys.stderr)
        sys.exit(1)

    if len(backups) == 0:
        print("No backups found")
        return

    if len(backups) > 1:
        for i, backup in enumerate(backups):
            backup_metadata = json.loads(backup["metadata"])
            print(f"Backup {i+1}: {backup['name']} ({backup['updateTime']})")

        print("Multiple backups found, please specify which one to download")

        questions = [
            inquirer.List(
                "backup",
                message="Which backup do you want to download?",
                choices=[
                    (
                        f"Backup {i+1}: {backup['name'].split('/')[-1]} ({backup['updateTime']})",
                        backup,
                    )
                    for i, backup in enumerate(backups)
                ],
            ),
        ]
        answers = inquirer.prompt(questions)

        # Exit if no backup is selected
        if not answers:
            print("No backup selected")
            return

        backup = answers["backup"]
    else:
        backup = backups[0]
    backup_metadata = json.loads(backup["metadata"])

    # Print backup information
    print(f"Backup: {backup['name'].split('/')[-1]} ({backup['updateTime']})")
    print(" - Total size:", sizeof_fmt(backup_metadata["backupSize"]))
    print(" - Chat size:", sizeof_fmt(backup_metadata["chatdbSize"]))

    # Set output directory
    if not output:
        timestamp = datetime.strptime(backup["updateTime"], "%Y-%m-%dT%H:%M:%S.%fZ")
        output = (
            pathlib.Path.cwd()
            / BACKUP_FOLDER
            / f'{backup["name"].split("/")[-1]}_{timestamp.strftime("%Y%m%d")}'
        )

    output.mkdir(parents=True, exist_ok=True)

    # Write metadata
    with open(output / "metadata.json", "w") as f:
        json.dump(backup_metadata, f, separators=(",", ":"))

    print("Downloading to", output)

    # Download files
    file_retrieval_progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        DownloadColumn(binary_units=True),
        TimeElapsedColumn(),
    )

    download_overall_progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        TextColumn("[yellow]{task.completed}/{task.total}"),
        ItemSpeedColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    )

    download_progress = Progress(
        TextColumn("[bold yellow]Downloading {task.fields[filename]}"),
        BarColumn(bar_width=None),
        DownloadColumn(binary_units=True),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    overall_progress = Progress(
        TimeElapsedColumn(), BarColumn(bar_width=None), TextColumn("{task.description}")
    )

    group = Group(
        Panel(
            Group(
                file_retrieval_progress,
                download_overall_progress,
                download_progress,
            )
        ),
        overall_progress,
    )

    steps = [
        "Retrieving list of files...",
        "Preparing folders...",
        "Downloading files...",
    ]
    current_step = 0

    overall_task_id = overall_progress.add_task("", total=len(steps))

    with Live(group):
        # Retrieve the list of files
        overall_progress.update(
            overall_task_id,
            description=f"{steps[current_step]} ({current_step+1}/{len(steps)})",
        )
        task_id = file_retrieval_progress.add_task(
            "Retrieving list of files...", total=int(backup["sizeBytes"])
        )
        files = []
        debug_files = []
        for file in wa.backup_files(backup):
            if save_files_list:
                debug_files.append(file)

            files.append(
                {
                    "path": file.get("name"),
                    "hash": base64.b64decode(file.get("md5Hash")),
                    "size": int(file.get("sizeBytes")),
                    "metadata": file.get("metadata"),
                }
            )
            file_retrieval_progress.update(
                task_id,
                advance=int(file.get("sizeBytes")),
            )

        file_retrieval_progress.stop_task(task_id)
        file_retrieval_progress.update(
            task_id, description=f"[bold green]All {len(files)} files retrieved!"
        )

        # Debug
        if save_files_list:
            with open(output / "files.json", "w") as f:
                json.dump(debug_files, f, separators=(",", ":"))

        current_step += 1
        overall_progress.update(overall_task_id, advance=1)

        # Prepare directories
        overall_progress.update(
            overall_task_id,
            description=f"{steps[current_step]} ({current_step+1}/{len(steps)})",
        )
        already_created = set()
        for file in files:
            target: pathlib.Path = (
                output / pathlib.Path(*file["path"].split("/")[5:]).parent
            )

            # Skip if already created
            if target in already_created:
                continue

            # Check if target is a directory
            if target.exists() and not target.is_dir():
                print(f"Error: {target} is not a directory", file=sys.stderr)
                sys.exit(1)

            target.mkdir(parents=True, exist_ok=True)
            already_created.add(target)

        current_step += 1
        overall_progress.update(overall_task_id, advance=1)

        # Download files
        overall_progress.update(
            overall_task_id,
            description=f"{steps[current_step]} ({current_step+1}/{len(steps)})",
        )

        overall_download_task_id = download_overall_progress.add_task(
            "Downloading files...", total=len(files)
        )

        queue = Queue()
        for file in files:
            queue.put(file)

        workers = []
        for _ in range(threads):
            # Add a sentinel to the queue to indicate the end of the queue
            queue.put(_sentinel)

            worker = DownloaderWorker(
                queue,
                output,
                download_progress,
                (download_overall_progress, overall_download_task_id),
                wa,
            )
            worker.start()
            workers.append(worker)

        # TODO: won't work if uncommented
        # Wait for all files to download
        # queue.join()

        # Wait for all workers to finish
        try:
            for worker in workers:
                worker.join()
        except KeyboardInterrupt:
            print("Keyboard Interrupt received! Stopping workers...")
            _stop_event.set()

            # TODO: not sure if this is necessary
            # Wait for remaining workers to finish
            for worker in workers:
                worker.join()

        download_overall_progress.stop_task(overall_download_task_id)
        download_overall_progress.update(
            overall_download_task_id,
            description=f"[bold green]All {len(files)} files downloaded!",
        )

        # Complete progress
        overall_progress.update(
            overall_task_id,
            advance=1,
            description=f"FINISHED! ({current_step+1}/{len(steps)})",
        )
