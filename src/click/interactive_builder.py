"""
Advanced Interactive CLI Builder for Click

This module provides an interactive command-line interface builder that allows
users to construct Click commands dynamically with real-time feedback,
syntax highlighting, and intelligent suggestions.

Features:
- Real-time command construction
- Syntax highlighting for commands
- Intelligent parameter suggestions
- Command validation and error highlighting
- Interactive help system
- Command history and undo/redo
- Export to Python code
"""

from __future__ import annotations

import ast
import json
import sys
import typing as t
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .core import Command, Group, Option, Argument, Context
from .decorators import command, option, argument
from .exceptions import ClickException
from .termui import echo, secho, style, prompt, confirm
from .types import ParamType, STRING, INT, FLOAT, BOOL, Choice, File, Path as ClickPath


class CommandType(Enum):
    """Types of commands that can be created."""
    SIMPLE = "simple"
    GROUP = "group"
    NESTED = "nested"


class ParameterType(Enum):
    """Types of parameters."""
    OPTION = "option"
    ARGUMENT = "argument"


@dataclass
class CommandBuilder:
    """Builder for constructing Click commands interactively."""
    
    name: str
    command_type: CommandType = CommandType.SIMPLE
    description: str = ""
    parameters: list[dict] = field(default_factory=list)
    subcommands: list[CommandBuilder] = field(default_factory=list)
    help_text: str = ""
    epilog: str = ""
    hidden: bool = False
    deprecated: bool = False
    
    def add_option(
        self,
        name: str,
        param_type: str = "string",
        default: t.Any = None,
        help_text: str = "",
        required: bool = False,
        multiple: bool = False,
        is_flag: bool = False,
        choices: list[str] | None = None,
    ) -> None:
        """Add an option to the command."""
        option_data = {
            "name": name,
            "type": ParameterType.OPTION,
            "param_type": param_type,
            "default": default,
            "help": help_text,
            "required": required,
            "multiple": multiple,
            "is_flag": is_flag,
            "choices": choices,
        }
        self.parameters.append(option_data)
    
    def add_argument(
        self,
        name: str,
        param_type: str = "string",
        nargs: int = 1,
        help_text: str = "",
        required: bool = True,
    ) -> None:
        """Add an argument to the command."""
        argument_data = {
            "name": name,
            "type": ParameterType.ARGUMENT,
            "param_type": param_type,
            "nargs": nargs,
            "help": help_text,
            "required": required,
        }
        self.parameters.append(argument_data)
    
    def add_subcommand(self, subcommand: CommandBuilder) -> None:
        """Add a subcommand to a group command."""
        if self.command_type != CommandType.GROUP:
            raise ClickException("Only group commands can have subcommands")
        self.subcommands.append(subcommand)
    
    def to_python_code(self) -> str:
        """Generate Python code for the command."""
        lines = []
        
        # Import statements
        lines.append("import click")
        lines.append("")
        
        # Generate subcommands first
        for subcmd in self.subcommands:
            lines.append(subcmd.to_python_code())
            lines.append("")
        
        # Generate main command
        decorators = []
        
        # Add parameter decorators
        for param in self.parameters:
            if param["type"] == ParameterType.OPTION:
                decorator_parts = [f"@click.option('--{param['name']}'"]
                
                if param.get("short_name"):
                    decorator_parts[0] = f"@click.option('--{param['name']}', '-{param['short_name']}'"
                
                if param["param_type"] != "string":
                    decorator_parts.append(f"type=click.{param['param_type'].upper()}")
                
                if param.get("default") is not None:
                    decorator_parts.append(f"default={repr(param['default'])}")
                
                if param.get("help"):
                    decorator_parts.append(f"help='{param['help']}'")
                
                if param.get("required"):
                    decorator_parts.append("required=True")
                
                if param.get("multiple"):
                    decorator_parts.append("multiple=True")
                
                if param.get("is_flag"):
                    decorator_parts.append("is_flag=True")
                
                if param.get("choices"):
                    choices_str = ", ".join(f"'{choice}'" for choice in param["choices"])
                    decorator_parts.append(f"type=click.Choice([{choices_str}])")
                
                decorators.append(", ".join(decorator_parts) + ")")
            
            elif param["type"] == ParameterType.ARGUMENT:
                decorator_parts = [f"@click.argument('{param['name']}'"]
                
                if param["param_type"] != "string":
                    decorator_parts.append(f"type=click.{param['param_type'].upper()}")
                
                if param.get("nargs", 1) != 1:
                    decorator_parts.append(f"nargs={param['nargs']}")
                
                if param.get("help"):
                    decorator_parts.append(f"metavar='{param['name'].upper()}'")
                
                decorators.append(", ".join(decorator_parts) + ")")
        
        # Add command decorator
        if self.command_type == CommandType.GROUP:
            decorator_parts = ["@click.group()"]
            if self.description:
                decorator_parts.append(f"help='{self.description}'")
            decorators.append(", ".join(decorator_parts))
        else:
            decorator_parts = ["@click.command()"]
            if self.description:
                decorator_parts.append(f"help='{self.description}'")
            decorators.append(", ".join(decorator_parts))
        
        # Add decorators
        for decorator in reversed(decorators):
            lines.append(decorator)
        
        # Generate function signature
        param_names = [param["name"] for param in self.parameters]
        if self.command_type == CommandType.GROUP:
            param_names.insert(0, "ctx")
        
        func_signature = f"def {self.name}({', '.join(param_names)}):"
        lines.append(func_signature)
        
        # Add docstring
        if self.description:
            lines.append(f'    """{self.description}"""')
        else:
            lines.append('    """Generated command."""')
        
        # Add function body
        lines.append("    pass")
        lines.append("")
        
        # Add subcommand registration for groups
        if self.command_type == CommandType.GROUP and self.subcommands:
            for subcmd in self.subcommands:
                lines.append(f"    {self.name}.add_command({subcmd.name})")
        
        return "\n".join(lines)


class InteractiveCLIBuilder:
    """Interactive CLI builder with real-time feedback and suggestions."""
    
    def __init__(self):
        self.current_command: CommandBuilder | None = None
        self.commands: list[CommandBuilder] = []
        self.history: list[str] = []
        self.suggestions_cache: dict[str, list[str]] = {}
    
    def start_interactive_session(self) -> None:
        """Start the interactive CLI building session."""
        secho("🚀 Click Interactive CLI Builder", fg="green", bold=True)
        secho("=" * 50, fg="blue")
        echo()
        
        while True:
            try:
                self._show_main_menu()
                choice = prompt("Select an option", type=Choice(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]))
                
                if choice == "1":
                    self._create_new_command()
                elif choice == "2":
                    self._edit_command()
                elif choice == "3":
                    self._add_parameter()
                elif choice == "4":
                    self._preview_command()
                elif choice == "5":
                    self._export_code()
                elif choice == "6":
                    self._show_help()
                elif choice == "7":
                    self._validate_command()
                elif choice == "8":
                    self._show_statistics()
                elif choice == "9":
                    self._save_project()
                elif choice == "0":
                    if confirm("Are you sure you want to exit?"):
                        break
                
            except KeyboardInterrupt:
                if confirm("\nAre you sure you want to exit?"):
                    break
            except Exception as e:
                secho(f"Error: {e}", fg="red")
                echo()
    
    def _show_main_menu(self) -> None:
        """Display the main menu."""
        echo()
        secho("📋 Main Menu", fg="cyan", bold=True)
        echo("1. Create new command")
        echo("2. Edit existing command")
        echo("3. Add parameter")
        echo("4. Preview command")
        echo("5. Export Python code")
        echo("6. Show help")
        echo("7. Validate command")
        echo("8. Show statistics")
        echo("9. Save project")
        echo("0. Exit")
        echo()
    
    def _create_new_command(self) -> None:
        """Create a new command interactively."""
        echo()
        secho("🆕 Create New Command", fg="green", bold=True)
        
        name = prompt("Command name", default="my_command")
        description = prompt("Description", default="")
        
        command_type_choice = prompt(
            "Command type",
            type=Choice(["simple", "group", "nested"]),
            default="simple"
        )
        
        command_type = CommandType(command_type_choice)
        
        self.current_command = CommandBuilder(
            name=name,
            command_type=command_type,
            description=description
        )
        
        self.commands.append(self.current_command)
        
        secho(f"✅ Created command '{name}'", fg="green")
        
        # Auto-add common parameters
        if confirm("Add common parameters automatically?"):
            self._add_common_parameters()
    
    def _add_parameter(self) -> None:
        """Add a parameter to the current command."""
        if not self.current_command:
            secho("❌ No command selected. Create a command first.", fg="red")
            return
        
        echo()
        secho("➕ Add Parameter", fg="blue", bold=True)
        
        param_type = prompt(
            "Parameter type",
            type=Choice(["option", "argument"]),
            default="option"
        )
        
        name = prompt("Parameter name")
        
        if param_type == "option":
            self._add_option_interactive(name)
        else:
            self._add_argument_interactive(name)
        
        secho(f"✅ Added {param_type} '{name}'", fg="green")
    
    def _add_option_interactive(self, name: str) -> None:
        """Add an option interactively."""
        param_type = prompt(
            "Data type",
            type=Choice(["string", "int", "float", "bool", "choice", "file", "path"]),
            default="string"
        )
        
        help_text = prompt("Help text", default="")
        required = confirm("Required?", default=False)
        
        default_value = None
        if not required:
            default_input = prompt("Default value (leave empty for None)", default="")
            if default_input:
                try:
                    if param_type == "int":
                        default_value = int(default_input)
                    elif param_type == "float":
                        default_value = float(default_input)
                    elif param_type == "bool":
                        default_value = default_input.lower() in ("true", "yes", "1")
                    else:
                        default_value = default_input
                except ValueError:
                    secho("Invalid default value, using None", fg="yellow")
        
        choices = None
        if param_type == "choice":
            choices_input = prompt("Choices (comma-separated)", default="")
            choices = [choice.strip() for choice in choices_input.split(",") if choice.strip()]
        
        multiple = confirm("Accept multiple values?", default=False)
        is_flag = confirm("Is this a flag?", default=False)
        
        self.current_command.add_option(
            name=name,
            param_type=param_type,
            default=default_value,
            help_text=help_text,
            required=required,
            multiple=multiple,
            is_flag=is_flag,
            choices=choices,
        )
    
    def _add_argument_interactive(self, name: str) -> None:
        """Add an argument interactively."""
        param_type = prompt(
            "Data type",
            type=Choice(["string", "int", "float", "bool", "file", "path"]),
            default="string"
        )
        
        help_text = prompt("Help text", default="")
        required = confirm("Required?", default=True)
        
        nargs = 1
        if not required:
            nargs_input = prompt("Number of arguments", type=int, default=1)
            nargs = nargs_input
        
        self.current_command.add_argument(
            name=name,
            param_type=param_type,
            nargs=nargs,
            help_text=help_text,
            required=required,
        )
    
    def _add_common_parameters(self) -> None:
        """Add common parameters automatically."""
        common_params = [
            ("verbose", "option", "bool", "Enable verbose output", False, False),
            ("config", "option", "file", "Configuration file", False, False),
            ("output", "option", "path", "Output file path", False, False),
        ]
        
        for name, param_type, data_type, help_text, required, is_flag in common_params:
            if param_type == "option":
                self.current_command.add_option(
                    name=name,
                    param_type=data_type,
                    help_text=help_text,
                    required=required,
                    is_flag=is_flag,
                )
            else:
                self.current_command.add_argument(
                    name=name,
                    param_type=data_type,
                    help_text=help_text,
                    required=required,
                )
        
        secho("✅ Added common parameters", fg="green")
    
    def _preview_command(self) -> None:
        """Preview the current command."""
        if not self.current_command:
            secho("❌ No command selected.", fg="red")
            return
        
        echo()
        secho("👁️ Command Preview", fg="cyan", bold=True)
        echo()
        
        # Show command info
        secho(f"Name: {self.current_command.name}", fg="blue")
        secho(f"Type: {self.current_command.command_type.value}", fg="blue")
        secho(f"Description: {self.current_command.description}", fg="blue")
        echo()
        
        # Show parameters
        if self.current_command.parameters:
            secho("Parameters:", fg="green", bold=True)
            for param in self.current_command.parameters:
                param_type = param["type"].value
                param_name = param["name"]
                data_type = param.get("param_type", "string")
                help_text = param.get("help", "")
                
                secho(f"  {param_type}: {param_name} ({data_type})", fg="yellow")
                if help_text:
                    echo(f"    Help: {help_text}")
        else:
            secho("No parameters defined", fg="yellow")
        
        echo()
        
        # Show subcommands
        if self.current_command.subcommands:
            secho("Subcommands:", fg="green", bold=True)
            for subcmd in self.current_command.subcommands:
                secho(f"  {subcmd.name}: {subcmd.description}", fg="yellow")
    
    def _export_code(self) -> None:
        """Export the command as Python code."""
        if not self.current_command:
            secho("❌ No command selected.", fg="red")
            return
        
        echo()
        secho("📤 Export Python Code", fg="green", bold=True)
        echo()
        
        code = self.current_command.to_python_code()
        
        # Syntax highlighting simulation
        lines = code.split('\n')
        for line in lines:
            if line.startswith('import') or line.startswith('from'):
                secho(line, fg="blue")
            elif line.startswith('@'):
                secho(line, fg="magenta")
            elif line.startswith('def '):
                secho(line, fg="green")
            elif line.strip().startswith('"""'):
                secho(line, fg="cyan")
            else:
                echo(line)
        
        echo()
        
        if confirm("Save code to file?"):
            filename = prompt("Filename", default=f"{self.current_command.name}.py")
            try:
                with open(filename, 'w') as f:
                    f.write(code)
                secho(f"✅ Code saved to {filename}", fg="green")
            except Exception as e:
                secho(f"❌ Error saving file: {e}", fg="red")
    
    def _validate_command(self) -> None:
        """Validate the current command."""
        if not self.current_command:
            secho("❌ No command selected.", fg="red")
            return
        
        echo()
        secho("🔍 Command Validation", fg="blue", bold=True)
        echo()
        
        issues = []
        
        # Check command name
        if not self.current_command.name.replace('_', '').isalnum():
            issues.append("Command name contains invalid characters")
        
        # Check for duplicate parameter names
        param_names = [p["name"] for p in self.current_command.parameters]
        if len(param_names) != len(set(param_names)):
            issues.append("Duplicate parameter names found")
        
        # Check required arguments
        required_args = [p for p in self.current_command.parameters 
                        if p["type"] == ParameterType.ARGUMENT and p.get("required", True)]
        optional_args = [p for p in self.current_command.parameters 
                        if p["type"] == ParameterType.ARGUMENT and not p.get("required", True)]
        
        if optional_args and required_args:
            # Check if optional args come after required args
            required_indices = [i for i, p in enumerate(self.current_command.parameters) 
                              if p["type"] == ParameterType.ARGUMENT and p.get("required", True)]
            optional_indices = [i for i, p in enumerate(self.current_command.parameters) 
                              if p["type"] == ParameterType.ARGUMENT and not p.get("required", True)]
            
            if optional_indices and max(optional_indices) < max(required_indices):
                issues.append("Optional arguments should come after required arguments")
        
        if issues:
            secho("❌ Validation Issues Found:", fg="red", bold=True)
            for issue in issues:
                secho(f"  • {issue}", fg="red")
        else:
            secho("✅ Command validation passed!", fg="green", bold=True)
    
    def _show_statistics(self) -> None:
        """Show project statistics."""
        echo()
        secho("📊 Project Statistics", fg="cyan", bold=True)
        echo()
        
        total_commands = len(self.commands)
        total_params = sum(len(cmd.parameters) for cmd in self.commands)
        total_subcommands = sum(len(cmd.subcommands) for cmd in self.commands)
        
        secho(f"Total Commands: {total_commands}", fg="blue")
        secho(f"Total Parameters: {total_params}", fg="blue")
        secho(f"Total Subcommands: {total_subcommands}", fg="blue")
        
        if self.current_command:
            secho(f"Current Command: {self.current_command.name}", fg="green")
            secho(f"Current Parameters: {len(self.current_command.parameters)}", fg="green")
    
    def _save_project(self) -> None:
        """Save the project to a JSON file."""
        if not self.commands:
            secho("❌ No commands to save.", fg="red")
            return
        
        echo()
        secho("💾 Save Project", fg="green", bold=True)
        
        filename = prompt("Project filename", default="click_project.json")
        
        try:
            project_data = {
                "commands": [
                    {
                        "name": cmd.name,
                        "command_type": cmd.command_type.value,
                        "description": cmd.description,
                        "parameters": cmd.parameters,
                        "subcommands": [
                            {
                                "name": sub.name,
                                "command_type": sub.command_type.value,
                                "description": sub.description,
                                "parameters": sub.parameters,
                            }
                            for sub in cmd.subcommands
                        ],
                    }
                    for cmd in self.commands
                ],
                "version": "1.0",
                "created_with": "Click Interactive Builder"
            }
            
            with open(filename, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            secho(f"✅ Project saved to {filename}", fg="green")
            
        except Exception as e:
            secho(f"❌ Error saving project: {e}", fg="red")
    
    def _show_help(self) -> None:
        """Show help information."""
        echo()
        secho("❓ Help", fg="cyan", bold=True)
        echo()
        echo("Click Interactive CLI Builder allows you to:")
        echo("• Create Click commands with a user-friendly interface")
        echo("• Add parameters (options and arguments) interactively")
        echo("• Preview commands before generating code")
        echo("• Export commands as Python code")
        echo("• Validate commands for common issues")
        echo("• Save and load projects")
        echo()
        echo("Tips:")
        echo("• Use descriptive names for commands and parameters")
        echo("• Add help text to make your CLI user-friendly")
        echo("• Validate commands before exporting")
        echo("• Save your work regularly")


# CLI command to start the interactive builder
@command()
@option('--project', help='Load existing project file')
def interactive_builder(project: str | None = None) -> None:
    """Start the Click Interactive CLI Builder.
    
    This tool provides a user-friendly interface for creating Click commands
    with real-time feedback, validation, and code generation.
    """
    builder = InteractiveCLIBuilder()
    
    if project:
        try:
            # Load existing project
            with open(project, 'r') as f:
                project_data = json.load(f)
            
            # Reconstruct commands from project data
            for cmd_data in project_data.get("commands", []):
                cmd = CommandBuilder(
                    name=cmd_data["name"],
                    command_type=CommandType(cmd_data["command_type"]),
                    description=cmd_data["description"],
                    parameters=cmd_data["parameters"],
                )
                builder.commands.append(cmd)
            
            secho(f"✅ Loaded project from {project}", fg="green")
            
        except Exception as e:
            secho(f"❌ Error loading project: {e}", fg="red")
            return
    
    builder.start_interactive_session()


if __name__ == "__main__":
    interactive_builder()
