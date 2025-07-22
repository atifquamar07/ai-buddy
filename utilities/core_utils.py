"""
Author: Atif Quamar (atif7102@gmail.com)

File: utilities/core_utils.py
Description: Implements functions with shared logic across all other util files
"""

import os
from termcolor import colored
import time
import json
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

def load_config(env="development"):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', f'{env}.json')
    with open(config_path, 'r') as config_file:
        return json.load(config_file)
        
config = load_config()

buddy_name = config['buddy_name']
global_path = config['global_path']
memory_model_name = config['memory_model_name']
reply_model_name = config['reply_model_name']

def load_text_file(file_path: str) -> str:
    # The file_path is relative to the project root where the app is run.
    # global_path should be used for user data, not application resources.
    with open(file_path, 'r') as file:
        return file.read().strip()

def remove_emojis(text):
    """Remove all emojis from the given text or dictionary."""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    if isinstance(text, dict):
        return {k: remove_emojis(v) for k, v in text.items()}
    elif isinstance(text, str):
        return emoji_pattern.sub(r'', text)
    else:
        return text

def truncate_conversation(conversation: str, word_limit: int = 1000) -> str:
    """
    Returns the last 'word_limit' words of a given conversation string.

    Args:
    conversation (str): The input conversation string.
    word_limit (int): The maximum number of words to keep. Defaults to 1000.

    Returns:
    str: The truncated conversation string containing the last 'word_limit' words.
    """
    words = conversation.split()
    if len(words) <= word_limit:
        return conversation
    else:
        return ' '.join(words[-word_limit:])

def remove_prefixes(text, prefixes: list):
    """
    Remove specified prefixes from the beginning of the text or dictionary values.
    
    Args:
    text (str or dict): The input text or dictionary to process.
    prefixes (list): A list of prefixes to remove.
    
    Returns:
    str or dict: The text or dictionary with specified prefixes removed from the beginning of string values.
    """
    if isinstance(text, dict):
        return {k: remove_prefixes(v, prefixes) for k, v in text.items()}
    elif isinstance(text, str):
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
        return text.strip()
    else:
        return text

def generate_new_user_id():
    # Generate a UUID, remove dashes, and prepend 'user_'
    uuid_str = str(uuid.uuid4()).replace('-', '')
    return f"user_{uuid_str[:32]}"

def generate_final_prompt(user_id: str, user_name: str, memory: str, user_utterance: str, conversation: str, buddy_name: str, user_summary : str, doc_context: str = ""):
    prompt_template = load_text_file('utilities/prompts/final_prompt_template.txt')

    if conversation: #conversation is non empty
        truncated_conversation =  f"""The following is a conversation of you and {user_name}, for context:
        {truncate_conversation(conversation = conversation, word_limit = 100)}
        """
    else:
        truncated_conversation = ""

    if memory:
        memory = f"""The following is a memory about {user_name}. It contains experiences and opinions.
        {memory}
        """

    # ------------------------------------------------------------------
    # Include uploaded document content if available
    # ------------------------------------------------------------------
    doc_section = ""
    if doc_context:
        doc_section = f"""The following content is extracted from documents uploaded by {user_name}:
        {doc_context}
        """

    # Combine memory, summary and document context
    memory_and_summary = "\n".join(filter(None, [memory, user_summary, doc_section]))

    prompt = prompt_template.format(
        user_name=user_name,
        memory_and_summary=memory_and_summary,
        buddy_name=buddy_name,
        user_utterance=user_utterance,
        truncated_conversation=truncated_conversation
    )
    return prompt

# ----------------------------------------------------------------------
# Utility: Retrieve aggregated text of uploaded documents for a user
# ----------------------------------------------------------------------

def get_uploaded_documents(user_id: str, max_chars: int = 5000) -> str:
    """Return concatenated text of all .txt documents uploaded by a user.

    Args:
        user_id (str): The ID of the user.
        max_chars (int, optional): Character limit for the returned string. Defaults to 5000.

    Returns:
        str: Aggregated document content truncated to *max_chars* characters, or an empty string if no docs are found.
    """
    docs_root = os.path.join(global_path, 'documents', user_id)
    if not os.path.isdir(docs_root):
        return ""

    contents = []
    for fname in os.listdir(docs_root):
        if fname.lower().endswith('.txt'):
            try:
                with open(os.path.join(docs_root, fname), 'r', encoding='utf-8') as f:
                    file_text = f.read().strip()
                    contents.append(f"{fname}:\n{file_text}")
            except Exception:
                # Skip unreadable files
                continue

    aggregated = "\n\n".join(contents)
    # Truncate to reasonable length
    return aggregated[:max_chars]

def transcribe_audio(file_path : str):

    audio_file= open(f"{global_path}/audio.mp3", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    print(transcription.text)

def extract_quoted_content(reply):
    reply = remove_prefixes(remove_emojis(reply), ['Nova:', 'Nova :', 'Haha,', 'haha,', 'nova:', 'nova: '])
    
    # Function to extract content and remove specific patterns
    def extract_and_clean(text):
        # Remove content within parentheses
        text = re.sub(r'\(.*?\)', '', text)
        # Remove content within brackets
        text = re.sub(r'\[.*?\]', '', text)
        # Remove content within asterisks
        text = re.sub(r'\*.*?\*', '', text)
        # Extract content from the first set of quotes
        match = re.search(r'"(.*?)"', text)
        if match:
            return match.group(1)
        return text.strip()
    
    return extract_and_clean(reply.strip())