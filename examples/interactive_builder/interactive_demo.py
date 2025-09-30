#!/usr/bin/env python3
"""
Click Interactive Builder Example

This example demonstrates the new Interactive CLI Builder feature in Click 8.4.
The Interactive Builder provides a user-friendly interface for creating Click
commands with real-time feedback, validation, and code generation.

Features demonstrated:
- Interactive command creation
- Parameter addition with type validation
- Real-time command preview
- Code generation and export
- Project saving and loading
- Command validation
"""

import click
from click.interactive_builder import CommandBuilder, InteractiveCLIBuilder, CommandType, ParameterType


@click.group()
def cli():
    """Click Interactive Builder Demo CLI."""
    pass


@cli.command()
def demo_basic():
    """Demonstrate basic interactive builder usage."""
    click.echo("🚀 Click Interactive Builder Demo")
    click.echo("=" * 50)
    
    # Create a simple command builder
    builder = CommandBuilder(
        name="greet",
        command_type=CommandType.SIMPLE,
        description="A simple greeting command"
    )
    
    # Add parameters
    builder.add_option(
        name="name",
        param_type="string",
        default="World",
        help_text="Name to greet",
        required=False
    )
    
    builder.add_option(
        name="count",
        param_type="int",
        default=1,
        help_text="Number of times to greet",
        required=False
    )
    
    builder.add_option(
        name="verbose",
        param_type="bool",
        help_text="Enable verbose output",
        required=False,
        is_flag=True
    )
    
    # Generate and display code
    click.echo("\n📝 Generated Python Code:")
    click.echo("-" * 30)
    
    code = builder.to_python_code()
    click.echo(code)
    
    click.echo("\n✅ Demo completed!")


@cli.command()
def demo_group():
    """Demonstrate group command creation."""
    click.echo("🏗️ Group Command Demo")
    click.echo("=" * 30)
    
    # Create a group command
    group_builder = CommandBuilder(
        name="project",
        command_type=CommandType.GROUP,
        description="Project management commands"
    )
    
    # Add group-level options
    group_builder.add_option(
        name="config",
        param_type="file",
        help_text="Configuration file",
        required=False
    )
    
    group_builder.add_option(
        name="verbose",
        param_type="bool",
        help_text="Enable verbose output",
        required=False,
        is_flag=True
    )
    
    # Create subcommands
    init_cmd = CommandBuilder(
        name="init",
        command_type=CommandType.SIMPLE,
        description="Initialize a new project"
    )
    
    init_cmd.add_argument(
        name="project_name",
        param_type="string",
        help_text="Name of the project",
        required=True
    )
    
    init_cmd.add_option(
        name="template",
        param_type="choice",
        help_text="Project template",
        required=False,
        choices=["basic", "web", "api", "cli"]
    )
    
    build_cmd = CommandBuilder(
        name="build",
        command_type=CommandType.SIMPLE,
        description="Build the project"
    )
    
    build_cmd.add_option(
        name="output",
        param_type="path",
        help_text="Output directory",
        required=False
    )
    
    build_cmd.add_option(
        name="clean",
        param_type="bool",
        help_text="Clean build directory first",
        required=False,
        is_flag=True
    )
    
    # Add subcommands to group
    group_builder.add_subcommand(init_cmd)
    group_builder.add_subcommand(build_cmd)
    
    # Generate code
    click.echo("\n📝 Generated Group Command Code:")
    click.echo("-" * 40)
    
    code = group_builder.to_python_code()
    click.echo(code)
    
    click.echo("\n✅ Group command demo completed!")


@cli.command()
def demo_validation():
    """Demonstrate command validation features."""
    click.echo("🔍 Validation Demo")
    click.echo("=" * 20)
    
    # Create a command with validation issues
    builder = CommandBuilder(
        name="test-command!",
        command_type=CommandType.SIMPLE,
        description="A command with validation issues"
    )
    
    # Add parameters with potential issues
    builder.add_argument("required_arg", param_type="string", required=True)
    builder.add_argument("optional_arg", param_type="string", required=False)
    builder.add_option("duplicate_name", param_type="string")
    builder.add_option("duplicate_name", param_type="int")  # Duplicate name!
    
    click.echo("Command created with potential validation issues...")
    click.echo("\n🔍 Running validation...")
    
    # Simulate validation
    issues = []
    
    # Check command name
    if not builder.name.replace('-', '').replace('!', '').isalnum():
        issues.append("Command name contains invalid characters")
    
    # Check for duplicate parameter names
    param_names = [p["name"] for p in builder.parameters]
    if len(param_names) != len(set(param_names)):
        issues.append("Duplicate parameter names found")
    
    # Check argument order
    required_args = [p for p in builder.parameters 
                    if p["type"] == ParameterType.ARGUMENT and p.get("required", True)]
    optional_args = [p for p in builder.parameters 
                    if p["type"] == ParameterType.ARGUMENT and not p.get("required", True)]
    
    if optional_args and required_args:
        required_indices = [i for i, p in enumerate(builder.parameters) 
                          if p["type"] == ParameterType.ARGUMENT and p.get("required", True)]
        optional_indices = [i for i, p in enumerate(builder.parameters) 
                          if p["type"] == ParameterType.ARGUMENT and not p.get("required", True)]
        
        if optional_indices and max(optional_indices) < max(required_indices):
            issues.append("Optional arguments should come after required arguments")
    
    if issues:
        click.echo("❌ Validation Issues Found:")
        for issue in issues:
            click.echo(f"  • {issue}")
    else:
        click.echo("✅ Command validation passed!")
    
    click.echo("\n✅ Validation demo completed!")


@cli.command()
def demo_interactive():
    """Start the full interactive builder."""
    click.echo("🎯 Starting Interactive CLI Builder...")
    click.echo("This will launch the full interactive interface.")
    
    if click.confirm("Do you want to start the interactive builder?"):
        from click.interactive_builder import interactive_builder
        interactive_builder()
    else:
        click.echo("Interactive builder cancelled.")


@cli.command()
@click.option('--name', default='demo_project', help='Project name')
@click.option('--template', type=click.Choice(['basic', 'web', 'api', 'cli']), 
              default='basic', help='Project template')
def create_project(name: str, template: str):
    """Create a new project using the interactive builder."""
    click.echo(f"🏗️ Creating project '{name}' with template '{template}'")
    
    # Create project command
    project_cmd = CommandBuilder(
        name=name,
        command_type=CommandType.GROUP,
        description=f"Commands for {name} project"
    )
    
    # Add common project options
    project_cmd.add_option(
        name="config",
        param_type="file",
        help_text="Project configuration file",
        required=False
    )
    
    project_cmd.add_option(
        name="verbose",
        param_type="bool",
        help_text="Enable verbose output",
        required=False,
        is_flag=True
    )
    
    # Add template-specific commands
    if template == "web":
        # Web project commands
        serve_cmd = CommandBuilder(
            name="serve",
            command_type=CommandType.SIMPLE,
            description="Start development server"
        )
        
        serve_cmd.add_option(
            name="port",
            param_type="int",
            default=8000,
            help_text="Port to serve on",
            required=False
        )
        
        serve_cmd.add_option(
            name="host",
            param_type="string",
            default="localhost",
            help_text="Host to serve on",
            required=False
        )
        
        project_cmd.add_subcommand(serve_cmd)
        
    elif template == "api":
        # API project commands
        run_cmd = CommandBuilder(
            name="run",
            command_type=CommandType.SIMPLE,
            description="Run the API server"
        )
        
        run_cmd.add_option(
            name="workers",
            param_type="int",
            default=1,
            help_text="Number of worker processes",
            required=False
        )
        
        run_cmd.add_option(
            name="reload",
            param_type="bool",
            help_text="Enable auto-reload",
            required=False,
            is_flag=True
        )
        
        project_cmd.add_subcommand(run_cmd)
    
    # Generate and save code
    code = project_cmd.to_python_code()
    filename = f"{name}_cli.py"
    
    try:
        with open(filename, 'w') as f:
            f.write(code)
        click.echo(f"✅ Project CLI created: {filename}")
        
        # Show preview
        click.echo("\n📝 Generated Code Preview:")
        click.echo("-" * 30)
        click.echo(code[:500] + "..." if len(code) > 500 else code)
        
    except Exception as e:
        click.echo(f"❌ Error creating project: {e}")


if __name__ == '__main__':
    cli()
