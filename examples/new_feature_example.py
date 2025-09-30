#!/usr/bin/env python3
"""
Example demonstrating a new CLI feature with verbose output.
This shows how Click can handle different output modes.
"""

import click

@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--count", default=1, help="Number of times to execute")
@click.option("--name", prompt="Your name", help="The person to greet")
def greet_with_verbose(count, name, verbose):
    """Enhanced greeting program with verbose mode."""
    if verbose:
        click.echo(f"Starting greeting process for {name}")
        click.echo(f"Will greet {count} time(s)")
        click.echo("=" * 40)
    
    for i in range(count):
        if verbose:
            click.echo(f"Greeting {i+1}/{count}: ", nl=False)
        click.echo(f"Hello, {name}!")
    
    if verbose:
        click.echo("=" * 40)
        click.echo("Greeting process completed")

if __name__ == '__main__':
    greet_with_verbose()