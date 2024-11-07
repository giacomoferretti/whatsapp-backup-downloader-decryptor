import click

from .commands import decrypt, download, token


@click.group()
def cli():
    pass


cli.add_command(token.token)
cli.add_command(download.download)
cli.add_command(decrypt.decrypt)

if __name__ == "__main__":
    cli()
