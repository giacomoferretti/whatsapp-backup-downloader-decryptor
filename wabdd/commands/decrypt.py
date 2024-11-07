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
import zlib

import click
from Cryptodome.Cipher import AES
from wa_crypt_tools.lib.db.dbfactory import DatabaseFactory
from wa_crypt_tools.lib.key.key15 import Key15
from wa_crypt_tools.lib.utils import encryptionloop, mcrypt1_metadata_decrypt


def decrypt_metadata(metadata_file: pathlib.Path, key: Key15):
    with open(metadata_file) as f:
        return mcrypt1_metadata_decrypt(key=key, encoded=f.read())


def decrypt_mcrypt1_file(
    dump_folder: pathlib.Path, encrypted_file: pathlib.Path, key: Key15
) -> tuple[pathlib.Path, bytes]:
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
        return output_file, cipher.decrypt(f.read())


def decrypt_crypt15_file(
    dump_folder: pathlib.Path, encrypted_file: pathlib.Path, key: Key15
) -> tuple[pathlib.Path, bytes]:
    output_file = encrypted_file.relative_to(dump_folder)

    # Remove .crypt15 extension
    output_file = output_file.with_suffix("")

    # Open .crypt15 file
    with open(encrypted_file, "rb") as f:
        db = DatabaseFactory.from_file(f)
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

    return output_file, decrypted_data


@click.group()
@click.option("--key", help="Key to use for decryption", default=None)
@click.option("--key-file", help="Key file to use for decryption", default=None)
@click.pass_context
def decrypt(ctx, key, key_file):
    if key is None and key_file is None:
        print("Please provide either a --key or a --key-file", file=sys.stderr)
        sys.exit(1)

    if key is not None and key_file is not None:
        print(
            "Please provide either a --key or a --key-file, not both", file=sys.stderr
        )
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
@click.pass_obj
def cmd_decrypt_dump(obj, folder, output):
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

    # Decrypt files
    wabdd_files = ["metadata.json", "files.json"]
    supported_extensions = [".crypt15", ".mcrypt1", ".mcrypt1-metadata"]
    already_decrypted = set()
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

        # Skip already decrypted files
        if file.name in already_decrypted:
            print(f"WARNING: Skipping {file}, already decrypted", file=sys.stderr)
            continue

        # Decrypt file
        if file.suffix == ".mcrypt1":
            output_file, decrypted_data = decrypt_mcrypt1_file(folder, file, key)

        if file.suffix == ".crypt15":
            output_file, decrypted_data = decrypt_crypt15_file(folder, file, key)

        # Write decrypted data to output file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output / output_file, "wb") as f:
            f.write(decrypted_data)

        # Add to already decrypted media
        already_decrypted.add(output_file.name)
