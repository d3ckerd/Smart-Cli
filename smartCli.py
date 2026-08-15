import ollama
import subprocess
import sys
import re
import os
import stat
import typer
import shutil
from pathlib import Path
# textaul for input text boxes
from textual.app import App, ComposeResult
from textual.widgets import Input
# rich for cli output
from rich.syntax import Syntax
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

# defining UI component using textual lib (was using prompt_toolkit but chose this instead)
class BoxPrompt(App[str]):
    # css for text box
    CSS = """
    Input {
        border: solid white;
        width: 100%;
        background: transparent;
    }
    """

    def __init__(self, placeholder_text: str):
        super().__init__()
        self.placeholder_text = placeholder_text
    
    def compose(self) -> ComposeResult:
        # input field with grey placeholder text
        yield Input(placeholder=self.placeholder_text)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        # when enter hit, eixt app and return string
        
        self.exit(event.value)


# Decision box ui
class DecisionPrompt(App[bool]):
    # Uses the exact same CSS as above
    CSS = """
    Input {
        border: solid white;
        width: 100%;
        background: transparent;
    }
    """
    
    def __init__(self, question: str):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        # Append the standard [y/N] indicator to question
        yield Input(placeholder=f"{self.question} [y/N]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip().lower()
        
        if val in ['y', 'yes']:
            self.exit(True)
        elif val in ['n', 'no', '']: # Hitting Enter with no text defaults to False
            self.exit(False)
        else:
            # If they type something invalid, clear the box and ask again
            event.input.placeholder = f"Invalid input. Please type 'y' or 'n'. {self.question} [y/N]"

# global var for message history
messages = []

# rich console for formatted printing of scripts
console = Console()

# typer app for cli 
app = typer.Typer()


def get_input(text = "Enter prompt"):
    app = BoxPrompt(text)

    # prevent ui from overriding whole screen
    user_input = app.run(inline = True)

    return user_input.strip() if user_input else ""


def get_decision(question):
    app = DecisionPrompt(question)
    # yes/no confirmation box
    # true if select yes, false otherwise
    decision = app.run(inline = True)
    return decision

def generate_script(command):
    messages.append({'role': 'user', 'content': command})
    response = ollama.chat(model = "bash-llama", messages = messages)

    # also appending models reply to the history as 'assistant'
    raw_text = response['message']['content']
    messages.append({"role": "assistant", "content": raw_text})

    '''
    should have a response of:
    ```bash
    <bash script>
    ```
    '''
    # extracting script with a regex: ```(?:bash)?\s*(.*?)```, not sure if 'bash' ]
    # will always be output why I made it an optional argument

    # DOTALL allows for multiline, ignorecase is used to treat upper/lower as identical
    extracted = re.search(r'```(?:bash)?\s*(.*?)```', raw_text, re.DOTALL | re.IGNORECASE)

    if extracted:
      # getting actual script content and remove extra whitespace
      script_content = extracted.group(1).strip()

    else:
      # if the llm doesnt put scope blocks in,, this is a fallback
      script_content = raw_text.strip()

    return script_content


def save_script(script_name, script_content):
    exec_dir = Path("~/.local/bin").expanduser()
    script_path = exec_dir / (script_name + ".sh")       
    # making sure directory already exists, if not makes it
    exec_dir.mkdir(parents = True, exist_ok = True)

    # mode 'w' sets write mode
    with open(script_path, mode = "w", encoding = "utf-8") as file:
        file.write(script_content)   
    
    success_panel = Panel(
        f"[bold green]File saved successfully to {script_path}[/bold green]",
        border_style="green",
        expand=False
    )
    console.print(success_panel)

    # making file executbale (same as 'chmod +x filename.sh')
    # gets files permssions
    current_mode = os.stat(script_path).st_mode
    # adding exectubale bits to current_mode for user, group and others
    executable = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(script_path, executable)


# adding in typer to the program
@app.command()
def main(
    # makes an optional argument can pass in right away
    prompt: str = typer.Argument(None, help = "The plain English instruciton to convert to bash"),
    # creates a save flag
    save: bool = typer.Option(False, "--save", "-s", help = "Save the generated script to a .sh file")
):

    if not prompt:
        prompt = get_input("Enter your prompt")
    
    script = generate_script(prompt)

    script_highlighted = Syntax(script, "bash", theme = "monokai", background_color = "default")
    script_panel = Panel(
        script_highlighted,
        title = "[bold green]Generated Bash Script[/bold green]",
        border_style = "white",
        expand = False  # box wrapped tight to code width
    )
    console.print()
    console.print(script_panel)
    run = get_decision("Run this script?")
    # should now be a selection can't choose any option but yes or no
    while True:
        if not run:
            edit = get_decision("Edit this prompt?")

            if not edit:
                save_prompt = get_decision("Save executable to ~/.local/bin?")
                if save_prompt:
                    script_name = get_input("Enter script name (no file type):")
                    save_script(script_name, script)

                sys.exit(1)

            elif edit:
                additional_prompt = get_input("Enter your prompt")
                script = generate_script(additional_prompt)
                console.print()
                # make output highlighted, cleaner to look at and read/distingiush from rest of cli
                script_highlighted = Syntax(script, "bash", theme = "monokai", background_color = "default")
                script_panel = Panel(
                    script_highlighted,
                    title = "[bold green]Generated Bash Script[/bold green]",
                    border_style = "white",
                    expand = False  # box wrapped tight to code width
                )
                console.print(script_panel)
                run = get_decision("Run this script?")

        elif run:
        # can excute script now
              break
        
        else:
            run = get_decision("unexpected input... enter [y/n]: ")

    try:    
        # changed to Popen over run so could get live streaming using PIPE
        result = subprocess.Popen(
            script,
            shell = True,
            executable = '/bin/bash',  # forcing bash
            text = True,               # output as a string
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize = 1 # forces line buffering
        )
        
        has_output = False

        # if no live output dont stream it
        for line in result.stdout:
            if not has_output:
                console.print()
                console.print(Rule("[bold cyan]Output stream:[/bold cyan]", style = "cyan"))
                has_output = True
            
            console.print(f"[bold cyan]>[/bold cyan]{line.strip()}")

        result.wait()

        if has_output:
            console.print(Rule(style="cyan"))
            console.print()

        # checking for bash errors
        if result.returncode != 0:
            error_msg = result.stderr.read().strip()
            error_panel = Panel(
                f"[bold red]{error_msg}[/bold red]",
                title = "[bold red]Execution failed[/bold red]",
                border_style = "red",
                expand = False
            )
            console.print(error_panel)
        else:
            success_panel = Panel(
                "[bold green]Script executed successfully[/bold green]",
                border_style = "green",
                expand = False
            )
            console.print(success_panel)

    except Exception as e:
        error_panel = Panel(
            f"[bold red]{e}[/bold red]",
            title="[bold red]System Error[/bold red]",
            border_style="red",
            expand=False
        )
        console.print(error_panel)

    # if passed in save block 
    if save:
        script_name = get_input("Enter script name (no file type): ")
        save_script(script_name, script)

    else:
        # could parse reponse and only take part up until a '.' if it exits as precaution
        save_prompt = get_decision("Save executable to ~/.local/bin?")
        if save_prompt:
            script_name = get_input("Enter script name (no file type): ")
            save_script(script_name, script)

if __name__ == "__main__":
    app()