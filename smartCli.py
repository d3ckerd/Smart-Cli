import ollama
import subprocess
import sys
import re
import os
import stat
from rich.syntax import Syntax
from rich.console import Console
from pathlib import Path

# TODO: research libs like click or typer to make the cli interface more professional/clean, clean up sections in cli as well so flow feels better

# global var for message history
messages = []

# rich console for formatted printing of scripts
console = Console()

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


def save_script(script_name):
    exec_dir = Path("~/.local/bin")
    script_path = exec_dir / (script_name + ".sh")       
    # making sure directory already exists, if not makes it
    exec_dir.mkdir(parents = True, exist_ok = True)

    # mode 'w' sets write mode
    with open(script_path, mode = "w", encoding = "utf-8") as file:
        for line in script:
            file.write(line)    
    print("file saved!")

    # making file executbale (same as 'chmod +x filename.sh')
    # gets files permssions
    current_mode = os.stat(script_path).st_mode
    # adding exectubale bits to current_mode for user, group and others
    executable = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(script_path, executable)

if __name__ == "__main__":

    # realized it is easier just to grab user input from python 'input' rather than argv

    inital_prompt = input("Enter inital prompt: ")
    script = generate_script(inital_prompt)
    script_highlighted = Syntax(script, "bash", theme = "monokai")
    print("Generated Bash Script:\n")
    console.print(script_highlighted)
    run = input("\nRun this script [y/n]: ").strip().lower() # allows for caps/whitespace

    # i like to have it so response could be y/yes/yurp/etc..
    while True:
        if not run:
            run = input("\nRun this script [y/n]: ").strip().lower()
            continue

        # TODO: make a [edit/save/exit instead of 3 y/n]
        if run[0] == 'n':
            edit = input("Edit the prompt [y/n]: ").strip().lower()
            if edit[0] == 'n':
                save = input("Save executable to ~/.local/bin? [y/n]: ").strip().lower()
                if save[0] == 'y':
                    script_name = input("Enter script name (no file type): ")
                    save_script(script_name)
                sys.exit(1)

            elif edit[0] == 'y':
                additional_prompt = input("\nEnter prompt: ")
                script = generate_script(additional_prompt)
                print("\nGenerated Bash Script:\n")
                
                # make output highlighted, cleaner to look at and read/distingiush from rest of cli
                script_highlighted = Syntax(script, "bash", line_numbers = True)
                console.print(script_highlighted)
                run = "" #  this will give the 'not run' ... cheeky way around

        elif run[0] == 'y':
        # can excute script now
              break

        else:
            run = input("unexpected input... enter [y/n]: ").strip().lower()

    try:    
        # changed to Popen over run so could get live streaming using PIPE
        result = subprocess.Popen(
            script,
            shell = True,
            executable = '/bin/bash',  # forcing bash
            text = True,               # output as a string
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        for line in result.stdout:
            print(f"{line.strip()}")

        result.wait()

        # checking for bash errors
        if result.returncode != 0:
            print("\nThe bash script failed to execute")
            print(f"Error:\n {result.stderr.read()}")
        else:
            print("\nScript executed successfully")

    except Exception as e:
        print("The bash script failed to excecute")
        print(f"Error output: {e.stderr}")


    save = input("Save executable to ~/.local/bin? [y/n]: ").strip().lower()

    if save[0] == 'y':
        # could parse reponse and only take part up until a '.' if it exits as precaution
        script_name = input("Enter script name (no file type): ")
        save_script(script_name)
    else:
        sys.exit(1)
    
'''
from ollama: what their .chat() json string looks like
{
  "model": "<string>",
  "created_at": "2023-11-07T05:31:56Z",
  "message": {
    "role": "assistant",
    "content": "<string>",
    "thinking": "<string>",
    "tool_calls": [
      {
        "function": {
          "name": "<string>",
          "description": "<string>",
          "arguments": {}
        }
      }
    ],
    "images": [
      "<string>"
    ]
  },
  "done": true,
  "done_reason": "<string>",
  "total_duration": 123,
  "load_duration": 123,
  "prompt_eval_count": 123,
  "prompt_eval_duration": 123,
  "eval_count": 123,
  "eval_duration": 123,
  "logprobs": [
    {
      "token": "<string>",
      "logprob": 123,
      "bytes": [
        123
      ],
      "top_logprobs": [
        {
          "token": "<string>",
          "logprob": 123,
          "bytes": [
            123
          ]
        }
      ]
    }
  ]
}
'''