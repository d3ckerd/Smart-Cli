import ollama
import subprocess
import sys
import re

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

    # using sys to grab arguments from user
    # sys.argv[0] = script name
    # sys.argv[1] = first arg after (will have to wrap in "" for ease)

    if len(sys.argv) != 2:
        print("Excepted input\n<script> <command>")
        sys.exit(1)

    inital_prompt = sys.argv[1]
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
            run = input("unexpected input... enter y/n").strip().lower()


    # now should excecute the script.. maybe have an option to save the script in a file and give a path/name?
    try:
        result = subprocess.run(
            script,
            shell = True,
            executable = '/bin/bash',  # forcing bash
            text = True,               # output as a string
            capture_output = True,     # captures stdout/stderr
            check = True               # throws excpetion if bash script fails
        )

        # some scripts won't have output
        if result.stdout:
          print("\nOutput of executed script:")
          print(result.stdout)
        
    
    except Exception as e:
        print("The bash script failed to excecute")
        print(f"Error output: {e.stderr}")


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
