import click


@click.command()
@click.argument("input", type=click.File("r"))
@click.argument("output", type=click.File("w"))
def cli(input, output):
    click.echo("This is a dummy function")
