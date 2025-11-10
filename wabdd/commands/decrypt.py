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
import pathlib
import sys
import traceback
import zlib
from datetime import datetime
from queue import Queue
from threading import Event, Thread
from typing import Tuple

import click
from Cryptodome.Cipher import AES
from rich.console import Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from wa_crypt_tools.lib.db.dbfactory import Database15, DatabaseFactory
from wa_crypt_tools.lib.key.key15 import Key15
from wa_crypt_tools.lib.utils import encryptionloop, mcrypt1_metadata_decrypt

_sentinel = object()
_stop_event = Event()


class DecryptionWorker(Thread):
    def __init__(
        self,
        queue: Queue,
        output: pathlib.Path,
        overall_progress: Tuple[Progress, TaskID],
        key: Key15,
    ):
        super().__init__()
        self.queue = queue
        self.output = output
        self.overall_progress = overall_progress[0]
        self.overall_task = overall_progress[1]
        self.key = key

        self.is_running = True

    def run(self):
        while self.is_running:
            self.task_id = None

            if _stop_event.is_set():
                self.is_running = False
                return

            try:
                # Get a file from the queue
                task = self.queue.get()

                # Check if we're done
                if task is _sentinel:
                    self.is_running = False
                    return

                folder, file = task
                self.ERROR_FOLDER = folder
                self.ERROR_FILE = file

                # Decrypt file
                if file.suffix == ".mcrypt1":
                    output_file, decrypted_data, file_timestamp = decrypt_mcrypt1_file(folder, file, self.key)
                elif file.suffix == ".crypt15":
                    output_file, decrypted_data, file_timestamp = decrypt_crypt15_file(folder, file, self.key)
                else:
                    # Copy unsupported files
                    self.overall_progress.console.print(f"Unsupported file: {file}")
                    output_file = file
                    decrypted_data = output_file.read_bytes()

                # Write decrypted data to output file
                (self.output / output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(self.output / output_file, "wb") as f:
                    f.write(decrypted_data)

                # Update file timestamp
                if file_timestamp:
                    timestamp = file_timestamp.timestamp()
                    os.utime((self.output / output_file), (timestamp, timestamp))

            except Exception as e:
                self.overall_progress.console.print(f"Error in {self.ERROR_FOLDER} {self.ERROR_FILE}")
                self.overall_progress.console.print(f"Error: {e}")
                self.overall_progress.console.print(traceback.format_exc())
                self.is_running = False
            finally:
                # Update overall progress
                if self.is_running:
                    self.overall_progress.update(
                        self.overall_task,
                        advance=1,
                    )

                # Indicate task completion
                self.queue.task_done()


def decrypt_metadata(metadata_file: pathlib.Path, key: Key15):
    with open(metadata_file) as f:
        return mcrypt1_metadata_decrypt(key=key, encoded=f.read())


def decrypt_mcrypt1_file(
    dump_folder: pathlib.Path, encrypted_file: pathlib.Path, key: Key15
) -> Tuple[pathlib.Path, bytes, datetime]:
    # Get filename without `.mcrypt1` extension and convert to bytes
    decryption_hash = bytes.fromhex(encrypted_file.with_suffix("").name)
    decryption_data = encryptionloop(
        first_iteration_data=key.get_root(),
        message=decryption_hash,
        output_bytes=48,
    )

    # Prepare AES
    aes_key = decryption_data[:32]
    aes_iv = decryption_data[32:48]
    cipher = AES.new(aes_key, AES.MODE_GCM, aes_iv)

    # Get metadata
    output_file = encrypted_file.with_suffix("")
    metadata_file = encrypted_file.with_suffix(".mcrypt1-metadata")
    if metadata_file.is_file():
        metadata = decrypt_metadata(metadata_file, key)
        output_file = pathlib.Path(metadata["name"])

    with open(encrypted_file, "rb") as f:
        return (
            output_file,
            cipher.decrypt(f.read()),
            datetime.fromisoformat(metadata["updateTime"]),
        )


def decrypt_crypt15_file(
    dump_folder: pathlib.Path, encrypted_file: pathlib.Path, key: Key15
) -> Tuple[pathlib.Path, bytes, None]:
    output_file = encrypted_file.relative_to(dump_folder)

    # Remove .crypt15 extension
    output_file = output_file.with_suffix("")

    # Open .crypt15 file
    with open(encrypted_file, "rb") as f:
        db = DatabaseFactory.from_file(f)

        # Check if db is Database15
        if not isinstance(db, Database15):
            raise ValueError("Unsupported database format")

        decrypted_data = db.decrypt(key, f.read())

    # Try to decompress the data
    try:
        z_obj = zlib.decompressobj()
        decrypted_data = z_obj.decompress(decrypted_data)

        if not z_obj.eof:
            print(
                f"WARNING: There is more data to decompress. {output_file}",
                file=sys.stderr,
            )
    except zlib.error:
        decrypted_data = decrypted_data

    return output_file, decrypted_data, None


@click.group()
@click.option("--key", help="Key to use for decryption", default=None)
@click.option("--key-file", help="Key file to use for decryption", default=None)
@click.pass_context
def decrypt(ctx, key, key_file):
    if key is None and key_file is None:
        print("Please provide either a --key or a --key-file", file=sys.stderr)
        sys.exit(1)

    if key is not None and key_file is not None:
        print("Please provide either a --key or a --key-file, not both", file=sys.stderr)
        sys.exit(1)

    if key_file is not None:
        try:
            with open(key_file, "r") as f:
                key = f.read().strip()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        key_bytes = bytes.fromhex(key)

        if len(key_bytes) != 32:
            raise ValueError("Key must be 32 bytes long")

        ctx.obj = Key15(keyarray=key_bytes)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@decrypt.command(name="dump")
@click.argument("folder", type=click.Path(exists=True))
@click.option("--output", help="Output directory", default=None)
@click.option("--threads", help="Number of threads to use", default=2)
@click.pass_obj
def cmd_decrypt_dump(obj, folder, output, threads):
    key = obj
    folder = pathlib.Path(folder)

    # Set default output directory
    if not output:
        output = f"{folder}-decrypted"

    # Create output directory
    output = pathlib.Path(output)
    output.mkdir(parents=True, exist_ok=True)

    # Check for correct dump structure
    paths_to_check = [
        "Databases",
        "Backups",
        # "Media", # Not necessary if user has no media
        # "metadata.json",
    ]
    for path in paths_to_check:
        if not (folder / path).exists():
            print(f"Error: {folder / path} not found", file=sys.stderr)
            sys.exit(1)

    # 3.96s user 2.98s system 95% cpu 7.236 total baseline
    # 3.91s user 3.01s system 95% cpu 7.251 total n=1
    # 3.86s user 1.72s system 157% cpu 3.554 total n=2
    # 4.59s user 2.76s system 209% cpu 3.513 total n=4
    # Decrypt files
    queue = Queue()

    download_overall_progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        TextColumn("[yellow]{task.completed}/{task.total}"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    )

    group = Group(download_overall_progress)

    with Live(group):
        # Prepare queue
        queue = Queue()
        wabdd_files = ["metadata.json", "files.json"]
        supported_extensions = [".crypt15", ".mcrypt1", ".mcrypt1-metadata"]
        ignored_extensions = [".mcrypt1-metadata"]
        for file in folder.glob("**/*"):
            # Skip folder
            if file.is_dir():
                continue

            # Skip wabdd related files
            if file.name in wabdd_files:
                continue

            # Warn if file is not supported
            if file.suffix not in supported_extensions:
                print(f"WARNING: Skipping {file}, not supported", file=sys.stderr)
                continue

            # Skip ignored files
            if file.suffix in ignored_extensions:
                continue

            queue.put((folder, file))

        overall_download_task_id = download_overall_progress.add_task("Decrypting files...", total=queue.qsize())

        # Start workers
        workers = []
        for _ in range(threads):
            # Add a sentinel to the queue to indicate the end of the queue
            queue.put(_sentinel)

            worker = DecryptionWorker(
                queue,
                output,
                (download_overall_progress, overall_download_task_id),
                key,
            )
            worker.start()
            workers.append(worker)

        # Wait for all workers to finish
        try:
            for worker in workers:
                worker.join()
        except KeyboardInterrupt:
            print("Keyboard Interrupt received! Stopping workers...")
            _stop_event.set()

            # Wait for remaining workers to finish
            for worker in workers:
                worker.join()
