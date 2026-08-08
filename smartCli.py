import ollama
import subprocess
import sys

if __name__ == "__main__":

    # using sys to grab arguments from user
    # sys.argv[0] = script name
    # sys.argv[1] = first arg after (will have to wrap in "" for ease)

    if len(sys.argv) != 2:
        print("Excepted input\n<script> <command>")
        exit(1)

    # know the command user wants to send to local llm now.. can use the ollama library to chat will bash-llama
    command = sys.argv[1]
    model_name = 'bash-llama'
    response = ollama.chat(
        model = model_name,
        messages=[{'role': 'user', 'content': command}]
    )

    raw_text = response['message']['content']
    parts = raw_text.split("```")
    
    '''
    not the most robust but now should have a response of:
    ```
    <bash script>
    ```
    so parts[1] should be the raw text of the bash script generated
    should output the generated script to the user before using subprocess to run it
    '''

    print("Bash script generated:")
    script_content = parts[1]
    print(script_content)
    run = input("Run this script [y/n]: ")

    # i like to have it so response could be y/yes/yurp/etc..
    while True:

        if run[0].lower() == 'n':
            print("maybe here would be a good place to keep memory of chat and edit output")
            exit(1)
    
        elif run[0].lower() == 'y':
        # can excute script now 
            break
        
        else:
            print("unexpected input... enter y/n")


    # now should excecute the script.. maybe have an option to save the script in a file and give a path/name?
    try:
        result = subprocess.run(
            script_content,
            shell = True,
            executable = '/bin/bash',  # forcing bash
            text = True,               # output as a string
            capture_output = True,     # captures stdout/stderr
            check = True               # throws excpetion if bash script fails
        )

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