import ollama
import subprocess
import sys
import re
from pathlib import Path

# TODO: add the ability to watch the live output of script if it is timed... also the option to save a script as a .sh

# global var for message history
messages = []

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

if __name__ == "__main__":

    # realized it is easier just to grab user input from python 'input' rather than argv

    inital_prompt = input("Enter inital prompt: ")
    script = generate_script(inital_prompt)
    print("Generated Bash Script:\n")
    print(script)
    run = input("\nRun this script [y/n]: ").strip().lower() # allows for caps/whitespace

    # i like to have it so response could be y/yes/yurp/etc..
    while True:
        if not run:
          run = input("\nRun this script [y/n]: ").strip().lower()
          continue

        if run[0] == 'n':
          edit = input("Edit the prompt [y/n]: ")
          if edit[0].strip().lower() == 'n':
            sys.exit(1)

          else:
            additional_prompt = input("\nEnter prompt: ")
            script = generate_script(additional_prompt)
            print("\nGenerated Bash Script:\n")
            print(script)
            run = "" # wondering if this will give the 'not run' could be cheeky way around]

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
            print(f"Live Output: {line.strip()}")

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

    # option to save the script in a directory (just default to the home directory?)


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
