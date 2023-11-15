import tiktoken
import openai
import json
import subprocess
import time
from typing import Dict, List
# import redis
from config import Config

CFG = Config()

# r = redis.StrictRedis(host=CFG.redis_host, port=CFG.redis_port, db=0, decode_responses=True)

def openai_call(
    messages: list[dict[str, str]],
    prompt: str = None,
    model: str = CFG.llm_model,
    temperature: float = 0.5,
    max_tokens: int = 2500,
    io = None
    ):
        while True:
            try:
                if model.startswith("llama"):
                    # Spawn a subprocess to run llama.cpp
                    cmd = ["llama/main", "-p", prompt]
                    result = subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
                    return result.stdout.strip()
                
                elif not model.startswith("gpt-"):
                    # Use completion API
                    response = openai.Completion.create(
                        engine=model,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=1,
                        stream=True,
                        frequency_penalty=0,
                        presence_penalty=0,
                    )

                    chat = []
                    for chunk in response:
                        delta = chunk['choices'][0]['delta']
                        msg = delta.get('content', '')
                        io.output_stream(msg)
                        chat.append(msg)
                    return messages + [{"role": "assistant", "content": "".join(chat)}]
                
                else:
                    # Use chat completion API
                    if prompt:
                        messages = [{"role": "system", "content": prompt}]
                    elif messages:
                        messages = messages
                    else:
                        messages = [{"role": "system", "content": prompt}] + messages
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        stream=True,
                        max_tokens=max_tokens,
                        n=1,
                        stop=None,
                    )

                    # streamowanie wiadomości                                
                    chat = []
                    for chunk in response:
                        delta = chunk['choices'][0]['delta']
                        msg = delta.get('content', '')
                        io.output_stream(msg)
                        chat.append(msg)
                    try:
                        return messages + [{"role": "assistant", "content": "".join(chat)}]
                    except TypeError:
                        print("Error: None")
                
            except openai.APIError:
                print("The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again.")
                time.sleep(10)
            except openai.error.RateLimitError:
                print("The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again.")
                time.sleep(10)  # Wait 10 seconds and try again
            except Exception as e:
                print("exception has occured")
                print(e)
                print("The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again.")
                time.sleep(10)
            else:
                break

def openai_call_functions(
    functions: list[dict],
    messages: list[dict[str, str]],
    prompt: str = None,
    model: str = CFG.llm_model,
    temperature: float = 0.5,
    max_tokens: int = 2500,
    function_call = "auto"
    ):
        while True:
            try:
                if not model.startswith("gpt-"):
                    # Use completion API
                    response = openai.Completion.create(
                        engine=model,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=1,
                        stream=True,
                        frequency_penalty=0,
                        presence_penalty=0,
                        function_call=function_call,
                        functions=functions,
                    )

                    chat = []
                    for chunk in response:
                        delta = chunk['choices'][0]['delta']
                        msg = delta.get('content', '')
                        print(msg, end="")
                        chat.append(msg)
                    return messages + [{"role": "assistant", "content": "".join(chat)}]
                
                else:
                    # Use chat completion API
                    if prompt:
                        messages = [{"role": "system", "content": prompt}]
                    elif messages:
                        messages = messages
                    else:
                        messages = [{"role": "system", "content": prompt}] + messages
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        stream=True,
                        max_tokens=max_tokens,
                        n=1,
                        stop=None,
                        functions=functions,
                        function_call=function_call,
                    )

                    # streamowanie wiadomości                                
                    chat = []
                    for chunk in response:
                        delta = chunk['choices'][0]['delta']
                        msg = delta.get('content', '')
                        print(msg, end="")
                        chat.append(msg)
                    try:
                        return messages + ["".join(chat)]
                    except TypeError:
                        print("Error: None")
                
            except openai.error.RateLimitError:
                print("The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again.")
                time.sleep(10)  # Wait 10 seconds and try again
            else:
                break

def get_embedding(text, model="text-embedding-ada-002"): # alternatively use code
    text = str(text)
    text = text.replace("\n", " ")
    if len(text) != 0:
        return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]
    return [0.0] * 1536


def prompt_function_call(message):
    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        function_args = json.loads(message["function_call"]["arguments"])

        # Get the function object based on function_name
        function = getattr(FunctionExecutor, function_name, None)
        if function is None:
            return f"Invalid function: {function_name}"

        # Prepare the arguments for the function call
        args = []
        for arg in function_args:
            arg_value = function_args[arg]
            args.append(arg_value)

        # Call the function with the arguments
        function_response = eval(function(*args))

        # Step 4, send model the info on the function call and function response
        prompt = f"What is the output of the function call: {function_name}?"
        second_response = openai_call(prompt)

        return second_response
    return message
    
def num_tokens_from_string(string: str, encoding_name: str = 'cl100k_base') -> int:
    """Returns the number of tokens in a text string."""

    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = num_tokens_from_messages(encoding.encode(string))
    return num_tokens

def num_tokens_from_messages(messages: list, model: str =CFG.llm_model) -> int:
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if "gpt-3.5-turbo" in model:
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-4" in model:
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. 
                                  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens