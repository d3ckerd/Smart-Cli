import ollama
import subprocess
import sys

# just using a main for this program for now.. not too complex
if __name__ == "__main__":

    # using sys to grab arguments from user
    # sys.argv[0] = script name
    # sys.argv[1] = first arg after (will have to wrap in "" for ease)

    if len(sys.argv) == 2:
        command = sys.argv[1]
        print (f"{sys.argv[0]}  {command}")
    else:
        print("Excepted input\n<script> <command>")
        exit(1)

    # know the command user wants to send to local llm now.. can use the ollama library to chat will bash-llama
    model_name = 'bash-llama'
    response = ollama.chat(
        model = model_name,
        messages=[{'role': 'user', 'content': command}]
    )

    print(response['message']['content'])
    

'''
from ollama... what their chat json string looks like.. response is stored in message content
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