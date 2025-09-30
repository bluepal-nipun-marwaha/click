<div align="center"><img src="https://raw.githubusercontent.com/pallets/click/refs/heads/stable/docs/_static/click-name.svg" alt="" height="150"></div>

# Click

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary. It's the "Command
Line Interface Creation Kit". It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to
implement an intended CLI API.

Click in three points:

-   Arbitrary nesting of commands
-   Automatic help page generation
-   Supports lazy loading of subcommands at runtime

## 🚀 New in Click 8.4: Interactive CLI Builder

Click now includes a revolutionary **Interactive CLI Builder** that provides a user-friendly interface for creating Click commands with real-time feedback, validation, and code generation.

```python
from click.interactive_builder import interactive_builder

# Start the interactive builder
interactive_builder()
```

**Features:**
- 🎯 **Interactive command creation** with guided prompts
- 🏗️ **Real-time validation** and error checking
- 📝 **Automatic code generation** with syntax highlighting
- 💾 **Project saving/loading** for collaboration
- 🔍 **Command validation** and best practices checking

Learn more: [Interactive Builder Documentation](examples/interactive_builder/README.md)


## A Simple Example

```python
import click

@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    hello()
```

```
$ python hello.py --count=3
Your name: Click
Hello, Click!
Hello, Click!
Hello, Click!
```


## Donate

The Pallets organization develops and supports Click and other popular
packages. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today][].

[please donate today]: https://palletsprojects.com/donate

## Contributing

See our [detailed contributing documentation][contrib] for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

[contrib]: https://palletsprojects.com/contributing/
