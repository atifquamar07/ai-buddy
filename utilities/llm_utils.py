"""
Author: Nishant Sharma (nishant@insituate.ai)

File: utilities/llm_utils.py
Description: Implements llm calls
"""

from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
import boto3
import json
from botocore.exceptions import ClientError
from groq import Groq
from utilities.core_utils import *
load_dotenv()

openai_client = OpenAI(api_key = os.getenv('OPENAI_KEY'))

config = load_config()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

bedrock_client = boto3.client(
    service_name='bedrock-runtime',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name='us-east-1',
)

class MemoryResponse(BaseModel):
    memory_found: bool
    memory: str

class GuardRailResponse(BaseModel):
    is_sensitive: bool
    explanation: str

def openai_response(prompt_list : list, structured = False):

    global openai_client

    if structured == "True-memory":

        completion = openai_client.beta.chat.completions.parse(
        model='gpt-4o-mini',
        messages=prompt_list,
        response_format=MemoryResponse,
        )
        message = completion.choices[0].message

        if message.refusal:
            return ({'memory_found' : False})
        elif message.parsed.memory_found == True:
            return ({'memory_found' : True, 'memory' : message.parsed.memory})
        else:
            return ({'memory_found' : False})

    else:
        completion = openai_client.chat.completions.create(
            model = config['openai_model'],
            messages = prompt_list,
            temperature = 0.2
        )
    reply = completion.choices[0].message.content
    print("usage: ", completion.usage)
    return(reply)

#---

def bedrock_response(prompt_list : list, structured = False):
    if structured == "True-memory":
        message = claude_3_5_sonnet_response(prompt_list = prompt_list)
        # Attempt to parse the JSON response
        try:
            parsed_message = json.loads(message.content)
            
            # Check if the required fields are present
            if 'memory_found' in parsed_message:
                if parsed_message['memory_found'] == True and 'memory' in parsed_message:
                    return {'memory_found': True, 'memory': parsed_message['memory']}
                else:
                    return {'memory_found': False}
            else:
                # If the expected structure is not found, return memory_found as False
                return {'memory_found': False}
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return memory_found as False
            return {'memory_found': False}
        except Exception:
            # Catch any other unexpected errors and return memory_found as False
            return {'memory_found': False}

    else:
        reply = claude_3_5_sonnet_response(prompt_list = prompt_list)
    return(reply)

def groq_response(prompt_list : list, structured = False):
    if structured == "True-memory":
        message = groq_mixtral_response(prompt_list)
        # Attempt to parse the JSON response
        try:
            parsed_message = json.loads(message.content)
            
            # Check if the required fields are present
            if 'memory_found' in parsed_message:
                if parsed_message['memory_found'] == True and 'memory' in parsed_message:
                    return {'memory_found': True, 'memory': parsed_message['memory']}
                else:
                    return {'memory_found': False}
            else:
                # If the expected structure is not found, return memory_found as False
                return {'memory_found': False}
        
        except json.JSONDecodeError:
            # If JSON parsing fails, return memory_found as False
            return {'memory_found': False}
        except Exception:
            # Catch any other unexpected errors and return memory_found as False
            return {'memory_found': False}

    else:
        reply = groq_mixtral_response(prompt_list = prompt_list)
    return(reply)

# Initialize Bedrock client
def claude_3_5_sonnet_response(prompt_list : list):
    messages = convert_openai_to_claude(prompt_list)

    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"  # Claude 3.5 Sonnet model
    body = json.dumps({
        "messages": messages,
        "max_tokens": 200000,
        "temperature": 0.3,
        "top_p": 1,
        "top_k": 250,
        "anthropic_version": "bedrock-2023-05-31"
    })  

    # Make the API call
    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=body
    )

    # Parse and print the response
    response_body = json.loads(response['body'].read())
    return(response_body['content'][0]['text'])

def convert_openai_to_claude(openai_messages):
    claude_messages = []
    system_content = ""

    for message in openai_messages:
        role = message['role']
        content = message['content']

        if role == 'system':
            system_content += content + "\n"
        elif role == 'user':
            if system_content:
                claude_messages.append({"role": "user", "content": system_content + content})
                system_content = ""
            else:
                claude_messages.append({"role": "user", "content": content})
        elif role == 'assistant':
            claude_messages.append({"role": "assistant", "content": content})

    # If there's any remaining system content, append it to the last Human message
    # or create a new Human message if there are no existing messages
    if system_content:
        if claude_messages and claude_messages[-1]['role'] == 'Human':
            claude_messages[-1]['content'] = system_content + claude_messages[-1]['content']
        else:
            claude_messages.append({"role": "user", "content": system_content})

    return claude_messages

def groq_mixtral_response(prompt_list : list):

    completion = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages= prompt_list,
        temperature=1,
        max_tokens=32768,
        top_p=1,
        stream=False,
        stop=None,
    )
    return(completion.choices[0].message.content)

def openai_guardrail(prompt_list: list):
    global openai_client

    try:
        completion = openai_client.beta.chat.completions.parse(
            model=config['openai_model'],
            messages=prompt_list,
            response_format=GuardRailResponse
        )
        message = completion.choices[0].message

        if message.refusal:
            return {'is_sensitive': False}
        elif message.parsed.is_sensitive == True:
            return ({'is_sensitive' : True, 'explanation' : message.parsed.explanation})
        else:
            return ({'is_sensitive' : False})
    except Exception as e:
        print(f"Error in OpenAI API call: {str(e)}")
        return {'is_sensitive' : False}